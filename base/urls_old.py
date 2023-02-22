from django.urls import path
from . import views_20230221

urlpatterns = [
    path('login/', views_20230221.loginPage, name="login"),
    path('logout/', views_20230221.logoutUser, name="logout"),
    path('register/', views_20230221.registerPage, name="register"),

    path('', views_20230221.home, name="home"),
    path('room/<str:pk>/', views_20230221.room, name="room"),  # id 전달

    path('exp011/<str:pk>/', views_20230221.exp011, name="exp011"),  # id 전달

    path('profile/<str:pk>/', views_20230221.userProfile, name="user-profile"),


    path('create-room/', views_20230221.createRoom, name="create-room"),
    path('update-room/<str:pk>/', views_20230221.updateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views_20230221.deleteRoom, name="delete-room"),
    path('delete-message/<str:pk>/', views_20230221.deleteMessage, name="delete-message"),

    path('update-user/', views_20230221.updateUser, name="update-user"),

    path('topics/', views_20230221.topicsPage, name="topics"),

    path('activity/', views_20230221.activityPage, name="activity"),
    path('activity_a/<str:hname>', views_20230221.activityPage_a, name="activity_a"),
    path('activityComponent_a/<str:hname>',
         views_20230221.activityComponentPage_a, name="activityComponent_a"),

    path('race/', views_20230221.racingPage, name="race"),

]
