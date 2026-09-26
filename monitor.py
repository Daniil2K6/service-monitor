"""Класс Monitor: система мониторинга и связи между сущностями."""

from group import Group
from service import Service


class Monitor:
    """Система мониторинга: группы, сервисы и проверки.

    Monitor отвечает за целостность связей: каждый сервис
    состоит в группе, каждая группа знает свои сервисы.
    """

    def __init__(
        self, services: list[Service], groups: list[Group]
    ) -> None:
        """Принять сервисы и группы, восстановить связи."""
        self.services = services
        self.groups = groups
        for service in services:
            group = service.group
            if group is None:
                group = Group("Без группы")
                service.group = group
            if group not in self.groups:
                self.groups.append(group)
            group.add_service(service)

    def get_or_create_group(self, name: str) -> Group:
        """Найти группу по названию или создать новую."""
        for group in self.groups:
            if group.name == name:
                return group
        group = Group(name)
        self.groups.append(group)
        return group

    def add_service(self, service: Service) -> None:
        """Добавить сервис и установить связь с группой."""
        self.services.append(service)
        if service.group is None:
            service.group = self.get_or_create_group("Без группы")
        if service.group not in self.groups:
            self.groups.append(service.group)
        service.group.add_service(service)

    def remove_service(self, service: Service) -> None:
        """Удалить сервис и разорвать связь с группой."""
        if service in self.services:
            self.services.remove(service)
        if service.group is not None:
            service.group.remove_service(service)

    def check_all(self) -> None:
        """Проверить все сервисы, записывая CheckResult."""
        print("\n=== Мониторинг сервисов ===\n")
        if not self.services:
            print("  Список сервисов пуст.\n")
            return
        for service in self.services:
            service.check()
            print(service)
            print()

    def check_one(self, service: Service) -> None:
        """Проверить один сервис и вывести результат."""
        service.check()
        print(service)
        print()
