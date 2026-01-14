from db_manager import DBManager

db = DBManager()
history = db.get_user_history(1)  # dla uzytkownika id=1 (ustawiony na sztywno jeszcze)

print("\n--- ZAWARTOŚĆ BAZY DANYCH ---")
if not history:
    print("Baza jest PUSTA! Coś nie zadziałało.")
else:
    for row in history:
        print(
            f"Data: {row[0]} | Ćwiczenie: {row[1]} | Powtórzenia: L:{row[2]} P:{row[3]} | Poprawność: {row[4]:.1f}%"
        )

db.close()
