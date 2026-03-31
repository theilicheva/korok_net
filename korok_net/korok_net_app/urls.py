from django.urls import path

from . import views


urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("main/", views.HomeView.as_view(), name="main"),
    path("registration/", views.RegistrationView.as_view(), name="registration"),
    path("authorization/", views.AuthorizationView.as_view(), name="authorization"),
    path("admin-login/", views.AdminLoginView.as_view(), name="admin_login"),
    path("admin-panel/", views.AdminPanelView.as_view(), name="admin_panel"),
    path("logout/", views.logout_user, name="logout"),
    path("user_applications/", views.ApplicationsView.as_view(), name="user_applications"),
    path("check-username/", views.CheckUsernameView.as_view(), name="check_username"),
    path("check-email/", views.CheckEmailView.as_view(), name="check_email"),
]
