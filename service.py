"""Класс Service: сущность сервиса и его история проверок."""

import urllib.error
import urllib.request

from check_result import CheckResult
from group import Group


class Service:
    """Сервис: принадлежит группе и хранит историю проверок."""

    def __init__(
        self,
        name: str,
        url: str,
        description: str = "",
        group: Group | None = None,
    ) -> None:
        """Инициализировать сервис и связать его с группой."""
        self.name = name
        self.url = url
        self.description = description
        self.group = group
        self.checks: list[CheckResult] = []
        self._available = False
        self._code = 0

    @property
    def available(self) -> bool:
        """Доступен ли сервис после последней проверки."""
        return self._available

    def record_result(
        self, available: bool, code: int
    ) -> CheckResult:
        """Сохранить результат проверки в историю сервиса."""
        self._available = available
        self._code = code
        result = CheckResult(self, available, code)
        self.checks.append(result)
        return result

    def last_check(self) -> CheckResult | None:
        """Последний результат проверки или None."""
        if self.checks:
            return self.checks[-1]
        return None

    def check(self) -> CheckResult:
        """Проверить сервис и записать результат в историю."""
        headers = {"User-Agent": "ServiceMonitor/1.0"}
        try:
            request = urllib.request.Request(self.url, headers=headers)
            response = urllib.request.urlopen(request, timeout=5)
            return self.record_result(True, response.getcode())
        except urllib.error.HTTPError as exc:
            return self.record_result(False, exc.code)
        except Exception:
            return self.record_result(False, 0)

    def get_status_text(self) -> str:
        """Вернуть текстовый статус сервиса."""
        if self._available:
            return "Доступен"
        return "Недоступен"

    def to_dict(self) -> dict:
        """Преобразовать объект в словарь для сохранения в JSON."""
        group_name = self.group.name if self.group else ""
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "group": group_name,
        }

    @classmethod
    def from_dict(
        cls, data: dict, groups: list[Group]
    ) -> "Service":
        """Создать сервис из JSON и связать его с группой.

        Если группы с таким названием ещё нет, она создаётся.
        """
        group_name = data.get("group") or "Без группы"
        group = None
        for item in groups:
            if item.name == group_name:
                group = item
                break
        if group is None:
            group = Group(group_name)
            groups.append(group)
        return cls(
            name=data["name"],
            url=data["url"],
            description=data.get("description", ""),
            group=group,
        )

    def __str__(self) -> str:
        """Строковое представление сервиса со статусом."""
        group_name = self.group.name if self.group else "—"
        last = self.last_check()
        history = ""
        if last is not None:
            history = f", проверок: {len(self.checks)}"
        return (
            f"  {self.name}\n"
            f"    URL: {self.url}\n"
            f"    Группа: {group_name}\n"
            f"    Статус: {self.get_status_text()}"
            f" (код: {self._code}){history}"
        )
