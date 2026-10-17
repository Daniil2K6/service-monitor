"""Страницы сервисов: список, карточка и операции CRUD."""

import os
from concurrent.futures import ThreadPoolExecutor

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.urls import reverse

from check_result import CheckResult
from checker import find_service_by_slug, sort_services
from group import Group
from monitor import Monitor
from service import Service
from storage import (
    DATA_DIR,
    delete_service,
    load_groups,
    load_services,
    save_service,
    service_filename,
)

LAST_CHECKS: dict[str, list[CheckResult]] = {}


def restore_checks(service: Service) -> None:
    """Восстановить историю проверок сессии сервера.

    Данные ПР3 загружаются на каждый запрос заново, поэтому
    результаты проверок хранятся в памяти процесса сервера.
    """
    if service.slug in LAST_CHECKS:
        service.checks = LAST_CHECKS[service.slug]


def remember_checks(service: Service) -> None:
    """Запомнить историю проверок сервиса между запросами."""
    LAST_CHECKS[service.slug] = service.checks


def _load_monitor() -> Monitor:
    """Загрузить данные ПР3 и собрать Monitor."""
    groups_list = load_groups()
    return Monitor(load_services(groups_list), groups_list)


def _find_service(slug: str) -> Service | None:
    """Найти сервис по slug среди загруженных данных."""
    monitor = _load_monitor()
    return find_service_by_slug(monitor.services, slug)


def _is_ajax(request: HttpRequest) -> bool:
    """Запрос из JavaScript: проверка в реальном времени."""
    header = request.headers.get("X-Requested-With")
    return header == "XMLHttpRequest"


def _find_group(name: str) -> Group | None:
    """Найти группу по названию среди загруженных."""
    if not name:
        return None
    for group in load_groups():
        if group.name == name:
            return group
    return None


def services(request: HttpRequest) -> HttpResponse:
    """Список сервисов: проверка в реальном времени и CRUD."""
    monitor = _load_monitor()
    services_list = sort_services(monitor.services)
    for service in services_list:
        restore_checks(service)
    context = {
        "services": services_list,
    }
    response = render(request, "services/service_list.html", context)
    response["Cache-Control"] = "no-store"
    return response


def _check_and_remember(service: Service) -> None:
    """Проверить сервис и сохранить результат в кеш."""
    service.check()
    remember_checks(service)


def check_all(request: HttpRequest) -> HttpResponse:
    """Проверить все сервисы одновременно (без JavaScript)."""
    monitor = _load_monitor()
    for service in monitor.services:
        restore_checks(service)
    with ThreadPoolExecutor(
        max_workers=max(len(monitor.services), 1)
    ) as pool:
        list(pool.map(_check_and_remember, monitor.services))
    return HttpResponseRedirect(reverse("services:list"))


def service_check(request: HttpRequest, slug: str) -> HttpResponse:
    """Проверить сервис: JSON для веба, редирект без JS."""
    service = _find_service(slug)
    if service is None:
        if _is_ajax(request):
            return JsonResponse(
                {"error": "not found"}, status=404
            )
        return HttpResponseRedirect(reverse("services:list"))
    restore_checks(service)
    _check_and_remember(service)
    if _is_ajax(request):
        last = service.last_check()
        return JsonResponse(
            {
                "slug": service.slug,
                "badge": service.status_class,
                "status": service.status_label,
                "code": last.code if last else None,
                "checks": len(service.checks),
            }
        )
    if request.GET.get("next") == "detail":
        return HttpResponseRedirect(
            reverse("services:detail", args=[service.slug])
        )
    return HttpResponseRedirect(reverse("services:list"))


