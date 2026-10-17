"""Главная страница и обработчик ошибки 404."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from storage import load_groups, load_services


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: описание и ссылки на разделы."""
    groups = load_groups()
    services = load_services(groups)
    context = {
        "services_count": len(services),
        "groups_count": len(groups),
    }
    return render(request, "homepage/index.html", context)


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Собственная страница ошибки 404 для адреса без маршрута.

    Обработчик подключается переменной handler404 в корневом
    urls.py и вызывается для любого адреса, которому не нашлось
    маршрута. Аргумент exception обязателен.
    """
    return render(request, "homepage/404.html", status=404)
