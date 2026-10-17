"""Страницы групп: список и карточка.

Данные получаются из базы данных SQLite запросами SQL с
соединением таблиц (JOIN) и группировкой (GROUP BY).
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection
from services.views import SERVICE_ROWS


def groups(request: HttpRequest) -> HttpResponse:
    """Список групп с числом сервисов в каждой."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                g.id AS id,
                g.name AS name,
                g.description AS description,
                g.slug AS slug,
                COUNT(s.id) AS services_count
            FROM groups g
            LEFT JOIN services s ON s.group_id = g.id
            GROUP BY g.id, g.name, g.description, g.slug
            ORDER BY g.name;
            """
        ).fetchall()
    finally:
        conn.close()
    return render(request, "groups/group_list.html", {"groups": rows})


def group_detail(
    request: HttpRequest, group_slug: str
) -> HttpResponse:
    """Карточка группы: описание, сервисы и статистика проверок."""
    conn = get_connection()
    try:
        group = conn.execute(
            """
            SELECT
                g.id AS id,
                g.name AS name,
                g.description AS description,
                g.slug AS slug
            FROM groups g
            WHERE g.slug = ?;
            """,
            [group_slug],
        ).fetchone()
        services = []
        stats = {"total": 0, "available": 0}
        if group is not None:
            services = conn.execute(
                SERVICE_ROWS + " WHERE g.id = ? ORDER BY s.name;",
                [group["id"]],
            ).fetchall()
            stats = conn.execute(
                """
                SELECT
                    COUNT(c.id) AS total,
                    SUM(CASE WHEN c.available = 1 THEN 1 ELSE 0 END)
                        AS available
                FROM checks c
                JOIN services s ON s.id = c.service_id
                WHERE s.group_id = ?;
                """,
                [group["id"]],
            ).fetchone()
    finally:
        conn.close()
    if group is None:
        return render(
            request,
            "groups/group_detail.html",
            {"group": None},
            status=404,
        )
    total = stats["total"] or 0
    available = stats["available"] or 0
    percent = round(available * 100 / total, 1) if total else 0.0
    context = {
        "group": group,
        "services": services,
        "total_results": total,
        "available": available,
        "percent": percent,
    }
    return render(request, "groups/group_detail.html", context)
