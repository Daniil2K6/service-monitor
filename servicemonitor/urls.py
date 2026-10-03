"""Корневая маршрутизация проекта."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("services/", include("services.urls")),
    path("groups/", include("groups.urls")),
]
