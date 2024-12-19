from collections import Counter
from datetime import datetime, timedelta
from typing import Dict
from datetime import date, datetime
from email.message import EmailMessage
import os
import shutil
import pandas as pd

from django.contrib import messages

# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Count, Max, Min, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from base.data_management import (
    get_breakingnews,
    get_file_contents,
    get_kradata,
    get_krafile,
    krafile_convert,
)

from base.mysqls import (
    get_award,
    get_award_race,
    get_axis,
    get_axis_rank,
    get_board_list,
    get_cycle_winning_rate,
    get_disease,
    get_expects,
    get_jockey_trend,
    get_judged,
    get_judged_horse,
    get_judged_jockey,
    get_last2weeks_loadin,
    get_loadin,
    get_paternal,
    get_paternal_dist,
    get_pedigree,
    get_popularity_rate_h,
    get_popularity_rate_j,
    get_popularity_rate_t,
    get_prediction,
    get_print_prediction,
    get_race,
    get_race_center_detail_view,
    get_race_related,
    get_recent_awardee,
    get_recent_horse,
    get_report_code,
    get_solidarity,
    get_status_stable,
    get_status_train,
    get_swim_horse,
    get_thethe9_ranks,
    get_thethe9_ranks_jockey,
    get_thethe9_ranks_multi,
    get_track_record,
    get_train,
    get_train_audit,
    get_train_horse,
    get_train_horse1,
    get_trainer_double_check,
    get_trainer_trend,
    get_training,
    get_status_training,
    get_training_awardee,
    get_treat_horse,
    get_weeks,
    get_last2weeks,
    get_weeks_status,
    insert_horse_disease,
    insert_race_judged,
    insert_race_simulation,
    insert_train_swim,
    set_changed_race,
    set_changed_race_horse,
    set_changed_race_jockey,
    set_changed_race_rank,
    set_changed_race_weight,
    trend_title,
)
from base.simulation import mock_insert, mock_traval, get_weight
from letsrace.settings import KRAFILE_ROOT

# import base.mysqls

from .forms import MyUserCreationForm, RoomForm, UserForm

# from django.contrib.auth.forms import UserCreationForm
from .models import (
    Award,
    Exp010,
    Exp011,
    Exp011s1,
    Exp012,
    JockeyW,
    JtRate,
    Message,
    PRecord,
    RaceResult,
    Racing,
    Rec010,
    RecordS,
    Room,
    Topic,
    User,
    Visitor,
    VisitorCount,
    VisitorLog,
)

from django.core.files.storage import FileSystemStorage  # 파일저장

from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from django.utils import timezone


def loginPage(request):
    page = "login"

    print(page)

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "User does not exist")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, messages.warning)

    context = {"page": page}
    return render(request, "account/login.html", context)


def registerPage(request):
    # page = 'register'
    form = MyUserCreationForm()

    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            # login(request, user)    # allauth 소셜로그인 적용전
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("home")
        else:
            messages.warning(request, form.errors)

        print(form.errors)
        print(form.non_field_errors())

        agree1 = request.POST.get("agree1")
        agree2 = request.POST.get("agree2")
        agree3 = request.POST.get("agree3")

        print("aaa", agree1, agree2, agree3)

    return render(request, "base/login_register.html", {"form": form})


def logoutUser(request):
    logout(request)
    return redirect("home")


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by("-created")
    participants = room.participants.all()

    if request.method == "POST":
        message = Message.objects.create(
            user=request.user, room=room, body=request.POST.get("body")
        )
        room.participants.add(request.user)
        return redirect("room", pk=room.id)

    context = {
        "room": room,
        "room_messages": room_messages,
        "participants": participants,
    }
    return render(request, "base/room.html", context)


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


@login_required(login_url="login")
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


@login_required(login_url="login")
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get("name"),
            description=request.POST.get("description"),
        )
        return redirect("home")

    context = {"form": form, "topics": topics}
    # render(request, 'base/room_form.html', context)
    return render(request, "base/room_form.html", context)


@login_required(login_url="login")
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    print(room.host)
    if request.user != room.host:
        return HttpResponse("You are not allowed here!!")

    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get("name")
        room.topic = topic
        room.description = request.POST.get("description")
        room.save()
        return redirect("home")

    context = {"form": form, "topics": topics, "room": room}
    return render(request, "base/room_form.html", context)


@login_required(login_url="login")
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse("You are not allowed here!!")

    if request.method == "POST":
        room.delete()
        return redirect("home")

    return render(request, "base/delete.html", {"obj": room})


@login_required(login_url="login")
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse("You are not allowed here!!")

    if request.method == "POST":
        message.delete()
        return redirect("home")

    return render(request, "base/delete.html", {"obj": message})


@login_required(login_url="login")
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    print(user)

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()

            request_file = (
                request.FILES["filename[]"] if "filename[]" in request.FILES else None
            )

            if request_file:
                # save attached file
                # create a new instance of FileSystemStorage
                fs = FileSystemStorage()
                file = fs.save(request_file.name, request_file)
                # the fileurl variable now contains the url to the file. This can be used to serve the file when needed.
                fileurl = fs.url(file)

                # destination = r"D:\Image1\i1.png"
                # shutil.copyfile(fileurl, destination)

            redirect("user-profile", pk=user.id)

            stream = os.popen("echo yes | python manage.py collectstatic")
            output = stream.read()
            print(output)

    return render(request, "base/update-user.html", {"form": form})


def topicsPage(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, "base/topics.html", {"topics": topics})


def activityPage(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    room_messages = Message.objects.all()

    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )

    first_race = racings[0]  # 첫번째 경주 조건

    horse = Exp011.objects.filter(
        rcity=first_race.rcity, rdate=first_race.rdate, rno=first_race.rno, rank=1
    ).get()
    print(horse.horse)

    # print(datetime.today().weekday())

    h_records = RecordS.objects.filter(horse=horse.horse).order_by("-rdate")

    context = {"room_messages": room_messages, "horse": horse, "h_records": h_records}

    return render(request, "base/activity.html", context)


def racingPage(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )
    return render(request, "base/race.html", {"racings": racings})


def leftPage(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )
    return render(request, "base/left_component.html", {"racings": racings})


def rightPage(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    # racings = Racing.objects.filter(rdate__icontains=q)
    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )

    r_results = RaceResult.objects.all().order_by("rdate", "rcity", "rno")
    return render(request, "base/right_component.html", {"r_results": r_results})


def exp011(request, pk):
    room = Exp011.objects.get(rdate=pk)
    print(room.key())
    room_messages = room.message_set.all().order_by("-rank")
    participants = room.participants.all()

    if request.method == "POST":
        message = Message.objects.create(
            user=request.user, room=room, body=request.POST.get("body")
        )
        room.participants.add(request.user)
        return redirect("room", pk=room.id)

    context = {
        "room": room,
        "room_messages": room_messages,
        "participants": participants,
    }
    return render(request, "base/room.html", context)


def home(request):

    q = request.GET.get("q") if request.GET.get("q") != None else ""  # 경마일

    if q == "":
        # rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]  # 초기값은 금요일

        rdate = Racing.objects.values("rdate").distinct()
        i_rdate = rdate[0]["rdate"]

        fdate = i_rdate[0:4] + "-" + i_rdate[4:6] + "-" + i_rdate[6:8]

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]

        i_rdate = rdate
        fdate = q

    # topics = Topic.objects.exclude(name__icontains=q)

    racings = get_race(i_rdate, i_awardee="jockey")
    # race_board = get_board_list(i_rdate, i_awardee="jockey")

    race, expects, rdays, award_j = get_prediction(i_rdate)
    # print(racings)

    # loadin = get_last2weeks_loadin(i_rdate)

    rflag = False  # 경마일, 비경마일 구분
    for r in rdays:
        # print(r[0], r[2])
        if r[0] == r[2]:
            rflag = True
            break

    t_count = check_visit(request)

    context = {
        "racings": racings,
        "expects": expects,
        "fdate": fdate,
        # "loadin": loadin,
        # "race_detail": race_detail,
        # "race_board": race_board,
        # "jname1": jname1,
        # "jname2": jname2,
        # "jname3": jname3,
        "award_j": award_j,
        "race": race,
        # "t_count": t_count,
        "rdays": rdays,
        # "judged_jockey": judged_jockey,
        "rflag": rflag,  # 경마일, 비경마일 구분
        # "topics": topics,  
        
    }

    return render(request, "base/home.html", context)


def homePage_a(request, rcity, rdate):
    racings = Racing.objects.filter(rcity=rcity, rdate=rdate)
    print(racings.query)
    context = {"rcity": rcity, "racings": racings}

    return render(request, "base/home_a.html", context)


def activityPage_a(request, hname):
    # q = request.GET.get('q') if request.GET.get('q') != None else ''

    h_records = RecordS.objects.filter(horse=hname).order_by("-rdate")

    horse = h_records[0]

    context = {"horse": horse, "h_records": h_records}

    return render(request, "base/activity_a.html", context)


def activityComponentPage_a(request, hname):
    # q = request.GET.get('q') if request.GET.get('q') != None else ''

    h_records = RecordS.objects.filter(horse=hname).order_by("-rdate")

    horse = h_records[0]

    context = {"horse": horse, "h_records": h_records}

    return render(request, "base/activity_component_a.html", context)


