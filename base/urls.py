from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),

    path('', views.home, name="home"),
    path('awards/', views.awards, name="awards"),


    path('room/<str:pk>/', views.room, name="room"),  # id 전달
    path('profile/<str:pk>/', views.userProfile, name="user-profile"),

    path('create-room/', views.createRoom, name="create-room"),
    path('update-room/<str:pk>/', views.updateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views.deleteRoom, name="delete-room"),
    path('delete-message/<str:pk>/', views.deleteMessage, name="delete-message"),

    path('update-user/', views.updateUser, name="update-user"),

    path('topics/', views.topicsPage, name="topics"),

    path('activity/', views.activityPage, name="activity"),


    # path('left-page/', views.leftPage, name="left-page"),               # 메인화면 왼쪽 view 
    # path('center-page/', views.centerPage, name="center-page"),         # 메인화면 가운데 view 
    # path('right-page/', views.rightPage, name="right-page"),            # 메인화면 오른쪽 view 



    path('race/', views.racingPage, name="race"),

    path('activity_a/<str:hname>', views.activityPage_a, name="activity_a"),
    path('activityComponent_a/<str:hname>', views.activityComponentPage_a, name="activityComponent_a"),

    path('home_a/<str:rcity>/<str:rdate>', views.homePage_a, name="home_a"),

    path('prediction_race/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>', views.prediction_race, name="prediction_race"),  # id 전달



    path('exp011/<str:pk>/', views.exp011, name="exp011"),  # id 전달

    path('update_popularity/<str:rcity>/<str:rdate>/<int:rno>', views.update_popularity, name="update_popularity"),
    
]

