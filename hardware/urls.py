from django.urls import path

from . import views

app_name = "hardware"

urlpatterns = [
    path("", views.home, name="home"),
    path("despre/", views.despre, name="despre"),
    path("info/", views.info, name="info"),
    path("log/", views.log, name="log"),
    path("produse/", views.in_lucru, {"page_title": "Produse"}, name="produse"),
    path("contact/", views.in_lucru, {"page_title": "Contact"}, name="contact"),
    path("cos/", views.in_lucru, {"page_title": "Coș virtual"}, name="cos"),
    path(
        "tutoriale/",
        views.in_lucru,
        {"page_title": "Tutoriale video"},
        name="tutoriale",
    ),
]