# @login_required(login_url="home")
def racePrediction(request, rcity, rdate, rno, hname, awardee):

    # if request.user.is_authenticated == False:
    #     context = {
    #         "rcity": rcity,
    #         "rdate": rdate,
    #         "rno": rno,
    #         "hname": hname,
    #         "awardee": awardee,
    #     }
    #     return redirect("prediction_list", rcity=rcity, rdate=rdate, rno=rno)

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "rank", "gate"
    )
    if exp011s:
        pass
    else:
        return render(request, "base/home.html")

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    # rdate_1year = str(int(rdate[0:4]) - 1) + rdate[4:8]  # 최근 1년 경주성적 조회조건 추가
    hr_records = RecordS.objects.filter(
        # hr_records = PRecord.objects.filter(
        # rdate__gt=rdate_1year,
        rdate__lt=rdate,
        horse__in=exp011s.values("horse"),
    ).order_by("horse", "-rdate")

    # print(hr_records)
    compare_r = exp011s.aggregate(
        Min("i_s1f"),
        Min("i_g1f"),
        Min("i_g2f"),
        Min("i_g3f"),
        Max("handycap"),
        Max("rating"),
        Max("r_pop"),
        Max("j_per"),
        Max("t_per"),
        Max("jt_per"),
        Min("recent5"),
        Min("recent3"),
        Min("convert_r"),
        Min("s1f_rank"),
    )

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
    paternal_dist = get_paternal_dist(rcity, rdate, rno)  # 부마 거리별 3착 성적

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    # # # axis = get_axis(rcity, rdate, rno)
    # axis1 = get_axis_rank(rcity, rdate, rno, 1)
    # axis2 = get_axis_rank(rcity, rdate, rno, 2)
    # axis3 = get_axis_rank(rcity, rdate, rno, 3)

    track = get_track_record(
        rcity, rdate, rno
    )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select horse, r_etc, r_flag
            from rec011 
            where rcity =  '"""
            + rcity
            + """'
            and rdate = '"""
            + rdate
            + """'
            and rno =  """
            + str(rno)
            + """
            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_memo = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 경주 메모")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity, rdate, rno, rday, rseq, distance, rcount, grade, dividing, rname, rcon1, rcon2, rtime
                from exp010 a 
                where rdate = '"""
            + rdate
            + """'
                order by rdate, rtime
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        weeksrace = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in exp010 : 주별 경주현황")

    t_count = check_visit(request)

    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 기수 기승가능 부딤중량
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        "paternal": paternal,
        "paternal_dist": paternal_dist,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        # "axis1": axis1,
        # "axis2": axis2,
        # "axis3": axis3,
        "r_memo": r_memo,
        "track": track,
        "weeksrace": weeksrace,
    }

    return render(request, "base/race_prediction.html", context)


def raceTraining(request, rcity, rdate, rno):

    train = get_train_horse(rcity, rdate, rno)
    train_title = trend_title(rdate)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    context = {
        "train": train,
        "train_title": train_title,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "r_condition": r_condition,
    }

    return render(request, "base/race_training.html", context)


def raceJudged(request, rcity, rdate, rno):

    pedigree = get_pedigree(rcity, rdate, rno)  # 병력
    treat = get_treat_horse(rcity, rdate, rno)
    judged_horse = get_judged_horse(rcity, rdate, rno)
    judged_jockey = get_judged_jockey(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    context = {
        "pedigree": pedigree,
        "treat": treat,
        "judged_horse": judged_horse,
        "judged_jockey": judged_jockey,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "r_condition": r_condition,
    }

    return render(request, "base/race_judged.html", context)


def raceRelated(request, rcity, rdate, rno):

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    award_j, award_t, award_h, race_detail = get_race_related(rcity, rdate, rno)

    loadin = get_loadin(rcity, rdate, rno)

    judged_jockey = get_judged_jockey(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    context = {
        "r_condition": r_condition,  # 기수 기승가능 부딤중량
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "judged_jockey": judged_jockey,
        "race_detail": race_detail,
        "award_j": award_j,
        "award_t": award_t,
        "award_h": award_h,
        "training_cnt": training_cnt,
        "trainer_double_check": str(trainer_double_check),
    }

    return render(request, "base/race_related.html", context)


def raceRelatedInfo(request, rcity, rdate, rno):

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    train = get_train_horse(rcity, rdate, rno)

    train_title = trend_title(rdate)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    pedigree = get_pedigree(rcity, rdate, rno)  # 병력
    treat = get_treat_horse(rcity, rdate, rno)
    judged_horse = get_judged_horse(rcity, rdate, rno)
    judged_jockey = get_judged_jockey(rcity, rdate, rno)

    award_j, award_t, award_h, race_detail = get_race_related(rcity, rdate, rno)

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    context = {
        "r_condition": r_condition,  # 기수 기승가능 부딤중량
        "train": train,  # 기수 기승가능 부딤중량
        "train_title": train_title,  # 기수 기승가능 부딤중량
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "pedigree": pedigree,  # 기수 기승가능 부딤중량
        "treat": treat,  # 기수 기승가능 부딤중량
        "judged_horse": judged_horse,  # 기수 기승가능 부딤중량
        "judged_jockey": judged_jockey,
        "award_j": award_j,
        "award_t": award_t,
        "award_h": award_h,
        "race_detail": race_detail,
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 기수 기승가능 부딤중량
    }

    return render(request, "base/race_related_info.html", context)


def predictionRace(request, rcity, rdate, rno, hname, awardee):

    if request.user.is_authenticated == False:
        context = {
            "rcity": rcity,
            "rdate": rdate,
            "rno": rno,
            "hname": hname,
            "awardee": awardee,
        }
        return redirect("prediction_list", rcity=rcity, rdate=rdate, rno=rno)

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "rank", "gate"
    )
    if exp011s:
        pass
    else:
        return render(request, "base/home.html")

    # if exp011s.values("rank")[4].get("rank") > 90:  # 신마일경우 skip
    #     complex5 = "0:00.0"``
    # else:
    #     complex5 = exp011s.values("complex")[4]

    #     if complex5:
    #         pass
    #     else:
    #         return render(request, "base/home.html")

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    # h_records = RecordS.objects.filter(
    #     rdate__lt=rdate, horse=horse.horse).order_by('-rdate')

    # rdate_1year = str(int(rdate[0:4]) - 1) + rdate[4:8]  # 최근 1년 경주성적 조회조건 추가
    hr_records = RecordS.objects.filter(
        # hr_records = PRecord.objects.filter(
        # rdate__gt=rdate_1year,
        rdate__lt=rdate,
        horse__in=exp011s.values("horse"),
    ).order_by("horse", "-rdate")

    # hr_pedigree = Exp012.objects.filter(
    #     rdate__lt=rdate, horse__in=exp011s.values("horse")).order_by('-rdate')

    # print(hr_records.query)

    # training_team = get_training_team(rcity, rdate, rno)

    racings, race_detail, race_board = get_race(rdate, i_awardee="jockey")

    compare_r = exp011s.aggregate(
        Min("i_s1f"),
        Min("i_g1f"),
        Min("i_g2f"),
        Min("i_g3f"),
        Max("handycap"),
        Max("rating"),
        Max("r_pop"),
        Max("j_per"),
        Max("t_per"),
        Max("jt_per"),
        Min("recent5"),
        Min("recent3"),
        Min("convert_r"),
        Min("s1f_rank"),
    )

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
    paternal_dist = get_paternal_dist(rcity, rdate, rno)  # 부마 거리별 3착 성적

    pedigree = get_pedigree(rcity, rdate, rno)  # 병력
    # training = get_training(rcity, rdate, rno)
    # train = get_train(rcity, rdate, rno)
    train = get_train_horse(rcity, rdate, rno)

    treat = get_treat_horse(rcity, rdate, rno)
    track = get_track_record(
        rcity, rdate, rno
    )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록
    # swim = get_swim_horse(rcity, rdate, rno)
    # train = sorted(train, key=lambda x: x[4] or 99)

    # print(training_cnt)

    # h_audit = get_train_audit(rcity, rdate, rno)      # get_treat_horse 함수 통합

    popularity_rate, award_j = get_popularity_rate_j(
        rcity, rdate, rno
    )  # 인기순위별 승률
    popularity_rate_t, award_t = get_popularity_rate_t(
        rcity, rdate, rno
    )  # 인기순위별 승률
    popularity_rate_h, award_h = get_popularity_rate_h(
        rcity, rdate, rno
    )  # 인기순위별 승률

    loadin = get_loadin(rcity, rdate, rno)
    # print(loadin)

    # judged = get_judged(rcity, rdate, rno)
    judged_horse = get_judged_horse(rcity, rdate, rno)
    judged_jockey = get_judged_jockey(rcity, rdate, rno)

    # trend_jockey = get_jockey_trend(rcity, rdate, rno)
    # trend_trainer = get_trainer_trend(rcity, rdate, rno)

    # # print(trend_j.to_html())

    # trend_j = trend_jockey.values.tolist()
    # trend_j_title = trend_jockey.columns.tolist()

    # trend_t = trend_trainer.values.tolist()
    # trend_t_title = trend_trainer.columns.tolist()

    # print(trend_j_title)
    # print(trend_j)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    # axis = get_axis(rcity, rdate, rno)
    axis1 = get_axis_rank(rcity, rdate, rno, 1)
    axis2 = get_axis_rank(rcity, rdate, rno, 2)
    axis3 = get_axis_rank(rcity, rdate, rno, 3)

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select horse, r_etc, r_flag
            from rec011 
            where rcity =  '"""
            + rcity
            + """'
            and rdate = '"""
            + rdate
            + """'
            and rno =  """
            + str(rno)
            + """

            ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_memo = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 경주 메모")

    name = get_client_ip(request)

    if name[0:6] != "15.177":
        update_visitor_count(name)

        # create a new Visitor instance
        new_visitor = Visitor(
            ip_address=name,
            user_agent=request.META.get("HTTP_USER_AGENT"),
            # referrer=request.META.get('HTTP_REFERER'),
            referer=rcity + " " + rdate + " " + str(rno) + " " + "predictionRace",
            # timestamp=timezone.now()
        )

        # insert the new_visitor object into the database
        new_visitor.save()

    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        #    'judged': judged,
        "judged_horse": judged_horse,
        "judged_jockey": judged_jockey,
        "race_detail": race_detail,
        "pedigree": pedigree,
        "paternal": paternal,
        "paternal_dist": paternal_dist,
        # 'hr_pedigree': hr_pedigree,
        "popularity_rate": popularity_rate,
        "award_j": award_j,
        "award_t": award_t,
        "award_h": award_h,
        "popularity_rate_t": popularity_rate_t,
        "popularity_rate_h": popularity_rate_h,
        "train": train,
        "training_cnt": training_cnt,
        "treat": treat,
        "track": track,
        #    'swim': swim,
        # "h_audit": h_audit,
        "trainer_double_check": str(trainer_double_check),
        "axis1": axis1,
        "axis2": axis2,
        "axis3": axis3,
        "r_memo": r_memo,
        # "trend_j": trend_j.to_html(
        #     index=False,
        #     header=True,
        #     justify="right",
        #     classes="rwd-table",
        #     table_id="rwd-table",
        # ),
        # "trend_j": trend_j,
        # "trend_j_title": trend_j_title,
        # "trend_t": trend_t,
        # "trend_t_title": trend_t_title,
    }

    return render(request, "base/prediction_race.html", context)


def predictionList(request, rcity, rdate, rno):
    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by("gate")
    if exp011s:
        pass
    else:
        return render(request, "base/home.html")

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    compare_r = exp011s.aggregate(
        Min("i_s1f"),
        Min("i_g1f"),
        Min("i_g2f"),
        Min("i_g3f"),
        Max("handycap"),
        Max("rating"),
        Max("r_pop"),
        Max("j_per"),
        Max("t_per"),
        Max("jt_per"),
        Min("recent5"),
        Min("recent3"),
        Min("convert_r"),
        Min("s1f_rank"),
    )

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    track = get_track_record(
        rcity, rdate, rno
    )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

    trainer_double_check = get_trainer_double_check(rcity, rdate, rno)

    paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
    paternal = sorted(paternal, key=lambda x: x[0] or 99)  # 게이트 순으로 정렬

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity, rdate, rno, rday, rseq, distance, rcount, grade, dividing, rname, rcon1, rcon2, rtime
                from exp010 a 
                where rdate = '"""
            + rdate
            + """'
                order by rdate, rtime
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        weeksrace = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in exp010 : 주별 경주현황")

    name = get_client_ip(request)

    if name[0:6] != "15.177":
        update_visitor_count(name)

        # create a new Visitor instance
        new_visitor = Visitor(
            ip_address=name,
            user_agent=request.META.get("HTTP_USER_AGENT"),
            # referrer=request.META.get('HTTP_REFERER'),
            referer=rcity + " " + rdate + " " + str(rno) + " " + "predictionList",
            # timestamp=timezone.now()
        )

        # insert the new_visitor object into the database
        new_visitor.save()

    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "compare_r": compare_r,
        "alloc": alloc,
        "track": track,
        "trainer_double_check": str(trainer_double_check),
        "paternal": paternal,
        "weeksrace": weeksrace,
    }

    return render(request, "base/prediction_list.html", context)


def awards(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q)
    )

    racings = Racing.objects.filter(
        Q(rcity__icontains=q) | Q(rdate__icontains=q) | Q(rday__icontains=q)
    )

    room_count = Exp011.objects.all().count()
    room_messages = Message.objects.filter(Q(room__name__icontains=q))

    # rdates = Racing.objects.distinct().values_list('rdate')
    rdays = (
        Racing.objects.distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rdate", "-rcity", "rno")
    )

    seoul = (
        Racing.objects.filter(rcity="서울")
        .values("rdate", "rday")
        .annotate(rcount=Count("rdate"))
    )
    busan = (
        Racing.objects.filter(rcity="부산")
        .values("rdate", "rday")
        .annotate(rcount=Count("rdate"))
    )

    seoul_fri = (
        Racing.objects.filter(rcity="서울", rday="금")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    seoul_sat = (
        Racing.objects.filter(rcity="서울", rday="토")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    seoul_sun = (
        Racing.objects.filter(rcity="서울", rday="일")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    busan_fri = (
        Racing.objects.filter(rcity="부산", rday="금")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    busan_sat = (
        Racing.objects.filter(rcity="부산", rday="토")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )
    busan_sun = (
        Racing.objects.filter(rcity="부산", rday="일")
        .distinct()
        .values(
            "rcity",
            "rdate",
            "rday",
            "rno",
            "distance",
            "rcount",
            "grade",
            "dividing",
            "rname",
            "rcon1",
            "rcon2",
            "rtime",
        )
        .order_by("rno")
    )

    # print(seoul_sat)

    first_race = racings[0]  # 첫번째 경주 조건

    exp011s = Exp011.objects.filter(
        rcity=first_race.rcity, rdate=first_race.rdate, rno=first_race.rno
    ).order_by("rank")

    horse = Exp011.objects.filter(
        rcity=first_race.rcity, rdate=first_race.rdate, rno=first_race.rno, rank=1
    ).get()

    # print(datetime.today().weekday())
    # print(seoul)

    h_records = RecordS.objects.filter(horse=horse.horse).order_by("-rdate")

    # 금주 경주예상 종합

    rdate = Racing.objects.values("rdate").distinct()
    # print(rdate[0]['rdate'])

    i_rdate = rdate[0]["rdate"]
    awards = get_award(i_rdate, i_awardee="jockey")

    r_results = RaceResult.objects.all().order_by("rdate", "rcity", "rno")
    # .filter( rdate__in=rdate.values_list('rdate', flat=True))

    allocs = Rec010.objects.filter(
        rdate__in=rdate.values_list("rdate", flat=True)
    ).order_by("rdate", "rcity", "rno")

    print(awards)

    context = {
        "rooms": rooms,
        "racings": racings,
        "room_count": room_count,
        "room_messages": room_messages,
        "rdays": rdays,
        "first_race": first_race,
        "exp011s": exp011s,
        "horse": horse,
        "seoul": seoul,
        "seoul_fri": seoul_fri,
        "seoul_sat": seoul_sat,
        "seoul_sun": seoul_sun,
        "busan_fri": busan_fri,
        "busan_sat": busan_sat,
        "busan_sun": busan_sun,
        "rdate": rdate,
        "r_results": r_results,
        "allocs": allocs,
        "awards": awards,
        "busan": busan,
        "h_records": h_records,
    }

    return render(request, "base/awards.html", context)


@login_required(login_url="login")
def updatePopularity(request, rcity, rdate, rno):
    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)
    context = {"rcity": rcity, "exp011s": exp011s}

    # user = request.user
    # form = UserForm(instance=user)

    if request.method == "POST":
        myDict = dict(request.POST)
        print(myDict["pop_1"][0])

        for race in exp011s:
            pop = "pop_" + str(race.gate)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011 set r_pop = """
                    + myDict[pop][0]
                    + """, r_rank = """
                    + myDict[pop][1]
                    + """
                            where rdate = '"""
                    + rdate
                    + """' and rcity = '"""
                    + rcity
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(race.gate)
                    + """
                        ; """
                )

                print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed selecting in BookListView")

        # form = Exp011(request.POST, request.FILES, rcity=rcity, rdate=rdate, rno=rno, instance=pop_1)
        # if form.is_valid():
        #     form.save()
        #     redirect('user-profile', pk=rdate)

    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)
    return render(request, "base/update_popularity.html", context)


