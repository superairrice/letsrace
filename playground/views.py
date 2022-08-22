# from django.http import HttpResponseRedirect
# from django.shortcuts import render
# from django.utils import timezone
# from django.urls import reverse

# from .models import Board, Weight


# # def index(request):
# #     all_boards = Board.objects.all().order_by(
# #         "-pub_date")  # 모든 데이터 조회, 내림차순(-표시) 조회
# #     return render(request, 'index.html', {'title': 'Board List', 'board_list': all_boards})

# def index(request):
#     all_weight = Weight.objects.all()
#     # .order_by(
#     #     "wdate")  # 모든 데이터 조회, 내림차순(-표시) 조회

#     print(all_weight.count())
#     return render(request, 'index.html', {'title': 'Weight List', 'weight_list': all_weight})


# def detail(request, board_id):
#     board = Board.objects.get(id=board_id)
#     return render(request, 'detail.html', {'board': board})


# def write(request):
#     return render(request, 'write.html')


# def write_board(request):
#     b = Board(title=request.POST['title'], content=request.POST['detail'],
#               author="choi", pub_date=timezone.now())
#     b.save()
#     return HttpResponseRedirect(reverse('board:index'))


# def create_reply(request, board_id):
#     b = Board.objects.get(id=board_id)
#     b.reply_set.create(
#         comment=request.POST['comment'], rep_date=timezone.now())
#     return HttpResponseRedirect(reverse('board:detail', args=(board_id,)))


from django.db import connection
from django.shortcuts import render
from django.http import HttpResponse

# def say_hello(request):
#   return HttpResponse('Hello World')


def say_hello(request):
    return render(request, 'hello.html', {'name': 'Mosh'})


# def index(request):
#     return render(request, 'index.html')


# # 새로 import 하는 모듈
# def BookListView(request):
#     # books = Book.objects.all()
#     try:
#         cursor = connection.cursor()

#         strSql = "SELECT code, name, author FROM bookstore_book"
#         result = cursor.execute(strSql)
#         books = cursor.fetchall()

#         connection.commit()
#         connection.close()

#     except:
#         connection.rollback()
#         print("Failed selecting in BookListView")

#     return render(request, 'book_list.html', {'books': books})
