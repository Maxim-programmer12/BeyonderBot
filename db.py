import sqlite3
from traceback import print_exc
from pathlib import Path
from typing import Union, List

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db.db"
# коннектимся к БД.
def connect(func):
    def wrapper(*args, **kwargs):
        connection = sqlite3.connect(str(DB_DIR))
        cur = connection.cursor()
        result = None

        try:
            result = func(cur, *args, **kwargs)
            connection.commit()

        except Exception:
            print(f"[ERROR] {func.__name__}: {print_exc()}")
            connection.rollback()

        finally:
            connection.close()

        return result
    return wrapper
# создаём таблицу в БД.
@connect
def create_table(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username VARCHAR(50) UNIQUE,
        user_id INTEGER NOT NULL,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_date DATE DEFAULT NULL,
        coins INTEGER DEFAULT 0,
        win INTEGER DEFAULT 0
    )""")
# добавляем пользователя в БД.
@connect
def insert_user(cur, username : Union[str], user_id : Union[int], reg_date : Union[str]) -> Union[None]:
    cur.execute("""
    INSERT OR REPLACE INTO users(username, user_id, reg_date)
    VALUES (?, ?, ?)
    """, (username, user_id, reg_date))
# возвращаем список id всех пользователей в БД.
@connect
def get_all_users_id(cur) -> List[int]:
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()

    list_users = list()

    for row in rows:
        list_users.append(*row)
    
    return list_users
# возвращаем дату пользователя по айди.
@connect
def get_user_info(cur, user_id  : Union[int]) -> Union[str]:
    cur.execute("SELECT username, coins, win, reg_date FROM users WHERE user_id = ?", 
                (user_id,))
    
    return cur.fetchone()
# изменяем условный 'баланс' пользователя.
@connect
def set_balance(cur, user_id : Union[int], coins : Union[int]):
    cur.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    old_coins = cur.fetchone()

    new_balance = coins + old_coins[0]

    cur.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_balance, user_id))
# изменяем кол-во побед пользователя.
@connect
def set_win(cur, user_id : Union[int], win : Union[str]):
    cur.execute("SELECT win FROM users WHERE user_id = ?", (user_id,))
    old_win = cur.fetchone()

    new_win = win + old_win[0]

    cur.execute("UPDATE users SET win = ? WHERE user_id = ?", (new_win, user_id))

if __name__ == "__main__":
    # create_table()
    # insert_user("Максим", 56, "24-03-2026")
    # insert_user("Дмитрий", 45, "23-03-2026")
    print(get_all_users_id())
    # print(get_user_info(56))
    # set_balance(56, 100)
    # set_win(56, 10)