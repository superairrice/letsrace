from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm

from .models import Room, User
# from django.contrib.auth.models import User


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'password1', 'password2']


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'    # 전체 컬럼 불러오기
        exclude = ['host', 'participants']


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['avatar', 'name', 'username', 'email', 'bio']


# class Racing(ModelForm):
#     class Meta:
#         model = Exp010
#         fields = ['rcity', 'rdate', 'rno', 'distance', 'rcount',
#                   'grade', 'dividing', 'rname', 'rcon1', 'rcon2',  'rtime']


# class Total(DBView):
#     userpkk = models.ForeignKey(User, on_delete=models.DO_NOTHING)
#     name = models.CharField(max_length=200)
#     gender = models.CharField(max_length=10)
#     view_definition = """
#         SELECT
#         row_number() over () as id,
#         User.pkk as userpkk_id,
#         User.name as name,
#         Gender.gender as gender
#         FROM User LEFT JOIN Gender
#         ON User.pkk = Gender.pkk_id
#     """

#     class Meta:
#         managed = False
#         db_table = "Total"
