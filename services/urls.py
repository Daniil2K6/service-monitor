"""Маршруты приложения сервисов."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.services, name="services"),
    path("check/", views.check_all, name="check_all"),
    path("new/", views.service_create, name="service_create"),
    path(
        "<str:slug>/check/",
        views.service_check,
        name="service_check",
    ),
    path(
        "<str:slug>/edit/",
        views.service_edit,
        name="service_edit",
    ),
    path(
        "<str:slug>/delete/",
        views.service_delete,
        name="service_delete",
    ),
    path(
        "<str:slug>/",
        views.service_detail,
        name="service_detail",
    ),
]
