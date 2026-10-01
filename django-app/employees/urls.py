from django.urls import path

from . import views


urlpatterns = [
    path("health", views.health),
    path("employees", views.employees),
    path("employees/<int:id>", views.employee_detail),
]