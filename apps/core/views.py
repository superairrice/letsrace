from apps.common import *
import contextlib
import io
import json
import logging
import copy
import hashlib
import pandas as pd
from time import perf_counter
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage as DjangoEmailMessage
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Count, F, Max, Q
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from base.models import Exp011, RaceComment, RaceCommentArchive
import smtplib
import re
from urllib.request import Request, urlopen
from urllib.parse import quote, urlparse, parse_qs
import xml.etree.ElementTree as ET
from html import unescape

logger = logging.getLogger(__name__)

ADMIN_PROFIT_TRIFECTA_BET_UNIT = 100
ADMIN_PROFIT_TRIO_BET_UNIT = 200


def _admin_method_sort_key(method: dict):
    label = str(method.get("label", "") or "").replace("  - ", "").strip()
    if "삼복" in label:
        type_order = 0
    elif "삼쌍" in label:
        type_order = 1
    else:
        type_order = 2
    return (type_order, label)


def _merge_admin_detail_methods_by_label(methods):
    merged = []
    index_by_label = {}
    for method in methods or []:
        label = str(method.get("label", "") or "")
        if label not in index_by_label:
            index_by_label[label] = len(merged)
            merged.append(dict(method))
            continue

        current = merged[index_by_label[label]]
        current["amount"] = float(current.get("amount", 0.0) or 0.0) + float(
            method.get("amount", 0.0) or 0.0
        )
        current["refund"] = float(current.get("refund", 0.0) or 0.0) + float(
            method.get("refund", 0.0) or 0.0
        )
        current["profit"] = float(current.get("profit", 0.0) or 0.0) + float(
            method.get("profit", 0.0) or 0.0
        )
        current["hits"] = int(current.get("hits", 0) or 0) + int(
            method.get("hits", 0) or 0
        )
        current_holes = int(current.get("holes_per_race", 0) or 0)
        incoming_holes = int(method.get("holes_per_race", 0) or 0)
        if current_holes != incoming_holes:
            raise ValueError(
                f"Duplicate admin strategy label with different holes_per_race: {label} "
                f"({current_holes} != {incoming_holes})"
            )
    return merged


def _drop_admin_strategy_result_columns(race_df, strategy_keys):
    if race_df is None or race_df.empty:
        return race_df

    drop_columns = set()
    for key in strategy_keys or []:
        column_meta = ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS.get(key) or {}
        for field in ("bet", "refund", "hit"):
            column_name = column_meta.get(field)
            if column_name:
                drop_columns.add(column_name)

    if not drop_columns:
        return race_df

    existing = [column for column in drop_columns if column in race_df.columns]
    if not existing:
        return race_df

    return race_df.drop(columns=existing)


def _admin_profit_has_hit(values):
    for value in values or []:
        try:
            if int(value or 0) > 0:
                return True
        except Exception:
            continue
    return False


def _admin_profit_hit_race_count(track_df, hit_cols):
    if track_df is None or getattr(track_df, "empty", True):
        return 0
    available_cols = [col for col in (hit_cols or []) if col in track_df.columns]
    if not available_cols:
        return 0
    return int(track_df[available_cols].fillna(0).astype(int).gt(0).any(axis=1).sum())


def _run_calc_rpop_anchor_26_trifecta_quietly(
    *,
    from_date,
    to_date,
    bet_unit=100,
    apply_odds_filter=False,
):
    """관리자 조회용 계산은 콘솔 출력/CSV 저장/주간 upsert 없이 실행한다."""
    from base import 총환수율_new as profit_base_mod

    original_upsert = profit_base_mod.upsert_weekly_betting_summary
    original_to_csv = pd.DataFrame.to_csv
    try:
        profit_base_mod.upsert_weekly_betting_summary = lambda *args, **kwargs: None
        pd.DataFrame.to_csv = lambda self, *args, **kwargs: None
        with contextlib.redirect_stdout(io.StringIO()):
            return calc_rpop_anchor_26_trifecta(
                from_date=from_date,
                to_date=to_date,
                bet_unit=bet_unit,
                apply_odds_filter=apply_odds_filter,
            )
    finally:
        profit_base_mod.upsert_weekly_betting_summary = original_upsert
        pd.DataFrame.to_csv = original_to_csv


def _nearest_saturday(dt):
    days_since_sat = (dt.weekday() - 5) % 7
    prev_sat = dt - timedelta(days=days_since_sat)
    next_sat = prev_sat + timedelta(days=7)
    if (dt - prev_sat) <= (next_sat - dt):
        return prev_sat
    return next_sat


def _prepare_admin_profit_analysis_race_df(
    i_rdate,
    bet_unit=ADMIN_PROFIT_TRIFECTA_BET_UNIT,
    trio_bet_unit=ADMIN_PROFIT_TRIO_BET_UNIT,
):
    try:
        base_dt = datetime.strptime(i_rdate, "%Y%m%d")
    except Exception:
        return {
            "from_date": None,
            "to_date": None,
            "race_df": None,
            "valid_race_keys": set(),
        }

    sat_dt = _nearest_saturday(base_dt)
    from_dt = sat_dt - timedelta(days=2)
    to_dt = sat_dt + timedelta(days=2)
    from_date = from_dt.strftime("%Y%m%d")
    to_date = to_dt.strftime("%Y%m%d")

    try:
        race_df, _summary = _run_calc_rpop_anchor_26_trifecta_quietly(
            from_date=from_date,
            to_date=to_date,
            bet_unit=bet_unit,
            apply_odds_filter=False,
        )
    except Exception as exc:
        print(f"[admin_profit_analysis_popup] calc failed: {exc}")
        race_df = None

    valid_race_keys = set()
    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        race_df = _filter_race_df_for_admin_profit_trio_odds(race_df)
        trio_strategy_keys = [
            "anchor1_23_46",
            "anchor1_24_56_trio",
            "anchor1_pair246_3_trio",
            "anchor1_3_47_trio",
            "top3pair_46_trio",
            "top4pair_56_trio",
        ]
        if trio_bet_unit != bet_unit:
            race_df = _drop_admin_strategy_result_columns(race_df, trio_strategy_keys)

        race_df = _augment_anchor1_25_6_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor1_25_67_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor1_26_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor2_37_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor2_pair146_378_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor1_second246_3578_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor1_third245_3678_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor2_pair345_678_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor2_36_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor1_23_46_trio_for_admin(race_df, bet_unit=trio_bet_unit)
        race_df = _augment_anchor1_24_56_trio_for_admin(race_df, bet_unit=trio_bet_unit)
        race_df = _augment_anchor1_pair246_3_trio_for_admin(race_df, bet_unit=trio_bet_unit)
        race_df = _augment_anchor1_3_47_trio_for_admin(race_df, bet_unit=trio_bet_unit)
        race_df = _augment_anchor3_pair124_56_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor4_pair123_56_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_pair58_anchor1_24_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor1_pair24_56_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor1_pair2_58_34_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor12_pair57_34_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor12_pair34_57_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor1_47_23_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor3_pair124_567_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor3_pair12_48_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor4_pair123_567_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor4_pair128_3567_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor4_box2356_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_anchor3_247_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_top3pair_46_trio_for_admin(race_df, bet_unit=trio_bet_unit)
        race_df = _augment_top4pair_56_trifecta_for_admin(race_df, bet_unit=bet_unit)
        race_df = _augment_top4pair_56_trio_for_admin(race_df, bet_unit=trio_bet_unit)
        race_df = _augment_anchor1_pair23_48_trifecta_for_admin(race_df, bet_unit=bet_unit)
        if not race_df.empty and {"경마장", "경주일", "경주번호"}.issubset(race_df.columns):
            valid_race_keys = {
                (str(row[0] or "").strip(), str(row[1]), int(row[2]))
                for row in race_df[["경마장", "경주일", "경주번호"]].itertuples(index=False, name=None)
            }
        if race_df.empty:
            race_df = None
    else:
        race_df = None

    return {
        "from_date": from_date,
        "to_date": to_date,
        "race_df": race_df,
        "valid_race_keys": valid_race_keys,
    }


def _env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return int(default)


HOME_DEFAULT_RDATE_CACHE_TTL = _env_int("HOME_DEFAULT_RDATE_CACHE_TTL", 600)
HOME_RACE_CACHE_TTL = _env_int("HOME_RACE_CACHE_TTL", 300)
HOME_NEWS_CACHE_TTL = _env_int("HOME_NEWS_CACHE_TTL", 1800)
HOME_NEWS_STALE_TTL = _env_int("HOME_NEWS_STALE_TTL", 21600)
HOME_NEWS_TIMEOUT_SEC = float(os.getenv("HOME_NEWS_TIMEOUT_SEC", "1.6"))
HOME_REFUND_CACHE_TTL = _env_int("HOME_REFUND_CACHE_TTL", 180)
HOME_RENDER_CACHE_TTL = _env_int("HOME_RENDER_CACHE_TTL", 20)
HOME_COMMENT_COUNT_CACHE_TTL = _env_int("HOME_COMMENT_COUNT_CACHE_TTL", 15)
HOME_TOP5_CACHE_TTL = _env_int("HOME_TOP5_CACHE_TTL", 20)
HOME_TOP5_DEBUG = os.getenv("HOME_TOP5_DEBUG", "false").lower() == "true"
HOME_RPOP2_DEBUG = os.getenv("HOME_RPOP2_DEBUG", "false").lower() == "true"


def _cache_copy_get(key):
    cached = cache.get(key)
    if cached is None:
        return None
    try:
        return copy.deepcopy(cached)
    except Exception:
        return cached


def _cache_copy_set(key, value, ttl):
    try:
        cache.set(key, copy.deepcopy(value), ttl)
    except Exception:
        cache.set(key, value, ttl)


def _resolve_home_rdate(q_value):
    q = (q_value or "").strip()
    today_ymd = datetime.now().strftime("%Y%m%d")
    if q:
        if len(q) == 10 and q[4] == "-" and q[7] == "-":
            return q[0:4] + q[5:7] + q[8:10]
        if len(q) == 8 and q.isdigit():
            return q

    cached = cache.get("home:default_rdate")
    if cached:
        return str(cached)
    return today_ymd


ADMIN_SUMMARY_METHOD_COLUMNS = [
    ("1축 2~4 5~7", "1축_2~4_5~7_베팅액", "1축_2~4_5~7_환수액", "r_pop1_축_2~4_5~7_적중"),
    ("1축 5~7 2~4", "1축_5~7_2~4_베팅액", "1축_5~7_2~4_환수액", "r_pop1_축_5~7_2~4_적중"),
    ("1축 2~4", "1축_2~4_베팅액", "1축_2~4_환수액", "r_pop1_축_2~4_적중"),
    ("r_pop 1~5 삼쌍승식", "r_pop1~5_BOX5_삼쌍_베팅액", "r_pop1~5_BOX5_삼쌍_환수액", "r_pop1~5_BOX5_삼쌍_적중"),
    ("1축 2~6 삼쌍", "1축_2~6_삼쌍_베팅액", "1축_2~6_삼쌍_환수액", "r_pop1_축_2~6_삼쌍_적중"),
    ("1~2복조 3~12 삼복", "1~2복조_3~12_삼복_베팅액", "1~2복조_3~12_삼복_환수액", "r_pop1~2_복조_3~12_삼복_적중"),
    ("BOX4 삼복", "BOX4_삼복_베팅액", "BOX4_삼복_환수액", "r_pop1~4_BOX4_삼복_적중"),
    ("r_pop 1~5 삼복승식", "r_pop1~5_BOX5_삼복_베팅액", "r_pop1~5_BOX5_삼복_환수액", "r_pop1~5_BOX5_삼복_적중"),
]

ADMIN_SUMMARY_SPECIAL_METHOD_COLUMNS = [
    ("r_pop 1~5 삼쌍승식", "r_pop1~5_BOX5_삼쌍_베팅액", "r_pop1~5_BOX5_삼쌍_환수액", "r_pop1~5_BOX5_삼쌍_적중"),
    ("1~2복조 3~12 삼복", "1~2복조_3~12_삼복_베팅액", "1~2복조_3~12_삼복_환수액", "r_pop1~2_복조_3~12_삼복_적중"),
    ("BOX4 삼복", "BOX4_삼복_베팅액", "BOX4_삼복_환수액", "r_pop1~4_BOX4_삼복_적중"),
    ("r_pop 1~5 삼복승식", "r_pop1~5_BOX5_삼복_베팅액", "r_pop1~5_BOX5_삼복_환수액", "r_pop1~5_BOX5_삼복_적중"),
]

ADMIN_SUMMARY_MAIN_METHOD_COLUMNS = [
    row
    for row in ADMIN_SUMMARY_METHOD_COLUMNS
    if row[0] not in {"r_pop 1~5 삼쌍승식", "1~2복조 3~12 삼복", "BOX4 삼복", "r_pop 1~5 삼복승식"}
]

ADMIN_PROFIT_GROUPS = {
    "부산": {
        "주력베팅": [
            "anchor1_24_58",
            "anchor1_58_24",
            "anchor1_25",
            "anchor1_23_47",
            "anchor1_47_23",
            "anchor1_pair246_3_trio",
            "anchor1_3_47_trio",
            "anchor1_23_46",
            "anchor1_second246_3578_trifecta",
            "anchor1_third245_3678_trifecta",
            "anchor2_pair345_678_trifecta",
            "anchor3_pair124_567_trifecta",
            "anchor4_box2356_trifecta",
        ],
        "보조베팅": [
            "anchor2_pair146_378_trifecta",
            "anchor1_pair23_48_besthit_trifecta",
            "anchor1_pair2_58_34_trifecta",
            "anchor12_pair57_34_trifecta",
            "anchor2_37_trifecta",
            "anchor1_25_68",
            "anchor4_pair123_56_trifecta",
            "anchor1_pair24_56_trifecta",
            "anchor4_pair123_567_trifecta",
            "anchor3_247",
            "anchor12_pair34_57_trifecta",
            "anchor1_25_6",
            "anchor1_25_67",
            "pair58_anchor1_24_trifecta",
        ],
    },
    "서울": {
        "주력베팅": [
            "anchor1_24_58",
            "anchor1_58_24",
            "anchor1_25",
            "anchor1_23_47",
            "anchor1_47_23",
            "anchor1_pair246_3_trio",
            "anchor1_3_47_trio",
            "anchor1_23_46",
            "anchor1_second246_3578_trifecta",
            "anchor1_third245_3678_trifecta",
            "anchor2_pair345_678_trifecta",
            "anchor3_pair124_567_trifecta",
            "anchor4_box2356_trifecta",
        ],
        "보조베팅": [
            "anchor2_pair146_378_trifecta",
            "anchor1_pair23_48_besthit_trifecta",
            "anchor1_pair2_58_34_trifecta",
            "anchor12_pair57_34_trifecta",
            "anchor2_37_trifecta",
            "anchor1_pair24_56_trifecta",
            "anchor4_pair123_56_trifecta",
            "anchor4_pair123_567_trifecta",
            "anchor3_247",
            "anchor12_pair34_57_trifecta",
            "anchor1_25_6",
            "anchor1_25_67",
            "anchor1_25_68",
            "pair58_anchor1_24_trifecta",
        ],
    },
}

ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS = {
    "anchor1_24_57": {
        "bet": "1축_2~4_5~7_베팅액",
        "refund": "1축_2~4_5~7_환수액",
        "hit": "r_pop1_축_2~4_5~7_적중",
        "holes_per_race": 9,
    },
    "anchor1_57_24": {
        "bet": "1축_5~7_2~4_베팅액",
        "refund": "1축_5~7_2~4_환수액",
        "hit": "r_pop1_축_5~7_2~4_적중",
        "holes_per_race": 9,
    },
    "anchor1_24_58": {
        "bet": "1축_2~4_5~8_베팅액",
        "refund": "1축_2~4_5~8_환수액",
        "hit": "r_pop1_축_2~4_5~8_적중",
        "holes_per_race": 12,
    },
    "anchor1_58_24": {
        "bet": "1축_5~8_2~4_베팅액",
        "refund": "1축_5~8_2~4_환수액",
        "hit": "r_pop1_축_5~8_2~4_적중",
        "holes_per_race": 12,
    },
    "anchor1_25": {
        "bet": "1축_2~5_베팅액",
        "refund": "1축_2~5_환수액",
        "hit": "r_pop1_축_2~5_적중",
        "holes_per_race": 12,
    },
    "anchor1_25_6": {
        "bet": "1축_2~5_6_베팅액",
        "refund": "1축_2~5_6_환수액",
        "hit": "r_pop1_축_2~5_6_적중",
        "holes_per_race": 4,
    },
    "anchor1_25_67": {
        "bet": "1축_2~5_6~7_베팅액",
        "refund": "1축_2~5_6~7_환수액",
        "hit": "r_pop1_축_2~5_6~7_적중",
        "holes_per_race": 8,
    },
    "anchor1_26": {
        "bet": "1축_2~6_삼쌍_베팅액",
        "refund": "1축_2~6_삼쌍_환수액",
        "hit": "r_pop1_축_2~6_삼쌍_적중",
        "holes_per_race": 20,
    },
    "anchor1_25_68": {
        "bet": "1축_2~5_6~8_베팅액",
        "refund": "1축_2~5_6~8_환수액",
        "hit": "r_pop1_축_2~5_6~8_적중",
        "holes_per_race": 12,
    },
    "anchor1_69_25": {
        "bet": "1축_6~9_2~5_베팅액",
        "refund": "1축_6~9_2~5_환수액",
        "hit": "r_pop1_축_6~9_2~5_적중",
        "holes_per_race": 16,
    },
    "anchor12_3_7": {
        "bet": "1축_2축_3~7_베팅액",
        "refund": "1축_2축_3~7_환수액",
        "hit": "r_pop1_1축_r_pop2_2축_3~7_적중",
        "holes_per_race": 5,
    },
    "anchor1_23_46": {
        "bet": "1축_2~3_4~6_삼복_베팅액",
        "refund": "1축_2~3_4~6_삼복_환수액",
        "hit": "r_pop1_축_2~3_4~6_삼복_적중",
        "holes_per_race": 6,
    },
    "anchor1_23_47": {
        "bet": "1축_2~3_4~7_베팅액",
        "refund": "1축_2~3_4~7_환수액",
        "hit": "r_pop1_축_2~3_4~7_적중",
        "holes_per_race": 8,
    },
    "anchor1_23_48": {
        "bet": "1축_2~3_4~8_베팅액",
        "refund": "1축_2~3_4~8_환수액",
        "hit": "r_pop1_축_2~3_4~8_적중",
        "holes_per_race": 40,
    },
    "anchor1_24_56_trio": {
        "bet": "1축_2~4_5~6_삼복_베팅액",
        "refund": "1축_2~4_5~6_삼복_환수액",
        "hit": "r_pop1_축_2~4_5~6_삼복_적중",
        "holes_per_race": 6,
    },
    "anchor3_24": {
        "bet": "3축_2~4_베팅액",
        "refund": "3축_2~4_환수액",
        "hit": "r_pop1_3축_2~4_적중",
        "holes_per_race": 6,
    },
    "anchor2_24": {
        "bet": "2축_2~4_베팅액",
        "refund": "2축_2~4_환수액",
        "hit": "r_pop1_2축_2~4_적중",
        "holes_per_race": 6,
    },
    "anchor1_24": {
        "bet": "1축_2~4_베팅액",
        "refund": "1축_2~4_환수액",
        "hit": "r_pop1_축_2~4_적중",
        "holes_per_race": 6,
    },
    "top4_box_trifecta": {
        "bet": "1~4_4복_베팅액",
        "refund": "1~4_4복_환수액",
        "hit": "r_pop1~4_4복_적중",
        "holes_per_race": 24,
    },
    "top5_box_trifecta": {
        "bet": "1~5_5복_베팅액",
        "refund": "1~5_5복_환수액",
        "hit": "r_pop1~5_5복_적중",
        "holes_per_race": 60,
    },
    "top6_trio": {
        "bet": "1~6_6복조_삼복_베팅액",
        "refund": "1~6_6복조_삼복_환수액",
        "hit": "r_pop1~6_6복조_삼복_적중",
        "holes_per_race": 20,
    },
    "top3pair_46_trio": {
        "bet": "1~3_복조_4~6_삼복_베팅액",
        "refund": "1~3_복조_4~6_삼복_환수액",
        "hit": "r_pop1~3_복조_4~6_삼복_적중",
        "holes_per_race": 9,
    },
    "top4pair_56_trifecta": {
        "bet": "1~4복조_5~6_삼쌍_베팅액",
        "refund": "1~4복조_5~6_삼쌍_환수액",
        "hit": "r_pop1~4_복조_5~6_삼쌍_적중",
        "holes_per_race": 24,
    },
    "anchor3_pair124_56_trifecta": {
        "bet": "3축_1~2,4_2축_5~6_3축_베팅액",
        "refund": "3축_1~2,4_2축_5~6_3축_환수액",
        "hit": "r_pop3_1축_1~2,4_2축_5~6_3축_적중",
        "holes_per_race": 6,
    },
    "anchor4_pair123_56_trifecta": {
        "bet": "4축_1~2,3_2축_5~6_3축_베팅액",
        "refund": "4축_1~2,3_2축_5~6_3축_환수액",
        "hit": "r_pop4_1축_1~2,3_2축_5~6_3축_적중",
        "holes_per_race": 6,
    },
    "pair58_anchor1_24_trifecta": {
        "bet": "5~8를1축_1을2축_2~4를3축_베팅액",
        "refund": "5~8를1축_1을2축_2~4를3축_환수액",
        "hit": "r_pop5~8_1축_r_pop1_2축_r_pop2~4_3축_적중",
        "holes_per_race": 12,
    },
    "anchor1_pair24_56_trifecta": {
        "bet": "1축_2~4_2축_5~6_3축_베팅액",
        "refund": "1축_2~4_2축_5~6_3축_환수액",
        "hit": "r_pop1_1축_2~4_2축_5~6_3축_적중",
        "holes_per_race": 6,
    },
    "anchor1_47_23": {
        "bet": "1축_4~7_2~3_베팅액",
        "refund": "1축_4~7_2~3_환수액",
        "hit": "r_pop1_축_4~7_2~3_적중",
        "holes_per_race": 8,
    },
    "anchor4_pair123_567_trifecta": {
        "bet": "4축_1~2,3_2축_5~7_3축_베팅액",
        "refund": "4축_1~2,3_2축_5~7_3축_환수액",
        "hit": "r_pop4_1축_1~2,3_2축_5~7_3축_적중",
        "holes_per_race": 9,
    },
    "anchor4_pair128_3567_trifecta": {
        "bet": "4축_1,2,8_2축_3,5,6,7_3축_베팅액",
        "refund": "4축_1,2,8_2축_3,5,6,7_3축_환수액",
        "hit": "r_pop4_1축_1,2,8_2축_3,5,6,7_3축_적중",
        "holes_per_race": 12,
    },
    "anchor3_pair12_48_trifecta": {
        "bet": "3축_1,2_2축_4~8_3축_베팅액",
        "refund": "3축_1,2_2축_4~8_3축_환수액",
        "hit": "r_pop3_1축_1,2_2축_4~8_3축_적중",
        "holes_per_race": 10,
    },
    "anchor3_pair124_567_trifecta": {
        "bet": "3축_1~2,4_2축_5~7_3축_베팅액",
        "refund": "3축_1~2,4_2축_5~7_3축_환수액",
        "hit": "r_pop3_1축_1~2,4_2축_5~7_3축_적중",
        "holes_per_race": 9,
    },
    "anchor3_247": {
        "bet": "3축_2,4~7_삼쌍_베팅액",
        "refund": "3축_2,4~7_삼쌍_환수액",
        "hit": "r_pop3_축_2,4~7_삼쌍_적중",
        "holes_per_race": 20,
    },
    "top4pair_56_trio": {
        "bet": "1~4복조_5~6_삼복_베팅액",
        "refund": "1~4복조_5~6_삼복_환수액",
        "hit": "r_pop1~4_복조_5~6_삼복_적중",
        "holes_per_race": 12,
    },
    "anchor2_37_trifecta": {
        "bet": "2축_3~7_삼쌍_베팅액",
        "refund": "2축_3~7_삼쌍_환수액",
        "hit": "r_pop2_축_3~7_삼쌍_적중",
        "holes_per_race": 20,
    },
    "anchor2_pair146_378_trifecta": {
        "bet": "2축_1,4~6_2축_3,7~8_3축_베팅액",
        "refund": "2축_1,4~6_2축_3,7~8_3축_환수액",
        "hit": "r_pop2_1축_1,4~6_2축_3,7~8_3축_적중",
        "holes_per_race": 12,
    },
    "anchor1_second246_3578_trifecta": {
        "bet": "1축_2,4,6_2축_1_3축_3,5,7,8_베팅액",
        "refund": "1축_2,4,6_2축_1_3축_3,5,7,8_환수액",
        "hit": "r_pop1_1축_2,4,6_2축_1_3축_3,5,7,8_적중",
        "holes_per_race": 12,
    },
    "anchor1_third245_3678_trifecta": {
        "bet": "1축_2,4,5_2축_3,6,7,8_3축_1_베팅액",
        "refund": "1축_2,4,5_2축_3,6,7,8_3축_1_환수액",
        "hit": "r_pop1_1축_2,4,5_2축_3,6,7,8_3축_1_적중",
        "holes_per_race": 12,
    },
    "anchor2_pair345_678_trifecta": {
        "bet": "2축_3,4,5_2축_6,7,8_3축_베팅액",
        "refund": "2축_3,4,5_2축_6,7,8_3축_환수액",
        "hit": "r_pop2_1축_3,4,5_2축_6,7,8_3축_적중",
        "holes_per_race": 9,
    },
    "anchor4_box2356_trifecta": {
        "bet": "4축_2,3,5,6_4복조_삼쌍_베팅액",
        "refund": "4축_2,3,5,6_4복조_삼쌍_환수액",
        "hit": "r_pop4_축_2,3,5,6_4복조_삼쌍_적중",
        "holes_per_race": 12,
    },
    "anchor2_36_trifecta": {
        "bet": "2축_3~6_삼쌍_베팅액",
        "refund": "2축_3~6_삼쌍_환수액",
        "hit": "r_pop2_축_3~6_삼쌍_적중",
        "holes_per_race": 12,
    },
    "anchor1_pair2_58_34_trifecta": {
        "bet": "1축_2,5~8_2축_3~4_3축_베팅액",
        "refund": "1축_2,5~8_2축_3~4_3축_환수액",
        "hit": "r_pop1_1축_2,5~8_2축_3~4_3축_적중",
        "holes_per_race": 10,
    },
    "anchor12_pair57_34_trifecta": {
        "bet": "1~2축_5~7_2축_3~4_3축_베팅액",
        "refund": "1~2축_5~7_2축_3~4_3축_환수액",
        "hit": "r_pop1~2_1축_5~7_2축_3~4_3축_적중",
        "holes_per_race": 12,
    },
    "anchor1_pair23_48_besthit_trifecta": {
        "bet": "1축_2~3_2축_4~8_3축_베팅액",
        "refund": "1축_2~3_2축_4~8_3축_환수액",
        "hit": "r_pop1_1축_2~3_2축_4~8_3축_적중",
        "holes_per_race": 10,
    },
    "anchor12_pair34_57_trifecta": {
        "bet": "1~2축_3~4_2축_5~7_3축_베팅액",
        "refund": "1~2축_3~4_2축_5~7_3축_환수액",
        "hit": "r_pop1~2_1축_3~4_2축_5~7_3축_적중",
        "holes_per_race": 12,
    },
    "anchor1_pair246_3_trio": {
        "bet": "1축_2,4~6_3_삼복_베팅액",
        "refund": "1축_2,4~6_3_삼복_환수액",
        "hit": "r_pop1_축_2,4~6_3_삼복_적중",
        "holes_per_race": 4,
    },
    "anchor1_3_47_trio": {
        "bet": "1축_3_4~7_삼복_베팅액",
        "refund": "1축_3_4~7_삼복_환수액",
        "hit": "r_pop1_축_3_4~7_삼복_적중",
        "holes_per_race": 4,
    },
}

