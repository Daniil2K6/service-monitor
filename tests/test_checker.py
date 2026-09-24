"""Тесты функций обработки коллекций и класса Monitor."""

from checker import search_services, sort_services
from monitor import Monitor
from service import Service


def make_services() -> list[Service]:
    return [
        Service("YouTube", "https://www.youtube.com"),
        Service("Telegram", "https://telegram.org"),
        Service("Apple", "https://www.apple.com"),
    ]


def test_search_services_found() -> None:
    found = search_services(make_services(), "tube")
    assert len(found) == 1
    assert found[0].name == "YouTube"


def test_search_services_not_found() -> None:
    assert search_services(make_services(), "discord") == []


def test_search_services_case_insensitive() -> None:
    assert len(search_services(make_services(), "TUBE")) == 1


def test_sort_services_by_name() -> None:
    names = [s.name for s in sort_services(make_services())]
    assert names == ["Apple", "Telegram", "YouTube"]


def test_sort_services_empty() -> None:
    assert sort_services([]) == []


def test_monitor_stores_objects() -> None:
    monitor = Monitor(make_services())
    assert all(isinstance(s, Service) for s in monitor.services)
    assert len(monitor.services) == 3


def test_monitor_find() -> None:
    monitor = Monitor(make_services())
    found = monitor.find("apple")
    assert len(found) == 1
    assert found[0].name == "Apple"


def test_monitor_ordered() -> None:
    monitor = Monitor(make_services())
    names = [s.name for s in monitor.ordered()]
    assert names == ["Apple", "Telegram", "YouTube"]


def test_monitor_add_and_remove() -> None:
    monitor = Monitor([])
    service = Service("Test", "https://example.com")
    monitor.add(service)
    assert len(monitor.services) == 1
    monitor.remove(service)
    assert len(monitor.services) == 0
