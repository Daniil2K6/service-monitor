"""Страницы сервисов: список, карточка и операции CRUD."""

import os
from concurrent.futures import ThreadPoolExecutor
from html import escape

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.middleware.csrf import get_token

from check_result import CheckResult
from checker import (
    find_service_by_slug,
    group_slug,
    service_slug,
    sort_services,
)
from group import Group
from homepage.views import html_response
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

SERVICES_STYLES = """
<style>
.upd-toast {
    display: inline-block;
    margin-left: 8px;
    padding: 2px 8px;
    border-radius: 4px;
    background: #198754;
    color: #fff;
    font-size: 12px;
    opacity: 0;
    transition: opacity 0.3s;
}
.upd-toast.show {
    opacity: 1;
}
</style>
"""

SERVICES_SCRIPT = """
<script>
function showToast(row) {
    const toast = row.querySelector(".upd-toast");
    toast.classList.add("show");
    setTimeout(function () {
        toast.classList.remove("show");
    }, 2000);
}
async function checkOne(row) {
    const slug = row.dataset.slug;
    const response = await fetch(
        "/services/" + slug + "/check/",
        {
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        }
    );
    const data = await response.json();
    const badge = row.querySelector(".badge");
    badge.className = "badge " + data.badge;
    badge.textContent = data.status;
    showToast(row);
}
document.querySelectorAll(".js-check").forEach(
    function (link) {
        link.addEventListener("click", function (event) {
            event.preventDefault();
            checkOne(link.closest("li"));
        });
    }
);
document.getElementById("check-all").addEventListener(
    "click",
    function (event) {
        event.preventDefault();
        document.querySelectorAll("li[data-slug]")
            .forEach(checkOne);
    }
);
</script>
"""


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
    if last.code == 0:
        return "bg-danger", "нет ответа (таймаут)"
    return "bg-danger", "Недоступен"


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


def _not_found() -> HttpResponse:
    """Страница «Сервис не найден»."""
    content = """
    <h1 class="text-danger">Сервис не найден</h1>
    <a href="/services/"
       class="btn btn-outline-secondary">
        ← к списку сервисов
    </a>
    """
    return html_response(
        "Сервис не найден", content, status=404
    )


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
    items = ""
    for service in sort_services(monitor.services):
        restore_checks(service)
        slug = service_slug(service)
        badge, status = status_badge(service)
        group_name = (
            service.group.name if service.group else "—"
        )
        text = f"{escape(service.name)} — {escape(group_name)}"
        check_url = f"/services/{slug}/check/"
        items += (
            '<li class="list-group-item d-flex'
            " justify-content-between"
            ' align-items-center flex-wrap gap-2"'
            f' data-slug="{slug}">'
            "<span>"
            f'<a href="/services/{slug}/">{text}</a>'
            '<span class="upd-toast">обновлено</span>'
            "</span>"
            '<span class="d-flex align-items-center'
            ' gap-2">'
            f'<span class="badge {badge}">{status}</span>'
            f'<a href="{check_url}"'
            ' class="btn btn-sm btn-outline-success'
            ' js-check">Проверить</a>'
            f'<a href="/services/{slug}/edit/"'
            ' class="btn btn-sm btn-outline-primary">'
            "Изменить</a>"
            f'<a href="/services/{slug}/delete/"'
            ' class="btn btn-sm btn-outline-danger">'
            "Удалить</a>"
            "</span>"
            "</li>"
        )
    content = """
    <h1>Сервисы</h1>
    <a href="/services/new/"
       class="btn btn-success mb-3">
        Добавить сервис
    </a>
    <a href="/services/check/" id="check-all"
       class="btn btn-warning mb-3">
        Проверить все сервисы
    </a>
    """
    content += f'<ul class="list-group">{items}</ul>'
    content += """
    <a href="/"
       class="btn btn-outline-secondary mt-3">
        ← на главную
    </a>
    """
    content += SERVICES_STYLES + SERVICES_SCRIPT
    return html_response("ServiceMonitor — сервисы", content)


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
    return HttpResponseRedirect("/services/")


def service_check(request: HttpRequest, slug: str) -> HttpResponse:
    """Проверить сервис: JSON для веба, редирект без JS."""
    service = _find_service(slug)
    if service is None:
        if _is_ajax(request):
            return JsonResponse(
                {"error": "not found"}, status=404
            )
        return HttpResponseRedirect("/services/")
    restore_checks(service)
    _check_and_remember(service)
    if _is_ajax(request):
        badge, status = status_badge(service)
        last = service.last_check()
        return JsonResponse(
            {
                "slug": service_slug(service),
                "badge": badge,
                "status": status,
                "code": last.code if last else None,
                "checks": len(service.checks),
            }
        )
    if request.GET.get("next") == "detail":
        return HttpResponseRedirect(
            f"/services/{service_slug(service)}/"
        )
    return HttpResponseRedirect("/services/")


