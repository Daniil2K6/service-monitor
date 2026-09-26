"""Класс CheckResult: результат одной проверки сервиса."""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service import Service


class CheckResult:
    """Результат проверки одного сервиса в момент времени."""

    def __init__(
        self, service: "Service", available: bool, code: int
    ) -> None:
        """Связать результат с сервисом и записать итог проверки."""
        self.service = service
        self.available = available
        self.code = code
        self.checked_at = datetime.now()

    def __str__(self) -> str:
        """Строковое представление результата."""
        status = "Доступен" if self.available else "Недоступен"
        moment = self.checked_at.strftime("%d.%m.%Y %H:%M")
        return f"{status} (код: {self.code}) от {moment}"
