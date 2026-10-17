"""Подключение Python к базе данных SQLite проекта."""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "servicemonitor.sqlite")


def get_connection() -> sqlite3.Connection:
    """Создать соединение с базой данных.

    Функция настраивает доступ к полям результата по именам
    (sqlite3.Row) и включает проверку внешних ключей
    (PRAGMA foreign_keys = ON).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