def _service_form(
    request: HttpRequest,
    action: str,
    title: str,
    submit: str,
    name: str = "",
    url: str = "",
    description: str = "",
    group_value: str = "",
    error: str = "",
) -> str:
    """Собрать HTML-форму создания или изменения сервиса."""
    token = get_token(request)
    options = ['<option value="">Без группы</option>']
    for group in load_groups():
        selected = ""
        if group.name == group_value:
            selected = " selected"
        label = escape(group.name)
        options.append(
            f'<option value="{label}"{selected}>'
            f"{label}</option>"
        )
    error_html = ""
    if error:
        error_html = (
            f'<p class="text-danger">{escape(error)}</p>'
        )
    return f"""
    <h1>{escape(title)}</h1>
    {error_html}
    <form method="post" action="{action}">
        <input type="hidden"
               name="csrfmiddlewaretoken"
               value="{token}">
        <div class="mb-3">
            <label class="form-label">Название</label>
            <input class="form-control" type="text"
                   name="name"
                   value="{escape(name)}" required>
        </div>
        <div class="mb-3">
            <label class="form-label">URL</label>
            <input class="form-control" type="url"
                   name="url"
                   value="{escape(url)}" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Описание</label>
            <input class="form-control" type="text"
                   name="description"
                   value="{escape(description)}">
        </div>
        <div class="mb-3">
            <label class="form-label">Группа</label>
            <select class="form-select" name="group">
                {"".join(options)}
            </select>
        </div>
        <button class="btn btn-primary"
                type="submit">{escape(submit)}</button>
        <a class="btn btn-outline-secondary"
           href="/services/">Отмена</a>
    </form>
    """


def service_create(request: HttpRequest) -> HttpResponse:
    """Создать сервис: форма и запись в data/."""
    fields = {}
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
                slug = service_slug(service)
                return HttpResponseRedirect(
                    f"/services/{slug}/"
                )
            error = (
                "Сервис с таким названием уже существует."
            )
        form = _service_form(
            request,
            action="/services/new/",
            title="Новый сервис",
            submit="Добавить",
            error=error,
            **fields,
        )
        return html_response("Новый сервис", form)
    form = _service_form(
        request,
        action="/services/new/",
        title="Новый сервис",
        submit="Добавить",
    )
    return html_response("Новый сервис", form)


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
        return _not_found()
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
                new_slug = service_slug(updated)
                return HttpResponseRedirect(
                    f"/services/{new_slug}/"
                )
        form = _service_form(
            request,
            action=f"/services/{slug}/edit/",
            title=f"Изменить: {service.name}",
            submit="Сохранить",
            error=error,
            **fields,
        )
        return html_response("Изменение сервиса", form)
    form = _service_form(
        request,
        action=f"/services/{slug}/edit/",
        title=f"Изменить: {service.name}",
        submit="Сохранить",
        name=service.name,
        url=service.url,
        description=service.description,
        group_value=(
            service.group.name if service.group else ""
        ),
    )
    return html_response("Изменение сервиса", form)


def service_delete(
    request: HttpRequest, slug: str
) -> HttpResponse:
    """Удалить сервис: подтверждение и запись в data/."""
    service = _find_service(slug)
    if service is None:
        return _not_found()
    if request.method == "POST":
        delete_service(service.name)
        return HttpResponseRedirect("/services/")
    token = get_token(request)
    name = escape(service.name)
    url = escape(service.url)
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">Удалить сервис?</h5>
            <p class="card-text">{name} — {url}</p>
            <form method="post"
                  action="/services/{slug}/delete/">
                <input type="hidden"
                       name="csrfmiddlewaretoken"
                       value="{token}">
                <button class="btn btn-danger"
                        type="submit">Удалить</button>
                <a class="btn btn-outline-secondary"
                   href="/services/{slug}/">Отмена</a>
            </form>
        </div>
    </div>
    """
    return html_response("Удаление сервиса", content)


def service_detail(
    request: HttpRequest, slug: str
) -> HttpResponse:
    """Карточка сервиса: проверка и операции CRUD."""
    service = _find_service(slug)
    if service is None:
        return _not_found()
    restore_checks(service)
    service.check()
    remember_checks(service)
    badge, status = status_badge(service)
    last = service.last_check()
    name = escape(service.name)
    url = escape(service.url)
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
        f'<li class="list-group-item">{escape(str(r))}</li>'
        for r in service.checks
    )
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">{name}</h5>
            <p class="card-text">
                <strong>URL:</strong>
                <a href="{url}">{url}</a>
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
                <strong>Последняя проверка:</strong>
                {moment}
            </p>
            <p class="card-text">
                <strong>Проверок:</strong> {len(service.checks)}
            </p>
            <h6>История проверок</h6>
            <ul class="list-group">{history}</ul>
            <div class="mt-3">
                <a href="/services/{slug}/check/?next=detail"
                   class="btn btn-success">
                    Проверить
                </a>
                <a href="/services/{slug}/edit/"
                   class="btn btn-primary">
                    Изменить
                </a>
                <a href="/services/{slug}/delete/"
                   class="btn btn-outline-danger">
                    Удалить
                </a>
                <a href="/services/"
                   class="btn btn-outline-secondary">
                    ← к списку
                </a>
            </div>
        </div>
    </div>
    """
    return html_response(
        f"ServiceMonitor — {escape(service.name)}", content
    )
