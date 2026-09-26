"""Тесты класса Monitor: связи между сущностями."""

from group import Group
from monitor import Monitor
from service import Service


def test_monitor_restores_group_relations() -> None:
    group = Group("G")
    service = Service("A", "https://a.com", group=group)
    monitor = Monitor([service], [])
    assert group in monitor.groups
    assert service in group.services
    assert service.group is group


def test_monitor_assigns_missing_group() -> None:
    service = Service("A", "https://a.com")
    Monitor([service], [])
    assert service.group is not None
    assert service in service.group.services


def test_get_or_create_group_existing() -> None:
    group = Group("G")
    monitor = Monitor([], [group])
    assert monitor.get_or_create_group("G") is group
    assert len(monitor.groups) == 1


def test_get_or_create_group_new() -> None:
    monitor = Monitor([], [])
    group = monitor.get_or_create_group("Новая")
    assert group in monitor.groups
    assert monitor.get_or_create_group("Новая") is group


def test_add_service_updates_both_sides() -> None:
    group = Group("G")
    monitor = Monitor([], [group])
    service = Service("A", "https://a.com", group=group)
    monitor.add_service(service)
    assert service in monitor.services
    assert service in group.services


def test_remove_service_updates_both_sides() -> None:
    group = Group("G")
    service = Service("A", "https://a.com", group=group)
    monitor = Monitor([service], [group])
    monitor.remove_service(service)
    assert service not in monitor.services
    assert service not in group.services


def test_check_all_records_results(
    monkeypatch, capsys
) -> None:
    group = Group("G")
    service = Service("A", "https://a.com", group=group)
    monitor = Monitor([service], [group])
    monkeypatch.setattr(
        Service, "check", lambda self: self.record_result(True, 200)
    )
    monitor.check_all()
    assert service.last_check().code == 200
    assert service.last_check().service is service
    assert "A" in capsys.readouterr().out


def test_check_one_records_result(monkeypatch, capsys) -> None:
    service = Service("A", "https://a.com", group=Group("G"))
    monitor = Monitor([service], [service.group])
    monkeypatch.setattr(
        Service, "check", lambda self: self.record_result(False, 503)
    )
    monitor.check_one(service)
    assert service.last_check().code == 503
    assert "Недоступен" in capsys.readouterr().out
