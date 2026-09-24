"""Класс Monitor: управление коллекцией сервисов."""

from checker import search_services, sort_services
from service import Service


class Monitor:
    """Мониторинг: хранит сервисы и управляет их проверками."""

    def __init__(self, services: list[Service]) -> None:
        """Принять список сервисов для отслеживания."""
        self._services = services

    @property
    def services(self) -> list[Service]:
        """Список отслеживаемых сервисов."""
        return self._services

    def check_all(self) -> None:
        """Проверить все сервисы и вывести результат."""
        print("\n=== Мониторинг сервисов ===\n")
        if not self._services:
            print("  Список сервисов пуст.\n")
            return

        for service in self._services:
            service.check()
            print(service)
            print()

    def check_one(self, service: Service) -> None:
        """Проверить один сервис и вывести результат."""
        service.check()
        print(service)
        print()

    def find(self, query: str) -> list[Service]:
        """Найти сервисы по подстроке названия."""
        return search_services(self._services, query)

    def ordered(self) -> list[Service]:
        """Сервисы, отсортированные по названию."""
        return sort_services(self._services)

    def add(self, service: Service) -> None:
        """Добавить сервис в коллекцию."""
        self._services.append(service)

    def remove(self, service: Service) -> None:
        """Удалить сервис из коллекции."""
        self._services.remove(service)