ADMIN_PROFIT_STRATEGY_LABELS = {
    "anchor1_24_57": "1 / (2~4) / (5~7) 삼쌍",
    "anchor1_57_24": "1 / (5~7) / (2~4) 삼쌍",
    "anchor1_24_58": "1 / (2~4) / (5~8) 삼쌍",
    "anchor1_58_24": "1 / (5~8) / (2~4) 삼쌍",
    "anchor1_24": "1 / (2~4) 3복조 삼쌍",
    "anchor1_25": "1 / (2~5) 삼쌍",
    "anchor1_25_6": "1 / (2~5) / 6 삼쌍",
    "anchor1_25_67": "1 / (2~5) / (6~7) 삼쌍",
    "anchor1_26": "1 / (2~6) 삼쌍",
    "anchor1_25_68": "1 / (2~5) / (6~8) 삼쌍",
    "anchor1_69_25": "1 / (6~9) / (2~5) 삼쌍",
    "anchor12_3_7": "1 / 2 / (3~7) 삼쌍",
    "anchor1_23_46": "1 / (2~3) / (4~6) 삼복",
    "anchor1_23_47": "1 / (2~3) / (4~7) 삼쌍",
    "anchor1_23_48": "1 / (2~3) / (4~8) 삼쌍",
    "anchor1_24_56_trio": "1 / (2~4) / (5~6) 삼복",
    "anchor3_24": "3 / 1 / (2~4) 삼쌍",
    "anchor2_24": "2 / 1 / (2~4) 삼쌍",
    "top4_box_trifecta": "1~4 4복 삼쌍",
    "top5_box_trifecta": "1~5 5복 삼쌍",
    "top6_trio": "1~6 6복 삼복",
    "top3pair_46_trio": "1~3 복조 / 4~6 삼복",
    "top4pair_56_trifecta": "1~4 복조 / 5~6 삼쌍",
    "anchor3_pair124_56_trifecta": "3 / (1,2,4) / (5~6) 삼쌍",
    "anchor4_pair123_56_trifecta": "4 / (1~3) / (5~6) 삼쌍",
    "pair58_anchor1_24_trifecta": "(5~8) / 1 / (2~4) 삼쌍",
    "anchor1_pair24_56_trifecta": "1 / (2~4) / (5~6) 삼쌍",
    "anchor1_47_23": "1 / (4~7) / (2~3) 삼쌍",
    "anchor4_pair123_567_trifecta": "4 / (1~3) / (5~7) 삼쌍",
    "anchor4_pair128_3567_trifecta": "4 / (1,2,8) / (3,5~7) 삼쌍",
    "anchor3_pair12_48_trifecta": "3 / (1~2) / (4~8) 삼쌍",
    "anchor3_pair124_567_trifecta": "3 / (1,2,4) / (5~7) 삼쌍",
    "anchor3_247": "3 / (2,4~7) 삼쌍",
    "top4pair_56_trio": "1~4 복조 / 5~6 삼복",
    "anchor2_37_trifecta": "2 / (3~7) 삼쌍",
    "anchor2_pair146_378_trifecta": "2 / (1,4~6) / (3,7~8) 삼쌍",
    "anchor1_second246_3578_trifecta": "(2,4,6) / 1 / (3,5,7,8) 삼쌍",
    "anchor1_third245_3678_trifecta": "(2,4,5) / (3,6,7,8) / 1 삼쌍",
    "anchor2_pair345_678_trifecta": "2 / (3,4,5) / (6,7,8) 삼쌍",
    "anchor4_box2356_trifecta": "4 / (2,3,5,6) 4복조 삼쌍",
    "anchor2_36_trifecta": "2 / (3~6) 삼쌍",
    "anchor1_pair2_58_34_trifecta": "1 / (2,5~8) / (3~4) 삼쌍",
    "anchor12_pair57_34_trifecta": "(1~2) / (5~7) / (3~4) 삼쌍",
    "anchor1_pair23_48_besthit_trifecta": "1 / (2~3) / (4~8) 삼쌍",
    "anchor12_pair34_57_trifecta": "(1~2) / (3~4) / (5~7) 삼쌍",
    "anchor1_pair246_3_trio": "1 / (2,4~6) / 3 삼복",
    "anchor1_3_47_trio": "1 / 3 / (4~7) 삼복",
}


def _admin_combo_card(title, values):
    return {
        "title": title,
        "values": [int(value) for value in values],
        "text": ", ".join(str(value) for value in values),
    }


def _admin_combo_pattern_catalog():
    def permute_with_fixed_first(first, second_group, third_group=None):
        tickets = []
        if third_group is None:
            for second in second_group:
                for third in second_group:
                    if second == third:
                        continue
                    tickets.append(f"{first}-{second}-{third}")
            return tickets
        for second in second_group:
            for third in third_group:
                if len({first, second, third}) < 3:
                    continue
                tickets.append(f"{first}-{second}-{third}")
        return tickets

    def ordered_product(first_group, second_group, third_group):
        tickets = []
        for first in first_group:
            for second in second_group:
                for third in third_group:
                    if len({first, second, third}) < 3:
                        continue
                    tickets.append(f"{first}-{second}-{third}")
        return tickets

    def trio_product(group_a, group_b, group_c):
        tickets = []
        for first in group_a:
            for second in group_b:
                for third in group_c:
                    combo = [first, second, third]
                    if len(set(combo)) < 3:
                        continue
                    tickets.append("-".join(str(value) for value in sorted(combo)))
        return sorted(set(tickets), key=lambda item: [int(part) for part in item.split("-")])

    catalog = {
        "anchor1_pair2_58_34_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1축", [1]),
                _admin_combo_card("2,5~8", [2, 5, 6, 7, 8]),
                _admin_combo_card("3~4", [3, 4]),
            ],
            "tickets": ordered_product([1], [2, 5, 6, 7, 8], [3, 4]),
        },
        "anchor12_pair57_34_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1~2", [1, 2]),
                _admin_combo_card("5~7", [5, 6, 7]),
                _admin_combo_card("3~4", [3, 4]),
            ],
            "tickets": ordered_product([1, 2], [5, 6, 7], [3, 4]),
        },
        "anchor1_pair246_3_trio": {
            "bet_type": "삼복",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("2,4~6", [2, 4, 5, 6]),
                _admin_combo_card("3", [3]),
            ],
            "tickets": trio_product([1], [2, 4, 5, 6], [3]),
        },
        "anchor1_3_47_trio": {
            "bet_type": "삼복",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("3", [3]),
                _admin_combo_card("4~7", [4, 5, 6, 7]),
            ],
            "tickets": trio_product([1], [3], [4, 5, 6, 7]),
        },
        "anchor2_pair146_378_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("2축", [2]),
                _admin_combo_card("1,4~6", [1, 4, 5, 6]),
                _admin_combo_card("3,7~8", [3, 7, 8]),
            ],
            "tickets": ordered_product([2], [1, 4, 5, 6], [3, 7, 8]),
        },
        "anchor1_second246_3578_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("2,4,6", [2, 4, 6]),
                _admin_combo_card("1", [1]),
                _admin_combo_card("3,5,7,8", [3, 5, 7, 8]),
            ],
            "tickets": ordered_product([2, 4, 6], [1], [3, 5, 7, 8]),
        },
        "anchor1_third245_3678_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("2,4,5", [2, 4, 5]),
                _admin_combo_card("3,6,7,8", [3, 6, 7, 8]),
                _admin_combo_card("1", [1]),
            ],
            "tickets": ordered_product([2, 4, 5], [3, 6, 7, 8], [1]),
        },
        "anchor2_pair345_678_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("2", [2]),
                _admin_combo_card("3,4,5", [3, 4, 5]),
                _admin_combo_card("6,7,8", [6, 7, 8]),
            ],
            "tickets": ordered_product([2], [3, 4, 5], [6, 7, 8]),
        },
        "anchor1_25": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1축", [1]),
                _admin_combo_card("2~5", [2, 3, 4, 5]),
            ],
            "tickets": permute_with_fixed_first(1, [2, 3, 4, 5]),
        },
        "anchor1_58_24": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("5~8", [5, 6, 7, 8]),
                _admin_combo_card("2~4", [2, 3, 4]),
            ],
            "tickets": ordered_product([1], [5, 6, 7, 8], [2, 3, 4]),
        },
        "anchor1_47_23": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("4~7", [4, 5, 6, 7]),
                _admin_combo_card("2~3", [2, 3]),
            ],
            "tickets": ordered_product([1], [4, 5, 6, 7], [2, 3]),
        },
        "anchor1_pair23_48_besthit_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("2~3", [2, 3]),
                _admin_combo_card("4~8", [4, 5, 6, 7, 8]),
            ],
            "tickets": ordered_product([1], [2, 3], [4, 5, 6, 7, 8]),
        },
        "anchor4_pair123_56_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("4", [4]),
                _admin_combo_card("1~3", [1, 2, 3]),
                _admin_combo_card("5~6", [5, 6]),
            ],
            "tickets": ordered_product([4], [1, 2, 3], [5, 6]),
        },
        "anchor1_pair24_56_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("2~4", [2, 3, 4]),
                _admin_combo_card("5~6", [5, 6]),
            ],
            "tickets": ordered_product([1], [2, 3, 4], [5, 6]),
        },
        "anchor4_pair123_567_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("4", [4]),
                _admin_combo_card("1~3", [1, 2, 3]),
                _admin_combo_card("5~7", [5, 6, 7]),
            ],
            "tickets": ordered_product([4], [1, 2, 3], [5, 6, 7]),
        },
        "anchor3_247": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("3축", [3]),
                _admin_combo_card("2,4~7", [2, 4, 5, 6, 7]),
            ],
            "tickets": permute_with_fixed_first(3, [2, 4, 5, 6, 7]),
        },
        "anchor1_23_47": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("2~3", [2, 3]),
                _admin_combo_card("4~7", [4, 5, 6, 7]),
            ],
            "tickets": ordered_product([1], [2, 3], [4, 5, 6, 7]),
        },
        "anchor12_pair34_57_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1~2", [1, 2]),
                _admin_combo_card("3~4", [3, 4]),
                _admin_combo_card("5~7", [5, 6, 7]),
            ],
            "tickets": ordered_product([1, 2], [3, 4], [5, 6, 7]),
        },
        "anchor1_25_6": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("2~5", [2, 3, 4, 5]),
                _admin_combo_card("6", [6]),
            ],
            "tickets": ordered_product([1], [2, 3, 4, 5], [6]),
        },
        "anchor1_25_67": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("2~5", [2, 3, 4, 5]),
                _admin_combo_card("6~7", [6, 7]),
            ],
            "tickets": ordered_product([1], [2, 3, 4, 5], [6, 7]),
        },
        "anchor1_25_68": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("1", [1]),
                _admin_combo_card("2~5", [2, 3, 4, 5]),
                _admin_combo_card("6~8", [6, 7, 8]),
            ],
            "tickets": ordered_product([1], [2, 3, 4, 5], [6, 7, 8]),
        },
        "pair58_anchor1_24_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("5~8", [5, 6, 7, 8]),
                _admin_combo_card("1", [1]),
                _admin_combo_card("2~4", [2, 3, 4]),
            ],
            "tickets": ordered_product([5, 6, 7, 8], [1], [2, 3, 4]),
        },
        "anchor3_pair124_567_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("3", [3]),
                _admin_combo_card("1,2,4", [1, 2, 4]),
                _admin_combo_card("5~7", [5, 6, 7]),
            ],
            "tickets": ordered_product([3], [1, 2, 4], [5, 6, 7]),
        },
        "anchor4_box2356_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _admin_combo_card("4", [4]),
                _admin_combo_card("2,3,5,6", [2, 3, 5, 6]),
            ],
            "tickets": permute_with_fixed_first(4, [2, 3, 5, 6]),
        },
    }

    for strategy_key, payload in catalog.items():
        payload["label"] = ADMIN_PROFIT_STRATEGY_LABELS.get(strategy_key, strategy_key)
        payload["holes_per_race"] = len(payload.get("tickets", []))
    return catalog


def _first_gate(values):
    return values[0] if values else None


def _gate_group(label, values):
    normalized = []
    seen = set()
    for value in values or []:
        try:
            gate = int(value)
        except Exception:
            continue
        if gate <= 0 or gate in seen:
            continue
        seen.add(gate)
        normalized.append(gate)
    if not normalized:
        return None
    return {
        "label": label,
        "gates": normalized,
        "text": ", ".join(str(gate) for gate in normalized),
    }


def _build_admin_profit_strategy_gate_groups(row_map, strategy_key):
    top3 = _parse_gate_list(row_map.get("r_pop_top3_마번"))
    top4 = _parse_gate_list(row_map.get("r_pop_top4_마번"))
    top6 = _parse_gate_list(row_map.get("r_pop_top6_마번"))
    anchor = _parse_gate_list(row_map.get("축마"))
    second_anchor = _parse_gate_list(row_map.get("2축마"))
    top2_4 = _parse_gate_list(row_map.get("2~4_마번"))
    top2_5 = _parse_gate_list(row_map.get("2~5_마번"))
    top2_6 = _parse_gate_list(row_map.get("2~6_마번"))
    top4_6 = _parse_gate_list(row_map.get("4~6_마번"))
    top5_7 = _parse_gate_list(row_map.get("5~7_마번"))
    top5_8 = _parse_gate_list(row_map.get("5~8_마번"))
    top6_8 = _parse_gate_list(row_map.get("6~8_마번"))
    top3_7 = _parse_gate_list(row_map.get("3~7_마번"))
    top3_8_12 = _parse_gate_list(row_map.get("3~8,12_마번"))

    r_pop1 = _first_gate(top3) or _first_gate(top4) or _first_gate(top6)
    r_pop2 = top3[1] if len(top3) > 1 else None
    r_pop3 = top3[2] if len(top3) > 2 else None
    r_pop4 = top4[3] if len(top4) > 3 else None
    top5_6 = top6[4:6] if len(top6) >= 6 else top5_8[:2]
    top4_7 = ([r_pop4] if r_pop4 else []) + list(top5_7)
    top3_4 = [gate for gate in [r_pop3, r_pop4] if gate]
    top1_2 = [gate for gate in [r_pop1, r_pop2] if gate]
    top1_3 = [gate for gate in [r_pop1, r_pop2, r_pop3] if gate]
    top1_2_4 = [gate for gate in [r_pop1, r_pop2, r_pop4] if gate]
    top2_58 = ([r_pop2] if r_pop2 else []) + list(top5_8)
    top146 = ([r_pop1] if r_pop1 else []) + list(top4_6)
    top378 = ([r_pop3] if r_pop3 else []) + list(top3_8_12[4:6])
    top246 = ([r_pop2] if r_pop2 else []) + list(top4_6)
    top245 = [gate for gate in [r_pop2, r_pop4] + top5_8[:1] if gate]
    top345 = [gate for gate in [r_pop3, r_pop4] + top5_8[:1] if gate]
    top3578 = [gate for gate in [r_pop3] + list(top6_8) if gate]
    top3678 = [gate for gate in [r_pop3] + list(top6_8) if gate]
    top678 = list(top6_8)
    top2356 = [gate for gate in [r_pop2, r_pop3] + list(top5_6) if gate]
    top24_56 = list(top2_4)
    top56 = list(top5_6)

    strategy_groups = {
        "anchor1_25": [
            _gate_group("축", anchor),
            _gate_group("상대", top2_5),
        ],
        "anchor1_25_6": [
            _gate_group("축", anchor),
            _gate_group("2~5", top2_5),
            _gate_group("6", top6_8[:1]),
        ],
        "anchor1_25_67": [
            _gate_group("축", anchor),
            _gate_group("2~5", top2_5),
            _gate_group("6~7", top6_8[:2]),
        ],
        "anchor1_25_68": [
            _gate_group("축", anchor),
            _gate_group("2~5", top2_5),
            _gate_group("6~8", top6_8),
        ],
        "anchor1_26": [
            _gate_group("축", anchor),
            _gate_group("2~6", top2_6),
        ],
        "anchor1_24_58": [
            _gate_group("1", anchor),
            _gate_group("2~4", top2_4),
            _gate_group("5~8", top5_8),
        ],
        "anchor1_58_24": [
            _gate_group("1", anchor),
            _gate_group("5~8", top5_8),
            _gate_group("2~4", top2_4),
        ],
        "anchor1_23_46": [
            _gate_group("1", anchor),
            _gate_group("2~3", top3[1:3]),
            _gate_group("4~6", top4_6),
        ],
        "anchor1_47_23": [
            _gate_group("1", anchor),
            _gate_group("4~7", top4_7),
            _gate_group("2~3", top3[1:3]),
        ],
        "anchor1_23_47": [
            _gate_group("1", anchor),
            _gate_group("2~3", top3[1:3]),
            _gate_group("4~7", top4_7),
        ],
        "anchor1_pair24_56_trifecta": [
            _gate_group("1", anchor),
            _gate_group("2~4", top24_56),
            _gate_group("5~6", top56),
        ],
        "pair58_anchor1_24_trifecta": [
            _gate_group("5~8", top5_8),
            _gate_group("1", anchor),
            _gate_group("2~4", top2_4),
        ],
        "anchor4_pair123_56_trifecta": [
            _gate_group("4", [r_pop4]),
            _gate_group("1~3", top1_3),
            _gate_group("5~6", top56),
        ],
        "anchor4_pair123_567_trifecta": [
            _gate_group("4", [r_pop4]),
            _gate_group("1~3", top1_3),
            _gate_group("5~7", top5_7),
        ],
        "anchor3_247": [
            _gate_group("3", [r_pop3]),
            _gate_group("2,4~7", ([r_pop2] if r_pop2 else []) + top4_7),
        ],
        "anchor3_pair124_567_trifecta": [
            _gate_group("3", [r_pop3]),
            _gate_group("1,2,4", top1_2_4),
            _gate_group("5~7", top5_7),
        ],
        "anchor4_box2356_trifecta": [
            _gate_group("4", [r_pop4]),
            _gate_group("2,3,5,6", top2356),
        ],
        "anchor2_37_trifecta": [
            _gate_group("2", second_anchor),
            _gate_group("3~7", top3_7),
        ],
        "anchor2_pair146_378_trifecta": [
            _gate_group("2", second_anchor),
            _gate_group("1,4~6", top146),
            _gate_group("3,7~8", top378),
        ],
        "anchor1_second246_3578_trifecta": [
            _gate_group("2,4,6", top246),
            _gate_group("1", [r_pop1]),
            _gate_group("3,5,7,8", top3578),
        ],
        "anchor1_third245_3678_trifecta": [
            _gate_group("2,4,5", top245),
            _gate_group("3,6,7,8", top3678),
            _gate_group("1", [r_pop1]),
        ],
        "anchor2_pair345_678_trifecta": [
            _gate_group("2", second_anchor),
            _gate_group("3,4,5", top345),
            _gate_group("6,7,8", top678),
        ],
        "anchor1_pair2_58_34_trifecta": [
            _gate_group("1", anchor),
            _gate_group("2,5~8", top2_58),
            _gate_group("3~4", top3_4),
        ],
        "anchor1_pair23_48_besthit_trifecta": [
            _gate_group("1", anchor),
            _gate_group("2~3", top3[1:3]),
            _gate_group("4~8", ([r_pop4] if r_pop4 else []) + top5_8),
        ],
        "anchor12_pair57_34_trifecta": [
            _gate_group("1~2", top1_2),
            _gate_group("5~7", top5_7),
            _gate_group("3~4", top3_4),
        ],
        "anchor12_pair34_57_trifecta": [
            _gate_group("1~2", top1_2),
            _gate_group("3~4", top3_4),
            _gate_group("5~7", top5_7),
        ],
        "anchor1_pair246_3_trio": [
            _gate_group("1", anchor),
            _gate_group("2,4~6", top246),
            _gate_group("3", [r_pop3]),
        ],
        "anchor1_3_47_trio": [
            _gate_group("1", anchor),
            _gate_group("3", [r_pop3]),
            _gate_group("4~7", top4_7),
        ],
    }

    return [group for group in strategy_groups.get(strategy_key, []) if group]


def _dedupe_gate_values(values):
    result = []
    seen = set()
    for value in values or []:
        try:
            gate = int(value)
        except Exception:
            continue
        if gate <= 0 or gate in seen:
            continue
        seen.add(gate)
        result.append(gate)
    return result


