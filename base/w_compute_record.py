# $PBExportHeader$w_compute_record.srw
# $PBExportComments$Compute Record
# forward
# global type w_compute_record from w_sheet
# end type
# type dw_1 from datawindow within w_compute_record
# end type
# type em_from from editmask within w_compute_record
# end type
# type em_to from editmask within w_compute_record
# end type
# type st_1 from statictext within w_compute_record
# end type
# type st_2 from statictext within w_compute_record
# end type
# type st_3 from statictext within w_compute_record
# end type
# type cb_4 from commandbutton within w_compute_record
# end type
# type cb_5 from commandbutton within w_compute_record
# end type
# type dw_2 from datawindow within w_compute_record
# end type
# type gb_2 from groupbox within w_compute_record
# end type
# type cb_1 from commandbutton within w_compute_record
# end type
# type ddlb_status from dropdownlistbox within w_compute_record
# end type
# type st_desc from statictext within w_compute_record
# end type
# type st_5 from statictext within w_compute_record
# end type
# type em_flag1 from editmask within w_compute_record
# end type
# type st_6 from statictext within w_compute_record
# end type
# type em_flag2 from editmask within w_compute_record
# end type
# type cbx_1 from checkbox within w_compute_record
# end type
# type dw_flag from datawindow within w_compute_record
# end type
# type rb_t from radiobutton within w_compute_record
# end type
# type rb_s from radiobutton within w_compute_record
# end type
# type rb_b from radiobutton within w_compute_record
# end type
# type cb_2 from commandbutton within w_compute_record
# end type
# type gb_1 from groupbox within w_compute_record
# end type
# end forward

# global type w_compute_record from w_sheet
# integer width = 10039
# integer height = 4992
# dw_1 dw_1
# em_from em_from
# em_to em_to
# st_1 st_1
# st_2 st_2
# st_3 st_3
# cb_4 cb_4
# cb_5 cb_5
# dw_2 dw_2
# gb_2 gb_2
# cb_1 cb_1
# ddlb_status ddlb_status
# st_desc st_desc
# st_5 st_5
# em_flag1 em_flag1
# st_6 st_6
# em_flag2 em_flag2
# cbx_1 cbx_1
# dw_flag dw_flag
# rb_t rb_t
# rb_s rb_s
# rb_b rb_b
# cb_2 cb_2
# gb_1 gb_1
# end type
# global w_compute_record w_compute_record

# type variables
# String	is_sortorder, is_rdate
# end variables

# forward prototypes
# public function integer wf_compute_record (string as_rcity, string as_rdate, integer ai_rno, integer ai_gate)
# public function integer wf_compute_rank (string as_rcity, string as_rdate, integer ai_rno)
# public function integer wf_compute_adv (string as_rcity, string as_rdate)
# end prototypes

# public function integer wf_compute_record (string as_rcity, string as_rdate, integer ai_rno, integer ai_gate);
# String	ls_from , ls_to 														//검색기간은 INI파일에서 읽어온다.
# String	ls_1corner, ls_2corner, ls_3corner, ls_4corner, ls_g3f, ls_s1f, ls_g1f, ls_g2f
# String	ls_middle,   ls_fast,   ls_slow,   ls_c100mid, ls_recent, ls_complex, ls_recent3, ls_recent5, ls_convert
# String	ls_grade, ls_horse, ls_jockey, ls_trainer

# Dec		i_jockey, i_s1f, i_r1c, i_r2c, i_r3c, i_r4c, i_g3f, i_g2f, i_g1f, i_convert, i_slow, i_fast, i_avg
# Dec		i_recent, i_complex, i_cnt, i_cnt3, i_compare, i_100m, i_recent3, i_recent5

# Long		ll_distance
# Integer  li_rcnt, li_1st, li_2nd, li_3rd 
# Dec		ld_handycap, ld_per, ld_jockey_per, ld_trainer_per

# Integer	iw_avg, iw_fast, iw_slow, iw_recent3, iw_recent5, iw_convert			// 가중치 변수

# iw_avg = dw_flag.GetItemNumber(1, 'i_avg')
# iw_fast = dw_flag.GetItemNumber(1, 'i_fast')
# iw_slow = dw_flag.GetItemNumber(1, 'i_slow')
# iw_recent3 = dw_flag.GetItemNumber(1, 'i_recent3')
# iw_recent5 = dw_flag.GetItemNumber(1, 'i_recent5')
# iw_convert = dw_flag.GetItemNumber(1, 'i_convert')

# /////////////////////////////////////////////////////////////////////////////////
# //				조건 검색 
# /////////////////////////////////////////////////////////////////////////////////

# ls_from = Mid(em_flag1.Text,1,4) + Mid(em_flag1.Text,6,2) + Mid(em_flag1.Text,9,2)
# ls_to = Mid(em_flag2.Text,1,4) + Mid(em_flag2.Text,6,2) + Mid(em_flag2.Text,9,2)

# SELECT grade,			distance,		horse,		handycap,			jockey, trainer,
# 		( select year_per from jockey_w where a.jockey = jockey and wdate = ( select max(wdate) from jockey_w where wdate < :as_rdate and weekday(wdate) = 6 ) ),
# 		( select year_per from trainer_w where a.trainer = trainer and wdate = ( select max(wdate) from trainer_w where wdate < :as_rdate and weekday(wdate) = 6 ) )
#   INTO :ls_grade,		:ll_distance,	:ls_horse,	:ld_handycap,		:ls_jockey,	:ls_trainer, :ld_jockey_per, :ld_trainer_per
#   FROM expect a
#  WHERE rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno AND gate = :ai_gate ;

# IF SQLCA.SQLCODE <> 0 THEN
# 	MessageBox("알림", SQLCA.SQLErrText +   " - condition" )  
# 	Return -1
# END IF

# select adv_jockey  +  f_burden_w(:as_rdate , :ld_handycap, :ll_distance, :ls_jockey )   /* + f_burden( :ld_handycap, :ll_distance, :ls_jockey ) */ into :i_jockey					// 기수의 거리별 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
#   from adv_jockey
#   where jockey = :ls_jockey and distance = :ll_distance and gate = :ai_gate ;

  
# IF SQLCA.SQLNRows = 0 THEN
	
# 	select avg( adv_jockey  +  f_burden_w(:as_rdate , :ld_handycap, :ll_distance, :ls_jockey ) ) /* + f_burden( :ld_handycap, :ll_distance, :ls_jockey )*/ into :i_jockey		// 기수의 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
# 	  from adv_jockey
# 	  where jockey = :ls_jockey and gate = :ai_gate ;
	  
#   	IF SQLCA.SQLNRows = 0 or i_jockey = 0 or IsNull(i_jockey) THEN
		
# 		select  f_burden_w(:as_rdate , :ld_handycap, :ll_distance, :ls_jockey )  /* f_burden( :ld_handycap, :ll_distance, :ls_jockey )  */ into :i_jockey							// 게이트별 거리별 기수의 실적이 없으면 부담중량만 감안
# 		 from dual ;
		 
# 	END IF
	
# ELSEIF SQLCA.SQLNRows = 1 THEN
	
