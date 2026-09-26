"""Тесты класса CheckResult."""

from check_result import CheckResult
from group import Group
from service import Service


def make_service() -> Service:
    return Service("Test", "https://example.com", group=Group("G"))


def test_check_result_attributes() -> None:
    service = make_service()
    result = CheckResult(service, True, 200)
    assert result.service is service
    assert result.available is True
    assert result.code == 200
    assert result.checked_at is not None


def test_check_result_str() -> None:
    service = make_service()
    result = CheckResult(service, False, 503)
    text = str(result)
    assert "Недоступен" in text
    assert "503" in text


def test_record_result_appends_to_history() -> None:
    service = make_service()
    result = service.record_result(True, 200)
    assert isinstance(result, CheckResult)
    assert service.checks == [result]
    assert result.service is service
    assert service.available is True
    assert service.get_status_text() == "Доступен"


def test_record_result_unavailable() -> None:
    service = make_service()
    service.record_result(False, 0)
    assert service.available is False
    assert service.get_status_text() == "Недоступен"
    assert len(service.checks) == 1
