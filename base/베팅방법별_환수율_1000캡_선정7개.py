"""관리자 수익 분석과 동일한 방식으로 기간 지정 콘솔/CSV 집계를 출력한다."""

import os
import sys
import copy
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


PROFILE_NAME = "베팅방법별_환수율_1000캡_선정7개"
DEFAULT_FROM_DATE = "20250101"
DEFAULT_TO_DATE = "20260325"
DEFAULT_OUTPUT_PATH = "/Users/Super007/Documents/r_pop_total_new_베팅방법별_환수율_1000캡_선정7개.csv"
DEFAULT_NO_CAP_OUTPUT_PATH = "/Users/Super007/Documents/r_pop_total_new_베팅방법별_환수율_무캡_선정7개.csv"
MAX_DISPLAY_ODDS = 1000.0


def _calc_hit_rate(hits, races) -> float:
    try:
        hits_value = int(hits or 0)
        races_value = int(races or 0)
    except Exception:
        return 0.0
    return (hits_value / races_value) if races_value > 0 else 0.0


def _method_display_sort_key(method: dict):
    label = str(method.get("label", "") or "").replace("  - ", "").strip()
    if "삼복" in label:
        type_order = 0
    elif "삼쌍" in label:
        type_order = 1
    else:
        type_order = 2
    return (type_order, label)


def _build_combined_track_total(payload: dict) -> dict:
    """서울/부산 경마장 총계를 합산한 통합 결과를 만든다."""
    tracks = payload.get("method_bet_by_track") or []
    if not tracks:
        return {}

    total_races = int(sum(int(track.get("total_races", 0) or 0) for track in tracks))
    hit_races = int(sum(int(track.get("hit_races", 0) or 0) for track in tracks))
    total_bet = float(
        sum(float(track.get("total_bet", 0.0) or 0.0) for track in tracks)
    )
    total_refund = float(
        sum(float(track.get("total_refund", 0.0) or 0.0) for track in tracks)
    )
    total_profit = total_refund - total_bet
    hole_values = {
        int(track.get("total_holes_per_race", 0) or 0)
        for track in tracks
        if track.get("total_holes_per_race") is not None
    }

    return {
        "track": "서울부산 통합",
        "total_races": total_races,
        "hit_races": hit_races,
        "total_bet": total_bet,
        "total_refund": total_refund,
        "total_profit": total_profit,
        "roi": (total_refund / total_bet) if total_bet > 0 else 0.0,
        "roi_pct": ((total_refund / total_bet) * 100.0) if total_bet > 0 else 0.0,
        "total_holes_per_race": hole_values.pop() if len(hole_values) == 1 else None,
    }


def _build_combined_method_totals(payload: dict) -> list[dict]:
    """서울/부산 상세 베팅방법을 합산한 통합 결과를 만든다."""
    combined = {}
    for track in payload.get("method_bet_by_track") or []:
        for method in track.get("methods") or []:
            if method.get("is_group"):
                continue
            label = str(method.get("label", "") or "").strip()
            if not label:
                continue
            item = combined.setdefault(
                label,
                {
                    "label": label,
                    "amount": 0.0,
                    "refund": 0.0,
                    "profit": 0.0,
                    "hits": 0,
                    "holes_per_race_values": set(),
                },
            )
            item["amount"] += float(method.get("amount", 0.0) or 0.0)
            item["refund"] += float(method.get("refund", 0.0) or 0.0)
            item["profit"] += float(method.get("profit", 0.0) or 0.0)
            item["hits"] += int(method.get("hits", 0) or 0)
            if method.get("holes_per_race") is not None:
                item["holes_per_race_values"].add(
                    int(method.get("holes_per_race", 0) or 0)
                )

    rows = []
    for item in combined.values():
        hole_values = item.pop("holes_per_race_values", set())
        item["holes_per_race"] = hole_values.pop() if len(hole_values) == 1 else None
        item["roi"] = (item["refund"] / item["amount"]) if item["amount"] > 0 else 0.0
        rows.append(item)

    rows.sort(key=_method_display_sort_key)
    return rows


def flatten_payload_to_df(payload: dict) -> pd.DataFrame:
    """관리자 수익 분석 payload를 CSV 저장용 행으로 펼친다."""
    rows = []
    summary_total = payload.get("summary_total") or {}
    metrics = payload.get("metrics") or {}
    combined_total = _build_combined_track_total(payload)
    combined_methods = _build_combined_method_totals(payload)
    summary_hit_rate = _calc_hit_rate(
        summary_total.get("hits", 0), summary_total.get("races", 0)
    )
    rows.append(
        {
            "row_type": "summary_total",
            "기준일": payload.get("i_rdate"),
            "집계시작일": payload.get("from_date"),
            "집계종료일": payload.get("to_date"),
            "배당캡": payload.get("odds_cap_label"),
            "경마장": "통합",
            "구분": "주력합계",
            "전략명": "주력베팅 총계",
            "경주수": summary_total.get("races", 0),
            "적중경주수": summary_total.get("hits", 0),
            "총베팅액": summary_total.get("total_bet", 0.0),
            "총환수액": summary_total.get("total_refund", 0.0),
            "이익금액": summary_total.get("profit", 0.0),
            "적중율": summary_hit_rate,
            "적중율_pct": summary_hit_rate * 100.0,
            "환수율": metrics.get("roi", 0.0),
            "환수율_pct": metrics.get("roi_pct", 0.0),
            "구멍수": None,
        }
    )

    if combined_total:
        rows.append(
            {
                "row_type": "combined_track_total",
                "기준일": payload.get("i_rdate"),
                "집계시작일": payload.get("from_date"),
                "집계종료일": payload.get("to_date"),
                "배당캡": payload.get("odds_cap_label"),
                "경마장": combined_total.get("track"),
                "구분": "경마장통합",
                "전략명": "총계",
                "경주수": combined_total.get("total_races", 0),
                "적중경주수": combined_total.get("hit_races", 0),
                "총베팅액": combined_total.get("total_bet", 0.0),
                "총환수액": combined_total.get("total_refund", 0.0),
                "이익금액": combined_total.get("total_profit", 0.0),
                "적중율": _calc_hit_rate(
                    combined_total.get("hit_races", 0),
                    combined_total.get("total_races", 0),
                ),
                "적중율_pct": _calc_hit_rate(
                    combined_total.get("hit_races", 0),
                    combined_total.get("total_races", 0),
                )
                * 100.0,
                "환수율": combined_total.get("roi", 0.0),
                "환수율_pct": combined_total.get("roi_pct", 0.0),
                "구멍수": combined_total.get("total_holes_per_race"),
            }
        )
    for method in combined_methods:
        rows.append(
            {
                "row_type": "combined_method",
                "기준일": payload.get("i_rdate"),
                "집계시작일": payload.get("from_date"),
                "집계종료일": payload.get("to_date"),
                "배당캡": payload.get("odds_cap_label"),
                "경마장": "서울부산 통합",
                "구분": "베팅방법통합",
                "전략명": method.get("label"),
                "경주수": combined_total.get("total_races", 0) if combined_total else 0,
                "적중경주수": method.get("hits", 0),
                "총베팅액": method.get("amount", 0.0),
                "총환수액": method.get("refund", 0.0),
                "이익금액": method.get("profit", 0.0),
                "적중율": _calc_hit_rate(
                    method.get("hits", 0),
                    combined_total.get("total_races", 0) if combined_total else 0,
                ),
                "적중율_pct": _calc_hit_rate(
                    method.get("hits", 0),
                    combined_total.get("total_races", 0) if combined_total else 0,
                )
                * 100.0,
                "환수율": method.get("roi", 0.0),
                "환수율_pct": float(method.get("roi", 0.0) or 0.0) * 100.0,
                "구멍수": method.get("holes_per_race"),
            }
        )

    for track in payload.get("method_bet_by_track") or []:
        rows.append(
            {
                "row_type": "track_total",
                "기준일": payload.get("i_rdate"),
                "집계시작일": payload.get("from_date"),
                "집계종료일": payload.get("to_date"),
                "배당캡": payload.get("odds_cap_label"),
                "경마장": track.get("track"),
                "구분": "경마장총계",
                "전략명": "총계",
                "경주수": track.get("total_races", 0),
                "적중경주수": track.get("hit_races", 0),
                "총베팅액": track.get("total_bet", 0.0),
                "총환수액": track.get("total_refund", 0.0),
                "이익금액": track.get("total_profit", 0.0),
                "적중율": _calc_hit_rate(
                    track.get("hit_races", 0), track.get("total_races", 0)
                ),
                "적중율_pct": _calc_hit_rate(
                    track.get("hit_races", 0), track.get("total_races", 0)
                )
                * 100.0,
                "환수율": track.get("roi", 0.0),
                "환수율_pct": track.get("roi_pct", 0.0),
                "구멍수": track.get("total_holes_per_race", 0),
            }
        )
        for method in track.get("methods") or []:
            rows.append(
                {
                    "row_type": "method",
                    "기준일": payload.get("i_rdate"),
                    "집계시작일": payload.get("from_date"),
                    "집계종료일": payload.get("to_date"),
                    "배당캡": payload.get("odds_cap_label"),
                    "경마장": track.get("track"),
                    "구분": (
                        "보조베팅"
                        if method.get("is_support_group")
                        else ("그룹" if method.get("is_group") else "상세")
                    ),
                    "전략명": method.get("label"),
                    "경주수": track.get("total_races", 0),
                    "적중경주수": method.get("hits", 0),
                    "총베팅액": method.get("amount", 0.0),
                    "총환수액": method.get("refund", 0.0),
                    "이익금액": method.get("profit", 0.0),
                    "적중율": _calc_hit_rate(
                        method.get("hits", 0), track.get("total_races", 0)
                    ),
                    "적중율_pct": _calc_hit_rate(
                        method.get("hits", 0), track.get("total_races", 0)
                    )
                    * 100.0,
                    "환수율": (
                        (
                            float(method.get("refund", 0.0))
                            / float(method.get("amount", 0.0))
                        )
                        if float(method.get("amount", 0.0) or 0.0) > 0
                        else 0.0
                    ),
                    "환수율_pct": (
                        (
                            (
                                float(method.get("refund", 0.0))
                                / float(method.get("amount", 0.0))
                            )
                            * 100.0
                        )
                        if float(method.get("amount", 0.0) or 0.0) > 0
                        else 0.0
                    ),
                    "구멍수": method.get("holes_per_race"),
                }
            )

    return pd.DataFrame(rows)


