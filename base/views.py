from datetime import datetime, timedelta
from datetime import date, datetime
from email.message import EmailMessage
import os

from django.contrib import messages

# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Count, Max, Min, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render

from base.g2f_update import g2f_update
from base.compute_gpt import process_race
from base.data_management import (
    get_krafile,
    krafile_convert,
)

from base.race_compute import baseline_compute, create_record, renewal_record_s
from base.race_finalscore import update_exp010_overview_for_race, update_exp011_for_period, update_exp011_for_race
from base.race_refund import calc_rpop_anchor_26_trifecta
from base.simulation2 import get_weight2, mock_insert2, mock_traval2
from base.mysqls import (
    get_award,
    get_axis_rank,
    get_cycle_winning_rate,
    get_disease,
    get_jockey_trend,
    get_jockeys_train,
    get_jt_collaboration,
    get_judged,
    get_judged_horse,
    get_judged_jockey,
    get_last2weeks_loadin,
    get_loadin,
    get_paternal,
    get_paternal_dist,
    get_pedigree,
    get_prediction,
    get_print_prediction,
    get_race,
    get_race_related,
    get_report_code,
    get_status_stable,
    get_status_week,
    get_thethe9_ranks,
    get_thethe9_ranks_jockey,
    get_thethe9_ranks_multi,
    get_track_record,
    get_train_horse,
    get_train_horse1,
    get_trainer_double_check,
    get_trainer_trend,
    get_training_awardee,
    get_treat_horse,
    get_last2weeks,
    get_weeks_status,
    insert_horse_disease,
    insert_race_judged,
    insert_race_simulation,
    insert_start_audit,
    insert_start_train,
    insert_train_swim,
    set_changed_race,
    set_changed_race_horse,
    set_changed_race_jockey,
    set_changed_race_rank,
    set_changed_race_weight,
    trend_title,
)
from base.simulation import mock_insert, mock_traval, get_weight

from base.race import countOfRace, recordsByHorse
from base.race_bet_guide import run_rguide_update
from base.train_LightGBM_roll12 import update_m_rank_score_for_period, update_m_rank_score_for_race
from letsrace.settings import KRAFILE_ROOT


from .forms import MyUserCreationForm, RoomForm, UserForm

# from django.contrib.auth.forms import UserCreationForm
from .models import (
    Exp010,
    Exp011,
    Exp011s1,
    Exp011s2,
    Message,
    RaceResult,
    Racing,
    Rec010,
    Rec011,
    RecordS,
    Room,
    Topic,
    User,
    Visitor,
    VisitorLog,
)

from django.core.files.storage import FileSystemStorage  # 파일저장

from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from django.utils import timezone


def loginPage(request):
    page = "login"

    # print(page)

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

        # print(form.errors)
        # print(form.non_field_errors())

        agree1 = request.POST.get("agree1")
        agree2 = request.POST.get("agree2")
        agree3 = request.POST.get("agree3")

        # print("aaa", agree1, agree2, agree3)

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

    # print(user)

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

    view_type = request.GET.get("view_type") if request.GET.get("view_type") != None else ""  # 정렬방식

    if q == "":
        # rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]  # 초기값은 금요일

        # rdate = Racing.objects.values("rdate").distinct().order_by("rdate")[:1]

        try:
            cursor = connection.cursor()

            strSql = """ 
                    SELECT min(rdate)
                    FROM The1.exp010
                    WHERE rdate >= ( SELECT MAX(DATE_FORMAT(CAST(rdate AS DATE) - INTERVAL 4 DAY, '%Y%m%d')) FROM The1.exp010 WHERE rno < 80)
                ; """

            cursor.execute(strSql)
            rdate = cursor.fetchall()

        except:
            print("Failed selecting in rdate")
        finally:
            cursor.close()

        # print(rdate[0][0], type(rdate))
        i_rdate = rdate[0][0]

        fdate = i_rdate[0:4] + "-" + i_rdate[4:6] + "-" + i_rdate[6:8]

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]

        i_rdate = rdate
        fdate = q

    # topics = Topic.objects.exclude(name__icontains=q)

    racings = get_race(i_rdate, i_awardee="jockey")
    # race_board = get_board_list(i_rdate, i_awardee="jockey")

    race, expects, rdays, judged_jockey, changed_race, award_j = get_prediction(i_rdate)
    # print(racings)

    if view_type == "1":
        # expects는 raw SQL fetchall 결과(튜플)일 수 있음. 안전하게 정렬 키를 구성.
        def _exp_key(row):
            # 객체(Attr) 또는 튜플(Idx) 모두 지원
            if hasattr(row, "rcity"):
                return (row.rcity, row.rdate, row.rno, row.rank, row.gate)
            # 튜플 인덱스: a.rcity(0), a.rdate(1), a.rno(3), b.gate(4), b.rank(5)
            try:
                return (row[0], row[1], row[3], row[5], row[4])
            except Exception:
                return row
        expects = sorted(expects, key=_exp_key)

    # expects Query
    try:
        cursor = connection.cursor()

        strSql = (
            """
            select a.rcity, a.rdate, a.rday, a.rno, b.gate, b.rank, b.r_rank, b.horse, b.remark, b.jockey, b.trainer, b.host, b.r_pop, a.distance, b.handycap, b.i_prehandy, b.complex,
                b.complex5, b.gap_back, 
                b.jt_per, b.jt_cnt, b.jt_3rd,
                b.s1f_rank, b.i_cycle, a.rcount, recent3, recent5, convert_r, jockey_old, reason, b.alloc3r*1
            
            from exp010 a, exp011 b
            where a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno
            and a.rdate between date_format(DATE_ADD(%s, INTERVAL - 3 DAY), '%%Y%%m%%d') and date_format(DATE_ADD(%s, INTERVAL + 4 DAY), '%%Y%%m%%d')
            and b.rank in ( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 98, 99 ) 
            order by b.rcity, b.rdate, b.rno, b.rank, b.gate 
            ; """
        )
        cursor.execute(strSql, (i_rdate, i_rdate))
        results = cursor.fetchall()

    except:
        # connection.rollback()
        print("Failed selecting in expect ")
    finally:
        cursor.close()

    # loadin = get_last2weeks_loadin(i_rdate)

    rflag = False  # 경마일, 비경마일 구분
    for r in rdays:
        # print(r[0], r[2])
        if r[0] == r[2]:
            rflag = True
            break

    check_visit(request)

    base_dt = datetime.strptime(i_rdate, "%Y%m%d")
    from_date = (base_dt - timedelta(days=3)).strftime("%Y%m%d")
    to_date = (base_dt + timedelta(days=4)).strftime("%Y%m%d")

    race_df, summary = calc_rpop_anchor_26_trifecta(
        from_date=from_date,
        to_date=to_date,
        bet_unit=100,
    )

    summary_display = []
    summary_total = None
    if isinstance(summary, dict):
        day_summary = summary.get("day_summary", {})
        total_races = 0
        total_bet = 0.0
        total_refund = 0.0
        total_hits = 0
        for day in sorted(day_summary.keys()):
            d = day_summary[day]
            refund_rate = (
                d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
            )
            hit_rate = d["hits"] / d["races"] if d["races"] > 0 else 0.0
            profit = d["total_refund"] - d["total_bet"]
            avg_bet = d["total_bet"] / d["races"] if d["races"] > 0 else 0.0
            summary_display.append(
                {
                    "date": day,
                    "races": d["races"],
                    "refund_rate": refund_rate,
                    "total_bet": d["total_bet"],
                    "total_refund": d["total_refund"],
                    "profit": profit,
                    "hits": d["hits"],
                    "hit_rate": hit_rate,
                    "avg_bet": avg_bet,
                }
            )
            total_races += d["races"]
            total_bet += d["total_bet"]
            total_refund += d["total_refund"]
            total_hits += d["hits"]
        if total_races > 0:
            total_profit = total_refund - total_bet
            total_refund_rate = total_refund / total_bet if total_bet > 0 else 0.0
            total_hit_rate = total_hits / total_races if total_races > 0 else 0.0
            total_avg_bet = total_bet / total_races if total_races > 0 else 0.0
            summary_total = {
                "races": total_races,
                "total_bet": total_bet,
                "total_refund": total_refund,
                "profit": total_profit,
                "hits": total_hits,
                "hit_rate": total_hit_rate,
                "refund_rate": total_refund_rate,
                "avg_bet": total_avg_bet,
            }
        else:
            summary_total = {
                "races": 0,
                "total_bet": 0.0,
                "total_refund": 0.0,
                "profit": 0.0,
                "hits": 0,
                "hit_rate": 0.0,
                "refund_rate": 0.0,
                "avg_bet": 0.0,
            }

    # print(summary_display)

    context = {
        "racings": racings,
        "expects": expects,
        "results": results,
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
        "judged_jockey": judged_jockey,
        "changed_race": changed_race,               #출마표 젼경
        "rflag": rflag,  # 경마일, 비경마일 구분
        "view_type": view_type,
        "summary": summary,
        "summary_display": summary_display,
        "summary_total": summary_total,

    }

    return render(request, "base/home.html", context)

