"""Маршруты приложения групп."""

from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path("", views.groups, name="list"),
    path(
        "<str:group_slug>/",
        views.group_detail,
        name="detail",
    ),
]
