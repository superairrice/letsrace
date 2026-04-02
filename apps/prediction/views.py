from apps.common import *
import re
import threading
import time
import traceback
import uuid
from contextlib import redirect_stderr, redirect_stdout
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlencode

import requests
from django.http import JsonResponse
from django.core.cache import cache
from apps.domains.race.race import resultOfRace
from django.db import close_old_connections
from apps.domains.ops.kra_change_sync import (
    KRA_CHANGE_PRESETS as SERVICE_KRA_CHANGE_PRESETS,
    sync_latest_kra_change_entries,
)

# Prediction views
RACE_PREDICTION_CACHE_TTL = 30


KRA_SCRAPER_PRESETS = {
    "change": {
        "label": "KRA 출전표 변경",
        "url": "https://race.kra.co.kr/thisweekrace/ThisWeekChulmapyoChange.do",
    },
    "weight": {
        "label": "KRA 출주마 체중",
        "url": "https://race.kra.co.kr/thisweekrace/ThisWeekWeight.do",
    },
    "score": {
        "label": "KRA 요약성적표",
        "url": "https://race.kra.co.kr/thisweekrace/ThisWeekScoretableDailyScoretable.do",
    },
}


def _strip_html_to_text(raw_html):
    text = raw_html or ""
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?i)<br\\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>|</div>|</li>|</tr>|</td>|</th>|</h[1-6]>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_kra_scrape_url(preset_key, custom_url):
    custom_url = (custom_url or "").strip()
    if custom_url:
        return custom_url

    preset = KRA_SCRAPER_PRESETS.get(preset_key) or KRA_SCRAPER_PRESETS["change"]
    return preset["url"]


class _SimpleHtmlTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._table = None
        self._row = None
        self._cell = None
        self._cell_tag = None
        self._capture_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self._table = {"rows": []}
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            attr_map = dict(attrs)
            self._cell_tag = tag
            self._cell = {
                "text": "",
                "is_header": tag == "th",
                "colspan": int(attr_map.get("colspan", "1") or "1"),
                "rowspan": int(attr_map.get("rowspan", "1") or "1"),
            }
            self._capture_depth = 1
        elif self._cell is not None:
            if tag == "br":
                self._cell["text"] += "\n"
            else:
                self._capture_depth += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "table":
            if self._table and self._table["rows"]:
                self.tables.append(self._table)
            self._table = None
        elif tag == "tr":
            if self._table is not None and self._row:
                self._table["rows"].append(self._row)
            self._row = None
        elif tag in {"th", "td"}:
            if self._row is not None and self._cell is not None:
                self._cell["text"] = re.sub(r"\s*\n\s*", "\n", self._cell["text"]).strip()
                self._row.append(self._cell)
            self._cell = None
            self._cell_tag = None
            self._capture_depth = 0
        elif self._cell is not None and self._capture_depth > 0:
            self._capture_depth -= 1

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"] += data


def _parse_html_tables(raw_html):
    parser = _SimpleHtmlTableParser()
    parser.feed(raw_html or "")
    parsed_tables = []
    for index, table in enumerate(parser.tables, start=1):
        rows = [row for row in table["rows"] if any((cell.get("text") or "").strip() for cell in row)]
        if not rows:
            continue
        header_row = None
        body_rows = rows
        if rows and all(cell.get("is_header") for cell in rows[0]):
            header_row = rows[0]
            body_rows = rows[1:]
        parsed_tables.append(
            {
                "index": index,
                "headers": header_row or [],
                "rows": body_rows,
            }
        )
    return parsed_tables


def _normalize_kra_header(text):
    return re.sub(r"[\s\n\r\t()\-_/]", "", (text or "").strip()).lower()


def _match_header_index(headers, candidates):
    normalized = [_normalize_kra_header(h.get("text", "")) for h in headers]
    candidate_keys = [_normalize_kra_header(c) for c in candidates]
    for idx, header in enumerate(normalized):
        if any(key and key in header for key in candidate_keys):
            return idx
    return -1


def _table_row_to_cells(row):
    return [str(cell.get("text", "") or "").strip() for cell in row]


def _extract_cancel_content_from_tables(scraped_tables):
    lines = []
    for table in scraped_tables or []:
        headers = table.get("headers") or []
        if not headers:
            continue
        idx_date = _match_header_index(headers, ["일자", "경주일", "시행일자"])
        idx_rno = _match_header_index(headers, ["경주번호", "경주"])
        idx_horse = _match_header_index(headers, ["마명", "경주마"])
        idx_reason = _match_header_index(headers, ["사유", "변경사유", "취소사유"])
        if min(idx_date, idx_rno, idx_horse, idx_reason) < 0:
            continue

        for row in table.get("rows") or []:
            cells = _table_row_to_cells(row)
            if max(idx_date, idx_rno, idx_horse, idx_reason) >= len(cells):
                continue
            date_text = cells[idx_date]
            horse_text = cells[idx_horse]
            if not date_text or not horse_text:
                continue
            line_items = [
                "취소",
                date_text,
                cells[idx_rno],
                "",
                horse_text,
                "",
                "",
                cells[idx_reason],
            ]
            lines.append("\t".join(line_items))
    return "\n".join(lines)


def _extract_jockey_change_content_from_tables(scraped_tables):
    lines = []
    for table in scraped_tables or []:
        headers = table.get("headers") or []
        if not headers:
            continue
        idx_date = _match_header_index(headers, ["일자", "경주일", "시행일자"])
        idx_rno = _match_header_index(headers, ["경주번호", "경주"])
        idx_horse = _match_header_index(headers, ["마명", "경주마"])
        idx_old_jockey = _match_header_index(headers, ["기수", "변경전기수", "당초기수"])
        idx_old_handy = _match_header_index(headers, ["부담중량", "변경전부담중량", "당초부담중량"])
        idx_new_jockey = _match_header_index(headers, ["변경기수", "변경후기수", "기수변경"])
        idx_new_handy = _match_header_index(headers, ["변경후부담중량", "변경부담중량", "신부담중량"])
        idx_reason = _match_header_index(headers, ["사유", "변경사유"])
        if min(idx_date, idx_rno, idx_horse, idx_old_jockey, idx_old_handy, idx_new_jockey, idx_new_handy, idx_reason) < 0:
            continue

        for row in table.get("rows") or []:
            cells = _table_row_to_cells(row)
            if max(idx_date, idx_rno, idx_horse, idx_old_jockey, idx_old_handy, idx_new_jockey, idx_new_handy, idx_reason) >= len(cells):
                continue
            date_text = cells[idx_date]
            horse_text = cells[idx_horse]
            if not date_text or not horse_text:
                continue
            line_items = [
                date_text,
                cells[idx_rno],
                "",
                horse_text,
                cells[idx_old_jockey],
                cells[idx_old_handy],
                cells[idx_new_jockey],
                cells[idx_new_handy],
                cells[idx_reason],
            ]
            lines.append("\t".join(line_items))
    return "\n".join(lines)

