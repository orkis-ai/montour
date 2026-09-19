# =============================================================
# MonTour — apps/accounts/urls.py
# =============================================================

from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,
    ProfileView, ChangePasswordView, ForgotPasswordView,
    UserListView, FCMTokenView, VerifyEmailView, ResendVerificationView,
    ResetPasswordView,
)

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('register/',         RegisterView.as_view(),       name='register'),
    path('login/',            LoginView.as_view(),           name='login'),
    path('logout/',           LogoutView.as_view(),          name='logout'),

    # Profil
    path('me/',               ProfileView.as_view(),         name='profile'),
    path('change-password/',  ChangePasswordView.as_view(),  name='change-password'),
    path('forgot-password/',  ForgotPasswordView.as_view(),  name='forgot-password'),
    path('reset-password/',   ResetPasswordView.as_view(),   name='reset-password'),

    # Administration
    path('users/',            UserListView.as_view(),        name='user-list'),

    # Notifications push
    path('fcm-token/',              FCMTokenView.as_view(),              name='fcm-token'),

    # Vérification email
    path('verify-email/',           VerifyEmailView.as_view(),           name='verify-email'),
    path('resend-verification/',    ResendVerificationView.as_view(),    name='resend-verification'),
]