from settings import *
from datetime import datetime


class IPStream:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.frame = np.zeros((480, 640, 3), np.uint8)
        self.running = True
        threading.Thread(target=self.update, daemon=True).start()

    def update(self):
        while self.running:
            ret, img = self.cap.read()
            if ret:
                self.frame = img

    def read(self):
        return True, self.frame

    def release(self):
        self.running = False
        self.cap.release()


class VoiceThread:
    def __init__(self, model_path="model"):  # ścieżka do folderu z modelem vosk
        self.started = False
        self.running = True
        self.last_command = "COMMAND_NONE"

        # Kolejka na dane audio
        self.q = queue.Queue()

        # Inicjalizacja modelu
        if not os.path.exists(model_path):
            print(" [Voice] BŁĄD: Nie znaleziono modelu Vosk w folderze:", model_path)
            self.running = False
            return

        self.model = Model(model_path)

        # Opcjonalnie: ograniczamy słownik, żeby zwiększyć celność
        # Słowa muszą być małymi literami
        self.words_list = '["start", "stop", "barki", "biceps"]'
        self.recognizer = KaldiRecognizer(self.model, 16000, self.words_list)

        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Pobiera audio z mikrofonu i wrzuca do kolejki"""
        self.q.put(in_data)
        return (None, pyaudio.paContinue)

    def listen_loop(self):
        print(" [VoiceThread] Aktywny (Vosk)")

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000,
            stream_callback=self.audio_callback,
        )

        stream.start_stream()

        while self.running:
            data = self.q.get()
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")

                if text:
                    # DLA TETSU DIAGNISTYCZNEGO
                    print(f" [VOSK] Usłyszałem: '{text}'")
                    self.last_command = text
            else:
                # Tutaj można wyciągać PartialResult(), jeśli chcesz widzieć tekst w trakcie mówienia
                pass

        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        self.running = False


class Trainer:
    def __init__(self):
        # Lewa
        self.reps_left = 0
        self.failed_reps_left = 0
        self.stage_left = "down"
        self.cheat_left = False
        # Prawa
        self.reps_right = 0
        self.failed_reps_right = 0
        self.stage_right = "down"
        self.cheat_right = False
        # Komunikaty
        self.feedback = []

    def process_biceps(self, angles):
        self.feedback = []

        l_angle = angles.get("left_elbow")
        l_swing = angles.get("left_shoulder_swing")
        l_flare = angles.get("left_flare")

        if l_angle is not None:
            if l_angle > 150:
                self.stage_left = "down"
                self.cheat_left = False

            if self.stage_left == "down" and l_angle < 140:
                if l_flare is not None and l_flare > 105:
                    self.cheat_left = True
                    self.feedback.append("LEWA: Nie machaj na boki!")

                if l_flare is not None and l_flare < 80:
                    self.cheat_left = True
                    self.feedback.append("LEWA: Nie ściągaj do środka!")

                if l_swing is not None and l_swing > 35:
                    self.cheat_left = True
                    self.feedback.append("LEWA: Łokieć przy ciele!")

            if l_angle < 50 and self.stage_left == "down":
                if not self.cheat_left:
                    self.stage_left = "up"
                    self.reps_left += 1
                else:
                    self.stage_left = "up"
                    self.failed_reps_left += 1
                    self.feedback.append("LEWA: Powtórzenie niezaliczone!")

        r_angle = angles.get("right_elbow")
        r_swing = angles.get("right_shoulder_swing")
        r_flare = angles.get("right_flare")

        if r_angle is not None:
            if r_angle > 150:
                self.stage_right = "down"
                self.cheat_right = False

            if self.stage_right == "down" and r_angle < 140:
                if r_flare is not None and r_flare > 105:
                    self.cheat_right = True
                    self.feedback.append("PRAWA: Nie machaj na boki!")

                if r_flare is not None and r_flare < 80:
                    self.cheat_right = True
                    self.feedback.append("PRAWA: Nie ściągaj do środka!")

                if r_swing is not None and r_swing > 35:
                    self.cheat_right = True
                    self.feedback.append("PRAWA: Łokieć przy ciele!")

            if r_angle < 50 and self.stage_right == "down":
                if not self.cheat_right:
                    self.stage_right = "up"
                    self.reps_right += 1
                else:
                    self.stage_right = "up"
                    self.failed_reps_right += 1
                    self.feedback.append("PRAWA: Powtórzenie niezaliczone!")

    def process_shoulders(self, angles):
        """Logika dla wyciskania na barki z wykrywaniem błędów (cheat)."""
        self.feedback = []

        # lewa
        l_lift = angles.get("left_shoulder_lift")  # Kąt wznosu (względem tułowia)
        l_elbow = angles.get("left_elbow")  # Kąt wyprostu ręki

        if l_lift is not None and l_elbow is not None:
            # 1. POZYCJA DOLNA (Start) - Resetujemy błędy
            # Warunek: Ręka nisko (<120) ORAZ łokieć mocno zgięty (<110)
            if l_lift < 120 and l_elbow < 110:
                self.stage_left = "down"
                self.cheat_left = False  # Resetujemy flagę oszustwa

            # 2. WYKRYWANIE OSZUSTWA (Wznosy zamiast wyciskania)
            # Jeśli ręka jest w poziomie (70-110 stopni), ale łokieć jest PROSTY (>140),
            # to znaczy, że robisz "pajacyka" / wznosy, a nie wyciskanie.
            if 70 < l_lift < 110 and l_elbow > 140:
                self.cheat_left = True
                self.feedback.append("LEWA: Zegnij łokcie! To nie wznosy.")

            # 3. ZALICZENIE POWTÓRZENIA (Góra)
            # Warunek: Ręka wysoko (>150) i wyprostowana (>145)
            if l_lift > 150 and l_elbow > 145 and self.stage_left == "down":
                if not self.cheat_left:
                    self.stage_left = "up"
                    self.reps_left += 1
                else:
                    # Jeśli wykryto wznosy, nie zaliczamy i resetujemy cykl
                    self.stage_left = "up"
                    self.failed_reps_left += 1
                    self.feedback.append("LEWA: Powtórzenie niezaliczone!")

            # Dodatkowy feedback: Niepełny wyprost na górze
            if l_lift > 155 and l_elbow < 130:
                self.feedback.append("LEWA: Doprostuj rękę na górze!")

        # prawa
        r_lift = angles.get("right_shoulder_lift")
        r_elbow = angles.get("right_elbow")

        if r_lift is not None and r_elbow is not None:
            # 1. Pozycja dolna (Reset)
            if r_lift < 120 and r_elbow < 110:
                self.stage_right = "down"
                self.cheat_right = False

            # 2. Wykrywanie oszustwa (Wznosy)
            if 70 < r_lift < 110 and r_elbow > 140:
                self.cheat_right = True
                self.feedback.append("PRAWA: Zegnij łokcie! To nie wznosy.")

            # 3. Zaliczenie powtórzenia
            if r_lift > 150 and r_elbow > 145 and self.stage_right == "down":
                if not self.cheat_right:
                    self.stage_right = "up"
                    self.reps_right += 1
                else:
                    self.stage_right = "up"
                    self.failed_reps_right += 1
                    self.feedback.append("PRAWA: Powtórzenie niezaliczone!")

            # Feedback
            if r_lift > 155 and r_elbow < 130:
                self.feedback.append("PRAWA: Doprostuj rękę na górze!")

    def reset(self):
        self.reps_left = 0
        self.reps_right = 0
        self.failed_reps_left = 0
        self.failed_reps_right = 0
        self.stage_left = "down"
        self.stage_right = "down"
        self.cheat_left = False
        self.cheat_right = False
        self.feedback = []

    def get_accuracy(self):
        """srednia % wartosc poprawnosci cwiczen"""
        total_good = self.reps_left + self.reps_right
        total_bad = self.failed_reps_left + self.failed_reps_right
        total_attempts = total_good + total_bad

        if total_attempts == 0:
            return 100.0  # brak powtorzen = 100% poprawnosci (?)

        return (total_good / total_attempts) * 100.0


class WorkoutManager:
    def __init__(self):
        # defaultowa liczba serii
        self.target_sets = {"biceps": 3, "barki": 3}

        # aktualna seria
        self.sets_done = {"biceps": 0, "barki": 0}

        # generowana po starcie treningu
        self.session_id = None

    # generuje id sesji, resetuje liczniki serii
    def start_new_training(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.sets_done["biceps"] = 0
        self.sets_done["barki"] = 0
        print(f" Rozpoczęto nową sesję: {self.session_id}")

    # wyswietla numer ROBIONEJ serii
    # jesli nie zrobilismy jeszcze zadnej to ofc robimy "1"
    def get_display_set_number(self, exercise):
        done = self.sets_done.get(exercise, 0)
        target = self.target_sets.get(exercise, 3)

        if done >= target:
            return target  # zeby nie wyswietlalo 4/3 serie xd np tylko 3/3 (albo nwm jakis napis koniec zaplanowanych serii?)

        return done + 1

    # zapisuje w bazie nr serii ktora wlasnie sie skonczyla
    def get_actual_set_number_for_db(self, exercise):
        return self.sets_done.get(exercise, 0) + 1

    # pobiera ustalona ilosc serii
    def get_target_set(self, exercise):
        return self.target_sets.get(exercise, 3)

    # po komendzie STOP koniec serii
    def mark_set_complete(self, exercise):
        if exercise in self.sets_done:
            if self.sets_done[exercise] < self.target_sets[exercise]:
                self.sets_done[exercise] += 1

    # czy wszystkie ustawione serie skonczone?
    def is_workout_complete(self, exercise):
        done = self.sets_done.get(exercise, 0)
        target = self.target_sets.get(exercise, 3)
        return done >= target

    # ustawianie ilosci serii
    def change_target(self, exercise, delta):
        new_val = self.target_sets[exercise] + delta
        if new_val < 1:
            new_val = 1
        if new_val > 99:
            new_val = 99
        self.target_sets[exercise] = new_val


# stan aplikacji zamiast zmiennych globalnych w main
class GameState:
    def __init__(self):
        self.state = "LOGIN"
        self.user_id = None
        self.user_name = ""
        self.login_msg = ""
        self.exercise_type = "none"
        self.running = True

        # historia
        self.selected_session_id = None
        self.session_buttons = []
