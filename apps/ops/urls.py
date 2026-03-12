from django.urls import path
from . import views


urlpatterns = [
    path(
        "mock_audit/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>/",
        views.mockAudit,
        name="mock_audit",
    ),
    path(
        "mock_accept/<str:rcity>/<str:rdate>/<int:rno>/",
        views.mockAccept,
        name="mock_accept",
    ),
    path("exec_chatGPT/<str:rcity>/<str:rdate>/<int:rno>/", views.execChatGPT, name="exec_chatGPT"),
    path("exec_chatGPT_v2/<str:rcity>/<str:rdate>/<int:rno>/", views.execChatGPTv2, name="exec_chatGPT_v2"),
    path("exec_chatGPT_v3/<str:rcity>/<str:rdate>/<int:rno>/", views.execChatGPTv3, name="exec_chatGPT_v3"),
    path("exec_chatGPT_v4/<str:rcity>/<str:rdate>/<int:rno>/", views.execChatGPTv4, name="exec_chatGPT_v4"),
    path("exec_chatGPT_v5/<str:rcity>/<str:rdate>/<int:rno>/", views.execChatGPTv5, name="exec_chatGPT_v5"),
    path("exec_chatGPT_v6/<str:rcity>/<str:rdate>/<int:rno>/", views.execChatGPTv6, name="exec_chatGPT_v6"),
    path(
        "update_popularity/<str:rcity>/<str:rdate>/<int:rno>",
        views.updatePopularity,
        name="update_popularity",
    ),
    path(
        "update_changed_race/<str:rcity>/<str:rdate>/<int:rno>",
        views.updateChangedRace,
        name="update_changed_race",
    ),
    path(
        "write_significant/<str:rdate>/<str:horse>",
        views.writeSignificant,
        name="write_significant",
    ),
]
