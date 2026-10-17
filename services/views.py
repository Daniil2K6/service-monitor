"""Страницы сервисов: список, поиск, статистика, история и CRUD.

Данные страниц получаются из базы данных SQLite запросами SQL:
представление выполняет запрос через модуль sqlite3, получает
результат (строки sqlite3.Row) и передаёт его в шаблон.
"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.urls import reverse

from db.database import get_connection
from service import Service

# Строки сервисов с названием группы и последней проверкой.
SERVICE_ROWS = """
SELECT
    s.id AS id,
    s.name AS name,
    s.url AS url,
    s.description AS description,
    s.slug AS slug,
    g.id AS group_id,
    g.name AS group_name,
    g.slug AS group_slug,
    (
        SELECT COUNT(*)
        FROM checks c
        WHERE c.service_id = s.id
    ) AS checks_count,
    lc.available AS last_available,
    lc.code AS last_code,
    lc.checked_at AS last_checked_at,
    CASE
        WHEN lc.id IS NULL THEN 'не проверялся'
        WHEN lc.available = 1 THEN 'Доступен'
        WHEN lc.code = 0 THEN 'нет ответа (таймаут)'
        ELSE 'Недоступен'
    END AS status_label,
    CASE
        WHEN lc.id IS NULL THEN 'bg-secondary'
        WHEN lc.available = 1 THEN 'bg-success'
        ELSE 'bg-danger'
    END AS status_class
FROM services s
LEFT JOIN groups g ON g.id = s.group_id
LEFT JOIN checks lc ON lc.id = (
    SELECT c.id
    FROM checks c
    WHERE c.service_id = s.id
    ORDER BY c.checked_at DESC, c.id DESC
    LIMIT 1
)
"""


def _slug(name: str) -> str:
    """Идентификатор сервиса для URL по его названию."""
    return name.lower().replace(" ", "_")


def _now() -> str:
    """Текущая дата и время для записи проверки."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _fetch_service(conn: sqlite3.Connection, slug: str):
    """Найти сервис по идентификатору из URL."""
    sql = SERVICE_ROWS + " WHERE s.slug = ?;"
    return conn.execute(sql, [slug]).fetchone()


def _perform_check(url: str) -> tuple[bool, int]:
    """Проверить доступность URL, использовав логику ПР3."""
    result = Service("check", url).check()
    return result.available, result.code


def _status_class(available: bool) -> str:
    """CSS-класс бейджа по результату проверки."""
    return "bg-success" if available else "bg-danger"


def _status_label(available: bool, code: int) -> str:
    """Текст статуса по результату проверки."""
    if available:
        return "Доступен"
    if code == 0:
        return "нет ответа (таймаут)"
    return "Недоступен"


def _is_ajax(request: HttpRequest) -> bool:
    """Запрос из JavaScript: проверка в реальном времени."""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _read_fields(request: HttpRequest) -> dict:
    """Собрать поля формы сервиса из POST-запроса."""
    return {
        "name": request.POST.get("name", "").strip(),
        "url": request.POST.get("url", "").strip(),
        "description": request.POST.get("description", "").strip(),
        "group_value": request.POST.get("group", "").strip(),
    }


def _form_context(
    title: str,
    submit: str,
    action: str,
    name: str = "",
    url: str = "",
    description: str = "",
    group_value: str = "",
    error: str = "",
) -> dict:
    """Подготовить контекст общей формы сервиса."""
    conn = get_connection()
    try:
        groups = conn.execute(
            "SELECT id, name FROM groups ORDER BY name;"
        ).fetchall()
    finally:
        conn.close()
    return {
        "title": title,
        "submit": submit,
        "action": action,
        "groups": groups,
        "name": name,
        "url": url,
        "description": description,
        "group_value": group_value,
        "error": error,
    }


def services(request: HttpRequest) -> HttpResponse:
    """Список сервисов, полученный из базы данных."""
    conn = get_connection()
    try:
        rows = conn.execute(
            SERVICE_ROWS + " ORDER BY s.name;"
        ).fetchall()
    finally:
        conn.close()
    response = render(
        request, "services/service_list.html", {"services": rows}
    )
    response["Cache-Control"] = "no-store"
    return response


def service_search(request: HttpRequest) -> HttpResponse:
    """Поиск сервисов по названию и группе (параметры в SQL)."""
    query = request.GET.get("q", "").strip()
    group_id = request.GET.get("group", "").strip()
    conn = get_connection()
    try:
        rows = []
        if query or group_id:
            conditions = []
            params = []
            if query:
                conditions.append("s.name LIKE ?")
                params.append(f"%{query}%")
            if group_id:
                conditions.append("s.group_id = ?")
                params.append(group_id)
            sql = (
                SERVICE_ROWS
                + " WHERE "
                + " AND ".join(conditions)
                + " ORDER BY s.name;"
            )
            rows = conn.execute(sql, params).fetchall()
        groups = conn.execute(
            "SELECT id, name FROM groups ORDER BY name;"
        ).fetchall()
    finally:
        conn.close()
    context = {
        "services": rows,
        "groups": groups,
        "query": query,
        "group_id": group_id,
    }
    return render(request, "services/search.html", context)


