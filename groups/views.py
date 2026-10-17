"""Страницы групп: список и карточка."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from checker import (
    collect_results,
    count_available,
    find_group_by_slug,
    percent_available,
)
from monitor import Monitor
from services.views import restore_checks
from storage import load_groups, load_services


def _load_monitor() -> Monitor:
    """Загрузить данные ПР3 и собрать Monitor."""
    groups_list = load_groups()
    return Monitor(load_services(groups_list), groups_list)


def groups(request: HttpRequest) -> HttpResponse:
    """Список групп сервисов."""
    monitor = _load_monitor()
    context = {
        "groups": monitor.groups,
    }
    return render(request, "groups/group_list.html", context)


def group_detail(
    request: HttpRequest, group_slug: str
) -> HttpResponse:
    """Карточка группы: описание, сервисы и статистика."""
    monitor = _load_monitor()
    group = find_group_by_slug(monitor.groups, group_slug)

    if group is None:
        return render(
            request,
            "groups/group_detail.html",
            {"group": None},
            status=404,
        )

    for service in group.services:
        restore_checks(service)
    results = collect_results(group.services)
    context = {
        "group": group,
        "services": group.services,
        "total_results": len(results),
        "available": count_available(results),
        "percent": percent_available(results),
    }
    return render(request, "groups/group_detail.html", context)
