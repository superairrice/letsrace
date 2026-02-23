from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import os
import uuid

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
        # User.email is nullable in model; allow empty input in profile update form.
        self.fields['email'].required = False

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        # Store empty as NULL to avoid unique collisions on empty string.
        return email or None

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar

        max_size = 5 * 1024 * 1024  # 5MB
        if avatar.size > max_size:
            raise ValidationError("아바타 이미지는 5MB 이하만 업로드할 수 있습니다.")

        ext = os.path.splitext(getattr(avatar, "name", ""))[1].lower()
        allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
        if ext not in allowed_ext:
            raise ValidationError("지원하지 않는 이미지 형식입니다. (jpg, png, gif, webp, svg)")

        # Normalize uploaded filename to ASCII-safe UUID to avoid encoded path issues.
        avatar.name = f"{uuid.uuid4().hex}{ext}"

        return avatar


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
