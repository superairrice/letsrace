from django.urls import include, path
from . import views


urlpatterns = [

    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),


    path('awards/', views.awards, name="awards"),


    path('room/<str:pk>/', views.room, name="room"),  # id 전달
    path('profile/<str:pk>/', views.userProfile, name="user-profile"),

    path('create-room/', views.createRoom, name="create-room"),
    path('create-border/', views.createBorder, name="create-border"),           # 게시판 글 작성
    
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

    path('left_component/', views.leftPage, name="left_component"),
    path('right_component/', views.rightPage, name="right_component"),

    path('activity_a/<str:hname>', views.activityPage_a, name="activity_a"),
    path('activityComponent_a/<str:hname>',
	    views.activityComponentPage_a, name="activityComponent_a"),

    path('home_a/<str:rcity>/<str:rdate>', views.homePage_a, name="home_a"),

    path('prediction_race/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:awardee>',
	    views.predictionRace, name="prediction_race"),  # id 전달
    path('race_result/<str:rcity>/<str:rdate>/<int:rno>/<str:hname>/<str:rcity1>/<str:rdate1>/<int:rno1>',
	    views.raceResult, name="race_result"),  # id 전달
    path('race_train/<str:rcity>/<str:rdate>/<int:rno>',
	    views.raceTrain, name="race_train"),  # id 전달


    path('print_prediction/', views.printPrediction,
	    name="print_prediction"),  # 경주일별 예상 순위 리스트 프린터

    path('award_status_trainer/', views.awardStatusTrainer,
	    name="award_status_trainer"),  # id 전달
    path('award_status_jockey/', views.awardStatusJockey,
	    name="award_status_jockey"),  # id 전달

    path('data_management/', views.dataManagement,
	    name="data_management"),  # id 전달
    path('data_breakingnews/', views.dataBreakingNews,
	    name="data_breakingnews"),  # id 전달
    path('krafile_input/', views.krafileInput, name="krafile_input"),  # id 전달
    path('breakingnews_input/', views.BreakingNewsInput, name="breakingnews_input"),  # id 전달

    path('pyscript_test/', views.pyscriptTest, name="pyscript_test"),  # id 전달



    path('exp011/<str:pk>/', views.exp011, name="exp011"),  # id 전달

    path('update_popularity/<str:rcity>/<str:rdate>/<int:rno>',
	    views.updatePopularity, name="update_popularity"),
    # path('update_changed_race/<str:rcity>/<str:rdate>/<int:rno>', views.updateChangedRace, name="update_changed_race"),


    path('', views.home, name="home"),

    path('send_email/', views.send_email, name='send_email'),


]