# @login_required(login_url="home")
def racePrediction(request, rcity, rdate, rno, hname, awardee):

    view_type = (
        request.GET.get("view_type") if request.GET.get("view_type") != None else ""
    )  # 정렬방식

    if view_type == "1":
        exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
            "rank", "gate"
        )
    else:
        exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
            "r_pop", "gate"
        )
        
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

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    hr_records = recordsByHorse(rcity, rdate, rno, 'None')
    # print(hr_records)

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    # paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
    # paternal_dist = get_paternal_dist(rcity, rdate, rno)  # 부마 거리별 3착 성적

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)
    judged_list, judged = get_judged(rcity, rdate, rno)

    # # # axis = get_axis(rcity, rdate, rno)
    # axis1 = get_axis_rank(rcity, rdate, rno, 1)
    # axis2 = get_axis_rank(rcity, rdate, rno, 2)
    # axis3 = get_axis_rank(rcity, rdate, rno, 3)

    track = get_track_record(
        rcity, rdate, rno
    )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

    # 경주 메모 Query
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT replace( replace( horse, '[서]', ''), '[부]', ''), r_etc, r_flag, judge
                FROM rec011 
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s;
            """
            cursor.execute(query, (rcity, rdate, rno))
            r_memo = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in 경주 메모: {e}")
    finally:
        cursor.close()

    # 경주일 - 출주정보
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT rcity, rdate, rno, rday, rseq, distance, rcount, grade, dividing,
                    rname, rcon1, rcon2, rtime
                FROM exp010 
                WHERE rdate = %s
                ORDER BY rdate, rtime;
            """
            cursor.execute(query, (rdate,))
            weeksrace = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in exp010 : 주별 경주현황 - {e}")

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    check_visit(request)

    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 기수 기승가능 부딤중량
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        "judged_list": judged_list,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        # "axis1": axis1,
        # "axis2": axis2,
        # "axis3": axis3,
        "r_memo": r_memo,
        "track": track,
        "weeksrace": weeksrace,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
        "view_type": view_type,
    }

    return render(request, "base/race_prediction.html", context)


def raceResult(request, rcity, rdate, rno, hname, rcity1, rdate1, rno1):
    records = RecordS.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "rank", "gate"
    )
    if not records:
        return render(request, "base/home.html")

    # r_condition = Rec010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    r_condition = Rec010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).first()

    # rdate_1year = (
    #     str(int(rdate[0:4]) - 1) + rdate[4:8]
    # )  # 최근 1년 경주성적 조회조건 추가

    # hr_records = RecordS.objects.filter(
    #     rdate__lt=rdate, horse__in=records.values("horse")
    # ).order_by("horse", "-rdate")

    hr_records = recordsByHorse(rcity, rdate, rno, "None")

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

    # if len(judged) > 0:
    #     judged = judged[0][0]

    horses = Exp011.objects.values("horse").filter(rcity=rcity1, rdate=rdate1, rno=rno1)

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except Rec010.DoesNotExist:
        alloc = None

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT rcity, rdate, rno, rday, rseq, distance, rcount, grade, dividing, rname, rcon1, rcon2, rtime
                FROM exp010 
                WHERE rdate = %s
                ORDER BY rtime;
            """
            cursor.execute(query, (rdate,))
            weeksrace = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in exp010 : 주별 경주현황 - {e}")

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)
    check_visit(request)

    context = {
        "records": records,
        "r_condition": r_condition,
        "hr_records": hr_records,
        "compare_r": compare_r,
        "hname": hname,
        "judged_list": judged_list,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "horses": horses,
        "alloc": alloc,
        "weeksrace": weeksrace,
        "track": track,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "disease": disease,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
    }

    return render(request, "base/race_result.html", context)


# 출주마 경주결과
def raceResultHorse(request, rcity, rdate, rno, hname):

    hname = (
        request.GET.get("hname") if request.GET.get("hname") != None else hname.strip()
    )

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    exp011s = Exp011.objects.filter(
        rcity=rcity, rdate=rdate, rno=rno, horse=hname
    ).get()

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
            order by rank, gate
                ; """
        )

        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        h_names = cursor.fetchall()

        # connection.commit()
        # connection.close()

    except:
        # connection.rollback()
        print("Failed selecting in 게이트별 출주마")

    # 경주 메모 Query
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT replace( replace( horse, '[서]', ''), '[부]', ''), r_etc, r_flag
                FROM rec011 
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s;
            """
            cursor.execute(query, (rcity, rdate, rno))
            r_memo = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in 경주 메모: {e}")

    # train = get_train_horse1(rdate, hname)
    hr_records = recordsByHorse(rcity, rdate, rno, hname)

    check_visit(request)

    # print(hr_records)
    # print(hname in h_names)

    context = {
        "r_condition": r_condition,
        "hr_records": hr_records,
        "rdate": rdate,
        "exp011s": exp011s,
        "hname": hname,
        "h_names": h_names,
        "r_memo": r_memo,
    }

    return render(request, "base/race_result_horse.html", context)

# 축마 선정
def raceAxis(request, rcity, rdate, rno, jockey):

    exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno, jockey=jockey).get()
    if exp011s:
        pass
    else:
        return render(request, "base/home.html")

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    # axis = get_axis(rcity, rdate, rno)
    axis = get_axis_rank(rdate, jockey, r_condition.distance, exp011s.s1f_rank)

    # print(axis)
    # print(hname in h_names)

    context = {
        "axis": axis,
        "exp011s": exp011s,
        "r_condition": r_condition,
    }

    return render(request, "base/race_axis.html", context)


def raceTraining(request, rcity, rdate, rno):

    train = get_train_horse(rcity, rdate, rno)
    train_title = trend_title(rdate)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    check_visit(request)

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

    check_visit(request)

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

    check_visit(request)

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

    # award_j, award_t, award_h, race_detail = get_race_related(rcity, rdate, rno)

    paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
    paternal_dist = get_paternal_dist(rcity, rdate, rno)  # 부마 거리별 3착 성적

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    try:
        cursor = connection.cursor()
        strSql = """ 
            select host, horse, trainer, birthplace, sex, age, grade, tot_race, tot_1st, tot_2nd, tot_3rd, year_race, year_1st, year_2nd, year_3rd, tot_prize/1000, rating, price/1000
            from horse_w
            where wdate = ( select max(wdate) from The1.horse_w where wdate < %s )  
            and host in  ( select host from exp011 where rcity =  %s and rdate = %s and rno =  %s )
            order by host, trainer, horse
        """
        # 안전한 SQL 파라미터 바인딩
        params = (
            rdate,
            rcity,
            rdate,
            rno,
        )

        cursor.execute(strSql, params)
        horses = cursor.fetchall()

    except:
        print(f"❌ Failed selecting in horses:")  # 오류 메시지 출력
    finally:
        cursor.close()

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    view_type = (
        request.GET.get("view_type") if request.GET.get("view_type") != None else ""
    )  # 정렬방식
    if view_type == "1":
        # train는 raw SQL fetchall 결과(튜플)일 수 있음. 안전하게 정렬 키를 구성.
        def _exp_key(row):
            # 객체(Attr) 또는 튜플(Idx) 모두 지원
            if hasattr(row, "rcity"):
                return (row.rcity, row.rdate, row.rno, row.rank, row.gate)
            # 튜플 인덱스: a.rcity(0), a.rdate(1), a.rno(3), b.gate(4), b.rank(5)
            try:
                return (row[0], row[1], row[3], row[5], row[4])
            except Exception:
                return row

        train = sorted(train, key=_exp_key)

    # print(start_cnt)

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
        "start_cnt": start_cnt,
        "recovery_cnt": recovery_cnt,
        "audit_cnt": audit_cnt,
        # "award_h": award_h,
        # "race_detail": race_detail,
        "paternal": paternal,  
        "paternal_dist": paternal_dist,  
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 경주마 중대 질병 진료 회수
        "horses": horses,  
    }

    return render(request, "base/race_related_info.html", context)

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

@login_required(login_url="login")
def raceReview(request, rcity, rdate, rno):

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

    # print(r_condition.rcount)

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    judged_list, judged = get_judged(rcity, rdate, rno)

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    # exp011s = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)

    # user = request.user
    # form = UserForm(instance=user)

    if request.method == "POST":

        myDict = dict(request.POST)
        # print(myDict)
        # print(myDict['judge'][0])
        # print(exp011_cnt)

        for i in range(1, int(r_condition.rcount) +1 ):

            # print(i, myDict["r_etc"][i - 1])
            try:
                cursor = connection.cursor()

                strSql = (
                    """ update exp011
                                set r_rank = """
                    + myDict['r_rank'][i - 1]
                    + """
                            where rcity = '"""
                    + rcity
                    + """' and rdate = '"""
                    + rdate
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(i)
                    + """
                        ; """
                )

                # print(strSql)
                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

            except:
                # connection.rollback()
                print("Failed updating in exp011")

            try:

                cursor = connection.cursor()

                strSql = (
                    """ update rec011
                                set judge = '""" + myDict['judge'][0] + """' 
                                , r_start = '""" + myDict['start'][i - 1] + """'
                                , r_flag = '""" + myDict['flag'][i - 1] + """'
                                , r_etc = '""" + myDict['r_etc'][i - 1] + """' 
                            where rcity = '"""
                    + rcity
                    + """' and rdate = '"""
                    + rdate
                    + """' and rno = """
                    + str(rno)
                    + """ and gate = """
                    + str(i)
                    + """
                        ; """
                )

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                awards = cursor.fetchall()

            except:
                # connection.rollback()
                print("Failed updating in rec011")

    try:
        cursor = connection.cursor()
        strSql = """ select cd_type, r_code, r_name from race_cd order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race_cd = cursor.fetchall()

    except:
        print("Failed selecting r_start")
    finally:
        cursor.close()

    try:
        cursor = connection.cursor()
        strSql = (
            """ select a.rcity, a.rdate, a.rno, a.gate, a.horse, a.jockey, a.trainer, a.rank, a.r_rank, a.h_sex, a.h_age, a.birthplace, a.i_cycle, a.h_weight, a.handycap, a.i_prehandy, a.reason, a.alloc1r, a.alloc3r,
                    b.r_start, b.r_flag, b.r_etc, TRIM(b.judge)
            from exp011 a, rec011 b
            where a.rcity = b.rcity
            and a.rdate = b.rdate
            and a.rno = b.rno
            and a.gate = b.gate
            and a.rcity = '"""
            + rcity
            + """'
            and a.rdate = '"""
            + rdate
            + """' 
            and a.rno = """
            + str(rno)
            + """
            order by a.gate 
            ; """
        )

        # print(strSql)

        exp011_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        exp011s = cursor.fetchall()

        # print(r_cnt)

    except:
        print("Failed selecting expext record")
    finally:
        cursor.close()

    context = {
        "rcity": rcity,
        "exp011s": exp011s,
        "r_condition": r_condition,
        "race_cd": race_cd,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 기수 기승가능 부딤중량
        "judged_list": judged_list,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
    }
    return render(request, "base/race_review.html", context)


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
    elif fdata == "출발심사(b4)":
        result_cnt = insert_start_audit(r_content)
    elif fdata == "출발조교(b5)":
        result_cnt = insert_start_train(r_content)

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


