"""Тесты функций проверки и поиска сервисов."""

from checker import (
    get_status_text,
    search_services,
    sort_services,
)


def test_get_status_text_available() -> None:
    assert get_status_text(True) == "Доступен"


def test_get_status_text_unavailable() -> None:
    assert get_status_text(False) == "Недоступен"


def test_search_services_found() -> None:
    services = [
        {"name": "YouTube", "url": "https://www.youtube.com"},
        {"name": "Telegram", "url": "https://telegram.org"},
    ]
    found = search_services(services, "tube")
    assert len(found) == 1
    assert found[0]["name"] == "YouTube"


def test_search_services_not_found() -> None:
    services = [{"name": "YouTube", "url": "https://www.youtube.com"}]
    assert search_services(services, "discord") == []


def test_search_services_case_insensitive() -> None:
    services = [{"name": "YouTube", "url": "https://www.youtube.com"}]
    assert len(search_services(services, "TUBE")) == 1


def test_sort_services_by_name() -> None:
    services = [
        {"name": "YouTube", "url": ""},
        {"name": "Apple", "url": ""},
        {"name": "Google", "url": ""},
    ]
    names = [service["name"] for service in sort_services(services)]
    assert names == ["Apple", "Google", "YouTube"]


def test_sort_services_empty() -> None:
    assert sort_services([]) == []
