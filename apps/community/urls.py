from django.urls import path
from . import views


urlpatterns = [
    path("room/<str:pk>/", views.room, name="room"),  # id 전달
    path("create-room/", views.createRoom, name="create-room"),
    path("create-border/", views.createBorder, name="create-border"),  # 게시판 글 작성
    path("update-room/<str:pk>/", views.updateRoom, name="update-room"),
    path("delete-room/<str:pk>/", views.deleteRoom, name="delete-room"),
    path("delete-message/<str:pk>/", views.deleteMessage, name="delete-message"),
    path("topics/", views.topicsPage, name="topics"),
    path("activity/", views.activityPage, name="activity"),
]