def racePrediction(request, rcity, rdate, rno, hname, awardee):

    view_type = (
        request.GET.get("view_type") if request.GET.get("view_type") != None else ""
    )  # 정렬방식

    base_qs = Exp011.objects.filter(rcity=rcity, rdate=rdate, rno=rno)
    if view_type == "1":
        exp011s = list(base_qs.order_by("rank", "gate"))
    else:
        exp011s = list(base_qs.order_by("r_pop", "gate"))
        
    compare_r = base_qs.aggregate(
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

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).first()
    if r_condition is None:
        return render(request, "base/home.html")

    cache_prefix = f"race_prediction:{rcity}:{rdate}:{rno}"

    hr_records = cache.get(f"{cache_prefix}:hr_records")
    if hr_records is None:
        hr_records = recordsByHorse(rcity, rdate, rno, "None")
        cache.set(f"{cache_prefix}:hr_records", hr_records, RACE_PREDICTION_CACHE_TTL)
    # print(hr_records)

    try:
        alloc = Rec010.objects.get(rcity=rcity, rdate=rdate, rno=rno)
    except:
        alloc = None

    # paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
    # paternal_dist = get_paternal_dist(rcity, rdate, rno)  # 부마 거리별 3착 성적

    loadin = cache.get(f"{cache_prefix}:loadin")
    if loadin is None:
        loadin = get_loadin(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:loadin", loadin, RACE_PREDICTION_CACHE_TTL)

    disease = cache.get(f"{cache_prefix}:disease")
    if disease is None:
        disease = get_disease(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:disease", disease, RACE_PREDICTION_CACHE_TTL)
    disease = disease or []

    trainer_training = cache.get(f"{cache_prefix}:trainer_training")
    if trainer_training is None:
        trainer_training = get_trainer_double_check(rcity, rdate, rno)
        cache.set(
            f"{cache_prefix}:trainer_training",
            trainer_training,
            RACE_PREDICTION_CACHE_TTL,
        )
    trainer_double_check, training_cnt = trainer_training

    judged_data = cache.get(f"{cache_prefix}:judged")
    if judged_data is None:
        judged_data = get_judged(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:judged", judged_data, RACE_PREDICTION_CACHE_TTL)
    judged_list, judged = judged_data

    loadin = loadin or []
    trainer_double_check = trainer_double_check or []
    training_cnt = training_cnt or []
    judged_list = judged_list or []
    judged = judged or []

    # # # axis = get_axis(rcity, rdate, rno)
    # axis1 = get_axis_rank(rcity, rdate, rno, 1)
    # axis2 = get_axis_rank(rcity, rdate, rno, 2)
    # axis3 = get_axis_rank(rcity, rdate, rno, 3)

    track = cache.get(f"{cache_prefix}:track")
    if track is None:
        track = get_track_record(
            rcity, rdate, rno
        )  # 경주거리별 등급별 평균기록, 최고기록, 최저기록
        cache.set(f"{cache_prefix}:track", track, RACE_PREDICTION_CACHE_TTL)

    # 경주 메모 Query
    r_memo = cache.get(f"{cache_prefix}:r_memo")
    if r_memo is None:
        r_memo = []
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
        cache.set(f"{cache_prefix}:r_memo", r_memo, RACE_PREDICTION_CACHE_TTL)

    # 경주일 - 출주정보
    weeksrace = cache.get(f"race_prediction:weeksrace:{rdate}")
    if weeksrace is None:
        weeksrace = []
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
        cache.set(
            f"race_prediction:weeksrace:{rdate}",
            weeksrace,
            RACE_PREDICTION_CACHE_TTL,
        )

    memo_map = {horse: (memo, flag, judge) for horse, memo, flag, judge in r_memo}
    loadin_map = {jname: (load_in, tot_1st) for jname, load_in, tot_1st in loadin}
    training_cnt_map = {jockey: cnt for jockey, cnt in training_cnt}
    disease_map = {horse: (max_date, cnt) for horse, max_date, cnt in disease}
    for row in exp011s:
        memo_data = memo_map.get(row.horse, (None, None, None))
        row.r_etc = memo_data[0]
        row.r_flag = memo_data[1]
        row.judge = memo_data[2]
        row.load_in = loadin_map.get(row.jockey, (None, None))[0]
        row.training_cnt = training_cnt_map.get(row.jockey)
        row.disease_cnt = disease_map.get(row.horse, (None, None))[1]

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)


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


# Race views

# 마방 경주마 보유현황

def printPrediction(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""

    if q == "":
        rdate = Racing.objects.values("rdate").distinct()[0]["rdate"]  # 초기값은 금요일
        fdate = rdate[0:4] + "-" + rdate[4:6] + "-" + rdate[6:8]

    else:
        rdate = q[0:4] + q[5:7] + q[8:10]
        fdate = q

    rcity = request.GET.get("rcity") if request.GET.get("rcity") != None else "부산"
    view_type = request.GET.get("view_type") if request.GET.get("view_type") != None else "2"
    if view_type not in ("1", "2"):
        view_type = "2"

    race, expects = get_print_prediction(rcity, rdate, view_type=view_type)


    if race:
        context = {
            "expects": expects,
            "race": race,
            "fdate": fdate,
            "view_type": view_type,
        }
    else:
        messages.warning(request, fdate + " " + rcity + " 경마 데이터가 없습니다.")
        context = {
            "expects": expects,
            "race": race,
            "fdate": fdate,
            "view_type": view_type,
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


def raceResult(request, rcity, rdate, rno, hname, rcity1, rdate1, rno1):
    # records = RecordS.objects.filter(rcity=rcity, rdate=rdate, rno=rno).order_by(
    #     "rank", "gate"
    # )
    cache_prefix = f"race_result:{rcity}:{rdate}:{rno}"

    records = cache.get(f"{cache_prefix}:records")
    if records is None:
        records = resultOfRace(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:records", records, RACE_PREDICTION_CACHE_TTL)
    if not records:
        return render(request, "base/home.html")

    # r_condition = Rec010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    r_condition = Rec010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).first()
    if r_condition is None:
        return render(request, "base/home.html")

    # rdate_1year = (
    #     str(int(rdate[0:4]) - 1) + rdate[4:8]
    # )  # 최근 1년 경주성적 조회조건 추가

    # hr_records = RecordS.objects.filter(
    #     rdate__lt=rdate, horse__in=records.values("horse")
    # ).order_by("horse", "-rdate")

    hr_records = cache.get(f"{cache_prefix}:hr_records")
    if hr_records is None:
        hr_records = recordsByHorse(rcity, rdate, rno, "None")
        cache.set(f"{cache_prefix}:hr_records", hr_records, RACE_PREDICTION_CACHE_TTL)

    compare_r = cache.get(f"{cache_prefix}:compare_r")
    if compare_r is None:
        compare_r = Rec011.objects.filter(rcity=rcity, rdate=rdate, rno=rno).aggregate(
        compare_i_s1f__min=Min("i_s1f"),
        compare_i_g1f__min=Min("i_g1f"),
        compare_i_g2f__min=Min("i_g2f"),
        compare_i_g3f__min=Min("i_g3f"),
        compare_handycap__max=Max("handycap"),
        compare_rating__max=Max("rating"),
        )
        cache.set(f"{cache_prefix}:compare_r", compare_r, RACE_PREDICTION_CACHE_TTL)

    # rec011 모델에 없는 필드(recent3/recent5/convert_r)는 resultOfRace 튜플에서 직접 산출
    def _min_tuple_value(rows, idx):
        vals = []
        for row in rows or []:
            if len(row) <= idx:
                continue
            v = row[idx]
            if v is None:
                continue
            s = str(v).strip()
            if not s:
                continue
            vals.append(s)
        return min(vals) if vals else None

    # race_result.html의 records 튜플 인덱스 기준
    # recent3:74, recent5:75, convert_r:79
    compare_r["compare_recent3__min"] = _min_tuple_value(records, 74)
    compare_r["compare_recent5__min"] = _min_tuple_value(records, 75)
    compare_r["compare_convert_r__min"] = _min_tuple_value(records, 79)

    judged_data = cache.get(f"{cache_prefix}:judged")
    if judged_data is None:
        judged_data = get_judged(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:judged", judged_data, RACE_PREDICTION_CACHE_TTL)
    judged_list, judged = judged_data

    track = cache.get(f"{cache_prefix}:track")
    if track is None:
        track = get_track_record(rcity, rdate, rno)  # 경주 등급 평균
        cache.set(f"{cache_prefix}:track", track, RACE_PREDICTION_CACHE_TTL)

    trainer_training = cache.get(f"{cache_prefix}:trainer_training")
    if trainer_training is None:
        trainer_training = get_trainer_double_check(rcity, rdate, rno)
        cache.set(
            f"{cache_prefix}:trainer_training",
            trainer_training,
            RACE_PREDICTION_CACHE_TTL,
        )
    trainer_double_check, training_cnt = trainer_training

    disease = cache.get(f"{cache_prefix}:disease")
    if disease is None:
        disease = get_disease(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:disease", disease, RACE_PREDICTION_CACHE_TTL)
    disease = disease or []

    trainer_double_check = trainer_double_check or []
    training_cnt = training_cnt or []
    judged_list = judged_list or []
    judged = judged or []

    # if len(judged) > 0:
    #     judged = judged[0][0]

    horse_set = cache.get(f"race_result:{rcity1}:{rdate1}:{rno1}:horse_set")
    if horse_set is None:
        horse_set = set(
            Exp011.objects.filter(rcity=rcity1, rdate=rdate1, rno=rno1).values_list(
                "horse", flat=True
            )
        )
        cache.set(
            f"race_result:{rcity1}:{rdate1}:{rno1}:horse_set",
            horse_set,
            RACE_PREDICTION_CACHE_TTL,
        )

    alloc = r_condition

    weeksrace = []
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

    training_cnt_map = {jname: cnt for jname, cnt in training_cnt}
    disease_map = {hname: cnt for hname, _max_date, cnt in disease}

    recovery_cnt, start_cnt, audit_cnt = countOfRace(rcity, rdate, rno)

    context = {
        "records": records,
        "r_condition": r_condition,
        "hr_records": hr_records,
        "compare_r": compare_r,
        "hname": hname,
        "judged_list": judged_list,
        "judged": " ".join(str(item) for sublist in judged for item in sublist),
        "horse_set": horse_set,
        "alloc": alloc,
        "weeksrace": weeksrace,
        "track": track,
        "trainer_double_check": trainer_double_check,
        "training_cnt": training_cnt,
        "training_cnt_map": training_cnt_map,
        "disease": disease,
        "disease_map": disease_map,
        "recovery_cnt": recovery_cnt,
        "start_cnt": start_cnt,
        "audit_cnt": audit_cnt,
        **compare_r,
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
    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).first()
    if r_condition is None:
        return render(request, "base/home.html")

    cache_prefix = f"race_related:{rcity}:{rdate}:{rno}"

    race_related_data = cache.get(f"{cache_prefix}:race_related_data")
    if race_related_data is None:
        race_related_data = get_race_related(rcity, rdate, rno)
        cache.set(
            f"{cache_prefix}:race_related_data",
            race_related_data,
            RACE_PREDICTION_CACHE_TTL,
        )
    if not race_related_data or len(race_related_data) != 4:
        award_j, award_t, award_h, race_detail = [], [], [], []
    else:
        award_j, award_t, award_h, race_detail = race_related_data

    loadin = cache.get(f"{cache_prefix}:loadin")
    if loadin is None:
        loadin = get_loadin(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:loadin", loadin, RACE_PREDICTION_CACHE_TTL)

    judged_jockey = cache.get(f"{cache_prefix}:judged_jockey")
    if judged_jockey is None:
        judged_jockey = get_judged_jockey(rcity, rdate, rno)
        cache.set(
            f"{cache_prefix}:judged_jockey",
            judged_jockey,
            RACE_PREDICTION_CACHE_TTL,
        )

    trainer_training = cache.get(f"{cache_prefix}:trainer_training")
    if trainer_training is None:
        trainer_training = get_trainer_double_check(rcity, rdate, rno)
        cache.set(
            f"{cache_prefix}:trainer_training",
            trainer_training,
            RACE_PREDICTION_CACHE_TTL,
        )
    trainer_double_check, training_cnt = trainer_training

    award_j = award_j or []
    award_t = award_t or []
    award_h = award_h or []
    race_detail = race_detail or []
    loadin = loadin or []
    judged_jockey = judged_jockey or []
    trainer_double_check = trainer_double_check or []
    training_cnt = training_cnt or []
    loadin_map = {jname: load_in for jname, load_in, _tot_1st in loadin}

    # race_detail 튜플 인덱스: 12=j_name, 13=t_name, 14=h_name
    race_detail_by_jockey = {}
    race_detail_by_trainer = {}
    race_detail_by_host = {}
    for row in race_detail:
        try:
            j_name = row[12]
            t_name = row[13]
            h_name = row[14]
            race_detail_by_jockey.setdefault(j_name, []).append(row)
            race_detail_by_trainer.setdefault(t_name, []).append(row)
            race_detail_by_host.setdefault(h_name, []).append(row)
        except Exception:
            continue


    context = {
        "r_condition": r_condition,  # 기수 기승가능 부딤중량
        "loadin": loadin,  # 기수 기승가능 부딤중량
        "judged_jockey": judged_jockey,
        "race_detail": race_detail,
        "award_j": award_j,
        "award_t": award_t,
        "award_h": award_h,
        "training_cnt": training_cnt,
        "trainer_double_check": trainer_double_check,
        "loadin_map": loadin_map,
        "race_detail_by_jockey": race_detail_by_jockey,
        "race_detail_by_trainer": race_detail_by_trainer,
        "race_detail_by_host": race_detail_by_host,
    }

    return render(request, "base/race_related.html", context)

def raceRelatedInfo(request, rcity, rdate, rno):
    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).first()
    if r_condition is None:
        return render(request, "base/home.html")

    cache_prefix = f"race_related_info:{rcity}:{rdate}:{rno}"

    train = cache.get(f"{cache_prefix}:train")
    if train is None:
        train = get_train_horse(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:train", train, RACE_PREDICTION_CACHE_TTL)

    train_title = trend_title(rdate)

    trainer_training = cache.get(f"{cache_prefix}:trainer_training")
    if trainer_training is None:
        trainer_training = get_trainer_double_check(rcity, rdate, rno)
        cache.set(
            f"{cache_prefix}:trainer_training",
            trainer_training,
            RACE_PREDICTION_CACHE_TTL,
        )
    trainer_double_check, training_cnt = trainer_training

    pedigree = cache.get(f"{cache_prefix}:pedigree")
    if pedigree is None:
        pedigree = get_pedigree(rcity, rdate, rno)  # 병력
        cache.set(f"{cache_prefix}:pedigree", pedigree, RACE_PREDICTION_CACHE_TTL)

    treat = cache.get(f"{cache_prefix}:treat")
    if treat is None:
        treat = get_treat_horse(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:treat", treat, RACE_PREDICTION_CACHE_TTL)

    judged_horse = cache.get(f"{cache_prefix}:judged_horse")
    if judged_horse is None:
        judged_horse = get_judged_horse(rcity, rdate, rno)
        cache.set(
            f"{cache_prefix}:judged_horse",
            judged_horse,
            RACE_PREDICTION_CACHE_TTL,
        )

    judged_jockey = cache.get(f"{cache_prefix}:judged_jockey")
    if judged_jockey is None:
        judged_jockey = get_judged_jockey(rcity, rdate, rno)
        cache.set(
            f"{cache_prefix}:judged_jockey",
            judged_jockey,
            RACE_PREDICTION_CACHE_TTL,
        )

    # award_j, award_t, award_h, race_detail = get_race_related(rcity, rdate, rno)

    paternal = cache.get(f"{cache_prefix}:paternal")
    if paternal is None or (hasattr(paternal, "__len__") and len(paternal) == 0):
        paternal = get_paternal(rcity, rdate, rno, r_condition.distance)  # 부마 3착 성적
        cache.set(f"{cache_prefix}:paternal", paternal, RACE_PREDICTION_CACHE_TTL)

    paternal_dist = cache.get(f"{cache_prefix}:paternal_dist")
    if paternal_dist is None or (
        hasattr(paternal_dist, "__len__") and len(paternal_dist) == 0
    ):
        paternal_dist = get_paternal_dist(rcity, rdate, rno)  # 부마 거리별 3착 성적
        cache.set(
            f"{cache_prefix}:paternal_dist",
            paternal_dist,
            RACE_PREDICTION_CACHE_TTL,
        )

    loadin = cache.get(f"{cache_prefix}:loadin")
    if loadin is None:
        loadin = get_loadin(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:loadin", loadin, RACE_PREDICTION_CACHE_TTL)

    disease = cache.get(f"{cache_prefix}:disease")
    if disease is None:
        disease = get_disease(rcity, rdate, rno)
        cache.set(f"{cache_prefix}:disease", disease, RACE_PREDICTION_CACHE_TTL)

    horses = []
    try:
        with connection.cursor() as cursor:
            strSql = """ 
                select host, horse, trainer, birthplace, sex, age, grade, tot_race, tot_1st, tot_2nd, tot_3rd, year_race, year_1st, year_2nd, year_3rd, tot_prize/1000, rating, price/1000
                from horse_w
                where wdate = COALESCE(
                    (select max(wdate) from The1.horse_w where wdate < %s),
                    (select max(wdate) from The1.horse_w where wdate <= %s)
                )
                and host in  ( select host from exp011 where rcity =  %s and rdate = %s and rno =  %s )
                order by host, trainer, horse
            """
            # 안전한 SQL 파라미터 바인딩
            params = (
                rdate,
                rdate,
                rcity,
                rdate,
                rno,
            )

            cursor.execute(strSql, params)
            horses = cursor.fetchall()

    except:
        print(f"❌ Failed selecting in horses:")  # 오류 메시지 출력
    
    train = train or []
    trainer_double_check = trainer_double_check or []
    training_cnt = training_cnt or []
    pedigree = pedigree or []
    treat = treat or []
    judged_horse = judged_horse or []
    judged_jockey = judged_jockey or []
    paternal = paternal or []
    paternal_dist = paternal_dist or []
    loadin = loadin or []
    disease = disease or []
    horses = horses or []

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
        "trainer_double_check": trainer_double_check,
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

def statusStable(request, rcity, rdate, rno):

    # r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).get()
    # print(r_condition)

    r_condition = Exp010.objects.filter(rcity=rcity, rdate=rdate, rno=rno).first()
    if not r_condition:
        # 1) 가장 무난: 404
        from django.http import Http404

        raise Http404("Exp010 not found")

        # 2) 또는: 빈 화면/기본값으로 처리하고 싶으면
        # return render(request, "some_template.html", {"warning": "데이터 없음"})

    stable, stable_g, stable_h = get_status_stable(rcity, rdate, rno)
    stable_list = stable.values.tolist()
    stable_list_g = stable_g.values.tolist()

    # 월별 피벗 결과가 일부 월 누락으로 가변 길이가 될 수 있어 템플릿 고정 언팩 길이에 맞춘다.
    def _pad_rows(rows, expected_len):
        padded = []
        for row in rows or []:
            row_list = list(row)
            if len(row_list) < expected_len:
                row_list.extend([0] * (expected_len - len(row_list)))
            elif len(row_list) > expected_len:
                row_list = row_list[:expected_len]
            padded.append(row_list)
        return padded

    stable_list = _pad_rows(stable_list, 35)
    stable_list_g = _pad_rows(stable_list_g, 36)
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

def raceTrain(request, rcity, rdate, rno):
    train = get_train_horse(rcity, rdate, rno)

    context = {
        "train": train,
    }

    return render(request, "base/race_train.html", context)

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

    rank1 = [item for item in status if item[29] == 1]  # item[29] : 예상착순(rank)
    rank2 = [item for item in status if item[29] == 2]  # item[29] : 예상착순(rank)
    rank3 = [item for item in status if item[29] == 3]  # item[29] : 예상착순(rank)
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


# Reports views


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


@login_required(login_url="account_login")

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


@login_required(login_url="account_login")

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

    result_success = 0
    result_failed = 0
    show_result = False
    result_cnt = 0

    def apply_result_counts(raw_result):
        nonlocal result_success, result_failed
        if isinstance(raw_result, dict):
            result_success = raw_result.get("success_cnt", 0)
            result_failed = raw_result.get("failed_cnt", 0)
        elif isinstance(raw_result, int):
            result_success = raw_result
            result_failed = 0

    if fdata == "-":
        result_cnt = 0
        pass
    elif fdata == "출전표변경":
        result_cnt = set_changed_race(rcity, rdate, rno, r_content)
        show_result = True
        apply_result_counts(result_cnt)
    elif fdata == "마체중":
        result_cnt = set_changed_race_weight(rcity, rdate, rno, r_content)
        show_result = True
        apply_result_counts(result_cnt)
    elif fdata == "경주순위":
        result_cnt = set_changed_race_rank(rcity, rdate, rno, r_content)
        show_result = True
        apply_result_counts(result_cnt)
    elif fdata == "경주마취소":
        result_cnt = set_changed_race_horse(rcity, rdate, rno, r_content)
    elif fdata == "기수변경":
        result_cnt = set_changed_race_jockey(rcity, rdate, rno, r_content)
    elif fdata == "수영조교":
        result_cnt = insert_train_swim(r_content)
        show_result = True
        apply_result_counts(result_cnt)
    elif fdata == "말진료현황":
        result_cnt = insert_horse_disease(r_content)
        show_result = True
        apply_result_counts(result_cnt)
    elif fdata == "출전등록 시뮬레이션":
        result_cnt = insert_race_simulation(rcity, rcount, r_content)
    elif fdata == "심판위원 Report":
        result_cnt = insert_race_judged(rcity, r_content)
        show_result = True
        apply_result_counts(result_cnt)
    elif fdata == "출발심사(b4)":
        result_cnt = insert_start_audit(r_content)
        show_result = True
        apply_result_counts(result_cnt)
    elif fdata == "출발조교(b5)":
        result_cnt = insert_start_train(r_content)
        show_result = True
        apply_result_counts(result_cnt)

    # 입력 처리 후에는 본문 입력창을 비워 재입력 준비 상태로 유지
    if request.method == "POST":
        r_content = ""

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
        "result_success": result_success,
        "result_failed": result_failed,
        "show_result": show_result,
    }

    # user = request.user
    # form = UserForm(instance=user)

    # return redirect('update_popularity', rcity=rcity, rdate=rdate, rno=rno)
    return render(request, "base/race_breakingnews.html", context)


@login_required
def kraScraper(request):
    if not (request.user.username == "admin" or request.user.is_superuser):
        return HttpResponse(status=403)

    preset = (request.POST.get("preset") if request.method == "POST" else request.GET.get("preset")) or "change"
    preset = preset if preset in SERVICE_KRA_CHANGE_PRESETS else "change"
    custom_url = (request.POST.get("custom_url") if request.method == "POST" else request.GET.get("custom_url")) or ""
    scraped_url = (custom_url or "").strip() or SERVICE_KRA_CHANGE_PRESETS[preset]["url"]
    scraped_text = ""
    processed_text = ""
    cancel_content = ""
    jockey_content = ""
    raw_html = ""
    page_title = ""
    fetch_error = ""
    fetched = False
    status_code = None
    action = (request.POST.get("action") if request.method == "POST" else "") or "scrape"
    db_result = {"mode": "", "count": 0, "error": ""}
    cancel_count = 0
    jockey_count = 0

    if request.method == "POST":
        fetched = True
        try:
            sync_result = sync_latest_kra_change_entries(
                url=scraped_url,
                commit=action in {"save_cancel", "save_jockey", "sync_all"},
                apply_cancel=action in {"save_cancel", "sync_all"},
                apply_jockey=action in {"save_jockey", "sync_all"},
            )
            scraped_url = sync_result.get("resolved_url") or scraped_url
            scraped_text = sync_result.get("text", "")
            cancel_content = (sync_result.get("cancel_content") or "").strip()
            jockey_content = (sync_result.get("jockey_content") or "").strip()
            cancel_count = int(sync_result.get("cancel_lines", 0) or 0)
            jockey_count = int(sync_result.get("jockey_lines", 0) or 0)
            processed_chunks = []
            if cancel_content:
                processed_chunks.append("[말취소]\n" + cancel_content)
            if jockey_content:
                processed_chunks.append("[기수변경]\n" + jockey_content)
            processed_text = "\n\n".join(processed_chunks).strip()
            raw_html = sync_result.get("html", "")
            page_title = (
                re.sub(r"\s+", " ", unescape(re.search(r"(?is)<title[^>]*>(.*?)</title>", raw_html).group(1))).strip()
                if raw_html and re.search(r"(?is)<title[^>]*>(.*?)</title>", raw_html)
                else ""
            )
            status_code = 200
            if not scraped_text and not raw_html:
                fetch_error = "본문 텍스트를 추출하지 못했습니다."
            if action == "save_cancel":
                if sync_result.get("cancel_lines", 0) <= 0:
                    db_result["error"] = "말취소 데이터로 변환할 행을 찾지 못했습니다."
                else:
                    db_result["count"] = int(sync_result.get("cancel_applied", 0) or 0)
                    db_result["mode"] = "말취소"
            elif action == "save_jockey":
                if sync_result.get("jockey_lines", 0) <= 0:
                    db_result["error"] = "기수변경 데이터로 변환할 행을 찾지 못했습니다."
                else:
                    db_result["count"] = int(sync_result.get("jockey_applied", 0) or 0)
                    db_result["mode"] = "기수변경"
            elif action == "sync_all":
                db_result["mode"] = "자동반영"
                db_result["count"] = int(sync_result.get("cancel_applied", 0) or 0) + int(sync_result.get("jockey_applied", 0) or 0)
        except Exception as e:
            fetch_error = str(e)

    context = {
        "preset": preset,
        "preset_items": SERVICE_KRA_CHANGE_PRESETS,
        "custom_url": custom_url,
        "scraped_url": scraped_url,
        "processed_text": processed_text,
        "cancel_content": cancel_content,
        "cancel_count": cancel_count,
        "jockey_content": jockey_content,
        "jockey_count": jockey_count,
        "scraped_text": scraped_text,
        "raw_html": raw_html,
        "page_title": page_title,
        "fetch_error": fetch_error,
        "fetched": fetched,
        "status_code": status_code,
        "action": action,
        "db_result": db_result,
    }
    return render(request, "base/kra_scraper.html", context)


# record calculation 기준정보 Setup

RACE_CALC_JOB_TTL = 60 * 60


def _race_calc_job_key(job_id):
    return f"race_calc:job:{job_id}"


def _race_calc_job_get(job_id):
    if not job_id:
        return None
    try:
        return cache.get(_race_calc_job_key(job_id))
    except Exception:
        return None


def _race_calc_job_set(job_id, state):
    if not job_id:
        return
    try:
        cache.set(_race_calc_job_key(job_id), state, RACE_CALC_JOB_TTL)
    except Exception:
        pass


def _race_calc_job_update(job_id, **kwargs):
    state = _race_calc_job_get(job_id) or {}
    state.update(kwargs)
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _race_calc_job_set(job_id, state)


def _race_calc_job_log(job_id, message):
    state = _race_calc_job_get(job_id) or {}
    logs = list(state.get("logs", []))
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    if len(logs) > 300:
        logs = logs[-300:]
    state["logs"] = logs
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _race_calc_job_set(job_id, state)


def _race_calc_elapsed_ms(start_ts):
    return (time.perf_counter() - start_ts) * 1000.0


class _RaceCalcJobLogStream:
    def __init__(self, job_id):
        self.job_id = job_id
        self._buf = ""

    def write(self, data):
        text = str(data or "")
        if not text:
            return 0
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.strip()
            if line:
                _race_calc_job_log(self.job_id, line)
        return len(text)

    def flush(self):
        line = self._buf.strip()
        if line:
            _race_calc_job_log(self.job_id, line)
        self._buf = ""


def _run_race_calculation_job(job_id, payload):
    from apps.ops.views import (
        execChatGPT,
        execChatGPTv2,
        execChatGPTv3,
        execChatGPTv4,
        execChatGPTv5,
    )

    close_old_connections()
    _stdout_stream = _RaceCalcJobLogStream(job_id)
    _stderr_stream = _RaceCalcJobLogStream(job_id)
    job_started_ts = time.perf_counter()
    try:
        with redirect_stdout(_stdout_stream), redirect_stderr(_stderr_stream):
            rdate1 = payload.get("rdate1", "")
            rdate2 = payload.get("rdate2", "")
            selected_exp010s = payload.get("selected_exp010s", [])
            do_baseline = bool(payload.get("rcheck1"))
            prediction_profile = str(payload.get("prediction_profile") or "v2").strip().lower()
            if prediction_profile == "v1":
                run_prediction = execChatGPT
            elif prediction_profile == "v2":
                run_prediction = execChatGPTv2
            elif prediction_profile == "v3":
                run_prediction = execChatGPTv3
            elif prediction_profile == "v4":
                run_prediction = execChatGPTv4
            else:
                prediction_profile = "v0"
                run_prediction = execChatGPTv5

            _race_calc_job_update(
                job_id,
                status="running",
                started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                done=0,
                total=len(selected_exp010s),
                errors=0,
                progress=0,
            )
            _race_calc_job_log(
                job_id,
                f"집계 시작 / 기간 {rdate1}~{rdate2} / 대상 {len(selected_exp010s)}건 / 프로파일 {prediction_profile.upper()}",
            )

            baseline_errors = 0
            if do_baseline:
                try:
                    baseline_started_ts = time.perf_counter()
                    # 누수 방지 목적: 기준정보 집계 기준일을 기간 시작일의 전일로 맞춘다.
                    try:
                        baseline_rdate = (
                            datetime.strptime(str(rdate1), "%Y%m%d") - timedelta(days=1)
                        ).strftime("%Y%m%d")
                    except Exception:
                        baseline_rdate = rdate1

                    for pass_idx in (1, 2):
                        pass_started_ts = time.perf_counter()
                        _race_calc_job_log(
                            job_id,
                            f"기준정보 {pass_idx}차 계산 시작: {baseline_rdate}",
                        )
                        ret = baseline_compute(connection, baseline_rdate)
                        if ret != 1:
                            baseline_errors += 1
                            _race_calc_job_update(job_id, errors=baseline_errors)
                            _race_calc_job_log(
                                job_id,
                                (
                                    f"기준정보 {pass_idx}차 계산 오류: {baseline_rdate} "
                                    f"({_race_calc_elapsed_ms(pass_started_ts):.1f}ms)"
                                ),
                            )
                            _race_calc_job_log(
                                job_id,
                                f"기준정보 {pass_idx}차 실패로 이후 기준정보 갱신 단계를 중단",
                            )
                            break

                        _race_calc_job_log(
                            job_id,
                            (
                                f"기준정보 {pass_idx}차 계산 완료: {baseline_rdate} "
                                f"({_race_calc_elapsed_ms(pass_started_ts):.1f}ms)"
                            ),
                        )
                        renew_started_ts = time.perf_counter()
                        renew_stats = renewal_record_s(connection, baseline_rdate) or {}
                        renew_errors = int(renew_stats.get("errors", 0) or 0)
                        if renew_errors > 0:
                            baseline_errors += renew_errors
                            _race_calc_job_update(job_id, errors=baseline_errors)
                            _race_calc_job_log(
                                job_id,
                                (
                                    f"기준정보 {pass_idx}차 갱신 부분실패: {baseline_rdate} "
                                    f"(clear={renew_stats.get('clear_xyz', 0)}, "
                                    f"x={renew_stats.get('set_x', 0)}, y={renew_stats.get('set_y', 0)}, "
                                    f"z={renew_stats.get('set_z', 0)}, "
                                    f"insert={renew_stats.get('insert_record_s', 0)}, "
                                    f"errors={renew_errors}, "
                                    f"elapsed={_race_calc_elapsed_ms(renew_started_ts):.1f}ms)"
                                ),
                            )
                        else:
                            _race_calc_job_log(
                                job_id,
                                (
                                    f"기준정보 {pass_idx}차 갱신 완료: {baseline_rdate} "
                                    f"(clear={renew_stats.get('clear_xyz', 0)}, "
                                    f"x={renew_stats.get('set_x', 0)}, y={renew_stats.get('set_y', 0)}, "
                                    f"z={renew_stats.get('set_z', 0)}, "
                                    f"insert={renew_stats.get('insert_record_s', 0)}, "
                                    f"elapsed={_race_calc_elapsed_ms(renew_started_ts):.1f}ms)"
                                ),
                            )
                    _race_calc_job_log(
                        job_id,
                        (
                            f"기준정보 단계 소요: {_race_calc_elapsed_ms(baseline_started_ts):.1f}ms "
                            f"/ errors={baseline_errors}"
                        ),
                    )
                except Exception as e:
                    baseline_errors += 1
                    _race_calc_job_update(job_id, errors=baseline_errors)
                    _race_calc_job_log(job_id, f"기준정보 단계 실패: {e}")

            if not selected_exp010s:
                _race_calc_job_log(job_id, "선택된 경주가 없어 경주별 집계를 건너뜀")
            else:
                weight = []
                try:
                    weight_started_ts = time.perf_counter()
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT w_avg, w_fast, w_slow, w_recent3, w_recent5, w_convert, 1 w_flag
                            FROM weight
                            WHERE wdate = (SELECT MAX(wdate) FROM weight);
                            """
                        )
                        weight = cursor.fetchall()
                    _race_calc_job_log(
                        job_id,
                        (
                            f"가중치 조회 완료: rows={len(weight)} "
                            f"({_race_calc_elapsed_ms(weight_started_ts):.1f}ms)"
                        ),
                    )
                except Exception as e:
                    _race_calc_job_log(job_id, f"가중치 조회 실패: {e}")

                if not weight:
                    baseline_errors += 1
                    _race_calc_job_update(job_id, errors=baseline_errors)
                    _race_calc_job_log(job_id, "가중치(weight) 데이터가 없어 집계를 중단")
                else:
                    done = 0
                    errors = baseline_errors
                    total = len(selected_exp010s)
                    loop_started_ts = time.perf_counter()
                    for exp010 in selected_exp010s:
                        race_started_ts = time.perf_counter()
                        rcity, rdate, rno = exp010[0], exp010[1], exp010[2]
                        _race_calc_job_log(job_id, f"[시작] {rcity} {rdate} {rno}경주")
                        try:
                            condition_started_ts = time.perf_counter()
                            r_condition = Exp010.objects.filter(
                                rcity=rcity, rdate=rdate, rno=rno
                            ).first()
                            if r_condition is None:
                                errors += 1
                                _race_calc_job_log(
                                    job_id, f"[실패] {rcity} {rdate} {rno}경주 - 조건 데이터 없음"
                                )
                            else:
                                condition_elapsed_ms = _race_calc_elapsed_ms(condition_started_ts)
                                create_record_started_ts = time.perf_counter()
                                create_record(connection, r_condition, weight)
                                create_record_elapsed_ms = _race_calc_elapsed_ms(
                                    create_record_started_ts
                                )
                                prediction_started_ts = time.perf_counter()
                                run_prediction(None, rcity=rcity, rdate=rdate, rno=rno)
                                prediction_elapsed_ms = _race_calc_elapsed_ms(
                                    prediction_started_ts
                                )
                                done += 1
                                _race_calc_job_log(
                                    job_id,
                                    (
                                        f"[완료] {rcity} {rdate} {rno}경주 "
                                        f"(condition={condition_elapsed_ms:.1f}ms, "
                                        f"record={create_record_elapsed_ms:.1f}ms, "
                                        f"prediction={prediction_elapsed_ms:.1f}ms, "
                                        f"total={_race_calc_elapsed_ms(race_started_ts):.1f}ms)"
                                    ),
                                )
                        except Exception as e:
                            errors += 1
                            _race_calc_job_log(
                                job_id,
                                (
                                    f"[실패] {rcity} {rdate} {rno}경주 - {e} "
                                    f"(elapsed={_race_calc_elapsed_ms(race_started_ts):.1f}ms)"
                                ),
                            )

                        progress = int(((done + errors) / total) * 100) if total > 0 else 100
                        _race_calc_job_update(
                            job_id,
                            done=done,
                            errors=errors,
                            total=total,
                            progress=progress,
                        )
                    _race_calc_job_log(
                        job_id,
                        (
                            f"경주별 집계 단계 소요: {_race_calc_elapsed_ms(loop_started_ts):.1f}ms "
                            f"/ success={done} / errors={errors}"
                        ),
                    )

                    # try:
                    #     update_m_rank_score_for_period(
                    #         rdate1,
                    #         rdate2,
                    #         model_name=f"sb_top3_roll12_{rdate1[0:6]}",
                    #     )
                    #     _race_calc_job_log(job_id, "m_rank/m_score 갱신 완료")
                    # except Exception as e:
                    #     _race_calc_job_log(job_id, f"m_rank/m_score 갱신 실패: {e}")
                        
                        
                    # try:
                    #     update_exp011_for_period(rdate1, rdate2)
                    #     _race_calc_job_log(job_id, "exp011 점수 갱신 완료")
                    # except Exception as e:
                    #     _race_calc_job_log(job_id, f"exp011 점수 갱신 실패: {e}")
                    # try:
                    #     run_rguide_update(from_date=rdate1, to_date=rdate2, dry_run=False)
                    #     _race_calc_job_log(job_id, "r_guide 업데이트 완료")
                    # except Exception as e:
                    #     _race_calc_job_log(job_id, f"r_guide 업데이트 실패: {e}")

            state = _race_calc_job_get(job_id) or {}
            final_errors = int(state.get("errors", 0) or 0)
            final_done = int(state.get("done", 0) or 0)
            final_status = "success"
            if final_errors > 0 and final_done > 0:
                final_status = "partial"
            elif final_errors > 0 and final_done == 0:
                final_status = "failed"

            _race_calc_job_update(
                job_id,
                status=final_status,
                done=final_done,
                errors=final_errors,
                progress=100,
                finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                elapsed_ms=round(_race_calc_elapsed_ms(job_started_ts), 1),
            )
            _race_calc_job_log(
                job_id,
                (
                    f"집계 작업 종료 / status={final_status} / done={final_done} "
                    f"/ errors={final_errors} / elapsed={_race_calc_elapsed_ms(job_started_ts):.1f}ms"
                ),
            )
    except Exception as e:
        _race_calc_job_update(
            job_id,
            status="failed",
            progress=100,
            finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            elapsed_ms=round(_race_calc_elapsed_ms(job_started_ts), 1),
        )
        _race_calc_job_log(job_id, f"치명적 오류: {e}")
        _race_calc_job_log(job_id, traceback.format_exc())
    finally:
        _stdout_stream.flush()
        _stderr_stream.flush()
        close_old_connections()


@login_required
def raceCalculation(request):
    if not (request.user.username == "admin" or request.user.is_superuser):
        return HttpResponse(status=403)

    def _to_ymd(raw):
        v = (raw or "").strip()
        if len(v) == 8 and v.isdigit():
            return v
        if len(v) == 10 and v[4] == "-" and v[7] == "-":
            return v[0:4] + v[5:7] + v[8:10]
        return ""

    def _to_date_dash(raw):
        ymd = _to_ymd(raw)
        if len(ymd) == 8:
            return f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"
        return ""

    q1 = request.GET.get("q1", "") if request.method == "GET" else request.POST.get("q1", "")
    q2 = request.GET.get("q2", "") if request.method == "GET" else request.POST.get("q2", "")
    selected_rcity = (
        request.GET.get("rcity", "") if request.method == "GET" else request.POST.get("rcity", "")
    ).strip()
    job_id = (request.GET.get("job_id", "") if request.method == "GET" else "").strip()
    prediction_profile = (
        request.GET.get("prediction_profile", "")
        if request.method == "GET"
        else request.POST.get("prediction_profile", "")
    ).strip().lower() or "v2"
    if prediction_profile == "v5":
        prediction_profile = "v0"
    elif prediction_profile not in {"v0", "v1", "v2", "v3", "v4"}:
        prediction_profile = "v2"
    if request.method == "POST":
        baseline_checked = bool(request.POST.get("rcheck1"))
    else:
        baseline_checked = request.GET.get("baseline", "1").strip() != "0"
    calc_logs = []

    rdate1 = _to_ymd(q1)
    rdate2 = _to_ymd(q2)

    if not rdate1 or not rdate2:
        rdates = list(Racing.objects.values("rdate").order_by("-rdate").distinct()[:3])
        if len(rdates) < 3:
            messages.error(request, "집계 기준 경주일 데이터가 부족합니다.")
            calc_logs.append("집계 기준 경주일 데이터가 부족하여 목록을 생성하지 못했습니다.")
            context = {
                "q1": q1,
                "q2": q2,
                "rdate1": "",
                "rdate2": "",
                "fdate1": "",
                "fdate2": "",
                "selected_rcity": selected_rcity,
                "available_rcities": [],
                "exp010s": [],
                "calc_logs": calc_logs,
            }
            return render(request, "base/race_calculation.html", context)
        rdate1 = rdates[0]["rdate"]
        rdate2 = rdates[2]["rdate"]

    if rdate1 > rdate2:
        rdate1, rdate2 = rdate2, rdate1

    fdate1 = _to_date_dash(rdate1)
    fdate2 = _to_date_dash(rdate2)

    available_rcities = []
    exp010s = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT rcity
                FROM exp010
                WHERE rdate BETWEEN %s AND %s
                ORDER BY rcity;
                """,
                (rdate1, rdate2),
            )
            available_rcities = [row[0] for row in cursor.fetchall() if row and row[0]]

            query = """
                SELECT rcity, rdate, rno, grade, rname, distance, dividing, rcount
                FROM exp010
                WHERE rdate BETWEEN %s AND %s
            """
            params = [rdate1, rdate2]
            if selected_rcity:
                query += " AND rcity = %s"
                params.append(selected_rcity)
            query += " ORDER BY rcity, rdate, rno;"
            cursor.execute(query, params)
            exp010s = cursor.fetchall()
    except Exception as e:
        print(f"❌ Failed selecting in 경주 메모: {e}")
        calc_logs.append(f"목록 조회 실패: {e}")

    if request.method == "POST":

        selected_keys = set(request.POST.getlist("rcheck"))
        selected_exp010s = []
        if selected_keys:
            for row in exp010s:
                row_key = f"{row[0]}|{row[1]}|{row[2]}"
                if row_key in selected_keys:
                    selected_exp010s.append(row)
        job_id = uuid.uuid4().hex
        initial_state = {
            "job_id": job_id,
            "status": "queued",
            "logs": [],
            "done": 0,
            "errors": 0,
            "total": len(selected_exp010s),
            "progress": 0,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _race_calc_job_set(job_id, initial_state)
        _race_calc_job_log(
            job_id,
            f"집계 요청 수신 / 기간 {rdate1}~{rdate2} / 대상 {len(selected_exp010s)}건 / 프로파일 {prediction_profile.upper()}",
        )

        payload = {
            "rdate1": rdate1,
            "rdate2": rdate2,
            "rcheck1": bool(request.POST.get("rcheck1")),
            "prediction_profile": prediction_profile,
            "selected_exp010s": selected_exp010s,
        }
        try:
            t = threading.Thread(
                target=_run_race_calculation_job,
                args=(job_id, payload),
                daemon=True,
            )
            t.start()
            messages.info(request, f"집계 작업을 시작했습니다. (job: {job_id[:8]})")
        except Exception as e:
            _race_calc_job_update(job_id, status="failed", progress=100)
            _race_calc_job_log(job_id, f"작업 스레드 시작 실패: {e}")
            messages.error(request, "집계 작업 시작에 실패했습니다.")
        query_string = urlencode(
            {
                "q1": fdate1,
                "q2": fdate2,
                "job_id": job_id,
                "prediction_profile": prediction_profile,
                "rcity": selected_rcity,
                "baseline": "1" if baseline_checked else "0",
            }
        )
        return redirect(f"{request.path}?{query_string}")

    if job_id:
        state = _race_calc_job_get(job_id) or {}
        calc_logs = list(state.get("logs", []))
    else:
        calc_logs = []

    context = {
        "q1": q1,
        "q2": q2,
        "rdate1": rdate1,
        "rdate2": rdate2,
        "fdate1": fdate1,
        "fdate2": fdate2,
        "selected_rcity": selected_rcity,
        "available_rcities": available_rcities,
        "exp010s": exp010s,
        "calc_logs": calc_logs,
        "job_id": job_id,
        "prediction_profile": prediction_profile,
        "baseline_checked": baseline_checked,
        "today": datetime.now().strftime("%Y%m%d"),
    }
    return render(request, "base/race_calculation.html", context)


@login_required
def raceCalculationJobStatus(request, job_id):
    # Defensive local import: prevents NameError even if module globals are stale.
    from django.http import JsonResponse as _JsonResponse

    if not (request.user.username == "admin" or request.user.is_superuser):
        return _JsonResponse({"ok": False, "message": "forbidden"}, status=403)
    try:
        state = _race_calc_job_get(job_id)
        if not state:
            return _JsonResponse({"ok": False, "message": "not_found"}, status=404)
        return _JsonResponse({"ok": True, **state})
    except Exception as e:
        return _JsonResponse({"ok": False, "message": str(e)}, status=200)

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
