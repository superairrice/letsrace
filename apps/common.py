from datetime import datetime, timedelta
from datetime import date, datetime
from email.message import EmailMessage
import logging
import os
from urllib.parse import unquote, urlsplit, urlunsplit

from django.contrib import messages

# from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import connection, DatabaseError, DataError, IntegrityError, transaction
from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Count, F, Max, Min, Q
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
    VisitorCount,
    VisitorLog,
)

from django.core.files.storage import FileSystemStorage  # 파일저장

from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.forms import PasswordChangeForm

from django.utils import timezone

logger = logging.getLogger(__name__)

VISIT_TRACKING_ENABLED = os.getenv("VISIT_TRACKING_ENABLED", "true").lower() == "true"
VISIT_THROTTLE_SECONDS = int(os.getenv("VISIT_THROTTLE_SECONDS", "60"))
TRUSTED_PROXY_IPS = {
    ip.strip() for ip in os.getenv("TRUSTED_PROXY_IPS", "").split(",") if ip.strip()
}


def get_client_ip(request):
    remote_addr = request.META.get("REMOTE_ADDR", "")
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    x_real_ip = (request.META.get("HTTP_X_REAL_IP") or "").strip()
    cf_connecting_ip = (request.META.get("HTTP_CF_CONNECTING_IP") or "").strip()
    # 신뢰 프록시에서 전달된 경우에만 X-Forwarded-For를 사용한다.
    if x_forwarded_for and remote_addr in TRUSTED_PROXY_IPS:
        ip = x_forwarded_for.split(",")[0].strip()
    elif x_real_ip:
        ip = x_real_ip
    elif cf_connecting_ip:
        ip = cf_connecting_ip
    elif x_forwarded_for and (not remote_addr or remote_addr in ("127.0.0.1", "::1")):
        # 로컬/프록시 개발환경 fallback
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = remote_addr.strip()
    return ip or "unknown"


def check_visit(request):
    if not VISIT_TRACKING_ENABLED:
        return

    name = get_client_ip(request)

    if name.startswith("15.177"):
        return

    # 요청 폭주 시 동일 방문에 대한 중복 DB write를 줄인다.
    if VISIT_THROTTLE_SECONDS > 0:
        throttle_key = f"visit:throttle:{name}:{request.path}"
        if cache.get(throttle_key):
            return
        cache.set(throttle_key, 1, VISIT_THROTTLE_SECONDS)

    update_visitor_count(name)

    try:
        current_url = unquote(request.build_absolute_uri() or "")
        referer_raw = request.META.get("HTTP_REFERER") or ""
        referer_url = unquote(referer_raw).strip() if referer_raw else "직접접속"

        # 프록시 환경에서 build_absolute_uri()가 http로 생성되는 경우를 보정한다.
        forwarded_proto = (request.META.get("HTTP_X_FORWARDED_PROTO") or "").split(",")[0].strip().lower()
        if current_url and forwarded_proto in ("http", "https"):
            split_url = urlsplit(current_url)
            if split_url.scheme and split_url.scheme != forwarded_proto:
                current_url = urlunsplit(
                    (
                        forwarded_proto,
                        split_url.netloc,
                        split_url.path,
                        split_url.query,
                        split_url.fragment,
                    )
                )

        if referer_url.lower() == "unknown":
            referer_url = "직접접속"

        new_visitor = Visitor(
            ip_address=name,
            user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:500],
            current=current_url[:500],
            referer=referer_url[:500],
            timestamp=timezone.now(),
        )
        new_visitor.save()
    except (OperationalError, ProgrammingError, DataError, IntegrityError, DatabaseError) as exc:
        # Dev/initial DB state에서 visitor 테이블이 없으면 홈 진입만 우선 허용.
        logger.warning("check_visit skipped: %s", exc)


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
    try:
        with transaction.atomic():
            updated = VisitorCount.objects.filter(date=today).update(count=F("count") + 1)
            if updated == 0:
                VisitorCount.objects.create(date=today, count=1)

            VisitorLog.objects.create(
                name=name,
                date=today,
                timestamp=timezone.now(),
            )
    except (OperationalError, ProgrammingError, DataError, IntegrityError, DatabaseError) as exc:
        logger.warning("update_visitor_count skipped: %s", exc)