# //	select avg( adv_jockey /* + f_burden( :ld_handycap, :ll_distance, :ls_jockey ) */ ) into :i_jockey		// 기수의 게이트별 역량 + 부담중량까지 감안된 adv_jpckey
# //     from adv_jockey
# //    where jockey = :ls_jockey and gate = :ai_gate ;
# //  
# //  	IF SQLCA.SQLNRows = 0 THEN
# //		
# //		select f_burden_w(:as_rdate , :ld_handycap, :ll_distance, :ls_jockey ) /* f_burden( :ld_handycap, :ll_distance, :ls_jockey )  */ into :i_jockey							// 게이트별 거리별 기수의 실적이 없으면 부담중량만 감안
# //		 from dual ;
# //		 
# //	END IF
		 
# ELSE
# 	MessageBox("알림", SQLCA.SQLErrText +   " - adv_jockey" )  
# 	Return -1
# END IF

# //IF ls_horse = '마패봉' THEN 
# //	MessageBox("", ls_horse )
# //END IF
# //
# st_desc.Text = as_rcity + " " + as_rdate + " " + String(ai_rno) + "경주 " + String(ai_gate) + " " + ls_horse + " " + String( i_jockey)

# ls_to = as_rdate

# SELECT ifnull( avg( (i_s1f * (i_convert - :i_jockey) )/i_record ), 0),
#        ifnull( avg( (i_r1c * (i_convert - :i_jockey) )/i_record ), 0),
# 		 ifnull( avg( (i_r2c * (i_convert - :i_jockey) )/i_record ), 0),
# 		 ifnull( avg( (i_r3c * (i_convert - :i_jockey) )/i_record ), 0),
# 		 ifnull( avg( (i_r4c * (i_convert - :i_jockey) )/i_record ), 0),
# 		 ifnull( avg( (i_g3f * (i_convert - :i_jockey) )/i_record ), 0),
# 		 ifnull( avg( (i_g2f * (i_convert - :i_jockey) )/i_record ), 0),
# 		 ifnull( avg( (i_g1f * (i_convert - :i_jockey) )/i_record ), 0),
# 		 ifnull( avg( i_convert - :i_jockey ), 0),
# 		 ifnull( max( i_convert - :i_jockey ), 0),
# 		 ifnull( min( i_convert - :i_jockey ), 0)
#   INTO :i_s1f,	:i_r1c,	:i_r2c,	:i_r3c,	:i_r4c,	:i_g3f,	:i_g2f,	:i_g1f,	:i_avg, :i_slow,	:i_fast
#   from record_s a
#  WHERE a.rdate between :ls_from and :ls_to and a.rdate < :as_rdate
#    AND a.horse  = :ls_horse 
#    AND a.distance = :ll_distance 
# 	and r_flag = '0'
# 	and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 777 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < :as_rdate  )         
#                    and ( select max(rdate) from record_s where horse = a.horse and rdate < :as_rdate )
#  ;

# IF SQLCA.SQLCODE = -1 THEN
# 	MessageBox("알림", SQLCA.SQLErrText + " 평균기록 산출오류")
# 	Return -1

# END IF

# Integer ll_weight

# select h_weight into :ll_weight from record_s  where horse = :ls_horse  and rdate = ( select  max(rdate) as rdate from record_s  where rdate < :as_rdate and  horse = :ls_horse  )  ;


# /* furlong 환산 */
# Integer	i_cs1f, i_cg3f, i_cg2f, i_cg1f
# String	ls_cs1f, ls_cg1f, ls_cg2f, ls_cg3f  

# SELECT ifnull( avg( (i_s1f * (i_convert - :i_jockey) )/i_record ), 0) +
#        avg( ifnull( ( select adv_s1f from adv_furlong where rcity = :as_rcity and grade = a.grade and dist1 = :ll_distance and dist2 = a.distance ), 
# 					( select avg( adv_s1f ) from adv_furlong where rcity = :as_rcity and dist1 = :ll_distance and dist2 = a.distance ) ) ),
# 		 ifnull( avg( (i_g1f * (i_convert - :i_jockey) )/i_record ), 0) +
# 		 avg( ifnull( ( select adv_g1f from adv_furlong where rcity = :as_rcity and grade = a.grade and dist1 = :ll_distance and dist2 = a.distance ), 
# 					( select avg( adv_g1f ) from adv_furlong where rcity = :as_rcity and dist1 = :ll_distance and dist2 = a.distance ) ) ),
# 		 ifnull( avg( (i_g2f * (i_convert - :i_jockey) )/i_record ), 0) +
# 		 avg( ifnull( ( select adv_g2f from adv_furlong where rcity = :as_rcity and grade = a.grade and dist1 = :ll_distance and dist2 = a.distance ), 
# 					( select avg( adv_g2f ) from adv_furlong where rcity = :as_rcity and dist1 = :ll_distance and dist2 = a.distance ) ) ),
# 		 ifnull( avg( (i_g3f * (i_convert - :i_jockey) )/i_record ), 0) +
# 		 avg( ifnull( ( select adv_g3f from adv_furlong where rcity = :as_rcity and grade = a.grade and dist1 = :ll_distance and dist2 = a.distance ), 
# 					( select avg( adv_g3f ) from adv_furlong where rcity = :as_rcity and dist1 = :ll_distance and dist2 = a.distance ) ) )
#   INTO :i_cs1f,	:i_cg1f,	:i_cg2f,	:i_cg3f
#   from record_s a
#  WHERE a.rdate between :ls_from and :ls_to and a.rdate < :as_rdate
#    AND a.horse  = :ls_horse 
# 	and r_flag = '0'
# 	and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 777 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < :as_rdate  )         
#                    and ( select max(rdate) from record_s where horse = a.horse and rdate < :as_rdate )
#  ;

# IF SQLCA.SQLCODE = -1 THEN
# 	MessageBox("알림", SQLCA.SQLErrText + " furlong 산출오류")
# 	Return -1

# END IF

# //////////////////////////////////////////////////////////////////////////////////
# ///////////			최근 7 경기 기록 compute
# ////////////////////////////////////////////////////////////////////////////////////
# Dec i_flag, i_rank, i_array[]
# String	ls_remark, i_rstate, i_rdate

# DECLARE C_recent CURSOR FOR  
#  SELECT distance, i_s1f + i_g1f + adv_track, rank, i_convert - :i_jockey, rstate, rdate,

#        ( ( i_convert )/a.distance ) * :ll_distance - :i_jockey + 
# 		            ifnull( ( select adv_dist from adv_distance where rcity = :as_rcity and grade = a.grade and dist1 = :ll_distance and dist2 = a.distance ), 
# //						        ( select avg( adv_dist ) from adv_distance where rcity = :as_rcity and dist1 = :ll_distance and dist2 = a.distance ) )		// 해당경주의 등급별 기록이 없으면, 평균값 치환
# 								  ( select avg( adv_dist ) from adv_distance where dist1 = :ll_distance and dist2 = a.distance ) )		// 해당경주의 등급별 기록이 없으면, 평균값 치환
#    FROM record_s 	a  
#   WHERE a.rdate between :ls_from and :ls_to and a.rdate < :as_rdate   
# 	 AND a.horse = :ls_horse
# 	 and r_flag = '0'
# 	 and a.rdate between ( select date_format(DATE_ADD( max(rdate), INTERVAL - 777 DAY), '%Y%m%d') from record_s where horse = a.horse and rdate < :as_rdate  )         
#                    and ( select max(rdate) from record_s where horse = a.horse and rdate < :as_rdate )
#   ORDER BY a.rdate DESC  ;