# record calculation 기준정보 Setup
def raceCalculation(request):

    if request.method == "GET":
        q1 = request.GET.get("q1") if request.GET.get("q1") != None else ""
        q2 = request.GET.get("q2") if request.GET.get("q2") != None else ""

        if q1 == "":
            rday1 = Racing.objects.values("rdate").distinct()[0]["rdate"]  # weeks 기준일

            rday3 = Racing.objects.values("rdate").distinct()[2]["rdate"]  # weeks 기준일

            rdate1 = rday1[0:4] + rday1[4:6] + rday1[6:8]
            rdate2 = rday3[0:4] + rday3[4:6] + rday3[6:8]

            fdate1 = rday1[0:4] + "-" + rday1[4:6] + "-" + rday1[6:8]
            fdate2 = rday3[0:4] + "-" + rday3[4:6] + "-" + rday3[6:8]

        else:
            rdate1 = q1[0:4] + q1[5:7] + q1[8:10]
            rdate2 = q2[0:4] + q2[5:7] + q2[8:10]

            fdate1 = q1[0:4] + "-" + q1[5:7] + "-" + q1[8:10]
            fdate2 = q2[0:4] + "-" + q2[5:7] + "-" + q2[8:10]

        # print(rdate1, rdate2)
        exp010s = []

        # exp011 조회
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT rcity, rdate, rno, grade, rname, distance, dividing, rcount
                    FROM exp010
                    WHERE rdate between %s and %s
                    ORDER BY rcity, rdate, rno;
                """
                cursor.execute(query, (rdate1, rdate2))
                exp010s = cursor.fetchall()

        except Exception as e:
            print(f"❌ Failed selecting in 경주 메모: {e}")
        finally:
            cursor.close()

    if request.method == "POST":

        rdate1 = request.POST.get("rdate1") 
        rdate2 = request.POST.get("rdate2")

        q1 = request.POST.get("q1")
        q2 = request.POST.get("q2")

        fdate1 = q1[0:4] + "-" + q1[5:7] + "-" + q1[8:10]
        fdate2 = q2[0:4] + "-" + q2[5:7] + "-" + q2[8:10]

        rcheck1 = request.POST.get("rcheck1")

        # print(rdate1, rdate2, q1, q2, rcheck1)

        if rcheck1:

            # print("POST", rdate1, rdate2)
            # print("경주 기준정보 계산 시작", rdate1)

            ret = baseline_compute(connection, rdate1)
            if ret == 1:
                messages.success(request, "경주 기준정보 계산 완료.")
            else:
                messages.error(request, "경주 기준정보 계산 오류 발생.")

            renewal_record_s(connection, rdate1)

        else:

            print("집계안함", rdate1, rdate2)

        # exp011 조회
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT rcity, rdate, rno, grade, rname, distance, dividing, rcount
                    FROM exp010
                    WHERE rdate between %s and %s
                    ORDER BY rcity, rdate, rno;
                """
                cursor.execute(query, (rdate1, rdate2))
                exp010s = cursor.fetchall()

        except Exception as e:
            print(f"❌ Failed selecting in 경주 메모: {e}")
        finally:
            cursor.close()

        try:
            cursor = connection.cursor()

            strSql = """ 
                select w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert, 1 w_flag
                from weight
                where wdate = ( select max(wdate) from weight )
                
                ; """

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            weight = cursor.fetchall()

            # connection.commit()
            # connection.close()

        except:
            # connection.rollback()
            print("Failed inserting in weight")

        # print(weight)

        for index, exp010 in enumerate(exp010s):

            print(exp010[0], exp010[1], exp010[2], "경주 Mock Audit 시작")

            r_condition = Exp010.objects.filter(rcity=exp010[0], rdate=exp010[1], rno=exp010[2]).get()

            create_record(connection, r_condition, weight)

            execChatGPT(request, rcity=exp010[0], rdate=exp010[1], rno=exp010[2])

            print(exp010, "경주 집계 완료")

            # if exp010[2] == 1:
            #     break

        # m_rank m_score 갱신
        update_m_rank_score_for_period(
            rdate1,
            rdate2,
            # model_name="sb_top3_20241129_20251130",
            model_name=f"sb_top3_roll12_{rdate1[0:6]}"
        )

        update_exp011_for_period(rdate1, rdate2)         #f_score, f_rank 점수 갱신  
        # exp010 r_guide 업데이트 (기간)
        run_rguide_update(from_date=rdate1, to_date=rdate2, dry_run=False)

    context = {
        "q1": q1,
        "q2": q2,
        "rdate1": rdate1,
        "rdate2": rdate2,
        "fdate1": fdate1,
        "fdate2": fdate2,
        "exp010s": exp010s,
    }

    return render(request, "base/race_calculation.html", context)

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection, transaction
from django.contrib import messages
from django.db.models import Min, Max