def print_payload(payload: dict) -> None:
    """관리자 수익 분석 payload를 콘솔에 텍스트로 출력한다."""
    summary_total = payload.get("summary_total") or {}
    metrics = payload.get("metrics") or {}
    combined_total = _build_combined_track_total(payload)
    combined_methods = _build_combined_method_totals(payload)
    summary_hit_rate = _calc_hit_rate(
        summary_total.get("hits", 0), summary_total.get("races", 0)
    )
    print(
        f"[{PROFILE_NAME} 관리자 수익 분석 동일 기준"
        f" - {payload.get('odds_cap_label', '')}]"
    )
    print(
        f"기준일: {payload.get('i_rdate')}  "
        f"집계기간: {payload.get('from_date')} ~ {payload.get('to_date')}"
    )

    if summary_total:
        print(
            f"[주력 총계]  경주수: {int(summary_total.get('races', 0) or 0)}  "
            f"적중경주수: {int(summary_total.get('hits', 0) or 0)}  "
            f"적중율: {summary_hit_rate:.3f}  "
            f"총베팅액: {float(summary_total.get('total_bet', 0.0) or 0.0):,.0f}원  "
            f"총환수액: {float(summary_total.get('total_refund', 0.0) or 0.0):,.0f}원  "
            f"이익금액: {float(summary_total.get('profit', 0.0) or 0.0):,.0f}원  "
            f"환수율: {float(metrics.get('roi', 0.0) or 0.0):.3f}"
        )

    for track in payload.get("method_bet_by_track") or []:
        print(
            f"[{track.get('track')}]  경주수: {int(track.get('total_races', 0) or 0)}  "
            f"적중경주수: {int(track.get('hit_races', 0) or 0)}  "
            f"적중율: {_calc_hit_rate(track.get('hit_races', 0), track.get('total_races', 0)):.3f}  "
            f"총베팅액: {float(track.get('total_bet', 0.0) or 0.0):,.0f}원  "
            f"총환수액: {float(track.get('total_refund', 0.0) or 0.0):,.0f}원  "
            f"이익금액: {float(track.get('total_profit', 0.0) or 0.0):,.0f}원  "
            f"환수율: {float(track.get('roi', 0.0) or 0.0):.3f}"
        )
        for method in track.get("methods") or []:
            amount = float(method.get("amount", 0.0) or 0.0)
            refund = float(method.get("refund", 0.0) or 0.0)
            roi = (refund / amount) if amount > 0 else 0.0
            print(
                f"  [{method.get('label')}]  적중: {int(method.get('hits', 0) or 0)}  "
                f"적중율: {_calc_hit_rate(method.get('hits', 0), track.get('total_races', 0)):.3f}  "
                f"구멍수: {int(method.get('holes_per_race', 0) or 0)}  "
                f"베팅: {amount:,.0f}원  환수: {refund:,.0f}원  "
                f"이익: {float(method.get('profit', 0.0) or 0.0):,.0f}원  "
                f"환수율: {roi:.3f}"
            )

    if combined_total:
        holes_text = (
            f"  구멍수: {int(combined_total.get('total_holes_per_race') or 0)}"
            if combined_total.get("total_holes_per_race") is not None
            else ""
        )
        print(
            f"[서울부산 통합]  경주수: {int(combined_total.get('total_races', 0) or 0)}  "
            f"적중경주수: {int(combined_total.get('hit_races', 0) or 0)}  "
            f"적중율: {_calc_hit_rate(combined_total.get('hit_races', 0), combined_total.get('total_races', 0)):.3f}  "
            f"총베팅액: {float(combined_total.get('total_bet', 0.0) or 0.0):,.0f}원  "
            f"총환수액: {float(combined_total.get('total_refund', 0.0) or 0.0):,.0f}원  "
            f"이익금액: {float(combined_total.get('total_profit', 0.0) or 0.0):,.0f}원  "
            f"환수율: {float(combined_total.get('roi', 0.0) or 0.0):.3f}"
            f"{holes_text}"
        )
    if combined_methods:
        print("[베팅방법별 통합]")
        for method in combined_methods:
            amount = float(method.get("amount", 0.0) or 0.0)
            refund = float(method.get("refund", 0.0) or 0.0)
            print(
                f"  [{method.get('label')}]  적중: {int(method.get('hits', 0) or 0)}  "
                f"적중율: {_calc_hit_rate(method.get('hits', 0), combined_total.get('total_races', 0) if combined_total else 0):.3f}  "
                f"구멍수: {int(method.get('holes_per_race', 0) or 0) if method.get('holes_per_race') is not None else 0}  "
                f"베팅: {amount:,.0f}원  환수: {refund:,.0f}원  "
                f"이익: {float(method.get('profit', 0.0) or 0.0):,.0f}원  "
                f"환수율: {float(method.get('roi', 0.0) or 0.0):.3f}"
            )


def save_payload_df(payload: dict, output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """관리자 수익 분석 payload를 CSV로 저장한다."""
    df = flatten_payload_to_df(payload)
    if df.empty:
        return
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"▶ {PROFILE_NAME} 관리자 수익 분석 CSV 저장: {output_path}")


