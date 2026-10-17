"""Перенос данных из JSON-файлов проекта в базу данных SQLite.

Порядок импорта важен из-за внешних ключей: сначала группы,
затем сервисы (ссылаются на группы), затем результаты проверок
(ссылаются на сервисы).
"""

import json
import os

from db.database import get_connection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCHEMA_FILE = os.path.join(BASE_DIR, "sql", "schema.sql")
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")
CHECKS_FILE = os.path.join(DATA_DIR, "checks.json")


def load_json(path: str) -> list:
    """Прочитать JSON-файл и вернуть его содержимое."""
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def slugify(name: str) -> str:
    """Идентификатор записи для URL по её названию."""
    return name.lower().replace(" ", "_")


def service_files() -> list[str]:
    """Вернуть пути ко всем JSON-файлам сервисов."""
    files = []
    for name in sorted(os.listdir(DATA_DIR)):
        if not name.endswith(".json"):
            continue
        if name in ("groups.json", "checks.json"):
            continue
        files.append(os.path.join(DATA_DIR, name))
    return files


def apply_schema(conn) -> None:
    """Выполнить sql/schema.sql (создать таблицы, если их нет)."""
    with open(SCHEMA_FILE, encoding="utf-8") as file:
        conn.executescript(file.read())


def clear_tables(conn) -> None:
    """Очистить таблицы перед повторным импортом."""
    conn.execute("DELETE FROM checks")
    conn.execute("DELETE FROM services")
    conn.execute("DELETE FROM groups")


def collect_groups(services: list) -> list:
    """Собрать группы из JSON и из ссылок сервисов."""
    groups = load_json(GROUPS_FILE)
    names = {group["name"] for group in groups}
    for service in services:
        name = service.get("group")
        if name and name not in names:
            groups.append({"name": name, "description": ""})
            names.add(name)
    return groups


def import_groups(conn, groups: list) -> dict:
    """Перенести группы и вернуть словарь «название -> id»."""
    conn.executemany(
        """
        INSERT INTO groups (id, name, slug, description)
        VALUES (?, ?, ?, ?);
        """,
        [
            (
                index,
                group["name"],
                slugify(group["name"]),
                group.get("description", ""),
            )
            for index, group in enumerate(groups, start=1)
        ],
    )
    return {
        row["name"]: row["id"]
        for row in conn.execute("SELECT id, name FROM groups")
    }


def import_services(conn, ids: dict) -> None:
    """Перенести сервисы, связав их с группами по group_id."""
    services = [
        load_json(path) for path in service_files()
    ]
    conn.executemany(
        """
        INSERT INTO services
            (id, name, slug, url, description, group_id)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        [
            (
                index,
                service["name"],
                slugify(service["name"]),
                service["url"],
                service.get("description", ""),
                ids.get(service.get("group")),
            )
            for index, service in enumerate(services, start=1)
        ],
    )


def import_checks(conn) -> None:
    """Перенести историю проверок из data/checks.json, если он есть."""
    if not os.path.exists(CHECKS_FILE):
        return
    ids = {
        row["name"]: row["id"]
        for row in conn.execute("SELECT id, name FROM services")
    }
    checks = load_json(CHECKS_FILE)
    conn.executemany(
        """
        INSERT INTO checks (id, service_id, available, code, checked_at)
        VALUES (?, ?, ?, ?, ?);
        """,
        [
            (
                index,
                ids[check["service"]],
                int(check["available"]),
                check["code"],
                check["checked_at"],
            )
            for index, check in enumerate(checks, start=1)
        ],
    )


def main() -> None:
    """Выполнить перенос данных в одной транзакции."""
    conn = get_connection()
    try:
        apply_schema(conn)
        clear_tables(conn)
        groups = collect_groups(
            [load_json(path) for path in service_files()]
        )
        ids = import_groups(conn, groups)
        import_services(conn, ids)
        import_checks(conn)
        conn.commit()
        print("Импорт данных завершён.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