@login_required(login_url="login")
def raceReport(request, rcity, rdate, rno):
    r_content = (
        request.GET.get("r_content") if request.GET.get("r_content") != None else ""
    )
    fdata = request.GET.get("fdata") if request.GET.get("fdata") != None else ""

    if fdata == "-":
        print(fdata)
    elif fdata == "마체중":
        set_changed_race_weight(rcity, rdate, rno, r_content)
    elif fdata == "경주순위":
        set_changed_race_rank(rcity, rdate, rno, r_content)
    elif fdata == "경주마취소":
        set_changed_race_horse(rcity, rdate, rno, r_content)
    elif fdata == "기수변경":
        set_changed_race_jockey(rcity, rdate, rno, r_content)

    rec011s, r_start, r_corners, r_finish, r_wrapup = get_report_code(rcity, rdate, rno)

    context = {
        "rcity": rcity,
        "rec011s": rec011s,
        "r_start": r_start,
        "r_corners": r_corners,
        "r_finish": r_finish,
        "r_wrapup": r_wrapup,
    }

    if request.method == "POST":
        myDict = dict(request.POST)
        print(myDict)

        for (
            rcity,
            rdate,
            rno,
            rank,
            gate,
            horse,
            r_start,
            r_corners,
            r_finish,
            r_wrapup,
            r_etc,
        ) in rec011s:
            pop = "pop_" + str(gate)
            # print(myDict[pop][0])

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update rec011 
                                set r_start = '"""
                    + myDict[pop][0]
                    + """',
                                    r_corners = '"""
                    + myDict[pop][1]
                    + """'
                            where rdate = '"""
                    + rdate
                    + """' and rcity = '"""
                    + rcity
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(gate)
                    + """
                        ; """
                )

                print(strSql)

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                connection.commit()
                connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                connection.rollback()
                print("Failed updating in rec011")

        # form = Exp011(request.POST, request.FILES, rcity=rcity, rdate=rdate, rno=rno, instance=pop_1)
        # if form.is_valid():
        #     form.save()
        #     redirect('user-profile', pk=rdate)

    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)
    return render(request, "base/race_report.html", context)