def _build_admin_profit_strategy_combo_payload(row_map, strategy_key):
    top3 = _parse_gate_list(row_map.get("r_pop_top3_마번"))
    top4 = _parse_gate_list(row_map.get("r_pop_top4_마번"))
    top6 = _parse_gate_list(row_map.get("r_pop_top6_마번"))
    anchor = _dedupe_gate_values(_parse_gate_list(row_map.get("축마")))
    second_anchor = _dedupe_gate_values(_parse_gate_list(row_map.get("2축마")))
    top2_4 = _dedupe_gate_values(_parse_gate_list(row_map.get("2~4_마번")))
    top2_5 = _dedupe_gate_values(_parse_gate_list(row_map.get("2~5_마번")))
    top2_6 = _dedupe_gate_values(_parse_gate_list(row_map.get("2~6_마번")))
    top4_6 = _dedupe_gate_values(_parse_gate_list(row_map.get("4~6_마번")))
    top5_7 = _dedupe_gate_values(_parse_gate_list(row_map.get("5~7_마번")))
    top5_8 = _dedupe_gate_values(_parse_gate_list(row_map.get("5~8_마번")))
    top6_8 = _dedupe_gate_values(_parse_gate_list(row_map.get("6~8_마번")))
    top3_7 = _dedupe_gate_values(_parse_gate_list(row_map.get("3~7_마번")))
    top3_8_12 = _dedupe_gate_values(_parse_gate_list(row_map.get("3~8,12_마번")))

    r_pop1 = top3[0] if len(top3) > 0 else (top4[0] if len(top4) > 0 else (top6[0] if len(top6) > 0 else None))
    r_pop2 = top3[1] if len(top3) > 1 else None
    r_pop3 = top3[2] if len(top3) > 2 else None
    r_pop4 = top4[3] if len(top4) > 3 else None
    top5_6 = _dedupe_gate_values(top6[4:6] if len(top6) >= 6 else top5_8[:2])
    top4_7 = _dedupe_gate_values((([r_pop4] if r_pop4 else []) + top5_7))
    top3_4 = _dedupe_gate_values([r_pop3, r_pop4])
    top1_2 = _dedupe_gate_values([r_pop1, r_pop2])
    top1_3 = _dedupe_gate_values([r_pop1, r_pop2, r_pop3])
    top1_2_4 = _dedupe_gate_values([r_pop1, r_pop2, r_pop4])
    top2_58 = _dedupe_gate_values((([r_pop2] if r_pop2 else []) + top5_8))
    top146 = _dedupe_gate_values((([r_pop1] if r_pop1 else []) + top4_6))
    top378 = _dedupe_gate_values((([r_pop3] if r_pop3 else []) + top3_8_12[4:6]))
    top246 = _dedupe_gate_values((([r_pop2] if r_pop2 else []) + top4_6))
    top245 = _dedupe_gate_values(([r_pop2, r_pop4] + top5_8[:1]))
    top345 = _dedupe_gate_values(([r_pop3, r_pop4] + top5_8[:1]))
    top3578 = _dedupe_gate_values(([r_pop3] + list(top6_8)))
    top3678 = _dedupe_gate_values(([r_pop3] + list(top6_8)))
    top678 = _dedupe_gate_values(top6_8)
    top2356 = _dedupe_gate_values(([r_pop2, r_pop3] + list(top5_6)))

    def ordered_product(first_group, second_group, third_group):
        tickets = []
        for first in _dedupe_gate_values(first_group):
            for second in _dedupe_gate_values(second_group):
                for third in _dedupe_gate_values(third_group):
                    if len({first, second, third}) < 3:
                        continue
                    tickets.append(f"{first}-{second}-{third}")
        return tickets

    def permute_with_fixed_first(first_group, pool_group):
        tickets = []
        for first in _dedupe_gate_values(first_group):
            for second in _dedupe_gate_values(pool_group):
                for third in _dedupe_gate_values(pool_group):
                    if len({first, second, third}) < 3:
                        continue
                    tickets.append(f"{first}-{second}-{third}")
        return tickets

    def trio_product(group_a, group_b, group_c):
        tickets = []
        for first in _dedupe_gate_values(group_a):
            for second in _dedupe_gate_values(group_b):
                for third in _dedupe_gate_values(group_c):
                    combo = [first, second, third]
                    if len(set(combo)) < 3:
                        continue
                    tickets.append("-".join(str(value) for value in sorted(combo)))
        return sorted(set(tickets), key=lambda item: [int(part) for part in item.split("-")])

    combo_map = {
        "anchor1_25": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("축", anchor),
                _gate_group("2~5", top2_5),
            ],
            "tickets": permute_with_fixed_first(anchor, top2_5),
        },
        "anchor1_25_6": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("축", anchor),
                _gate_group("2~5", top2_5),
                _gate_group("6", top6_8[:1]),
            ],
            "tickets": ordered_product(anchor, top2_5, top6_8[:1]),
        },
        "anchor1_25_67": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("축", anchor),
                _gate_group("2~5", top2_5),
                _gate_group("6~7", top6_8[:2]),
            ],
            "tickets": ordered_product(anchor, top2_5, top6_8[:2]),
        },
        "anchor1_25_68": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("축", anchor),
                _gate_group("2~5", top2_5),
                _gate_group("6~8", top6_8),
            ],
            "tickets": ordered_product(anchor, top2_5, top6_8),
        },
        "anchor1_26": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("축", anchor),
                _gate_group("2~6", top2_6),
            ],
            "tickets": permute_with_fixed_first(anchor, top2_6),
        },
        "anchor1_24_58": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("2~4", top2_4),
                _gate_group("5~8", top5_8),
            ],
            "tickets": ordered_product(anchor, top2_4, top5_8),
        },
        "anchor1_58_24": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("5~8", top5_8),
                _gate_group("2~4", top2_4),
            ],
            "tickets": ordered_product(anchor, top5_8, top2_4),
        },
        "anchor1_23_46": {
            "bet_type": "삼복",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("2~3", top3[1:3]),
                _gate_group("4~6", top4_6),
            ],
            "tickets": trio_product(anchor, top3[1:3], top4_6),
        },
        "anchor1_47_23": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("4~7", top4_7),
                _gate_group("2~3", top3[1:3]),
            ],
            "tickets": ordered_product(anchor, top4_7, top3[1:3]),
        },
        "anchor1_23_47": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("2~3", top3[1:3]),
                _gate_group("4~7", top4_7),
            ],
            "tickets": ordered_product(anchor, top3[1:3], top4_7),
        },
        "anchor1_pair24_56_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("2~4", top2_4),
                _gate_group("5~6", top5_6),
            ],
            "tickets": ordered_product(anchor, top2_4, top5_6),
        },
        "pair58_anchor1_24_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("5~8", top5_8),
                _gate_group("1", anchor),
                _gate_group("2~4", top2_4),
            ],
            "tickets": ordered_product(top5_8, anchor, top2_4),
        },
        "anchor4_pair123_56_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("4", [r_pop4]),
                _gate_group("1~3", top1_3),
                _gate_group("5~6", top5_6),
            ],
            "tickets": ordered_product([r_pop4], top1_3, top5_6),
        },
        "anchor4_pair123_567_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("4", [r_pop4]),
                _gate_group("1~3", top1_3),
                _gate_group("5~7", top5_7),
            ],
            "tickets": ordered_product([r_pop4], top1_3, top5_7),
        },
        "anchor3_247": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("3", [r_pop3]),
                _gate_group("2,4~7", ([r_pop2] if r_pop2 else []) + top4_7),
            ],
            "tickets": permute_with_fixed_first([r_pop3], ([r_pop2] if r_pop2 else []) + top4_7),
        },
        "anchor3_pair124_567_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("3", [r_pop3]),
                _gate_group("1,2,4", top1_2_4),
                _gate_group("5~7", top5_7),
            ],
            "tickets": ordered_product([r_pop3], top1_2_4, top5_7),
        },
        "anchor4_box2356_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("4", [r_pop4]),
                _gate_group("2,3,5,6", top2356),
            ],
            "tickets": permute_with_fixed_first([r_pop4], top2356),
        },
        "anchor2_37_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("2", second_anchor),
                _gate_group("3~7", top3_7),
            ],
            "tickets": permute_with_fixed_first(second_anchor, top3_7),
        },
        "anchor2_pair146_378_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("2", second_anchor),
                _gate_group("1,4~6", top146),
                _gate_group("3,7~8", top378),
            ],
            "tickets": ordered_product(second_anchor, top146, top378),
        },
        "anchor1_second246_3578_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("2,4,6", top246),
                _gate_group("1", [r_pop1]),
                _gate_group("3,5,7,8", top3578),
            ],
            "tickets": ordered_product(top246, [r_pop1], top3578),
        },
        "anchor1_third245_3678_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("2,4,5", top245),
                _gate_group("3,6,7,8", top3678),
                _gate_group("1", [r_pop1]),
            ],
            "tickets": ordered_product(top245, top3678, [r_pop1]),
        },
        "anchor2_pair345_678_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("2", second_anchor),
                _gate_group("3,4,5", top345),
                _gate_group("6,7,8", top678),
            ],
            "tickets": ordered_product(second_anchor, top345, top678),
        },
        "anchor1_pair2_58_34_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("2,5~8", top2_58),
                _gate_group("3~4", top3_4),
            ],
            "tickets": ordered_product(anchor, top2_58, top3_4),
        },
        "anchor12_pair57_34_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1~2", top1_2),
                _gate_group("5~7", top5_7),
                _gate_group("3~4", top3_4),
            ],
            "tickets": ordered_product(top1_2, top5_7, top3_4),
        },
        "anchor12_pair34_57_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1~2", top1_2),
                _gate_group("3~4", top3_4),
                _gate_group("5~7", top5_7),
            ],
            "tickets": ordered_product(top1_2, top3_4, top5_7),
        },
        "anchor1_pair246_3_trio": {
            "bet_type": "삼복",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("2,4~6", top246),
                _gate_group("3", [r_pop3]),
            ],
            "tickets": trio_product(anchor, top246, [r_pop3]),
        },
        "anchor1_3_47_trio": {
            "bet_type": "삼복",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("3", [r_pop3]),
                _gate_group("4~7", top4_7),
            ],
            "tickets": trio_product(anchor, [r_pop3], top4_7),
        },
        "anchor1_pair23_48_besthit_trifecta": {
            "bet_type": "삼쌍",
            "groups": [
                _gate_group("1", anchor),
                _gate_group("2~3", top3[1:3]),
                _gate_group("4~8", _dedupe_gate_values(([r_pop4] if r_pop4 else []) + top5_8)),
            ],
            "tickets": ordered_product(anchor, top3[1:3], _dedupe_gate_values(([r_pop4] if r_pop4 else []) + top5_8)),
        },
    }

    payload = combo_map.get(strategy_key)
    if not payload:
        return None

    groups = [group for group in payload.get("groups", []) if group]
    tickets = payload.get("tickets", [])
    return {
        "bet_type": payload.get("bet_type", ""),
        "groups": groups,
        "tickets": tickets,
        "holes_per_race": len(tickets),
    }


def _build_race_row_from_exp011(rcity, rdate, rno):
    exp010 = (
        Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno)
        .values("grade", "distance")
        .first()
    )
    rows = list(
        Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)
        .values("gate", "r_pop", "r_rank")
    )
    if not rows:
        return None

    def _safe_int(value, default=999):
        try:
            return int(value)
        except Exception:
            return default

    sorted_rows = sorted(rows, key=lambda item: (_safe_int(item.get("r_pop")), _safe_int(item.get("gate"))))
    gate_by_rank = [_safe_int(item.get("gate"), 0) for item in sorted_rows if _safe_int(item.get("gate"), 0) > 0]
    if not gate_by_rank:
        return None

    actual_top3_rows = sorted(
        [item for item in rows if 0 < _safe_int(item.get("r_rank")) <= 3],
        key=lambda item: _safe_int(item.get("r_rank")),
    )
    actual_top3 = [_safe_int(item.get("gate"), 0) for item in actual_top3_rows if _safe_int(item.get("gate"), 0) > 0]

    top3 = gate_by_rank[:3]
    top4 = gate_by_rank[:4]
    top5 = gate_by_rank[:5]
    top6 = gate_by_rank[:6]
    anchor_gate = top3[0] if len(top3) >= 1 else None
    second_gate = top3[1] if len(top3) >= 2 else None
    top2_4 = gate_by_rank[1:4]
    top2_5 = gate_by_rank[1:5]
    top2_6 = gate_by_rank[1:6]
    top4_6 = gate_by_rank[3:6]
    top5_7 = gate_by_rank[4:7]
    top5_8 = gate_by_rank[4:8]
    top6_8 = gate_by_rank[5:8]
    top3_8 = gate_by_rank[2:8]
    rank12_gate = gate_by_rank[11] if len(gate_by_rank) >= 12 else None
    top3_8_12 = top3_8 + ([rank12_gate] if rank12_gate is not None else [])

    return {
        "경마장": rcity,
        "경주일": rdate,
        "경주번호": rno,
        "경주거리": exp010.get("distance") if exp010 else "",
        "등급": exp010.get("grade") if exp010 else "",
        "축마": anchor_gate if anchor_gate is not None else "",
        "2축마": second_gate if second_gate is not None else "",
        "2~4_마번": ",".join(map(str, top2_4)),
        "2~5_마번": ",".join(map(str, top2_5)),
        "2~6_마번": ",".join(map(str, top2_6)),
        "4~6_마번": ",".join(map(str, top4_6)),
        "5~7_마번": ",".join(map(str, top5_7)),
        "5~8_마번": ",".join(map(str, top5_8)),
        "6~8_마번": ",".join(map(str, top6_8)),
        "3~8,12_마번": ",".join(map(str, top3_8_12)),
        "r_pop_top3_마번": ",".join(map(str, top3)),
        "r_pop_top4_마번": ",".join(map(str, top4)),
        "r_pop_top5_마번": ",".join(map(str, top5)),
        "r_pop_top6_마번": ",".join(map(str, top6)),
        "실제_top3_마번": ",".join(map(str, actual_top3)),
    }


def _filter_race_df_for_admin_profit_trio_odds(race_df):
    """관리자 수익 분석은 삼복승식 배당율이 입력된 경주만 집계한다."""
    if race_df is None or not hasattr(race_df, "columns") or race_df.empty:
        return race_df
    if "삼복승식배당율" not in race_df.columns:
        return race_df
    trio_odds = pd.to_numeric(race_df["삼복승식배당율"], errors="coerce")
    return race_df[trio_odds.gt(0)].copy()


def _parse_gate_list(raw_value):
    text = str(raw_value or "").strip()
    if not text:
        return []
    numbers = []
    for token in re.findall(r"\d+", text):
        try:
            numbers.append(int(token))
        except Exception:
            continue
    return numbers