# OPEN C_recent ;

# FETCH	C_recent INTO :i_compare, :i_flag, :i_rank, :i_recent, :i_rstate, :i_rdate, :i_100m ; 

# DO WHILE SQLCA.SQLCODE = 0

	
# 	IF i_cnt <= 6 THEN ls_remark = ls_remark + String(i_rank) + "-"
	
# 	i_cnt = i_cnt + 1
	
# 	IF i_compare = ll_distance THEN 		/* 해당거리 최근 경주만 합산 */
# 		i_cnt3 = i_cnt3 + 1
# 		i_recent3 = i_recent3 + i_recent
# 	END IF
	
# 	/* i_100m이 null 이면 거리 환산 기록이 없는 경우 발생 -- 예외처리 필요 */
# 	IF IsNull(i_100m) THEN
# 		i_cnt = i_cnt - 1					/* 환산기록이 없는 경주는 스킵하고 진행 ?(로직 고민 필요 )     이 경주 이후에는 기록이 생성됨   adv_distance Table 집계 */
# 	ELSE
# 		i_recent5 = i_recent5 + i_100m
# 		i_array[i_cnt] = i_100m
# 	END IF

	
# 	IF i_cnt = 7 THEN	EXIT
	
# 	FETCH	C_recent INTO :i_compare, :i_flag, :i_rank, :i_recent, :i_rstate, :i_rdate, :i_100m ;

# LOOP

# CLOSE C_recent;

# Dec tval, max, min = 30000, i

# IF i_cnt >= 3 THEN
	
# 	FOR i = 1 TO i_cnt

# 		tval = i_array[i]
# 		if max < tval then //최대값 비교 
# 			max = tval 
# 		end if 
		
# 		if min > tval then //최소값 비교 
# 			min = tval 
# 		end if 
		
# 	NEXT
	
# 	IF max > i_recent5/i_cnt + 60 THEN			// 제일 느린 기록이 평균기록보다 1초 이상 느리면 제외
	
# 		IF i_rstate = '불량' AND i_rstate = '포화' THEN					// 주로 상태가 불량이면 제외	
# 			i_recent5 = i_recent5 - max
# 			i_cnt = i_cnt -1
			
# 			update record_s set flag = '1'  where rdate = :i_rdate and horse = :ls_horse ;
# 			commit ;
			
# 		END IF
			
# 	END IF
	
# 	IF min < i_recent5/i_cnt - 60 THEN			// 제일 빠른 기록이 평균기록보다 2초이상 빠르면 제외
	
# 		IF i_rstate = '불량' AND i_rstate = '포화' THEN					// 주로 상태가 불량이면 제외	
# 			i_recent5 = i_recent5 - min
# 			i_cnt = i_cnt -1
			
# 			update record_s set flag = '1'  where rdate = :i_rdate and horse = :ls_horse ;
# 			commit ;
			
# 		END IF
		
# 	END IF
	
# END IF

# IF i_cnt >= 1 THEN 
# 	i_recent5 = i_recent5 / i_cnt  
# ELSE
# 	i_recent5 = 0
# END IF

# IF i_cnt3 >= 1 THEN 
# 	i_recent3 = i_recent3 / i_cnt3 
# ELSE
# 	i_recent3 = 0
# END IF

# //IF IsNull(i_recent3) THEN i_recent3 = 0
# //IF IsNull(i_recent5) THEN i_recent5 = 0
# ////////////////////////////////////////////////////////////////////////////////////
# /////////		종합 평균기록 Compute 
# ////////////////////////////////////////////////////////////////////////////////////

# ////i_convert = i_avg * 0.3 + i_fast * 0.4 + i_slow * 0.3
# ////
# ////IF i_convert = 0 THEN i_convert = i_recent5
# ////IF i_recent3 = 0 THEN i_recent3 = i_recent5
# ////
# ////i_complex = ( i_recent3 * 0.3 + i_recent5 * 0.5 + i_convert * 0.2 ) 
# //
# //i_convert = i_avg * 0.4 + i_fast * 0.5 + i_slow * 0.1
# //
# //IF i_convert = 0 THEN i_convert = i_recent5
# //IF i_recent3 = 0 THEN i_recent3 = i_recent5
# //
# //i_complex = ( i_recent3 * 0.3 + i_recent5 * 0.4 + i_convert * 0.3 ) 

# //i_convert = i_avg * 0.5 + i_fast * 0.4 + i_slow * 0.1
# //
# //IF i_convert = 0 THEN i_convert = i_recent5
# //IF i_recent3 = 0 THEN i_recent3 = i_recent5
# //
# //i_complex = ( i_recent3 * 0.4 + i_recent5 * 0.2 + i_convert * 0.4 ) 

# i_convert = ( i_avg * iw_avg + i_fast * iw_fast + i_slow * iw_slow ) /100

# IF i_convert = 0 THEN i_convert = i_recent5
# IF i_recent3 = 0 THEN i_recent3 = i_recent5

# i_complex = ( i_recent3 * iw_recent3 + i_recent5 * iw_recent5 + i_convert * iw_convert ) / 100

# ////////////////////////////////////////////////////////////////////////////////////

# ////////////////////////////////////////////////////////////////////////////////////
# /////////////			기록 저장 
# ////////////////////////////////////////////////////////////////////////////////////


# ls_s1f     = f_change_t2s(i_s1f)


# ls_1corner = f_change_t2s(i_r1c)
# ls_2corner = f_change_t2s(i_r2c)
# ls_3corner = f_change_t2s(i_r3c)
# ls_4corner = f_change_t2s(i_r4c)

# ls_g3f     = f_change_t2s(i_g3f)
# ls_g2f     = f_change_t2s(i_g2f)
# ls_g1f     = f_change_t2s(i_g1f)

# ls_middle = f_change_t2s(i_avg)
# ls_fast = f_change_t2s(i_fast)
# ls_slow = f_change_t2s(i_slow)

# ls_recent3 = f_change_t2s((i_recent3))
# ls_recent5 = f_change_t2s((i_recent5))

# ls_convert = f_change_t2s((i_convert))

# IF i_complex > 0 THEN
# 	ls_complex = f_change_t2s((i_complex))				//종합평균
# ELSE
	
# 	select h_weight into :ll_weight from rec011 where horse = :ls_horse and rdate = ( select max(rdate) from rec011 where horse = :ls_horse and rdate <> :as_rdate ) ;
	
# 	ls_remark = '-'
# 	ls_complex = ''
# END IF

