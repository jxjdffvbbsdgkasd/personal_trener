from db_manager import DBManager

print("Testowanie bazy danych...")
db = DBManager()

print("Rejestracja 'admin':", db.register_user("admin", "admin123"))

user = db.login_user("admin", "admin123")
print("Logowanie 'admin':", user)

if user:
    uid = user[0]
    db.save_workout(uid, "biceps", 10, 10, 95.0)
    db.save_workout(uid, "barki", 8, 8, 88.5)

    # 4. Odczyt
    hist = db.get_user_history(uid)
    print("Historia usera:", hist)

db.close()
