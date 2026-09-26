"""Класс Group: группа сервисов."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service import Service


class Group:
    """Группа, к которой принадлежат сервисы (связь 1:N)."""

    def __init__(self, name: str, description: str = "") -> None:
        """Инициализировать группу названием и описанием."""
        self.name = name
        self.description = description
        self.services: list[Service] = []

    def add_service(self, service: Service) -> None:
        """Добавить сервис в группу (связь группа -> сервис)."""
        if service not in self.services:
            self.services.append(service)

    def remove_service(self, service: Service) -> None:
        """Убрать сервис из группы."""
        if service in self.services:
            self.services.remove(service)

    def __str__(self) -> str:
        """Строковое представление группы."""
        count = len(self.services)
        return f"  {self.name} (сервисов: {count})"
