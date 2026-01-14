import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "fitness_data.db"


class DBManager:
    def __init__(self):
        # check_same_thread=False jest potrzebne, bo będziemy (później)
        # zapisywać do bazy z wątku głównego lub wątku VoiceThread
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Tabela użytkowników
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT
            )
        """
        )

        # Tabela sesji treningowych
        # Zapisujemy tu podsumowanie jednej "serii" (od komendy start do stop)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                exercise_type TEXT,
                reps_left INTEGER,
                reps_right INTEGER,
                correctness_percent REAL,
                date_time TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """
        )
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        pwd_hash = self.hash_password(password)
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, pwd_hash, timestamp),
            )
            self.conn.commit()
            return True, "Zarejestrowano pomyślnie!"
        except sqlite3.IntegrityError:
            return False, "Użytkownik o takiej nazwie już istnieje."

    def login_user(self, username, password):
        pwd_hash = self.hash_password(password)
        self.cursor.execute(
            "SELECT id, username FROM users WHERE username=? AND password_hash=?",
            (username, pwd_hash),
        )
        user = self.cursor.fetchone()
        if user:
            return user  # Zwraca (id, username)
        return None

    def save_workout(self, user_id, exercise_type, reps_left, reps_right, correctness):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            """
            INSERT INTO workout_sessions (user_id, exercise_type, reps_left, reps_right, correctness_percent, date_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (user_id, exercise_type, reps_left, reps_right, correctness, timestamp),
        )
        self.conn.commit()
        print(f" [DB] Zapisano trening dla ID {user_id}: {exercise_type}")

    def get_user_history(self, user_id):
        # Pobieramy ostatnie 10 treningów
        self.cursor.execute(
            """
            SELECT date_time, exercise_type, reps_left, reps_right, correctness_percent 
            FROM workout_sessions 
            WHERE user_id=? 
            ORDER BY date_time DESC LIMIT 10
        """,
            (user_id,),
        )
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