# ls_cs1f     = f_change_t2s(i_cs1f)
# ls_cg1f     = f_change_t2s(i_cg1f)
# ls_cg2f     = f_change_t2s(i_cg2f)
# ls_cg3f     = f_change_t2s(i_cg3f)

# ls_remark = mid( ls_remark, 1, len(ls_remark) - 1 )


# select count(0) AS r_cnt,sum(a.r_1st) AS r_1st, sum(a.r_2nd) AS r_2nd,sum(a.r_3rd) AS r_3rd, round(sum(a.r_3rd) / count(0) * 100,1) AS r_per 
#   into :li_rcnt, :li_1st, :li_2nd, :li_3rd, :ld_per
#   from 
#   (
# 	select a.jockey AS jockey,a.trainer AS trainer,a.rank AS rank,
# 				if(a.rank <= 1,1,0) AS r_1st,
# 				if(a.rank <= 2,1,0) AS r_2nd,
# 				if(a.rank <= 3,1,0) AS r_3rd 
# 	 from rec011 a 
# 	where  (a.rcity,a.rdate,a.rno) in (
# 													select rcity, rdate,rno
# 													  from rec010 
# 													 where rdate >= (select max(date_format(cast(rdate as date) - interval 365+7 day,'%Y%m%d')) from rec010)
# 													   and grade <> '주행검사'
# 												  ) 
# 	  and a.rank <= 20											 
#      and a.jockey = :ls_jockey
#      and a.trainer = :ls_trainer
  
# 	) a     
# ;


# ////////////////  최근 7경주 순위 재설정

# ls_remark = ''
# i_cnt = 0

# DECLARE R_recent CURSOR FOR  
#  SELECT rank
#    FROM record 	a  
#   WHERE a.rdate between :ls_from and :ls_to and a.rdate < :as_rdate   
# 	 AND a.horse = :ls_horse
# 	 and a.judge is null
# 	 and a.rank <= 20

#   ORDER BY a.rdate DESC  ;

# OPEN R_recent ;

# FETCH	R_recent INTO :i_rank ; 

# DO WHILE SQLCA.SQLCODE = 0

	
# 	IF i_cnt <= 6 THEN ls_remark = ls_remark + String(i_rank) + "-"
	
# 	i_cnt = i_cnt + 1
	
	
# 	IF i_cnt = 7 THEN	EXIT
	
# 	FETCH	R_recent INTO :i_rank ; 

# LOOP

# CLOSE R_recent;


# ls_remark = mid( ls_remark, 1, len(ls_remark) - 1 )
# ///////////////////////////////////


# IF li_rcnt = 0 THEN
# 	li_1st = 0
# 	li_2nd = 0
# 	li_3rd = 0
# 	ld_per = 0.0
	
# ELSE
	
# END IF


#   UPDATE exp011  
#      SET rs1f = :ls_s1f,		
# 	  		r1c = :ls_1corner,		r2c = :ls_2corner, 		r3c = :ls_3corner,		r4c = :ls_4corner,
# 			rg3f = :ls_g3f,			rg2f = :ls_g2f,			rg1f = :ls_g1f,
# 			fast_r = :ls_fast,		slow_r = :ls_slow,		avg_r = :ls_middle,
# 			recent3 = :ls_recent3,	recent5 = :ls_recent5, 	complex = :ls_complex,	convert_r = :ls_convert,
# 			cs1f = :ls_cs1f,			cg3f = :ls_cg3f,			cg2f = :ls_cg2f,			cg1f = :ls_cg1f,
# 			i_s1f = :i_cs1f,			i_g3f = :i_cg3f,			i_g2f = :i_cg2f,			i_g1f = :i_cg1f,	i_complex = :i_complex,		i_jockey = :i_jockey,
			
# 			i_cycle = f_rcycle( :as_rcity, :as_rdate, :ls_horse ),
# 			i_prehandy = f_prehandy( :as_rcity, :as_rdate, :ls_horse ),
			
# 			remark = :ls_remark,
# 			h_weight = :ll_weight,
# 			j_per = :ld_jockey_per,
# 			t_per = :ld_trainer_per,
# 			jt_per = :ld_per,
# 			jt_cnt = :li_rcnt,
# 			jt_1st = :li_1st,
# 			jt_2nd = :li_2nd,
# 			jt_3rd = :li_3rd
#    WHERE rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno AND gate = :ai_gate   ;
	


# IF SQLCA.SQLCODE = -1 THEN
# 	MessageBox("알림",SQLCA.SQLerrText + " Update exp011")
# 	ROLLBACK;
# 	Return -1
# END IF

# COMMIT;

# delete from exp013 
#  where rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno AND gate = :ai_gate ;
 
# insert into exp013 
# select rcity, rdate, rno, gate, horse, null, null, null, null, distance, 0,0, ''
#   from expect
#  where rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno AND gate = :ai_gate ;

# commit ;


# Return 1


# end function

# public function integer wf_compute_rank (string as_rcity, string as_rdate, integer ai_rno);////////////////////////////////////////////////////////////////////////
# //  Temp Rank Insert
# ////////////////////////////////////////////////////////////////////////
# Dec		i_complex
# Integer	i_rank, i_gate

# DECLARE C_rank CURSOR FOR  
#  SELECT i_complex, gate
#    FROM exp011
#   WHERE rcity = :as_rcity
#     AND rdate = :as_rdate 
#     AND rno = :ai_rno
#   ORDER BY i_complex    ASC, gate      ASC ;

# OPEN C_rank ;

# FETCH C_rank INTO :i_complex, :i_gate  ;

# IF SQLCA.SQLCODE <> 0 THEN
# 	ROLLBACK;
# 	MessageBox("알림",SQLCA.SQLErrText + " Rank 설정 중 에러발생!")
# 	Return -1
# END IF

# DO WHILE SQLCA.SQLCODE = 0
# 	i_rank = i_rank + 1

# 	IF i_complex = 0 THEN			//신마
		
# 	  UPDATE exp011  															//가상 순위 Update
# 		  SET rank = 98
# 		WHERE rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno AND gate = :i_gate   ;
		
# 		i_rank = i_rank - 1       

# 	ELSE

# 	  UPDATE exp011  															//가상 순위 Update
# 		  SET rank = :i_rank
# 		WHERE  rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno AND gate = :i_gate   ;
		
# 	END IF

# 	FETCH C_rank INTO :i_complex, :i_gate  ;
	
# LOOP

# CLOSE C_rank;

# COMMIT;
# ////////////////////////////////////////////////////////////////////////


# update exp011 a
# set complex5 = ( select complex from exp011 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = 4 ),
# 	 gap = a.i_complex - ( select i_complex from exp011 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = a.rank - 1 ),
# 	 gap_back = ( select i_complex from exp011 where rcity = a.rcity and rdate = a.rdate AND rno = a.rno AND rank = a.rank + 1 ) - a.i_complex 
# where rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno
# ;


# IF SQLCA.SQLCODE <> 0 THEN
# 	ROLLBACK;
# 	MessageBox("알림",SQLCA.SQLErrText + " complex5, gap 설정 중 에러발생!")
# 	Return -1
# END IF

# commit ;



# end function

