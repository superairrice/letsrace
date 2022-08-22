from django.urls import path

from . import views

app_name = 'board'
urlpatterns = [
    path('', views.index, name='index'),
    #     path('<int:board_id>/', views.detail, name='detail'),
    #     path('write/', views.write, name='write'),
    #     path('write/write_board', views.write_board, name='write_board'),
    #     path('<int:board_id>/create_reply', views.create_reply, name='create_reply'),
]


# from django.urls import path
# from . import views

# # URLConf
# urlpatterns = [
#     # path('playground/hello/', views.say_hello),
#     path('hello/', views.say_hello),         # 기번 urls.py에 경로가 추가되었기때문에 playground 경로 제거 가능
# ]
