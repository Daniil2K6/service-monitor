"""Тесты класса Service."""

from group import Group
from service import Service


def test_service_attributes() -> None:
    group = Group("Соцсети")
    service = Service(
        "YouTube", "https://www.youtube.com", "Видео", group
    )
    assert service.name == "YouTube"
    assert service.url == "https://www.youtube.com"
    assert service.description == "Видео"
    assert service.group is group
    assert service.checks == []
    assert service.available is False


def test_service_default_description() -> None:
    service = Service("Test", "https://example.com")
    assert service.description == ""
    assert service.group is None


def test_last_check_none_without_history() -> None:
    service = Service("Test", "https://example.com")
    assert service.last_check() is None


def test_last_check_returns_latest() -> None:
    service = Service("Test", "https://example.com")
    service.record_result(False, 0)
    service.record_result(True, 200)
    assert service.last_check().code == 200
    assert len(service.checks) == 2


def test_to_dict_contains_group_name() -> None:
    group = Group("Поиск")
    service = Service("Yandex", "https://yandex.com", "Поисковая", group)
    assert service.to_dict() == {
        "name": "Yandex",
        "url": "https://yandex.com",
        "description": "Поисковая",
        "group": "Поиск",
    }


def test_from_dict_links_existing_group() -> None:
    group = Group("Поиск")
    groups = [group]
    data = {
        "name": "Yandex",
        "url": "https://yandex.com",
        "description": "",
        "group": "Поиск",
    }
    service = Service.from_dict(data, groups)
    assert service.group is group
    assert len(groups) == 1


def test_from_dict_creates_missing_group() -> None:
    groups = []
    data = {"name": "X", "url": "https://x.com", "group": "Новая"}
    service = Service.from_dict(data, groups)
    assert service.group.name == "Новая"
    assert groups == [service.group]


def test_from_dict_without_group() -> None:
    groups = []
    data = {"name": "X", "url": "https://x.com"}
    service = Service.from_dict(data, groups)
    assert service.group.name == "Без группы"


def test_dict_roundtrip() -> None:
    groups = [Group("G")]
    data = {
        "name": "X",
        "url": "https://x.com",
        "description": "d",
        "group": "G",
    }
    restored = Service.from_dict(data, groups)
    assert restored.to_dict() == data
    assert restored.group is groups[0]


def test_str_contains_name_and_group() -> None:
    group = Group("Поиск")
    service = Service("Yandex", "https://yandex.com", group=group)
    text = str(service)
    assert "Yandex" in text
    assert "Поиск" in text
    assert "Недоступен" in text
