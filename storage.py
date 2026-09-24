"""Загрузка и сохранение сервисов в JSON-файлах."""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def service_filename(name: str) -> str:
    """Сформировать имя JSON-файла по названию сервиса."""
    safe_name = name.lower().replace(" ", "_")
    return f"{safe_name}.json"


def load_services() -> list[dict]:
    """Загрузить все сервисы из папки data.

    Некорректные файлы пропускаются, чтобы программа не падала.
    """
    services = []
    if not os.path.isdir(DATA_DIR):
        return services

    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(DATA_DIR, filename)
        try:
            with open(path, encoding="utf-8") as file:
                services.append(json.load(file))
        except FileNotFoundError:
            continue
        except json.JSONDecodeError:
            print(f"  Ошибка: файл {filename} содержит некорректный JSON")
    return services


def save_service(service: dict) -> bool:
    """Сохранить сервис в отдельный JSON-файл.

    Возвращает False, если файл уже существует.
    """
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)

    path = os.path.join(DATA_DIR, service_filename(service["name"]))
    if os.path.exists(path):
        return False

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(service, file, ensure_ascii=False, indent=2)
    except OSError:
        return False
    return True


def delete_service(name: str) -> bool:
    """Удалить JSON-файл сервиса по названию."""
    path = os.path.join(DATA_DIR, service_filename(name))
    if not os.path.exists(path):
        return False

    try:
        os.remove(path)
    except OSError:
        return False
    return True