# 필요한 유틸/모듈은 실제 위치에 따라 import 경로 조정
# from .models import Exp010, Exp011s2, Rec010, Rec011
# from .utils import get_weight2, mock_insert2, mock_traval2, recordsByHorse, get_track_record, get_loadin, get_disease, get_trainer_double_check, countOfRace


def mockAudit(request, rcity, rdate, rno, hname, awardee):
    """
    mockAudit view (리팩토링)
    - 기본: 초기 로드 -> 조회만 (집계 X)
    - ?calc=1 이면 -> 집계 로직 실행(UPDATE/INSERT 등) 후 HttpResponse 반환
    """
    weight = get_weight2(rcity, rdate, rno)  # 예상: list/tuple 형태
    # print("first weight:", weight)
    wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")

    w_avg = weight[0][0]
    w_fast = weight[0][1]
    w_slow = weight[0][2]
    w_recent3 = weight[0][3]
    w_recent5 = weight[0][4]
    w_convert = weight[0][5]
    w_flag = weight[0][6]

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    # print("r_condition:", r_condition)

    mock_insert2(rcity, rdate, rno)

    # 5) do_calc 체크: ?calc=1 이면 집계 실행 (fetch로 호출되는 경우)
    do_calc = request.GET.get("calc", "0")
    if do_calc == "1":

        # weight = get_weight2(rcity, rdate, rno)  # 예상: list/tuple 형태
        # print("weight:", weight[0][0])
        # wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")

        w_avg = request.GET.get("w_avg") 
        w_fast = request.GET.get("w_fast") 
        w_slow = request.GET.get("w_slow") 
        w_recent3 = request.GET.get("w_recent3") 
        w_recent5 = request.GET.get("w_recent5") 
        w_convert = request.GET.get("w_convert") 
        w_flag = request.GET.get("w_flag") 

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
        # print("1.weight_mock:", weight_mock)

        if (
            int(w_avg) + int(w_fast) + int(w_slow) == 100
            and int(w_recent3) + int(w_recent5) + int(w_convert) == 100  # 가중치 오류 check
        ):
            weight_sum_ok = True
        else:
            weight_sum_ok = False

        if weight_sum_ok:

            messages.warning(request, "weight ok")

            try:
                with connection.cursor() as cursor:
                    update_sql = """
                        UPDATE rec011
                        SET i_mock = NULL
                        WHERE horse IN (
                            SELECT horse FROM exp011 WHERE rcity = %s AND rdate = %s AND rno = %s
                        )
                    """
                    cursor.execute(update_sql, (rcity, rdate, rno))
            except Exception as e:
                print("❌ Failed updating rec011 i_mock:", e)
                # 오류 발생시 롤백 (cursor context manager 사용 시 자동 rollback 아님)
                try:
                    connection.rollback()
                except Exception:
                    pass
                return JsonResponse({"status": "error", "msg": "Broken pipe"})

            # INSERT weight_s2 (파라미터 바인딩으로 안전하게)
            try:
                with connection.cursor() as cursor:
                    insert_sql = """
                        INSERT INTO weight_s2
                        (rcity, rdate, rno, wdate, w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert)
                        VALUES (%s, %s, %s, now(), %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        insert_sql,
                        (
                            rcity,
                            rdate,
                            rno,
                            int(w_avg),
                            int(w_fast),
                            int(w_slow),
                            int(w_recent3),
                            int(w_recent5),
                            int(w_convert),
                        ),
                    )
            except Exception as e:
                print("❌ Failed inserting into weight_s2:", e)
                try:
                    connection.rollback()
                except Exception:
                    pass
                return JsonResponse({"status": "error", "msg": "Broken pipe"})

            try:
                mock_traval2(r_condition, weight_mock)
            except Exception as e:
                print("❌ mock_traval2 에러:", e)
                return JsonResponse({"status": "error", "msg": "Broken pipe"})

            # update_m_rank_score_for_race(
            #     rcity, rdate, rno, model_name="sb_top3_20241129_20251130"
            # )  # 저장해둔 모델 이름

            update_m_rank_score_for_race(
                rcity, rdate, rno, model_name=f"sb_top3_roll12_{rdate[0:6]}"
            )  # 저장해둔 모델 이름

        else:
            messages.error(request, "weight error")

        # print(f"✅ Mock 집계 실행 완료: {rcity}, {rdate}, {rno}")
        # Ajax 호출(프론트)의 경우 간단 텍스트 또는 JSON 반환
        return JsonResponse({"status": "ok", "message": "Mock 집계 완료"})

    # 6) calc != 1 이면 -> 초기 로드(조회) 모드: DB에서 필요한 데이터 조회 후 context 생성
    # exp011s 조회
    exp011s = Exp011s2.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
        "r_pop", "gate"
    )
    # for r in exp011s:
    #     print(r.s1f_rank, r.g1f_rank, r.g2f_rank, r.g3f_rank)

    if not exp011s.exists():
        return render(request, "base/home.html")

    # horse_records
    try:
        hr_records = recordsByHorse(rcity, rdate, rno, "None")
    except Exception as e:
        print("❌ recordsByHorse 에러:", e)
        hr_records = []

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

    # alloc (Rec010 존재 여부)
    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except Rec010.DoesNotExist:
        alloc = None

    # track, memo, loadin, disease, trainer check 등
    track = get_track_record(rcity, rdate, rno)

    try:
        with connection.cursor() as cursor:
            memo_sql = """
                SELECT REPLACE(REPLACE(horse, '[서]', ''), '[부]', ''), r_etc, r_flag, judge
                FROM rec011
                WHERE rcity = %s AND rdate = %s AND rno = %s
            """
            cursor.execute(memo_sql, (rcity, rdate, rno))
            r_memo = cursor.fetchall()
    except Exception as e:
        print("❌ Failed selecting in 경주 메모:", e)
        r_memo = []

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    # 7) context 구성 및 렌더
    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,
        "disease": disease,
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        "track": track,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        "weight": weight,
        "wdate": wdate,
        "w_avg": w_avg,
        "w_fast": w_fast,
        "w_slow": w_slow,
        "w_recent3": w_recent3,
        "w_recent5": w_recent5,
        "w_convert": w_convert,
        "r_memo": r_memo,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
    }

    return render(request, "base/mock_audit.html", context)


# def mockAudit(request, rcity, rdate, rno, hname, awardee):

#     weight = get_weight2(rcity, rdate, rno)
#     # print(weight[0][7])
#     wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")

#     # i_mock clear
#     try:
#         with connection.cursor() as cursor:

#             strSql = """
#                 UPDATE rec011
#                 SET i_mock = null
#                 WHERE horse in (select horse from exp011 where rcity = %s and rdate = %s and rno = %s)
#             """
#             r_cnt = cursor.execute(strSql, (rcity, rdate, rno))
#             # connection.commit()

#     except Exception as e:
#         print("❌ Failed updating rec011 i_mock:", rcity, rdate, rno, "| Error:", e)
#         connection.rollback()

#     mock_insert2(rcity, rdate, rno)

#     w_avg = (
#         request.GET.get("w_avg") if request.GET.get("w_avg") != None else weight[0][0]
#     )
#     w_fast = (
#         request.GET.get("w_fast") if request.GET.get("w_fast") != None else weight[0][1]
#     )
#     w_slow = (
#         request.GET.get("w_slow") if request.GET.get("w_slow") != None else weight[0][2]
#     )
#     w_recent3 = (
#         request.GET.get("w_recent3")
#         if request.GET.get("w_recent3") != None
#         else weight[0][3]
#     )
#     w_recent5 = (
#         request.GET.get("w_recent5")
#         if request.GET.get("w_recent5") != None
#         else weight[0][4]
#     )
#     w_convert = (
#         request.GET.get("w_convert")
#         if request.GET.get("w_convert") != None
#         else weight[0][5]
#     )
#     w_flag = (
#         request.GET.get("w_flag") if request.GET.get("w_flag") != None else weight[0][6]
#     )

#     r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

#     weight_mock = (
#         (
#             int(w_avg),
#             int(w_fast),
#             int(w_slow),
#             int(w_recent3),
#             int(w_recent5),
#             int(w_convert),
#             w_flag,
#         ),
#     )  # tuple로 정의