# public function integer wf_compute_adv (string as_rcity, string as_rdate);String	ls_rcity, ls_from, ls_to, ls_flagdate

# ls_rcity = gs_rcity

# ls_from = Mid(em_flag1.Text,1,4) + Mid(em_flag1.Text,6,2) + Mid(em_flag1.Text,9,2)
# ls_to = as_rdate

# //select DATE_FORMAT( subdate( str_to_date( :as_rdate, '%Y%m%d' ) , 3 ),'%Y%m%d') into :ls_to from dual ;//

# st_desc.Text = ls_to + "  award Table Computing..."  
# messagebox("", as_rdate)

# Delete from award where rmonth = substr(:as_rdate,1,6) ;
# commit;

# //	기수 조교사 마주 월별 상금 수득현황
# insert into award  
# select substr( rdate,1,6) rmonth, jockey, trainer, host, 
# 		  sum(if(a.rank = 1, 1, 0)) r1_cnt, 
#         sum(if(a.rank = 2, 1, 0)) r2_cnt, 
#         sum(if(a.rank = 3, 1, 0)) r3_cnt, 
#         sum(if(a.rank = 4, 1, 0)) r4_cnt, 
#         sum(if(a.rank = 5, 1, 0)) r5_cnt,
#         count(*) r_cnt,
# 		sum( if(a.rank = 1, r1award + sub1award, 0) +
# 		if(a.rank = 2, r2award + sub2award, 0) +
# 		if(a.rank = 3, r3award + sub3award, 0) +
# 		if(a.rank = 4, r4award, 0) +
# 		if(a.rank = 5, r5award, 0)) award
#   from record a
#  where a.rank <= 5 and grade <> '주행검사'
# 	and substr(a.rdate,1,6) = substr(:as_rdate,1,6) 
#  group by  substr( rdate,1,6), jockey, trainer, host ;

# commit ;


# st_desc.Text = ls_to + "  adv_table Computing..."  


# Delete from adv_jockey ;
# commit;

# //	기수의 게이트별 거리별 평균기록
# insert into adv_jockey  
# select jockey, 
# 	distance,   
# 	gate,
# 	round( avg, 4 ) avg, 
# 	round( i_record, 4 ) i_record, 
# 	round( avg - i_record ,4 ) adv_gate, 
# 	rcnt, 
# 	round( jockey_w,4) joc_rate,
	
# //	ifnull(round( ((  avg - i_record  ) / 500 ) * 500, 4), 0)	adv_jockey	

# 	       	ifnull(round( ((  avg - i_record  ) / distance ) * 500, 4), 0)	adv_jockey	

#   from (
# 			select jockey, distance,  gate, sum( i_record  + burden_w) / count(*) i_record, count(*) rcnt, //	기수의 게이트별 거리별 평균기록

# 									( select sum(i_record  + burden_w )/count(*)  
# 										 from record_s
# 										where rdate between :ls_from and :ls_to //and rdate <  :ls_to
# 										  and rank between 1 and 5
# 										  and jockey = a.jockey
# 										  and distance = a.distance ) avg, 
										  
# 					avg(jockey_w) jockey_w

# 			  from record_s a
# 			 where rdate between :ls_from and :ls_to // and rdate <  :ls_to
# 				 and rank between 1 and 5
# 			 group by jockey, distance,  gate 
# 	) a
#  where rcnt > 1 		//	최소 1번이상 뛰어본 케이스만 대상 
# ;

# commit ;

# st_desc.Text = ls_to + " adv_jockey Table Complet !   adv_track Table Computing..."

# Delete from adv_track;
						
# insert into adv_track 
# select aa.rcity, aa.rdate, aa.rno, aa.grade, aa.distance, round( aa.rec, 4) record, round( bb.avg, 4) avg_rec, round( ( bb.avg - aa.rec ),4) adv_flag, 
#        round( ( ( bb.avg - aa.rec )/ aa.distance ) * 500, 4) adv_track
#   from
# 	(
# 		select rcity, rdate, rno, grade, distance, avg( rec ) rec 
# 		  from 
# 			(
# 				select rcity,rdate, rno, grade, distance, i_record + burden_w + 
# 							  ( select adv_jockey from adv_jockey where jockey = a.jockey and gate = a.gate and distance = a.distance) rec		//경주결과 환산시 (+)
# 				  from record_s a
# 				 where rdate between :ls_from and :ls_to //and rdate <  :ls_to
# 			      and rank between 1 and 5
# 			) b
# 		 group by rcity, rdate, rno, grade, distance
# 	) aa,
# 	(

# 		select rcity, grade, distance, avg( rec ) avg
# 		  from 
# 			(
# 				select rcity, grade, distance, i_record + burden_w + 
# 							  ( select adv_jockey from adv_jockey where jockey = a.jockey and gate = a.gate and distance = a.distance) rec
# 				  from record_s a
# 				 where rdate between :ls_from and :ls_to //and rdate <  :ls_to
# 			      and rank between 1 and 5
# 			) b
# 		 group by rcity, grade, distance

# 	) bb
#  where aa.rcity = bb.rcity
#    and aa.grade = bb.grade
#    and aa.distance = bb.distance
# ;
# commit ;

# st_desc.Text = ls_to +  " adv_track Table Complet !   adv_jockey Table  Computing..."

# update rec011 a set adv_jockey = ifnull( ( select adv_jockey from adv_jockey 
# 														  where jockey = a.jockey 
# 													 		and distance = a.distance_w  
# 													 		and gate = a.gate ), 0) ,
#                     		    adv_track = ifnull( ( select adv_track from adv_track where rcity = a.rcity and rdate = a.rdate and rno = a.rno ), 0)
# where rdate >= '20180101'
# ;
# commit ;

# update record_s a set adv_jockey = ifnull( ( select adv_jockey from adv_jockey 
# 														  where jockey = a.jockey 
# 													 		and distance = a.distance_w  
# 													 		and gate = a.gate ), 0) ,
#                     		    adv_track = ifnull( ( select adv_track from adv_track where rcity = a.rcity and rdate = a.rdate and rno = a.rno ), 0)
# where rdate >= '20180101'
# ;
# commit ;

# st_desc.Text = ls_to + " adv_jockey Column Complet !   i_convert Column  Computing..."

# update rec011 a set i_convert = i_record + ifnull( adv_jockey, 0 ) + ifnull( adv_track, 0 ) + burden_w
#  where rdate >= '20180101'
#  ;
# commit ;

# update record_s a set i_convert = i_record + ifnull( adv_jockey, 0 ) + ifnull( adv_track, 0 ) + burden_w
#  where rdate >= '20180101'
#  ;
# commit ;


# st_desc.Text = ls_to + " i_convert Column Complet !   adv_distance Table  Computing..."

# Delete from adv_distance ; 

# insert into adv_distance
# select aa.rcity, aa.grade, aa.distance as dist1, bb.distance as dist2, aa.rec as i_100m1, bb.rec as i_100m2, 
#      ( aa.rec - bb.rec ) * (aa.distance/100) adv_dist, aa.rcnt rcnt1,  bb.rcnt rcnt2

