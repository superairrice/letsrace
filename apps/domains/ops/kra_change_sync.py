import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from apps.domains.ops.mysqls import set_changed_race_horse, set_changed_race_jockey


KRA_CHANGE_PRESETS = {
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


class SimpleHtmlTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._table = None
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self._table = {"rows": []}
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            attr_map = dict(attrs)
            self._cell = {
                "text": "",
                "is_header": tag == "th",
                "colspan": int(attr_map.get("colspan", "1") or "1"),
                "rowspan": int(attr_map.get("rowspan", "1") or "1"),
            }
        elif self._cell is not None and tag == "br":
            self._cell["text"] += "\n"

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

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"] += data


def strip_html_to_text(raw_html):
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


def parse_html_tables(raw_html):
    parser = SimpleHtmlTableParser()
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
        parsed_tables.append({"index": index, "headers": header_row or [], "rows": body_rows})
    return parsed_tables


def normalize_kra_header(text):
    return re.sub(r"[\s\n\r\t()\-_/.:]", "", (text or "").strip()).lower()


def match_header_index(headers, candidates):
    normalized = [normalize_kra_header(h.get("text", "")) for h in headers]
    candidate_keys = [normalize_kra_header(c) for c in candidates]
    for idx, header in enumerate(normalized):
        if any(key and key in header for key in candidate_keys):
            return idx
    return -1


def table_row_to_cells(row):
    return [str(cell.get("text", "") or "").strip() for cell in row]


def extract_iframe_urls(html, base_url):
    refs = set()
    for pattern in [r'(?is)<iframe[^>]+src=["\']([^"\']+)["\']', r'(?is)<frame[^>]+src=["\']([^"\']+)["\']']:
        for ref in re.findall(pattern, html or ""):
            ref = (ref or "").strip()
            if ref:
                refs.add(urljoin(base_url, ref))
    return list(refs)


def fetch_html_bundle(url, timeout=15):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    main_html = response.text
    pages = [{"url": url, "html": main_html, "status_code": response.status_code}]

    iframe_urls = extract_iframe_urls(main_html, url)
    for iframe_url in iframe_urls[:5]:
        try:
            iframe_response = requests.get(iframe_url, headers=headers, timeout=timeout)
            iframe_response.raise_for_status()
            pages.append(
                {
                    "url": iframe_url,
                    "html": iframe_response.text,
                    "status_code": iframe_response.status_code,
                }
            )
        except Exception:
            continue
    return pages


def collect_tables_from_pages(pages):
    all_tables = []
    best_text = ""
    best_html = ""
    best_url = ""
    for page in pages:
        html = page.get("html", "")
        page_tables = parse_html_tables(html)
        if page_tables:
            all_tables.extend(page_tables)
        page_text = strip_html_to_text(html)
        if len(page_text) > len(best_text):
            best_text = page_text
            best_html = html
            best_url = page.get("url", "")
    return {
        "tables": all_tables,
        "text": best_text,
        "html": best_html,
        "best_url": best_url,
    }


def extract_cancel_content_from_tables(scraped_tables):
    lines = []
    for table in scraped_tables or []:
        headers = table.get("headers") or []
        if not headers:
            continue
        idx_date = match_header_index(headers, ["일자", "경주일", "시행일자"])
        idx_rno = match_header_index(headers, ["경주번호", "경주"])
        idx_horse = match_header_index(headers, ["마명", "경주마"])
        idx_reason = match_header_index(headers, ["사유", "변경사유", "취소사유"])
        if min(idx_date, idx_rno, idx_horse, idx_reason) < 0:
            continue
        for row in table.get("rows") or []:
            cells = table_row_to_cells(row)
            if max(idx_date, idx_rno, idx_horse, idx_reason) >= len(cells):
                continue
            if not cells[idx_date] or not cells[idx_horse]:
                continue
            line_items = ["취소", cells[idx_date], cells[idx_rno], "", cells[idx_horse], "", "", cells[idx_reason]]
            lines.append("\t".join(line_items))
    return "\n".join(lines)


def extract_jockey_change_content_from_tables(scraped_tables):
    lines = []
    for table in scraped_tables or []:
        headers = table.get("headers") or []
        if not headers:
            continue
        idx_date = match_header_index(headers, ["일자", "경주일", "시행일자"])
        idx_rno = match_header_index(headers, ["경주번호", "경주"])
        idx_horse = match_header_index(headers, ["마명", "경주마"])
        idx_old_jockey = match_header_index(headers, ["변경전기수", "당초기수", "변경전"])
        idx_new_jockey = match_header_index(headers, ["변경후기수", "변경기수", "기수변경", "변경후"])
        idx_old_handy = match_header_index(headers, ["변경전중량", "당초부담중량", "기존부담중량"])
        idx_new_handy = match_header_index(headers, ["변경후중량", "변경부담중량", "신부담중량", "중량", "부담중량"])
        idx_reason = match_header_index(headers, ["사유", "변경사유"])

        # Current KRA page often exposes one shared "중량" column instead of before/after weights.
        if idx_old_handy < 0 and idx_new_handy >= 0:
            idx_old_handy = idx_new_handy
        if idx_new_handy < 0 and idx_old_handy >= 0:
            idx_new_handy = idx_old_handy

        required_indexes = [idx_date, idx_rno, idx_horse, idx_old_jockey, idx_new_jockey, idx_new_handy, idx_reason]
        if min(required_indexes) < 0:
            continue
        for row in table.get("rows") or []:
            cells = table_row_to_cells(row)
            if max(required_indexes + [idx_old_handy]) >= len(cells):
                continue
            if not cells[idx_date] or not cells[idx_horse]:
                continue

            old_handy = cells[idx_old_handy] if idx_old_handy >= 0 else cells[idx_new_handy]
            new_handy = cells[idx_new_handy]
            line_items = [
                cells[idx_date],
                cells[idx_rno],
                "",
                cells[idx_horse],
                cells[idx_old_jockey],
                old_handy,
                cells[idx_new_jockey],
                new_handy,
                cells[idx_reason],
            ]
            lines.append("\t".join(line_items))
    return "\n".join(lines)


def sync_latest_kra_change_entries(url=None, commit=True, apply_cancel=True, apply_jockey=True):
    target_url = (url or "").strip() or KRA_CHANGE_PRESETS["change"]["url"]
    pages = fetch_html_bundle(target_url)
    collected = collect_tables_from_pages(pages)
    tables = collected["tables"]
    cancel_content = extract_cancel_content_from_tables(tables)
    jockey_content = extract_jockey_change_content_from_tables(tables)

    result = {
        "url": target_url,
        "resolved_url": collected.get("best_url") or target_url,
        "tables": tables,
        "text": collected.get("text", ""),
        "html": collected.get("html", ""),
        "cancel_content": cancel_content,
        "jockey_content": jockey_content,
        "cancel_lines": 0,
        "jockey_lines": 0,
        "cancel_applied": 0,
        "jockey_applied": 0,
        "commit": bool(commit),
    }

    if cancel_content.strip():
        result["cancel_lines"] = len([line for line in cancel_content.splitlines() if line.strip()])
        if commit and apply_cancel:
            result["cancel_applied"] = int(set_changed_race_horse("", "", 0, cancel_content) or 0)

    if jockey_content.strip():
        result["jockey_lines"] = len([line for line in jockey_content.splitlines() if line.strip()])
        if commit and apply_jockey:
            result["jockey_applied"] = int(set_changed_race_jockey("", "", 0, jockey_content) or 0)

    return result
