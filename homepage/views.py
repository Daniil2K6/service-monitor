"""Главная страница и обработчик ошибки 404."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: счётчики из базы данных и ссылки."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM services) AS services_count,
                (SELECT COUNT(*) FROM groups) AS groups_count,
                (SELECT COUNT(*) FROM checks) AS checks_count;
            """
        ).fetchone()
    finally:
        conn.close()
    context = {
        "services_count": row["services_count"],
        "groups_count": row["groups_count"],
        "checks_count": row["checks_count"],
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
