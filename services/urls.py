"""Маршруты приложения сервисов."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.services, name="services"),
    path(
        "<str:service_slug>/",
        views.service_detail,
        name="service_detail",
    ),
]
