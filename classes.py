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