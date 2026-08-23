# =============================================================
# MonTour — apps/accounts/urls.py
# =============================================================

from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,
    ProfileView, ChangePasswordView, ForgotPasswordView,
    UserListView, FCMTokenView,
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

    # Administration
    path('users/',            UserListView.as_view(),        name='user-list'),

    # Notifications push
    path('fcm-token/',        FCMTokenView.as_view(),        name='fcm-token'),
]