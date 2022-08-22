from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),

    path('', views.home, name="home"),
    path('room/<str:pk>/', views.room, name="room"),  # id 전달

    path('exp011/<str:pk>/', views.exp011, name="exp011"),  # id 전달

    path('profile/<str:pk>/', views.userProfile, name="user-profile"),


    path('create-room/', views.createRoom, name="create-room"),
    path('update-room/<str:pk>/', views.updateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views.deleteRoom, name="delete-room"),
    path('delete-message/<str:pk>/', views.deleteMessage, name="delete-message"),

    path('update-user/', views.updateUser, name="update-user"),

    path('topics/', views.topicsPage, name="topics"),

    path('activity/', views.activityPage, name="activity"),
    path('activity_a/<str:hname>', views.activityPage_a, name="activity_a"),
    path('activityComponent_a/<str:hname>',
         views.activityComponentPage_a, name="activityComponent_a"),

    path('race/', views.racingPage, name="race"),

]