@login_required(login_url="login")
def updateChangedRace(request, rcity, rdate, rno):

    r_content = (
        request.GET.get("r_content") if request.GET.get("r_content") != None else ""
    )
    fdata = request.GET.get("fdata") if request.GET.get("fdata") != None else ""

    if fdata == "-":
        print(fdata)
    elif fdata == "마체중":
        set_changed_race_weight(rcity, rdate, rno, r_content)
    elif fdata == "경주순위":
        set_changed_race_rank(rcity, rdate, rno, r_content)
    elif fdata == "경주마취소":
        set_changed_race_horse(rcity, rdate, rno, r_content)
    elif fdata == "기수변경":
        set_changed_race_jockey(rcity, rdate, rno, r_content)
    elif fdata == "수영조교":
        insert_train_swim(r_content)
    elif fdata == "말진료현황":
        insert_horse_disease(r_content)

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)

    # user = request.user
    # form = UserForm(instance=user)

    if request.method == "POST":
        myDict = dict(request.POST)
        # print(myDict)
        # print(myDict['pop_1'][0])

        for race in exp011s:
            pop = "pop_" + str(race.gate)

            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011 
                                set r_rank = """
                    + myDict[pop][0]
                    + """,
                                    r_pop = """
                    + myDict[pop][1]
                    + """,
                                    bet = """
                    + myDict[pop][2]
                    + """
                            where rdate = '"""
                    + rdate
                    + """' and rcity = '"""
                    + rcity
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(race.gate)
                    + """
                        ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

                # connection.commit()
                # connection.close()

                # return render(request, 'base/update_popularity.html', context)
                # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

            except:
                # connection.rollback()
                print("Failed updating in exp011")

            exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)

    context = {"rcity": rcity, "exp011s": exp011s, "fdata": fdata}
    return render(request, "base/update_changed_race.html", context)


def raceResult(request, rcity, rdate, rno, hname, rcity1, rdate1, rno1):
    records = RecordS.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "rank", "gate"
    )
    if records:
        pass
    else:
        return render(request, "base/home.html")

    r_condition = Rec010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    rdate_1year = (
        str(int(rdate[0:4]) - 1) + rdate[4:8]
    )  # 최근 1년 경주성적 조회조건 추가

    hr_records = RecordS.objects.filter(
        rdate__lt=rdate, rdate__gt=rdate_1year, horse__in=records.values("horse")
    ).order_by("horse", "-rdate")

    compare_r = records.aggregate(
        Min("i_s1f"),
        Min("i_g1f"),
        Min("i_g2f"),
        Min("i_g3f"),
        Min("s1f_rank"),
        Min("recent3"),
        Min("recent5"),
        Min("convert_r"),
        Min("p_record"),
        Max("handycap"),
        Max("rating"),
    )

    judged_list, judged = get_judged(rcity, rdate, rno)
    track = get_track_record(rcity, rdate, rno)  # 경주 등급 평균

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    disease = get_disease(rcity, rdate, rno)

    # print(len(judged))
    if len(judged) > 0:
        judged = judged[0][0]

    horses = Exp011.objects.values("horse").filter(rcity=rcity1, rdate=rdate1, rno=rno1)

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select rcity, rdate, rno, rday, rseq, distance, rcount, grade, dividing, rname, rcon1, rcon2, rtime
                from exp010 a 
                where rdate = '"""
            + rdate
            + """'
                order by rdate, rtime
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        weeksrace = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in exp010 : 주별 경주현황")

    check_visit(request)

    context = {
        "records": records,
        "r_condition": r_condition,
        "hr_records": hr_records,
        "compare_r": compare_r,
        "hname": hname,
        "judged_list": judged_list,
        "judged": judged,
        "horses": horses,
        "alloc": alloc,
        "weeksrace": weeksrace,
        "track": track,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "disease": disease,
    }

    return render(request, "base/race_result.html", context)


# def raceResult(request, rcity, rdate, rno, hname, rcity1, rdate1, rno1):
#     records = RecordS.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
#         "rank", "gate"
#     )
#     if records:
#         pass
#     else:
#         return render(request, "base/home.html")

#     r_condition = Rec010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

#     rdate_1year = (
#         str(int(rdate[0:4]) - 1) + rdate[4:8]
#     )  # 최근 1년 경주성적 조회조건 추가

#     hr_records = RecordS.objects.filter(
#         rdate__lt=rdate, rdate__gt=rdate_1year, horse__in=records.values("horse")
#     ).order_by("horse", "-rdate")

#     compare_r = records.aggregate(
#         Min("i_s1f"),
#         Min("i_g1f"),
#         Min("i_g2f"),
#         Min("i_g3f"),
#         Min("s1f_rank"),
#         Min("recent3"),
#         Min("recent5"),
#         Min("convert_r"),
#         Min("p_record"),
#         Max("handycap"),
#         Max("rating"),
#     )

#     judged_horse = get_judged_horse(rcity, rdate, rno)
#     judged_jockey = get_judged_jockey(rcity, rdate, rno)

#     pedigree = get_pedigree(rcity, rdate, rno)
#     # training = get_training(rcity, rdate, rno)
#     train = get_train_horse(rcity, rdate, rno)
#     train = sorted(train, key=lambda x: x[5] or 99)

#     treat = get_treat_horse(rcity, rdate, rno)
#     track = get_track_record(rcity, rdate, rno)  # 경주거리별 등급별 평균기록,

#     # h_audit = get_train_audit(rcity, rdate, rno)

#     pedigree = sorted(pedigree, key=lambda x: x[2] or 99)

#     judged_list, judged = get_judged(rcity, rdate, rno)

#     # print(len(judged))
#     if len(judged) > 0:
#         judged = judged[0][0]

#     # lst = judged).split('●')

#     # for i in range(1,len(lst)):             # 첫번째 라인 스킵
#     #     str1 = lst[i].replace(' ', '')
#     #     print(str1)

#     horses = Exp011.objects.values("horse").filter(rcity=rcity1, rdate=rdate1, rno=rno1)

#     context = {
#         "records": records,
#         "r_condition": r_condition,
#         #    'training': training,
#         "train": train,
#         # "training_cnt": training_cnt,
#         "treat": treat,
#         "track": track,
#         "hr_records": hr_records,
#         "compare_r": compare_r,
#         "hname": hname,
#         "pedigree": pedigree,
#         # "h_audit": h_audit,
#         "judged_horse": judged_horse,
#         "judged_jockey": judged_jockey,
#         "judged_list": judged_list,
#         "judged": judged,
#         "horses": horses,
#     }

#     return render(request, "base/race_result.html", context)


def raceSimulation(request, rcity, rdate, rno, hname, awardee):

    weight = get_weight(rcity, rdate, rno)
    print(weight)
    mock_insert(rcity, rdate, rno)

    w_avg = (
        request.GET.get("w_avg") if request.GET.get("w_avg") != None else weight[0][0]
    )
    w_fast = (
        request.GET.get("w_fast") if request.GET.get("w_fast") != None else weight[0][1]
    )
    w_slow = (
        request.GET.get("w_slow") if request.GET.get("w_slow") != None else weight[0][2]
    )
    w_recent3 = (
        request.GET.get("w_recent3")
        if request.GET.get("w_recent3") != None
        else weight[0][3]
    )
    w_recent5 = (
        request.GET.get("w_recent5")
        if request.GET.get("w_recent5") != None
        else weight[0][4]
    )
    w_convert = (
        request.GET.get("w_convert")
        if request.GET.get("w_convert") != None
        else weight[0][5]
    )
    w_flag = (
        request.GET.get("w_flag") if request.GET.get("w_flag") != None else weight[0][6]
    )

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    weight_mock = (
        (
            int(w_avg),
            int(w_fast),
            int(w_slow),
            int(w_recent3),
            int(w_recent5),
            int(w_convert),
            w_flag,
        ),
    )  # tuple로 정의

    if weight == weight_mock:  # query 가중치와 입력된 가중치가 동일하면
        # print("같음")
        pass

    if (
        int(w_avg) + int(w_fast) + int(w_slow) == 100
        and int(w_recent3) + int(w_recent5) + int(w_convert) == 100  # 가중치 오류 check
    ):

        if weight != weight_mock:  # 가중치가 뱐경되었으면
            try:
                cursor = connection.cursor()

                strSql = (
                    """ 
                    insert into weight_s1 
                    (
                        rcity,
                        rdate,
                        rno,
                        wdate,
                        w_avg,
                        w_fast,
                        w_slow,
                        w_recent3,
                        w_recent5,
                        w_convert
                    )
                    VALUES
                    (
                        '"""
                    + rcity
                    + """',
                        '"""
                    + rdate
                    + """',
                        """
                    + str(rno)
                    + """,
                        """
                    " now() "
                    """,
                        """
                    + str(w_avg)
                    + """,
                        """
                    + str(w_fast)
                    + """,
                        """
                    + str(w_slow)
                    + """,
                        """
                    + str(w_recent3)
                    + """,
                        """
                    + str(w_recent5)
                    + """,
                        """
                    + str(w_convert)
                    + """
                    )
                ; """
                )

                # print(strSql)
                # print(weight_mock)

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                weight = cursor.fetchall()

                # connection.commit()
                # connection.close()

                # print(list(r_condition))

                # print( r_condition[0][0])

            except:
                connection.rollback()
                print("Failed inserting in weight_s1")

            mock = mock_traval(r_condition, weight_mock)

        if w_flag == 0:
            messages.warning(request, "weight_s1")

        else:
            messages.warning(request, "weight only")

    else:
        messages.warning(request, "오류")
        # weight = get_weight(rcity, rdate, rno)

    # print(
    #     "aaaa",
    #     int(w_avg) + int(w_fast) + int(w_slow),
    #     int(w_recent3) + int(w_recent5) + int(w_convert),
    # )
    # print(weight)

    exp011s = Exp011s1.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "rank", "gate"
    )

    if exp011s:
        pass
    else:
        return render(request, "base/home.html")

    hr_records = RecordS.objects.filter(
        # hr_records = PRecord.objects.filter(
        # rdate__gt=rdate_1year,
        rdate__lt=rdate,
        horse__in=exp011s.values("horse"),
    ).order_by("horse", "-rdate")

    compare_r = exp011s.aggregate(
        Min("i_s1f"),
        Min("i_g1f"),
        Min("i_g2f"),
        Min("i_g3f"),
        Max("handycap"),
        Max("rating"),
        Max("r_pop"),
        Max("j_per"),
        Max("t_per"),
        Max("jt_per"),
        Min("recent5"),
        Min("recent3"),
        Min("convert_r"),
        Min("s1f_rank"),
    )

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    track = get_track_record(
        rcity, rdate, rno
    )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

    loadin = get_loadin(rcity, rdate, rno)

    trainer_double_check = get_trainer_double_check(rcity, rdate, rno)

    # axis = get_axis(rcity, rdate, rno)
    axis1 = get_axis_rank(rcity, rdate, rno, 1)
    axis2 = get_axis_rank(rcity, rdate, rno, 2)
    axis3 = get_axis_rank(rcity, rdate, rno, 3)

    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        "track": track,
        #    'swim': swim,
        # "h_audit": h_audit,
        "trainer_double_check": str(trainer_double_check),
        "axis1": axis1,
        "axis2": axis2,
        "axis3": axis3,
        "weight": weight,
        "w_avg": w_avg,
        "w_fast": w_fast,
        "w_slow": w_slow,
        "w_recent3": w_recent3,
        "w_recent5": w_recent5,
        "w_convert": w_convert,
    }
    return render(request, "base/race_simulation.html", context)