def _augment_top4pair_56_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~4_복조_5~6_삼쌍_적중" in race_df.columns:
        return race_df

    required = {
        "r_pop_top4_마번",
        "r_pop_top6_마번",
        "실제_top3_마번",
        "삼쌍승식배당율",
    }
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top6_series = race_df["r_pop_top6_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 24 * bet_unit

    for top4, top6, actual_top3, odds in zip(
        top4_series,
        top6_series,
        actual_top3_series,
        trifecta_odds,
    ):
        top5_6 = list(top6[4:6]) if len(top6) >= 6 else []
        valid = len(top4) == 4 and len(top5_6) == 2
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0

        if valid and len(actual_top3) == 3:
            first_two = actual_top3[:2]
            third = actual_top3[2]
            if (
                len(set(first_two)) == 2
                and all(gate in top4 for gate in first_two)
                and third in top5_6
            ):
                hit = 1
                refund = float(odds) * bet_unit

        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1~4_복조_5~6_삼쌍_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1~4_복조_5~6_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1~4복조_5~6_삼쌍_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1~4복조_5~6_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_top4pair_56_trio_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~4_복조_5~6_삼복_적중" in race_df.columns:
        return race_df

    required = {
        "r_pop_top4_마번",
        "r_pop_top6_마번",
        "실제_top3_마번",
        "삼복승식배당율",
    }
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top6_series = race_df["r_pop_top6_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trio_odds = pd.to_numeric(race_df["삼복승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top4, top6, actual_top3, odds in zip(
        top4_series,
        top6_series,
        actual_top3_series,
        trio_odds,
    ):
        top5_6 = list(top6[4:6]) if len(top6) >= 6 else []
        valid = len(top4) == 4 and len(top5_6) == 2
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0

        if valid and len(actual_top3) == 3:
            actual_set = set(actual_top3)
            if len(actual_set) == 3 and len(actual_set.intersection(top4)) == 2 and len(actual_set.intersection(top5_6)) == 1:
                hit = 1
                refund = float(odds) * bet_unit

        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1~4_복조_5~6_삼복_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1~4_복조_5~6_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1~4복조_5~6_삼복_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1~4복조_5~6_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_top3pair_46_trio_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~3_복조_4~6_삼복_적중" in race_df.columns:
        return race_df

    required = {
        "r_pop_top3_마번",
        "4~6_마번",
        "실제_top3_마번",
        "삼복승식배당율",
    }
    if not required.issubset(race_df.columns):
        return race_df

    top3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top4_6_series = race_df["4~6_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trio_odds = pd.to_numeric(race_df["삼복승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 9 * bet_unit

    for top3, top4_6, actual_top3, odds in zip(
        top3_series,
        top4_6_series,
        actual_top3_series,
        trio_odds,
    ):
        top3_set = set(top3)
        top4_6_set = set(top4_6)
        valid = (
            len(top3) == 3
            and len(top3_set) == 3
            and len(top4_6) == 3
            and len(top4_6_set) == 3
            and top3_set.isdisjoint(top4_6_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0

        if valid and len(actual_top3) == 3:
            actual_set = set(actual_top3)
            if (
                len(actual_set) == 3
                and len(actual_set.intersection(top3_set)) == 2
                and len(actual_set.intersection(top4_6_set)) == 1
            ):
                hit = 1
                refund = float(odds) * bet_unit

        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1~3_복조_4~6_삼복_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1~3_복조_4~6_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1~3_복조_4~6_삼복_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1~3_복조_4~6_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_24_56_trio_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~4_5~6_삼복_적중" in race_df.columns:
        return race_df

    required = {
        "축마",
        "2~4_마번",
        "r_pop_top4_마번",
        "r_pop_top6_마번",
        "실제_top3_마번",
        "삼복승식배당율",
    }
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["축마"].apply(_parse_gate_list)
    top2_4_series = race_df["2~4_마번"].apply(_parse_gate_list)
    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top6_series = race_df["r_pop_top6_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trio_odds = pd.to_numeric(race_df["삼복승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 6 * bet_unit

    for anchor_list, top2_4, top4, top6, actual_top3, odds in zip(
        anchor_series,
        top2_4_series,
        top4_series,
        top6_series,
        actual_top3_series,
        trio_odds,
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        top5_6 = [gate for gate in top6 if gate not in set(top4)][:2]
        actual_set = set(actual_top3)
        top2_4_set = set(top2_4)
        top5_6_set = set(top5_6)
        valid = (
            anchor_gate is not None
            and len(top2_4) == 3
            and len(top2_4_set) == 3
            and len(top5_6) == 2
            and len(top5_6_set) == 2
            and anchor_gate not in top2_4_set
            and anchor_gate not in top5_6_set
            and top2_4_set.isdisjoint(top5_6_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0

        if valid and len(actual_top3) == 3:
            if (
                anchor_gate in actual_set
                and len(actual_set & top2_4_set) == 1
                and len(actual_set & top5_6_set) == 1
            ):
                hit = 1
                refund = float(odds) * bet_unit

        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_축_2~4_5~6_삼복_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_축_2~4_5~6_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2~4_5~6_삼복_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2~4_5~6_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_23_46_trio_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~3_4~6_삼복_적중" in race_df.columns:
        return race_df

    required = {
        "축마",
        "r_pop_top3_마번",
        "4~6_마번",
        "실제_top3_마번",
        "삼복승식배당율",
    }
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["축마"].apply(_parse_gate_list)
    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top4_6_series = race_df["4~6_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trio_odds = pd.to_numeric(race_df["삼복승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 6 * bet_unit

    for anchor_list, top1_3, top4_6, actual_top3, odds in zip(
        anchor_series, top1_3_series, top4_6_series, actual_top3_series, trio_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        top2_3 = top1_3[1:3]
        actual_set = set(actual_top3)
        top2_3_set = set(top2_3)
        top4_6_set = set(top4_6)
        valid = (
            anchor_gate is not None
            and len(top2_3) == 2
            and len(top2_3_set) == 2
            and len(top4_6) == 3
            and len(top4_6_set) == 3
            and anchor_gate not in top2_3_set
            and anchor_gate not in top4_6_set
            and top2_3_set.isdisjoint(top4_6_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0

        if valid and len(actual_top3) == 3:
            if (
                anchor_gate in actual_set
                and len(actual_set & top2_3_set) == 1
                and len(actual_set & top4_6_set) == 1
            ):
                hit = 1
                refund = float(odds) * bet_unit

        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_축_2~3_4~6_삼복_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_축_2~3_4~6_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2~3_4~6_삼복_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2~3_4~6_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_pair246_3_trio_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2,4~6_3_삼복_적중" in race_df.columns:
        return race_df

    required = {"축마", "r_pop_top6_마번", "실제_top3_마번", "삼복승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["축마"].apply(_parse_gate_list)
    top6_series = race_df["r_pop_top6_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trio_odds = pd.to_numeric(race_df["삼복승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 4 * bet_unit

    for anchor_list, top6, actual_top3, odds in zip(
        anchor_series, top6_series, actual_top3_series, trio_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        pair246 = []
        if len(top6) >= 6:
            pair246 = [top6[1], top6[3], top6[4], top6[5]]
        third_group = [top6[2]] if len(top6) >= 3 else []
        actual_set = set(actual_top3)
        pair246_set = set(pair246)
        third_set = set(third_group)
        valid = (
            anchor_gate is not None
            and len(pair246) == 4
            and len(pair246_set) == 4
            and len(third_group) == 1
            and len(third_set) == 1
            and anchor_gate not in pair246_set
            and anchor_gate not in third_set
            and pair246_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0

        if valid and len(actual_top3) == 3:
            if (
                anchor_gate in actual_set
                and len(actual_set & pair246_set) == 1
                and len(actual_set & third_set) == 1
            ):
                hit = 1
                refund = float(odds) * bet_unit

        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_축_2,4~6_3_삼복_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_축_2,4~6_3_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2,4~6_3_삼복_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2,4~6_3_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_3_47_trio_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_3_4~7_삼복_적중" in race_df.columns:
        return race_df

    required = {"축마", "r_pop_top3_마번", "3~8,12_마번", "실제_top3_마번", "삼복승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["축마"].apply(_parse_gate_list)
    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top3_8_12_series = race_df["3~8,12_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trio_odds = pd.to_numeric(race_df["삼복승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 4 * bet_unit

    for anchor_list, top1_3, top3_8_12, actual_top3, odds in zip(
        anchor_series, top1_3_series, top3_8_12_series, actual_top3_series, trio_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        top1_3_set = set(top1_3)
        second_group = [top1_3[2]] if len(top1_3) >= 3 else []
        third_group = [gate for gate in top3_8_12 if gate not in top1_3_set][:4]
        actual_set = set(actual_top3)
        second_set = set(second_group)
        third_set = set(third_group)
        valid = (
            anchor_gate is not None
            and len(second_group) == 1
            and len(second_set) == 1
            and len(third_group) == 4
            and len(third_set) == 4
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0

        if valid and len(actual_top3) == 3:
            if (
                anchor_gate in actual_set
                and len(actual_set & second_set) == 1
                and len(actual_set & third_set) == 1
            ):
                hit = 1
                refund = float(odds) * bet_unit

        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_축_3_4~7_삼복_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_축_3_4~7_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_3_4~7_삼복_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_3_4~7_삼복_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_26_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~6_삼쌍_적중" in race_df.columns:
        return race_df

    required = {"축마", "2~6_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["축마"].apply(_parse_gate_list)
    top2_6_series = race_df["2~6_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 20 * bet_unit

    for anchor_list, top2_6, actual_top3, odds in zip(
        anchor_series, top2_6_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        valid = anchor_gate is not None and len(top2_6) == 5
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in top2_6
                and actual_top3[2] in top2_6
                and actual_top3[1] != actual_top3[2]
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_축_2~6_삼쌍_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_축_2~6_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2~6_삼쌍_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2~6_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_25_6_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~5_6_적중" in race_df.columns:
        return race_df

    required = {"축마", "2~5_마번", "6~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["축마"].apply(_parse_gate_list)
    top2_5_series = race_df["2~5_마번"].apply(_parse_gate_list)
    top6_8_series = race_df["6~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 4 * bet_unit

    for anchor_list, top2_5, top6_8, actual_top3, odds in zip(
        anchor_series, top2_5_series, top6_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        third_gate = top6_8[0] if len(top6_8) >= 1 else None
        valid = anchor_gate is not None and len(top2_5) == 4 and third_gate is not None
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if actual_top3[0] == anchor_gate and actual_top3[1] in top2_5 and actual_top3[2] == third_gate:
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_축_2~5_6_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_축_2~5_6_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2~5_6_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2~5_6_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_25_67_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~5_6~7_적중" in race_df.columns:
        return race_df

    required = {"축마", "2~5_마번", "6~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["축마"].apply(_parse_gate_list)
    top2_5_series = race_df["2~5_마번"].apply(_parse_gate_list)
    top6_8_series = race_df["6~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 8 * bet_unit

    for anchor_list, top2_5, top6_8, actual_top3, odds in zip(
        anchor_series, top2_5_series, top6_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        third_candidates = top6_8[:2] if len(top6_8) >= 2 else []
        valid = anchor_gate is not None and len(top2_5) == 4 and len(third_candidates) == 2
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if actual_top3[0] == anchor_gate and actual_top3[1] in top2_5 and actual_top3[2] in third_candidates:
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_축_2~5_6~7_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_축_2~5_6~7_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2~5_6~7_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2~5_6~7_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor2_37_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_축_3~7_삼쌍_적중" in race_df.columns:
        return race_df

    required = {"2축마", "3~7_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["2축마"].apply(_parse_gate_list)
    top3_7_series = race_df["3~7_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 20 * bet_unit

    for anchor_list, top3_7, actual_top3, odds in zip(
        anchor_series, top3_7_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        valid = anchor_gate is not None and len(top3_7) == 5
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in top3_7
                and actual_top3[2] in top3_7
                and actual_top3[1] != actual_top3[2]
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop2_축_3~7_삼쌍_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop2_축_3~7_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["2축_3~7_삼쌍_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["2축_3~7_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor2_pair146_378_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_1축_1,4~6_2축_3,7~8_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top1_3, top4, top5_8, actual_top3, odds in zip(
        top1_3_series, top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        top1_3_set = set(top1_3)
        anchor_gate = top1_3[1] if len(top1_3) >= 2 else None
        second_candidates = []
        if len(top1_3) >= 1:
            second_candidates.append(top1_3[0])
        second_candidates.extend([gate for gate in top4 if gate not in top1_3_set][:1])
        second_candidates.extend(top5_8[:2])
        third_candidates = []
        if len(top1_3) >= 3:
            third_candidates.append(top1_3[2])
        third_candidates.extend(top5_8[2:4])
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(second_candidates) == 4
            and len(second_set) == 4
            and len(third_candidates) == 3
            and len(third_set) == 3
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop2_1축_1,4~6_2축_3,7~8_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop2_1축_1,4~6_2축_3,7~8_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["2축_1,4~6_2축_3,7~8_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["2축_1,4~6_2축_3,7~8_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_second246_3578_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_1축_2,4,6_2축_1_3축_3,5,7,8_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top1_3, top4, top5_8, actual_top3, odds in zip(
        top1_3_series, top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top1_3[0] if len(top1_3) >= 1 else None
        first_candidates = []
        if len(top1_3) >= 2:
            first_candidates.append(top1_3[1])
        if len(top4) >= 4:
            first_candidates.append(top4[3])
        if len(top5_8) >= 2:
            first_candidates.append(top5_8[1])
        third_candidates = []
        if len(top1_3) >= 3:
            third_candidates.append(top1_3[2])
        if len(top5_8) >= 1:
            third_candidates.append(top5_8[0])
        third_candidates.extend(top5_8[2:4])
        first_set = set(first_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(first_candidates) == 3
            and len(first_set) == 3
            and len(third_candidates) == 4
            and len(third_set) == 4
            and anchor_gate not in first_set
            and anchor_gate not in third_set
            and first_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] in first_set
                and actual_top3[1] == anchor_gate
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_1축_2,4,6_2축_1_3축_3,5,7,8_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_1축_2,4,6_2축_1_3축_3,5,7,8_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2,4,6_2축_1_3축_3,5,7,8_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2,4,6_2축_1_3축_3,5,7,8_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_third245_3678_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_1축_2,4,5_2축_3,6,7,8_3축_1_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top1_3, top4, top5_8, actual_top3, odds in zip(
        top1_3_series, top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top1_3[0] if len(top1_3) >= 1 else None
        first_candidates = []
        if len(top1_3) >= 2:
            first_candidates.append(top1_3[1])
        if len(top4) >= 4:
            first_candidates.append(top4[3])
        if len(top5_8) >= 1:
            first_candidates.append(top5_8[0])
        second_candidates = []
        if len(top1_3) >= 3:
            second_candidates.append(top1_3[2])
        if len(top5_8) >= 2:
            second_candidates.append(top5_8[1])
        second_candidates.extend(top5_8[2:4])
        first_set = set(first_candidates)
        second_set = set(second_candidates)
        valid = (
            anchor_gate is not None
            and len(first_candidates) == 3
            and len(first_set) == 3
            and len(second_candidates) == 4
            and len(second_set) == 4
            and anchor_gate not in first_set
            and anchor_gate not in second_set
            and first_set.isdisjoint(second_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] in first_set
                and actual_top3[1] in second_set
                and actual_top3[2] == anchor_gate
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_1축_2,4,5_2축_3,6,7,8_3축_1_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_1축_2,4,5_2축_3,6,7,8_3축_1_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2,4,5_2축_3,6,7,8_3축_1_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2,4,5_2축_3,6,7,8_3축_1_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor2_pair345_678_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_1축_3,4,5_2축_6,7,8_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 9 * bet_unit

    for top1_3, top4, top5_8, actual_top3, odds in zip(
        top1_3_series, top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top1_3[1] if len(top1_3) >= 2 else None
        second_candidates = []
        if len(top1_3) >= 3:
            second_candidates.append(top1_3[2])
        if len(top4) >= 4:
            second_candidates.append(top4[3])
        if len(top5_8) >= 1:
            second_candidates.append(top5_8[0])
        third_candidates = top5_8[1:4]
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(second_candidates) == 3
            and len(second_set) == 3
            and len(third_candidates) == 3
            and len(third_set) == 3
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop2_1축_3,4,5_2축_6,7,8_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop2_1축_3,4,5_2축_6,7,8_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["2축_3,4,5_2축_6,7,8_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["2축_3,4,5_2축_6,7,8_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor2_36_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_축_3~6_삼쌍_적중" in race_df.columns:
        return race_df

    required = {"2축마", "3~8,12_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["2축마"].apply(_parse_gate_list)
    top3_8_12_series = race_df["3~8,12_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for anchor_list, top3_8_12, actual_top3, odds in zip(
        anchor_series, top3_8_12_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        top3_6 = top3_8_12[:4]
        top3_6_set = set(top3_6)
        valid = anchor_gate is not None and len(top3_6) == 4
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in top3_6_set
                and actual_top3[2] in top3_6_set
                and actual_top3[1] != actual_top3[2]
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop2_축_3~6_삼쌍_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop2_축_3~6_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["2축_3~6_삼쌍_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["2축_3~6_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor3_pair124_56_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop3_1축_1~2,4_2축_5~6_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 6 * bet_unit

    for top1_3, top4, top5_8, actual_top3, odds in zip(
        top1_3_series, top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top1_3[2] if len(top1_3) >= 3 else None
        second_candidates = [gate for gate in top4 if gate != anchor_gate][:3]
        third_candidates = top5_8[:2]
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(second_candidates) == 3
            and len(second_set) == 3
            and len(third_candidates) == 2
            and len(third_set) == 2
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop3_1축_1~2,4_2축_5~6_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop3_1축_1~2,4_2축_5~6_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["3축_1~2,4_2축_5~6_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["3축_1~2,4_2축_5~6_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor4_pair123_56_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop4_1축_1~2,3_2축_5~6_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 6 * bet_unit

    for top4, top5_8, actual_top3, odds in zip(
        top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top4[3] if len(top4) >= 4 else None
        second_candidates = top4[:3]
        third_candidates = top5_8[:2]
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(second_candidates) == 3
            and len(second_set) == 3
            and len(third_candidates) == 2
            and len(third_set) == 2
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop4_1축_1~2,3_2축_5~6_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop4_1축_1~2,3_2축_5~6_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["4축_1~2,3_2축_5~6_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["4축_1~2,3_2축_5~6_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_pair58_anchor1_24_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop5~8_1축_r_pop1_2축_r_pop2~4_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "r_pop_top3_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top4, top1_3, top5_8, actual_top3, odds in zip(
        top4_series, top1_3_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor2_gate = top1_3[0] if top1_3 else None
        anchor3_candidates = [gate for gate in top4 if gate != anchor2_gate][:3]
        anchor3_set = set(anchor3_candidates)
        top5_8_set = set(top5_8)
        valid = (
            anchor2_gate is not None
            and len(anchor3_candidates) == 3
            and len(anchor3_set) == 3
            and len(top5_8) == 4
            and len(top5_8_set) == 4
            and anchor2_gate not in top5_8_set
            and anchor2_gate not in anchor3_set
            and anchor3_set.isdisjoint(top5_8_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] in top5_8_set
                and actual_top3[1] == anchor2_gate
                and actual_top3[2] in anchor3_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop5~8_1축_r_pop1_2축_r_pop2~4_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop5~8_1축_r_pop1_2축_r_pop2~4_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["5~8를1축_1을2축_2~4를3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["5~8를1축_1을2축_2~4를3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_pair24_56_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_1축_2~4_2축_5~6_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "r_pop_top3_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 6 * bet_unit

    for top4, top1_3, top5_8, actual_top3, odds in zip(
        top4_series, top1_3_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor1_gate = top1_3[0] if top1_3 else None
        pair24 = [gate for gate in top4 if gate != anchor1_gate][:3]
        pair24_set = set(pair24)
        top5_6 = top5_8[:2]
        top5_6_set = set(top5_6)
        valid = (
            anchor1_gate is not None
            and len(pair24) == 3
            and len(pair24_set) == 3
            and len(top5_6) == 2
            and len(top5_6_set) == 2
            and anchor1_gate not in pair24_set
            and anchor1_gate not in top5_6_set
            and pair24_set.isdisjoint(top5_6_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor1_gate
                and actual_top3[1] in pair24_set
                and actual_top3[2] in top5_6_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_1축_2~4_2축_5~6_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_1축_2~4_2축_5~6_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2~4_2축_5~6_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2~4_2축_5~6_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_pair2_58_34_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_1축_2,5~8_2축_3~4_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "r_pop_top3_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 10 * bet_unit

    for top4, top1_3, top5_8, actual_top3, odds in zip(
        top4_series, top1_3_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor1_gate = top1_3[0] if top1_3 else None
        second_candidates = ([top1_3[1]] if len(top1_3) >= 2 else []) + top5_8[:4]
        third_candidates = top4[2:4]
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor1_gate is not None
            and len(second_candidates) == 5
            and len(second_set) == 5
            and len(third_candidates) == 2
            and len(third_set) == 2
            and anchor1_gate not in second_set
            and anchor1_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor1_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_1축_2,5~8_2축_3~4_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_1축_2,5~8_2축_3~4_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2,5~8_2축_3~4_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2,5~8_2축_3~4_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor12_pair57_34_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~2_1축_5~7_2축_3~4_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "r_pop_top3_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top4, top1_3, top5_8, actual_top3, odds in zip(
        top4_series, top1_3_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor1_candidates = top1_3[:2]
        second_candidates = top5_8[:3]
        third_candidates = top4[2:4]
        anchor1_set = set(anchor1_candidates)
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            len(anchor1_candidates) == 2
            and len(anchor1_set) == 2
            and len(second_candidates) == 3
            and len(second_set) == 3
            and len(third_candidates) == 2
            and len(third_set) == 2
            and anchor1_set.isdisjoint(second_set)
            and anchor1_set.isdisjoint(third_set)
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] in anchor1_set
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1~2_1축_5~7_2축_3~4_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1~2_1축_5~7_2축_3~4_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1~2축_5~7_2축_3~4_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1~2축_5~7_2축_3~4_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_pair23_48_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_1축_2~3_2축_4~8_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "3~8,12_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top3_8_12_series = race_df["3~8,12_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 10 * bet_unit

    for top1_3, top3_8_12, actual_top3, odds in zip(
        top1_3_series, top3_8_12_series, actual_top3_series, trifecta_odds
    ):
        top1_3_set = set(top1_3)
        anchor1_gate = top1_3[0] if top1_3 else None
        pair23 = top1_3[1:3]
        top4_8 = [gate for gate in top3_8_12 if gate not in top1_3_set][:5]
        pair23_set = set(pair23)
        top4_8_set = set(top4_8)
        valid = (
            anchor1_gate is not None
            and len(pair23) == 2
            and len(pair23_set) == 2
            and len(top4_8) == 5
            and len(top4_8_set) == 5
            and anchor1_gate not in pair23_set
            and anchor1_gate not in top4_8_set
            and pair23_set.isdisjoint(top4_8_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor1_gate
                and actual_top3[1] in pair23_set
                and actual_top3[2] in top4_8_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_1축_2~3_2축_4~8_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_1축_2~3_2축_4~8_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_2~3_2축_4~8_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_2~3_2축_4~8_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor1_47_23_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_4~7_2~3_적중" in race_df.columns:
        return race_df

    required = {"축마", "r_pop_top3_마번", "3~8,12_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    anchor_series = race_df["축마"].apply(_parse_gate_list)
    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top3_8_12_series = race_df["3~8,12_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 8 * bet_unit

    for anchor_list, top1_3, top3_8_12, actual_top3, odds in zip(
        anchor_series, top1_3_series, top3_8_12_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = anchor_list[0] if anchor_list else None
        top1_3_set = set(top1_3)
        anchor4_7 = [gate for gate in top3_8_12 if gate not in top1_3_set][:4]
        top2_3 = top1_3[1:3]
        top2_3_set = set(top2_3)
        anchor4_7_set = set(anchor4_7)
        valid = (
            anchor_gate is not None
            and
            len(anchor4_7) == 4
            and len(anchor4_7_set) == 4
            and len(top2_3) == 2
            and len(top2_3_set) == 2
            and anchor4_7_set.isdisjoint(top2_3_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in anchor4_7_set
                and actual_top3[2] in top2_3_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1_축_4~7_2~3_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1_축_4~7_2~3_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1축_4~7_2~3_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1축_4~7_2~3_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor12_pair34_57_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~2_1축_3~4_2축_5~7_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "r_pop_top3_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top4, top1_3, top5_8, actual_top3, odds in zip(
        top4_series, top1_3_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor1_candidates = top1_3[:2]
        second_candidates = top4[2:4]
        third_candidates = top5_8[:3]
        anchor1_set = set(anchor1_candidates)
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            len(anchor1_candidates) == 2
            and len(anchor1_set) == 2
            and len(second_candidates) == 2
            and len(second_set) == 2
            and len(third_candidates) == 3
            and len(third_set) == 3
            and anchor1_set.isdisjoint(second_set)
            and anchor1_set.isdisjoint(third_set)
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] in anchor1_set
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop1~2_1축_3~4_2축_5~7_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop1~2_1축_3~4_2축_5~7_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["1~2축_3~4_2축_5~7_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["1~2축_3~4_2축_5~7_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor3_pair124_567_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop3_1축_1~2,4_2축_5~7_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 9 * bet_unit

    for top1_3, top4, top5_8, actual_top3, odds in zip(
        top1_3_series, top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top1_3[2] if len(top1_3) >= 3 else None
        second_candidates = [gate for gate in top4 if gate != anchor_gate][:3]
        third_candidates = top5_8[:3]
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(second_candidates) == 3
            and len(second_set) == 3
            and len(third_candidates) == 3
            and len(third_set) == 3
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop3_1축_1~2,4_2축_5~7_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop3_1축_1~2,4_2축_5~7_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["3축_1~2,4_2축_5~7_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["3축_1~2,4_2축_5~7_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor3_pair12_48_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop3_1축_1,2_2축_4~8_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "3~8,12_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top3_8_12_series = race_df["3~8,12_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 10 * bet_unit

    for top1_3, top3_8_12, actual_top3, odds in zip(
        top1_3_series, top3_8_12_series, actual_top3_series, trifecta_odds
    ):
        top1_3_set = set(top1_3)
        anchor_gate = top1_3[2] if len(top1_3) >= 3 else None
        second_candidates = top1_3[:2]
        third_candidates = [gate for gate in top3_8_12 if gate not in top1_3_set][:5]
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(second_candidates) == 2
            and len(second_set) == 2
            and len(third_candidates) == 5
            and len(third_set) == 5
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop3_1축_1,2_2축_4~8_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop3_1축_1,2_2축_4~8_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["3축_1,2_2축_4~8_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["3축_1,2_2축_4~8_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor4_pair123_567_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop4_1축_1~2,3_2축_5~7_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 9 * bet_unit

    for top4, top5_8, actual_top3, odds in zip(
        top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top4[3] if len(top4) >= 4 else None
        second_candidates = top4[:3]
        third_candidates = top5_8[:3]
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(second_candidates) == 3
            and len(second_set) == 3
            and len(third_candidates) == 3
            and len(third_set) == 3
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop4_1축_1~2,3_2축_5~7_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop4_1축_1~2,3_2축_5~7_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["4축_1~2,3_2축_5~7_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["4축_1~2,3_2축_5~7_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor4_box2356_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop4_축_2,3,5,6_4복조_삼쌍_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "r_pop_top6_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top6_series = race_df["r_pop_top6_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top4, top6, top5_8, actual_top3, odds in zip(
        top4_series, top6_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top4[3] if len(top4) >= 4 else None
        candidate_gates = []
        if len(top4) >= 3:
            candidate_gates.extend(top4[1:3])
        top5_6 = top6[4:6] if len(top6) >= 6 else top5_8[:2]
        candidate_gates.extend(top5_6)
        candidate_set = set(candidate_gates)
        valid = (
            anchor_gate is not None
            and len(candidate_gates) == 4
            and len(candidate_set) == 4
            and anchor_gate not in candidate_set
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in candidate_set
                and actual_top3[2] in candidate_set
                and actual_top3[1] != actual_top3[2]
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop4_축_2,3,5,6_4복조_삼쌍_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop4_축_2,3,5,6_4복조_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["4축_2,3,5,6_4복조_삼쌍_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["4축_2,3,5,6_4복조_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor4_pair128_3567_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop4_1축_1,2,8_2축_3,5,6,7_3축_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top4_마번", "5~8_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top4_series = race_df["r_pop_top4_마번"].apply(_parse_gate_list)
    top5_8_series = race_df["5~8_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 12 * bet_unit

    for top4, top5_8, actual_top3, odds in zip(
        top4_series, top5_8_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top4[3] if len(top4) >= 4 else None
        second_candidates = top4[:2] + top5_8[3:4]
        third_candidates = top4[2:3] + top5_8[:3]
        second_set = set(second_candidates)
        third_set = set(third_candidates)
        valid = (
            anchor_gate is not None
            and len(second_candidates) == 3
            and len(second_set) == 3
            and len(third_candidates) == 4
            and len(third_set) == 4
            and anchor_gate not in second_set
            and anchor_gate not in third_set
            and second_set.isdisjoint(third_set)
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in second_set
                and actual_top3[2] in third_set
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop4_1축_1,2,8_2축_3,5,6,7_3축_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop4_1축_1,2,8_2축_3,5,6,7_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["4축_1,2,8_2축_3,5,6,7_3축_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["4축_1,2,8_2축_3,5,6,7_3축_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _augment_anchor3_247_trifecta_for_admin(race_df, bet_unit=100):
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop3_축_2,4~7_삼쌍_적중" in race_df.columns:
        return race_df

    required = {"r_pop_top3_마번", "3~8,12_마번", "실제_top3_마번", "삼쌍승식배당율"}
    if not required.issubset(race_df.columns):
        return race_df

    top1_3_series = race_df["r_pop_top3_마번"].apply(_parse_gate_list)
    top3_8_12_series = race_df["3~8,12_마번"].apply(_parse_gate_list)
    actual_top3_series = race_df["실제_top3_마번"].apply(_parse_gate_list)
    trifecta_odds = pd.to_numeric(race_df["삼쌍승식배당율"], errors="coerce").fillna(0.0)

    hits = []
    refunds = []
    bets = []
    bet_per_race = 20 * bet_unit

    for top1_3, top3_8_12, actual_top3, odds in zip(
        top1_3_series, top3_8_12_series, actual_top3_series, trifecta_odds
    ):
        anchor_gate = top1_3[2] if len(top1_3) >= 3 else None
        second_gate = top1_3[1] if len(top1_3) >= 2 else None
        top1_3_set = set(top1_3)
        top4_7 = [gate for gate in top3_8_12 if gate not in top1_3_set][:4]
        candidate_gates = [second_gate] + top4_7 if second_gate is not None else top4_7
        candidate_set = set(candidate_gates)
        valid = (
            anchor_gate is not None
            and second_gate is not None
            and len(top4_7) == 4
            and len(candidate_gates) == 5
            and len(candidate_set) == 5
            and anchor_gate not in candidate_set
        )
        hit = 0
        refund = 0.0
        bet = float(bet_per_race) if valid else 0.0
        if valid and len(actual_top3) == 3:
            if (
                actual_top3[0] == anchor_gate
                and actual_top3[1] in candidate_set
                and actual_top3[2] in candidate_set
                and actual_top3[1] != actual_top3[2]
            ):
                hit = 1
                refund = float(odds) * bet_unit
        hits.append(hit)
        refunds.append(refund)
        bets.append(bet)

    race_df = race_df.copy()
    race_df["r_pop3_축_2,4~7_삼쌍_적중"] = pd.Series(hits, index=race_df.index, dtype="int64")
    race_df["r_pop3_축_2,4~7_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    race_df["3축_2,4~7_삼쌍_베팅액"] = pd.Series(bets, index=race_df.index, dtype="float64")
    race_df["3축_2,4~7_삼쌍_환수액"] = pd.Series(refunds, index=race_df.index, dtype="float64")
    return race_df


def _build_admin_summary_payload(i_rdate, method_columns=None):
    summary = {}
    summary_total = None
    method_bet_totals = []
    method_bet_by_track = []
    gate_top3_by_city = []
    gate_top3_period_label = i_rdate
    method_bet_total_sum = 0.0
    method_refund_total_sum = 0.0
    method_profit_total_sum = 0.0
    metrics = {
        "roi": 0.0,
        "hit_rate": 0.0,
        "r_pop1_top3_rate": 0.0,
        "r_pop1_top1_rate": 0.0,
        "mdd": 0.0,
        "data_age_sec": None,
        "is_cached": False,
    }
    method_columns = method_columns or ADMIN_SUMMARY_METHOD_COLUMNS

    try:
        base_dt = datetime.strptime(i_rdate, "%Y%m%d")
    except Exception:
        return {
            "i_rdate": i_rdate,
            "from_date": None,
            "to_date": None,
            "summary": summary,
            "summary_total": summary_total,
            "method_bet_totals": method_bet_totals,
            "method_bet_by_track": method_bet_by_track,
            "gate_top3_by_city": gate_top3_by_city,
            "gate_top3_period_label": gate_top3_period_label,
            "method_bet_total_sum": method_bet_total_sum,
            "method_refund_total_sum": method_refund_total_sum,
            "method_profit_total_sum": method_profit_total_sum,
            "metrics": metrics,
        }

    def _nearest_saturday(dt):
        # 기준일과 가장 가까운 토요일을 앵커로 사용한다.
        # (동일 거리면 과거 토요일 우선)
        days_since_sat = (dt.weekday() - 5) % 7
        prev_sat = dt - timedelta(days=days_since_sat)
        next_sat = prev_sat + timedelta(days=7)
        if (dt - prev_sat) <= (next_sat - dt):
            return prev_sat
        return next_sat

    sat_dt = _nearest_saturday(base_dt)
    from_dt = sat_dt - timedelta(days=2)
    to_dt = sat_dt + timedelta(days=2)
    from_date = from_dt.strftime("%Y%m%d")
    to_date = to_dt.strftime("%Y%m%d")
    race_df = None
    has_refund_base = False
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM The1.rec010
            WHERE rdate BETWEEN %s AND %s
              AND r123alloc IS NOT NULL AND r123alloc <> '' AND r123alloc <> '0.00'
              AND r333alloc IS NOT NULL AND r333alloc <> '' AND r333alloc <> '0.00'
            LIMIT 1
            """,
            (from_date, to_date),
        )
        has_refund_base = cursor.fetchone() is not None
    except Exception:
        has_refund_base = True
    finally:
        if cursor:
            cursor.close()

    if has_refund_base:
        try:
            race_df, summary = _run_calc_rpop_anchor_26_trifecta_quietly(
                from_date=from_date,
                to_date=to_date,
                bet_unit=100,
            )
        except Exception as exc:
            print(f"[admin_summary_popup] calc failed: {exc}")
    else:
        summary = {}

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        active_hit_cols = [
            hit_col for _, _, _, hit_col in method_columns if hit_col in race_df.columns
        ]

        # cumulative PnL 기준 최대 낙폭(MDD)
        try:
            if {"총베팅액", "총환수액"}.issubset(set(race_df.columns)):
                sort_cols = [c for c in ["경주일", "경마장", "경주번호"] if c in race_df.columns]
                calc_df = race_df.sort_values(sort_cols) if sort_cols else race_df
                pnl = (
                    calc_df["총환수액"].fillna(0).astype(float)
                    - calc_df["총베팅액"].fillna(0).astype(float)
                )
                if not pnl.empty:
                    equity = pnl.cumsum()
                    drawdown = equity - equity.cummax()
                    metrics["mdd"] = float(drawdown.min())
        except Exception:
            metrics["mdd"] = 0.0

        for label, bet_col, refund_col, hit_col in method_columns:
            if bet_col in race_df.columns and refund_col in race_df.columns:
                bet_amount = float(race_df[bet_col].fillna(0).sum())
                refund_amount = float(race_df[refund_col].fillna(0).sum())
                profit_amount = refund_amount - bet_amount
                hit_count = (
                    int(race_df[hit_col].fillna(0).astype(int).sum())
                    if hit_col in race_df.columns
                    else 0
                )
                method_bet_totals.append(
                    {
                        "label": label,
                        "amount": bet_amount,
                        "refund": refund_amount,
                        "profit": profit_amount,
                        "hits": hit_count,
                    }
                )
                method_bet_total_sum += bet_amount
                method_refund_total_sum += refund_amount
                method_profit_total_sum += profit_amount

        if "경마장" in race_df.columns:
            try:
                grouped = race_df.groupby("경마장", dropna=False)
                for track, gdf in grouped:
                    track_name = str(track or "").strip() or "기타"
                    methods = []
                    track_bet = 0.0
                    track_refund = 0.0
                    track_profit = 0.0
                    if "경주일" in gdf.columns and "경주번호" in gdf.columns:
                        track_races = int(
                            gdf[["경주일", "경주번호"]].drop_duplicates().shape[0]
                        )
                    elif "경주번호" in gdf.columns:
                        track_races = int(gdf["경주번호"].dropna().nunique())
                    else:
                        track_races = int(len(gdf))
                    for label, bet_col, refund_col, hit_col in method_columns:
                        if bet_col not in gdf.columns or refund_col not in gdf.columns:
                            continue
                        bet_amount = float(gdf[bet_col].fillna(0).sum())
                        refund_amount = float(gdf[refund_col].fillna(0).sum())
                        profit_amount = refund_amount - bet_amount
                        hit_count = (
                            int(gdf[hit_col].fillna(0).astype(int).sum())
                            if hit_col in gdf.columns
                            else 0
                        )
                        methods.append(
                            {
                                "label": label,
                                "amount": bet_amount,
                                "refund": refund_amount,
                                "profit": profit_amount,
                                "hits": hit_count,
                            }
                        )
                        track_bet += bet_amount
                        track_refund += refund_amount
                        track_profit += profit_amount
                    if methods:
                        track_hit_races = 0
                        if active_hit_cols:
                            try:
                                track_hit_races = int(
                                    gdf[active_hit_cols]
                                    .fillna(0)
                                    .astype(int)
                                    .gt(0)
                                    .any(axis=1)
                                    .sum()
                                )
                            except Exception:
                                track_hit_races = 0
                        track_bet_per_race = (
                            track_bet / track_races if track_races > 0 else 0.0
                        )
                        method_bet_by_track.append(
                            {
                                "track": track_name,
                                "methods": methods,
                                "total_races": track_races,
                                "total_bet": track_bet,
                                "bet_per_race": track_bet_per_race,
                                "total_refund": track_refund,
                                "total_profit": track_profit,
                                "hit_races": track_hit_races,
                            }
                        )
            except Exception as exc:
                print(f"[admin_summary_popup] track grouping failed: {exc}")

    if method_bet_by_track:
        preferred_track_order = {"서울": 0, "부산": 1}
        method_bet_by_track.sort(
            key=lambda x: (
                preferred_track_order.get(str(x.get("track") or "").strip(), 9),
                str(x.get("track") or ""),
            )
        )

    raw_track_summary = {}
    if isinstance(summary, dict):
        raw_track_summary = summary.get("track_summary", {}) or {}

    # 경마장별 부가 지표(r_pop1~4의 1위/3착내 적중률) 매핑
    track_stat_map = {}
    perf_rows = []
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT rcity, rdate, rno, r_pop, r_rank, rank
            FROM exp011
            WHERE rdate BETWEEN %s AND %s
              AND rno < 80
              AND r_rank BETWEEN 1 AND 98
              AND r_pop BETWEEN 1 AND 4
            ORDER BY rcity, rdate, rno, r_pop
            """,
            (from_date, to_date),
        )
        perf_rows = cursor.fetchall()
    except Exception:
        perf_rows = []
    finally:
        if cursor:
            cursor.close()

    if perf_rows:
        race_perf_map = {}
        for row in perf_rows:
            try:
                track_name = str(row[0] or "").strip() or "기타"
                rdate = str(row[1] or "").strip()
                rno = int(row[2])
                pop_rank = int(row[3])
                actual_rank = int(row[4])
                base_rank = int(row[5])
            except Exception:
                continue
            race_key = (track_name, rdate, rno)
            race_perf = race_perf_map.setdefault(
                race_key,
                {
                    "excluded": False,
                    "actuals": {},
                },
            )
            if pop_rank in (1, 3) and base_rank >= 98:
                race_perf["excluded"] = True
            race_perf["actuals"][pop_rank] = actual_rank

        for (track_name, _rdate, _rno), race_perf in race_perf_map.items():
            if race_perf.get("excluded"):
                continue
            item = track_stat_map.setdefault(
                track_name,
                {
                    "races": 0,
                    "r_pop1_top3_hits": 0,
                    "r_pop1_top1_hits": 0,
                    "r_pop2_top3_hits": 0,
                    "r_pop2_top1_hits": 0,
                    "r_pop3_top3_hits": 0,
                    "r_pop3_top1_hits": 0,
                    "r_pop4_top3_hits": 0,
                    "r_pop4_top1_hits": 0,
                },
            )
            item["races"] += 1
            for pop_rank in (1, 2, 3, 4):
                actual_rank = race_perf["actuals"].get(pop_rank)
                if actual_rank is None:
                    continue
                if actual_rank <= 3:
                    item[f"r_pop{pop_rank}_top3_hits"] += 1
                if actual_rank == 1:
                    item[f"r_pop{pop_rank}_top1_hits"] += 1

        for item in track_stat_map.values():
            races = int(item.get("races", 0) or 0)
            for pop_rank in (1, 2, 3, 4):
                top3_hits = int(item.get(f"r_pop{pop_rank}_top3_hits", 0) or 0)
                top1_hits = int(item.get(f"r_pop{pop_rank}_top1_hits", 0) or 0)
                item[f"r_pop{pop_rank}_top3_rate"] = (
                    top3_hits / races if races > 0 else 0.0
                )
                item[f"r_pop{pop_rank}_top1_rate"] = (
                    top1_hits / races if races > 0 else 0.0
                )
    elif isinstance(summary, dict):
        for tk, d in raw_track_summary.items():
            track_name = str(tk or "").strip() or "기타"
            races = int(d.get("races", 0) or 0)
            top3_hits = int(d.get("r_pop1_top3_hits", 0) or 0)
            top1_hits = int(d.get("r_pop1_top1_hits", 0) or 0)
            track_stat_map[track_name] = {
                "races": races,
                "r_pop1_top3_hits": top3_hits,
                "r_pop1_top3_rate": (top3_hits / races) if races > 0 else 0.0,
                "r_pop1_top1_hits": top1_hits,
                "r_pop1_top1_rate": (top1_hits / races) if races > 0 else 0.0,
                "r_pop2_top3_hits": 0,
                "r_pop2_top3_rate": 0.0,
                "r_pop2_top1_hits": 0,
                "r_pop2_top1_rate": 0.0,
                "r_pop3_top3_hits": 0,
                "r_pop3_top3_rate": 0.0,
                "r_pop3_top1_hits": 0,
                "r_pop3_top1_rate": 0.0,
                "r_pop4_top3_hits": 0,
                "r_pop4_top3_rate": 0.0,
                "r_pop4_top1_hits": 0,
                "r_pop4_top1_rate": 0.0,
            }

    # 경마장별 ROI(환수율) 보강: 캐시/실시간 공통 처리
    for t in method_bet_by_track:
        try:
            t_bet = float(t.get("total_bet", 0.0) or 0.0)
            t_refund = float(t.get("total_refund", 0.0) or 0.0)
            t_roi = (t_refund / t_bet) if t_bet > 0 else 0.0
            t["roi"] = t_roi
            t["roi_pct"] = t_roi * 100.0
            t_name = str(t.get("track") or "").strip() or "기타"
            ts = track_stat_map.get(t_name, {})
            t["hit_races"] = int(t.get("hit_races", 0) or 0)
            t["r_pop1_top3_rate"] = float(ts.get("r_pop1_top3_rate", 0.0) or 0.0)
            t["r_pop1_top1_rate"] = float(ts.get("r_pop1_top1_rate", 0.0) or 0.0)
            t["r_pop2_top3_rate"] = float(ts.get("r_pop2_top3_rate", 0.0) or 0.0)
            t["r_pop2_top1_rate"] = float(ts.get("r_pop2_top1_rate", 0.0) or 0.0)
            t["r_pop3_top3_rate"] = float(ts.get("r_pop3_top3_rate", 0.0) or 0.0)
            t["r_pop3_top1_rate"] = float(ts.get("r_pop3_top1_rate", 0.0) or 0.0)
            t["r_pop4_top3_rate"] = float(ts.get("r_pop4_top3_rate", 0.0) or 0.0)
            t["r_pop4_top1_rate"] = float(ts.get("r_pop4_top1_rate", 0.0) or 0.0)
            t["r_pop1_top3_hits"] = int(ts.get("r_pop1_top3_hits", 0) or 0)
            t["r_pop1_top1_hits"] = int(ts.get("r_pop1_top1_hits", 0) or 0)
            t["r_pop2_top3_hits"] = int(ts.get("r_pop2_top3_hits", 0) or 0)
            t["r_pop2_top1_hits"] = int(ts.get("r_pop2_top1_hits", 0) or 0)
            t["r_pop3_top3_hits"] = int(ts.get("r_pop3_top3_hits", 0) or 0)
            t["r_pop3_top1_hits"] = int(ts.get("r_pop3_top1_hits", 0) or 0)
            t["r_pop4_top3_hits"] = int(ts.get("r_pop4_top3_hits", 0) or 0)
            t["r_pop4_top1_hits"] = int(ts.get("r_pop4_top1_hits", 0) or 0)
            t["r_pop1_top3_rate_pct"] = t["r_pop1_top3_rate"] * 100.0
            t["r_pop1_top1_rate_pct"] = t["r_pop1_top1_rate"] * 100.0
            t["r_pop2_top3_rate_pct"] = t["r_pop2_top3_rate"] * 100.0
            t["r_pop2_top1_rate_pct"] = t["r_pop2_top1_rate"] * 100.0
            t["r_pop3_top3_rate_pct"] = t["r_pop3_top3_rate"] * 100.0
            t["r_pop3_top1_rate_pct"] = t["r_pop3_top1_rate"] * 100.0
            t["r_pop4_top3_rate_pct"] = t["r_pop4_top3_rate"] * 100.0
            t["r_pop4_top1_rate_pct"] = t["r_pop4_top1_rate"] * 100.0
        except Exception:
            t["roi"] = 0.0
            t["roi_pct"] = 0.0
            t["hit_races"] = 0
            t["r_pop1_top3_rate"] = 0.0
            t["r_pop1_top1_rate"] = 0.0
            t["r_pop2_top3_rate"] = 0.0
            t["r_pop2_top1_rate"] = 0.0
            t["r_pop3_top3_rate"] = 0.0
            t["r_pop3_top1_rate"] = 0.0
            t["r_pop4_top3_rate"] = 0.0
            t["r_pop4_top1_rate"] = 0.0
            t["r_pop1_top3_hits"] = 0
            t["r_pop1_top1_hits"] = 0
            t["r_pop2_top3_hits"] = 0
            t["r_pop2_top1_hits"] = 0
            t["r_pop3_top3_hits"] = 0
            t["r_pop3_top1_hits"] = 0
            t["r_pop4_top3_hits"] = 0
            t["r_pop4_top1_hits"] = 0
            t["r_pop1_top3_rate_pct"] = 0.0
            t["r_pop1_top1_rate_pct"] = 0.0
            t["r_pop2_top3_rate_pct"] = 0.0
            t["r_pop2_top1_rate_pct"] = 0.0
            t["r_pop3_top3_rate_pct"] = 0.0
            t["r_pop3_top1_rate_pct"] = 0.0
            t["r_pop4_top3_rate_pct"] = 0.0
            t["r_pop4_top1_rate_pct"] = 0.0

    if method_bet_by_track and not any(
        str(x.get("track") or "").strip() in {"서울", "부산"} for x in method_bet_by_track
    ):
        method_bet_by_track.sort(key=lambda x: str(x.get("track") or ""))

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        total_races = 0
        if "경주일" in race_df.columns and "경주번호" in race_df.columns:
            total_races = int(race_df[["경주일", "경주번호"]].drop_duplicates().shape[0])
        elif "경주번호" in race_df.columns:
            total_races = int(race_df["경주번호"].dropna().nunique())
        else:
            total_races = int(len(race_df))

        total_hits = 0
        if active_hit_cols:
            try:
                total_hits = int(
                    race_df[active_hit_cols]
                    .fillna(0)
                    .astype(int)
                    .gt(0)
                    .any(axis=1)
                    .sum()
                )
            except Exception:
                total_hits = 0

        if total_races > 0:
            total_r_pop1_top1_hits = int(sum((raw_track_summary.get(key, {}) or {}).get("r_pop1_top1_hits", 0) for key in raw_track_summary))
            total_r_pop1_top3_hits = int(sum((raw_track_summary.get(key, {}) or {}).get("r_pop1_top3_hits", 0) for key in raw_track_summary))
            summary_total = {
                "races": total_races,
                "total_bet": method_bet_total_sum,
                "total_refund": method_refund_total_sum,
                "profit": method_profit_total_sum,
                "hits": total_hits,
                "hit_rate": total_hits / total_races if total_races > 0 else 0.0,
                "r_pop1_top1_hits": total_r_pop1_top1_hits,
                "r_pop1_top1_rate": total_r_pop1_top1_hits / total_races if total_races > 0 else 0.0,
                "r_pop1_top3_hits": total_r_pop1_top3_hits,
                "r_pop1_top3_rate": total_r_pop1_top3_hits / total_races if total_races > 0 else 0.0,
                "refund_rate": method_refund_total_sum / method_bet_total_sum if method_bet_total_sum > 0 else 0.0,
                "avg_bet": method_bet_total_sum / total_races if total_races > 0 else 0.0,
            }

    if summary_total:
        metrics["roi"] = float(summary_total.get("refund_rate", 0.0) or 0.0)
        metrics["hit_rate"] = float(summary_total.get("hit_rate", 0.0) or 0.0)
        metrics["r_pop1_top3_rate"] = float(summary_total.get("r_pop1_top3_rate", 0.0) or 0.0)
        metrics["r_pop1_top1_rate"] = float(summary_total.get("r_pop1_top1_rate", 0.0) or 0.0)
    elif method_bet_total_sum > 0:
        metrics["roi"] = method_refund_total_sum / method_bet_total_sum
    if metrics.get("data_age_sec") is None and not metrics.get("is_cached"):
        metrics["data_age_sec"] = 0
    metrics["roi_pct"] = float(metrics.get("roi", 0.0) or 0.0) * 100.0
    metrics["hit_rate_pct"] = float(metrics.get("hit_rate", 0.0) or 0.0) * 100.0
    metrics["r_pop1_top3_rate_pct"] = float(metrics.get("r_pop1_top3_rate", 0.0) or 0.0) * 100.0
    metrics["r_pop1_top1_rate_pct"] = float(metrics.get("r_pop1_top1_rate", 0.0) or 0.0) * 100.0
    metrics["mdd_abs"] = abs(float(metrics.get("mdd", 0.0) or 0.0))

    # 관리자 팝업 하단용: 경마장별 마번/기수/마방 Top5 (앵커 토요일 기준 ±2일)
    try:
        gate_from_dt = sat_dt - timedelta(days=2)
        gate_to_dt = sat_dt + timedelta(days=2)
        gate_from = gate_from_dt.strftime("%Y%m%d")
        gate_to = gate_to_dt.strftime("%Y%m%d")
        gate_top3_period_label = (
            f"{gate_from_dt.strftime('%Y.%m.%d')} ~ {gate_to_dt.strftime('%Y.%m.%d')}"
        )

        gate_rows = []
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT rcity, gate, r_rank, jockey, trainer
                FROM exp011
                WHERE rdate BETWEEN %s AND %s
                  AND r_rank <= 98
                  AND rno < 80
                ORDER BY rcity, rdate, rno, gate
                """,
                (gate_from, gate_to),
            )
            gate_rows = cursor.fetchall()
        finally:
            if cursor:
                cursor.close()

        def _acc_perf(bucket, key, rank):
            name = str(key or "").strip()
            if not name:
                return
            item = bucket.setdefault(
                name,
                {
                    "name": name,
                    "entries": 0,
                    "top3": 0,
                    "wins": 0,
                    "seconds": 0,
                    "thirds": 0,
                    "rank_sum": 0.0,
                },
            )
            item["entries"] += 1
            item["rank_sum"] += float(rank)
            if rank <= 3:
                item["top3"] += 1
            if rank == 1:
                item["wins"] += 1
            elif rank == 2:
                item["seconds"] += 1
            elif rank == 3:
                item["thirds"] += 1

        def _top5_perf(bucket):
            rows = []
            for it in bucket.values():
                entries = int(it.get("entries") or 0)
                if entries <= 0:
                    continue
                rows.append(
                    {
                        "name": it.get("name", ""),
                        "entries": entries,
                        "top3": int(it.get("top3") or 0),
                        "top3_pct": (float(it.get("top3") or 0) / entries) * 100.0,
                        "wins": int(it.get("wins") or 0),
                        "seconds": int(it.get("seconds") or 0),
                        "thirds": int(it.get("thirds") or 0),
                        "avg_rank": float(it.get("rank_sum") or 0.0) / entries,
                    }
                )
            rows.sort(
                key=lambda x: (
                    -x["top3"],
                    -x["wins"],
                    x["avg_rank"],
                    -x["entries"],
                    str(x["name"]),
                )
            )
            return rows[:5]

        city_perf_map = {}
        for row in gate_rows:
            try:
                rcity = str(row[0] or "").strip()
                gate = str(row[1] or "").strip()
                rank = int(row[2])
                jockey = row[3]
                trainer = row[4]
                if not rcity or not gate or rank < 1 or rank > 12:
                    continue
                city_bucket = city_perf_map.setdefault(
                    rcity, {"gates": {}, "jockeys": {}, "trainers": {}}
                )
                _acc_perf(city_bucket["gates"], gate, rank)
                _acc_perf(city_bucket["jockeys"], jockey, rank)
                _acc_perf(city_bucket["trainers"], trainer, rank)
            except Exception:
                continue

        preferred_city_order = ["서울", "부산"]
        ordered_cities = [c for c in preferred_city_order if c in city_perf_map]
        ordered_cities.extend(
            sorted([c for c in city_perf_map.keys() if c not in preferred_city_order])
        )
        for city in ordered_cities:
            perf = city_perf_map.get(city, {})
            gate_top3_by_city.append(
                {
                    "rcity": city,
                    "gates": _top5_perf(perf.get("gates", {})),
                    "jockeys": _top5_perf(perf.get("jockeys", {})),
                    "trainers": _top5_perf(perf.get("trainers", {})),
                }
            )
    except Exception:
        gate_top3_by_city = []

    return {
        "i_rdate": i_rdate,
        "from_date": from_date,
        "to_date": to_date,
        "summary": summary,
        "summary_total": summary_total,
        "method_bet_totals": method_bet_totals,
        "method_bet_by_track": method_bet_by_track,
        "gate_top3_by_city": gate_top3_by_city,
        "gate_top3_period_label": gate_top3_period_label,
        "method_bet_total_sum": method_bet_total_sum,
        "method_refund_total_sum": method_refund_total_sum,
        "method_profit_total_sum": method_profit_total_sum,
        "metrics": metrics,
    }


def _build_admin_profit_analysis_payload(i_rdate):
    summary_total = None
    method_bet_by_track = []
    metrics = {
        "roi": 0.0,
        "roi_pct": 0.0,
    }
    admin_profit_groups = copy.deepcopy(ADMIN_PROFIT_GROUPS)

    prep = _prepare_admin_profit_analysis_race_df(i_rdate, bet_unit=100)
    from_date = prep.get("from_date")
    to_date = prep.get("to_date")
    race_df = prep.get("race_df")
    valid_race_keys = prep.get("valid_race_keys", set())

    if not from_date or not to_date:
        return {
            "i_rdate": i_rdate,
            "from_date": None,
            "to_date": None,
            "summary_total": summary_total,
            "method_bet_by_track": method_bet_by_track,
            "metrics": metrics,
        }

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        primary_total_bet = 0.0
        primary_total_refund = 0.0
        primary_total_hits = 0
        primary_total_races = 0
        track_stat_map = {}

        perf_rows = []
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT rcity, rdate, rno, r_pop, r_rank, rank
                FROM exp011
                WHERE rdate BETWEEN %s AND %s
                  AND rno < 80
                  AND r_rank BETWEEN 1 AND 98
                  AND r_pop BETWEEN 1 AND 4
                ORDER BY rcity, rdate, rno, r_pop
                """,
                (from_date, to_date),
            )
            perf_rows = cursor.fetchall()
        except Exception:
            perf_rows = []
        finally:
            if cursor:
                cursor.close()

        if perf_rows:
            race_perf_map = {}
            for row in perf_rows:
                try:
                    track_name = str(row[0] or "").strip() or "기타"
                    rdate = str(row[1] or "").strip()
                    rno = int(row[2])
                    pop_rank = int(row[3])
                    actual_rank = int(row[4])
                    base_rank = int(row[5])
                except Exception:
                    continue
                race_key = (track_name, rdate, rno)
                if valid_race_keys and race_key not in valid_race_keys:
                    continue
                race_perf = race_perf_map.setdefault(
                    race_key,
                    {
                        "excluded": False,
                        "actuals": {},
                    },
                )
                if pop_rank in (1, 3) and base_rank >= 98:
                    race_perf["excluded"] = True
                race_perf["actuals"][pop_rank] = actual_rank

            for (track_name, _rdate, _rno), race_perf in race_perf_map.items():
                if race_perf.get("excluded"):
                    continue
                item = track_stat_map.setdefault(
                    track_name,
                    {
                        "races": 0,
                        "r_pop1_top3_hits": 0,
                        "r_pop1_top1_hits": 0,
                        "r_pop2_top3_hits": 0,
                        "r_pop2_top1_hits": 0,
                        "r_pop3_top3_hits": 0,
                        "r_pop3_top1_hits": 0,
                        "r_pop4_top3_hits": 0,
                        "r_pop4_top1_hits": 0,
                    },
                )
                item["races"] += 1
                for pop_rank in (1, 2, 3, 4):
                    actual_rank = race_perf["actuals"].get(pop_rank)
                    if actual_rank is None:
                        continue
                    if actual_rank <= 3:
                        item[f"r_pop{pop_rank}_top3_hits"] += 1
                    if actual_rank == 1:
                        item[f"r_pop{pop_rank}_top1_hits"] += 1

            for item in track_stat_map.values():
                races = int(item.get("races", 0) or 0)
                for pop_rank in (1, 2, 3, 4):
                    top3_hits = int(item.get(f"r_pop{pop_rank}_top3_hits", 0) or 0)
                    top1_hits = int(item.get(f"r_pop{pop_rank}_top1_hits", 0) or 0)
                    item[f"r_pop{pop_rank}_top3_rate"] = (
                        top3_hits / races if races > 0 else 0.0
                    )
                    item[f"r_pop{pop_rank}_top1_rate"] = (
                        top1_hits / races if races > 0 else 0.0
                    )

        for track_name in ["서울", "부산"]:
            track_df = race_df[race_df.get("경마장") == track_name].copy()
            if track_df.empty:
                continue

            track_races = int(
                track_df[["경주일", "경주번호"]].drop_duplicates().shape[0]
                if {"경주일", "경주번호"}.issubset(track_df.columns)
                else len(track_df)
            )
            methods = []
            track_bet = 0.0
            track_refund = 0.0

            for group_label, strategy_keys in admin_profit_groups.get(track_name, {}).items():
                bet_cols = []
                refund_cols = []
                hit_cols = []
                detail_methods = []
                for key in strategy_keys:
                    column_meta = ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS.get(key)
                    if not column_meta:
                        continue
                    if column_meta["bet"] in track_df.columns:
                        bet_cols.append(column_meta["bet"])
                    if column_meta["refund"] in track_df.columns:
                        refund_cols.append(column_meta["refund"])
                    if column_meta["hit"] in track_df.columns:
                        hit_cols.append(column_meta["hit"])
                    bet_amount = (
                        float(track_df[column_meta["bet"]].fillna(0).sum())
                        if column_meta["bet"] in track_df.columns
                        else 0.0
                    )
                    refund_amount = (
                        float(track_df[column_meta["refund"]].fillna(0).sum())
                        if column_meta["refund"] in track_df.columns
                        else 0.0
                    )
                    hit_count = (
                        int(track_df[column_meta["hit"]].fillna(0).astype(int).sum())
                        if column_meta["hit"] in track_df.columns
                        else 0
                    )
                    detail_methods.append(
                        {
                            "label": f"  - {ADMIN_PROFIT_STRATEGY_LABELS.get(key, key)}",
                            "strategy_key": key,
                            "amount": bet_amount,
                            "refund": refund_amount,
                            "profit": refund_amount - bet_amount,
                            "hits": hit_count,
                            "holes_per_race": column_meta.get("holes_per_race", 0),
                            "is_support_detail": group_label == "보조베팅",
                            "strategy_tone": (
                                "cool-lime"
                                if key == "anchor1_47_23"
                                else (
                                    "cool-lime"
                                    if key == "anchor2_pair146_378_trifecta"
                                    else ""
                                )
                            ),
                        }
                    )

                group_bet = float(track_df[bet_cols].sum().sum()) if bet_cols else 0.0
                group_refund = (
                    float(track_df[refund_cols].sum().sum()) if refund_cols else 0.0
                )
                group_profit = group_refund - group_bet
                group_holes_per_race = int(
                    sum(
                        ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS.get(key, {}).get(
                            "holes_per_race", 0
                        )
                        for key in strategy_keys
                    )
                )
                group_hits = _admin_profit_hit_race_count(track_df, hit_cols)
                methods.append(
                    {
                        "label": group_label,
                        "amount": group_bet,
                        "refund": group_refund,
                        "profit": group_profit,
                        "hits": group_hits,
                        "holes_per_race": group_holes_per_race,
                        "is_group": True,
                        "is_support_group": group_label == "보조베팅",
                        "is_primary_group": group_label == "주력베팅",
                    }
                )
                detail_methods = _merge_admin_detail_methods_by_label(detail_methods)
                detail_methods.sort(key=_admin_method_sort_key)
                methods.extend(detail_methods)
                track_bet += group_bet
                track_refund += group_refund
                if group_label == "주력베팅":
                    primary_total_bet += group_bet
                    primary_total_refund += group_refund
                    primary_total_hits += group_hits
                    primary_total_races += track_races

            track_profit = track_refund - track_bet
            track_hit_races = (
                int(sum(1 for item in methods if item["hits"] > 0))
                if track_races == 0
                else 0
            )
            if methods:
                hit_cols_all = []
                for group_label, strategy_keys in admin_profit_groups.get(track_name, {}).items():
                    for key in strategy_keys:
                        column_meta = ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS.get(key)
                        if column_meta and column_meta["hit"] in track_df.columns:
                            hit_cols_all.append(column_meta["hit"])
                if hit_cols_all:
                    track_hit_races = _admin_profit_hit_race_count(track_df, hit_cols_all)
                method_bet_by_track.append(
                    {
                        "track": track_name,
                        "methods": methods,
                        "total_races": track_races,
                        "total_bet": track_bet,
                        "total_refund": track_refund,
                        "total_profit": track_profit,
                        "total_holes_per_race": int(
                            sum(
                                ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS.get(key, {}).get(
                                    "holes_per_race", 0
                                )
                                for groups in admin_profit_groups.get(track_name, {}).values()
                                for key in groups
                            )
                        ),
                        "hit_races": track_hit_races,
                        "roi": (track_refund / track_bet) if track_bet > 0 else 0.0,
                        "roi_pct": ((track_refund / track_bet) * 100) if track_bet > 0 else 0.0,
                        "r_pop1_top1_hits": int(track_stat_map.get(track_name, {}).get("r_pop1_top1_hits", 0) or 0),
                        "r_pop1_top1_rate": float(track_stat_map.get(track_name, {}).get("r_pop1_top1_rate", 0.0) or 0.0),
                        "r_pop1_top1_rate_pct": float(track_stat_map.get(track_name, {}).get("r_pop1_top1_rate", 0.0) or 0.0) * 100.0,
                        "r_pop1_top3_hits": int(track_stat_map.get(track_name, {}).get("r_pop1_top3_hits", 0) or 0),
                        "r_pop1_top3_rate": float(track_stat_map.get(track_name, {}).get("r_pop1_top3_rate", 0.0) or 0.0),
                        "r_pop1_top3_rate_pct": float(track_stat_map.get(track_name, {}).get("r_pop1_top3_rate", 0.0) or 0.0) * 100.0,
                        "r_pop2_top1_hits": int(track_stat_map.get(track_name, {}).get("r_pop2_top1_hits", 0) or 0),
                        "r_pop2_top1_rate": float(track_stat_map.get(track_name, {}).get("r_pop2_top1_rate", 0.0) or 0.0),
                        "r_pop2_top1_rate_pct": float(track_stat_map.get(track_name, {}).get("r_pop2_top1_rate", 0.0) or 0.0) * 100.0,
                        "r_pop2_top3_hits": int(track_stat_map.get(track_name, {}).get("r_pop2_top3_hits", 0) or 0),
                        "r_pop2_top3_rate": float(track_stat_map.get(track_name, {}).get("r_pop2_top3_rate", 0.0) or 0.0),
                        "r_pop2_top3_rate_pct": float(track_stat_map.get(track_name, {}).get("r_pop2_top3_rate", 0.0) or 0.0) * 100.0,
                        "r_pop3_top1_hits": int(track_stat_map.get(track_name, {}).get("r_pop3_top1_hits", 0) or 0),
                        "r_pop3_top1_rate": float(track_stat_map.get(track_name, {}).get("r_pop3_top1_rate", 0.0) or 0.0),
                        "r_pop3_top1_rate_pct": float(track_stat_map.get(track_name, {}).get("r_pop3_top1_rate", 0.0) or 0.0) * 100.0,
                        "r_pop3_top3_hits": int(track_stat_map.get(track_name, {}).get("r_pop3_top3_hits", 0) or 0),
                        "r_pop3_top3_rate": float(track_stat_map.get(track_name, {}).get("r_pop3_top3_rate", 0.0) or 0.0),
                        "r_pop3_top3_rate_pct": float(track_stat_map.get(track_name, {}).get("r_pop3_top3_rate", 0.0) or 0.0) * 100.0,
                        "r_pop4_top1_hits": int(track_stat_map.get(track_name, {}).get("r_pop4_top1_hits", 0) or 0),
                        "r_pop4_top1_rate": float(track_stat_map.get(track_name, {}).get("r_pop4_top1_rate", 0.0) or 0.0),
                        "r_pop4_top1_rate_pct": float(track_stat_map.get(track_name, {}).get("r_pop4_top1_rate", 0.0) or 0.0) * 100.0,
                        "r_pop4_top3_hits": int(track_stat_map.get(track_name, {}).get("r_pop4_top3_hits", 0) or 0),
                        "r_pop4_top3_rate": float(track_stat_map.get(track_name, {}).get("r_pop4_top3_rate", 0.0) or 0.0),
                        "r_pop4_top3_rate_pct": float(track_stat_map.get(track_name, {}).get("r_pop4_top3_rate", 0.0) or 0.0) * 100.0,
                    }
                )
        summary_total = {
            "races": primary_total_races,
            "hits": primary_total_hits,
            "total_bet": primary_total_bet,
            "total_refund": primary_total_refund,
            "profit": primary_total_refund - primary_total_bet,
        }
        metrics["roi"] = (
            (primary_total_refund / primary_total_bet) if primary_total_bet > 0 else 0.0
        )
        metrics["roi_pct"] = metrics["roi"] * 100

    return {
        "i_rdate": i_rdate,
        "from_date": from_date,
        "to_date": to_date,
        "summary_total": summary_total,
        "method_bet_by_track": method_bet_by_track,
        "metrics": metrics,
    }


def _extract_image_src(html_text):
    if not html_text:
        return ""
    text = unescape(str(html_text))
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE)
    return (m.group(1) if m else "").strip()


def _favicon_url(link):
    try:
        host = (urlparse(link).netloc or "").strip()
        if not host:
            return ""
        return f"https://www.google.com/s2/favicons?domain={host}&sz=64"
    except Exception:
        return ""


def _fetch_google_rss(query_text, limit=8, cache_key_prefix="home:rss"):
    cache_key = f"{cache_key_prefix}:{query_text}:{limit}"
    stale_key = f"{cache_key}:stale"

    cached = _cache_copy_get(cache_key)
    if cached is not None:
        return cached

    query = quote(query_text)
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    items = []
    try:
        req = Request(
            rss_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; thethe9-bot/1.0; +https://thethe9.com)"
            },
        )
        with urlopen(req, timeout=HOME_NEWS_TIMEOUT_SEC) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        if channel is not None:
            for node in channel.findall("item")[:limit]:
                title = (node.findtext("title") or "").strip()
                link = (node.findtext("link") or "").strip()
                pub_date = (node.findtext("pubDate") or "").strip()
                description = (node.findtext("description") or "").strip()
                source_node = node.find("source")
                source = (source_node.text if source_node is not None else "").strip()
                thumbnail = _extract_image_src(description) or _favicon_url(link)

                if not title or not link:
                    continue
                items.append(
                    {
                        "title": title,
                        "link": link,
                        "pub_date": pub_date,
                        "source": source,
                        "thumbnail": thumbnail,
                    }
                )
    except Exception as exc:
        print(f"[rss] fetch failed ({query_text}): {exc}")
        stale = _cache_copy_get(stale_key)
        if stale is not None:
            _cache_copy_set(cache_key, stale, HOME_NEWS_CACHE_TTL)
            return stale
        items = []

    _cache_copy_set(cache_key, items, HOME_NEWS_CACHE_TTL)
    if items:
        _cache_copy_set(stale_key, items, HOME_NEWS_STALE_TTL)
    return items


def _fetch_public_feed(feed_name, feed_url, limit=10):
    items = []
    try:
        req = Request(
            feed_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; thethe9-bot/1.0; +https://thethe9.com)"
            },
        )
        with urlopen(req, timeout=3) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)

        # RSS 2.0
        channel = root.find("channel")
        if channel is not None:
            for node in channel.findall("item")[:limit]:
                title = (node.findtext("title") or "").strip()
                link = (node.findtext("link") or "").strip()
                pub_date = (node.findtext("pubDate") or "").strip()
                description = (node.findtext("description") or "").strip()
                thumbnail = _extract_image_src(description) or _favicon_url(link)
                if title and link:
                    items.append(
                        {
                            "title": title,
                            "link": link,
                            "pub_date": pub_date,
                            "source": feed_name,
                            "thumbnail": thumbnail,
                        }
                    )
            return items

        # Atom
        atom_ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("a:entry", atom_ns)[:limit]:
            title = (entry.findtext("a:title", default="", namespaces=atom_ns) or "").strip()
            link_node = entry.find("a:link", atom_ns)
            link = (link_node.attrib.get("href", "") if link_node is not None else "").strip()
            updated = (entry.findtext("a:updated", default="", namespaces=atom_ns) or "").strip()
            summary = (entry.findtext("a:summary", default="", namespaces=atom_ns) or "").strip()
            content = (entry.findtext("a:content", default="", namespaces=atom_ns) or "").strip()
            thumbnail = _extract_image_src(content or summary) or _favicon_url(link)
            if title and link:
                items.append(
                    {
                        "title": title,
                        "link": link,
                        "pub_date": updated,
                        "source": feed_name,
                        "thumbnail": thumbnail,
                    }
                )
    except Exception as exc:
        print(f"[humor] feed failed ({feed_name}): {exc}")
    return items


def fetch_recent_racing_news(limit=8):
    return _fetch_google_rss("경마", limit=limit, cache_key_prefix="home:racing_news")


def fetch_recent_kra_notices(limit=6):
    # park.kra.co.kr 공지성 게시물을 우선 수집
    queries = [
        "site:park.kra.co.kr 공지사항 한국마사회",
        "site:park.kra.co.kr 렛츠런파크 공지사항",
        "site:park.kra.co.kr 방문안내 공지사항",
    ]
    merged = []
    seen = set()
    for q in queries:
        rows = _fetch_google_rss(q, limit=8, cache_key_prefix="home:kra_notice")
        for item in rows:
            link = (item.get("link") or "").strip()
            title = (item.get("title") or "").strip()
            key = link or title
            if not key or key in seen:
                continue
            if "park.kra.co.kr" not in link:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= limit:
                return merged
    return merged[:limit]


def fetch_recent_humor(limit=6):
    cache_key = f"home:humor:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # 국내 커뮤니티 공개 RSS/피드 우선 수집
    community_feeds = [
        ("클리앙 모두의공원", "https://www.clien.net/service/board/park/rss"),
        ("뽐뿌 유머/감동", "https://www.ppomppu.co.kr/rss/humor.xml"),
        ("루리웹 유머게시판", "https://bbs.ruliweb.com/community/board/300143/rss"),
        ("오늘의유머 베스트", "https://www.todayhumor.co.kr/rss/todayhumor_best.xml"),
    ]
    humor_items = []
    seen = set()
    hangul_re = re.compile(r"[가-힣]")
    for source_name, source_url in community_feeds:
        rows = _fetch_public_feed(source_name, source_url, limit=12)
        for item in rows:
            title = (item.get("title") or "").strip()
            link = (item.get("link") or "").strip()
            key = link or title
            if not key or key in seen:
                continue
            if not hangul_re.search(title):
                continue
            seen.add(key)
            humor_items.append(item)
            if len(humor_items) >= limit:
                cache.set(cache_key, humor_items, 600)  # 10 minutes
                return humor_items

    # 커뮤니티 피드가 모두 실패하면 기존 방식으로 완만한 fallback
    if not humor_items:
        fallback_rows = _fetch_google_rss(
            "유머 밈 화제 한국",
            limit=max(limit, 8),
            cache_key_prefix="home:humor_ko_fallback",
        )
        for item in fallback_rows:
            title = (item.get("title") or "").strip()
            link = (item.get("link") or "").strip()
            key = link or title
            if not key or key in seen:
                continue
            if not hangul_re.search(title):
                continue
            seen.add(key)
            humor_items.append(item)
            if len(humor_items) >= limit:
                break

    cache.set(cache_key, humor_items, 600)  # 10 minutes
    return humor_items

@ensure_csrf_cookie
def home(request):
    t_home_start = perf_counter()
    t_prev = t_home_start
    timing_steps = []

    def mark_timing(step_name):
        nonlocal t_prev
        now = perf_counter()
        timing_steps.append((step_name, (now - t_prev) * 1000.0))
        t_prev = now

    q = request.GET.get("q") if request.GET.get("q") != None else ""  # 경마일

    view_type = request.GET.get("view_type") if request.GET.get("view_type") != None else ""  # 정렬방식
    today_ymd = datetime.now().strftime("%Y%m%d")

    if q == "":
        # rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]  # 초기값은 금요일

        # rdate = Racing.objects.values("rdate").distinct().order_by("rdate")[:1]

        i_rdate = cache.get("home:default_rdate")
        if not i_rdate:
            cursor = None
            rdate = None
            try:
                cursor = connection.cursor()

                strSql = """ 
                        SELECT min(rdate)
                        FROM The1.exp010
                        WHERE rdate >= ( SELECT MAX(DATE_FORMAT(CAST(rdate AS DATE) - INTERVAL 4 DAY, '%Y%m%d')) FROM The1.exp010 WHERE rno < 80)
                    ; """

                cursor.execute(strSql)
                rdate = cursor.fetchall()

            except Exception as exc:
                print(f"Failed selecting in rdate: {exc}")
            finally:
                if cursor:
                    cursor.close()

            if rdate and len(rdate) > 0 and rdate[0] and rdate[0][0]:
                i_rdate = rdate[0][0]
            else:
                i_rdate = today_ymd
            cache.set("home:default_rdate", i_rdate, HOME_DEFAULT_RDATE_CACHE_TTL)

        fdate = i_rdate[0:4] + "-" + i_rdate[4:6] + "-" + i_rdate[6:8]

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]

        i_rdate = rdate
        fdate = q

    mark_timing("resolve_date")

    # topics = Topic.objects.exclude(name__icontains=q)

    racings = []
    race, expects, rdays, judged_jockey, changed_race, award_j = [], [], [], [], [], []
    results = []

    race_cache_key = f"home:racings:{i_rdate}"
    cached_racings = _cache_copy_get(race_cache_key)
    if cached_racings is not None:
        racings = cached_racings
    else:
        try:
            racings = get_race(i_rdate, i_awardee="jockey")
            _cache_copy_set(race_cache_key, racings, HOME_RACE_CACHE_TTL)
        except Exception as exc:
            print(f"Failed get_race: {exc}")
    # race_board = get_board_list(i_rdate, i_awardee="jockey")

    prediction_cache_key = f"home:prediction:{i_rdate}"
    cached_prediction = _cache_copy_get(prediction_cache_key)
    if cached_prediction is not None:
        race, expects, rdays, judged_jockey, changed_race, award_j = cached_prediction
    else:
        try:
            race, expects, rdays, judged_jockey, changed_race, award_j = get_prediction(i_rdate)
            _cache_copy_set(
                prediction_cache_key,
                (race, expects, rdays, judged_jockey, changed_race, award_j),
                HOME_RACE_CACHE_TTL,
            )
        except Exception as exc:
            print(f"Failed get_prediction: {exc}")
    # print(racings)
    mark_timing("load_race_prediction")

    # 홈 경주 표시 순서: 일자별 -> 시간별
    def _race_sort_key(row):
        try:
            rdate = str(row[1] or "")
            rtime = str(row[4] or "").replace(":", "").strip()
            if len(rtime) == 3:
                rtime = "0" + rtime
            if not (len(rdate) == 8 and rdate.isdigit() and len(rtime) == 4 and rtime.isdigit()):
                return (rdate, "9999", str(row[0] or ""), int(row[3] or 0))
            return (rdate, rtime, str(row[0] or ""), int(row[3] or 0))
        except Exception:
            return ("99999999", "9999", "", 0)

    race = sorted(race, key=_race_sort_key)

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

    expects_grouped = {}
    for e in expects:
        try:
            if hasattr(e, "rcity"):
                e_rcity = e.rcity
                e_rdate = e.rdate
                e_rno = int(e.rno)
            else:
                e_rcity = e[0]
                e_rdate = e[1]
                e_rno = int(e[3])
            by_city = expects_grouped.setdefault(e_rcity, {})
            by_date = by_city.setdefault(e_rdate, {})
            by_date.setdefault(e_rno, []).append(e)
        except Exception:
            continue

    # legacy results 조회는 홈 템플릿에서 사용하지 않아 제거(쿼리 비용 절감)
    results = []
    mark_timing("load_expect_rows")

    # loadin = get_last2weeks_loadin(i_rdate)

    rflag = False  # 경마일, 비경마일 구분
    for r in rdays:
        # print(r[0], r[2])
        if r[0] == r[2]:
            rflag = True
            break

    # 홈 상단 퍼널 카드용:
    # 1) 출발 전 경주가 있으면 임박 순(TOP3)
    # 2) 출발 전 경주가 없으면 최근(최종) 경주부터 TOP3
    # 신마 경주도 포함
    funnel_candidates = []
    for r in race:
        try:
            rcity, rdate, _, rno, rtime = r[0], r[1], r[2], r[3], r[4]
            try:
                rno_num = int(rno)
            except Exception:
                rno_num = 0

            time_raw = str(rtime or "").strip().replace(":", "")
            if len(time_raw) == 3:
                time_raw = "0" + time_raw
            if len(time_raw) != 4 or not time_raw.isdigit():
                race_dt = None
            else:
                race_dt = datetime.strptime(f"{rdate}{time_raw}", "%Y%m%d%H%M")

            # 임박/종료 판단을 위해 datetime 보존
            sort_dt = race_dt if race_dt is not None else datetime.min
            funnel_candidates.append((sort_dt, race_dt, rno_num, r))
        except Exception:
            continue

    now_dt = datetime.now()
    upcoming_candidates = [item for item in funnel_candidates if item[1] is not None and item[1] >= now_dt]
    funnel_mode = "finished"

    home_default_city_tab = "서울"

    if upcoming_candidates:
        upcoming_candidates.sort(key=lambda x: (x[0], x[2]))
        funnel_races = [row for _, _, _, row in upcoming_candidates[:3]]
        funnel_mode = "imminent"
        try:
            nearest_city = str(upcoming_candidates[0][3][0] or "").strip()
            if nearest_city in ("서울", "부산"):
                home_default_city_tab = nearest_city
        except Exception:
            pass
    else:
        finished_candidates = [item for item in funnel_candidates if item[1] is not None]
        finished_candidates.sort(key=lambda x: (x[0], x[2]), reverse=True)
        funnel_races = [row for _, _, _, row in finished_candidates[:3]]

    # home_right 정보 카드용 데이터 (가벼운 집계)
    race_meta_map = {}
    for r in race:
        try:
            race_meta_map[(r[0], r[1], int(r[3]))] = {
                "rcity": r[0],
                "rdate": r[1],
                "rday": r[2],
                "rno": int(r[3]),
                "rtime": r[4],
                "distance": r[5],
                "grade": r[9],
                "dividing": r[10],
            }
        except Exception:
            continue

    admin_primary_status_grouped = {}
    try:
        admin_profit_prep = _prepare_admin_profit_analysis_race_df(
            i_rdate,
            bet_unit=ADMIN_PROFIT_TRIFECTA_BET_UNIT,
            trio_bet_unit=ADMIN_PROFIT_TRIO_BET_UNIT,
        )
        admin_profit_race_df = admin_profit_prep.get("race_df")
        if (
            admin_profit_race_df is not None
            and hasattr(admin_profit_race_df, "columns")
            and not admin_profit_race_df.empty
            and {"경마장", "경주일", "경주번호"}.issubset(admin_profit_race_df.columns)
        ):
            for track_name in ["서울", "부산"]:
                track_df = admin_profit_race_df[admin_profit_race_df.get("경마장") == track_name].copy()
                if track_df.empty:
                    continue
                hit_cols = []
                for strategy_key in ADMIN_PROFIT_GROUPS.get(track_name, {}).get("주력베팅", []):
                    column_meta = ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS.get(strategy_key) or {}
                    hit_col = column_meta.get("hit")
                    if hit_col and hit_col in track_df.columns:
                        hit_cols.append(hit_col)
                if not hit_cols:
                    continue
                for row in track_df[["경마장", "경주일", "경주번호", *hit_cols]].itertuples(index=False, name=None):
                    row_track = str(row[0] or "").strip()
                    row_date = str(row[1] or "").strip()
                    try:
                        row_rno = int(row[2])
                    except Exception:
                        continue
                    is_hit = _admin_profit_has_hit(row[3:])
                    by_city = admin_primary_status_grouped.setdefault(row_track, {})
                    by_date = by_city.setdefault(row_date, {})
                    by_date[row_rno] = {
                        "state": "hit" if is_hit else "miss",
                        "label": "관리자 주력 적중" if is_hit else "관리자 주력 미적중",
                        "is_hit": is_hit,
                    }
    except Exception as exc:
        print(f"[home] admin primary status build failed: {exc}")

    # home_right 상단 카드: 경마장별 성적 우수 Top3 (마번/기수/마방)
    # 기수/마방 기준 기간: i_rdate -16일 ~ i_rdate -4일
    # 마번 기준 기간: 이번주 토요일 기준 ±2일
    right_city_top3_window_days = 16
    right_city_top3_future_days = -4
    right_city_top3_from = i_rdate
    right_city_top3_to = i_rdate
    right_city_top3_gate_from = i_rdate
    right_city_top3_gate_to = i_rdate
    right_city_top3_gate_label = i_rdate
    try:
        base_dt = datetime.strptime(i_rdate, "%Y%m%d")
        right_city_top3_from = (
            base_dt - timedelta(days=right_city_top3_window_days)
        ).strftime("%Y%m%d")
        right_city_top3_to = (
            base_dt + timedelta(days=right_city_top3_future_days)
        ).strftime("%Y%m%d")
        sat_dt = base_dt + timedelta(days=(5 - base_dt.weekday()))
        gate_from_dt = sat_dt - timedelta(days=2)
        gate_to_dt = sat_dt + timedelta(days=2)
        right_city_top3_gate_from = gate_from_dt.strftime("%Y%m%d")
        right_city_top3_gate_to = gate_to_dt.strftime("%Y%m%d")
        right_city_top3_gate_label = (
            f"{gate_from_dt.strftime('%Y.%m.%d')} ~ {gate_to_dt.strftime('%Y.%m.%d')}"
        )
    except Exception:
        pass
    perf_rows = []
    gate_perf_rows = []
    active_perf_rows = []
    perf_cache_key = f"home:top3_perf:{i_rdate}:{right_city_top3_window_days}:{right_city_top3_future_days}"
    gate_perf_cache_key = f"home:top3_gate_perf:{right_city_top3_gate_from}:{right_city_top3_gate_to}"
    active_perf_cache_key = (
        f"home:top3_active_perf:{right_city_top3_gate_from}:{right_city_top3_gate_to}"
    )
    cached_perf_rows = _cache_copy_get(perf_cache_key)
    cached_gate_perf_rows = _cache_copy_get(gate_perf_cache_key)
    cached_active_perf_rows = _cache_copy_get(active_perf_cache_key)
    if cached_perf_rows is not None:
        perf_rows = cached_perf_rows
    else:
        cursor = None
        try:
            cursor = connection.cursor()
            str_sql_common = """
                SELECT
                    rcity,
                    gate,
                    r_rank,
                    jockey,
                    trainer
                FROM exp011
                WHERE rdate BETWEEN date_format(DATE_ADD(%s, INTERVAL - %s DAY), '%%Y%%m%%d')
                                AND date_format(DATE_ADD(%s, INTERVAL %s DAY), '%%Y%%m%%d')
                  AND r_rank <= 98
                  AND rno < 80
                ORDER BY rcity, rdate, rno, gate
            """
            cursor.execute(
                str_sql_common,
                (i_rdate, right_city_top3_window_days, i_rdate, right_city_top3_future_days),
            )
            perf_rows = cursor.fetchall()
            _cache_copy_set(perf_cache_key, perf_rows, HOME_RACE_CACHE_TTL)
        except Exception as exc:
            print(f"Failed selecting top3 perf rows: {exc}")
            perf_rows = []
        finally:
            if cursor:
                cursor.close()
    if cached_gate_perf_rows is not None:
        gate_perf_rows = cached_gate_perf_rows
    else:
        cursor = None
        try:
            cursor = connection.cursor()
            str_sql_gate = """
                SELECT
                    rcity,
                    gate,
                    r_rank
                FROM exp011
                WHERE rdate BETWEEN %s AND %s
                  AND r_rank <= 98
                  AND rno < 80
                ORDER BY rcity, rdate, rno, gate
            """
            cursor.execute(
                str_sql_gate,
                (right_city_top3_gate_from, right_city_top3_gate_to),
            )
            gate_perf_rows = cursor.fetchall()
            _cache_copy_set(gate_perf_cache_key, gate_perf_rows, HOME_RACE_CACHE_TTL)
        except Exception as exc:
            print(f"Failed selecting top3 gate rows: {exc}")
            gate_perf_rows = []
        finally:
            if cursor:
                cursor.close()
    if cached_active_perf_rows is not None:
        active_perf_rows = cached_active_perf_rows
    else:
        cursor = None
        try:
            cursor = connection.cursor()
            str_sql_active = """
                SELECT
                    rcity,
                    jockey,
                    trainer
                FROM exp011
                WHERE rdate BETWEEN %s AND %s
                  AND rno < 80
                ORDER BY rcity, rdate, rno, gate
            """
            cursor.execute(
                str_sql_active,
                (right_city_top3_gate_from, right_city_top3_gate_to),
            )
            active_perf_rows = cursor.fetchall()
            _cache_copy_set(active_perf_cache_key, active_perf_rows, HOME_RACE_CACHE_TTL)
        except Exception as exc:
            print(f"Failed selecting top3 active perf rows: {exc}")
            active_perf_rows = []
        finally:
            if cursor:
                cursor.close()

    # 기수/마방 데이터가 비어 있으면 기존 expects로 fallback
    if not perf_rows:
        perf_rows = expects
    # 마번 데이터가 비어 있으면 기대데이터로 fallback(집계는 동일 키: gate/r_rank 사용)
    if not gate_perf_rows:
        gate_perf_rows = expects

    active_name_map = {}
    for row in active_perf_rows:
        try:
            if hasattr(row, "rcity"):
                active_city = str(getattr(row, "rcity", "") or "").strip()
                active_jockey = str(getattr(row, "jockey", "") or "").strip()
                active_trainer = str(getattr(row, "trainer", "") or "").strip()
            else:
                active_city = str(row[0] or "").strip()
                active_jockey = str(row[1] or "").strip()
                active_trainer = str(row[2] or "").strip()
            if not active_city:
                continue
            city_active = active_name_map.setdefault(
                active_city, {"jockeys": set(), "trainers": set()}
            )
            if active_jockey:
                city_active["jockeys"].add(active_jockey)
            if active_trainer:
                city_active["trainers"].add(active_trainer)
        except Exception:
            continue

    city_perf_map = {}

    def _acc_perf(bucket, key, rank_value):
        if key is None:
            return
        k = str(key).strip()
        if not k:
            return
        row = bucket.setdefault(
            k,
            {
                "name": k,
                "entries": 0,
                "top3": 0,
                "wins": 0,
                "seconds": 0,
                "thirds": 0,
                "rank_sum": 0.0,
            },
        )
        row["entries"] += 1
        row["rank_sum"] += float(rank_value)
        if rank_value <= 3:
            row["top3"] += 1
        if rank_value == 1:
            row["wins"] += 1
        elif rank_value == 2:
            row["seconds"] += 1
        elif rank_value == 3:
            row["thirds"] += 1

    for e in perf_rows:
        try:
            if hasattr(e, "rcity"):
                e_rcity = str(getattr(e, "rcity", "") or "").strip()
                e_gate = getattr(e, "gate", None)
                e_rank = getattr(e, "r_rank", None)
                e_jockey = getattr(e, "jockey", "")
                e_trainer = getattr(e, "trainer", "")
            else:
                e_rcity = str(e[0] or "").strip()
                # perf_rows 쿼리: (rcity, gate, r_rank, jockey, trainer)
                if len(e) == 5:
                    e_gate = e[1]
                    e_rank = e[2]
                    e_jockey = e[3]
                    e_trainer = e[4]
                # expects fallback: (rcity, rdate, rday, rno, gate, rank, r_rank, ..., jockey, trainer, ...)
                else:
                    e_gate = e[4] if len(e) > 4 else None
                    e_rank = e[6] if len(e) > 6 else None
                    e_jockey = e[9] if len(e) > 9 else ""
                    e_trainer = e[10] if len(e) > 10 else ""

            if not e_rcity:
                continue
            rank_int = int(e_rank)
            if rank_int < 1 or rank_int > 12:
                continue

            city_bucket = city_perf_map.setdefault(
                e_rcity, {"gate": {}, "jockey": {}, "trainer": {}}
            )
            city_active = active_name_map.get(
                e_rcity, {"jockeys": set(), "trainers": set()}
            )
            if str(e_jockey or "").strip() in city_active["jockeys"]:
                _acc_perf(city_bucket["jockey"], e_jockey, rank_int)
            if str(e_trainer or "").strip() in city_active["trainers"]:
                _acc_perf(city_bucket["trainer"], e_trainer, rank_int)
        except Exception:
            continue

    for e in gate_perf_rows:
        try:
            if hasattr(e, "rcity"):
                e_rcity = str(getattr(e, "rcity", "") or "").strip()
                e_gate = getattr(e, "gate", None)
                e_rank = getattr(e, "r_rank", None)
            else:
                e_rcity = str(e[0] or "").strip()
                # gate 전용 쿼리: (rcity, gate, r_rank)
                if len(e) == 3:
                    e_gate = e[1]
                    e_rank = e[2]
                # expects fallback: (rcity, rdate, rday, rno, gate, rank, r_rank, ...)
                else:
                    e_gate = e[4] if len(e) > 4 else None
                    e_rank = e[6] if len(e) > 6 else None

            if not e_rcity:
                continue
            rank_int = int(e_rank)
            if rank_int < 1 or rank_int > 12:
                continue

            city_bucket = city_perf_map.setdefault(
                e_rcity, {"gate": {}, "jockey": {}, "trainer": {}}
            )
            _acc_perf(city_bucket["gate"], e_gate, rank_int)
        except Exception:
            continue

    def _top3_perf(bucket):
        rows = []
        for item in bucket.values():
            entries = int(item.get("entries") or 0)
            if entries <= 0:
                continue
            avg_rank = float(item.get("rank_sum") or 0.0) / entries
            rows.append(
                {
                    "name": item.get("name", ""),
                    "entries": entries,
                    "top3": int(item.get("top3") or 0),
                    "top3_pct": (float(item.get("top3") or 0) / entries) * 100.0,
                    "wins": int(item.get("wins") or 0),
                    "seconds": int(item.get("seconds") or 0),
                    "thirds": int(item.get("thirds") or 0),
                    "avg_rank": avg_rank,
                }
            )
        rows.sort(
            key=lambda x: (
                -x["top3"],
                -x["wins"],
                x["avg_rank"],
                -x["entries"],
                str(x["name"]),
            )
        )
        return rows[:5]

    city_order = []
    seen_city = set()
    preferred_city_order = ["서울", "부산"]

    for city in preferred_city_order:
        if city in city_perf_map and city not in seen_city:
            seen_city.add(city)
            city_order.append(city)

    for r in race:
        try:
            c = str(r[0] or "").strip()
            if c and c not in seen_city and c in city_perf_map:
                seen_city.add(c)
                city_order.append(c)
        except Exception:
            continue

    right_city_top3 = []
    for city in city_order:
        perf = city_perf_map.get(city)
        if not perf:
            continue
        right_city_top3.append(
            {
                "rcity": city,
                "gates": _top3_perf(perf["gate"]),
                "jockeys": _top3_perf(perf["jockey"]),
                "trainers": _top3_perf(perf["trainer"]),
            }
        )

    now_dt = datetime.now()
    imminent_races = []
    for r in race:
        try:
            time_raw = str(r[4] or "").replace(":", "").strip()
            if len(time_raw) == 3:
                time_raw = "0" + time_raw
            if len(time_raw) != 4 or not time_raw.isdigit():
                continue
            race_dt = datetime.strptime(f"{r[1]}{time_raw}", "%Y%m%d%H%M")
            if race_dt >= now_dt:
                imminent_races.append((race_dt, r))
        except Exception:
            continue
    imminent_races.sort(key=lambda x: x[0])
    right_imminent_races = [
        {
            "rcity": rr[0],
            "rdate": rr[1],
            "rday": rr[2],
            "rno": rr[3],
            "rtime": rr[4],
            "distance": rr[5],
            "grade": rr[9],
            "dividing": rr[10],
            "minutes_left": max(0, int((race_dt - now_dt).total_seconds() // 60)),
        }
        for race_dt, rr in imminent_races[:8]
    ]

    right_hot_races = []
    try:
        race_dates = sorted({str(r[1]) for r in race if len(r) > 1 and r[1]})
        if race_dates:
            hot_qs = (
                RaceComment.objects.filter(rdate__in=race_dates)
                .values("rcity", "rdate", "rno")
                .annotate(
                    comment_count=Count("id"),
                    latest_created=Max("created"),
                )
                .order_by("-latest_created", "-comment_count")[:20]
            )
            hot_tmp = []
            for item in hot_qs:
                key = (item["rcity"], item["rdate"], int(item["rno"]))
                meta = race_meta_map.get(key)
                if not meta:
                    continue
                hot_tmp.append(
                    {
                        **meta,
                        "comment_count": int(item["comment_count"]),
                        "latest_created": item.get("latest_created"),
                    }
                )
            hot_tmp.sort(
                key=lambda x: (x.get("latest_created") or datetime.min, x.get("comment_count", 0)),
                reverse=True,
            )
            right_hot_races = hot_tmp[:8]

            hot_keys = {(x.get("rcity"), x.get("rdate"), int(x.get("rno") or 0)) for x in right_hot_races}
            hot_comment_map = {}
            hot_comment_count_map = {}
            if hot_keys:
                hot_comments = (
                    RaceComment.objects.filter(rdate__in=race_dates)
                    .values("rcity", "rdate", "rno", "content", "report_count", "created")
                    .order_by("-created")[:300]
                )
                for c in hot_comments:
                    key = (c.get("rcity"), c.get("rdate"), int(c.get("rno") or 0))
                    if key not in hot_keys:
                        continue
                    hot_comment_count_map[key] = hot_comment_count_map.get(key, 0) + 1
                    bucket = hot_comment_map.setdefault(key, [])
                    if len(bucket) >= 2:
                        continue
                    is_hidden = int(c.get("report_count") or 0) >= 5
                    text = "반대 누적으로 숨김 처리된 댓글입니다." if is_hidden else str(c.get("content") or "").strip()
                    if not text:
                        continue
                    if len(text) > 34:
                        text = text[:34].rstrip() + "..."
                    bucket.append(text)

            for row in right_hot_races:
                key = (row.get("rcity"), row.get("rdate"), int(row.get("rno") or 0))
                row["recent_comments"] = hot_comment_map.get(key, [])
                row["recent_comments_more"] = max(0, int(hot_comment_count_map.get(key, 0)) - len(row["recent_comments"]))
    except (OperationalError, ProgrammingError):
        right_hot_races = []

    right_volatile_races = []
    try:
        changed_counter = {}
        changed_details_map = {}
        for item in changed_race:
            try:
                c_rcity = item[0]
                c_rdate = None
                c_rno = None
                c_reason = ""
                c_gate = ""
                c_horse = ""

                # new format: (rcity, rdate, rday, rno, gate, horse, jockey_old, jockey, reason, r_rank)
                if len(item) >= 10:
                    c_rdate = str(item[1] or "")
                    c_rno = int(item[3])
                    c_reason = item[8] if len(item) > 8 else ""
                    c_gate = item[4] if len(item) > 4 else ""
                    c_horse = item[5] if len(item) > 5 else ""
                # legacy format fallback: (rcity, rday, rno, gate, horse, jockey_old, jockey, reason, r_rank)
                elif len(item) >= 9:
                    c_rday = str(item[1] or "")
                    c_rno = int(item[2])
                    c_reason = item[7] if len(item) > 7 else ""
                    c_gate = item[3] if len(item) > 3 else ""
                    c_horse = item[4] if len(item) > 4 else ""
                    # infer rdate by matching race meta in same weekday/rcity/rno window
                    matched_dates = [
                        str(mv.get("rdate"))
                        for mv in race_meta_map.values()
                        if mv.get("rcity") == c_rcity
                        and int(mv.get("rno") or 0) == c_rno
                        and str(mv.get("rday") or "") == c_rday
                    ]
                    c_rdate = max(matched_dates) if matched_dates else None
                else:
                    continue

                if not c_rdate or c_rno is None:
                    continue
                key = (c_rcity, c_rdate, c_rno)
                changed_counter[key] = changed_counter.get(key, 0) + 1
                gate_label = str(c_gate or "").strip()
                if gate_label and gate_label.isdigit():
                    gate_label = f"{gate_label}번"
                horse_label = str(c_horse or "").strip()
                reason_label = str(c_reason or "").strip()
                detail = " ".join(part for part in [gate_label, horse_label, reason_label] if part).strip()
                if detail:
                    changed_details_map.setdefault(key, []).append(detail)
            except Exception:
                continue

        volatile_tmp = []
        for (c_rcity, c_rdate, c_rno), change_count in changed_counter.items():
            match_meta = race_meta_map.get((c_rcity, c_rdate, c_rno))
            if not match_meta:
                continue
            volatile_tmp.append(
                {
                    **match_meta,
                    "change_count": int(change_count),
                    "change_details": changed_details_map.get((c_rcity, c_rdate, c_rno), [])[:2],
                    "change_detail_more": max(0, len(changed_details_map.get((c_rcity, c_rdate, c_rno), [])) - 2),
                }
            )

        # 최근 경주순(경주일자/발주시간 내림차순) 정렬
        volatile_tmp.sort(
            key=lambda x: (str(x.get("rdate", "")), str(x.get("rtime", ""))),
            reverse=True,
        )
        right_volatile_races = volatile_tmp[:8]
    except Exception:
        right_volatile_races = []

    mark_timing("build_right_cards")

    right_racing_news = fetch_recent_racing_news(limit=6)
    # 홈 우측에서는 유머 데이터를 렌더링하지 않으므로 기본 비활성화.
    # 필요 시 ENABLE_HUMOR_FEED=true 로 켜서 다시 수집 가능.
    if os.getenv("ENABLE_HUMOR_FEED", "false").lower() == "true":
        right_humor_items = fetch_recent_humor(limit=6)
    else:
        right_humor_items = []
    mark_timing("fetch_news")

    mark_timing("calc_refund_summary")
    mark_timing("aggregate_summary")

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
        "expects_grouped": expects_grouped,
        "funnel_races": funnel_races,
        "funnel_mode": funnel_mode,
        "home_default_city_tab": home_default_city_tab,
        "admin_primary_status_grouped": admin_primary_status_grouped,
        "right_city_top3": right_city_top3,
        "right_city_top3_window_days": right_city_top3_window_days,
        "right_city_top3_future_days": right_city_top3_future_days,
        "right_city_top3_from": right_city_top3_from,
        "right_city_top3_to": right_city_top3_to,
        "right_city_top3_gate_label": right_city_top3_gate_label,
        "right_imminent_races": right_imminent_races,
        "right_hot_races": right_hot_races,
        "right_volatile_races": right_volatile_races,
        "right_racing_news": right_racing_news,
        "right_humor_items": right_humor_items,
        # "t_count": t_count,
        "rdays": rdays,
        "judged_jockey": judged_jockey,
        "changed_race": changed_race,               #출마표 젼경
        "rflag": rflag,  # 경마일, 비경마일 구분
        "view_type": view_type,
    }

    render_cache_key = None
    use_render_cache = request.method == "GET"
    if use_render_cache:
        user_key = f"u{request.user.id}" if request.user.is_authenticated else "anon"
        q_key = (request.GET.get("q") or "").strip()
        view_type_key = (request.GET.get("view_type") or "").strip()
        render_cache_key = f"home:render:v3:{user_key}:{i_rdate}:{q_key}:{view_type_key}"
        cached_render = cache.get(render_cache_key)
        if isinstance(cached_render, dict) and cached_render.get("content") is not None:
            response = HttpResponse(
                cached_render.get("content"),
                content_type=cached_render.get("content_type") or "text/html; charset=utf-8",
            )
            mark_timing("render_template")
        else:
            response = render(request, "base/home.html", context)
            mark_timing("render_template")
            cache.set(
                render_cache_key,
                {
                    "content": bytes(response.content),
                    "content_type": response.get("Content-Type", "text/html; charset=utf-8"),
                },
                HOME_RENDER_CACHE_TTL,
            )
    else:
        response = render(request, "base/home.html", context)
        mark_timing("render_template")

    total_ms = (perf_counter() - t_home_start) * 1000.0
    steps_msg = ", ".join(f"{name}={elapsed:.1f}ms" for name, elapsed in timing_steps)
    race_count = len(race)
    expects_count = len(expects)
    old_template_scan_est = race_count * expects_count
    new_template_scan_est = race_count + expects_count
    scan_reduction = old_template_scan_est - new_template_scan_est
    log_msg = (
        f"[home.timing] total={total_ms:.1f}ms "
        f"rdate={i_rdate} race={race_count} expects={expects_count} "
        f"scan_old_est={old_template_scan_est} scan_new_est={new_template_scan_est} "
        f"scan_reduction_est={scan_reduction} "
        f"steps=[{steps_msg}]"
    )
    if total_ms >= 1200:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    response["X-Home-Total-Ms"] = f"{total_ms:.1f}"
    return response

# @login_required(login_url="home")

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

def pyscriptTest(request):
    pass

    return render(request, "base/pyscript_test.html")

def send_email():
    subject = "message"
    to = ["keombit@gmail.com"]
    from_email = "id@gmail.com"
    message = "메지시 테스트"
    DjangoEmailMessage(subject=subject, body=message, to=to, from_email=from_email).send()


@login_required
def admin_summary_popup(request):
    if not (request.user.username == "admin" or request.user.is_superuser):
        return HttpResponse(status=403)

    q_in_request = (request.GET.get("q", "") or "").strip()
    q = q_in_request
    if not q:
        ref = (request.META.get("HTTP_REFERER", "") or "").strip()
        if ref:
            try:
                ref_q = parse_qs(urlparse(ref).query).get("q", [""])[0]
                q = (ref_q or "").strip()
            except Exception:
                q = ""
    i_rdate = _resolve_home_rdate(q)
    refresh_sec = 30
    try:
        refresh_sec = int(request.GET.get("refresh", "30"))
    except Exception:
        refresh_sec = 30
    refresh_sec = max(10, min(refresh_sec, 300))

    # 새로고침/자동갱신 시 기준일이 흔들리지 않도록 URL을 q 포함 형태로 정규화
    if not q_in_request and len(i_rdate) == 8 and i_rdate.isdigit():
        return redirect(f"{request.path}?q={i_rdate}&refresh={refresh_sec}")

    payload = _build_admin_summary_payload(i_rdate, ADMIN_SUMMARY_MAIN_METHOD_COLUMNS)
    context = {
        **payload,
        "refresh_sec": refresh_sec,
        "fdate": f"{i_rdate[0:4]}-{i_rdate[4:6]}-{i_rdate[6:8]}" if len(i_rdate) == 8 else i_rdate,
        "updated_at": timezone.now(),
        "popup_title": "관리자 요약",
        "show_gate_popup_button": True,
        "gate_popup_button_label": "마번 TOP5",
        "show_special_popup_button": True,
        "enable_method_hit_popup": False,
    }
    return render(request, "base/admin_summary_popup.html", context)


@login_required
def admin_summary_gate_popup(request):
    if not (request.user.username == "admin" or request.user.is_superuser):
        return HttpResponse(status=403)

    q_in_request = (request.GET.get("q", "") or "").strip()
    q = q_in_request
    if not q:
        ref = (request.META.get("HTTP_REFERER", "") or "").strip()
        if ref:
            try:
                ref_q = parse_qs(urlparse(ref).query).get("q", [""])[0]
                q = (ref_q or "").strip()
            except Exception:
                q = ""
    i_rdate = _resolve_home_rdate(q)
    refresh_sec = 30
    try:
        refresh_sec = int(request.GET.get("refresh", "30"))
    except Exception:
        refresh_sec = 30
    refresh_sec = max(10, min(refresh_sec, 300))

    if not q_in_request and len(i_rdate) == 8 and i_rdate.isdigit():
        return redirect(f"{request.path}?q={i_rdate}&refresh={refresh_sec}")

    payload = _build_admin_summary_payload(i_rdate)
    context = {
        "i_rdate": payload.get("i_rdate", i_rdate),
        "gate_top3_by_city": payload.get("gate_top3_by_city", []),
        "gate_top3_period_label": payload.get("gate_top3_period_label", i_rdate),
        "refresh_sec": refresh_sec,
        "fdate": f"{i_rdate[0:4]}-{i_rdate[4:6]}-{i_rdate[6:8]}" if len(i_rdate) == 8 else i_rdate,
        "updated_at": timezone.now(),
    }
    return render(request, "base/admin_summary_gate_popup.html", context)


@login_required
def admin_summary_special_popup(request):
    if not (request.user.username == "admin" or request.user.is_superuser):
        return HttpResponse(status=403)

    q_in_request = (request.GET.get("q", "") or "").strip()
    q = q_in_request
    if not q:
        ref = (request.META.get("HTTP_REFERER", "") or "").strip()
        if ref:
            try:
                ref_q = parse_qs(urlparse(ref).query).get("q", [""])[0]
                q = (ref_q or "").strip()
            except Exception:
                q = ""
    i_rdate = _resolve_home_rdate(q)

    if not q_in_request and len(i_rdate) == 8 and i_rdate.isdigit():
        return redirect(f"{request.path}?q={i_rdate}")

    payload = _build_admin_summary_payload(i_rdate, ADMIN_SUMMARY_SPECIAL_METHOD_COLUMNS)
    context = {
        **payload,
        "fdate": f"{i_rdate[0:4]}-{i_rdate[4:6]}-{i_rdate[6:8]}" if len(i_rdate) == 8 else i_rdate,
        "updated_at": timezone.now(),
        "popup_title": "BOX 요약",
        "show_gate_popup_button": False,
        "gate_popup_button_label": "마번 TOP5",
        "show_special_popup_button": False,
        "enable_method_hit_popup": False,
    }
    return render(request, "base/admin_summary_popup.html", context)


@login_required
def admin_profit_analysis_popup(request):
    if not (request.user.username == "admin" or request.user.is_superuser):
        return HttpResponse(status=403)

    q_in_request = (request.GET.get("q", "") or "").strip()
    q = q_in_request
    if not q:
        ref = (request.META.get("HTTP_REFERER", "") or "").strip()
        if ref:
            try:
                ref_q = parse_qs(urlparse(ref).query).get("q", [""])[0]
                q = (ref_q or "").strip()
            except Exception:
                q = ""
    i_rdate = _resolve_home_rdate(q)

    if not q_in_request and len(i_rdate) == 8 and i_rdate.isdigit():
        return redirect(f"{request.path}?q={i_rdate}")

    payload = _build_admin_profit_analysis_payload(i_rdate)
    context = {
        **payload,
        "fdate": f"{i_rdate[0:4]}-{i_rdate[4:6]}-{i_rdate[6:8]}" if len(i_rdate) == 8 else i_rdate,
        "updated_at": timezone.now(),
        "popup_title": "관리자 수익 분석",
        "show_gate_popup_button": True,
        "gate_popup_button_label": "마번 TOP5",
        "show_special_popup_button": False,
        "enable_method_hit_popup": True,
    }
    return render(request, "base/admin_summary_popup.html", context)


@login_required
def admin_profit_method_hits_popup(request):
    if not (request.user.username == "admin" or request.user.is_superuser):
        return HttpResponse(status=403)

    q_in_request = (request.GET.get("q", "") or "").strip()
    q = q_in_request
    if not q:
        ref = (request.META.get("HTTP_REFERER", "") or "").strip()
        if ref:
            try:
                ref_q = parse_qs(urlparse(ref).query).get("q", [""])[0]
                q = (ref_q or "").strip()
            except Exception:
                q = ""

    i_rdate = _resolve_home_rdate(q)
    strategy_key = (request.GET.get("strategy", "") or "").strip()
    track_name = (request.GET.get("track", "") or "").strip()

    column_meta = ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS.get(strategy_key)
    if not strategy_key or not column_meta:
        return HttpResponse(status=400)

    prep = _prepare_admin_profit_analysis_race_df(i_rdate, bet_unit=100)
    race_df = prep.get("race_df")
    from_date = prep.get("from_date")
    to_date = prep.get("to_date")

    hit_rows = []
    total_hits = 0
    total_refund = 0.0

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        hit_col = column_meta.get("hit")
        refund_col = column_meta.get("refund")
        required_cols = [c for c in [hit_col, refund_col, "경마장", "경주일", "경주번호"] if c]
        if all(col in race_df.columns for col in required_cols):
            target_df = race_df.copy()
            if track_name:
                target_df = target_df[target_df["경마장"].astype(str).str.strip() == track_name]
            target_df = target_df[target_df[hit_col].fillna(0).astype(int) > 0].copy()
            if not target_df.empty:
                total_hits = int(target_df[hit_col].fillna(0).astype(int).sum())
                total_refund = float(target_df[refund_col].fillna(0).sum()) if refund_col in target_df.columns else 0.0

                race_keys = []
                actual_top3_map = {}
                for row_map in target_df.to_dict("records"):
                    race_key = (
                        str(row_map.get("경마장") or "").strip(),
                        str(row_map.get("경주일") or ""),
                        int(row_map.get("경주번호") or 0),
                    )
                    actual_top3_map[race_key] = _parse_gate_list(row_map.get("실제_top3_마번"))[:3]
                    race_keys.append(race_key)

                runner_map = {}
                if race_keys:
                    query = Q()
                    for rcity, rdate, rno in race_keys:
                        query |= Q(rcity=rcity, rdate=rdate, rno=rno, r_rank__lte=3)
                    for rec in Exp011.objects.filter(query).values(
                        "rcity", "rdate", "rno", "gate", "r_rank", "r_pop", "horse", "jockey", "trainer", "host"
                    ):
                        key = (str(rec["rcity"] or "").strip(), str(rec["rdate"] or ""), int(rec["rno"] or 0))
                        gate = int(rec["gate"] or 0)
                        runner_map[(key, gate)] = {
                            "rank": int(rec["r_rank"] or 0),
                            "r_pop": int(rec["r_pop"] or 0) if rec.get("r_pop") is not None else 0,
                            "horse": str(rec["horse"] or "").strip(),
                            "jockey": str(rec["jockey"] or "").strip(),
                            "trainer": str(rec["trainer"] or "").strip(),
                            "host": str(rec["host"] or "").strip(),
                        }

                def _format_top3(value):
                    nums = _parse_gate_list(value)
                    return ",".join(str(x) for x in nums[:3]) if nums else "-"

                strategy_label = ADMIN_PROFIT_STRATEGY_LABELS.get(strategy_key, strategy_key)
                odds_col = "삼복승식배당율" if "삼복" in strategy_label else "삼쌍승식배당율"
                target_df = target_df.sort_values(["경주일", "경주번호"], ascending=[False, True])
                for row_map in target_df.to_dict("records"):
                    race_key = (
                        str(row_map.get("경마장") or "").strip(),
                        str(row_map.get("경주일") or ""),
                        int(row_map.get("경주번호") or 0),
                    )
                    condition_parts = []
                    grade = str(row_map.get("등급") or "").strip()
                    distance = str(row_map.get("경주거리") or "").strip()
                    anchor = str(row_map.get("축마") or "").strip()
                    second_anchor = str(row_map.get("2축마") or "").strip()
                    if grade:
                        condition_parts.append(grade)
                    if distance:
                        condition_parts.append(f"{distance}m")
                    if anchor:
                        condition_parts.append(f"축 {anchor}")
                    if second_anchor:
                        condition_parts.append(f"2축 {second_anchor}")
                    runners = []
                    for idx, gate_no in enumerate(actual_top3_map.get(race_key, []), start=1):
                        runner = runner_map.get((race_key, gate_no), {})
                        horse = runner.get("horse") or "-"
                        jockey = runner.get("jockey") or "-"
                        trainer = runner.get("trainer") or "-"
                        host = runner.get("host") or "-"
                        runners.append(
                            {
                                "rank": idx,
                                "gate": gate_no,
                                "r_pop": runner.get("r_pop") or 0,
                                "horse": horse,
                                "jockey": jockey,
                                "trainer": trainer,
                                "host": host,
                            }
                        )
                    hit_rows.append(
                        {
                            "track": str(row_map.get("경마장") or "").strip() or "-",
                            "rdate": str(row_map.get("경주일") or ""),
                            "rno": int(row_map.get("경주번호") or 0),
                            "actual_top3": _format_top3(row_map.get("실제_top3_마번")),
                            "condition": " · ".join(condition_parts) if condition_parts else "-",
                            "runners": runners,
                            "odds": float(row_map.get(odds_col) or 0.0) if odds_col in row_map else 0.0,
                            "refund": float(row_map.get(refund_col) or 0.0) if refund_col in row_map else 0.0,
                        }
                    )

    context = {
        "i_rdate": i_rdate,
        "from_date": from_date,
        "to_date": to_date,
        "track_name": track_name,
        "strategy_label": ADMIN_PROFIT_STRATEGY_LABELS.get(strategy_key, strategy_key),
        "is_primary_strategy": strategy_key in (ADMIN_PROFIT_GROUPS.get(track_name, {}) or {}).get("주력베팅", []),
        "hit_rows": hit_rows,
        "total_hits": total_hits,
        "total_refund": total_refund,
        "updated_at": timezone.now(),
    }
    return render(request, "base/admin_profit_method_hits_popup.html", context)


@login_required
def admin_profit_method_gates_popup(request):
    if not (request.user.username == "admin" or request.user.is_superuser):
        return HttpResponse(status=403)

    rcity = (request.GET.get("rcity", "") or "").strip()
    rdate = (request.GET.get("rdate", "") or "").strip()
    try:
        rno = int(request.GET.get("rno", "0") or 0)
    except Exception:
        rno = 0

    if not rcity or not rdate or rno <= 0:
        return HttpResponse(status=400)

    prep = _prepare_admin_profit_analysis_race_df(
        rdate,
        bet_unit=ADMIN_PROFIT_TRIFECTA_BET_UNIT,
        trio_bet_unit=ADMIN_PROFIT_TRIO_BET_UNIT,
    )
    race_df = prep.get("race_df")

    race_row = None
    if (
        race_df is not None
        and hasattr(race_df, "columns")
        and not race_df.empty
        and {"경마장", "경주일", "경주번호"}.issubset(race_df.columns)
    ):
        filtered = race_df[
            (race_df["경마장"].astype(str).str.strip() == rcity)
            & (race_df["경주일"].astype(str).str.strip() == rdate)
            & (pd.to_numeric(race_df["경주번호"], errors="coerce").fillna(0).astype(int) == rno)
        ]
        if not filtered.empty:
            race_row = filtered.iloc[0].to_dict()
    if race_row is None:
        race_row = _build_race_row_from_exp011(rcity, rdate, rno)

    method_sections = []
    actual_top3 = "-"
    actual_top3_gates = []
    track_name = rcity
    section_totals = {}

    if race_row:
        track_name = str(race_row.get("경마장") or rcity).strip() or rcity
        actual_top3_values = _parse_gate_list(race_row.get("실제_top3_마번"))
        if actual_top3_values:
            actual_top3_gates = [int(gate) for gate in actual_top3_values[:3]]
            actual_top3 = ", ".join(str(gate) for gate in actual_top3_gates)

        for section_label in ("주력베팅", "보조베팅"):
            methods = []
            for strategy_key in ADMIN_PROFIT_GROUPS.get(track_name, {}).get(section_label, []):
                combo_payload = _build_admin_profit_strategy_combo_payload(race_row, strategy_key)
                if not combo_payload:
                    continue
                column_meta = ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS.get(strategy_key) or {}
                hit_col = column_meta.get("hit")
                bet_col = column_meta.get("bet")
                refund_col = column_meta.get("refund")
                holes_per_race = int(
                    combo_payload.get("holes_per_race")
                    or column_meta.get("holes_per_race")
                    or 0
                )
                bet_type = combo_payload.get("bet_type", "")
                default_bet_unit = (
                    ADMIN_PROFIT_TRIO_BET_UNIT
                    if bet_type == "삼복"
                    else ADMIN_PROFIT_TRIFECTA_BET_UNIT
                )
                raw_bet_amount = float(race_row.get(bet_col) or 0.0) if bet_col else 0.0
                bet_amount = raw_bet_amount if raw_bet_amount > 0 else float(
                    holes_per_race * default_bet_unit
                )
                methods.append(
                    {
                        "strategy_key": strategy_key,
                        "label": ADMIN_PROFIT_STRATEGY_LABELS.get(strategy_key, strategy_key),
                        "anchor_axis": (
                            1
                            if str(ADMIN_PROFIT_STRATEGY_LABELS.get(strategy_key, strategy_key)).strip().startswith("1 /")
                            else 2
                            if str(ADMIN_PROFIT_STRATEGY_LABELS.get(strategy_key, strategy_key)).strip().startswith("2 /")
                            else None
                        ),
                        "holes_per_race": holes_per_race,
                        "groups": combo_payload.get("groups", []),
                        "tickets": combo_payload.get("tickets", []),
                        "bet_type": bet_type,
                        "is_hit": int(race_row.get(hit_col) or 0) > 0 if hit_col else False,
                        "bet_amount": bet_amount,
                        "refund_amount": float(race_row.get(refund_col) or 0.0) if refund_col else 0.0,
                    }
                )
            if methods:
                section_bet_amount = sum(
                    float(method.get("bet_amount") or 0.0) for method in methods
                )
                section_refund_amount = sum(
                    float(method.get("refund_amount") or 0.0) for method in methods
                )
                section_totals[section_label] = {
                    "bet_amount": section_bet_amount,
                    "refund_amount": section_refund_amount,
                }
                methods.sort(key=_admin_method_sort_key)
                method_sections.append(
                    {
                        "label": section_label,
                        "methods": methods,
                    }
                )

    context = {
        "track_name": track_name,
        "rdate": rdate,
        "rno": rno,
        "actual_top3": actual_top3,
        "actual_top3_gates": actual_top3_gates,
        "section_totals": section_totals,
        "method_sections": method_sections,
        "updated_at": timezone.now(),
    }
    return render(request, "base/admin_profit_method_gates_popup.html", context)


@require_http_methods(["GET", "POST"])
def race_comments(request):
    action_map = dict(request.session.get("race_comment_actions", {}))
    authored_ids = set(request.session.get("race_comment_authored_ids", []))

    def serialize_comment(c):
        is_hidden = c.report_count >= 5
        content = "반대 누적으로 숨김 처리된 댓글입니다." if is_hidden else c.content
        is_mine = False
        if request.user.is_authenticated and c.user_id == request.user.id:
            is_mine = True
        elif c.id in authored_ids:
            is_mine = True
        return {
            "id": c.id,
            "nickname": c.nickname,
            "content": content,
            "created": c.created.strftime("%m-%d %H:%M"),
            "like_count": c.like_count,
            "report_count": c.report_count,
            "is_hidden": is_hidden,
            "liked": bool(action_map.get(f"like:{c.id}")),
            "reported": bool(action_map.get(f"report:{c.id}")),
            "is_mine": is_mine,
        }

    if request.method == "GET":
        rcity = (request.GET.get("rcity") or "").strip()
        rdate = (request.GET.get("rdate") or "").strip()
        rno_raw = (request.GET.get("rno") or "").strip()
        if not (rcity and rdate and rno_raw):
            return JsonResponse({"ok": False, "error": "rcity, rdate, rno are required."}, status=400)
        try:
            rno = int(rno_raw)
        except ValueError:
            return JsonResponse({"ok": False, "error": "rno must be integer."}, status=400)

        limit_raw = request.GET.get("limit") or "30"
        try:
            limit = max(1, min(100, int(limit_raw)))
        except ValueError:
            limit = 30

        try:
            qs = RaceComment.objects.filter(rcity=rcity, rdate=rdate, rno=rno)
        except (OperationalError, ProgrammingError):
            return JsonResponse({"ok": False, "error": "댓글 테이블이 준비되지 않았습니다. migrate를 실행하세요."}, status=500)
        count = qs.count()
        comments = [serialize_comment(c) for c in qs.order_by("-created")[:limit]]
        return JsonResponse({"ok": True, "count": count, "comments": comments})

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = {}

    rcity = (payload.get("rcity") or request.POST.get("rcity") or "").strip()
    rdate = (payload.get("rdate") or request.POST.get("rdate") or "").strip()
    rno_raw = str(payload.get("rno") or request.POST.get("rno") or "").strip()
    content = (payload.get("content") or request.POST.get("content") or "").strip()

    if not (rcity and rdate and rno_raw and content):
        return JsonResponse({"ok": False, "error": "rcity, rdate, rno, content are required."}, status=400)
    if len(content) > 300:
        return JsonResponse({"ok": False, "error": "content is too long."}, status=400)
    try:
        rno = int(rno_raw)
    except ValueError:
        return JsonResponse({"ok": False, "error": "rno must be integer."}, status=400)

    if request.user.is_authenticated:
        nickname = request.user.name or request.user.username
        user = request.user
    else:
        nickname = (payload.get("nickname") or request.POST.get("nickname") or "익명").strip()[:50] or "익명"
        user = None

    try:
        item = RaceComment.objects.create(
            rcity=rcity,
            rdate=rdate,
            rno=rno,
            user=user,
            nickname=nickname,
            content=content,
        )
        count = RaceComment.objects.filter(rcity=rcity, rdate=rdate, rno=rno).count()
    except (OperationalError, ProgrammingError):
        return JsonResponse({"ok": False, "error": "댓글 테이블이 준비되지 않았습니다. migrate를 실행하세요."}, status=500)

    authored_set = {int(x) for x in authored_ids if str(x).isdigit()}
    authored_set.add(item.id)
    request.session["race_comment_authored_ids"] = sorted(authored_set)[-500:]
    request.session.modified = True

    return JsonResponse(
        {
            "ok": True,
            "count": count,
            "comment": serialize_comment(item),
        }
    )


@require_http_methods(["POST"])
def race_comment_action(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = {}

    comment_id_raw = str(payload.get("comment_id") or "").strip()
    action = str(payload.get("action") or "").strip().lower()

    if not comment_id_raw or action not in {"like", "report"}:
        return JsonResponse({"ok": False, "error": "comment_id and valid action are required."}, status=400)

    try:
        comment_id = int(comment_id_raw)
    except ValueError:
        return JsonResponse({"ok": False, "error": "comment_id must be integer."}, status=400)

    try:
        comment = RaceComment.objects.get(id=comment_id)
    except RaceComment.DoesNotExist:
        return JsonResponse({"ok": False, "error": "comment not found."}, status=404)
    except (OperationalError, ProgrammingError):
        return JsonResponse({"ok": False, "error": "댓글 테이블이 준비되지 않았습니다. migrate를 실행하세요."}, status=500)

    action_map = request.session.get("race_comment_actions", {})
    action_key = f"{action}:{comment_id}"
    opposite_action = "report" if action == "like" else "like"
    opposite_key = f"{opposite_action}:{comment_id}"

    if action_map.get(opposite_key):
        return JsonResponse(
            {
                "ok": False,
                "error": "같은 댓글에는 좋아요와 반대를 동시에 할 수 없습니다.",
            },
            status=409,
        )

    if action_map.get(action_key):
        return JsonResponse({"ok": False, "error": "이미 처리한 요청입니다."}, status=409)

    if action == "like":
        RaceComment.objects.filter(id=comment_id).update(like_count=F("like_count") + 1)
    else:
        RaceComment.objects.filter(id=comment_id).update(report_count=F("report_count") + 1)

    action_map[action_key] = True
    request.session["race_comment_actions"] = action_map
    request.session.modified = True

    comment.refresh_from_db(fields=["like_count", "report_count"])
    return JsonResponse(
        {
            "ok": True,
            "comment": {
                "id": comment.id,
                "like_count": comment.like_count,
                "report_count": comment.report_count,
                "is_hidden": comment.report_count >= 5,
                "liked": bool(action_map.get(f"like:{comment.id}")),
                "reported": bool(action_map.get(f"report:{comment.id}")),
            },
        }
    )


@require_http_methods(["POST"])
def race_comment_delete(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = {}

    comment_id_raw = str(payload.get("comment_id") or "").strip()
    if not comment_id_raw:
        return JsonResponse({"ok": False, "error": "comment_id is required."}, status=400)

    try:
        comment_id = int(comment_id_raw)
    except ValueError:
        return JsonResponse({"ok": False, "error": "comment_id must be integer."}, status=400)

    try:
        comment = RaceComment.objects.get(id=comment_id)
    except RaceComment.DoesNotExist:
        return JsonResponse({"ok": False, "error": "comment not found."}, status=404)
    except (OperationalError, ProgrammingError):
        return JsonResponse({"ok": False, "error": "댓글 테이블이 준비되지 않았습니다. migrate를 실행하세요."}, status=500)

    authored_ids = {int(x) for x in request.session.get("race_comment_authored_ids", []) if str(x).isdigit()}
    is_owner = False
    if request.user.is_authenticated and comment.user_id == request.user.id:
        is_owner = True
    elif comment.id in authored_ids:
        is_owner = True

    if not is_owner:
        return JsonResponse({"ok": False, "error": "본인이 작성한 댓글만 삭제할 수 있습니다."}, status=403)

    try:
        with transaction.atomic():
            RaceCommentArchive.objects.create(
                rcity=comment.rcity,
                rdate=comment.rdate,
                rno=comment.rno,
                original_comment_id=comment.id,
                user=comment.user,
                nickname=comment.nickname,
                content=comment.content,
                like_count=comment.like_count,
                report_count=comment.report_count,
                original_created=comment.created,
                original_updated=comment.updated,
                archived_reason="self_delete",
                archived_by_user=request.user if request.user.is_authenticated else None,
                archived_by_authenticated=request.user.is_authenticated,
            )
            rcity = comment.rcity
            rdate = comment.rdate
            rno = comment.rno
            comment.delete()

            count = RaceComment.objects.filter(rcity=rcity, rdate=rdate, rno=rno).count()
    except (OperationalError, ProgrammingError):
        return JsonResponse({"ok": False, "error": "댓글 테이블이 준비되지 않았습니다. migrate를 실행하세요."}, status=500)

    action_map = dict(request.session.get("race_comment_actions", {}))
    action_map.pop(f"like:{comment_id}", None)
    action_map.pop(f"report:{comment_id}", None)
    request.session["race_comment_actions"] = action_map

    if comment_id in authored_ids:
        authored_ids.remove(comment_id)
        request.session["race_comment_authored_ids"] = sorted(authored_ids)[-500:]

    request.session.modified = True

    return JsonResponse({"ok": True, "deleted_id": comment_id, "count": count})


@require_http_methods(["POST"])
def race_comment_counts(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = {}

    raw_items = payload.get("items") if isinstance(payload, dict) else []
    if not isinstance(raw_items, list):
        raw_items = []

    keys = []
    key_set = set()
    for item in raw_items[:300]:
        if not isinstance(item, dict):
            continue
        rcity = str(item.get("rcity") or "").strip()
        rdate = str(item.get("rdate") or "").strip()
        rno_raw = str(item.get("rno") or "").strip()
        if not (rcity and rdate and rno_raw):
            continue
        try:
            rno = int(rno_raw)
        except ValueError:
            continue
        key = (rcity, rdate, rno)
        if key in key_set:
            continue
        key_set.add(key)
        keys.append(key)

    if not keys:
        return JsonResponse({"ok": True, "counts": {}})

    key_parts = sorted(f"{k[0]}|{k[1]}|{k[2]}" for k in keys)
    key_raw = ",".join(key_parts)
    key_hash = hashlib.md5(key_raw.encode("utf-8")).hexdigest()
    cache_key = f"home:race_comment_counts:{key_hash}"
    cached_counts = cache.get(cache_key)
    if isinstance(cached_counts, dict):
        return JsonResponse({"ok": True, "counts": cached_counts})

    rcities = {k[0] for k in keys}
    rdates = {k[1] for k in keys}
    rnos = {k[2] for k in keys}
    requested = {f"{k[0]}|{k[1]}|{k[2]}": 0 for k in keys}

    try:
        rows = (
            RaceComment.objects.filter(rcity__in=rcities, rdate__in=rdates, rno__in=rnos)
            .values("rcity", "rdate", "rno")
            .annotate(count=Count("id"))
        )
    except (OperationalError, ProgrammingError):
        return JsonResponse({"ok": False, "error": "댓글 테이블이 준비되지 않았습니다. migrate를 실행하세요."}, status=500)

    for row in rows:
        key = f"{row['rcity']}|{row['rdate']}|{row['rno']}"
        if key in requested:
            requested[key] = row["count"]

    cache.set(cache_key, requested, HOME_COMMENT_COUNT_CACHE_TTL)
    return JsonResponse({"ok": True, "counts": requested})


@require_http_methods(["GET", "POST"])
def race_top5_results(request):
    raw_items = []
    if request.method == "GET":
        items_param = (request.GET.get("items") or "").strip()
        if items_param:
            for chunk in items_param.split(","):
                parts = chunk.split("|")
                if len(parts) != 3:
                    continue
                raw_items.append({"rcity": parts[0], "rdate": parts[1], "rno": parts[2]})
    else:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            payload = {}
        raw_items = payload.get("items") if isinstance(payload, dict) else []

    if not isinstance(raw_items, list):
        raw_items = []

    keys = []
    key_set = set()
    for item in raw_items[:100]:
        if not isinstance(item, dict):
            continue
        rcity = str(item.get("rcity") or "").strip()
        rdate = str(item.get("rdate") or "").strip()
        rno_raw = str(item.get("rno") or "").strip()
        if not (rcity and rdate and rno_raw):
            continue
        try:
            rno = int(rno_raw)
        except ValueError:
            continue
        key = (rcity, rdate, rno)
        if key in key_set:
            continue
        key_set.add(key)
        keys.append(key)

    if not keys:
        return JsonResponse({"ok": True, "results": {}})

    key_parts = sorted(f"{k[0]}|{k[1]}|{k[2]}" for k in keys)
    key_raw = ",".join(key_parts)
    key_hash = hashlib.md5(key_raw.encode("utf-8")).hexdigest()
    cache_key = f"home:race_top5_results:{key_hash}"
    cached_results = cache.get(cache_key)
    if isinstance(cached_results, dict):
        return JsonResponse({"ok": True, "results": cached_results})

    rcities = {k[0] for k in keys}
    rdates = {k[1] for k in keys}
    rnos = {k[2] for k in keys}
    requested = {
        f"{k[0]}|{k[1]}|{k[2]}": {
            "expected_top5": [],
            "actual_top3": [],
            "newbie_count": 0,
        }
        for k in keys
    }

    try:
        rows = (
            Exp011.objects.filter(
                rcity__in=rcities,
                rdate__in=rdates,
                rno__in=rnos,
            )
            .filter(r_pop__gte=1, r_pop__lte=5)
            .values("rcity", "rdate", "rno", "gate", "r_pop")
        )
    except (OperationalError, ProgrammingError):
        return JsonResponse(
            {"ok": False, "error": "경주 결과 테이블이 준비되지 않았습니다."},
            status=500,
        )

    grouped = {
        k: {"pop_rows": [], "actual_rows": [], "newbie_count": 0, "newbie_gates": set()}
        for k in keys
    }
    for row in rows:
        try:
            key = (row["rcity"], row["rdate"], int(row["rno"]))
            if key not in grouped:
                continue
            gate = str(row.get("gate") or "").strip()
            if not gate:
                continue

            r_pop = row.get("r_pop")
            if r_pop is not None:
                try:
                    pop_int = int(r_pop)
                    if 1 <= pop_int <= 5:
                        grouped[key]["pop_rows"].append({"pop": pop_int, "gate": gate})
                except Exception:
                    pass
        except Exception:
            continue

    # race-level 실제 순위 상위 3마번 집계 (r_rank=1,2,3)
    try:
        actual_rows = (
            Exp011.objects.filter(
                rcity__in=rcities,
                rdate__in=rdates,
                rno__in=rnos,
            )
            .filter(r_rank__gte=1, r_rank__lte=3)
            .values("rcity", "rdate", "rno", "gate", "r_rank")
        )
    except (OperationalError, ProgrammingError):
        actual_rows = []

    for row in actual_rows:
        try:
            key = (row["rcity"], row["rdate"], int(row["rno"]))
            if key not in grouped:
                continue
            gate = str(row.get("gate") or "").strip()
            if not gate:
                continue
            r_rank = row.get("r_rank")
            if r_rank is None:
                continue
            try:
                r_rank_int = int(r_rank)
            except Exception:
                continue
            if 1 <= r_rank_int <= 3:
                grouped[key]["actual_rows"].append({"r_rank": r_rank_int, "gate": gate})
        except Exception:
            continue

    # race-level 신마 출주두수 집계 (exp011.rank = 99 기준)
    try:
        newbie_rows = (
            Exp011.objects.filter(
                rcity__in=rcities,
                rdate__in=rdates,
                rno__in=rnos,
            )
            .filter(rank=99)
            .values("rcity", "rdate", "rno", "gate")
        )
    except (OperationalError, ProgrammingError):
        newbie_rows = []

    for row in newbie_rows:
        try:
            key = (row["rcity"], row["rdate"], int(row["rno"]))
            if key not in grouped:
                continue
            gate = str(row.get("gate") or "").strip()
            if gate:
                grouped[key]["newbie_gates"].add(gate)
        except Exception:
            continue

    for key in keys:
        pop_rows = grouped[key]["pop_rows"]
        expected_rows = []
        for row in pop_rows:
            try:
                pop_int = int(row.get("pop") or 0)
            except Exception:
                continue
            gate = str(row.get("gate") or "").strip()
            if not gate or pop_int < 1 or pop_int > 5:
                continue
            expected_rows.append({"pop": pop_int, "gate": gate})

        expected_rows.sort(key=lambda x: (x["pop"], x["gate"]))
        expected_top5 = []
        expected_seen_gate = set()
        for row in expected_rows:
            gate = row["gate"]
            if gate in expected_seen_gate:
                continue
            expected_seen_gate.add(gate)
            expected_top5.append(row)
            if len(expected_top5) >= 5:
                break

        actual_rows = grouped[key]["actual_rows"]
        actual_rows.sort(key=lambda x: (x["r_rank"], x["gate"]))
        actual_top3 = []
        actual_seen_gate = set()
        for row in actual_rows:
            gate = row["gate"]
            if gate in actual_seen_gate:
                continue
            actual_seen_gate.add(gate)
            actual_top3.append(row)
            if len(actual_top3) >= 3:
                break

        key_str = f"{key[0]}|{key[1]}|{key[2]}"
        newbie_gates = grouped[key].get("newbie_gates") or set()
        newbie_count = len(newbie_gates)
        requested[key_str] = {
            "expected_top5": expected_top5,
            "actual_top3": actual_top3,
            "newbie_count": newbie_count,
        }
        if settings.DEBUG and HOME_TOP5_DEBUG:
            try:
                gates_sorted = sorted(newbie_gates, key=lambda x: int(x))
            except Exception:
                gates_sorted = sorted(newbie_gates)
            logger.debug(
                f"[top5] newbie key={key_str} count={newbie_count} gates={gates_sorted}"
            )

    cache.set(cache_key, requested, HOME_TOP5_CACHE_TTL)
    return JsonResponse({"ok": True, "results": requested})


def inquiry(request):
    wants_json = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("accept") or "")
        or (request.POST.get("response_format") == "json")
    )
    form_data = {"name": "", "email": "", "message": ""}
    errors = []
    submitted = False

    if request.method == "POST":
        form_data = {
            "name": (request.POST.get("name") or "").strip(),
            "email": (request.POST.get("email") or "").strip(),
            "message": (request.POST.get("message") or "").strip(),
        }

        if not form_data["name"]:
            errors.append("이름(별칭)을 입력해주세요.")
        if not form_data["email"]:
            errors.append("이메일을 입력해주세요.")
        else:
            try:
                validate_email(form_data["email"])
            except ValidationError:
                errors.append("유효한 이메일 형식이 아닙니다.")
        if not form_data["message"]:
            errors.append("문의 내용을 입력해주세요.")

        if not errors:
            subject = f"[thethe9 문의] {form_data['name']}"
            body = (
                f"이름(별칭): {form_data['name']}\n"
                f"이메일: {form_data['email']}\n"
                "\n"
                f"[문의 내용]\n{form_data['message']}\n"
            )
            to_email = getattr(settings, "INQUIRY_TO", settings.EMAIL_HOST_USER)
            try:
                mail = DjangoEmailMessage(
                    subject=subject,
                    body=body,
                    to=[to_email],
                    reply_to=[form_data["email"]],
                    from_email=settings.DEFAULT_FROM_EMAIL,
                )
                sent_count = mail.send(fail_silently=False)
                if sent_count < 1:
                    print(
                        f"[inquiry] send_count=0 "
                        f"from={settings.DEFAULT_FROM_EMAIL} to={to_email} reply_to={form_data['email']}"
                    )
                    errors.append("메일 서버가 전송을 수락하지 않았습니다. 잠시 후 다시 시도해주세요.")
                else:
                    print(
                        f"[inquiry] sent "
                        f"from={settings.DEFAULT_FROM_EMAIL} to={to_email} reply_to={form_data['email']}"
                    )
                    submitted = True
                    form_data = {"name": "", "email": "", "message": ""}
            except smtplib.SMTPAuthenticationError as exc:
                print(f"[inquiry] SMTP auth error: {exc}")
                errors.append("메일 계정 인증에 실패했습니다. 관리자에게 SMTP 설정을 확인해달라고 요청해주세요.")
            except smtplib.SMTPConnectError as exc:
                print(f"[inquiry] SMTP connect error: {exc}")
                errors.append("메일 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.")
            except smtplib.SMTPException as exc:
                print(f"[inquiry] SMTP error: {exc}")
                errors.append("메일 서버 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            except Exception as exc:
                print(f"[inquiry] Unexpected error: {type(exc).__name__}: {exc}")
                errors.append("메일 전송에 실패했습니다. 잠시 후 다시 시도해주세요.")

        if wants_json:
            return JsonResponse(
                {
                    "ok": submitted and not errors,
                    "submitted": submitted,
                    "errors": errors,
                }
            )

    context = {
        "form_data": form_data,
        "errors": errors,
        "submitted": submitted,
    }
    return render(request, "base/inquiry.html", context)


# backward-compatible alias
def partnership_inquiry(request):
    return inquiry(request)


def terms_of_service(request):
    return render(request, "base/terms_of_service.html")


def privacy_policy(request):
    return render(request, "base/privacy_policy.html")


def comment_policy(request):
    return render(request, "base/comment_policy.html")
# 주별 입상마 경주전개 현황


def error_400(request, exception):
    return render(request, "errors/400.html", status=400)


def error_403(request, exception):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
