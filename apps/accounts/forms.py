import re

from allauth.account.forms import SignupForm
from django import forms


class TrendSignupForm(SignupForm):
    name = forms.CharField(
        max_length=50,
        label="이름(별칭)",
        widget=forms.TextInput(
            attrs={
                "placeholder": "서비스에서 표시될 이름",
                "autocomplete": "nickname",
            }
        ),
    )
    username = forms.CharField(
        max_length=30,
        label="아이디",
        widget=forms.TextInput(
            attrs={
                "placeholder": "영문/숫자/._ 조합",
                "autocomplete": "username",
            }
        ),
    )
    email = forms.EmailField(
        label="이메일",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "name@example.com",
                "autocomplete": "email",
            }
        ),
    )
    agree_terms = forms.BooleanField(
        label="이용약관 및 개인정보 처리방침에 동의합니다.",
        required=True,
    )
    agree_marketing = forms.BooleanField(
        label="이벤트/업데이트 안내 메일 수신(선택)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "비밀번호"
        self.fields["password2"].label = "비밀번호 확인"
        self.fields["password1"].widget.attrs.update(
            {"placeholder": "8자 이상 입력", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"placeholder": "비밀번호 다시 입력", "autocomplete": "new-password"}
        )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not re.fullmatch(r"[A-Za-z0-9._]+", username):
            raise forms.ValidationError("아이디는 영문, 숫자, 점(.), 밑줄(_)만 사용할 수 있습니다.")
        return username.lower()

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("이름(별칭)은 2자 이상 입력해 주세요.")
        return name

    def save(self, request):
        user = super().save(request)
        user.name = self.cleaned_data["name"]
        user.save(update_fields=["name"])
        return user