#     if weight == weight_mock:  # query 가중치와 입력된 가중치가 동일하면
#         # print("같음")
#         pass

#     if (
#         int(w_avg) + int(w_fast) + int(w_slow) == 100
#         and int(w_recent3) + int(w_recent5) + int(w_convert) == 100  # 가중치 오류 check
#     ):

#         if weight != weight_mock:  # 가중치가 뱐경되었으면
#             try:
#                 cursor = connection.cursor()

#                 strSql = (
#                     """
#                     insert into weight_s2
#                     (
#                         rcity,
#                         rdate,
#                         rno,
#                         wdate,
#                         w_avg,
#                         w_fast,
#                         w_slow,
#                         w_recent3,
#                         w_recent5,
#                         w_convert
#                     )
#                     VALUES
#                     (
#                         '"""
#                     + rcity
#                     + """',
#                         '"""
#                     + rdate
#                     + """',
#                         """
#                     + str(rno)
#                     + """,
#                         """
#                     " now() "
#                     """,
#                         """
#                     + str(w_avg)
#                     + """,
#                         """
#                     + str(w_fast)
#                     + """,
#                         """
#                     + str(w_slow)
#                     + """,
#                         """
#                     + str(w_recent3)
#                     + """,
#                         """
#                     + str(w_recent5)
#                     + """,
#                         """
#                     + str(w_convert)
#                     + """
#                     )
#                 ; """
#                 )

#                 r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
#                 weight = cursor.fetchall()

#             except:
#                 print("Failed inserting in weight_s1")
#             finally:
#                 connection.close()

#             mock = mock_traval2(r_condition, weight_mock)

#         if w_flag == 0:
#             messages.warning(request, "weight_s1")

#         else:
#             messages.warning(request, "weight only")

#     else:
#         messages.warning(request, "오류")
#         # weight = get_weight(rcity, rdate, rno)

#     # print(
#     #     "aaaa",
#     #     int(w_avg) + int(w_fast) + int(w_slow),
#     #     int(w_recent3) + int(w_recent5) + int(w_convert),
#     # )
#     # print(weight)

#     exp011s = Exp011s2.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
#         "rank", "gate"
#     )

#     if exp011s:
#         pass
#     else:
#         return render(request, "base/home.html")

#     hr_records = recordsByHorse(rcity, rdate, rno, 'None')

#     # print(hr_records)
#     compare_r = exp011s.aggregate(
#         Min("i_s1f"),
#         Min("i_g1f"),
#         Min("i_g2f"),
#         Min("i_g3f"),
#         Max("handycap"),
#         Max("rating"),
#         Max("r_pop"),
#         Max("j_per"),
#         Max("t_per"),
#         Max("jt_per"),
#         Min("recent5"),
#         Min("recent3"),
#         Min("convert_r"),
#         Min("s1f_rank"),
#     )

#     try:
#         alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
#     except:
#         alloc = None

#     track = get_track_record(
#         rcity, rdate, rno
#     )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

#     # 경주 메모 Query
#     try:
#         with connection.cursor() as cursor:
#             query = """
#                 SELECT replace( replace( horse, '[서]', ''), '[부]', ''), r_etc, r_flag, judge
#                 FROM rec011
#                 WHERE rcity = %s
#                 AND rdate = %s
#                 AND rno = %s;
#             """
#             cursor.execute(query, (rcity, rdate, rno))
#             r_memo = cursor.fetchall()

#     except Exception as e:
#         print(f"❌ Failed selecting in 경주 메모: {e}")
#     finally:
#         cursor.close()

#     loadin = get_loadin(rcity, rdate, rno)
#     disease = get_disease(rcity, rdate, rno)

#     trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

#     trainer_double_check = get_trainer_double_check(rcity, rdate, rno)

#     # axis = get_axis(rcity, rdate, rno)
#     # axis1 = get_axis_rank(rcity, rdate, rno, 1)
#     # axis2 = get_axis_rank(rcity, rdate, rno, 2)
#     # axis3 = get_axis_rank(rcity, rdate, rno, 3)

#     recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

#     context = {
#         "exp011s": exp011s,
#         "r_condition": r_condition,
#         "loadin": loadin,  # 기수 기승가능 부딤중량
#         "disease": disease,  # 기수 기승가능 부딤중량
#         "hr_records": hr_records,
#         "compare_r": compare_r,
#         "alloc": alloc,
#         "track": track,
#         #    'swim': swim,
#         # "h_audit": h_audit,
#         "trainer_double_check": str(trainer_double_check),
#         "training_cnt": training_cnt,
#         # "axis1": axis1,
#         # "axis2": axis2,
#         # "axis3": axis3,
#         "weight": weight,
#         "wdate": wdate,
#         "w_avg": w_avg,
#         "w_fast": w_fast,
#         "w_slow": w_slow,
#         "w_recent3": w_recent3,
#         "w_recent5": w_recent5,
#         "w_convert": w_convert,
#         "r_memo": r_memo,
#         "recovery_cnt": recovery_cnt,
#         "start_cnt": start_cnt,
#         "audit_cnt": audit_cnt,
#     }
#     return render(request, "base/mock_audit.html", context)


# @login_required(login_url="login")
# def mockAudit(request, rcity, rdate, rno, hname, awardee):
#     """
#     특정 경주에 대한 Mock Audit
#     - 처음 화면 진입(GET): 조회만
#     - 버튼 클릭 또는 요청 파라미터 있을 때: 집계 실행
#     """

#     # 1️⃣ 기본 가중치 조회
#     weight = get_weight2(rcity, rdate, rno)
#     wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")

#     # 2️⃣ 가중치 파라미터 (GET 요청이면 weight값 그대로)
#     w_avg = request.GET.get("w_avg") or weight[0][0]
#     w_fast = request.GET.get("w_fast") or weight[0][1]
#     w_slow = request.GET.get("w_slow") or weight[0][2]
#     w_recent3 = request.GET.get("w_recent3") or weight[0][3]
#     w_recent5 = request.GET.get("w_recent5") or weight[0][4]
#     w_convert = request.GET.get("w_convert") or weight[0][5]
#     w_flag = request.GET.get("w_flag") or weight[0][6]

#     # 3️⃣ 기본 조건
#     r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()

#     # 4️⃣ mock 집계 여부 체크 (예: "calc" 파라미터가 있을 때만 집계)
#     do_calc = request.GET.get("calc", "0")  # 기본값 0 → 조회만
#     if do_calc == "1":
#         print("✅ Mock 집계 실행 중:", rcity, rdate, rno)

#         # i_mock clear
#         try:
#             with connection.cursor() as cursor:
#                 strSql = """
#                     UPDATE rec011
#                     SET i_mock = null
#                     WHERE horse in (
#                         SELECT horse FROM exp011
#                         WHERE rcity = %s AND rdate = %s AND rno = %s
#                     )
#                 """
#                 cursor.execute(strSql, (rcity, rdate, rno))
#         except Exception as e:
#             print("❌ Failed updating rec011 i_mock:", e)
#             connection.rollback()

#         # mock 집계
#         mock_insert2(rcity, rdate, rno)
#         mock_traval2(
#             r_condition,
#             (
#                 (
#                     int(w_avg),
#                     int(w_fast),
#                     int(w_slow),
#                     int(w_recent3),
#                     int(w_recent5),
#                     int(w_convert),
#                     w_flag,
#                 ),
#             ),
#         )

#         messages.success(request, "Mock 집계가 완료되었습니다.")
#     else:
#         print("🔹 초기 로드: 집계 생략 (조회만 수행)")

#     # 5️⃣ 이하 조회용 쿼리 그대로 유지
#     exp011s = Exp011s2.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
#         "rank", "gate"
#     )
#     if not exp011s:
#         return render(request, "base/home.html")

#     hr_records = recordsByHorse(rcity, rdate, rno, "None")

#     compare_r = exp011s.aggregate(
#         Min("i_s1f"),
#         Min("i_g1f"),
#         Min("i_g2f"),
#         Min("i_g3f"),
#         Max("handycap"),
#         Max("rating"),
#         Max("r_pop"),
#         Max("j_per"),
#         Max("t_per"),
#         Max("jt_per"),
#         Min("recent5"),
#         Min("recent3"),
#         Min("convert_r"),
#         Min("s1f_rank"),
#     )

