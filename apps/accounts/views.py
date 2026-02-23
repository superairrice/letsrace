from apps.common import *

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    context = {
        "user": user,
        "rooms": rooms,
        "room_messages": room_messages,
        "topics": topics,
    }
    return render(request, "base/profile.html", context)

def profilePage(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    context = {
        "user": user,
        "rooms": rooms,
        "room_messages": room_messages,
        "topics": topics,
    }
    return render(request, "base/profile.html", context)

@login_required(login_url="account_login")
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()
            messages.success(request, "프로필이 업데이트되었습니다.")
            return redirect("user-profile", pk=user.id)
        messages.error(request, "입력값을 확인해 주세요.")

    return render(request, "base/update-user.html", {"form": form})


@login_required(login_url="account_login")
def passwordChange(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Your password was successfully updated!")
            return redirect("home")
        else:
            messages.error(
                request,
                "기존 비밀번호와 새 비밀번호를 규칙에 맞게 설정하십시오(툭수문자와 숫자포함 8자 이상)",
            )
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "account/password_change.html", {"form": form})
