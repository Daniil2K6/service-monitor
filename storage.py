"""Загрузка и сохранение групп и сервисов в JSON-файлах."""

import json
import os

from group import Group
from service import Service

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def service_filename(name: str) -> str:
    """Сформировать имя JSON-файла по названию сервиса."""
    safe_name = name.lower().replace(" ", "_")
    return f"{safe_name}.json"


def load_groups() -> list[Group]:
    """Загрузить группы сервисов из data/groups.json."""
    path = os.path.join(DATA_DIR, "groups.json")
    groups = []
    if not os.path.exists(path):
        return groups
    try:
        with open(path, encoding="utf-8") as file:
            items = json.load(file)
        for item in items:
            groups.append(
                Group(item["name"], item.get("description", ""))
            )
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"  Ошибка: groups.json повреждён ({exc})")
    return groups


def load_services(groups: list[Group]) -> list[Service]:
    """Создать объекты Service из JSON и связать их с группами.

    Некорректные файлы пропускаются, чтобы программа не падала.
    """
    services = []
    if not os.path.isdir(DATA_DIR):
        return services

    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".json"):
            continue
        if filename == "groups.json":
            continue
        path = os.path.join(DATA_DIR, filename)
        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
            services.append(Service.from_dict(data, groups))
        except FileNotFoundError:
            continue
        except json.JSONDecodeError:
            print(f"  Ошибка: файл {filename} — неверный JSON")
        except KeyError as exc:
            print(f"  Ошибка: в файле {filename} нет поля {exc}")
    return services


def save_service(service: Service) -> bool:
    """Сохранить сервис в JSON-файл вместе с именем группы.

    Возвращает False, если файл уже существует.
    """
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)

    path = os.path.join(DATA_DIR, service_filename(service.name))
    if os.path.exists(path):
        return False

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(service.to_dict(), file, ensure_ascii=False, indent=2)
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
