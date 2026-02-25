from apps.common import *
import json
import logging
import copy
from time import perf_counter
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage as DjangoEmailMessage
from django.core.cache import cache
from django.http import JsonResponse
from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Count, F, Max, Q
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from base.models import RaceComment, RaceCommentArchive
import smtplib
import re
from urllib.request import Request, urlopen
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET
from html import unescape

logger = logging.getLogger(__name__)


def _env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return int(default)


HOME_DEFAULT_RDATE_CACHE_TTL = _env_int("HOME_DEFAULT_RDATE_CACHE_TTL", 120)
HOME_RACE_CACHE_TTL = _env_int("HOME_RACE_CACHE_TTL", 30)
HOME_NEWS_CACHE_TTL = _env_int("HOME_NEWS_CACHE_TTL", 1800)
HOME_NEWS_STALE_TTL = _env_int("HOME_NEWS_STALE_TTL", 21600)
HOME_NEWS_TIMEOUT_SEC = float(os.getenv("HOME_NEWS_TIMEOUT_SEC", "1.6"))


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

    # expects Query
    cursor = None
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

    except Exception as exc:
        # connection.rollback()
        print(f"Failed selecting in expect: {exc}")
    finally:
        if cursor:
            cursor.close()
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

    if upcoming_candidates:
        upcoming_candidates.sort(key=lambda x: (x[0], x[2]))
        funnel_races = [row for _, _, _, row in upcoming_candidates[:3]]
        funnel_mode = "imminent"
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

    # home_right 상단 카드: 경마장별 성적 우수 Top3 (마번/기수/마방)
    # 기준 기간: i_rdate -14일 ~ i_rdate +3일
    right_city_top3_window_days = 16
    right_city_top3_future_days = 3
    perf_rows = []
    perf_cache_key = f"home:top3_perf:{i_rdate}:{right_city_top3_window_days}:{right_city_top3_future_days}"
    cached_perf_rows = _cache_copy_get(perf_cache_key)
    if cached_perf_rows is not None:
        perf_rows = cached_perf_rows
    else:
        cursor = None
        try:
            cursor = connection.cursor()
            str_sql = """
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
                str_sql,
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

    # 최근 14일 데이터가 비어 있으면 기존 expects(±3~4일)로 fallback
    if not perf_rows:
        perf_rows = expects

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
            _acc_perf(city_bucket["gate"], e_gate, rank_int)
            _acc_perf(city_bucket["jockey"], e_jockey, rank_int)
            _acc_perf(city_bucket["trainer"], e_trainer, rank_int)
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
        return rows[:3]

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

    try:
        check_visit(request)
    except Exception as exc:
        print(f"check_visit failed: {exc}")

    race_df = None
    summary = {}
    from_date = None
    to_date = None
    if request.user.is_authenticated and request.user.username == "admin":
        base_dt = datetime.strptime(i_rdate, "%Y%m%d")
        from_date = (base_dt - timedelta(days=3)).strftime("%Y%m%d")
        to_date = (base_dt + timedelta(days=4)).strftime("%Y%m%d")
        try:
            race_df, summary = calc_rpop_anchor_26_trifecta(
                from_date=from_date,
                to_date=to_date,
                bet_unit=100,
            )
        except Exception as exc:
            print(f"[rpop2] calc failed: {exc}")
    mark_timing("calc_refund_summary")
    
    
    
    if from_date and to_date:
        try:
            summary_keys = list(summary.keys()) if isinstance(summary, dict) else []
            race_rows = len(race_df) if race_df is not None else 0
            day_summary_len = (
                len(summary.get("day_summary", {})) if isinstance(summary, dict) else 0
            )
            print(
                "[rpop2] from_date=%s to_date=%s summary_type=%s summary_keys=%s "
                "race_rows=%s day_summary_len=%s"
                % (
                    from_date,
                    to_date,
                    type(summary).__name__,
                    summary_keys,
                    race_rows,
                    day_summary_len,
                )
            )
        except Exception as exc:
            print(f"[rpop2] debug failed: {exc}")

    summary_display = []
    summary_total = None
    method_bet_totals = []
    method_bet_total_sum = 0.0
    method_refund_total_sum = 0.0
    method_profit_total_sum = 0.0

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        method_columns = [
            ("1축 2~4 5~7", "1축_2~4_5~7_베팅액", "1축_2~4_5~7_환수액"),
            ("1축 2~4", "1축_2~4_베팅액", "1축_2~4_환수액"),
            ("1축 2~6 삼복", "1축_2~6_삼복_베팅액", "1축_2~6_삼복_환수액"),
            ("1~2복조 3~8 삼복", "1~2복조_3~8_삼복_베팅액", "1~2복조_3~8_삼복_환수액"),
            ("BOX4 삼복", "BOX4_삼복_베팅액", "BOX4_삼복_환수액"),
        ]
        for label, bet_col, refund_col in method_columns:
            if bet_col in race_df.columns and refund_col in race_df.columns:
                bet_amount = float(race_df[bet_col].fillna(0).sum())
                refund_amount = float(race_df[refund_col].fillna(0).sum())
                profit_amount = refund_amount - bet_amount
                method_bet_totals.append(
                    {
                        "label": label,
                        "amount": bet_amount,
                        "refund": refund_amount,
                        "profit": profit_amount,
                    }
                )
                method_bet_total_sum += bet_amount
                method_refund_total_sum += refund_amount
                method_profit_total_sum += profit_amount

    if isinstance(summary, dict):
        day_summary = summary.get("day_summary", {})
        track_summary = summary.get("track_summary", {})
        day_hit_summary = summary.get("day_hit_summary", {})
        track_hit_summary = summary.get("track_hit_summary", {})
        use_track = bool(track_summary)
        summary_source = track_summary if use_track else day_summary
        hit_source = track_hit_summary if use_track else day_hit_summary
        total_races = 0
        total_bet = 0.0
        total_refund = 0.0
        total_hits = 0
        total_r_pop1_top3_hits = 0
        for key in sorted(summary_source.keys()):
            d = summary_source[key]
            hits_detail = hit_source.get(key, [])
            refund_rate = (
                d["total_refund"] / d["total_bet"] if d["total_bet"] > 0 else 0.0
            )
            hit_rate = d["hits"] / d["races"] if d["races"] > 0 else 0.0
            profit = d["total_refund"] - d["total_bet"]
            avg_bet = d["total_bet"] / d["races"] if d["races"] > 0 else 0.0
            summary_display.append(
                {
                    "label": key,
                    "races": d["races"],
                    "refund_rate": refund_rate,
                    "total_bet": d["total_bet"],
                    "total_refund": d["total_refund"],
                    "profit": profit,
                    "hits": d["hits"],
                    "hit_rate": hit_rate,
                    "avg_bet": avg_bet,
                    "hit_details": hits_detail,
                }
            )
            total_races += d["races"]
            total_bet += d["total_bet"]
            total_refund += d["total_refund"]
            total_hits += d["hits"]
            total_r_pop1_top3_hits += d.get("r_pop1_top3_hits", 0)
        if total_races > 0:
            total_profit = total_refund - total_bet
            total_refund_rate = total_refund / total_bet if total_bet > 0 else 0.0
            total_hit_rate = total_hits / total_races if total_races > 0 else 0.0
            total_avg_bet = total_bet / total_races if total_races > 0 else 0.0
            total_r_pop1_top3_rate = (
                total_r_pop1_top3_hits / total_races if total_races > 0 else 0.0
            )
            summary_total = {
                "races": total_races,
                "total_bet": total_bet,
                "total_refund": total_refund,
                "profit": total_profit,
                "hits": total_hits,
                "hit_rate": total_hit_rate,
                "r_pop1_top3_hits": total_r_pop1_top3_hits,
                "r_pop1_top3_rate": total_r_pop1_top3_rate,
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
                "r_pop1_top3_hits": 0,
                "r_pop1_top3_rate": 0.0,
                "refund_rate": 0.0,
                "avg_bet": 0.0,
            }
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
        "right_city_top3": right_city_top3,
        "right_city_top3_window_days": right_city_top3_window_days,
        "right_city_top3_future_days": right_city_top3_future_days,
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
        "summary": summary,
        "summary_display": summary_display,
        "summary_total": summary_total,
        "method_bet_totals": method_bet_totals,
        "method_bet_total_sum": method_bet_total_sum,
        "method_refund_total_sum": method_refund_total_sum,
        "method_profit_total_sum": method_profit_total_sum,

    }

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

    return JsonResponse({"ok": True, "counts": requested})


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