def _apply_max_odds_cap_to_refunds(
    race_df: pd.DataFrame,
    admin_profit_strategy_result_columns: dict,
    admin_profit_strategy_labels: dict,
    bet_unit: int = 100,
    max_display_odds: float = MAX_DISPLAY_ODDS,
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df

    race_df = race_df.copy()
    trio_odds = (
        pd.to_numeric(race_df.get("삼복승식배당율"), errors="coerce")
        .clip(upper=max_display_odds)
    )
    trifecta_odds = (
        pd.to_numeric(race_df.get("삼쌍승식배당율"), errors="coerce")
        .clip(upper=max_display_odds)
    )
    race_df["삼복승식배당율"] = trio_odds
    race_df["삼쌍승식배당율"] = trifecta_odds
    for key, column_meta in admin_profit_strategy_result_columns.items():
        hit_col = column_meta.get("hit")
        refund_col = column_meta.get("refund")
        if not hit_col or not refund_col or hit_col not in race_df.columns:
            continue
        label = str(admin_profit_strategy_labels.get(key, "") or "")
        if "삼복" in label:
            odds = trio_odds
        elif "삼쌍" in label:
            odds = trifecta_odds
        else:
            continue
        hit_mask = (
            pd.to_numeric(race_df[hit_col], errors="coerce")
            .fillna(0)
            .gt(0)
            .astype(int)
        )
        refund_values = (odds.fillna(0.0) * bet_unit * hit_mask).astype(float)
        race_df[refund_col] = refund_values
        derived_refund_col = str(hit_col).replace("적중", "환수액")
        if derived_refund_col in race_df.columns:
            race_df[derived_refund_col] = refund_values
    return race_df


def _parse_gate_list(value) -> list[int]:
    if pd.isna(value):
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, (list, tuple, set)):
        parts = list(value)
    else:
        parts = [value]
    parsed = []
    for part in parts:
        try:
            parsed.append(int(part))
        except (TypeError, ValueError):
            continue
    return parsed


