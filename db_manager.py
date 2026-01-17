import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "fitness_data.db"


class DBManager:
    def __init__(self):
        # check_same_thread=False jest potrzebne, bo zapisujemy
        # do bazy z wątku głównego lub wątku VoiceThread
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
                session_id TEXT,
                exercise_type TEXT,
                set_number INTEGER,
                reps_left INTEGER,
                reps_right INTEGER,
                correctness_percent REAL,
                date_time TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """
        )

        # tabela do trzymania ustawien uzytkownika
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                biceps_sets INTEGER NOT NULL,
                shoulders_sets INTEGER NOT NULL,
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

    def save_workout(
        self,
        user_id,
        session_id,
        exercise_type,
        set_number,
        reps_left,
        reps_right,
        correctness,
    ):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            """
            INSERT INTO workout_sessions 
            (user_id, session_id, exercise_type, set_number, reps_left, reps_right, correctness_percent, date_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                session_id,
                exercise_type,
                set_number,
                reps_left,
                reps_right,
                correctness,
                timestamp,
            ),
        )
        self.conn.commit()
        print(f" [DB] Zapisano serię {set_number} dla {exercise_type}")

    # zapis ustawien uzytkownika
    def save_user_settings(self, user_id, biceps_sets, shoulders_sets):
        self.cursor.execute(
            """
            INSERT INTO user_settings (user_id, biceps_sets, shoulders_sets)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                biceps_sets=excluded.biceps_sets,
                shoulders_sets=excluded.shoulders_sets
            """,
            (user_id, biceps_sets, shoulders_sets),
        )
        self.conn.commit()
        print(f"Zapisano ustawienia dla użytkownika ID: {user_id}")

    # pobieranie ustawien uzytkownika
    def get_user_settings(self, user_id):
        self.cursor.execute(
            "SELECT biceps_sets, shoulders_sets FROM user_settings WHERE user_id=?",
            (user_id,),
        )
        settings = self.cursor.fetchone()
        if settings:
            return {"biceps": settings[0], "barki": settings[1]}
        return None

    # pobieranie unikalnych sesji do listy w historii
    def get_unique_sessions(self, user_id):
        self.cursor.execute(
            """
            SELECT DISTINCT session_id, date_time 
            FROM workout_sessions 
            WHERE user_id=? 
            GROUP BY session_id 
            ORDER BY date_time DESC
        """,
            (user_id,),
        )
        return self.cursor.fetchall()

    # szczegoly konkretnej sesji
    def get_session_details(self, session_id):
        self.cursor.execute(
            """
            SELECT exercise_type, set_number, reps_left, reps_right, correctness_percent
            FROM workout_sessions
            WHERE session_id=?
            ORDER BY date_time ASC
        """,
            (session_id,),
        )
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
