"""Тесты загрузки и сохранения групп и сервисов."""

import json
import os

import storage
from service import Service


def test_load_groups_empty_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    assert storage.load_groups() == []


def test_load_groups_from_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    items = [{"name": "G1", "description": "Первая"}]
    path = os.path.join(str(tmp_path), "groups.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(items, file, ensure_ascii=False)

    groups = storage.load_groups()
    assert len(groups) == 1
    assert groups[0].name == "G1"
    assert groups[0].description == "Первая"


def test_save_and_delete_service(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    groups = []
    service = Service.from_dict(
        {
            "name": "TestSite",
            "url": "https://example.com",
            "description": "тест",
            "group": "G1",
        },
        groups,
    )

    assert storage.save_service(service) is True

    path = os.path.join(str(tmp_path), "testsite.json")
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    assert data["name"] == "TestSite"
    assert data["group"] == "G1"

    assert storage.delete_service("TestSite") is True
    assert not os.path.exists(path)


def test_save_duplicate_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    service = Service("TestSite", "https://example.com")
    assert storage.save_service(service) is True
    assert storage.save_service(service) is False


def test_delete_missing_service(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    assert storage.delete_service("NoSuch") is False


def test_load_services_links_groups(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    groups_path = os.path.join(str(tmp_path), "groups.json")
    with open(groups_path, "w", encoding="utf-8") as file:
        json.dump([{"name": "G1"}], file, ensure_ascii=False)

    service = {
        "name": "Ok",
        "url": "https://example.com",
        "description": "",
        "group": "G1",
    }
    path = os.path.join(str(tmp_path), "ok.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(service, file, ensure_ascii=False)

    groups = storage.load_groups()
    services = storage.load_services(groups)
    assert len(services) == 1
    assert isinstance(services[0], Service)
    assert services[0].group is groups[0]


def test_load_services_skips_groups_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    path = os.path.join(str(tmp_path), "groups.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump([{"name": "G"}], file, ensure_ascii=False)

    assert storage.load_services([]) == []


def test_load_services_skips_bad_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    bad = os.path.join(str(tmp_path), "bad.json")
    with open(bad, "w", encoding="utf-8") as file:
        file.write("{не json")

    good = {"name": "Ok", "url": "https://example.com"}
    path = os.path.join(str(tmp_path), "ok.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(good, file, ensure_ascii=False)

    services = storage.load_services([])
    assert len(services) == 1
    assert services[0].name == "Ok"
    assert services[0].group.name == "Без группы"


def test_service_filename() -> None:
    assert storage.service_filename("My Service") == "my_service.json"