# 마방 경주마 보유현황
def statusStable(request, rcity, rdate, rno):

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    # print(r_condition)

    stable, stable_g, stable_h = get_status_stable(rcity, rdate, rno)
    stable_list = stable.values.tolist()
    stable_list_g = stable_g.values.tolist()
    stable_title = stable.columns.tolist()

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
                select a.trainer
                from exp011 a
                where a.rcity =  '"""
            + rcity
            + """'
                and a.rdate = '"""
            + rdate
            + """'
                and a.rno =  """
            + str(rno)
            + """
                group by a.rcity, a.rdate, a.rno, a.trainer
                having count(*) >= 2

                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        trainer_double_check = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in trainer double cheeck")

    context = {
        "r_condition": r_condition,
        "stable_list": stable_list,
        "stable_list_g": stable_list_g,
        "stable_title": stable_title,
        "stable_h": stable_h,
        "trainer_double_check": str(trainer_double_check),
    }

    return render(request, "base/status_stable.html", context)


# 기수 or 조교사 최근 12주 성적 / 99일 경주결과
def trendWinningRate(request, rcity, rdate, rno, awardee, i_filter):
    if awardee == "jockey":
        trend_data, trend_title = get_jockey_trend(rcity, rdate, rno)
        # solidarity = get_solidarity(
        #     rcity, rdate, rno, "jockey", i_filter
        # )  # 기수, 조교사, 마주 연대현황 최근1년

    else:
        trend_data, trend_title = get_trainer_trend(rcity, rdate, rno)
        # solidarity = get_solidarity(
        #     rcity, rdate, rno, "trainer", i_filter
        # )  # 기수, 조교사, 마주 연대현황 최근1년

    # print(solidarity)
    # print(trend_title)

    trend_j = trend_data.values.tolist()
    trend_j_title = trend_data.columns.tolist()

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    context = {
        "trend_j": trend_j,
        "trend_j_title": trend_j_title,
        "trend_title": trend_title,
        "r_condition": r_condition,
        "awardee": awardee,
        # "solidarity": solidarity,
    }

    return render(request, "base/trend_winning_rate.html", context)


# 출주주기별 마방 승률 - 최근 1년
def cycleWinningRate(request, rcity, rdate, rno, awardee, i_filter):
    if awardee == "jockey":
        trend_data, trend_title = get_jockey_trend(rcity, rdate, rno)
        # solidarity = get_solidarity(
        #     rcity, rdate, rno, "jockey", i_filter
        # )  # 기수, 조교사, 마주 연대현황 최근1년

    else:
        trend_data = get_cycle_winning_rate(rcity, rdate, rno)
        # solidarity = get_solidarity(
        #     rcity, rdate, rno, "trainer", i_filter
        # )  # 기수, 조교사, 마주 연대현황 최근1년

    # print(solidarity)
    # print(trend_title)

    trend_j = trend_data.values.tolist()

    trend_j_title = trend_data.columns.tolist()

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    trainer_double_check = get_trainer_double_check(rcity, rdate, rno)
    # print(trainer_double_check)

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    context = {
        "trend_j": trend_j,
        "trend_j_title": trend_j_title,
        "r_condition": r_condition,
        "awardee": awardee,
        # "solidarity": solidarity,
        "trainer_double_check": str(trainer_double_check),
        "alloc": alloc,
    }

    return render(request, "base/cycle_winning_rate.html", context)


# 기수 or 조교사 or 마주 44일 경주결과
def getRaceAwardee(request, rdate, awardee, i_name, i_jockey, i_trainer, i_host):
    solidarity = get_recent_awardee(
        rdate, awardee, i_name
    )  # 기수, 조교사, 마주 연대현황 최근1년

    # print(solidarity)

    context = {
        "solidarity": solidarity,
        "awardee": awardee,
        "i_jockey": i_jockey,
        "i_trainer": i_trainer,
        "i_host": i_host,
    }

    return render(request, "base/get_race_awardee.html", context)


# 주별 입상마 경주전개 현황
def weeksStatus(request, rcity, rdate):
    status = get_weeks_status(rcity, rdate)

    rank1 = [item for item in status if item[15] == 1]  # item[15] : 예상착순(rank)
    rank2 = [item for item in status if item[15] == 2]  # item[15] : 예상착순(rank)
    rank3 = [item for item in status if item[15] == 3]  # item[15] : 예상착순(rank)
    r_rank1 = [item for item in status if item[16] == 1]  # item[16] : 실제착순(r_rank)
    r_rank2 = [item for item in status if item[16] == 2]  # item[16] : 실제착순(r_rank)
    r_rank3 = [item for item in status if item[16] == 3]  # item[16] : 실제착순(r_rank)

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select jockey, cast(load_in as decimal) 
            from jockey_w 
            where wdate = ( select max(wdate) from jockey_w where wdate < '"""
            + rdate
            + """' ) 
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        loadin = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기승가능중량")

    # print(status)

    context = {
        "status": status,
        "loadin": loadin,
        "rank1": len(rank1),
        "rank2": len(rank2),
        "rank3": len(rank3),
        "r_rank1": len(r_rank1),
        "r_rank2": len(r_rank2),
        "r_rank3": len(r_rank3),
        "rcount": len(status),
    }

    return render(request, "base/weeks_status.html", context)


# thethe9 rank1 실경주 입상현황
def jtAnalysis(
    request,
    rcity,
    fdate,
    tdate,
    jockey,
    trainer,
    host,
    horse,
    r1,
    r2,
    rr1,
    rr2,
    gate,
    distance,
    handycap,
):

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else rcity
    fdate = (
        request.GET.get("fdate")
        if request.GET.get("fdate") != None
        else fdate[0:4] + "-" + fdate[4:6] + "-" + fdate[6:8]
    )
    tdate = (
        request.GET.get("tdate")
        if request.GET.get("tdate") != None
        else tdate[0:4] + "-" + tdate[4:6] + "-" + tdate[6:8]
    )
    jockey = request.GET.get("jockey") if request.GET.get("jockey") != None else jockey
    trainer = (
        request.GET.get("trainer") if request.GET.get("trainer") != None else trainer
    )
    host = request.GET.get("host") if request.GET.get("host") != None else host
    horse = request.GET.get("horse") if request.GET.get("horse") != None else horse
    r1 = request.GET.get("r1") if request.GET.get("r1") != None else r1
    r2 = request.GET.get("r2") if request.GET.get("r2") != None else r2
    rr1 = request.GET.get("rr1") if request.GET.get("rr1") != None else rr1
    rr2 = request.GET.get("rr2") if request.GET.get("rr2") != None else rr2
    gate = request.GET.get("gate") if request.GET.get("gate") != None else gate
    distance = (
        request.GET.get("distance") if request.GET.get("distance") != None else distance
    )
    handycap = (
        request.GET.get("handycap") if request.GET.get("handycap") != None else handycap
    )

    # print('2', fdate, tdate, jockey, trainer, host, horse, r1, r2, rr1, rr2)

    # if fdate == "":
    #     # fdate =
    #     pass
    # else:
    #     fdate = fdate[0:4] + fdate[5:7] + fdate[8:10]
    #     tdate = tdate[0:4] + tdate[5:7] + tdate[8:10]

    status = get_thethe9_ranks(
        rcity,
        fdate[0:4] + fdate[5:7] + fdate[8:10],
        tdate[0:4] + tdate[5:7] + tdate[8:10],
        jockey,
        trainer,
        host,
        horse,
        r1,
        r2,
        rr1,
        rr2,
        gate,
        distance,
        handycap,
    )

    rank1 = [item for item in status if item[15] == 1]  # item[15] : 예상착순(rank)
    rank2 = [item for item in status if item[15] == 2]  # item[15] : 예상착순(rank)
    rank3 = [item for item in status if item[15] == 3]  # item[15] : 예상착순(rank)
    r_rank1 = [item for item in status if item[16] == 1]  # item[16] : 실제착순(r_rank)
    r_rank2 = [item for item in status if item[16] == 2]  # item[16] : 실제착순(r_rank)
    r_rank3 = [item for item in status if item[16] == 3]  # item[16] : 실제착순(r_rank)

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select jockey, cast(load_in as decimal) 
            from jockey_w 
            where wdate = ( select max(wdate) from jockey_w where wdate < '"""
            + tdate[0:4]
            + tdate[5:7]
            + tdate[8:10]
            + """' ) 
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        loadin = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기승가능중량")

    # print(status)
    
    check_visit(request)

    context = {
        "status": status,
        "loadin": loadin,
        "rcity": rcity,
        "fdate": fdate,
        "tdate": tdate,
        "today": tdate[0:4] + tdate[5:7] + tdate[8:10],
        "jockey": jockey,
        "trainer": trainer,
        "host": host,
        "horse": horse,
        "r1": r1,
        "r2": r2,
        "rr1": rr1,
        "rr2": rr2,
        "gate": gate,
        "distance": distance,
        "handycap": handycap[0:2],
        "rank1": len(rank1),
        "rank2": len(rank2),
        "rank3": len(rank3),
        "r_rank1": len(r_rank1),
        "r_rank2": len(r_rank2),
        "r_rank3": len(r_rank3),
        "rcount": len(status),
    }

    return render(request, "base/jt_analysis.html", context)


# thethe9 rank1 실경주 입상현황
def jtAnalysisJockey(
    request,
    rcity,
    fdate,
    tdate,
    jockey,
    trainer,
    host,
    jockey_b,
    r1,
    r2,
    rr1,
    rr2,
    gate,
    distance,
    handycap,
    rno,
):

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else rcity
    fdate = (
        request.GET.get("fdate")
        if request.GET.get("fdate") != None
        else fdate[0:4] + "-" + fdate[4:6] + "-" + fdate[6:8]
    )
    tdate = (
        request.GET.get("tdate")
        if request.GET.get("tdate") != None
        else tdate[0:4] + "-" + tdate[4:6] + "-" + tdate[6:8]
    )
    jockey = request.GET.get("jockey") if request.GET.get("jockey") != None else jockey
    trainer = (
        request.GET.get("trainer") if request.GET.get("trainer") != None else trainer
    )
    host = request.GET.get("host") if request.GET.get("host") != None else host
    jockey_b = (
        request.GET.get("jockey_b") if request.GET.get("jockey_b") != None else jockey_b
    )
    r1 = request.GET.get("r1") if request.GET.get("r1") != None else r1
    r2 = request.GET.get("r2") if request.GET.get("r2") != None else r2
    rr1 = request.GET.get("rr1") if request.GET.get("rr1") != None else rr1
    rr2 = request.GET.get("rr2") if request.GET.get("rr2") != None else rr2
    gate = request.GET.get("gate") if request.GET.get("gate") != None else gate
    distance = (
        request.GET.get("distance") if request.GET.get("distance") != None else distance
    )
    handycap = (
        request.GET.get("handycap") if request.GET.get("handycap") != None else handycap
    )
    rno = request.GET.get("rno") if request.GET.get("rno") != None else rno

    # print('2', fdate, tdate, jockey, trainer, host, horse, r1, r2, rr1, rr2)

    # if fdate == "":
    #     # fdate =
    #     pass
    # else:
    #     fdate = fdate[0:4] + fdate[5:7] + fdate[8:10]
    #     tdate = tdate[0:4] + tdate[5:7] + tdate[8:10]

    status = get_thethe9_ranks_jockey(
        rcity,
        fdate[0:4] + fdate[5:7] + fdate[8:10],
        tdate[0:4] + tdate[5:7] + tdate[8:10],
        jockey,
        trainer,
        host,
        jockey_b,
        r1,
        r2,
        rr1,
        rr2,
        gate,
        distance,
        handycap,
    )

    rank1 = [item for item in status if item[15] == 1]  # item[15] : 예상착순(rank)
    rank2 = [item for item in status if item[15] == 2]  # item[15] : 예상착순(rank)
    rank3 = [item for item in status if item[15] == 3]  # item[15] : 예상착순(rank)
    r_rank1 = [item for item in status if item[16] == 1]  # item[16] : 실제착순(r_rank)
    r_rank2 = [item for item in status if item[16] == 2]  # item[16] : 실제착순(r_rank)
    r_rank3 = [item for item in status if item[16] == 3]  # item[16] : 실제착순(r_rank)

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select jockey, cast(load_in as decimal) 
            from jockey_w 
            where wdate = ( select max(wdate) from jockey_w where wdate < '"""
            + tdate[0:4]
            + tdate[5:7]
            + tdate[8:10]
            + """' ) 
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        loadin = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기승가능중량")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select gate, jockey
            from exp011 
            where rcity = '"""
            + rcity
            + """'
            and rdate = '"""
            + tdate[0:4]
            + tdate[5:7]
            + tdate[8:10]
            + """' 
            and rno = """
            + str(rno)
            + """
            order by gate, jockey
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        jockeys = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed selecting in 기승가능중량")

    # print(jockeys)
    check_visit(request)

    context = {
        "status": status,
        "loadin": loadin,
        "rcity": rcity,
        "fdate": fdate,
        "tdate": tdate,
        "today": tdate[0:4] + tdate[5:7] + tdate[8:10],
        "jockey": jockey,
        "trainer": trainer,
        "host": host,
        "jockey_b": jockey_b,
        "r1": r1,
        "r2": r2,
        "rr1": rr1,
        "rr2": rr2,
        "gate": gate,
        "distance": distance,
        "handycap": handycap[0:2],
        "rank1": len(rank1),
        "rank2": len(rank2),
        "rank3": len(rank3),
        "r_rank1": len(r_rank1),
        "r_rank2": len(r_rank2),
        "r_rank3": len(r_rank3),
        "rcount": len(status),
        "rno": rno,
        "jockeys": jockeys,
    }

    return render(request, "base/jt_analysis_jockey.html", context)

def jtAnalysisMulti(
    request,
    rcity,
    fdate,
    tdate,
    jockey,
    trainer,
    host,
    jockey_b,
    r1,
    r2,
    rr1,
    rr2,
    gate,
    distance,
    handycap,
    rno,
    start,
):

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else rcity
    fdate = (
        request.GET.get("fdate")
        if request.GET.get("fdate") != None
        else fdate[0:4] + "-" + fdate[4:6] + "-" + fdate[6:8]
    )
    tdate = (
        request.GET.get("tdate")
        if request.GET.get("tdate") != None
        else tdate[0:4] + "-" + tdate[4:6] + "-" + tdate[6:8]
    )
    jockey = request.GET.get("jockey") if request.GET.get("jockey") != None else jockey.strip()
    trainer = (
        request.GET.get("trainer") if request.GET.get("trainer") != None else trainer.strip()
    )
    host = request.GET.get("host") if request.GET.get("host") != None else host.strip()
    jockey_b = (
        request.GET.get("jockey_b")
        if request.GET.get("jockey_b") != None
        else jockey_b.strip()
    )
    r1 = request.GET.get("r1") if request.GET.get("r1") != None else r1
    r2 = request.GET.get("r2") if request.GET.get("r2") != None else r2
    rr1 = request.GET.get("rr1") if request.GET.get("rr1") != None else rr1
    rr2 = request.GET.get("rr2") if request.GET.get("rr2") != None else rr2
    gate = request.GET.get("gate") if request.GET.get("gate") != None else gate
    distance = (
        request.GET.get("distance") if request.GET.get("distance") != None else distance
    )
    handycap = (
        request.GET.get("handycap") if request.GET.get("handycap") != None else handycap
    )
    rno = request.GET.get("rno") if request.GET.get("rno") != None else rno
    start = request.GET.get("start") if request.GET.get("start") != None else start

    # print('2', fdate, tdate, jockey, trainer, host, jockey_b, r1, r2, rr1, rr2)
    # print(tdate)

    # if fdate == "":
    #     # fdate =
    #     pass
    # else:
    #     fdate = fdate[0:4] + fdate[5:7] + fdate[8:10]
    #     tdate = tdate[0:4] + tdate[5:7] + tdate[8:10]

    status = get_thethe9_ranks_multi(
        rcity,
        fdate[0:4] + fdate[5:7] + fdate[8:10],
        tdate[0:4] + tdate[5:7] + tdate[8:10],
        jockey,
        trainer,
        host,
        jockey_b,
        r1,
        r2,
        rr1,
        rr2,
        gate,
        distance,
        handycap,
        start,
    )

    rank1 = [item for item in status if item[15] == 1]  # item[15] : 예상착순(rank)
    rank2 = [item for item in status if item[15] == 2]  # item[15] : 예상착순(rank)
    rank3 = [item for item in status if item[15] == 3]  # item[15] : 예상착순(rank)
    r_rank1 = [item for item in status if item[16] == 1]  # item[16] : 실제착순(r_rank)
    r_rank2 = [item for item in status if item[16] == 2]  # item[16] : 실제착순(r_rank)
    r_rank3 = [item for item in status if item[16] == 3]  # item[16] : 실제착순(r_rank)

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select jockey, cast(load_in as decimal) 
            from jockey_w 
            where wdate = ( select max(wdate) from jockey_w where wdate < '"""
            + tdate[0:4]
            + tdate[5:7]
            + tdate[8:10]
            + """' ) 
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        loadin = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 기승가능중량")

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select gate, jockey, trainer, host, horse
            from exp011 
            where rcity = '"""
            + rcity
            + """'
            and rdate = '"""
            + tdate[0:4]
            + tdate[5:7]
            + tdate[8:10]
            + """' 
            and rno = """
            + str(rno)
            + """
            order by gate, jockey
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        jockeys = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 기승가능중량")

    # print(jockeys)
    j_string=""
    t_string=""
    h_string=""
    for i, j in enumerate(jockeys):
        # print(i, j[1], j[2], j[3])
        j_string = j_string + j[1]
        t_string = t_string + j[2]
        h_string = h_string + j[3]

    check_visit(request)
    
    context = {
        "status": status,
        "loadin": loadin,
        "rcity": rcity,
        "fdate": fdate,
        "tdate": tdate,
        "today": tdate[0:4] + tdate[5:7] + tdate[8:10],
        "jockey": jockey,
        "trainer": trainer,
        "host": host,
        "jockey_b": jockey_b,
        "r1": r1,
        "r2": r2,
        "rr1": rr1,
        "rr2": rr2,
        "gate": gate,
        "distance": distance,
        "handycap": handycap[0:2],
        "rank1": len(rank1),
        "rank2": len(rank2),
        "rank3": len(rank3),
        "r_rank1": len(r_rank1),
        "r_rank2": len(r_rank2),
        "r_rank3": len(r_rank3),
        "rcount": len(status),
        "rno": rno,
        "start": start,
        "jockeys": jockeys,
        "j_string": j_string,
        "t_string": t_string,
        "h_string": h_string,
    }

    return render(request, "base/jt_analysis_multi.html", context)


# 기수 or 조교사 or 마주 44일 경주결과
def getRaceHorse(request, rdate, awardee, i_name, i_jockey, i_trainer, i_host):
    if i_host == "":
        i_host = " "

    solidarity = get_recent_horse(
        "99991231", awardee, i_name
    )  # 기수, 조교사, 마주 연대현황 최근1년
    # print(solidarity)

    context = {
        "solidarity": solidarity,
        "awardee": awardee,
        "i_jockey": i_jockey,
        "i_trainer": i_trainer,
        "i_host": i_host,
    }

    return render(request, "base/get_race_horse.html", context)


def raceTrain(request, rcity, rdate, rno):
    train = get_train_horse(rcity, rdate, rno)

    context = {
        "train": train,
    }

    return render(request, "base/race_train.html", context)


def printPrediction(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""

    if q == "":
        rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]  # 초기값은 금요일
        fdate = rdate[0:4] + "-" + rdate[4:6] + "-" + rdate[6:8]

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]
        fdate = q

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else "부산"

    jname1 = request.GET.get("j1") if request.GET.get("j1") != None else ""
    jname2 = request.GET.get("j2") if request.GET.get("j2") != None else ""
    jname3 = request.GET.get("j3") if request.GET.get("j3") != None else ""

    race, expects = get_print_prediction(rcity, rdate)

    if race:
        context = {
            "expects": expects,
            "race": race,
            "fdate": fdate,
            "jname1": jname1,
            "jname2": jname2,
            "jname3": jname3,
        }
    else:
        messages.warning(request, fdate + " " + rcity + " 경마 데이터가 없습니다.")
        context = {
            "expects": expects,
            "race": race,
            "fdate": fdate,
            "jname1": jname1,
            "jname2": jname2,
            "jname3": jname3,
        }

    # name = get_client_ip(request)
    # if name[0:6] != "15.177":
    #     update_visitor_count(name)

    #     # create a new Visitor instance
    #     new_visitor = Visitor(
    #         ip_address=name,
    #         user_agent=request.META.get("HTTP_USER_AGENT"),
    #         # referrer=request.META.get('HTTP_REFERER'),
    #         referer=rcity + " " + rdate + " " + "Print Prediction",
    #         # timestamp=timezone.now()
    #     )

    #     # insert the new_visitor object into the database
    #     new_visitor.save()

    return render(request, "base/print_prediction.html", context)


# 기수/조교사 주별 출주마 조교현황
def trainingAwardee(request, rdate, awardee, name):

    status = get_training_awardee(rdate, awardee, name)
    train_title = trend_title(rdate)

    # print(status)

    context = {
        "status": status,
        "train_title": train_title,
        "awardee": awardee,
        "name": name,
    }

    return render(request, "base/training_awardee.html", context)

# 출주마 이전 조교현황
def trainingHorse(request, rcity, rdate, rno, hname):

    hname = request.GET.get("hname") if request.GET.get("hname") != None else hname.strip()

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno, horse=hname).get()

    try:
        cursor = connection.cursor()

        strSql = (
            """ 
            select gate, horse
            from exp011 
            where rcity = '"""
            + rcity
            + """'
            and rdate = '"""
            + rdate
            + """' 
            and rno = """
            + str(rno)
            + """
            order by gate
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        h_names = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 게이트별 출주마")

    train = get_train_horse1(rdate, hname)

    # print(exp011s.rdate)
    # print(hname in h_names)

    context = {
        "r_condition": r_condition,
        "train": train,
        "rdate": rdate,
        "exp011s": exp011s,
        "hname": hname,
        "h_names": h_names,
    }

    return render(request, "base/training_horse.html", context)


def awardStatusTrainer(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    jname1 = request.GET.get("j1") if request.GET.get("j1") != None else ""
    jname2 = request.GET.get("j2") if request.GET.get("j2") != None else ""
    jname3 = request.GET.get("j3") if request.GET.get("j3") != None else ""

    if q == "":
        today = datetime.today()
        if today.weekday() == 4:  # {0:월, 1:화, 2:수, 3:목, 4:금, 5:토, 6:일}
            rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]
        elif today.weekday() == 5:
            rdate = Racing.objects.values("rdate").distinct()[1]["rdate"]
        else:
            rdate = Racing.objects.values("rdate").distinct()[2]["rdate"]

        friday = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일
        fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

    else:
        # print(q[5:7] + "-" + q[8:10] + "-" + q[0:4])
        today = datetime.strptime(q[5:7] + "-" + q[8:10] + "-" + q[0:4], "%m-%d-%Y")

        if today.weekday() == 4:
            rdate = q[0:4] + q[5:7] + q[8:10]
            friday = rdate
            fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

        else:
            rdate = q[0:4] + q[5:7] + q[8:10]

            friday = rdate
            fdate = q

            # messages.warning(request, "선택된 날짜가 금요일이 아닙니다.")

    weeks = get_last2weeks(
        friday,
        i_awardee="trainer",
        i_friday=Racing.objects.values("rdate").distinct()[0]["rdate"],
    )
    loadin = get_last2weeks_loadin(friday)

    check_visit(request)
    
    context = {
        "weeks": weeks,
        "loadin": loadin,
        "fdate": fdate,
        "rdate": rdate,
        "jname1": jname1,
        "jname2": jname2,
        "jname3": jname3,
    }

    return render(request, "base/award_status_trainer.html", context)


def awardStatusJockey(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    jname1 = request.GET.get("j1") if request.GET.get("j1") != None else ""
    jname2 = request.GET.get("j2") if request.GET.get("j2") != None else ""
    jname3 = request.GET.get("j3") if request.GET.get("j3") != None else ""

    if q == "":
        today = datetime.today()
        if today.weekday() == 4:  # {0:월, 1:화, 2:수, 3:목, 4:금, 5:토, 6:일}
            rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]
        elif today.weekday() == 5:
            rdate = Racing.objects.values("rdate").distinct()[1]["rdate"]
        else:
            rdate = Racing.objects.values("rdate").distinct()[2]["rdate"]

        friday = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일
        fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

    else:
        # print(q[5:7] + "-" + q[8:10] + "-" + q[0:4])
        today = datetime.strptime(q[5:7] + "-" + q[8:10] + "-" + q[0:4], "%m-%d-%Y")
        # print(today)

        if today.weekday() == 4:
            rdate = q[0:4] + q[5:7] + q[8:10]
            friday = rdate
            fdate = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]

        else:
            rdate = q[0:4] + q[5:7] + q[8:10]

            friday = rdate
            fdate = q

            # messages.warning(request, "선택된 날짜가 금요일이 아닙니다.")

    weeks = get_last2weeks(
        friday,
        i_awardee="jockey",
        i_friday=Racing.objects.values("rdate").distinct()[0]["rdate"],
    )

    loadin = get_last2weeks_loadin(friday)

    check_visit(request)

    context = {
        "weeks": weeks,
        "loadin": loadin,
        "fdate": fdate,
        "rdate": rdate,
        "jname1": jname1,
        "jname2": jname2,
        "jname3": jname3,
    }

    return render(request, "base/award_status_jockey.html", context)


def dataManagement(request):
    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else ""
    q1 = request.GET.get("q1") if request.GET.get("q1") != None else ""
    q2 = request.GET.get("q2") if request.GET.get("q2") != None else ""
    fcode = request.GET.get("fcode") if request.GET.get("fcode") != None else ""
    fstatus = request.GET.get("fstatus") if request.GET.get("fstatus") != None else ""

    if q1 == "":
        friday = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일

        sunday = Racing.objects.values("rdate").distinct()[1]["rdate"]  # weeks 기준일

        rdate1 = friday[0:4] + friday[4:6] + friday[6:8]
        rdate2 = sunday[0:4] + sunday[4:6] + sunday[6:8]

        fdate1 = friday[0:4] + "-" + friday[4:6] + "-" + friday[6:8]
        fdate2 = sunday[0:4] + "-" + sunday[4:6] + "-" + sunday[6:8]

    else:
        rdate1 = q1[0:4] + q1[5:7] + q1[8:10]
        rdate2 = q2[0:4] + q2[5:7] + q2[8:10]

        fdate1 = q1[0:4] + "-" + q1[5:7] + "-" + q1[8:10]
        fdate2 = q2[0:4] + "-" + q2[5:7] + "-" + q2[8:10]

    krafile = get_krafile(rcity, rdate1, rdate2, fcode, fstatus)
    if krafile:
        messages.warning(request, "총 " + str(len(krafile)) + "건.")
    else:
        messages.warning(request, "결과 0.")
    # kradata = get_kradata(rcity, rdate1, rdate2, fcode, fstatus)

    # print(krafile)
    # print(kradata)

    if request.method == "POST":
        myDict = dict(request.POST)

        krafile_convert(myDict["rcheck"])

        # for fname in myDict['rcheck']:
        #     print(fname)

        #     if fname[-12:-10] == '11':
        #         print(fname[-12:-10])

        #     file = open(fname, "r")
        #     while True:
        #         line = file.readline()
        #         if not line:
        #             break
        #         print(line.strip())
        #     file.close()

    context = {
        "q1": q1,
        "q2": q2,
        "fcode": fcode,
        "fstatus": fstatus,
        "krafile": krafile,
        #    'kradata': kradata,
        "fdate1": fdate1,
        "fdate2": fdate2,
    }

    return render(request, "base/data_management.html", context)


def raceBreakingNews(request):
    r_content = (
        request.POST.get("r_content") if request.POST.get("r_content") != None else ""
    )

    rcity = request.POST.get("rcity") if request.POST.get("rcity") != None else ""

    fdate = (
        request.POST.get("fdate") if request.POST.get("fdate") != None else "0000-00-00"
    )

    rno = request.POST.get("rno") if request.POST.get("rno") != None else 99

    rcount = request.POST.get("rcount") if request.POST.get("rcount") != None else 30

    fdata = request.POST.get("fdata") if request.POST.get("fdata") != None else "-"

    # fdate = rdate[0:4] + '-' + rdate[4:6] + '-' + rdate[6:8]
    rdate = fdate[0:4] + fdate[5:7] + fdate[8:10]

    if fdata == "-":
        result_cnt = 0
        pass
    elif fdata == "출전표변경":
        result_cnt = set_changed_race(rcity, rdate, rno, r_content)
    elif fdata == "마체중":
        result_cnt = set_changed_race_weight(rcity, rdate, rno, r_content)
    elif fdata == "경주순위":
        result_cnt = set_changed_race_rank(rcity, rdate, rno, r_content)
    elif fdata == "경주마취소":
        result_cnt = set_changed_race_horse(rcity, rdate, rno, r_content)
    elif fdata == "기수변경":
        result_cnt = set_changed_race_jockey(rcity, rdate, rno, r_content)
    elif fdata == "수영조교":
        result_cnt = insert_train_swim(r_content)
    elif fdata == "말진료현황":
        result_cnt = insert_horse_disease(r_content)
    elif fdata == "출전등록 시뮬레이션":
        result_cnt = insert_race_simulation(rcity, rcount, r_content)
    elif fdata == "심판위원 Report":
        result_cnt = insert_race_judged(rcity, r_content)

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=86)

    context = {
        "rcity": rcity,
        "rdate": rdate,
        "rno": rno,
        "rcount": rcount,
        "exp011s": exp011s,
        "r_content": r_content,
        "fdata": fdata,
        "fdate": fdate,
        "result_cnt": result_cnt,
    }

    # user = request.user
    # form = UserForm(instance=user)

    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)
    return render(request, "base/race_breakingnews.html", context)


@csrf_exempt
def krafileInput(request):
    request_files = (
        request.FILES.getlist("image_uploads")
        if "image_uploads" in request.FILES
        else None
    )

    if request_files:
        # save attached file
        for request_file in request_files:
            # create a new instance of FileSystemStorage
            fs = FileSystemStorage()

            fname = request_file.name

            if fname[-4:] == "xlsx":
                os.makedirs(KRAFILE_ROOT / "xlsx", exist_ok=True)
                fs.location = KRAFILE_ROOT / "xlsx"
            else:
                if fname[0:4] < "2018":
                    os.makedirs(KRAFILE_ROOT / "2022이전", exist_ok=True)
                    fs.location = KRAFILE_ROOT / "2022이전"
                else:
                    os.makedirs(KRAFILE_ROOT / fname[0:4], exist_ok=True)
                    fs.location = KRAFILE_ROOT / fname[0:4]

            if fs.exists(fname):
                fs.delete(fname)

                try:
                    cursor = connection.cursor()

                    strSql = (
                        """
                            DELETE FROM krafile
                            WHERE fname = '"""
                        + fname
                        + """'
                            ; """
                    )

                    # print(strSql)

                    r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                    result = cursor.fetchone()
                    # result = cursor.fetchall()

                    connection.commit()
                    connection.close()

                except:
                    connection.rollback()
                    print("Failed deleting in krafile")

            # file = fs.save(request_file.name, request_file)
            # # the fileurl variable now contains the url to the file. This can be used to serve the file when needed.
            # fileurl = fs.url(file)

            if fname[-4:] == "xlsx":
                print(fname[-4:])

                fdate = fname[-19:-11]
                fcode = "c1"

                file = fs.save(request_file.name, request_file)
                # shutil.copy(request_file, str(fs.location) + '/')
            else:
                fdate = fname[0:8]
                fcode = fname[-12:-10]
                fcontent = request_file.read().decode(
                    "euc-kr", errors="strict"
                )  # 한글 decode

                letter = open(str(fs.location) + "/" + fname, "w")  # 새 파일 열기
                letter.write(fcontent)
                letter.close()  # 닫기

            try:
                cursor = connection.cursor()

                strSql = (
                    """
                        INSERT INTO krafile
                        ( fname, fpath, rdate, fcode, fstatus, in_date )
                        VALUES
                        ( '"""
                    + fname
                    + """',
                        '"""
                    + str(fs.location)
                    + "/"
                    + fname
                    + """',
                        '"""
                    + fdate
                    + """',
                        '"""
                    + fcode
                    + """',
                        'I',
                        """
                    + "NOW()"
                    + """
                        ) ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                result = cursor.fetchone()
                # result = cursor.fetchall()

                connection.commit()
                connection.close()

            except:
                connection.rollback()
                print("Failed inserting in krafile")

    context = {"request_files": request_files}

    return render(request, "base/krafile_input.html", context)


@csrf_exempt
def BreakingNewsInput(request):
    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else ""
    rdate = request.GET.get("rdate") if request.GET.get("rdate") != None else ""
    title = request.GET.get("title") if request.GET.get("title") != None else ""
    news = request.GET.get("news") if request.GET.get("news") != None else ""

    try:
        cursor = connection.cursor()

        strSql = (
            """
                DELETE FROM breakingnews
                WHERE rcity = '"""
            + rcity
            + """' and rdate = '"""
            + rdate
            + """' and title = '"""
            + title
            + """'
                ; """
        )

        # print(strSql)

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchone()
        # result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed deleting in Breaking News")

    try:
        cursor = connection.cursor()

        strSql = (
            """
                INSERT INTO breakingnews
                ( rcity, rdate, title, news, in_date )
                VALUES
                ( '"""
            + rcity
            + """',
                '"""
            + rdate
            + """',
                '"""
            + title
            + """',
                '"""
            + news
            + """',
                """
            + "NOW()"
            + """
                ) ; """
        )

        # print(strSql)
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        result = cursor.fetchone()
        # result = cursor.fetchall()

        connection.commit()
        connection.close()

    except:
        connection.rollback()
        print("Failed inserting in Breaking News")

    context = {"rdate": rdate}

    return render(request, "base/breakingnews_input.html", context)