#     try:
#         alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
#     except:
#         alloc = None

#     track = get_track_record(rcity, rdate, rno)

#     # 경주 메모
#     try:
#         with connection.cursor() as cursor:
#             query = """
#                 SELECT REPLACE(REPLACE(horse, '[서]', ''), '[부]', ''), r_etc, r_flag, judge
#                 FROM rec011
#                 WHERE rcity = %s AND rdate = %s AND rno = %s;
#             """
#             cursor.execute(query, (rcity, rdate, rno))
#             r_memo = cursor.fetchall()
#     except Exception as e:
#         print(f"❌ Failed selecting in 경주 메모: {e}")
#         r_memo = []

#     loadin = get_loadin(rcity, rdate, rno)
#     disease = get_disease(rcity, rdate, rno)
#     trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)
#     recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

#     context = {
#         "exp011s": exp011s,
#         "r_condition": r_condition,
#         "loadin": loadin,
#         "disease": disease,
#         "hr_records": hr_records,
#         "compare_r": compare_r,
#         "alloc": alloc,
#         "track": track,
#         "trainer_double_check": str(trainer_double_check),
#         "training_cnt": training_cnt,
#         "weight": weight,
#         "wdate": wdate,
#         "w_avg": w_avg,
#         "w_fast": w_fast,
#         "w_slow": w_slow,
#         "w_recent3": w_recent3,
#         "w_recent5": w_recent5,
#         "w_convert": w_convert,
#         "r_memo": r_memo,
#         "recovery_cnt": recovery_cnt,
#         "start_cnt": start_cnt,
#         "audit_cnt": audit_cnt,
#     }
#     return render(request, "base/mock_audit.html", context)


from django.http import JsonResponse


def mockAccept(request, rcity, rdate, rno):
    """
    특정 경주에 대한 Mock Accept 처리를 수행하는 함수
    """
    if request.method == "GET":
        # 예시: 로그 출력
        print(f"Mock Accept 실행: {rcity}, {rdate}, {rno}")

        # 예시: DB 처리 로직
        try:
            cursor = connection.cursor()

            # complex5 update
            strSql = (
                """
                UPDATE exp011 a
                JOIN The1.exp011s2 b
                ON a.rcity = b.rcity
                AND a.rdate = b.rdate
                AND a.rno   = b.rno
                AND a.gate  = b.gate
                SET 
                    a.rank      = b.rank,
                    a.complex   = b.complex,
                    a.recent3   = b.recent3,
                    a.recent5   = b.recent5,
                    a.convert_r = b.convert_r,
                    a.rs1f      = b.rs1f,
                    a.rg3f      = b.rg3f,
                    a.rg2f      = b.rg2f,
                    a.rg1f      = b.rg1f,
                    a.cs1f      = b.cs1f,
                    a.cg3f      = b.cg3f,
                    a.cg2f      = b.cg2f,
                    a.cg1f      = b.cg1f,
                    a.i_s1f     = b.i_s1f,
                    a.i_g3f     = b.i_g3f,
                    a.i_g2f     = b.i_g2f,
                    a.i_g1f     = b.i_g1f,
                    a.s1f_rank  = b.s1f_rank,
                    a.g3f_rank  = b.g3f_rank,
                    a.g2f_rank  = b.g2f_rank,
                    a.g1f_rank  = b.g1f_rank,
                    a.remark    = b.remark,
                    a.bet       = b.bet,
                    a.complex5  = b.complex5,
                    a.gap       = b.gap,
                    a.gap_back  = b.gap_back
                WHERE a.rcity = '"""
                + rcity
                + """'
                AND a.rdate = '"""
                + rdate
                + """'
                AND a.rno  = """
                + str(rno)
                + """
                ; """
            )

            # print(strSql)

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            # connection.commit()

        except Exception as e:
            connection.rollback()
            print("Failed Update exp011 all :", e, strSql)
        finally:
            if cursor:
                cursor.close()

        # ✅ 반드시 HTTP 응답 객체를 반환해야 함
        return JsonResponse(
            {
                "status": "success",
                "message": f"Mock Accept 실행 완료 ({rcity}, {rdate}, {rno})",
            }
        )

    # 잘못된 요청일 경우
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

from django.http import JsonResponse
from django.db import connection

# from compute_gpt import process_race  # 우리가 만든 모듈