def _augment_top3pair_46_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~3_복조_4~6_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 18 * bet_unit  # P(3,2) * 3

    def _calc_row(row: pd.Series) -> pd.Series:
        top1_3 = _parse_gate_list(row.get("r_pop_top3_마번"))
        top4_6 = _parse_gate_list(row.get("4~6_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top1_3_set = set(top1_3)
        top4_6_set = set(top4_6)
        valid = len(top1_3) == 3 and len(top4_6) == 3
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] in top1_3_set
            and actual_top3[1] in top1_3_set
            and actual_top3[0] != actual_top3[1]
            and actual_top3[2] in top4_6_set
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1~3_복조_4~6_삼쌍_적중": hit,
                "r_pop1~3_복조_4~6_삼쌍_환수액": refund,
                "1~3복조_4~6_삼쌍_베팅액": bet,
                "1~3복조_4~6_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor1_26_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~6_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 20 * bet_unit  # 5P2

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor_list = _parse_gate_list(row.get("축마"))
        anchor_gate = anchor_list[0] if anchor_list else None
        top2_6 = _parse_gate_list(row.get("2~6_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        valid = anchor_gate is not None and len(top2_6) == 5
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor_gate
            and actual_top3[1] in top2_6
            and actual_top3[2] in top2_6
            and actual_top3[1] != actual_top3[2]
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_축_2~6_삼쌍_적중": hit,
                "r_pop1_축_2~6_삼쌍_환수액": refund,
                "1축_2~6_삼쌍_베팅액": bet,
                "1축_2~6_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor2_38_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_축_3~8_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 30 * bet_unit  # 6P2

    def _calc_row(row: pd.Series) -> pd.Series:
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_8 = top3_8_12[:6]
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top3_8_set = set(top3_8)
        valid = second_anchor_gate is not None and len(top3_8) == 6
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == second_anchor_gate
            and actual_top3[1] in top3_8_set
            and actual_top3[2] in top3_8_set
            and actual_top3[1] != actual_top3[2]
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop2_축_3~8_삼쌍_적중": hit,
                "r_pop2_축_3~8_삼쌍_환수액": refund,
                "2축_3~8_삼쌍_베팅액": bet,
                "2축_3~8_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor2_37_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_축_3~7_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 20 * bet_unit  # 5P2

    def _calc_row(row: pd.Series) -> pd.Series:
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_7 = top3_8_12[:5]
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top3_7_set = set(top3_7)
        valid = second_anchor_gate is not None and len(top3_7) == 5
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == second_anchor_gate
            and actual_top3[1] in top3_7_set
            and actual_top3[2] in top3_7_set
            and actual_top3[1] != actual_top3[2]
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop2_축_3~7_삼쌍_적중": hit,
                "r_pop2_축_3~7_삼쌍_환수액": refund,
                "2축_3~7_삼쌍_베팅액": bet,
                "2축_3~7_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor2_36_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_축_3~6_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 12 * bet_unit  # 4P2

    def _calc_row(row: pd.Series) -> pd.Series:
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_6 = top3_8_12[:4]
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top3_6_set = set(top3_6)
        valid = second_anchor_gate is not None and len(top3_6) == 4
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == second_anchor_gate
            and actual_top3[1] in top3_6_set
            and actual_top3[2] in top3_6_set
            and actual_top3[1] != actual_top3[2]
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop2_축_3~6_삼쌍_적중": hit,
                "r_pop2_축_3~6_삼쌍_환수액": refund,
                "2축_3~6_삼쌍_베팅액": bet,
                "2축_3~6_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor2_137_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_축_1,3~7_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 30 * bet_unit  # 6P2

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_7 = top3_8_12[:5]
        candidate_gates = (
            [anchor1_gate] + top3_7 if anchor1_gate is not None else top3_7
        )
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        candidate_set = set(candidate_gates)
        valid = (
            second_anchor_gate is not None
            and anchor1_gate is not None
            and len(top3_7) == 5
            and len(candidate_set) == 6
            and second_anchor_gate not in candidate_set
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == second_anchor_gate
            and actual_top3[1] in candidate_set
            and actual_top3[2] in candidate_set
            and actual_top3[1] != actual_top3[2]
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop2_축_1,3~7_삼쌍_적중": hit,
                "r_pop2_축_1,3~7_삼쌍_환수액": refund,
                "2축_1,3~7_삼쌍_베팅액": bet,
                "2축_1,3~7_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor2_136_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_축_1,3~6_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 20 * bet_unit  # 5P2

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_6 = top3_8_12[:4]
        candidate_gates = (
            [anchor1_gate] + top3_6 if anchor1_gate is not None else top3_6
        )
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        candidate_set = set(candidate_gates)
        valid = (
            second_anchor_gate is not None
            and anchor1_gate is not None
            and len(top3_6) == 4
            and len(candidate_set) == 5
            and second_anchor_gate not in candidate_set
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == second_anchor_gate
            and actual_top3[1] in candidate_set
            and actual_top3[2] in candidate_set
            and actual_top3[1] != actual_top3[2]
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop2_축_1,3~6_삼쌍_적중": hit,
                "r_pop2_축_1,3~6_삼쌍_환수액": refund,
                "2축_1,3~6_삼쌍_베팅액": bet,
                "2축_1,3~6_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor1_27_trio(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~7_삼복_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 15 * bet_unit  # C(6,2)

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_7 = top3_8_12[:5]
        candidate_gates = (
            [second_anchor_gate] + top3_7 if second_anchor_gate is not None else top3_7
        )
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        trio_odds = pd.to_numeric(row.get("삼복승식배당율"), errors="coerce")

        actual_set = set(actual_top3)
        candidate_set = set(candidate_gates)
        valid = (
            anchor1_gate is not None
            and second_anchor_gate is not None
            and len(top3_7) == 5
            and len(candidate_set) == 6
            and anchor1_gate not in candidate_set
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and anchor1_gate in actual_set
            and len(actual_set & candidate_set) == 2
        )
        refund = (
            float(trio_odds) * bet_unit if hit == 1 and pd.notna(trio_odds) else 0.0
        )
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_축_2~7_삼복_적중": hit,
                "r_pop1_축_2~7_삼복_환수액": refund,
                "1축_2~7_삼복_베팅액": bet,
                "1축_2~7_삼복_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor1_26_trio(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~6_삼복_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 10 * bet_unit  # C(5,2)

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_6 = top3_8_12[:4]
        candidate_gates = (
            [second_anchor_gate] + top3_6 if second_anchor_gate is not None else top3_6
        )
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        trio_odds = pd.to_numeric(row.get("삼복승식배당율"), errors="coerce")

        actual_set = set(actual_top3)
        candidate_set = set(candidate_gates)
        valid = (
            anchor1_gate is not None
            and second_anchor_gate is not None
            and len(top3_6) == 4
            and len(candidate_set) == 5
            and anchor1_gate not in candidate_set
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and anchor1_gate in actual_set
            and len(actual_set & candidate_set) == 2
        )
        refund = (
            float(trio_odds) * bet_unit if hit == 1 and pd.notna(trio_odds) else 0.0
        )
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_축_2~6_삼복_적중": hit,
                "r_pop1_축_2~6_삼복_환수액": refund,
                "1축_2~6_삼복_베팅액": bet,
                "1축_2~6_삼복_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_top4_box_trio(race_df: pd.DataFrame, bet_unit: int = 100) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~4_4복조_삼복_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 4 * bet_unit  # C(4,3)

    def _calc_row(row: pd.Series) -> pd.Series:
        top4 = _parse_gate_list(row.get("r_pop_top4_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        trio_odds = pd.to_numeric(row.get("삼복승식배당율"), errors="coerce")

        top4_set = set(top4)
        actual_set = set(actual_top3)
        valid = len(top4) == 4 and len(actual_top3) == 3
        hit = int(valid and actual_set.issubset(top4_set))
        refund = (
            float(trio_odds) * bet_unit if hit == 1 and pd.notna(trio_odds) else 0.0
        )
        bet = float(bet_per_race) if len(top4) == 4 else 0.0
        return pd.Series(
            {
                "r_pop1~4_4복조_삼복_적중": hit,
                "r_pop1~4_4복조_삼복_환수액": refund,
                "1~4_4복조_삼복_베팅액": bet,
                "1~4_4복조_삼복_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor1_24_trio(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~4_삼복_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 3 * bet_unit  # C(3,2)

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_4 = top3_8_12[:2]
        candidate_gates = (
            [second_anchor_gate] + top3_4 if second_anchor_gate is not None else top3_4
        )
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        trio_odds = pd.to_numeric(row.get("삼복승식배당율"), errors="coerce")

        actual_set = set(actual_top3)
        candidate_set = set(candidate_gates)
        valid = (
            anchor1_gate is not None
            and second_anchor_gate is not None
            and len(top3_4) == 2
            and len(candidate_set) == 3
            and anchor1_gate not in candidate_set
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and anchor1_gate in actual_set
            and len(actual_set & candidate_set) == 2
        )
        refund = (
            float(trio_odds) * bet_unit if hit == 1 and pd.notna(trio_odds) else 0.0
        )
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_축_2~4_삼복_적중": hit,
                "r_pop1_축_2~4_삼복_환수액": refund,
                "1축_2~4_삼복_베팅액": bet,
                "1축_2~4_삼복_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor1_25_trio(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_축_2~5_삼복_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 6 * bet_unit  # C(4,2)

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_5 = top3_8_12[:3]
        candidate_gates = (
            [second_anchor_gate] + top3_5 if second_anchor_gate is not None else top3_5
        )
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        trio_odds = pd.to_numeric(row.get("삼복승식배당율"), errors="coerce")

        actual_set = set(actual_top3)
        candidate_set = set(candidate_gates)
        valid = (
            anchor1_gate is not None
            and second_anchor_gate is not None
            and len(top3_5) == 3
            and len(candidate_set) == 4
            and anchor1_gate not in candidate_set
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and anchor1_gate in actual_set
            and len(actual_set & candidate_set) == 2
        )
        refund = (
            float(trio_odds) * bet_unit if hit == 1 and pd.notna(trio_odds) else 0.0
        )
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_축_2~5_삼복_적중": hit,
                "r_pop1_축_2~5_삼복_환수액": refund,
                "1축_2~5_삼복_베팅액": bet,
                "1축_2~5_삼복_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor12_3_12_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_1축_r_pop2_2축_3~12_적중" in race_df.columns:
        return race_df

    df = race_df.copy()

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_12 = _parse_gate_list(row.get("3~12_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top3_12_set = set(top3_12)
        valid = (
            anchor1_gate is not None
            and second_anchor_gate is not None
            and len(top3_12) >= 1
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor1_gate
            and actual_top3[1] == second_anchor_gate
            and actual_top3[2] in top3_12_set
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(len(top3_12) * bet_unit) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_1축_r_pop2_2축_3~12_적중": hit,
                "r_pop1_1축_r_pop2_2축_3~12_환수액": refund,
                "1축_2축_3~12_베팅액": bet,
                "1축_2축_3~12_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor21_3_12_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_1축_r_pop1_2축_3~12_적중" in race_df.columns:
        return race_df

    df = race_df.copy()

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        pop1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        pop2_gate = second_anchor_list[0] if second_anchor_list else None
        top3_12 = _parse_gate_list(row.get("3~12_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top3_12_set = set(top3_12)
        valid = pop1_gate is not None and pop2_gate is not None and len(top3_12) >= 1
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == pop2_gate
            and actual_top3[1] == pop1_gate
            and actual_top3[2] in top3_12_set
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(len(top3_12) * bet_unit) if valid else 0.0
        return pd.Series(
            {
                "r_pop2_1축_r_pop1_2축_3~12_적중": hit,
                "r_pop2_1축_r_pop1_2축_3~12_환수액": refund,
                "2를1축_1을2축_3~12_베팅액": bet,
                "2를1축_1을2축_3~12_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor21_3_10_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop2_1축_r_pop1_2축_3~10_적중" in race_df.columns:
        return race_df

    df = race_df.copy()

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        pop1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        pop2_gate = second_anchor_list[0] if second_anchor_list else None
        top3_10 = _parse_gate_list(row.get("3~10_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top3_10_set = set(top3_10)
        valid = pop1_gate is not None and pop2_gate is not None and len(top3_10) >= 1
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == pop2_gate
            and actual_top3[1] == pop1_gate
            and actual_top3[2] in top3_10_set
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(len(top3_10) * bet_unit) if valid else 0.0
        return pd.Series(
            {
                "r_pop2_1축_r_pop1_2축_3~10_적중": hit,
                "r_pop2_1축_r_pop1_2축_3~10_환수액": refund,
                "2를1축_1을2축_3~10_베팅액": bet,
                "2를1축_1을2축_3~10_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor12_3_10_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_1축_r_pop2_2축_3~10_적중" in race_df.columns:
        return race_df

    df = race_df.copy()

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_10 = _parse_gate_list(row.get("3~10_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top3_10_set = set(top3_10)
        valid = (
            anchor1_gate is not None
            and second_anchor_gate is not None
            and len(top3_10) >= 1
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor1_gate
            and actual_top3[1] == second_anchor_gate
            and actual_top3[2] in top3_10_set
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(len(top3_10) * bet_unit) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_1축_r_pop2_2축_3~10_적중": hit,
                "r_pop1_1축_r_pop2_2축_3~10_환수액": refund,
                "1축_2축_3~10_베팅액": bet,
                "1축_2축_3~10_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_anchor12_3_8_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1_1축_r_pop2_2축_3~8_적중" in race_df.columns:
        return race_df

    df = race_df.copy()

    def _calc_row(row: pd.Series) -> pd.Series:
        anchor1_list = _parse_gate_list(row.get("축마"))
        anchor1_gate = anchor1_list[0] if anchor1_list else None
        second_anchor_list = _parse_gate_list(row.get("2축마"))
        second_anchor_gate = second_anchor_list[0] if second_anchor_list else None
        top3_8_12 = _parse_gate_list(row.get("3~8,12_마번"))
        top3_8 = top3_8_12[:6]
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top3_8_set = set(top3_8)
        valid = (
            anchor1_gate is not None
            and second_anchor_gate is not None
            and len(top3_8) == 6
        )
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] == anchor1_gate
            and actual_top3[1] == second_anchor_gate
            and actual_top3[2] in top3_8_set
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(len(top3_8) * bet_unit) if valid else 0.0
        return pd.Series(
            {
                "r_pop1_1축_r_pop2_2축_3~8_적중": hit,
                "r_pop1_1축_r_pop2_2축_3~8_환수액": refund,
                "1축_2축_3~8_베팅액": bet,
                "1축_2축_3~8_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_top4pair_56_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~4_복조_5~6_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 24 * bet_unit  # P(4,2) * 2

    def _calc_row(row: pd.Series) -> pd.Series:
        top4 = _parse_gate_list(row.get("r_pop_top4_마번"))
        top6 = _parse_gate_list(row.get("r_pop_top6_마번"))
        top5_6 = top6[4:6] if len(top6) >= 6 else []
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top4_set = set(top4)
        top5_6_set = set(top5_6)
        valid = len(top4) == 4 and len(top5_6) == 2
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] in top4_set
            and actual_top3[1] in top4_set
            and actual_top3[0] != actual_top3[1]
            and actual_top3[2] in top5_6_set
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1~4_복조_5~6_삼쌍_적중": hit,
                "r_pop1~4_복조_5~6_삼쌍_환수액": refund,
                "1~4복조_5~6_삼쌍_베팅액": bet,
                "1~4복조_5~6_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_top4pair_57_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~4_복조_5~7_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 36 * bet_unit  # P(4,2) * 3

    def _calc_row(row: pd.Series) -> pd.Series:
        top4 = _parse_gate_list(row.get("r_pop_top4_마번"))
        top5_7 = _parse_gate_list(row.get("5~7_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        top4_set = set(top4)
        top5_7_set = set(top5_7)
        valid = len(top4) == 4 and len(top5_7) == 3
        hit = int(
            valid
            and len(actual_top3) == 3
            and actual_top3[0] in top4_set
            and actual_top3[1] in top4_set
            and actual_top3[0] != actual_top3[1]
            and actual_top3[2] in top5_7_set
        )
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1~4_복조_5~7_삼쌍_적중": hit,
                "r_pop1~4_복조_5~7_삼쌍_환수액": refund,
                "1~4복조_5~7_삼쌍_베팅액": bet,
                "1~4복조_5~7_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_top4pair_57_trio(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~4_복조_5~7_삼복_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 18 * bet_unit  # C(4,2) * 3

    def _calc_row(row: pd.Series) -> pd.Series:
        top4 = _parse_gate_list(row.get("r_pop_top4_마번"))
        top5_7 = _parse_gate_list(row.get("5~7_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        trio_odds = pd.to_numeric(row.get("삼복승식배당율"), errors="coerce")

        actual_set = set(actual_top3)
        top4_set = set(top4)
        top5_7_set = set(top5_7)
        valid = len(top4) == 4 and len(top5_7) == 3
        hit = int(
            valid
            and len(actual_top3) == 3
            and len(actual_set & top4_set) == 2
            and len(actual_set & top5_7_set) == 1
        )
        refund = (
            float(trio_odds) * bet_unit if hit == 1 and pd.notna(trio_odds) else 0.0
        )
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1~4_복조_5~7_삼복_적중": hit,
                "r_pop1~4_복조_5~7_삼복_환수액": refund,
                "1~4복조_5~7_삼복_베팅액": bet,
                "1~4복조_5~7_삼복_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_top4pair_56_trio(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~4_복조_5~6_삼복_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 12 * bet_unit  # C(4,2) * 2

    def _calc_row(row: pd.Series) -> pd.Series:
        top4 = _parse_gate_list(row.get("r_pop_top4_마번"))
        top6 = _parse_gate_list(row.get("r_pop_top6_마번"))
        top5_6 = top6[4:6] if len(top6) >= 6 else []
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        trio_odds = pd.to_numeric(row.get("삼복승식배당율"), errors="coerce")

        actual_set = set(actual_top3)
        top4_set = set(top4)
        top5_6_set = set(top5_6)
        valid = len(top4) == 4 and len(top5_6) == 2
        hit = int(
            valid
            and len(actual_top3) == 3
            and len(actual_set & top4_set) == 2
            and len(actual_set & top5_6_set) == 1
        )
        refund = (
            float(trio_odds) * bet_unit if hit == 1 and pd.notna(trio_odds) else 0.0
        )
        bet = float(bet_per_race) if valid else 0.0
        return pd.Series(
            {
                "r_pop1~4_복조_5~6_삼복_적중": hit,
                "r_pop1~4_복조_5~6_삼복_환수액": refund,
                "1~4복조_5~6_삼복_베팅액": bet,
                "1~4복조_5~6_삼복_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_top4_box_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~4_4복_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 24 * bet_unit  # 4P3

    def _calc_row(row: pd.Series) -> pd.Series:
        top4 = _parse_gate_list(row.get("r_pop_top4_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        valid = len(top4) == 4 and len(actual_top3) == 3
        hit = int(valid and len(set(actual_top3)) == 3 and set(actual_top3).issubset(set(top4)))
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if len(top4) == 4 else 0.0
        return pd.Series(
            {
                "r_pop1~4_4복_적중": hit,
                "r_pop1~4_4복_환수액": refund,
                "1~4_4복_베팅액": bet,
                "1~4_4복_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def _augment_top6_box_trifecta(
    race_df: pd.DataFrame, bet_unit: int = 100
) -> pd.DataFrame:
    if race_df is None or race_df.empty:
        return race_df
    if "r_pop1~6_6복조_삼쌍_적중" in race_df.columns:
        return race_df

    df = race_df.copy()
    bet_per_race = 120 * bet_unit  # 6P3

    def _calc_row(row: pd.Series) -> pd.Series:
        top6 = _parse_gate_list(row.get("r_pop_top6_마번"))
        actual_top3 = _parse_gate_list(row.get("실제_top3_마번"))
        odds = pd.to_numeric(row.get("삼쌍승식배당율"), errors="coerce")

        valid = len(top6) == 6 and len(actual_top3) == 3
        hit = int(valid and len(set(actual_top3)) == 3 and set(actual_top3).issubset(set(top6)))
        refund = float(odds) * bet_unit if hit == 1 and pd.notna(odds) else 0.0
        bet = float(bet_per_race) if len(top6) == 6 else 0.0
        return pd.Series(
            {
                "r_pop1~6_6복조_삼쌍_적중": hit,
                "r_pop1~6_6복조_삼쌍_환수액": refund,
                "1~6_6복조_삼쌍_베팅액": bet,
                "1~6_6복조_삼쌍_환수액": refund,
            }
        )

    added = df.apply(_calc_row, axis=1)
    for col in added.columns:
        df[col] = added[col]
    return df


def build_admin_profit_analysis_payload_for_range(
    from_date: str, to_date: str, use_odds_cap: bool = True
) -> dict:
    """관리자 수익 분석과 같은 방식으로 기간 지정 payload를 만든다."""
    from django.db import connection
    from apps.core.views import (
        ADMIN_PROFIT_GROUPS,
        ADMIN_PROFIT_STRATEGY_LABELS,
        ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS,
        _filter_race_df_for_admin_profit_trio_odds,
        _run_calc_rpop_anchor_26_trifecta_quietly,
    )

    admin_profit_groups = copy.deepcopy(ADMIN_PROFIT_GROUPS)
    admin_profit_strategy_result_columns = copy.deepcopy(
        ADMIN_PROFIT_STRATEGY_RESULT_COLUMNS
    )
    admin_profit_strategy_labels = copy.deepcopy(ADMIN_PROFIT_STRATEGY_LABELS)

    admin_profit_strategy_result_columns["top3pair_46_trifecta"] = {
        "bet": "1~3복조_4~6_삼쌍_베팅액",
        "refund": "1~3복조_4~6_삼쌍_환수액",
        "hit": "r_pop1~3_복조_4~6_삼쌍_적중",
        "holes_per_race": 18,
    }
    admin_profit_strategy_labels["top3pair_46_trifecta"] = "1~3 복조 / 4~6 삼쌍"
    admin_profit_strategy_result_columns["top4_box_trifecta"] = {
        "bet": "1~4_4복_베팅액",
        "refund": "1~4_4복_환수액",
        "hit": "r_pop1~4_4복_적중",
        "holes_per_race": 24,
    }
    admin_profit_strategy_labels["top4_box_trifecta"] = "1~4 4복조 삼쌍"
    admin_profit_strategy_result_columns["anchor1_26"] = {
        "bet": "1축_2~6_삼쌍_베팅액",
        "refund": "1축_2~6_삼쌍_환수액",
        "hit": "r_pop1_축_2~6_삼쌍_적중",
        "holes_per_race": 20,
    }
    admin_profit_strategy_labels["anchor1_26"] = "1축(2~6) 삼쌍"
    admin_profit_strategy_result_columns["anchor2_38_trifecta"] = {
        "bet": "2축_3~8_삼쌍_베팅액",
        "refund": "2축_3~8_삼쌍_환수액",
        "hit": "r_pop2_축_3~8_삼쌍_적중",
        "holes_per_race": 30,
    }
    admin_profit_strategy_labels["anchor2_38_trifecta"] = "2축(3~8) 삼쌍"
    admin_profit_strategy_result_columns["anchor2_37_trifecta"] = {
        "bet": "2축_3~7_삼쌍_베팅액",
        "refund": "2축_3~7_삼쌍_환수액",
        "hit": "r_pop2_축_3~7_삼쌍_적중",
        "holes_per_race": 20,
    }
    admin_profit_strategy_labels["anchor2_37_trifecta"] = "2축(3~7) 삼쌍"
    admin_profit_strategy_result_columns["anchor2_36_trifecta"] = {
        "bet": "2축_3~6_삼쌍_베팅액",
        "refund": "2축_3~6_삼쌍_환수액",
        "hit": "r_pop2_축_3~6_삼쌍_적중",
        "holes_per_race": 12,
    }
    admin_profit_strategy_labels["anchor2_36_trifecta"] = "2축(3~6) 삼쌍"
    admin_profit_strategy_result_columns["anchor2_137_trifecta"] = {
        "bet": "2축_1,3~7_삼쌍_베팅액",
        "refund": "2축_1,3~7_삼쌍_환수액",
        "hit": "r_pop2_축_1,3~7_삼쌍_적중",
        "holes_per_race": 30,
    }
    admin_profit_strategy_labels["anchor2_137_trifecta"] = "2축(1,3~7) 삼쌍"
    admin_profit_strategy_result_columns["anchor2_136_trifecta"] = {
        "bet": "2축_1,3~6_삼쌍_베팅액",
        "refund": "2축_1,3~6_삼쌍_환수액",
        "hit": "r_pop2_축_1,3~6_삼쌍_적중",
        "holes_per_race": 20,
    }
    admin_profit_strategy_labels["anchor2_136_trifecta"] = "2축(1,3~6) 삼쌍"
    admin_profit_strategy_result_columns["anchor1_27_trio"] = {
        "bet": "1축_2~7_삼복_베팅액",
        "refund": "1축_2~7_삼복_환수액",
        "hit": "r_pop1_축_2~7_삼복_적중",
        "holes_per_race": 15,
    }
    admin_profit_strategy_labels["anchor1_27_trio"] = "1축(2~7) 삼복"
    admin_profit_strategy_result_columns["anchor1_26_trio"] = {
        "bet": "1축_2~6_삼복_베팅액",
        "refund": "1축_2~6_삼복_환수액",
        "hit": "r_pop1_축_2~6_삼복_적중",
        "holes_per_race": 10,
    }
    admin_profit_strategy_labels["anchor1_26_trio"] = "1축(2~6) 삼복"
    admin_profit_strategy_result_columns["top4_box_trio"] = {
        "bet": "1~4_4복조_삼복_베팅액",
        "refund": "1~4_4복조_삼복_환수액",
        "hit": "r_pop1~4_4복조_삼복_적중",
        "holes_per_race": 4,
    }
    admin_profit_strategy_labels["top4_box_trio"] = "1~4 4복조 삼복"
    admin_profit_strategy_result_columns["top5_box_trifecta"] = {
        "bet": "1~5_5복_베팅액",
        "refund": "1~5_5복_환수액",
        "hit": "r_pop1~5_5복_적중",
        "holes_per_race": 60,
    }
    admin_profit_strategy_labels["top5_box_trifecta"] = "1~5 5복조 삼쌍"
    admin_profit_strategy_result_columns["top6_box_trifecta"] = {
        "bet": "1~6_6복조_삼쌍_베팅액",
        "refund": "1~6_6복조_삼쌍_환수액",
        "hit": "r_pop1~6_6복조_삼쌍_적중",
        "holes_per_race": 120,
    }
    admin_profit_strategy_labels["top6_box_trifecta"] = "1~6 6복조 삼쌍"
    admin_profit_strategy_result_columns["top12anchor_3_12_trio"] = {
        "bet": "1~2_복조축_3~12_삼복_베팅액",
        "refund": "1~2_복조축_3~12_삼복_환수액",
        "hit": "r_pop1~2_복조축_3~12_삼복_적중",
        "holes_per_race": 10,
    }
    admin_profit_strategy_labels["top12anchor_3_12_trio"] = "1축 2축 / 3~12 삼복"
    admin_profit_strategy_labels["anchor1_24"] = "1축(2~4) 삼쌍"
    admin_profit_strategy_labels["anchor1_25"] = "1축(2~5) 삼쌍"
    admin_profit_strategy_result_columns["anchor1_25_68"] = {
        "bet": "1축_2~5_6~8_베팅액",
        "refund": "1축_2~5_6~8_환수액",
        "hit": "r_pop1_축_2~5_6~8_적중",
        "holes_per_race": 12,
    }
    admin_profit_strategy_labels["anchor1_25_68"] = "1축(2~5) / 6~8 삼쌍"
    admin_profit_strategy_result_columns["anchor1_25_69"] = {
        "bet": "1축_2~5_6~9_베팅액",
        "refund": "1축_2~5_6~9_환수액",
        "hit": "r_pop1_축_2~5_6~9_적중",
        "holes_per_race": 16,
    }
    admin_profit_strategy_labels["anchor1_25_69"] = "1축(2~5) / 6~9 삼쌍"
    admin_profit_strategy_result_columns["anchor1_24_trio"] = {
        "bet": "1축_2~4_삼복_베팅액",
        "refund": "1축_2~4_삼복_환수액",
        "hit": "r_pop1_축_2~4_삼복_적중",
        "holes_per_race": 3,
    }
    admin_profit_strategy_labels["anchor1_24_trio"] = "1축(2~4) 삼복"
    admin_profit_strategy_result_columns["anchor1_25_trio"] = {
        "bet": "1축_2~5_삼복_베팅액",
        "refund": "1축_2~5_삼복_환수액",
        "hit": "r_pop1_축_2~5_삼복_적중",
        "holes_per_race": 6,
    }
    admin_profit_strategy_labels["anchor1_25_trio"] = "1축(2~5) 삼복"
    admin_profit_strategy_result_columns["anchor12_3_12_trifecta"] = {
        "bet": "1축_2축_3~12_베팅액",
        "refund": "1축_2축_3~12_환수액",
        "hit": "r_pop1_1축_r_pop2_2축_3~12_적중",
        "holes_per_race": 10,
    }
    admin_profit_strategy_labels["anchor12_3_12_trifecta"] = "1축 2축 / 3~12 삼쌍"
    admin_profit_strategy_result_columns["anchor21_3_12_trifecta"] = {
        "bet": "2를1축_1을2축_3~12_베팅액",
        "refund": "2를1축_1을2축_3~12_환수액",
        "hit": "r_pop2_1축_r_pop1_2축_3~12_적중",
        "holes_per_race": 10,
    }
    admin_profit_strategy_labels["anchor21_3_12_trifecta"] = "2를1축 1을2축 / 3~12 삼쌍"
    admin_profit_strategy_result_columns["anchor21_3_10_trifecta"] = {
        "bet": "2를1축_1을2축_3~10_베팅액",
        "refund": "2를1축_1을2축_3~10_환수액",
        "hit": "r_pop2_1축_r_pop1_2축_3~10_적중",
        "holes_per_race": 8,
    }
    admin_profit_strategy_labels["anchor21_3_10_trifecta"] = "2를1축 1을2축 / 3~10 삼쌍"
    admin_profit_strategy_result_columns["anchor12_3_10_trifecta"] = {
        "bet": "1축_2축_3~10_베팅액",
        "refund": "1축_2축_3~10_환수액",
        "hit": "r_pop1_1축_r_pop2_2축_3~10_적중",
        "holes_per_race": 8,
    }
    admin_profit_strategy_labels["anchor12_3_10_trifecta"] = "1축 2축 / 3~10 삼쌍"
    admin_profit_strategy_result_columns["anchor12_3_8_trifecta"] = {
        "bet": "1축_2축_3~8_베팅액",
        "refund": "1축_2축_3~8_환수액",
        "hit": "r_pop1_1축_r_pop2_2축_3~8_적중",
        "holes_per_race": 6,
    }
    admin_profit_strategy_labels["anchor12_3_8_trifecta"] = "1축 2축 / 3~8 삼쌍"
    admin_profit_strategy_result_columns["top4pair_56_trifecta"] = {
        "bet": "1~4복조_5~6_삼쌍_베팅액",
        "refund": "1~4복조_5~6_삼쌍_환수액",
        "hit": "r_pop1~4_복조_5~6_삼쌍_적중",
        "holes_per_race": 24,
    }
    admin_profit_strategy_labels["top4pair_56_trifecta"] = "1~4 복조 / 5~6 삼쌍"
    admin_profit_strategy_result_columns["top4pair_57_trifecta"] = {
        "bet": "1~4복조_5~7_삼쌍_베팅액",
        "refund": "1~4복조_5~7_삼쌍_환수액",
        "hit": "r_pop1~4_복조_5~7_삼쌍_적중",
        "holes_per_race": 36,
    }
    admin_profit_strategy_labels["top4pair_57_trifecta"] = "1~4 복조 / 5~7 삼쌍"
    admin_profit_strategy_result_columns["top4pair_57_trio"] = {
        "bet": "1~4복조_5~7_삼복_베팅액",
        "refund": "1~4복조_5~7_삼복_환수액",
        "hit": "r_pop1~4_복조_5~7_삼복_적중",
        "holes_per_race": 18,
    }
    admin_profit_strategy_labels["top4pair_57_trio"] = "1~4 복조 / 5~7 삼복"
    admin_profit_strategy_result_columns["top4pair_56_trio"] = {
        "bet": "1~4복조_5~6_삼복_베팅액",
        "refund": "1~4복조_5~6_삼복_환수액",
        "hit": "r_pop1~4_복조_5~6_삼복_적중",
        "holes_per_race": 12,
    }
    admin_profit_strategy_labels["top4pair_56_trio"] = "1~4 복조 / 5~6 삼복"

    for track_name in ["서울", "부산"]:
        track_groups = admin_profit_groups.get(track_name, {})
        primary_keys = track_groups.get("주력베팅", [])
        if "top4_box_trifecta" not in primary_keys:
            primary_keys.append("top4_box_trifecta")
        if "anchor1_26" not in primary_keys:
            primary_keys.append("anchor1_26")
        if "anchor2_38_trifecta" not in primary_keys:
            primary_keys.append("anchor2_38_trifecta")
        if "anchor2_37_trifecta" not in primary_keys:
            primary_keys.append("anchor2_37_trifecta")
        if "anchor2_36_trifecta" not in primary_keys:
            primary_keys.append("anchor2_36_trifecta")
        if "anchor2_137_trifecta" not in primary_keys:
            primary_keys.append("anchor2_137_trifecta")
        if "anchor2_136_trifecta" not in primary_keys:
            primary_keys.append("anchor2_136_trifecta")
        if "anchor1_27_trio" not in primary_keys:
            primary_keys.append("anchor1_27_trio")
        if "anchor1_26_trio" not in primary_keys:
            primary_keys.append("anchor1_26_trio")
        if "top4_box_trio" not in primary_keys:
            primary_keys.append("top4_box_trio")
        if "top5_box_trifecta" not in primary_keys:
            primary_keys.append("top5_box_trifecta")
        if "top6_box_trifecta" not in primary_keys:
            primary_keys.append("top6_box_trifecta")
        if "top12anchor_3_12_trio" not in primary_keys:
            primary_keys.append("top12anchor_3_12_trio")
        if "anchor1_24" not in primary_keys:
            primary_keys.append("anchor1_24")
        if "anchor1_25" not in primary_keys:
            primary_keys.append("anchor1_25")
        if "anchor1_25_68" not in primary_keys:
            primary_keys.append("anchor1_25_68")
        if "anchor1_25_69" not in primary_keys:
            primary_keys.append("anchor1_25_69")
        if "anchor1_24_trio" not in primary_keys:
            primary_keys.append("anchor1_24_trio")
        if "anchor1_25_trio" not in primary_keys:
            primary_keys.append("anchor1_25_trio")
        if "anchor12_3_12_trifecta" not in primary_keys:
            primary_keys.append("anchor12_3_12_trifecta")
        if "anchor21_3_12_trifecta" not in primary_keys:
            primary_keys.append("anchor21_3_12_trifecta")
        if "anchor21_3_10_trifecta" not in primary_keys:
            primary_keys.append("anchor21_3_10_trifecta")
        if "anchor12_3_10_trifecta" not in primary_keys:
            primary_keys.append("anchor12_3_10_trifecta")
        if "anchor12_3_8_trifecta" not in primary_keys:
            primary_keys.append("anchor12_3_8_trifecta")
        if "anchor1_23_47" not in primary_keys:
            primary_keys.append("anchor1_23_47")
        if "anchor1_24_57" not in primary_keys:
            primary_keys.append("anchor1_24_57")
        if "top3pair_46_trifecta" not in primary_keys:
            primary_keys.append("top3pair_46_trifecta")
        if "top4pair_56_trifecta" not in primary_keys:
            primary_keys.append("top4pair_56_trifecta")
        if "top4pair_57_trifecta" not in primary_keys:
            primary_keys.append("top4pair_57_trifecta")
        if "top4pair_57_trio" not in primary_keys:
            primary_keys.append("top4pair_57_trio")
        if "top4pair_56_trio" not in primary_keys:
            primary_keys.append("top4pair_56_trio")
        track_groups.pop("보조베팅", None)

    selected_primary_keys = [
        "top4pair_56_trio",
        "anchor1_23_46",
        "anchor1_23_47",
        "anchor1_24_57",
        "anchor1_24_58",
        "anchor1_25",
        "anchor1_26",
        "anchor1_57_24",
        "anchor1_58_24",
        "anchor2_37_trifecta",
    ]
    for track_name in ["서울", "부산"]:
        admin_profit_groups.setdefault(track_name, {})["주력베팅"] = list(
            selected_primary_keys
        )
        admin_profit_groups[track_name].pop("보조베팅", None)

    summary_total = None
    method_bet_by_track = []
    metrics = {"roi": 0.0, "roi_pct": 0.0}

    try:
        race_df, _summary = _run_calc_rpop_anchor_26_trifecta_quietly(
            from_date=from_date,
            to_date=to_date,
            bet_unit=100,
            apply_odds_filter=False,
        )
    except Exception as exc:
        print(f"[admin_profit_analysis_range] calc failed: {exc}")
        race_df = None

    if race_df is not None and hasattr(race_df, "columns") and not race_df.empty:
        race_df = _filter_race_df_for_admin_profit_trio_odds(race_df)
        race_df = _augment_top3pair_46_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor1_26_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor2_38_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor2_37_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor2_36_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor2_137_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor2_136_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor1_27_trio(race_df, bet_unit=100)
        race_df = _augment_anchor1_26_trio(race_df, bet_unit=100)
        race_df = _augment_top4_box_trio(race_df, bet_unit=100)
        race_df = _augment_anchor1_24_trio(race_df, bet_unit=100)
        race_df = _augment_anchor1_25_trio(race_df, bet_unit=100)
        race_df = _augment_anchor12_3_12_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor21_3_12_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor21_3_10_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor12_3_10_trifecta(race_df, bet_unit=100)
        race_df = _augment_anchor12_3_8_trifecta(race_df, bet_unit=100)
        race_df = _augment_top4pair_56_trifecta(race_df, bet_unit=100)
        race_df = _augment_top4pair_57_trifecta(race_df, bet_unit=100)
        race_df = _augment_top4pair_57_trio(race_df, bet_unit=100)
        race_df = _augment_top4pair_56_trio(race_df, bet_unit=100)
        race_df = _augment_top4_box_trifecta(race_df, bet_unit=100)
        race_df = _augment_top6_box_trifecta(race_df, bet_unit=100)
        if use_odds_cap:
            race_df = _apply_max_odds_cap_to_refunds(
                race_df,
                admin_profit_strategy_result_columns,
                admin_profit_strategy_labels,
                bet_unit=100,
                max_display_odds=MAX_DISPLAY_ODDS,
            )
        valid_race_keys = set()
        if not race_df.empty and {"경마장", "경주일", "경주번호"}.issubset(
            race_df.columns
        ):
            valid_race_keys = {
                (str(row[0] or "").strip(), str(row[1]), int(row[2]))
                for row in race_df[["경마장", "경주일", "경주번호"]].itertuples(
                    index=False, name=None
                )
            }
        if race_df.empty:
            race_df = None
    else:
        valid_race_keys = set()

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

            for group_label, strategy_keys in admin_profit_groups.get(
                track_name, {}
            ).items():
                bet_cols = []
                refund_cols = []
                hit_cols = []
                detail_methods = []
                for key in strategy_keys:
                    column_meta = admin_profit_strategy_result_columns.get(key)
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
                            "label": f"  - {admin_profit_strategy_labels.get(key, key)}",
                            "amount": bet_amount,
                            "refund": refund_amount,
                            "profit": refund_amount - bet_amount,
                            "hits": hit_count,
                            "holes_per_race": column_meta.get("holes_per_race", 0),
                        }
                    )
                detail_methods.sort(key=_method_display_sort_key)

                group_bet = float(track_df[bet_cols].sum().sum()) if bet_cols else 0.0
                group_refund = (
                    float(track_df[refund_cols].sum().sum()) if refund_cols else 0.0
                )
                group_profit = group_refund - group_bet
                group_holes_per_race = int(
                    sum(
                        admin_profit_strategy_result_columns.get(key, {}).get(
                            "holes_per_race", 0
                        )
                        for key in strategy_keys
                    )
                )
                group_hits = (
                    int(
                        track_df[hit_cols].fillna(0).astype(int).gt(0).any(axis=1).sum()
                    )
                    if hit_cols
                    else 0
                )
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
                    }
                )
                methods.extend(detail_methods)
                track_bet += group_bet
                track_refund += group_refund
                if group_label == "주력베팅":
                    primary_total_bet += group_bet
                    primary_total_refund += group_refund
                    primary_total_hits += group_hits
                    primary_total_races += track_races

            track_profit = track_refund - track_bet
            track_hit_races = 0
            if methods:
                hit_cols_all = []
                for strategy_keys in admin_profit_groups.get(track_name, {}).values():
                    for key in strategy_keys:
                        column_meta = admin_profit_strategy_result_columns.get(key)
                        if column_meta and column_meta["hit"] in track_df.columns:
                            hit_cols_all.append(column_meta["hit"])
                if hit_cols_all:
                    track_hit_races = int(
                        track_df[hit_cols_all]
                        .fillna(0)
                        .astype(int)
                        .gt(0)
                        .any(axis=1)
                        .sum()
                    )
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
                                admin_profit_strategy_result_columns.get(key, {}).get(
                                    "holes_per_race", 0
                                )
                                for groups in admin_profit_groups.get(
                                    track_name, {}
                                ).values()
                                for key in groups
                            )
                        ),
                        "hit_races": track_hit_races,
                        "roi": (track_refund / track_bet) if track_bet > 0 else 0.0,
                        "roi_pct": (
                            ((track_refund / track_bet) * 100) if track_bet > 0 else 0.0
                        ),
                        "r_pop1_top1_hits": int(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop1_top1_hits", 0
                            )
                            or 0
                        ),
                        "r_pop1_top1_rate": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop1_top1_rate", 0.0
                            )
                            or 0.0
                        ),
                        "r_pop1_top1_rate_pct": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop1_top1_rate", 0.0
                            )
                            or 0.0
                        )
                        * 100.0,
                        "r_pop1_top3_hits": int(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop1_top3_hits", 0
                            )
                            or 0
                        ),
                        "r_pop1_top3_rate": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop1_top3_rate", 0.0
                            )
                            or 0.0
                        ),
                        "r_pop1_top3_rate_pct": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop1_top3_rate", 0.0
                            )
                            or 0.0
                        )
                        * 100.0,
                        "r_pop2_top1_hits": int(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop2_top1_hits", 0
                            )
                            or 0
                        ),
                        "r_pop2_top1_rate": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop2_top1_rate", 0.0
                            )
                            or 0.0
                        ),
                        "r_pop2_top1_rate_pct": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop2_top1_rate", 0.0
                            )
                            or 0.0
                        )
                        * 100.0,
                        "r_pop2_top3_hits": int(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop2_top3_hits", 0
                            )
                            or 0
                        ),
                        "r_pop2_top3_rate": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop2_top3_rate", 0.0
                            )
                            or 0.0
                        ),
                        "r_pop2_top3_rate_pct": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop2_top3_rate", 0.0
                            )
                            or 0.0
                        )
                        * 100.0,
                        "r_pop3_top1_hits": int(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop3_top1_hits", 0
                            )
                            or 0
                        ),
                        "r_pop3_top1_rate": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop3_top1_rate", 0.0
                            )
                            or 0.0
                        ),
                        "r_pop3_top1_rate_pct": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop3_top1_rate", 0.0
                            )
                            or 0.0
                        )
                        * 100.0,
                        "r_pop3_top3_hits": int(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop3_top3_hits", 0
                            )
                            or 0
                        ),
                        "r_pop3_top3_rate": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop3_top3_rate", 0.0
                            )
                            or 0.0
                        ),
                        "r_pop3_top3_rate_pct": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop3_top3_rate", 0.0
                            )
                            or 0.0
                        )
                        * 100.0,
                        "r_pop4_top1_hits": int(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop4_top1_hits", 0
                            )
                            or 0
                        ),
                        "r_pop4_top1_rate": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop4_top1_rate", 0.0
                            )
                            or 0.0
                        ),
                        "r_pop4_top1_rate_pct": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop4_top1_rate", 0.0
                            )
                            or 0.0
                        )
                        * 100.0,
                        "r_pop4_top3_hits": int(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop4_top3_hits", 0
                            )
                            or 0
                        ),
                        "r_pop4_top3_rate": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop4_top3_rate", 0.0
                            )
                            or 0.0
                        ),
                        "r_pop4_top3_rate_pct": float(
                            track_stat_map.get(track_name, {}).get(
                                "r_pop4_top3_rate", 0.0
                            )
                            or 0.0
                        )
                        * 100.0,
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
        metrics["roi_pct"] = metrics["roi"] * 100.0

    return {
        "i_rdate": to_date,
        "from_date": from_date,
        "to_date": to_date,
        "odds_cap_label": f"{int(MAX_DISPLAY_ODDS)}캡" if use_odds_cap else "무캡",
        "summary_total": summary_total,
        "method_bet_by_track": method_bet_by_track,
        "metrics": metrics,
    }


def main() -> None:
    """관리자 수익 분석과 동일한 방식으로 기본 기간 집계한다."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "letsrace.settings")

    import django

    django.setup()

    capped_payload = build_admin_profit_analysis_payload_for_range(
        DEFAULT_FROM_DATE,
        DEFAULT_TO_DATE,
        use_odds_cap=True,
    )
    uncapped_payload = build_admin_profit_analysis_payload_for_range(
        DEFAULT_FROM_DATE,
        DEFAULT_TO_DATE,
        use_odds_cap=False,
    )

    print_payload(capped_payload)
    save_payload_df(capped_payload, DEFAULT_OUTPUT_PATH)
    print()
    print_payload(uncapped_payload)
    save_payload_df(uncapped_payload, DEFAULT_NO_CAP_OUTPUT_PATH)


if __name__ == "__main__":
    main()
