"""Логика проверки сервисов и работа со списком сервисов."""

import urllib.error
import urllib.request


def ping_service(url: str) -> tuple[bool, int]:
    """Проверить доступность сервиса по URL.

    Возвращает пару: доступен ли сервис и код HTTP-ответа.
    """
    headers = {"User-Agent": "ServiceMonitor/1.0"}
    try:
        request = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(request, timeout=5)
        return True, response.getcode()
    except urllib.error.HTTPError as exc:
        return False, exc.code
    except Exception:
        return False, 0


def get_status_text(available: bool) -> str:
    """Вернуть текстовый статус сервиса."""
    if available:
        return "Доступен"
    return "Недоступен"


def check_service_status(service: dict) -> bool:
    """Проверить и вывести статус одного сервиса.

    Возвращает True, если сервис доступен.
    """
    available, code = ping_service(service["url"])
    print(f"  {service['name']}")
    print(f"    URL: {service['url']}")
    print(f"    Статус: {get_status_text(available)} (код: {code})")
    print()
    return available


def search_services(services: list[dict], query: str) -> list[dict]:
    """Найти сервисы, в названии которых есть подстрока query."""
    query_lower = query.lower()
    found = []
    for service in services:
        if query_lower in service["name"].lower():
            found.append(service)
    return found


def sort_services(services: list[dict]) -> list[dict]:
    """Вернуть сервисы, отсортированные по названию."""
    return sorted(services, key=lambda service: service["name"].lower())
