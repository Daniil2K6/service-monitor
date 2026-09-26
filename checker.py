"""Чистые функции обработки коллекций сервисов и результатов.

Это запросы над коллекциями (как SQL-запросы к таблицам):
функции не меняют объекты и не дублируют методы Monitor.
"""

from check_result import CheckResult
from service import Service


def search_services(
    services: list[Service], query: str
) -> list[Service]:
    """Найти сервисы, в названии которых есть подстрока query."""
    query_lower = query.lower()
    return [s for s in services if query_lower in s.name.lower()]


def sort_services(services: list[Service]) -> list[Service]:
    """Вернуть сервисы, отсортированные по названию."""
    return sorted(services, key=lambda s: s.name.lower())


def collect_results(
    services: list[Service],
) -> list[CheckResult]:
    """Собрать всю историю проверок по коллекции сервисов."""
    results = []
    for service in services:
        results.extend(service.checks)
    return results


def count_available(results: list[CheckResult]) -> int:
    """Посчитать успешные проверки в списке результатов."""
    return len([r for r in results if r.available])


def percent_available(results: list[CheckResult]) -> float:
    """Доля успешных проверок в процентах."""
    if not results:
        return 0.0
    available = count_available(results)
    return round(available * 100 / len(results), 1)
