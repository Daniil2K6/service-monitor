"""Маршруты приложения сервисов."""

from django.urls import path

from . import views

app_name = "services"

urlpatterns = [
    path("", views.services, name="list"),
    path("check/", views.check_all, name="check_all"),
    path("new/", views.service_create, name="create"),
    path(
        "<str:slug>/check/",
        views.service_check,
        name="check",
    ),
    path(
        "<str:slug>/edit/",
        views.service_edit,
        name="edit",
    ),
    path(
        "<str:slug>/delete/",
        views.service_delete,
        name="delete",
    ),
    path(
        "<str:slug>/",
        views.service_detail,
        name="detail",
    ),
]
