from settings import *

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
    def __init__(self):
        self.started = False
        self.running = True
        self.last_command = "COMMAND_NONE"
 
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.5  
        self.recognizer.non_speaking_duration = 0.4 

        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()


    def listen_loop(self):
        print(" [VoiceThread] active")
        
        mic = sr.Microphone(device_index=1, sample_rate=48000) # NIE RZUCAC MIKROFONU POMIEDZY WATKAMI BO PYTHON SIE DENERWUJE
        
        print(" [Voice] noise calibration... please wait")
        with mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.recognizer.dynamic_energy_threshold = False 
            # self.recognizer.energy_threshold = 400 #reczne ustawienie progu
            
        print(" [Voice] ready.")
        while self.running:
            try:
                command = self.grab_voice(mic=mic) 
                if command:
                    matches = difflib.get_close_matches(command, state, n=1, cutoff=0.5)
                    if not matches:
                        continue
                    cmd = matches[0]
                    print(f" [VoiceThread] heard: {cmd}")
                    if not self.started and ("start" in cmd):
                        self.started = True
                        self.last_command = "START"
                        print(" -> Rozpoczynam serie!")

                    elif self.started and ("stop" in cmd or "koniec" in cmd):
                        self.started = False
                        self.last_command = "STOP"
                        print(" -> Koncze serie!")
                        
            except Exception:
                pass
                
    def grab_voice(self, mic, timeout=None, phrase_time_limit=3):
        r = self.recognizer
        try:
            with mic as source:
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = r.recognize_google(audio, show_all=False,language='pl-PL')
            if not text:
                return None
            text = text.lower()
            return text
        except Exception as e:
            pass
        return None
    
    def stop(self):
        self.running = False


class Trainer:
    def __init__(self):
        # Lewa
        self.reps_left = 0
        self.stage_left = "down"
        # Prawa
        self.reps_right = 0
        self.stage_right = "down"
        # Komunikaty
        self.feedback = []

    def process_biceps(self, angles):
        self.feedback = []

        l_angle = angles.get("left_elbow")
        l_swing = angles.get("left_shoulder_swing")

        if l_angle is not None:
            if l_angle > 150:
                self.stage_left = "down"
            if l_angle < 50 and self.stage_left == "down":
                self.stage_left = "up"
                self.reps_left += 1

            # Korekta
            if l_swing is not None and l_swing > 25:
                self.feedback.append("LEWA: Łokieć przy ciele!")

        r_angle = angles.get("right_elbow")
        r_swing = angles.get("right_shoulder_swing")

        if r_angle is not None:
            if r_angle > 150:
                self.stage_right = "down"
            if r_angle < 50 and self.stage_right == "down":
                self.stage_right = "up"
                self.reps_right += 1

            # Korekta
            if r_swing is not None and r_swing > 25:
                self.feedback.append("PRAWA: Łokieć przy ciele!")

    def reset(self):
        self.reps_left = 0
        self.reps_right = 0
        self.stage_left = "down"
        self.stage_right = "down"
        self.feedback = []