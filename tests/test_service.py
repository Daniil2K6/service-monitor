"""Тесты класса Service."""

from service import Service


def test_service_attributes() -> None:
    service = Service("YouTube", "https://www.youtube.com", "Видео")
    assert service.name == "YouTube"
    assert service.url == "https://www.youtube.com"
    assert service.description == "Видео"
    assert service.available is False


def test_service_default_description() -> None:
    service = Service("Test", "https://example.com")
    assert service.description == ""


def test_get_status_text_available() -> None:
    service = Service("Test", "https://example.com")
    service._available = True
    assert service.get_status_text() == "Доступен"


def test_get_status_text_unavailable() -> None:
    service = Service("Test", "https://example.com")
    assert service.get_status_text() == "Недоступен"


def test_to_dict() -> None:
    service = Service("YouTube", "https://www.youtube.com", "Видео")
    data = service.to_dict()
    assert data == {
        "name": "YouTube",
        "url": "https://www.youtube.com",
        "description": "Видео",
    }


def test_from_dict() -> None:
    data = {"name": "Test", "url": "https://example.com", "description": "d"}
    service = Service.from_dict(data)
    assert isinstance(service, Service)
    assert service.name == "Test"
    assert service.description == "d"


def test_dict_roundtrip() -> None:
    service = Service("YouTube", "https://www.youtube.com", "Видео")
    restored = Service.from_dict(service.to_dict())
    assert restored.name == service.name
    assert restored.url == service.url
    assert restored.description == service.description


def test_from_dict_without_description() -> None:
    data = {"name": "Test", "url": "https://example.com"}
    service = Service.from_dict(data)
    assert service.description == ""


def test_str_contains_name_and_status() -> None:
    service = Service("YouTube", "https://www.youtube.com")
    text = str(service)
    assert "YouTube" in text
    assert "https://www.youtube.com" in text
    assert "Недоступен" in text
