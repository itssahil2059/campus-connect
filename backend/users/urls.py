from django.urls import path

from .views import LoginView, LogoutView, MeView, SignupView, VerifyEmailView

app_name = "users"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("verify/<str:uidb64>/<str:token>/", VerifyEmailView.as_view(), name="verify"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