def execChatGPT(request, rcity, rdate, rno):
    """
    ChatGPT 기반 예측을 수행하는 함수
    - exp011에서 해당 경주마들 조회
    - compute_gpt.process_race 로 예측
    - 결과를 JSON으로 반환
    """

    cursor = None
    try:
        cursor = connection.cursor()

        # ✅ 안전한 파라미터 바인딩 사용
        strSql = """
            SELECT
                rcity,
                rdate,
                rno,
                gate,
                horse,
                birthplace,
                h_sex,
                h_age,
                handycap,
                joc_adv,
                jockey,
                trainer,
                host,
                rating,
                prize_tot,
                prize_year,
                prize_half,
                tot_1st,
                tot_2nd,
                tot_3rd,
                tot_race,
                year_1st,
                year_2nd,
                year_3rd,
                year_race,
                
                if(f_s2t(recent3) = 0,f_s2t(recent5),f_s2t(recent3)) AS recent3,
                f_s2t(recent5) AS recent5,
                if(f_s2t(fast_r) = 0,f_s2t(recent5),f_s2t(fast_r)) AS fast_r,
                if(f_s2t(slow_r) = 0,f_s2t(recent5),f_s2t(slow_r)) AS slow_r,
                if(f_s2t(avg_r) = 0,f_s2t(recent5),f_s2t(avg_r)) AS avg_r,

                rs1f,
                r1c,
                r2c,
                r3c,
                r4c,
                rg3f,
                rg2f,
                rg1f,

                cs1f,
                cg3f,
                cg2f,
                cg1f,
                rank,
                i_s1f,
                i_g3f,
                i_g2f,
                i_g1f,

                i_jockey,
                i_cycle,
                i_prehandy,

                remark,
                s1f_rank,
                g2f_rank,

                h_weight,
                j_per,
                t_per,
                jt_per,
                jt_cnt,
                jt_1st,
                jt_2nd,
                jt_3rd,
                ( select distance from exp010 where rcity = The1.exp011.rcity and rdate = The1.exp011.rdate and rno = The1.exp011.rno ) as distance
            FROM The1.exp011
            WHERE rcity = %s
            AND rdate = %s
            AND rno   = %s
            AND rank < 98
        ORDER BY gate ASC
        """
        
        # print(strSql % (rcity, rdate, rno))  # 디버깅용 출력

        cursor.execute(strSql, [rcity, rdate, rno])
        exp011s = cursor.fetchall()   # 튜플 리스트
        
        
        """       # ✅ g2f_update 함수 호출"""
        # for e in exp011s:
        #     rcity = e[0]
        #     rdate = e[1]
        #     horse = e[4]
        #     distance = e[52]
        #     print("g2f_update 호출:", rcity, rdate, horse, distance)
        #     try:
        #         g2f_update(rcity, rdate, horse, distance, connection,)
        #     except Exception as e:
        #         print("g2f_update 실패:", rcity, rdate, horse, distance, e)
            
            

        # ✅ compute_gpt.py 에서 만든 메인 함수 호출
        predictions = process_race(exp011s)

        print("✅ ChatGPT 예측 완료:")
        # 도표 형태로 출력 (콘솔)
        print(
            f"{'순위':^3} | {'마번':^3} | {'종합':^3} | "
            f"{'s1f':^5} | {'g3f':^5} | {'g1f':^5} | {'기록':^5} | {'최근8r':^5} | {'연대':^3} | {'선행%':^3} | {'마명':^10} | {'트렌드':^6} | {'코멘트':^6}"
        )
        print("-" * 100)

        if predictions:
            for p in predictions:

                r_pop = p["expected_rank"]
                tot_score = p["score"]
                s1f_per = p["early_score"]
                g3f_per = p["late_score"]
                g1f_per = p["late200_score"]
                rec_per = p["speed_score"]    
                rec8_trend = p["form_score"]
                jt_score = p["conn_score"]
                start_score = p["front_run_place_prob"]
                comment_one = p["one_line_comment"]
                comment_all = p["reason"]

                try:
                    cursor = connection.cursor()
                    update_sql = """
                        UPDATE exp011
                        SET r_pop = %s,
                            tot_score = %s,
                            s1f_per = %s,
                            g3f_per = %s,
                            g1f_per = %s,
                            rec_per = %s,
                            rec8_trend = %s,
                            jt_score = %s,
                            start_score = %s,
                            comment_one = %s,
                            comment_all = %s
                        WHERE rcity = %s AND rdate = %s AND rno = %s AND gate = %s
                    """
                    cursor.execute(
                        update_sql,
                        (
                            r_pop,
                            tot_score,
                            s1f_per,
                            g3f_per,
                            g1f_per,
                            rec_per,
                            rec8_trend,
                            jt_score,
                            start_score,
                            comment_one,
                            comment_all,
                            rcity,
                            rdate,
                            rno,
                            p["gate"],
                        ),
                    )
                    connection.commit()
                except Exception as e:
                    print(f"Failed to update exp011: {e}")
                finally:
                    if cursor:
                        cursor.close()

                score_display = p["score"] if p["score"] is not None else 0.0
                early_display = p["early_score"] if p["early_score"] is not None else 0.0
                late_display = p["late_score"] if p["late_score"] is not None else 0.0
                late200_display = (
                    p["late200_score"] if p["late200_score"] is not None else 0.0
                )
                speed_display = (
                    p["speed_score"] if p["speed_score"] is not None else 0.0
                )
                form_display = p["form_score"] if p["form_score"] is not None else 0.0
                conn_display = p["conn_score"] if p["conn_score"] is not None else 0.0
                front_display = (
                    p["front_run_place_prob"]
                    if p["front_run_place_prob"] is not None
                    else 0.0
                )

                one_line_display = (
                    p["one_line_comment"] if p["one_line_comment"] is not None else ""
                )
                reason_display = p["reason"] if p["reason"] is not None else ""

                print(
                    f"{p['expected_rank']:^4} | {p['gate']:^6} | "
                    f"{score_display:^6.2f} | {early_display:^5.1f} | {late_display:^5.1f} | {late200_display:^5.1f} | "
                    f"{speed_display:^6.1f} | {form_display:^6.1f} | {conn_display:^6.1f} | {front_display:^6.1f} | {p['horse']:10} | {one_line_display:^60} | {reason_display:^1000}"
                )

    except Exception as e:
        # 에러 내용도 같이 내려주면 디버깅 편함

        return JsonResponse(
            {
                "status": "error",
                "message": f"Failed Select exp011 / process_race: {e}",
            },
            status=500,
        )
    finally:
        if cursor:
            cursor.close()

    try:
        cursor = connection.cursor()
        update_sql = """
            UPDATE exp011
            SET r_pop = rank
            WHERE rcity = %s AND rdate = %s AND rno = %s AND rank >= 98
        """
        cursor.execute(
            update_sql,
            (
                rcity,
                rdate,
                rno
            ),
        )
        
        connection.commit()
    except Exception as e:
        print(f"Failed to update exp011: {e}")
    finally:
        if cursor:
            cursor.close()

    print("✅ ChatGPT 예측 exp011 tot_race = 0 update 완료")

    # update_m_rank_score_for_race(
    #             rcity, rdate, rno, model_name="sb_top3_20241129_20251130"
    #         )  # 저장해둔 모델 이름

    try:
        update_m_rank_score_for_race(
            rcity, rdate, rno, model_name=f"sb_top3_roll12_{rdate[0:6]}"
        )  # 저장해둔 모델 이름
    except Exception as e:
        print(f"⚠️ update_m_rank_score_for_race skipped: {e}")

    # exp011 점수/순위 반영 (단일 경주)
    try:
        update_exp011_for_race(rcity, rdate, int(rno))
    except Exception as e:
        print(f"⚠️ update_exp011_for_race skipped: {e}")

    # exp010 r_guide 업데이트 (단일 경주)
    try:
        info = run_rguide_update(
            rcity=rcity,
            rdate=rdate,
            rno=int(rno),
            dry_run=False,
        )
        updated = (info or {}).get("updated_rows")
        total = (info or {}).get("total_races")
        if updated is not None and total is not None:
            print(f"[done] {rcity} {rdate} R{rno} -> exp010={total} races, updated={updated} rows")
        else:
            print("✅ r_guide updated successfully.")
    except Exception as e:
        print(f"⚠️ r_guide update skipped: {e}")
    finally:
        print("---")

    # ✅ 예측 결과를 그대로 반환
    return JsonResponse(
        {
            "status": "success",
            "message": f"Exec chatGPT 실행 완료 ({rcity}, {rdate}, {rno})",
            "predictions": predictions,   # gate, horse, expected_rank, reason 등
        }
    )

