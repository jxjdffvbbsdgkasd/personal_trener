from db_manager import DBManager
import os

db_file = "fitness_data.db"

if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Usunięto stary plik: {db_file}")

print("Inicjalizacja nowej, czystej bazy danych...")
db = DBManager()

user, msg = db.register_user("admin", "admin123")

if user:
    print("SUKCES: Utworzono użytkownika 'admin' (ID: 1).")
    print("Hasło: admin123")
else:
    print(f"INFO: {msg}")

hist = db.get_user_history(1)
if len(hist) == 0:
    print("Baza historii treningów jest PUSTA. Gotowe do testów!")
else:
    print("Coś poszło nie tak, w bazie nadal są wpisy.")

db.close()
