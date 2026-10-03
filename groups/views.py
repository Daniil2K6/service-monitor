"""Страницы групп: список и карточка."""

from django.http import HttpRequest, HttpResponse

from checker import (
    collect_results,
    count_available,
    find_group_by_slug,
    group_slug,
    percent_available,
    service_slug,
)
from homepage.views import page
from monitor import Monitor
from services.views import restore_checks, status_badge
from storage import load_groups, load_services


def groups(request: HttpRequest) -> HttpResponse:
    """Список групп сервисов."""
    groups_list = load_groups()
    monitor = Monitor(load_services(groups_list), groups_list)
    items = ""
    for group in monitor.groups:
        slug = group_slug(group)
        count = len(group.services)
        items += (
            '<li class="list-group-item d-flex'
            ' justify-content-between align-items-center">'
            f'<a href="/groups/{slug}/">{group.name}</a>'
            '<span class="badge bg-primary">'
            f"сервисов: {count}</span>"
            "</li>"
        )
    content = f"""
    <h1>Группы</h1>
    <ul class="list-group">{items}</ul>
    <a href="/"
       class="btn btn-outline-secondary mt-3">
        ← на главную
    </a>
    """
    return HttpResponse(page("ServiceMonitor – группы", content))


def group_detail(
    request: HttpRequest, group_slug: str
) -> HttpResponse:
    """Карточка группы: описание, сервисы и статистика."""
    groups_list = load_groups()
    monitor = Monitor(load_services(groups_list), groups_list)
    group = find_group_by_slug(monitor.groups, group_slug)

    if group is None:
        content = """
        <h1 class="text-danger">Группа не найдена</h1>
        <a href="/groups/"
           class="btn btn-outline-secondary">
            ← к списку групп
        </a>
        """
        return HttpResponse(
            page("Группа не найдена", content),
            status=404,
        )

    items = ""
    for service in group.services:
        restore_checks(service)
        slug = service_slug(service)
        badge, status = status_badge(service)
        items += (
            '<li class="list-group-item d-flex'
            ' justify-content-between align-items-center">'
            f'<a href="/services/{slug}/">{service.name}</a>'
            f'<span class="badge {badge}">{status}</span>'
            "</li>"
        )
    results = collect_results(group.services)
    available = count_available(results)
    percent = percent_available(results)
    description = group.description or "—"
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">{group.name}</h5>
            <p class="card-text">
                <strong>Описание:</strong> {description}
            </p>
            <p class="card-text">
                <strong>Сервисов:</strong>
                {len(group.services)}
            </p>
            <p class="card-text">
                <strong>Проверок:</strong> {len(results)},
                доступно: {available} ({percent}%)
            </p>
            <h6>Сервисы группы</h6>
            <ul class="list-group">{items}</ul>
            <a href="/groups/"
               class="btn btn-outline-secondary mt-3">
                ← к списку групп
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(group.name, content))
