"""Страницы сервисов: список и карточка."""

from django.http import HttpRequest, HttpResponse

from check_result import CheckResult
from checker import (
    find_service_by_slug,
    group_slug,
    service_slug,
    sort_services,
)
from homepage.views import page
from monitor import Monitor
from service import Service
from storage import load_groups, load_services

LAST_CHECKS: dict[str, list[CheckResult]] = {}


def restore_checks(service: Service) -> None:
    """Восстановить историю проверок сессии сервера.

    Данные ПР3 загружаются на каждый запрос заново, поэтому
    результаты проверок хранятся в памяти процесса сервера.
    """
    slug = service_slug(service)
    if slug in LAST_CHECKS:
        service.checks = LAST_CHECKS[slug]


def remember_checks(service: Service) -> None:
    """Запомнить историю проверок сервиса между запросами."""
    LAST_CHECKS[service_slug(service)] = service.checks


def status_badge(service: Service) -> tuple[str, str]:
    """Класс бейджа и текст статуса по последней проверке."""
    last = service.last_check()
    if last is None:
        return "bg-secondary", "не проверялся"
    if last.available:
        return "bg-success", "Доступен"
    return "bg-danger", "Недоступен"


def services(request: HttpRequest) -> HttpResponse:
    """Список всех сервисов, отсортированный по названию."""
    groups_list = load_groups()
    monitor = Monitor(load_services(groups_list), groups_list)
    items = ""
    for service in sort_services(monitor.services):
        restore_checks(service)
        slug = service_slug(service)
        badge, status = status_badge(service)
        group_name = service.group.name if service.group else "—"
        text = f"{service.name} — {group_name}"
        items += (
            '<li class="list-group-item d-flex'
            ' justify-content-between align-items-center">'
            f'<a href="/services/{slug}/">{text}</a>'
            f'<span class="badge {badge}">{status}</span>'
            "</li>"
        )
    content = f"""
    <h1>Сервисы</h1>
    <ul class="list-group">{items}</ul>
    <a href="/"
       class="btn btn-outline-secondary mt-3">
        ← на главную
    </a>
    """
    return HttpResponse(
        page("ServiceMonitor – сервисы", content)
    )


def service_detail(
    request: HttpRequest, service_slug: str
) -> HttpResponse:
    """Карточка сервиса: данные и проверка доступности."""
    groups_list = load_groups()
    monitor = Monitor(load_services(groups_list), groups_list)
    service = find_service_by_slug(
        monitor.services, service_slug
    )

    if service is None:
        content = """
        <h1 class="text-danger">Сервис не найден</h1>
        <a href="/services/"
           class="btn btn-outline-secondary">
            ← к списку сервисов
        </a>
        """
        return HttpResponse(
            page("Сервис не найден", content),
            status=404,
        )

    restore_checks(service)
    service.check()
    remember_checks(service)
    badge, status = status_badge(service)
    last = service.last_check()
    group_name = service.group.name if service.group else "—"
    if service.group is not None:
        group_url = f"/groups/{group_slug(service.group)}/"
    else:
        group_url = "/groups/"
    code = last.code if last is not None else "—"
    moment = "—"
    if last is not None:
        moment = last.checked_at.strftime("%d.%m.%Y %H:%M")
    description = service.description or "—"
    history = "".join(
        f'<li class="list-group-item">{result}</li>'
        for result in service.checks
    )
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">{service.name}</h5>
            <p class="card-text">
                <strong>URL:</strong>
                <a href="{service.url}">{service.url}</a>
            </p>
            <p class="card-text">
                <strong>Группа:</strong>
                <a href="{group_url}">{group_name}</a>
            </p>
            <p class="card-text">
                <strong>Описание:</strong> {description}
            </p>
            <p class="card-text">
                <strong>Статус:</strong>
                <span class="badge {badge}">{status}</span>
            </p>
            <p class="card-text">
                <strong>Код ответа:</strong> {code}
            </p>
            <p class="card-text">
                <strong>Последняя проверка:</strong> {moment}
            </p>
            <p class="card-text">
                <strong>Проверок:</strong> {len(service.checks)}
            </p>
            <h6>История проверок</h6>
            <ul class="list-group">{history}</ul>
            <a href="/services/"
               class="btn btn-outline-secondary mt-3">
                ← к списку сервисов
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(service.name, content))
