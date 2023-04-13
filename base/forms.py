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
        # widgets = {
        #     'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '15자 이내로 입력 가능합니다.'}),
        #     'email': forms.EmailInput(attrs={'class': 'form-control'}),
        #     'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        # }
        labels = {
            'name': '필명',
            'username': 'ID',
            'email': '이메일',
            'bio': '하고싶은 말 '
        }
    # 글자수 제한

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['maxlength'] = 15


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