#   from 
# 	(
# 		select rcity, grade, distance, sum(i_convert)/count(*) / (distance/100) rec, count(*) rcnt
# 		  from record_s a
# 		 where rdate between :ls_from and :ls_to //and rdate <  :ls_to
# 		   and rank between 1 and 5
		
# 		 group by rcity, grade, distance
# 	) aa,	
# 	(

# 		select rcity, grade, distance, sum(i_convert)/count(*) / (distance/100) rec, count(*) rcnt
# 		  from record_s a
# 		 where rdate between :ls_from and :ls_to //and rdate <  :ls_to
# 			and rank between 1 and 5
			
# 		 group by rcity, grade, distance
# 	) bb
#  where aa.rcity = bb.rcity
#    and aa.grade = bb.grade 
# ;
# commit ;


# st_desc.Text = ls_to + " adv_distance Table Complet !   adv_furlong Table  Computing..."
# Delete from adv_furlong ;

# insert into adv_furlong
# select aa.rcity, aa.grade, aa.distance as dist1, bb.distance as dist2, 
# 		aa.s1f, bb.s1f, aa.s1f - bb.s1f, 
# 		aa.g1f, bb.g1f, aa.g1f - bb.g1f, 
# 		aa.g2f, bb.g2f, aa.g2f - bb.g2f, 
# 		aa.g3f, bb.g3f, aa.g3f - bb.g3f, 
# 		aa.rcnt rcnt1,  bb.rcnt rcnt2

#   from 
# 	(
# 		select rcity, grade, distance,  avg(i_s1f) s1f, avg(i_g1f) g1f , avg(i_g2f) g2f, avg(i_g3f) g3f, count(*) rcnt
# 		  from record_s a
# 		 where rdate between :ls_from and :ls_to //and rdate <  :ls_to
# 		   and rank between 1 and 5
# 		 group by rcity, grade, distance
# 	) aa,	
# 	(
# 		select rcity, grade, distance,  avg(i_s1f) s1f, avg(i_g1f) g1f , avg(i_g2f) g2f, avg(i_g3f) g3f, count(*) rcnt
# 		  from record_s a
# 		 where rdate between :ls_from and :ls_to //and rdate <  :ls_to
# 		   and rank between 1 and 5

# 		 group by rcity, grade, distance
# 	) bb
#  where aa.rcity = bb.rcity
#    and aa.grade = bb.grade 
# ;
# commit ;
# //select rdate, rno, adv_track from record where rdate >= '20200101' ;

# st_desc.Text = "Complet !"

# return 1
# end function

# on w_compute_record.create
# int iCurrent
# call super::create
# this.dw_1=create dw_1
# this.em_from=create em_from
# this.em_to=create em_to
# this.st_1=create st_1
# this.st_2=create st_2
# this.st_3=create st_3
# this.cb_4=create cb_4
# this.cb_5=create cb_5
# this.dw_2=create dw_2
# this.gb_2=create gb_2
# this.cb_1=create cb_1
# this.ddlb_status=create ddlb_status
# this.st_desc=create st_desc
# this.st_5=create st_5
# this.em_flag1=create em_flag1
# this.st_6=create st_6
# this.em_flag2=create em_flag2
# this.cbx_1=create cbx_1
# this.dw_flag=create dw_flag
# this.rb_t=create rb_t
# this.rb_s=create rb_s
# this.rb_b=create rb_b
# this.cb_2=create cb_2
# this.gb_1=create gb_1
# iCurrent=UpperBound(this.Control)
# this.Control[iCurrent+1]=this.dw_1
# this.Control[iCurrent+2]=this.em_from
# this.Control[iCurrent+3]=this.em_to
# this.Control[iCurrent+4]=this.st_1
# this.Control[iCurrent+5]=this.st_2
# this.Control[iCurrent+6]=this.st_3
# this.Control[iCurrent+7]=this.cb_4
# this.Control[iCurrent+8]=this.cb_5
# this.Control[iCurrent+9]=this.dw_2
# this.Control[iCurrent+10]=this.gb_2
# this.Control[iCurrent+11]=this.cb_1
# this.Control[iCurrent+12]=this.ddlb_status
# this.Control[iCurrent+13]=this.st_desc
# this.Control[iCurrent+14]=this.st_5
# this.Control[iCurrent+15]=this.em_flag1
# this.Control[iCurrent+16]=this.st_6
# this.Control[iCurrent+17]=this.em_flag2
# this.Control[iCurrent+18]=this.cbx_1
# this.Control[iCurrent+19]=this.dw_flag
# this.Control[iCurrent+20]=this.rb_t
# this.Control[iCurrent+21]=this.rb_s
# this.Control[iCurrent+22]=this.rb_b
# this.Control[iCurrent+23]=this.cb_2
# this.Control[iCurrent+24]=this.gb_1
# end on

# on w_compute_record.destroy
# call super::destroy
# destroy(this.dw_1)
# destroy(this.em_from)
# destroy(this.em_to)
# destroy(this.st_1)
# destroy(this.st_2)
# destroy(this.st_3)
# destroy(this.cb_4)
# destroy(this.cb_5)
# destroy(this.dw_2)
# destroy(this.gb_2)
# destroy(this.cb_1)
# destroy(this.ddlb_status)
# destroy(this.st_desc)
# destroy(this.st_5)
# destroy(this.em_flag1)
# destroy(this.st_6)
# destroy(this.em_flag2)
# destroy(this.cbx_1)
# destroy(this.dw_flag)
# destroy(this.rb_t)
# destroy(this.rb_s)
# destroy(this.rb_b)
# destroy(this.cb_2)
# destroy(this.gb_1)
# end on

# event open;call super::open;Integer  i_avg, 	i_fast, 	i_slow, 	i_recent3, 		i_recent5, 		i_convert

# dw_1.SetTransObject(SQLCA)
# dw_2.SetTransObject(SQLCA)

# dw_flag.SetTransObject(SQLCA)

# em_flag1.Text = "2018.07.22"
# em_flag2.Text = String(Today() ,'yyyy.mm.dd')

# String		ls_from, ls_to

# select DATE_FORMAT( subdate( str_to_date( max(rdate), '%Y%m%d' ) , 2),'%Y.%m.%d') , DATE_FORMAT( max(rdate), '%Y.%m.%d') 
#   into :ls_from, :ls_to
#   from exp010
#  where rname <> '주행검사'
# ;

# //em_from.Text = String(Today() ,'yyyy.mm.dd')
# //em_to.Text = String(Today() ,'yyyy.mm.dd')

# em_from.Text = ls_from
# em_to.Text = ls_to

# ddlb_status.SelectItem("% All",1)

# dw_flag.InsertRow(0)

# select w_avg,	w_fast,	w_slow,	w_recent3,		w_recent5,		w_convert
#   into  :i_avg, 	:i_fast, 	:i_slow, 	:i_recent3, 		:i_recent5, 		:i_convert
#   from weight
#  where wdate = ( select max(wdate) from weight ) ;
 
 
# dw_flag.setItem(1,"i_avg", i_avg)
# dw_flag.setItem(1,"i_fast", i_fast)
# dw_flag.setItem(1,"i_slow", i_slow)
# dw_flag.setItem(1,"i_recent3", i_recent3)
# dw_flag.setItem(1,"i_recent5", i_recent5)
# dw_flag.setItem(1,"i_convert", i_convert)

