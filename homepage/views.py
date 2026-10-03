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
    return HttpResponse(page("ServiceMonitor", content))
