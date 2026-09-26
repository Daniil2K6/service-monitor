"""Тесты класса Group."""

from group import Group
from service import Service


def test_group_attributes() -> None:
    group = Group("Мессенджеры", "Общение")
    assert group.name == "Мессенджеры"
    assert group.description == "Общение"
    assert group.services == []


def test_group_add_and_remove_service() -> None:
    group = Group("G")
    service = Service("Test", "https://example.com", group=group)
    group.add_service(service)
    assert service in group.services
    group.add_service(service)
    assert len(group.services) == 1
    group.remove_service(service)
    assert service not in group.services


def test_group_str_contains_name() -> None:
    group = Group("Поиск")
    text = str(group)
    assert "Поиск" in text
    assert "сервисов: 0" in text