def service_statistics(request: HttpRequest) -> HttpResponse:
    """Статистика проверок: агрегаты, GROUP BY и HAVING."""
    conn = get_connection()
    try:
        per_service = conn.execute(
            """
            SELECT
                s.name AS service_name,
                COUNT(c.id) AS checks_count,
                SUM(CASE WHEN c.available = 1 THEN 1 ELSE 0 END)
                    AS available_count
            FROM services s
            LEFT JOIN checks c ON c.service_id = s.id
            GROUP BY s.id, s.name
            ORDER BY checks_count DESC, s.name;
            """
        ).fetchall()
        top_services = conn.execute(
            """
            SELECT
                s.name AS service_name,
                COUNT(c.id) AS checks_count
            FROM services s
            JOIN checks c ON c.service_id = s.id
            GROUP BY s.id, s.name
            HAVING COUNT(c.id) > ?
            ORDER BY checks_count DESC, s.name;
            """,
            [2],
        ).fetchall()
        without_checks = conn.execute(
            """
            SELECT s.name AS service_name, s.url
            FROM services s
            LEFT JOIN checks c ON c.service_id = s.id
            WHERE c.id IS NULL
            ORDER BY s.name;
            """
        ).fetchall()
        by_group = conn.execute(
            """
            SELECT
                g.name AS group_name,
                COUNT(s.id) AS services_count
            FROM groups g
            LEFT JOIN services s ON s.group_id = g.id
            GROUP BY g.id, g.name
            ORDER BY services_count DESC, g.name;
            """
        ).fetchall()
    finally:
        conn.close()
    stats = []
    for row in per_service:
        available = row["available_count"] or 0
        total = row["checks_count"]
        percent = round(available * 100 / total, 1) if total else 0.0
        stats.append(
            {
                "service_name": row["service_name"],
                "checks_count": total,
                "available_count": available,
                "percent": percent,
            }
        )
    context = {
        "statistics": stats,
        "top_services": top_services,
        "without_checks": without_checks,
        "by_group": by_group,
    }
    return render(request, "services/statistics.html", context)


def service_checks(request: HttpRequest) -> HttpResponse:
    """История проверок: соединение checks, services и groups."""
    available = request.GET.get("available", "").strip()
    where = ""
    params = []
    if available in ("0", "1"):
        where = " WHERE checks.available = ?"
        params.append(int(available))
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                checks.id AS id,
                services.name AS service_name,
                groups.name AS group_name,
                checks.available AS available,
                checks.code AS code,
                checks.checked_at AS checked_at
            FROM checks
            JOIN services ON services.id = checks.service_id
            LEFT JOIN groups ON groups.id = services.group_id
            """
            + where
            + " ORDER BY checks.checked_at DESC, checks.id DESC;",
            params,
        ).fetchall()
        summary = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(available) AS available_count
            FROM checks;
            """
        ).fetchone()
    finally:
        conn.close()
    context = {
        "checks": rows,
        "available": available,
        "total": summary["total"] or 0,
        "available_count": summary["available_count"] or 0,
    }
    return render(request, "services/check_list.html", context)


