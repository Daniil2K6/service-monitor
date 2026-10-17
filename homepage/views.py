"""Каркас страниц проекта и главная страница."""

from django.http import HttpRequest, HttpResponse

from storage import load_groups, load_services

BOOTSTRAP_CSS = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
    "/dist/css/bootstrap.min.css"
)


def page(title: str, content: str) -> str:
    """Собрать HTML-страницу: каркас, меню и содержимое."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{BOOTSTRAP_CSS}">
</head>
<body>
    <nav class="nav">
        <a class="nav-link" href="/">Главная</a>
        <a class="nav-link" href="/services/">Сервисы</a>
        <a class="nav-link" href="/groups/">Группы</a>
    </nav>
    <main class="container">{content}</main>
</body>
</html>"""


def html_response(
    title: str, content: str, status: int = 200
) -> HttpResponse:
    """Собрать HTTP-ответ без кеширования.

    Заголовок Cache-Control: no-store запрещает браузеру
    показывать устаревшую копию страницы при возврате назад:
    данные перечитываются при каждом открытии.
    """
    response = HttpResponse(page(title, content), status=status)
    response["Cache-Control"] = "no-store"
    return response


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: описание и кнопки-ссылки на разделы."""
    groups = load_groups()
    services = load_services(groups)
    content = f"""
    <h1 class="display-4">ServiceMonitor</h1>
    <p class="lead">
        Мониторинг доступности веб-сервисов.
    </p>
    <p>Сервисов: {len(services)}, групп: {len(groups)}.</p>
    <a href="/services/" class="btn btn-primary me-2">Сервисы</a>
    <a href="/groups/" class="btn btn-secondary">Группы</a>
    """
    return html_response("ServiceMonitor", content)


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Собственная страница ошибки 404 для адреса без маршрута.

    Обработчик подключается переменной handler404 в корневом
    urls.py и вызывается для любого адреса, которому не нашлось
    маршрута. Аргумент exception обязателен.
    """
    content = """
    <h1 class="text-danger">404 — страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a href="/" class="btn btn-primary">На главную</a>
    """
    return html_response(
        "404 — страница не найдена", content, status=404
    )