def pyscriptTest(request):
    pass

    return render(request, "base/pyscript_test.html")


def writeSignificant(request, rdate, horse):
    if request.method == "POST":
        start = request.POST.get("start")
        corners = request.POST.get("corners")
        finish = request.POST.get("finish")
        wrapup = request.POST.get("wrapup")
        r_etc = request.POST.get("r_etc")
        r_flag = request.POST.get("r_flag")

        # print(start, corners, finish, wrapup, r_etc)
        # print(r_flag)

        try:
            cursor = connection.cursor()

            strSql = (
                """ update rec011 
                    set r_start = '"""
                + start
                + """',
                        r_corners = '"""
                + corners
                + """',
                        r_finish = '"""
                + finish
                + """',
                        r_wrapup = '"""
                + wrapup
                + """',
                        r_flag = '"""
                + r_flag
                + """',
                        r_etc = '"""
                + r_etc.strip()
                + """'
                    where rdate =  '"""
                + rdate
                + """'
                    and horse like '%"""
                + horse
                + """%'
                    ; """
            )

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            awards = cursor.fetchall()

            # connection.commit()
            # connection.close()

            # return render(request, 'base/update_popularity.html', context)
            # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)

        except:
            # connection.rollback()
            print("Failed updating in rec011")

        try:
            cursor = connection.cursor()
            strSql = (
                """ update record_s set r_flag = '"""
                + r_flag
                + """'
                        where rdate = '"""
                + rdate
                + """'
                        and horse like '%"""
                + horse
                + """%'
                        ;"""
            )
            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            r_significant = cursor.fetchall()

            # print(r_significant)

            # connection.commit()
            # connection.close()

        except:
            connection.rollback()
            print("Failed updating r_flag")

    try:
        cursor = connection.cursor()
        strSql = (
            """ select r_start, r_corners, r_finish, r_wrapup, r_etc, r_flag
                    from rec011 
                    where rdate = '"""
            + rdate
            + """'
                    and horse like '%"""
            + horse
            + """%'
                    ;"""
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_significant = cursor.fetchall()

        # print(r_significant)

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting start")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R1' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_start = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting r_start")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R2' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_corners = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting r_corners")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R3' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_finish = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting r_finish")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R4' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_wrapup = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting r_wrapup")

    try:
        cursor = connection.cursor()
        strSql = """ select r_code, r_name from race_cd where cd_type = 'R0' order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_flag = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting r_flag ; 집계 제외 사유")

    context = {
        "rdate": rdate,
        "horse": horse,
        "r_significant": r_significant,
        "r_start": r_start,
        "r_corners": r_corners,
        "r_finish": r_finish,
        "r_wrapup": r_wrapup,
        "r_flag": r_flag,
    }
    return render(request, "base/write_significant.html", context)


@login_required(login_url="login")
def createBorder(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get("name"),
            description=request.POST.get("description"),
        )
        return redirect("home")

    context = {"form": form, "topics": topics}
    # render(request, 'base/room_form.html', context)
    return render(request, "base/room_form.html", context)


def send_email():
    subject = "message"
    to = ["keombit@gmail.com"]
    from_email = "id@gmail.com"
    message = "메지시 테스트"
    EmailMessage(subject=subject, body=message, to=to, from_email=from_email).send()


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    # print((x_forwarded_for.split(',')[0]))
    # print((request.META.get('REMOTE_ADDR')))

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def check_visit(request):
    name = get_client_ip(request)

    if name[0:6] != "15.177":
        update_visitor_count(name)

        # create a new Visitor instance
        new_visitor = Visitor(
            ip_address=name,
            user_agent=request.META.get("HTTP_USER_AGENT"),
            current = request.build_absolute_uri(), # 현재 페이지 정보
            referer=request.META.get( "HTTP_REFERER", "Unknown"),  # referer 값이 없으면 기본값으로 "home" 설정
            timestamp=timezone.now(),  # 현재 시간으로 설정
        )

        # insert the new_visitor object into the database
        new_visitor.save()

    t_count = visitor_count()

    return t_count


def visitor_count():
    today = date.today()
    user = (
        VisitorLog.objects.values("name")
        .filter(date=today)
        .annotate(max_count=Count("name"))
    )

    return user.count()


# def update_visitor_count(name):
#     today = date.today()
#     now = datetime.now()
#     timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

#     # Connect to the MySQL database

#     cursor = connection.cursor()

#     # Check if a record already exists for today
#     cursor.execute("SELECT COUNT(*) FROM base_visitorcount WHERE date = %s", (today,))
#     result = cursor.fetchone()
#     if result[0] > 0:
#         # If a record exists, update the count
#         cursor.execute(
#             "UPDATE base_visitorcount SET count = count + 1 WHERE date = %s", (today,)
#         )
#     else:
#         # If a record doesn't exist, create a new record
#         cursor.execute(
#             "INSERT INTO base_visitorcount (date, count) VALUES (%s, %s)", (today, 1)
#         )

#     # Add a new visitor to the visitors_log table
#     sql = "INSERT INTO base_visitorlog (name, date, timestamp) VALUES (%s, %s, %s)"
#     val = (name, today, timestamp)
#     cursor.execute(sql, val)

#     # Commit the changes and close the connection
#     connection.commit()
#     connection.close()

def update_visitor_count(name):
    today = date.today()
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    try:
      
        # Connect to the MySQL database
        cursor = connection.cursor()

        # 오늘 날짜로 기록이 이미 있는지 확인
        cursor.execute(
            "SELECT COUNT(*) FROM base_visitorcount WHERE date = %s", (today,)
        )
        result = cursor.fetchone()

        if result[0] > 0:
            # 기록이 있으면 count 증가
            cursor.execute(
                "UPDATE base_visitorcount SET count = count + 1 WHERE date = %s",
                (today,),
            )
        else:
            # 기록이 없으면 새로운 기록 생성
            cursor.execute(
                "INSERT INTO base_visitorcount (date, count) VALUES (%s, %s)",
                (today, 1),
            )

        # 방문자 기록 추가
        sql = "INSERT INTO base_visitorlog (name, date, timestamp) VALUES (%s, %s, %s)"
        val = (name, today, timestamp)
        cursor.execute(sql, val)

        # 변경 사항 커밋
        connection.commit()

    except:
        print("데이터베이스 오류가 발생했습니다:")

    finally:
        # 연결 종료
        cursor.close()
        connection.close()
