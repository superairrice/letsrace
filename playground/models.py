# Used to generate URLs by reversing the URL patterns
# import uuid  # Required for unique book instances
# from django.urls import reverse
# from django.db import models

# Create your models here.

# PrimaryKey는 별도로 지정하지 않으면 디폴트로 다음과 같은 코드가 각 모델에 수행된다.
# id = models.AutoField(primary_key=True)


# class Weight(models.Model):
#     wdate = models.DateTimeField(primary_key=True)
#     w_avg = models.IntegerField(blank=True, null=True)
#     w_fast = models.IntegerField(blank=True, null=True)
#     w_slow = models.IntegerField(blank=True, null=True)
#     w_recent3 = models.IntegerField(blank=True, null=True)
#     w_recent5 = models.IntegerField(blank=True, null=True)
#     w_convert = models.IntegerField(blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'weight'


# class Board(models.Model):
#     """
#         title: 제목
#         content: 내용
#         author: 작성자
#         like_count: 좋아요 카운트
#         pub_date: 배포일
#     """
#     title = models.CharField(max_length=100)
#     content = models.CharField(max_length=500)
#     author = models.CharField(max_length=100)
#     like_count = models.PositiveIntegerField(default=0)  # 양수입력 필드
#     pub_date = models.DateTimeField()

#     def __str__(self):
#         return self.title


# class Reply(models.Model):
#     """
#         reply: Reply -> Board 연결관계
#         comment: 댓글내용
#         rep_date: 작성일
#     """
#     reply = models.ForeignKey(Board, on_delete=models.CASCADE)
#     comment = models.CharField(max_length=200)
#     rep_date = models.DateTimeField()

#     def __str__(self):
#         return self.comment