def service_create(request: HttpRequest) -> HttpResponse:
    """Создать сервис: форма и запись в data/."""
    if request.method == "POST":
        fields = {
            "name": request.POST.get("name", "").strip(),
            "url": request.POST.get("url", "").strip(),
            "description": request.POST.get(
                "description", ""
            ).strip(),
            "group_value": request.POST.get(
                "group", ""
            ).strip(),
        }
        error = ""
        if not fields["name"] or not fields["url"]:
            error = "Заполните название и URL."
        else:
            group = _find_group(fields["group_value"])
            service = Service(
                fields["name"],
                fields["url"],
                fields["description"],
                group,
            )
            if save_service(service):
                return HttpResponseRedirect(
                    reverse(
                        "services:detail",
                        args=[service.slug],
                    )
                )
            error = (
                "Сервис с таким названием уже существует."
            )
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
    return {
        "title": title,
        "submit": submit,
        "action": action,
        "groups": load_groups(),
        "name": name,
        "url": url,
        "description": description,
        "group_value": group_value,
        "error": error,
    }


def _save_updated(
    service: Service,
    name: str,
    url: str,
    description: str,
    group_value: str,
) -> tuple[Service | None, str]:
    """Перезаписать сервис, вернуть (новый объект, ошибка)."""
    new_path = os.path.join(
        DATA_DIR, service_filename(name)
    )
    if name != service.name and os.path.isfile(new_path):
        return None, (
            "Сервис с таким названием уже существует."
        )
    delete_service(service.name)
    updated = Service(
        name,
        url,
        description,
        _find_group(group_value),
    )
    if not save_service(updated):
        return None, "Не удалось сохранить сервис."
    return updated, ""


def service_edit(request: HttpRequest, slug: str) -> HttpResponse:
    """Изменить сервис: форма с данными и сохранение."""
    service = _find_service(slug)
    if service is None:
        return render(
            request,
            "services/service_detail.html",
            {"service": None},
            status=404,
        )
    if request.method == "POST":
        fields = {
            "name": request.POST.get("name", "").strip(),
            "url": request.POST.get("url", "").strip(),
            "description": request.POST.get(
                "description", ""
            ).strip(),
            "group_value": request.POST.get(
                "group", ""
            ).strip(),
        }
        error = ""
        if not fields["name"] or not fields["url"]:
            error = "Заполните название и URL."
        else:
            updated, error = _save_updated(
                service,
                fields["name"],
                fields["url"],
                fields["description"],
                fields["group_value"],
            )
            if updated is not None:
                return HttpResponseRedirect(
                    reverse(
                        "services:detail",
                        args=[updated.slug],
                    )
                )
        context = _form_context(
            f"Изменить: {service.name}",
            "Сохранить",
            reverse("services:edit", args=[slug]),
            error=error,
            **fields,
        )
        return render(request, "services/service_form.html", context)
    context = _form_context(
        f"Изменить: {service.name}",
        "Сохранить",
        reverse("services:edit", args=[slug]),
        name=service.name,
        url=service.url,
        description=service.description,
        group_value=(
            service.group.name if service.group else ""
        ),
    )
    return render(request, "services/service_form.html", context)


def service_delete(
    request: HttpRequest, slug: str
) -> HttpResponse:
    """Удалить сервис: подтверждение и запись в data/."""
    service = _find_service(slug)
    if service is None:
        return render(
            request,
            "services/service_detail.html",
            {"service": None},
            status=404,
        )
    if request.method == "POST":
        delete_service(service.name)
        return HttpResponseRedirect(reverse("services:list"))
    return render(
        request,
        "services/service_delete.html",
        {"service": service},
    )


def service_detail(
    request: HttpRequest, slug: str
) -> HttpResponse:
    """Карточка сервиса: проверка и операции CRUD."""
    service = _find_service(slug)
    if service is None:
        return render(
            request,
            "services/service_detail.html",
            {"service": None},
            status=404,
        )
    restore_checks(service)
    service.check()
    remember_checks(service)
    last = service.last_check()
    context = {
        "service": service,
        "code": last.code if last is not None else None,
        "moment": (
            last.checked_at.strftime("%d.%m.%Y %H:%M")
            if last is not None
            else None
        ),
    }
    return render(request, "services/service_detail.html", context)
