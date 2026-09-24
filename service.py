"""Класс Service: сущность сервиса для мониторинга."""

import urllib.error
import urllib.request


class Service:
    """Сервис, доступность которого отслеживается."""

    def __init__(self, name: str, url: str, description: str = "") -> None:
        """Инициализировать сервис названием, адресом и описанием."""
        self.name = name
        self.url = url
        self.description = description
        self._available = False
        self._code = 0

    @property
    def available(self) -> bool:
        """Доступен ли сервис после последней проверки."""
        return self._available

    def check(self) -> bool:
        """Проверить доступность сервиса по HTTP.

        Результат сохраняется в объект: доступность и код ответа.
        """
        headers = {"User-Agent": "ServiceMonitor/1.0"}
        try:
            request = urllib.request.Request(self.url, headers=headers)
            response = urllib.request.urlopen(request, timeout=5)
            self._code = response.getcode()
            self._available = True
        except urllib.error.HTTPError as exc:
            self._code = exc.code
            self._available = False
        except Exception:
            self._code = 0
            self._available = False
        return self._available

    def get_status_text(self) -> str:
        """Вернуть текстовый статус сервиса."""
        if self._available:
            return "Доступен"
        return "Недоступен"

    def to_dict(self) -> dict:
        """Преобразовать объект в словарь для сохранения в JSON."""
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Service":
        """Создать объект из словаря, прочитанного из JSON."""
        return cls(
            name=data["name"],
            url=data["url"],
            description=data.get("description", ""),
        )

    def __str__(self) -> str:
        """Строковое представление сервиса с результатом проверки."""
        return (
            f"  {self.name}\n"
            f"    URL: {self.url}\n"
            f"    Статус: {self.get_status_text()} (код: {self._code})"
        )