# dw_flag.AcceptText()
# end event

# type uo_progress from w_sheet`uo_progress within w_compute_record
# integer taborder = 100
# end type

# type dw_1 from datawindow within w_compute_record
# integer x = 27
# integer y = 356
# integer width = 3959
# integer height = 3628
# integer taborder = 90
# boolean bringtotop = true
# string title = "none"
# string dataobject = "d_compute_record"
# boolean hscrollbar = true
# boolean vscrollbar = true
# boolean livescroll = true
# end type

# event clicked;String		ls_OldSQL, ls_CurrentSQL, ls_Where
# String		ls_rdate, ls_rcity

# Integer		i_rno

# IF row <= 0 THEN Return

# SelectRow(0,False)
# SelectRow(row, True)

# ls_rcity = GetItemString( row, "rcity" )
# ls_rdate = GetItemString( row, "rdate" )
# i_rno = GetItemNumber( row, "rno" )

# dw_2.Reset()

# ls_OldSQL = dw_2.GetSqlSelect()

# ls_CurrentSQL = ls_OldSQL + " Where 1 =1 "

# ls_CurrentSQL = ls_CurrentSQL + " AND rcity = '" + ls_rcity + "'"
# ls_CurrentSQL = ls_CurrentSQL + " AND rdate = '" + ls_rdate + "'"
# ls_CurrentSQL = ls_CurrentSQL + " AND rno = " + String(i_rno)


# dw_2.SetSQLSelect(ls_CurrentSQL)
# dw_2.Retrieve()
# dw_2.SetSQLSelect(ls_OldSQL)


# end event

# type em_from from editmask within w_compute_record
# integer x = 512
# integer y = 188
# integer width = 512
# integer height = 92
# integer taborder = 20
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# string text = "none"
# alignment alignment = center!
# borderstyle borderstyle = stylelowered!
# maskdatatype maskdatatype = datemask!
# string mask = "yyyy.mm.dd"
# boolean spin = true
# end type

# event modified;

# em_flag2.text = This.Text
# end event

# type em_to from editmask within w_compute_record
# integer x = 1143
# integer y = 188
# integer width = 512
# integer height = 92
# integer taborder = 30
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# string text = "none"
# alignment alignment = center!
# borderstyle borderstyle = stylelowered!
# maskdatatype maskdatatype = datemask!
# string mask = "yyyy.mm.dd"
# boolean spin = true
# end type

# type st_1 from statictext within w_compute_record
# integer x = 105
# integer y = 204
# integer width = 379
# integer height = 64
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "경주일자 : "
# alignment alignment = right!
# boolean focusrectangle = false
# end type

# type st_2 from statictext within w_compute_record
# integer x = 1029
# integer y = 204
# integer width = 114
# integer height = 64
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "~~"
# alignment alignment = center!
# boolean focusrectangle = false
# end type

# type st_3 from statictext within w_compute_record
# integer x = 3323
# integer y = 204
# integer width = 279
# integer height = 64
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "Status :"
# alignment alignment = right!
# boolean focusrectangle = false
# end type

# type cb_4 from commandbutton within w_compute_record
# integer x = 4695
# integer y = 180
# integer width = 448
# integer height = 104
# integer taborder = 70
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# string text = "Select All"
# boolean flatstyle = true
# end type

# event clicked;Long		ll_row, i , ll_RowCount


# ll_RowCount = dw_1.RowCount()
# FOR i = 1 TO ll_RowCount
# 	dw_1.SetItem( i, "rcheck", "Y")
# NEXT

# dw_1.AcceptText()
# end event

# type cb_5 from commandbutton within w_compute_record
# integer x = 5179
# integer y = 180
# integer width = 553
# integer height = 104
# integer taborder = 80
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# string text = "Compute Record"
# boolean flatstyle = true
# end type

# event clicked;String	ls_check, ls_rcity, ls_rdate, ls_fdate
# Long		ll_cnt, ll_row, ll_return, ll_rtn
# Integer	i_rno, i_rcount, i

# is_rdate = '0000.00.00'	//	재집계 기준일

# dw_flag.AcceptText()	//	가중치 확정

# ll_cnt = dw_1.RowCount()

# FOR ll_row = 1 TO ll_cnt
	
# 	ls_check = dw_1.GetItemString(ll_row, "rcheck")
	
# 	IF ls_check = 'Y' THEN
		
# 		ls_rcity = dw_1.GetItemString( ll_row, "rcity" )
# 		ls_rdate = dw_1.GetItemString( ll_row, "rdate" )
		
# 		ls_fdate = dw_1.GetItemString( ll_row, "fdate" )
		
# 		IF is_rdate <> ls_fdate THEN 
			
# 			IF cbx_1.Checked = True THEN
# 				ll_rtn = wf_compute_adv( ls_rcity, ls_fdate )				// adv_table 제집계
# 				IF ll_rtn = -1 THEN Return
# 			END IF

# 			is_rdate = ls_fdate

# 		END IF
		
# 		i_rno = dw_1.GetItemNumber( ll_row, "rno" )
		
# 		i_rcount = Long( dw_1.GetItemString( ll_row, "rcount" ))
		
# 		FOR i = 1 TO i_rcount
# 			ll_rtn = wf_compute_record( ls_rcity, ls_rdate, i_rno, i )
			
			
# 			IF ll_rtn = -1 THEN Return
# 		NEXT

# 		ll_rtn = wf_compute_rank( ls_rcity, ls_rdate, i_rno )
# 		IF ll_rtn = -1 THEN Return
		
# 	END IF
	
# NEXT

# COMMIT ;

# Integer	iw_avg, iw_fast, iw_slow, iw_recent3, iw_recent5, iw_convert			// 가중치 변수

# iw_avg = dw_flag.GetItemNumber(1, 'i_avg')
# iw_fast = dw_flag.GetItemNumber(1, 'i_fast')
# iw_slow = dw_flag.GetItemNumber(1, 'i_slow')
# iw_recent3 = dw_flag.GetItemNumber(1, 'i_recent3')
# iw_recent5 = dw_flag.GetItemNumber(1, 'i_recent5')
# iw_convert = dw_flag.GetItemNumber(1, 'i_convert')

# INSERT INTO weight  
# 		( wdate,   	w_avg,   	w_fast,	w_slow,	w_recent3,		w_recent5,		w_convert  )  
# VALUES 	( now(),	:iw_avg,	:iw_fast,	:iw_slow,	:iw_recent3,	:iw_recent5,	:iw_convert ) ;

# COMMIT;

# //String	ls_rdate = '20200101'
# //
# //select DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 2 ),'%Y%m%d')  into :ls_rdate from dual ;
# //
# //messagebox( "", ls_rdate )

# end event