def check_all(request: HttpRequest) -> HttpResponse:
    """Проверить все сервисы и записать результаты в базу."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, url FROM services ORDER BY id;"
        ).fetchall()
        if rows:
            with ThreadPoolExecutor(max_workers=len(rows)) as pool:
                results = list(
                    pool.map(_perform_check, [row["url"] for row in rows])
                )
            moment = _now()
            conn.executemany(
                """
                INSERT INTO checks
                    (service_id, available, code, checked_at)
                VALUES (?, ?, ?, ?);
                """,
                [
                    (row["id"], int(ok), code, moment)
                    for row, (ok, code) in zip(rows, results)
                ],
            )
            conn.commit()
    finally:
        conn.close()
    return HttpResponseRedirect(reverse("services:list"))


def service_check(request: HttpRequest, slug: str) -> HttpResponse:
    """Проверить сервис: JSON для веба, редирект без JavaScript."""
    conn = get_connection()
    try:
        service = _fetch_service(conn, slug)
        if service is None:
            if _is_ajax(request):
                return JsonResponse(
                    {"error": "not found"}, status=404
                )
            return HttpResponseRedirect(reverse("services:list"))
        available, code = _perform_check(service["url"])
        conn.execute(
            """
            INSERT INTO checks
                (service_id, available, code, checked_at)
            VALUES (?, ?, ?, ?);
            """,
            [service["id"], int(available), code, _now()],
        )
        conn.commit()
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM checks WHERE service_id = ?;",
            [service["id"]],
        ).fetchone()["n"]
    finally:
        conn.close()
    if _is_ajax(request):
        return JsonResponse(
            {
                "slug": slug,
                "badge": _status_class(available),
                "status": _status_label(available, code),
                "code": code,
                "checks": count,
            }
        )
    if request.GET.get("next") == "detail":
        return HttpResponseRedirect(
            reverse("services:detail", args=[slug])
        )
    return HttpResponseRedirect(reverse("services:list"))


def service_create(request: HttpRequest) -> HttpResponse:
    """Создать сервис: запись в базу данных."""
    if request.method == "POST":
        fields = _read_fields(request)
        error = ""
        if not fields["name"] or not fields["url"]:
            error = "Заполните название и URL."
        else:
            conn = get_connection()
            try:
                conn.execute(
                    """
                    INSERT INTO services
                        (name, slug, url, description, group_id)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    [
                        fields["name"],
                        _slug(fields["name"]),
                        fields["url"],
                        fields["description"],
                        fields["group_value"] or None,
                    ],
                )
                conn.commit()
                return HttpResponseRedirect(
                    reverse(
                        "services:detail",
                        args=[_slug(fields["name"])],
                    )
                )
            except sqlite3.IntegrityError:
                error = "Сервис с таким названием уже существует."
            finally:
                conn.close()
        context = _form_context(
            "Новый сервис",
            "Добавить",
            reverse("services:create"),
            error=error,
            **fields,
        )
        return render(request, "services/service_form.html", context)
    context = _form_context(
        "Новый сервис",
        "Добавить",
        reverse("services:create"),
    )
    return render(request, "services/service_form.html", context)


def service_edit(request: HttpRequest, slug: str) -> HttpResponse:
    """Изменить сервис: обновление записи в базе данных."""
    conn = get_connection()
    try:
        service = _fetch_service(conn, slug)
        if service is None:
            return render(
                request,
                "services/service_detail.html",
                {"service": None},
                status=404,
            )
        if request.method == "POST":
            fields = _read_fields(request)
            error = ""
            if not fields["name"] or not fields["url"]:
                error = "Заполните название и URL."
            else:
                try:
                    conn.execute(
                        """
                        UPDATE services
                        SET name = ?, slug = ?, url = ?,
                            description = ?, group_id = ?
                        WHERE id = ?;
                        """,
                        [
                            fields["name"],
                            _slug(fields["name"]),
                            fields["url"],
                            fields["description"],
                            fields["group_value"] or None,
                            service["id"],
                        ],
                    )
                    conn.commit()
                    return HttpResponseRedirect(
                        reverse(
                            "services:detail",
                            args=[_slug(fields["name"])],
                        )
                    )
                except sqlite3.IntegrityError:
                    error = (
                        "Сервис с таким названием уже существует."
                    )
            context = _form_context(
                f"Изменить: {service['name']}",
                "Сохранить",
                reverse("services:edit", args=[slug]),
                error=error,
                **fields,
            )
            return render(
                request, "services/service_form.html", context
            )
        context = _form_context(
            f"Изменить: {service['name']}",
            "Сохранить",
            reverse("services:edit", args=[slug]),
            name=service["name"],
            url=service["url"],
            description=service["description"],
            group_value=str(service["group_id"] or ""),
        )
        return render(request, "services/service_form.html", context)
    finally:
        conn.close()


def service_delete(request: HttpRequest, slug: str) -> HttpResponse:
    """Удалить сервис и его проверки из базы данных."""
    conn = get_connection()
    try:
        service = _fetch_service(conn, slug)
        if service is None:
            return render(
                request,
                "services/service_detail.html",
                {"service": None},
                status=404,
            )
        if request.method == "POST":
            conn.execute(
                "DELETE FROM checks WHERE service_id = ?;",
                [service["id"]],
            )
            conn.execute(
                "DELETE FROM services WHERE id = ?;",
                [service["id"]],
            )
            conn.commit()
            return HttpResponseRedirect(reverse("services:list"))
    finally:
        conn.close()
    return render(
        request,
        "services/service_delete.html",
        {"service": service},
    )


def service_detail(
    request: HttpRequest, slug: str
) -> HttpResponse:
    """Карточка сервиса: данные и история проверок из базы."""
    conn = get_connection()
    try:
        service = _fetch_service(conn, slug)
        checks = []
        if service is not None:
            checks = conn.execute(
                """
                SELECT available, code, checked_at
                FROM checks
                WHERE service_id = ?
                ORDER BY checked_at DESC, id DESC;
                """,
                [service["id"]],
            ).fetchall()
    finally:
        conn.close()
    if service is None:
        return render(
            request,
            "services/service_detail.html",
            {"service": None},
            status=404,
        )
    context = {"service": service, "checks": checks}
    return render(request, "services/service_detail.html", context)
