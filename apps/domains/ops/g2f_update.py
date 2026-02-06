from apps.domains.race.race_compute import f_t2s
from apps.domains.prediction.simulation2 import judge_horse_trend_7level


def g2f_update(rcity, rdate, horse, distance, connection,):
    cursor = None
    g2f_rank = "(사유 및 최근 경주 데이터 없음)"
    try:
        cursor = connection.cursor()
        strSql = """
            select %s, gate, horse, rdate '과거경주일', distance, rank, 
            
            -- i_convert '부담중량 주로상태 반영 환산기록', 
            
            ( ( i_convert )/a.distance ) * %s + 
                    ifnull( ( select adv_dist from adv_distance 
                                where rcity = %s and grade = a.grade and dist1 = %s and dist2 = a.distance ), 
            ( select ifnull(avg( adv_dist ),0) from adv_distance where rcity = %s and dist1 = %s and dist2 = a.distance ) )	,
            
            ifnull( ( (i_s1f * (i_convert ) )/i_record ), 0) +
                        ( ifnull( ( select adv_s1f from adv_furlong where rcity = %s and grade = a.grade and dist1 = %s and dist2 = a.distance ), 
                        ( select ifnull( avg( adv_s1f ), 0) from adv_furlong where rcity = %s and dist1 = %s and dist2 = a.distance ) ) ),
                        
            ifnull( ( (i_g3f * (i_convert) )/i_record ), 0) +
                        ( ifnull( ( select adv_g3f from adv_furlong where rcity = %s and grade = a.grade and dist1 = %s and dist2 = a.distance ), 
                    ( select ifnull( avg( adv_g3f ), 0) from adv_furlong where rcity = %s and dist1 = %s and dist2 = a.distance ) ) ),
            
            -- i_s1f '초반 200m', 
            -- i_g3f '종반 600m', 
            
            h_weight, w_change, grade, r_judge '경주등급별 편성강도', alloc3r
            from The1.record a
            where horse = %s 
            and r_judge is not null
            -- and ( r_flag = '0' or r_flag is null ) 
            and rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 365 DAY), '%%Y%%m%%d') from record where horse = a.horse and rdate < %s )         
                            and ( select max(rdate) from record where horse = a.horse and rdate < %s )
            and rank < 98
            -- and r_flag = '0'
            order by rdate desc
            limit 8

            ;
        """

        r_cnt = cursor.execute(
            strSql,
            (
                rdate,
                distance,
                rcity,
                distance,
                rcity,
                distance,
                rcity,
                distance,
                rcity,
                distance,
                rcity,
                distance,
                rcity,
                distance,
                horse,
                rdate,
                rdate,
            ),
        )  # 결과값 개수 반환
        races = cursor.fetchall()

        if not races:
            g2f_rank = "(최근 경주 데이터 없음)"
        else:
            (trend, trend_numeric), detail = judge_horse_trend_7level(races)

            # print(horse, trend_numeric)

            # print(horse, trend, trend_numeric, detail["reasons"])  # '상승세' / '하락세' / '보합세'

            s1f_rank = trend_numeric
            g3f_rank = round(detail["pos_votes"], 1) * 5
            g1f_rank = round(detail["neg_votes"], 1) * 5

            net = round(detail["net"], 1) * 5

            # 1) 사유(reasons) 부분
            reason_lines = detail.get("reasons", [])
            reason_block = "\n".join(reason_lines) if reason_lines else ""

            # 2) 경주(races) 부분
            race_lines = []
            for r in races:
                # r[3] : race_date, r[5] : rank, r[6] : i_convert
                racedate = " '" + r[3][2:4] + "." + r[3][4:6] + "." + r[3][6:8]
                rec = f_t2s(int(r[6]))
                s1f = f_t2s(int(r[7]))[2:]
                g3f = f_t2s(int(r[8]))[2:]
                # grade = r[11][0:2]           # 원본 "국5" / "혼2" / "O4" / "5등" 등

                grade = (
                    r[11][0:2]
                    .replace("혼", "")
                    .replace("국", "")
                    .replace("등", "")
                    .replace("O", "0")
                )

                alloc3r = r[13]
                # 필요하면 정수 변환도 가능
                # clean_int = int(clean)

                race_lines.append(
                    f"{racedate} ... G{grade} ... {s1f} ... {g3f}  ... {rec} ... 순위: {r[5]} ... {alloc3r} ... {r[12]}"
                )

            race_block = "\n".join(race_lines) if race_lines else ""

            # 3) 최종 g2f_rank 조합
            if reason_block and race_block:
                # 사유 + 빈 줄 + [최근 경주] + 경주목록
                g2f_rank = (
                    reason_block
                    + "\n\n'경주 일자 ... 등급 ... S1F ... G3F ... 환산기록 ... 순위 ... 연식 ... 강도 \n"
                    + race_block
                )
            elif reason_block:
                g2f_rank = reason_block
            elif race_block:
                g2f_rank = race_block
            else:
                g2f_rank = "(사유 및 최근 경주 데이터 없음)"

        # print(g2f_rank)
        # print(horse, result["category"], result["diff"], s1f_rank)
        # print("                    사용된 경주 수:", result["used_count"], g3f_rank)
        # print("                    지표별 변화:", result["components"])

    except Exception as e:
        print("Failed selecting 경주마 최근 1년간 8경주 성적 :", horse, e)
    finally:
        if cursor:
            cursor.close()

    try:

        print(g2f_rank)
        cursor = connection.cursor()
        strSql = """
            UPDATE exp011 a
            SET 
                s1f_rank = %s,
                g3f_rank = %s,
                g1f_rank = %s,
                g2f_rank = %s
            WHERE rdate = %s
            AND horse = %s
        """
        params = (
            
            s1f_rank,
            g3f_rank,
            g1f_rank,
            g2f_rank,
            rdate,
            horse,
        )

        # 디버깅용 실제 SQL문 출력
        # print("Executing SQL:", strSql % params)

        r_cnt = cursor.execute(strSql, params)
        # connection.commit()

    except Exception as e:
        connection.rollback()
        print("Failed updating 경주마 데이터:", horse, e)

    finally:
        if cursor:
            cursor.close()