def raceSimulation(request, rcity, rdate, rno, hname, awardee):

    weight = get_weight(rcity, rdate, rno)
    # print(weight[0][7])
    wdate = weight[0][7].strftime("%Y-%m-%d %H:%M:%S")
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

                r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
                weight = cursor.fetchall()

            except:
                print("Failed inserting in weight_s1")
            finally:
                connection.close()

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

    hr_records = recordsByHorse(rcity, rdate, rno, 'None')

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

    track = get_track_record(
        rcity, rdate, rno
    )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록

    # 경주 메모 Query
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT replace( replace( horse, '[서]', ''), '[부]', ''), r_etc, r_flag
                FROM rec011 
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s;
            """
            cursor.execute(query, (rcity, rdate, rno))
            r_memo = cursor.fetchall()

    except Exception as e:
        print(f"❌ Failed selecting in 경주 메모: {e}")
    finally:
        cursor.close()

    loadin = get_loadin(rcity, rdate, rno)
    disease = get_disease(rcity, rdate, rno)

    trainer_double_check, training_cnt = get_trainer_double_check(rcity, rdate, rno)

    trainer_double_check = get_trainer_double_check(rcity, rdate, rno)

    # axis = get_axis(rcity, rdate, rno)
    # axis1 = get_axis_rank(rcity, rdate, rno, 1)
    # axis2 = get_axis_rank(rcity, rdate, rno, 2)
    # axis3 = get_axis_rank(rcity, rdate, rno, 3)

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    context = {
        "exp011s": exp011s,
        "r_condition": r_condition,
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "disease": disease,  # 기수 기승가능 부딤중량
        "hr_records": hr_records,
        "compare_r": compare_r,
        "alloc": alloc,
        "track": track,
        #    'swim': swim,
        # "h_audit": h_audit,
        "trainer_double_check": str(trainer_double_check),
        "training_cnt": training_cnt,
        # "axis1": axis1,
        # "axis2": axis2,
        # "axis3": axis3,
        "weight": weight,
        "wdate": wdate,
        "w_avg": w_avg,
        "w_fast": w_fast,
        "w_slow": w_slow,
        "w_recent3": w_recent3,
        "w_recent5": w_recent5,
        "w_convert": w_convert,
        "r_memo": r_memo,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
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

    except:
        print("Failed selecting in trainer double cheeck")
    finally:
        connection.close()

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
    
    try:
        cursor = connection.cursor()

        strSql = """  
            select b.rcity,
                b.jockey awardee,
                b.rdate,
                a.rday,
                b.rno,
                a.grade,
                dividing,
                b.gate,
                b.rank,
                b.r_rank,
                b.horse,
                b.remark,
                b.jockey j_name,
                b.trainer t_name, b.host h_name,
                r_pop,
                a.distance,
                handycap,
                jt_per,
                jt_cnt,
                remark,
                s1f_rank,
                replace( corners, ' ', '') corners,
                g3f_rank,
                g1f_rank,
                alloc3r,
                jockey_old,
                reason
            from The1.exp010 a, The1.exp011 b 
            where a.rcity = b.rcity and a.rdate = b.rdate and a.rno = b.rno
            and a.rdate between date_format(DATE_ADD(%s, INTERVAL - 4 DAY), '%%Y%%m%%d') and date_format(DATE_ADD(%s, INTERVAL + 3 DAY), '%%Y%%m%%d')
            and a.rno < 80
            order by a.rdate, a.rtime, gate
            ; """
        cursor.execute(strSql, (rdate, rdate))
        race_detail = cursor.fetchall()

    except:
        print("Failed selecting in expect : 경주별 Detail(약식)) ")
    finally:
        cursor.close()

    context = {
        "trend_j": trend_j,
        "trend_j_title": trend_j_title,
        "trend_title": trend_title,
        "r_condition": r_condition,
        "awardee": awardee,
        "race_detail": race_detail,
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
        with connection.cursor() as cursor:
            query = """
                SELECT jockey, CAST(load_in AS DECIMAL)
                FROM jockey_w
                WHERE wdate = (SELECT MAX(wdate) FROM jockey_w WHERE wdate < %s);
            """
            cursor.execute(query, (tdate[0:4] + tdate[5:7] + tdate[8:10],))
            loadin = cursor.fetchall()

    except Exception as e:
        print(f"Failed selecting in 기승가능중량: {e}")

    
    # check_visit(request)

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
        with connection.cursor() as cursor:
            query = """
                SELECT jockey, CAST(load_in AS DECIMAL)
                FROM jockey_w
                WHERE wdate = (SELECT MAX(wdate) FROM jockey_w WHERE wdate < %s);
            """
            cursor.execute(query, (tdate[0:4] + tdate[5:7] + tdate[8:10],))
            loadin = cursor.fetchall()

    except Exception as e:
        print(f"Failed selecting in 기승가능중량: {e}")

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
        with connection.cursor() as cursor:
            query = """
                SELECT jockey, CAST(load_in AS DECIMAL)
                FROM jockey_w
                WHERE wdate = (SELECT MAX(wdate) FROM jockey_w WHERE wdate < %s);
            """
            cursor.execute(query, (tdate[0:4] + tdate[5:7] + tdate[8:10],))
            loadin = cursor.fetchall()

    except Exception as e:
        print(f"Failed selecting in 기승가능중량: {e}")

    # 경주별 출주 기수, 조교사, 마주 
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT gate, jockey, trainer, host, horse
                FROM exp011 
                WHERE rcity = %s
                AND rdate = %s
                AND rno = %s
                ORDER BY gate, jockey;
            """
            cursor.execute(query, (rcity, tdate[0:4] + tdate[5:7] + tdate[8:10], rno))
            jockeys = cursor.fetchall()

    except Exception as e:
        print(f"Failed selecting in 기승가능중량: {e}")

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

    check_visit(request)

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
def trainingAwardee(request, rdate, awardee, name, hname):

    status = get_training_awardee(rdate, awardee, name)
    train_title = trend_title(rdate)

    # print(status)

    context = {
        "status": status,
        "train_title": train_title,
        "awardee": awardee,
        "name": name,
        "hname": hname,
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
    check_visit(request)

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


# 기수 마방 연대 현황
def jtCollaboration(request, rcity, rdate, rno, jockey, trainer):

    collaboration = get_jt_collaboration(rcity, rdate, rno, jockey, trainer)
    check_visit(request)

    context = {
        "collaboration": collaboration,
        "rdate": rdate,
    }

    return render(request, "base/jt_collaboration.html", context)


# 기수 최근 2주간 훈련현황
def jockey2weekTrain(request, rcity, rdate, rno):

    j2week = get_jockeys_train(rcity, rdate, rno)

    context = {
        "j2week": j2week,
        "rdate": rdate,
    }

    return render(request, "base/jockey_2week_train.html", context)


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


def awardStatusWeek(request):
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

    week = get_status_week(
        friday
    )

    loadin = get_last2weeks_loadin(friday)

    check_visit(request)

    context = {
        "week": week,
        "loadin": loadin,
        "fdate": fdate,
        "rdate": rdate,
        "jname1": jname1,
        "jname2": jname2,
        "jname3": jname3,
    }

    return render(request, "base/award_status_week.html", context)


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

    # print(krafile)
    # print(kradata)

    if request.method == "POST":

        # print(krafile, "POST")
        myDict = dict(request.POST) 
        # print(myDict['fpath'])

        for index, rcheck in enumerate(myDict["rcheck"]):
            # print(rcheck)

            fpath = myDict['fpath'][index].strip()

            if rcheck == "0":
                krafile_convert(fpath)

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
        "rcity": rcity,
        "fcode": fcode,
        "fstatus": fstatus,
        "krafile": krafile,
        # 'kradata': kradata,
        "fdate1": fdate1,
        "fdate2": fdate2,
    }

    return render(request, "base/data_management.html", context)


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
        
        h_memo = request.POST.get("h_memo")
        print('---', h_memo)

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
                    and horse = '"""
                + horse
                + """'
                    ; """
            )

            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            awards = cursor.fetchall()

        except:
            # connection.rollback()
            print("Failed updating in rec011")
        finally:
            cursor.close()

        try:
            
            with connection.cursor() as cur:
                sql = """
                INSERT INTO horse_memo
                    ( horse, rdate, memo )
                VALUES
                    (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    memo      = VALUES(memo) 
                    
                """

                values = ( horse, rdate, h_memo.strip() )
                cur.execute(sql, values)
                # connection.commit()
                print("성공적으로 INSERT 또는 UPDATE 완료")

        except Exception as e:
            print("DB 처리 중 오류 발생:", e)
            # connection.rollback()

        finally:
            connection.close()
            
        try:
            cursor = connection.cursor()
            strSql = (
                """ update record_s set r_flag = '"""
                + r_flag
                + """'
                        where rdate = '"""
                + rdate
                + """'
                        and horse = '"""
                + horse
                + """'
                        ;"""
            )
            r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
            r_significant = cursor.fetchall()

        except:
            connection.rollback()
            print("Failed updating r_flag")
        finally:
            cursor.close()

    try:
        cursor = connection.cursor()
        strSql = (
            """ select r_start, r_corners, r_finish, r_wrapup, r_etc, r_flag
                    from rec011 
                    where rdate = '"""
            + rdate
            + """'
                    and horse = '"""
            + horse
            + """'
                    ;"""
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        r_significant = cursor.fetchall()

    except:
        print("Failed selecting start")
    finally:
        cursor.close()

    try:
        cursor = connection.cursor()
        strSql = (
            """ select memo
                    from horse_memo 
                    where rdate = '"""
            + rdate
            + """'
                    and horse = '"""
            + horse
            + """'
                    ;"""
        )
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        h_memo = cursor.fetchall()

    except:
        print("Failed selecting Horse Memo")
    finally:
        cursor.close()

    try:
        cursor = connection.cursor()
        strSql = """ select cd_type, r_code, r_name from race_cd order by r_code; """
        r_cnt = cursor.execute(strSql)  # 결과값 개수 반환
        race_cd = cursor.fetchall()

    except:
        print("Failed selecting r_start")
    finally:
        cursor.close()
        
    # print(r_significant, a)

    context = {
        "rdate": rdate,
        "horse": horse,
        "r_significant": r_significant,
        "race_cd": race_cd,
        # "r_start": r_start,
        # "r_corners": r_corners,
        # "r_finish": r_finish,
        # "r_wrapup": r_wrapup,
        "h_memo": h_memo,
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

    if name.startswith("15.177"):
        return

    update_visitor_count(name)

    new_visitor = Visitor(
        ip_address=name,
        user_agent=request.META.get("HTTP_USER_AGENT"),
        current=request.build_absolute_uri(),
        referer=request.META.get("HTTP_REFERER", "Unknown"),
        timestamp=timezone.now(),
    )
    new_visitor.save()

# def check_visit(request):
#     name = get_client_ip(request)

#     if name[0:6] != "15.177":
#         update_visitor_count(name)

#         # create a new Visitor instance
#         new_visitor = Visitor(
#             ip_address=name,
#             user_agent=request.META.get("HTTP_USER_AGENT"),
#             current = request.build_absolute_uri(), # 현재 페이지 정보
#             referer=request.META.get( "HTTP_REFERER", "Unknown"),  # referer 값이 없으면 기본값으로 "home" 설정
#             timestamp=timezone.now(),  # 현재 시간으로 설정
#         )

#         # insert the new_visitor object into the database
#         new_visitor.save()

#     # t_count = visitor_count()

#     return 0


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

        strSql = """
            SELECT jockey, CAST(load_in AS DECIMAL)
            FROM jockey_w
            WHERE wdate = (SELECT MAX(wdate) FROM jockey_w WHERE wdate < %s);
        """
        cursor.execute(strSql, (rdate,))
        loadin = cursor.fetchall()

    except:
        print("Failed selecting in 기승가능중량")
    finally:
        cursor.close()

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
        "winname": "weeksStatus",
    }

    return render(request, "base/weeks_status.html", context)
