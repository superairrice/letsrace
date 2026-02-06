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
