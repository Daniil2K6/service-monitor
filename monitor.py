"""Класс Monitor: система мониторинга и связи между сущностями."""

from concurrent.futures import ThreadPoolExecutor, as_completed

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
        """Проверить все сервисы одновременно.

        Запросы уходят всем адресам параллельно: даже если
        часть сервисов отвечает до таймаута 10 секунд,
        общее время проверки равно времени самого медленного
        адреса. Результаты печатаются по мере поступления
        ответов — не дожидаясь завершения всех проверок.
        """
        print("\n=== Мониторинг сервисов ===\n")
        if not self.services:
            print("  Список сервисов пуст.\n")
            return
        with ThreadPoolExecutor(
            max_workers=max(len(self.services), 1)
        ) as pool:
            futures = {
                pool.submit(service.check): service
                for service in self.services
            }
            for future in as_completed(futures):
                future.result()
                print(futures[future])
                print()

    def check_one(self, service: Service) -> None:
        """Проверить один сервис и вывести результат."""
        service.check()
        print(service)
        print()
