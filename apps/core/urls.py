from django.urls import path
from . import views


urlpatterns = [
    # path('left-page/', views.leftPage, name="left-page"),               # 메인화면 왼쪽 view
    # path('center-page/', views.centerPage, name="center-page"),         # 메인화면 가운데 view
    # path('right-page/', views.rightPage, name="right-page"),            # 메인화면 오른쪽 view
    path("race/", views.racingPage, name="race"),
    path("left_component/", views.leftPage, name="left_component"),
    path("right_component/", views.rightPage, name="right_component"),
    # path(
    #     "prediction_race/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>",
    #     views.predictionRace,
    #     name="prediction_race",
    # ),  # 로그인 후
    # path(
    #     "prediction_list/<str:rcity>/<str:rdate>/<int:rno>",
    #     views.predictionList,
    #     name="prediction_list",
    # ),  # 로그인 전
    
    
    path("pyscript_test/", views.pyscriptTest, name="pyscript_test"),
    path("exp011/<str:pk>/", views.exp011, name="exp011"),
    path("", views.home, name="home"),
    path("send_email/", views.send_email, name="send_email"),
    # path(
    #     "thethe9_ranks/<str:rcity>/<str:fdate>/<str:tdate>/<str:jockey>/<str:trainer>/<str:host>/<str:horse>/<int:r1>/<int:r2>/<int:rr1>/<int:rr2>/<int:gate>",
    #     views.thethe9Ranks,
    #     name="thethe9_ranks",
    # ),
]
