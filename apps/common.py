from datetime import datetime, timedelta
from datetime import date, datetime
from email.message import EmailMessage
import os

from django.contrib import messages

# from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Count, Max, Min, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render

from apps.domains.ops.g2f_update import g2f_update
from apps.domains.prediction.compute_gpt import process_race
from apps.domains.ops.data_management import (
    get_krafile,
    krafile_convert,
)

from apps.domains.race.race_compute import baseline_compute, create_record, renewal_record_s
from apps.domains.race.race_finalscore import update_exp010_overview_for_race, update_exp011_for_period, update_exp011_for_race
from apps.domains.race.race_refund import calc_rpop_anchor_26_trifecta
from apps.domains.prediction.simulation2 import get_weight2, mock_insert2, mock_traval2
from apps.domains.ops.mysqls import (
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
from apps.domains.prediction.simulation import mock_insert, mock_traval, get_weight

from apps.domains.race.race import countOfRace, recordsByHorse
from apps.domains.race.race_bet_guide import run_rguide_update
from apps.domains.prediction.train_LightGBM_roll12 import update_m_rank_score_for_period, update_m_rank_score_for_race
from letsrace.settings import KRAFILE_ROOT


from base.forms import RoomForm, UserForm

# from django.contrib.auth.forms import UserCreationForm
from base.models import (
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

from django.contrib.auth.forms import PasswordChangeForm

from django.utils import timezone


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
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

    try:
        new_visitor = Visitor(
            ip_address=name,
            user_agent=request.META.get("HTTP_USER_AGENT"),
            current=request.build_absolute_uri(),
            referer=request.META.get("HTTP_REFERER", "Unknown"),
            timestamp=timezone.now(),
        )
        new_visitor.save()
    except (OperationalError, ProgrammingError) as exc:
        # Dev/initial DB state에서 visitor 테이블이 없으면 홈 진입만 우선 허용.
        print(f"check_visit skipped: {exc}")


def visitor_count():
    today = date.today()
    user = (
        VisitorLog.objects.values("name")
        .filter(date=today)
        .annotate(max_count=Count("name"))
    )

    return user.count()


def update_visitor_count(name):
    today = date.today()
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    cursor = None
    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM base_visitorcount WHERE date = %s", (today,)
        )
        result = cursor.fetchone()

        if result[0] > 0:
            cursor.execute(
                "UPDATE base_visitorcount SET count = count + 1 WHERE date = %s",
                (today,),
            )
        else:
            cursor.execute(
                "INSERT INTO base_visitorcount (date, count) VALUES (%s, %s)",
                (today, 1),
            )

        sql = "INSERT INTO base_visitorlog (name, date, timestamp) VALUES (%s, %s, %s)"
        val = (name, today, timestamp)
        cursor.execute(sql, val)

        connection.commit()

    except (OperationalError, ProgrammingError) as exc:
        print(f"update_visitor_count skipped: {exc}")

    finally:
        if cursor:
            cursor.close()
