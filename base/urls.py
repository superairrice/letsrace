from django.urls import path
from . import views_20230221

urlpatterns = [
    path('login/', views_20230221.loginPage, name="login"),
    path('logout/', views_20230221.logoutUser, name="logout"),
    path('register/', views_20230221.registerPage, name="register"),

    path('', views_20230221.home, name="home"),
    path('awards/', views_20230221.awards, name="awards"),


    path('room/<str:pk>/', views_20230221.room, name="room"),  # id 전달
    path('profile/<str:pk>/', views_20230221.userProfile, name="user-profile"),

    path('create-room/', views_20230221.createRoom, name="create-room"),
    path('update-room/<str:pk>/', views_20230221.updateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views_20230221.deleteRoom, name="delete-room"),
    path('delete-message/<str:pk>/', views_20230221.deleteMessage, name="delete-message"),

    path('update-user/', views_20230221.updateUser, name="update-user"),

    path('topics/', views_20230221.topicsPage, name="topics"),

    path('activity/', views_20230221.activityPage, name="activity"),


    # path('left-page/', views.leftPage, name="left-page"),               # 메인화면 왼쪽 view
    # path('center-page/', views.centerPage, name="center-page"),         # 메인화면 가운데 view
    # path('right-page/', views.rightPage, name="right-page"),            # 메인화면 오른쪽 view

    path('race/', views_20230221.racingPage, name="race"),

    path('left_component/', views_20230221.leftPage, name="left_component"),
    path('right_component/', views_20230221.rightPage, name="right_component"),

    path('activity_a/<str:hname>', views_20230221.activityPage_a, name="activity_a"),
    path('activityComponent_a/<str:hname>',
         views_20230221.activityComponentPage_a, name="activityComponent_a"),

    path('home_a/<str:rcity>/<str:rdate>', views_20230221.homePage_a, name="home_a"),

    path('prediction_race/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>',
         views_20230221.predictionRace, name="prediction_race"),  # id 전달
    path('race_result/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>',
         views_20230221.raceResult, name="race_result"),  # id 전달
    path('race_train/<str:rcity>/<str:rdate>/<int:rno>',
         views_20230221.raceTrain, name="race_train"),  # id 전달


    path('print_prediction/', views_20230221.printPrediction,
         name="print_prediction"),  # 경주일별 예상 순위 리스트 프린터

    path('award_status_trainer/', views_20230221.awardStatusTrainer,
         name="award_status_trainer"),  # id 전달
    path('award_status_jockey/', views_20230221.awardStatusJockey,
         name="award_status_jockey"),  # id 전달

    path('data_management/', views_20230221.dataManagement,
         name="data_management"),  # id 전달
    path('data_breakingnews/', views_20230221.dataBreakingNews,
         name="data_breakingnews"),  # id 전달
    path('krafile_input/', views_20230221.krafileInput, name="krafile_input"),  # id 전달
    path('breakingnews_input/', views_20230221.BreakingNewsInput, name="breakingnews_input"),  # id 전달

    path('pyscript_test/', views_20230221.pyscriptTest, name="pyscript_test"),  # id 전달



    path('exp011/<str:pk>/', views_20230221.exp011, name="exp011"),  # id 전달

    path('update_popularity/<str:rcity>/<str:rdate>/<int:rno>',
         views_20230221.updatePopularity, name="update_popularity"),
    # path('update_changed_race/<str:rcity>/<str:rdate>/<int:rno>', views.updateChangedRace, name="update_changed_race"),

]
