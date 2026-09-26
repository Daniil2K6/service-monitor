"""Тесты функций-запросов над коллекциями."""

from checker import (
    collect_results,
    count_available,
    percent_available,
    search_services,
    sort_services,
)
from group import Group
from service import Service


def make_services() -> list[Service]:
    group = Group("G")
    return [
        Service("YouTube", "https://www.youtube.com", group=group),
        Service("Telegram", "https://telegram.org", group=group),
        Service("Apple", "https://www.apple.com", group=group),
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


def test_collect_results_from_history() -> None:
    services = make_services()
    services[0].record_result(True, 200)
    services[0].record_result(False, 0)
    services[2].record_result(True, 200)
    results = collect_results(services)
    assert len(results) == 3
    assert all(r.service in services for r in results)


def test_collect_results_empty() -> None:
    assert collect_results(make_services()) == []


def test_count_available() -> None:
    services = make_services()
    services[0].record_result(True, 200)
    services[1].record_result(False, 0)
    results = collect_results(services)
    assert count_available(results) == 1


def test_percent_available() -> None:
    service = Service("A", "https://a.com")
    service.record_result(True, 200)
    service.record_result(True, 200)
    service.record_result(False, 0)
    results = collect_results([service])
    assert percent_available(results) == 66.7


def test_percent_available_empty() -> None:
    assert percent_available([]) == 0.0
