"""Функции обработки коллекций сервисов."""

from service import Service


def search_services(services: list[Service], query: str) -> list[Service]:
    """Найти сервисы, в названии которых есть подстрока query."""
    query_lower = query.lower()
    found = []
    for service in services:
        if query_lower in service.name.lower():
            found.append(service)
    return found


def sort_services(services: list[Service]) -> list[Service]:
    """Вернуть сервисы, отсортированные по названию."""
    return sorted(services, key=lambda service: service.name.lower())
