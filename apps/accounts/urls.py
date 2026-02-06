from django.urls import path
from . import views


urlpatterns = [
    path("password_change/", views.passwordChange, name="password_change"),
    path("profile/<str:pk>/", views.userProfile, name="user-profile"),
    path("update-user/", views.updateUser, name="update-user"),
]
