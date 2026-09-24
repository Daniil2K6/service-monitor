"""Тесты сохранения и загрузки сервисов."""

import json
import os

import storage


def test_load_services_empty_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    assert storage.load_services() == []


def test_save_and_delete_service(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    service = {
        "name": "TestSite",
        "url": "https://example.com",
        "description": "тест",
    }

    assert storage.save_service(service) is True

    path = os.path.join(str(tmp_path), "testsite.json")
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as file:
        assert json.load(file)["name"] == "TestSite"

    assert storage.delete_service("TestSite") is True
    assert not os.path.exists(path)


def test_save_duplicate_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    service = {
        "name": "TestSite",
        "url": "https://example.com",
        "description": "",
    }
    assert storage.save_service(service) is True
    assert storage.save_service(service) is False


def test_delete_missing_service(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    assert storage.delete_service("NoSuch") is False


def test_load_services_skips_bad_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))

    bad_path = os.path.join(str(tmp_path), "bad.json")
    with open(bad_path, "w", encoding="utf-8") as file:
        file.write("{не json")

    good = {"name": "Ok", "url": "https://example.com", "description": ""}
    good_path = os.path.join(str(tmp_path), "ok.json")
    with open(good_path, "w", encoding="utf-8") as file:
        json.dump(good, file, ensure_ascii=False)

    services = storage.load_services()
    assert len(services) == 1
    assert services[0]["name"] == "Ok"


def test_service_filename() -> None:
    assert storage.service_filename("My Service") == "my_service.json"