# type dw_2 from datawindow within w_compute_record
# integer x = 4009
# integer y = 356
# integer width = 4617
# integer height = 3636
# integer taborder = 120
# boolean bringtotop = true
# string title = "none"
# string dataobject = "d_compute_record_sub"
# boolean hscrollbar = true
# boolean vscrollbar = true
# boolean livescroll = true
# end type

# event clicked;
# string ls_column, ls_original_border 
# IF NOT dwo.name = "datawindow" then //DWObject 바탕을 클릭! 
#   IF dwo.band = "header" THEN 
#     IF dwo.name = "" THEN 
#       Messagebox("Error", "칼럼 헤더 오브젝트에 칼럼명이 없습니다.") 
#       Return 
#    END IF

#   // DW의 컬럼 타이틀은 기본적으로 "컬럼이름_t"로 만들어 집니다. 그 규칙에 맞게 "_t"를 잘라내어 
#   // 컬럼명을 얻어서 Sort를 합니다. 타이틀의 이름을 "컬럼이름_t"로 모두 동일하게 맞춰 주십시오. 
#   ls_column = LeftA(dwo.name, PosA(dwo.name,"_t") -1 ) 
#   this.SetSort(ls_column + " " + is_sortorder) 
#   this.Sort()

#  IF is_sortorder = 'A' THEN // Ascending 이면 
#      is_sortorder = 'D' // Desending 한다. 
#  ELSE 
#     is_sortorder = 'A' 
#  END IF

#  END IF 
# END IF 


# IF row <= 0 THEN Return

# SelectRow(0,False)
# SelectRow(row, True)


# end event

# type gb_2 from groupbox within w_compute_record
# integer y = 300
# integer width = 8649
# integer height = 3716
# integer taborder = 130
# integer textsize = -8
# integer weight = 400
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = swiss!
# string facename = "System"
# long textcolor = 33554432
# long backcolor = 67108864
# end type

# type cb_1 from commandbutton within w_compute_record
# integer x = 4233
# integer y = 180
# integer width = 425
# integer height = 104
# integer taborder = 60
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# string text = "Search"
# boolean flatstyle = true
# end type

# event clicked;String		ls_OldSQL, ls_CurrentSQL, ls_Where
# String		ls_from, ls_to, ls_status, ls_fcode, ls_rcity


# em_flag2.text = em_from.Text

# dw_1.Reset()

# ls_OldSQL = dw_1.GetSqlSelect()

# ls_CurrentSQL = ls_OldSQL + " Where 1 =1 "

# ls_from = Mid(em_from.Text,1,4) + Mid(em_from.Text,6,2) + Mid(em_from.Text,9,2)
# ls_to = Mid(em_to.Text,1,4) + Mid(em_to.Text,6,2) + Mid(em_to.Text,9,2)
# ls_status = Mid(ddlb_status.Text,1,1)

# IF rb_t.Checked = True THEN
# 	ls_rcity = '%'
# ELSEIF rb_s.Checked = True THEN
# 	ls_rcity = '서울'
# ELSEIF rb_b.Checked = True THEN
# 	ls_rcity = '부산'
# END IF

# ls_CurrentSQL = ls_CurrentSQL + " AND rcity like '" + ls_rcity + "'"

# ls_CurrentSQL = ls_CurrentSQL + " AND rdate >= '" + ls_from + "'"
# ls_CurrentSQL = ls_CurrentSQL + " AND rdate <= '" + ls_to + "'"
# ls_CurrentSQL = ls_CurrentSQL + " ORDER BY rdate, rcity, rno "

# //MessageBox("", ls_CurrentSQL)

# dw_1.SetSQLSelect(ls_CurrentSQL)
# dw_1.Retrieve()
# dw_1.SEtSQLSelect(ls_OldSQL)

# dw_1.ResetUpdate()
# end event

# type ddlb_status from dropdownlistbox within w_compute_record
# integer x = 3653
# integer y = 188
# integer width = 507
# integer height = 332
# integer taborder = 50
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# string item[] = {"C Complet","D Computing","% ALL"}
# borderstyle borderstyle = stylelowered!
# end type

# type st_desc from statictext within w_compute_record
# integer x = 5810
# integer y = 196
# integer width = 1861
# integer height = 88
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "ing..."
# boolean focusrectangle = false
# end type

# type st_5 from statictext within w_compute_record
# integer x = 114
# integer y = 92
# integer width = 379
# integer height = 64
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "집계기준 : "
# alignment alignment = right!
# boolean focusrectangle = false
# end type

# type em_flag1 from editmask within w_compute_record
# integer x = 512
# integer y = 68
# integer width = 512
# integer height = 92
# integer taborder = 10
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# string text = "none"
# alignment alignment = center!
# borderstyle borderstyle = stylelowered!
# maskdatatype maskdatatype = datemask!
# string mask = "yyyy.mm.dd"
# boolean spin = true
# end type

# type st_6 from statictext within w_compute_record
# integer x = 1029
# integer y = 96
# integer width = 114
# integer height = 64
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "~~"
# alignment alignment = center!
# boolean focusrectangle = false
# end type

# type em_flag2 from editmask within w_compute_record
# integer x = 1143
# integer y = 68
# integer width = 512
# integer height = 92
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# boolean enabled = false
# string text = "none"
# alignment alignment = center!
# boolean displayonly = true
# borderstyle borderstyle = stylelowered!
# maskdatatype maskdatatype = datemask!
# string mask = "yyyy.mm.dd"
# boolean spin = true
# end type

# type cbx_1 from checkbox within w_compute_record
# integer x = 3397
# integer y = 84
# integer width = 430
# integer height = 76
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 16711680
# long backcolor = 67108864
# string text = "다시 집계"
# boolean checked = true
# end type

# type dw_flag from datawindow within w_compute_record
# integer x = 1742
# integer y = 64
# integer width = 1563
# integer height = 248
# integer taborder = 40
# boolean bringtotop = true
# string title = "none"
# string dataobject = "d_complex_flag"
# boolean border = false
# boolean livescroll = true
# end type

# type rb_t from radiobutton within w_compute_record
# integer x = 3918
# integer y = 84
# integer width = 224
# integer height = 76
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "ALL"
# boolean checked = true
# end type

# type rb_s from radiobutton within w_compute_record
# integer x = 4160
# integer y = 84
# integer width = 224
# integer height = 76
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "서울"
# end type

# type rb_b from radiobutton within w_compute_record
# integer x = 4411
# integer y = 84
# integer width = 224
# integer height = 76
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "부산"
# end type

# type cb_2 from commandbutton within w_compute_record
# integer x = 5179
# integer y = 60
# integer width = 553
# integer height = 104
# integer taborder = 90
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# string text = "adv_table Regen"
# boolean flatstyle = true
# end type

# event clicked;String	ls_rcity, ls_fdate

# ls_rcity = dw_1.GetItemString( 1, "rcity" )
# ls_fdate = dw_1.GetItemString( 1, "fdate" )

# ls_fdate = String(Today() ,'yyyymmdd')


# wf_compute_adv( ls_rcity, ls_fdate )				// adv_table 제집계

# end event

# type gb_1 from groupbox within w_compute_record
# integer width = 8649
# integer height = 304
# integer taborder = 110
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# end type

