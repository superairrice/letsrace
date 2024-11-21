from django.urls import include, path
from . import views


urlpatterns = [
    path("login/", views.loginPage, name="login"),
    path("logout/", views.logoutUser, name="logout"),
    path("register/", views.registerPage, name="register"),
    path("password_change/", views.passwordChange, name="password_change"),
    path("awards/", views.awards, name="awards"),
    path("room/<str:pk>/", views.room, name="room"),  # id 전달
    path("profile/<str:pk>/", views.userProfile, name="user-profile"),
    path("create-room/", views.createRoom, name="create-room"),
    path("create-border/", views.createBorder, name="create-border"),  # 게시판 글 작성
    path("update-room/<str:pk>/", views.updateRoom, name="update-room"),
    path("delete-room/<str:pk>/", views.deleteRoom, name="delete-room"),
    path("delete-message/<str:pk>/", views.deleteMessage, name="delete-message"),
    path("update-user/", views.updateUser, name="update-user"),
    path("topics/", views.topicsPage, name="topics"),
    path("activity/", views.activityPage, name="activity"),
    # path('left-page/', views.leftPage, name="left-page"),               # 메인화면 왼쪽 view
    # path('center-page/', views.centerPage, name="center-page"),         # 메인화면 가운데 view
    # path('right-page/', views.rightPage, name="right-page"),            # 메인화면 오른쪽 view
    path("race/", views.racingPage, name="race"),
    path("left_component/", views.leftPage, name="left_component"),
    path("right_component/", views.rightPage, name="right_component"),
    path("activity_a/<str:hname>", views.activityPage_a, name="activity_a"),
    path(
        "activityComponent_a/<str:hname>",
        views.activityComponentPage_a,
        name="activityComponent_a",
    ),
    path("home_a/<str:rcity>/<str:rdate>", views.homePage_a, name="home_a"),
    path(
        "race_prediction/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>",
        views.racePrediction,
        name="race_prediction",
    ),  # 로그인 후
    path(
        "race_training/<str:rcity>/<str:rdate>/<int:rno>",
        views.raceTraining,
        name="race_training",
    ),
    path(
        "race_judged/<str:rcity>/<str:rdate>/<int:rno>",
        views.raceJudged,
        name="race_judged",
    ),
    path(
        "race_related/<str:rcity>/<str:rdate>/<int:rno>",
        views.raceRelated,
        name="race_related",
    ),
    path(
        "race_related_info/<str:rcity>/<str:rdate>/<int:rno>",
        views.raceRelatedInfo,
        name="race_related_info",
    ),
    path(
        "training_awardee/<str:rdate>/<str:awardee>/<str:name>",
        views.trainingAwardee,
        name="training_awardee",
    ),
    path(
        "training_horse/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>",
        views.trainingHorse,
        name="training_horse", 
    ),
    path(
        "prediction_race/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>",
        views.predictionRace,
        name="prediction_race",
    ),  # 로그인 후
    path(
        "prediction_list/<str:rcity>/<str:rdate>/<int:rno>",
        views.predictionList,
        name="prediction_list",
    ),  # 로그인 전
    path(
        "race_result/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:rcity1>/<str:rdate1>/<int:rno1>",
        views.raceResult,
        name="race_result",
    ),
    path(
        "race_simulation/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>",
        views.raceSimulation,
        name="race_simulation",
    ),
    path(
        "status_stable/<str:rcity>/<str:rdate>/<int:rno>",
        views.statusStable,
        name="status_stable",
    ),
    path(
        "race_train/<str:rcity>/<str:rdate>/<int:rno>",
        views.raceTrain,
        name="race_train",
    ),
    path(
        "print_prediction/", views.printPrediction, name="print_prediction"
    ),  # 경주일별 예상 순위 리스트 프린터
    path(
        "award_status_trainer/", views.awardStatusTrainer, name="award_status_trainer"
    ),
    path("award_status_jockey/", views.awardStatusJockey, name="award_status_jockey"),
    path("data_management/", views.dataManagement, name="data_management"),
    path("race_breakingnews/", views.raceBreakingNews, name="race_breakingnews"),
    path("krafile_input/", views.krafileInput, name="krafile_input"),
    path("breakingnews_input/", views.BreakingNewsInput, name="breakingnews_input"),
    path("pyscript_test/", views.pyscriptTest, name="pyscript_test"),
    path("exp011/<str:pk>/", views.exp011, name="exp011"),
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
        "race_report/<str:rcity>/<str:rdate>/<int:rno>",
        views.raceReport,
        name="race_report",
    ),
    path("", views.home, name="home"),
    path("send_email/", views.send_email, name="send_email"),
    path(
        "trend_winning_rate/<str:rcity>/<str:rdate>/<int:rno>/<str:awardee>/<str:i_filter>",
        views.trendWinningRate,
        name="trend_winning_rate",
    ),
    path(
        "cycle_winning_rate/<str:rcity>/<str:rdate>/<int:rno>/<str:awardee>/<str:i_filter>",
        views.cycleWinningRate,
        name="cycle_winning_rate",
    ),
    path(
        "weeks_status/<str:rcity>/<str:rdate>", views.weeksStatus, name="weeks_status"
    ),
    # path(
    #     "thethe9_ranks/<str:rcity>/<str:fdate>/<str:tdate>/<str:jockey>/<str:trainer>/<str:host>/<str:horse>/<int:r1>/<int:r2>/<int:rr1>/<int:rr2>/<int:gate>",
    #     views.thethe9Ranks,
    #     name="thethe9_ranks",
    # ),
    path(
        "jt_analysis/<str:rcity>/<str:fdate>/<str:tdate>/<str:jockey>/<str:trainer>/<str:host>/<str:horse>/<int:r1>/<int:r2>/<int:rr1>/<int:rr2>/<int:gate>/<int:distance>/<str:handycap>",
        views.jtAnalysis,
        name="jt_analysis",
    ),
    path(
        "jt_analysis_jockey/<str:rcity>/<str:fdate>/<str:tdate>/<str:jockey>/<str:trainer>/<str:host>/<str:jockey_b>/<int:r1>/<int:r2>/<int:rr1>/<int:rr2>/<int:gate>/<int:distance>/<str:handycap>/<int:rno>",
        views.jtAnalysisJockey,
        name="jt_analysis_jockey",
    ),
    path(
        "jt_analysis_multi/<str:rcity>/<str:fdate>/<str:tdate>/<str:jockey>/<str:trainer>/<str:host>/<str:jockey_b>/<int:r1>/<int:r2>/<int:rr1>/<int:rr2>/<int:gate>/<int:distance>/<str:handycap>/<int:rno>/<str:start>",
        views.jtAnalysisMulti,
        name="jt_analysis_multi",
    ),
    path(
        "get_race_awardee/<str:rdate>/<str:awardee>/<str:i_name>/<str:i_jockey>/<str:i_trainer>/<str:i_host>",
        views.getRaceAwardee,
        name="get_race_awardee",
    ),
    path(
        "get_race_horse/<str:rdate>/<str:awardee>/<str:i_name>/<str:i_jockey>/<str:i_trainer>/<str:i_host>",
        views.getRaceHorse,
        name="get_race_horse",
    ),
    path(
        "write_significant/<str:rdate>/<str:horse>",
        views.writeSignificant,
        name="write_significant",
    ),
]
