import sqlite3 as sq
from createbot import *
import datetime
from loggers import database_logger


def sql_start():
    global base, cur

    base = sq.connect('database.db')
    cur = base.cursor()
    if base:
        database_logger.info('База данных подключена')

    base.execute('CREATE TABLE IF NOT EXISTS Users(user_id INTEGER PRIMARY KEY, username TEXT, register_date DATETIME, is_blocked INTEGER DEFAULT 0)')
    base.commit()
    # Migration: add is_blocked if it doesn't exist (in case the table already exists)
    try:
        base.execute('ALTER TABLE Users ADD COLUMN is_blocked INTEGER DEFAULT 0')
        base.commit()
    except sq.OperationalError:
        pass # Column already exists

    base.execute('CREATE TABLE IF NOT EXISTS Messages(message_id INTEGER PRIMARY KEY, recipient INTEGER, sender INTEGER, content TEXT, register_date DATETIME)')
    base.commit()


async def sql_add_id(message) -> None:
    id_user = message.from_user.id
    username = message.from_user.username
    if (id_user,) not in cur.execute('SELECT user_id FROM Users').fetchall():
        current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        base.execute('INSERT INTO Users (user_id, username, register_date) VALUES (?, ?, ?)', (id_user, username, current_timestamp))
        base.commit()
        database_logger.info(f"Пользователь {id_user}-{username} добавлен в базу данных.")


async def sql_add_message(message, content, recipient_id) -> None:
    user_id = message.from_user.id
    msg_id = message.message_id
    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    base.execute('INSERT INTO Messages (message_id, recipient, sender, content, register_date) VALUES (?, ?, ?, ?, ?)', (msg_id, recipient_id, user_id, content, current_timestamp))
    base.commit()
    database_logger.info(f"Сообщение {msg_id} добавлено в базу данных. Маршрут сообщения от {user_id} -> {recipient_id}")


async def sql_select_id(identifier):
    if identifier is None:
        return None

    if isinstance(identifier, int):
        return cur.execute('SELECT user_id FROM Users WHERE user_id = (?)', (identifier,)).fetchone()

    identifier_str = str(identifier)
    if identifier_str.startswith("id:"):
        try:
            identifier_value = int(identifier_str.split(":", 1)[1])
            return cur.execute('SELECT user_id FROM Users WHERE user_id = (?)', (identifier_value,)).fetchone()
        except ValueError:
            return None

    return cur.execute('SELECT user_id FROM Users WHERE username = (?)', (identifier_str,)).fetchone()


async def sql_is_blocked(user_id: int) -> bool:
    res = cur.execute('SELECT is_blocked FROM Users WHERE user_id = (?)', (user_id,)).fetchone()
    return bool(res[0]) if res else False


async def sql_set_block_status(user_id: int, status: int) -> None:
    base.execute('UPDATE Users SET is_blocked = ? WHERE user_id = ?', (status, user_id))
    base.commit()


async def sql_get_all_users():
    return cur.execute('SELECT user_id FROM Users').fetchall()


async def sql_get_user_info(user_id: int):
    return cur.execute('SELECT user_id, username, register_date, is_blocked FROM Users WHERE user_id = ?', (user_id,)).fetchone()
