from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegistrationView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profil/", views.ProfileView.as_view(), name="profile"),
    path("profil/editare/", views.ProfileUpdateView.as_view(), name="profile_update"),
    path("parola/", views.UserPasswordChangeView.as_view(), name="password_change"),
]
