# $PBExportHeader$w_kradata_input.srw
# $PBExportComments$kra data 입력
# forward
# global type w_kradata_input from w_sheet
# end type
# type dw_1 from datawindow within w_kradata_input
# end type
# type mle_krafile from multilineedit within w_kradata_input
# end type
# type cb_1 from commandbutton within w_kradata_input
# end type
# type cb_2 from commandbutton within w_kradata_input
# end type
# type cb_3 from commandbutton within w_kradata_input
# end type
# type em_from from editmask within w_kradata_input
# end type
# type em_to from editmask within w_kradata_input
# end type
# type ddlb_status from dropdownlistbox within w_kradata_input
# end type
# type ddlb_fcode from dropdownlistbox within w_kradata_input
# end type
# type st_1 from statictext within w_kradata_input
# end type
# type st_2 from statictext within w_kradata_input
# end type
# type st_3 from statictext within w_kradata_input
# end type
# type st_4 from statictext within w_kradata_input
# end type
# type cb_4 from commandbutton within w_kradata_input
# end type
# type rb_s from radiobutton within w_kradata_input
# end type
# type rb_b from radiobutton within w_kradata_input
# end type
# type rb_t from radiobutton within w_kradata_input
# end type
# end forward

# global type w_kradata_input from w_sheet
# integer width = 10011
# integer height = 5768
# string title = "KRA Data Input"
# boolean hscrollbar = true
# boolean vscrollbar = true
# long backcolor = 16777215
# dw_1 dw_1
# mle_krafile mle_krafile
# cb_1 cb_1
# cb_2 cb_2
# cb_3 cb_3
# em_from em_from
# em_to em_to
# ddlb_status ddlb_status
# ddlb_fcode ddlb_fcode
# st_1 st_1
# st_2 st_2
# st_3 st_3
# st_4 st_4
# cb_4 cb_4
# rb_s rb_s
# rb_b rb_b
# rb_t rb_t
# end type
# global w_kradata_input w_kradata_input

# type variables

# String	is_fname
# end variables

# forward prototypes
# public function integer wf_convert_11 ()
# public function integer wf_convert_23 ()
# public function integer wf_convert_71 ()
# public function integer wf_convert_b1 ()
# public function integer wf_convert_b2 ()
# public function integer wf_convert_b3 ()
# public function integer wf_convert_b6 ()
# public function integer wf_convert_72 ()
# public function integer wf_convert_55 ()
# public function string wf_gettext (integer ai_linenumber)
# public function integer wf_convert_b5 ()
# public function integer wf_convert_b4 ()
# public function integer wf_convert_b7 ()
# public function integer wf_convert_b2_20180719 ()
# public function integer wf_convert_b3_20180719 ()
# public function integer wf_convert_b1_20180719 ()
# public function integer wf_convert_13 ()
# public function integer wf_convert_01 ()
# public function integer wf_convert_01_busan ()
# public function integer wf_convert_11_busan ()
# public function integer wf_convert_13_busan ()
# public function integer wf_convert_23_busan ()
# public function integer wf_convert_55_busan ()
# public function integer wf_convert_71_busan ()
# public function integer wf_convert_72_busan ()
# public function integer wf_convert_b1_busan ()
# public function integer wf_convert_b1_20180719_busan ()
# public function integer wf_convert_b2_busan ()
# public function integer wf_convert_b2_20180719_busan ()
# public function integer wf_convert_b3_busan ()
# public function integer wf_convert_b3_20180719_busan ()
# public function integer wf_convert_b4_busan ()
# public function integer wf_convert_b5_busan ()
# public function integer wf_convert_b6_busan ()
# public function integer wf_convert_b7_busan ()
# public function integer wf_update_11_busan (string as_rdate)
# public function integer wf_convert_b2_jockey ()
# public function integer wf_update_11 (string as_rcity, string as_rdate)
# public function integer wf_update_pop11 (string as_rcity, string as_rdate, integer ai_rno)
# public function integer w_convert_b3_trainer ()
# public function integer wf_convert_b3_trainer ()
# end prototypes

# public function integer wf_convert_11 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_imdate, ls_rdate, ls_rday, ls_rcity, ls_grade, ls_dividing, ls_rname, ls_rcon1, ls_rcon2, ls_weather, ls_rstate, ls_rmoisture
# Long		ll_rno, ll_rseq, ll_distance
# Long		ll_prize, ll_prize1, ll_prize2, ll_prize3, ll_prize4, ll_prize5, ll_subprize1, ll_subprize2, ll_subprize3

# Long		ll_rank, ll_gate, ll_pos, ll_rating
# String		ls_horse, ls_birthplace, ls_sex, ls_age, ls_jockey, ls_trainer, ls_host
# Double	ld_handicap

# Long		ll_weight, ll_record
# String		ls_weight, ls_record, ls_gap, ls_corners, ls_iweight

# String		ls_g1f, ls_g3f, ls_s1f, ls_1corner, ls_2corner, ls_3corner, ls_4corner
# Long		ll_g1f, ll_g3f, ll_s1f, ll_1corner, ll_2corner, ll_3corner, ll_4corner
# String		ls_gsingle, ls_gdouble

# Double	ld_alloc
# String		ls_pair
# Long 		ll_pair1, ll_pair2

# Dec		ld_sale1, ld_sale2, ld_sale3, ld_sale4, ld_sale5, ld_sale6, ld_sale7, ld_sale8

# String		ls_r1alloc, ls_r3alloc, ls_r2alloc, ls_r12alloc, ls_r23alloc, ls_r333alloc, ls_r123alloc, ls_r4f, ls_r3f

# String		ls_furlong, ls_passage, ls_passage_t
# String		ls_passage_s1f, ls_passage_1c, ls_passage_2c, ls_passage_3c, ls_passage_4c, ls_passage_g1f, ls_fast

# Long		ll_seq				// rec013 rno seq


# String	ls_t_type, ls_t_detail, ls_t_reason, ls_t_horse, ls_t_jockey, ls_t_trainer, ls_t_sort
# Long		ll_t_gate    // 징계사유를 등록할 게이트 번호 , 이 번호로 기수와 조교사, 마필명을 가져온다.


# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )				//포커스의 시작점을 가리킨다.  
#     	ls_text = trim(mle_krafile.TextLine())		// 값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		IF Left(ls_text,10) = '----------' THEN ll_handle = Mod(ll_handle + 1,14)

# 		CHOOSE CASE ll_handle

# 			CASE 0					//경주 제반조건 설정을 읽어들인다.

# 				IF	Trim(Mid(ls_text,1,2)) = '제목'  THEN													//제    목
				
# 					ls_imdate = Mid(ls_text,6,12)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 					ls_rdate  = '20' + Mid(ls_imdate,1,2) + Mid(ls_imdate,4,2) + Mid(ls_imdate,7,2)	//경주일자
# 					ls_rday = Mid(ls_text,16,1)
																											
# 					ll_rno = Long(Mid(ls_text,21,2))														//경주번호
					
# 				ELSEIF Left(ls_text,1) = '(' THEN														//(서울)
				
# 					ls_rcity = Mid(ls_text,2,2)	
# 					ll_rseq = Long(Mid(ls_text,7,2))
# 					ll_distance = Long(Mid(ls_text,11,4))									//거리
# 					ls_grade = Trim(Mid(ls_text,17,6))										//등급
# //					ls_dividing = Trim(Mid(ls_text,24,8))										//경주구분
# 					ls_dividing = Trim(Mid(ls_text,pos(ls_text, '경주명') -10 ,10))
# 					ls_rname = Trim(Mid(ls_text,pos(ls_text, '경주명') + 6,30))									//경주명
					
# //					SELECT rdate INTO :ls_rdate FROM rec010 									//기존 입력여부 확인 
# //					 WHERE rcity = :ls_rcity
# //					   AND rdate = :ls_rdate  
# //					   AND rno = :ll_rno ;
# //					 
# //					IF SQLCA.SQLNROWS > 0 THEN
# //						MessageBox("알림","이미 입력되어있는 데이타입니다. 데이타를 확인하십시오!")
# //						Return -1
# //					END IF

# 				ELSEIF Left(ls_text,4) = '경주조건' THEN																	//경주조건
					
# 					ls_rcon1 = Trim(Mid(ls_text,6,12))	
# 					ls_rcon2 = Trim(Mid(ls_text,19,Pos(ls_text,'날씨') - 19))									//경주조건

# 					ls_weather = Mid(ls_text,Pos(ls_text,'날씨') + 3,2)

# 					ls_rstate = Mid(ls_text,Pos(ls_text,'주로') + 3,2)
# 					ls_rmoisture = Trim(Mid(ls_text, Pos(ls_text,'주로') + 5,10))

# 				ELSEIF Left(ls_text,4) = '순위상금' THEN												//착순상금
					
# 					ll_prize1 = Dec(Trim(Mid(ls_text,6,7)))
# 					ll_prize2 = Dec(Trim(Mid(ls_text,16,7)))
# 					ll_prize3 = Dec(Trim(Mid(ls_text,26,7)))
# 					ll_prize4 = Dec(Trim(Mid(ls_text,36,7)))
# 					ll_prize5 = Dec(Trim(Mid(ls_text,46,7)))

# 				ELSEIF Left(ls_text,4) = '부가상금' THEN	 													//부가상금

# 					ll_subprize1 = Dec(Trim(Mid(ls_text,6,7)))
# 					ll_subprize2 = Dec(Trim(Mid(ls_text,16,7)))
# 					ll_subprize3 = Dec(Trim(Mid(ls_text,26,7)))

# 				END IF

# 			CASE 1						
				
# 					///////////////////////////////////////////////////////////////////////////
# 					////////// 경주제반조건 및 게이트별 마피및 기수,조교사 Insert /////////////
# 					///////////////////////////////////////////////////////////////////////////
					
# 				select rdate into :ls_rdate from rec010 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno ;
				
# 				IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
				
# 					UPDATE rec010  
# 						SET rday = :ls_rday,   				rseq = :ll_rseq,   			distance = :ll_distance,   			grade = :ls_grade,   
# 							 dividing = :ls_dividing,  	rname = :ls_rname,   		rcon1 = :ls_rcon1,   					rcon2 = :ls_rcon2,   				
# 							 weather = :ls_weather,   		rstate = :ls_rstate,   		rmoisture = :ls_rmoisture,   			rtime = null,   					
# 							 r1award = :ll_prize1,   		r2award = :ll_prize2,   	r3award = :ll_prize3,   				r4award = :ll_prize4,   				
# 							 r5award = :ll_prize5,   		sub1award = :ll_subprize1, sub2award = :ll_subprize2,				sub3award = :ll_subprize3 					
# 					 WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;
					 
# 					IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","경주 제반조건을 Update 하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 							ROLLBACK ;
# 							Return -1
# 					END IF
					
# 					COMMIT;
				
				
# 				ELSE
					
# 					INSERT INTO rec010  
# 							( rcity,   						rdate,   						rno,   						rday,   							rseq,   							distance,   					grade,   
# 							  dividing,   					rname,   						rcon1,   					rcon2,   						weather,   						rstate,   						rmoisture,   
# 							  rtime,   						r1award,   						r2award,   					r3award,   						r4award,   						r5award,   						sub1award,   
# 							  sub2award,   				sub3award,   					sale1,   					sale2,   						sale3,   						sale4,   						sale5,   
# 							  sale6,   						sale7,   						sales,   					r1alloc,   						r3alloc,   						r2alloc,   						r12alloc,   
# 							  r23alloc,   					r333alloc,   					r123alloc,   				passage_s1f,   				passage_1c,   					passage_2c,   				   passage_3c,   				
# 							  passage_4c,   				passage_g1f,   				r3f,   						 r4f,   							furlong,   						passage,   					   passage_t,   					
# 							  race_speed, 					r_judge )  
# 				  	VALUES ( :ls_rcity,   				:ls_rdate,   					:ll_rno,   					:ls_rday,   					:ll_rseq,   					:ll_distance,   				:ls_grade,   
# 							  :ls_dividing,   			:ls_rname,   					:ls_rcon1,   				:ls_rcon2,   					:ls_weather,   				:ls_rstate,   					:ls_rmoisture,   
# 							  null,   						:ll_prize1,   					:ll_prize2,   				:ll_prize3,   					:ll_prize4,   					:ll_prize5,   					:ll_subprize1,   
# 							  :ll_subprize2,   			:ll_subprize3,   				null,   						null,   							null,   							null,   							null,   							  
# 							  null,   						null,   							null,   						null,   							null,   							null,   							null,   							  
# 							  null,   						null,   							null,   					   null,   							null,   							null,   							null,   							  
# 							  null,   						null,   							null,   						null,   							null,   						   null,   							null,   							  
# 							  null, 							null )  ;

# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
# 						COMMIT;
# 					END IF
				
# 			CASE 2						//경주순위 및 기수,조교사 마주 등을 읽어들인다.
				
# 				IF Left(ls_text,10) <> '----------' THEN 
					
# 					IF Long( Right(Trim(Mid(ls_text,1,7)), 2) ) = 0 THEN 
# 						ll_rank = 99											//경주제외된 마필의 순위를 99로 지정한다
# 					ELSE
# 						ll_rank = Long(Trim(Mid(ls_text,1,4)))
# 					END IF
					
# 					IF ll_rank = 99 THEN 
# 						ll_gate = Long(Trim(Mid(ls_text,1,3)))									//게이트
# 						ls_horse = Trim(Mid(ls_text, Pos(ls_text, String(ll_gate)) + 2,11))										//마필명
# 					ELSE
# 						ll_gate = Long(Trim(Mid(ls_text,4,4)))									//게이트
# 						ls_horse = Trim(Mid(ls_text,9,11))										//마필명
# 					END IF
					
# 					IF Pos( ls_horse, ' ' ) > 0 THEN
# 						ls_horse = Mid( ls_horse, 1, Pos( ls_horse, ' ' ))
# 					END IF
					
# 					ll_pos = Pos(ls_text, ".")
# 					ls_birthplace = Trim(Mid(ls_text, ll_pos - 19,5))									//산지
										
# 					ls_sex = Trim(Mid(ls_text, ll_pos - 13, 2))											//성별
# 					ls_age = Trim(Mid(ls_text, ll_pos - 8, 4))											//연령
					
# 					ld_handicap = Dec(Mid(ls_text, ll_pos - 2, 4))										//부담중량
# 					ls_jockey = Trim(Mid(ls_text, ll_pos + 5, 4))										//기수
					
# 					ls_trainer = Trim(Mid(ls_text,  Pos(ls_text, ls_jockey) + 4 ,6))									//조교사
# 					ls_host = Trim(Mid(ls_text, Pos(ls_text, ls_trainer) + 4, 10))										//마주
					

# //					ll_rating = Long(Trim(Mid(ls_text, Pos(ls_text, ls_host) + 10, 10)))
# 					ll_rating = Long(Trim(Right(ls_text, 5)))
					
# 					IF ll_rank = 1 THEN 
# 						ll_prize = ll_prize1 + ll_subprize1
# 					ELSEIF ll_rank = 2 THEN 
# 						ll_prize = ll_prize2 + ll_subprize2
# 					ELSEIF ll_rank = 3 THEN 
# 						ll_prize = ll_prize3 + ll_subprize3
# 					ELSEIF ll_rank = 4 THEN 
# 						ll_prize = ll_prize4
# 					ELSEIF ll_rank = 5 THEN 
# 						ll_prize = ll_prize5
# 					ELSE
# 						ll_prize = 0
# 					END IF

# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
					
# 						UPDATE rec011  
# 							SET rank = :ll_rank,         horse = :ls_horse,          birthplace = :ls_birthplace,              h_sex = :ls_sex,              h_age = :ls_age,              
# 								 handycap = :ld_handicap, jockey = :ls_jockey,			trainer = :ls_trainer,        				host = :ls_host,              rating = :ll_rating				
# 						 WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate ;
						 
# 						IF SQLCA.SQLCODE <> 0 THEN
# 								MessageBox("알림","rec011 Update Fail " +  SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ))
# 								ROLLBACK ;
# 								Return -1
# 						END IF
						
# 						COMMIT;
						
# 					ELSE
					
# 						  INSERT INTO rec011  
# 									( rcity,          rdate,             rno,              gate,              rank,              horse,              birthplace,              h_sex,              h_age,              handycap,   
# 									  jockey,         joc_adv,           trainer,          host,              rating			  )  
# 						  VALUES ( :ls_rcity,     	:ls_rdate,         :ll_rno,          :ll_gate,          :ll_rank,          :ls_horse,          :ls_birthplace,          :ls_sex,            :ls_age,            :ld_handicap,   
# 									  :ls_jockey,     null,              :ls_trainer,      :ls_host,          :ll_rating     )  ;
			  					
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","rec011 Insert Fail " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
						
# 						COMMIT;
# 					END IF

# 				END IF				
				
# 			CASE 3						//skip
# 			CASE 4						//마필기록 
					
# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					IF Long( Right(Trim(Mid(ls_text,1,7)), 2) ) = 0 THEN 
# 						ll_rank = 99											//경주제외된 마필의 순위를 99로 지정한다
						
# 					ELSE
# 						ll_rank = Long(Trim(Mid(ls_text,1,4)))
# 					END IF
					
# 					IF ll_rank = 99 THEN 
# 						ll_gate = Long(Trim(Mid(ls_text,1,3)))									//게이트
# 						ls_horse = Trim(Mid(ls_text, Pos(ls_text, String(ll_gate)) + 2,11))										//마필명
# //						MessageBox("", ls_horse)
# 					ELSE
# 						ll_gate = Long(Trim(Mid(ls_text,4,4)))									//게이트
# 						ls_horse = Trim(Mid(ls_text,9,11))										//마필명
# 					END IF
					
# 					ll_pos = Pos( ls_text, ":")
# 					ll_weight = Long(Mid(ls_text, ll_pos - 10, 3))										//마체중
# 					ls_iweight = Trim(Mid(ls_text,ll_pos - 6, 3))									//마체중 증감
# 					ls_record = Trim(Mid(ls_text, ll_pos -1, 6))										//기록(String)
					
# 					ll_record = f_change_s2t(ls_record)										//수치로 변환된 기록
					
# 					ls_gap = Trim(Mid(ls_text, ll_pos + 6, 8))									//착차
# 					ls_corners = Trim(Right(ls_text, 20))									//코너별 전개
					
					
# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE rec011  
#      							SET h_weight = :ll_weight, 	w_change = :ls_iweight,		record = :ls_record,	i_record = :ll_record,	gap = :ls_gap,		corners = :ls_corners  
#    							WHERE rec011.rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF

# 			CASE 5						//skip
# 			CASE 6						//코너별 전개기록

# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					IF Len(Trim(Mid(ls_text,1,8))) <= 2 THEN
# 						ll_rank = 99	
						
						
# 					ELSE
# 						ll_rank = Long(Trim(Mid(ls_text,1,4)))
# 					END IF
					
# 					IF ll_rank = 99 THEN 
# 						ll_gate = Long(Trim(Mid(ls_text,1,2)))										//게이트
						
# 					ELSE
# 						ll_gate = Long(Trim(Mid(ls_text,4,4)))									//게이트
# 					END IF

# 					IF ll_rank = 99 THEN
# 						ls_g3f = ''
						
# 						ls_s1f = ''											//S1F(String)
# 						ls_1corner =''
# 						ls_2corner = ''
# 						ls_3corner = ''
# 						ls_4corner = ''
						

# 						ls_g1f = ''
						
# 						//ls_gsingle = Trim(Mid(ls_text, ll_pos + 44, 6))						//단승식 배당(인기순위1)
# 						//ls_gdouble = Trim(Mid(ls_text, ll_pos + 52, 6))								//연승식 배당(인기순위2)
						
# 						ls_gsingle = Trim(Mid( Right(ls_text, 14), 1, 7 ))						//단승식 배당(인기순위1)
# 						ls_gdouble = Trim(Right(ls_text, 7))								//연승식 배당(인기순위2)
						

# 					ELSE
# 						ll_pos = Pos(ls_text, ".")
# 						ls_g3f = Mid(ls_text, ll_pos - 2, 4)											//G3F(String)
# 						ls_s1f = Mid(ls_text,ll_pos + 6, 6)												//S1F(String)
# 						ls_1corner = Mid(ls_text, ll_pos + 14, 6)
# 						ls_2corner = Mid(ls_text, ll_pos + 22, 6)
# 						ls_3corner = Mid(ls_text, ll_pos + 30, 6)
# 						ls_4corner = Mid(ls_text, ll_pos + 38, 6)
						

# 						ls_g1f = Trim(  Mid(ls_text, ll_pos+ 46, 7) )
	
						
# 						//ls_gsingle = Trim(Mid(ls_text, ll_pos + 54, 6))						//단승식 배당(인기순위1)
# 						//ls_gdouble = Trim(Mid(ls_text, ll_pos + 62, 6))								//연승식 배당(인기순위2)
						
						
												
# 						ls_gsingle = Trim(Mid( Right(ls_text, 14), 1, 7 ))						//단승식 배당(인기순위1)
# 						ls_gdouble = Trim(Right(ls_text, 7))								//연승식 배당(인기순위2)
						
# 					END IF
					
					
# 					// select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
# 					select gap into :ls_gap from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
					
# 					IF right( ls_gap, 2) = '제외' or right( ls_gap, 2) = '취소' THEN
# 						ls_gsingle = ''
# 						ls_gdouble = ''
# 					END IF
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
					
						

# 						  UPDATE rec011  
#      							SET rg3f = :ls_g3f, 	rs1f = :ls_s1f,		r1c = :ls_1corner,	r2c = :ls_2corner,	  r3c = :ls_3corner,		r4c = :ls_4corner,  
# 								    rg1f = :ls_g1f,	alloc1r = :ls_gsingle, alloc3r = :ls_gdouble 
#    							WHERE rec011.rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;
								
	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF
				
# 			CASE 77						//복승식 배당률 - 각 마필간 인기순위
				
# 				IF Left(ls_text,10) = '----------' OR Trim(ls_text) = '(복승식 배당률)' THEN 
					
# 				ELSE
					
# 					/*	1 et of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 1, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 6, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	2 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 14, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 19, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	3 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 28, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 33, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	4 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 42, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 47, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	5 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 56, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 61, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	6 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 70, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 75, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# 						IF SQLCA.SQLCODE = -1 THEN
# 							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# 							ROLLBACK ;
# 							Return -1
# 						END IF		
# 						COMMIT;
						
# 					END IF

# 				END IF
		
# 			CASE 8						//해당경주 승식별 매출액
				
# 					IF Left(ls_text,3) = '매출액' THEN 
	
# 						ld_sale1 = Dec(Trim(Mid(ls_text,Pos(ls_text, "단식:") + 3, 15)))				//단식 매출액
# 						ld_sale2 = Dec(Trim(Mid(ls_text,Pos(ls_text, "연식:") + 3, 15)))				//연식 매출액
# 						ld_sale3 = Dec(Trim(Mid(ls_text,Pos(ls_text, "복식:") + 3, 15)))				//복식 매출액			
		
# 					ELSEIF Left(ls_text,2) = '복연' THEN 
# 						ld_sale4 = Dec(Trim(Mid(ls_text,Pos(ls_text, "복연:") + 3, 15)))				//연식 매출액
# 						ld_sale5 = Dec(Trim(Mid(ls_text,Pos(ls_text, "쌍식:") + 3, 15)))				//복식 매출액	
# 						ld_sale6 = Dec(Trim(Mid(ls_text,Pos(ls_text, "삼복:") + 3, 15)))				//복식 매출액	
# 					ELSEIF Left(ls_text,2) = '삼쌍' THEN 
# 						ld_sale7 = Dec(Trim(Mid(ls_text,Pos(ls_text, "삼쌍:") + 3, 15)))				//연식 매출액
# 						ld_sale8 = Dec(Trim(Mid(ls_text,Pos(ls_text, "합계:") + 3, 15)))				//복식 매출액	
# 					END IF
					
# 					UPDATE rec010  
# 						  SET sale1 = :ld_sale1,            sale2 = :ld_sale2,            sale3 = :ld_sale3,            sale4 = :ld_sale4,            
# 						      sale5 = :ld_sale5,            sale6 = :ld_sale6,            sale7 = :ld_sale7,            sales = :ld_sale8
# 					 WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;
	
		
# 					IF SQLCA.SQLCODE = -1 THEN
# 						MessageBox("알림","rec010 Table Insert Fail!  Sales  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# 						ROLLBACK ;
# 						Return -1
# 					END IF		
							
# 					COMMIT;
				
				
# 			CASE 9						//승식별 배당률
				
# 				IF Left(ls_text,3) = '배당률' THEN 
	
# 						ls_r1alloc = Trim(Mid(ls_text, Pos(ls_text, "단:") + 2, Pos(ls_text, "연:") - Pos(ls_text, "단:") -2 ))				//단식 배당률
# 						ls_r3alloc = Trim(Mid(ls_text, Pos(ls_text, "연:") + 2, Pos(ls_text, "복:") - Pos(ls_text, "연:") -2 ))				//연식 배당률
# 						ls_r2alloc = Trim(Mid(ls_text, Pos(ls_text, "복:") + 2, Pos(ls_text, "4F:") - Pos(ls_text, "복:") -2))					//복식 배당률			
# 						ls_r4f = Trim(Mid(ls_text, Pos(ls_text, "4F:") + 3, 10))																		//4F	
		
# 					ELSEIF Trim(Left(ls_text,3)) = '3F:' THEN 
# 						ls_r3f = Trim(Mid(ls_text,Pos(ls_text, "3F:") + 3, 10))				//3F
# 					ELSEIF Trim(Left(ls_text,2)) = '쌍:' THEN 
# 						ls_r12alloc = Trim(Mid(ls_text,Pos(ls_text, "쌍:") + 2, 10))				//쌍
# 						ls_fast = Trim(right(ls_text,1))													//주로빠르기
						
# 					ELSEIF Left(ls_text,3) = '복연:' THEN 
# 						ls_r23alloc = Trim(Mid(ls_text,Pos(ls_text, "복연:") + 3, 25))				//연식 매출액
# 					ELSEIF Left(ls_text,3) = '삼복:' THEN 
# 						ls_r333alloc = Trim(Mid(ls_text,Pos(ls_text, "삼복:") + 3, 25))				//연식 매출액
# 					ELSEIF Left(ls_text,3) = '삼쌍:' THEN 
# 						ls_r123alloc = Trim(Mid(ls_text,Pos(ls_text, "삼쌍:") + 3, 25))				//연식 매출액
# 					END IF
					
# 					  UPDATE rec010  
# 						  SET r1alloc = :ls_r1alloc,   
# 								r3alloc = :ls_r3alloc,   
# 								r2alloc = :ls_r2alloc,   
# 								r12alloc = :ls_r12alloc,   
# 								r23alloc = :ls_r23alloc,   
# 								r333alloc = :ls_r333alloc,   
# 								r123alloc = :ls_r123alloc,   
# 								r3f = :ls_r3f,   
# 								r4f = :ls_r4f ,
# 								race_speed = :ls_fast
# 						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;

# 					IF SQLCA.SQLCODE = -1 THEN
# 						MessageBox("알림","rec010 Table Insert Fail!  Sales  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# 						ROLLBACK ;
# 						Return -1
# 					END IF		
							
# 					COMMIT;

# 			CASE 10								//화롱타임,통과M,통과T
				
# 				IF Trim(Left(ls_text,4)) = '펄 롱:' THEN 
# 					ls_furlong = Trim(Mid(ls_text,Pos(ls_text, "펄 롱:") + 4, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = '통과M:' THEN 
# 					ls_passage = Trim(Mid(ls_text,Pos(ls_text, "통과M:") + 4, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = '통과T:' THEN 
# 					ls_passage_t = Trim(Mid(ls_text,Pos(ls_text, "통과T:") + 4, 100))
# 				END IF
					
# 					  UPDATE rec010  
# 						  SET furlong = :ls_furlong,
# 						  	    passage = :ls_passage,
# 								passage_t = :ls_passage_t
# 						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;

# 					IF SQLCA.SQLCODE = -1 THEN
# 						MessageBox("알림","rec010 Table Insert Fail!  passage  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# 						ROLLBACK ;
# 						Return -1
# 					END IF		
							
# 					COMMIT;

# 			CASE 11								//코너별 통과순위
				
				
# //				MessageBox("", Trim(Left(ls_text,4)))
				
# 				IF Trim(Left(ls_text,4)) = '통과순위' THEN 
# 					ls_passage_s1f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = 'C1 :' THEN 
# 					ls_passage_1c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = 'C2 :' THEN 
# 					ls_passage_2c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = 'C3 :' THEN 
# 					ls_passage_3c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = 'C4 :' THEN 
# 					ls_passage_4c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = 'G-1F' THEN 
# 					ls_passage_g1f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				END IF
					
# 					  UPDATE rec010  
# 						  SET passage_s1f = :ls_passage_s1f,
# 						  	    passage_1c = :ls_passage_1c,
# 								passage_2c = :ls_passage_2c,
# 								passage_3c = :ls_passage_3c,
# 								passage_4c = :ls_passage_4c,
# 								passage_g1f = :ls_passage_g1f
# 						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;

# 					IF SQLCA.SQLCODE = -1 THEN
# 						MessageBox("알림","rec010 Table Insert Fail!  passage  " + SQLCA.SQLErrText + ls_passage_s1f )
# 						ROLLBACK ;
# 						Return -1
# 					END IF		
							
# 					COMMIT;

# 			CASE 12							//Skip
# 			CASE 13							//특기사항

# //		ls_t_type, ls_t_detail, ls_t_reason

# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					IF Len(ls_text) >= 3 THEN
						
# 						ls_t_type = Trim(Mid(ls_text, 25, 9))	
						
# 						ls_t_sort = Trim(Mid(ls_text, 1, 5))	
						
# 						ll_t_gate = Integer(Trim(Mid(ls_text, 5, 5)))
						
# 						select horse, jockey, trainer into :ls_t_horse, :ls_t_jockey, :ls_t_trainer from rec011 where rcity = :ls_rcity and  rdate = :ls_rdate and rno = :ll_rno and gate = :ll_t_gate ;
						
# 						IF ls_t_type = '과태금' THEN
							
# 							ls_t_detail = Trim(Mid(ls_text, 25 + 9, 20 ))	
# 							ls_t_reason = Trim(Mid(ls_text, 25 + 9 + 20 , 100))	
							
# 						ELSEIF Mid(ls_t_type,3,2) = '정지' THEN
							
# 							ll_pos = Pos( ls_text, ")")
# 							ls_t_detail = Trim(Mid(ls_text, Pos( ls_text, "(") - 5, Pos( ls_text, ")") - Pos( ls_text, "(") + 5 +1 ))	
# 							ls_t_reason = Trim(Mid(ls_text, ll_pos + 1 , 100))	
							
# 						ELSE
							
# 							ls_t_detail = ''
# 							ls_t_reason = Trim(Mid(ls_text, 27 + 9 + 20 , 100))	
							
# 						END IF
						
# 						IF ls_t_type = '경주부' or ls_t_type = '경주부적' or ls_t_type = '경주부적격' THEN ls_t_type = '경주부적격마' 
# 						IF ls_t_type = '주행심'  THEN ls_t_type = '주행심사' 
# 						IF ls_t_type = '주행중'  THEN ls_t_type = '주행중지' 
# 						IF ls_t_type = '출발심'  THEN ls_t_type = '출발심사' 
# 						IF ls_t_type = '출전정'  THEN ls_t_type = '출전정지' 
# 						IF ls_t_type = '출전제'  THEN ls_t_type = '출전제외' 
# 						IF ls_t_type = '출전취'  THEN ls_t_type = '출전취소' 
						
						
					
# 						INSERT INTO rec015  
# 							( rcity, 		rdate,		rno,		gate,		t_sort,		 horse,		t_type,		t_detail,		t_reason, 		jockey,		trainer ,		t_text )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,	:ll_rno,	:ll_t_gate,	:ls_t_sort,		:ls_t_horse,		:ls_t_type,		:ls_t_detail,		:ls_t_reason, 	:ls_t_jockey,		:ls_t_trainer,	:ls_text ) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec015 Table Insert Fail! " + SQLCA.SQLErrText + ls_t_horse  + ' ' +  ls_t_type )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# 						COMMIT;

# 					END IF
					
# 				END IF
				
# 		END CHOOSE
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
   
# NEXT

# ipos = 0

# /* 인기도 update */
# For i = 1 to ll_rno
	
# 	// IF wf_update_pop11( ls_rcity, ls_rdate, i ) = -1 Then EXIT
# 	wf_update_pop11( ls_rcity, ls_rdate, i )
	
# NEXT

# update rec011 a
#       set horse = replace(  replace(horse, '[서]', ''), '[부]', ''), 
#            distance_w = ( select distance from rec010 where rcity = a.rcity and rdate = a.rdate and rno = a.rno ) 
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;

# update rec011 a set distance_w = ( select distance from rec010 where rcity = a.rcity and rdate = a.rdate and a.rno = rno )  
#  where rcity = :ls_rcity and rdate = :ls_rdate 
#  ;
# commit ;

# update rec011
#       set jockey_w = f_jockey_w( rdate, jockey), 
#            burden_w =  f_burden_w(rdate, handycap, distance_w,jockey) 
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;



# update rec015 set horse = replace(  replace(horse, '[서]', ''), '[부]', '')
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;

# update rec010 set rmoisture = replace( replace(  replace(rmoisture, '%', ''), '(', ''), ')', '' )
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;


# update exp011 a 
#      set r_rank  = ( select rank from rec011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ) ,
# 		  r_record  = ( select record from rec011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ) ,
# 		  ir_record  = ( select i_record from rec011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# 		  h_weight =  ( select concat(h_weight, ' ', w_change) from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate  ),
# 		  alloc1r =  ( select alloc1r from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate  ) ,
#      	  alloc3r =  ( select alloc3r from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate  )
		  
		  
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;

# commit ;


# String	ls_rs1f, ls_r1c,  ls_r2c, ls_r3c, ls_r4c, ls_rg3f, ls_rg2f, ls_rg1f
# Integer	i_rno, i_gate

# Integer	i_s1f, i_r1c, i_r2c, i_r3c, i_r4c, i_g3f, i_g2f, i_g1f, i_record

# DECLARE C_race CURSOR FOR  
#  SELECT rcity, rdate, rno, gate, rs1f, r1c, r2c, r3c, r4c, rg3f, rg2f, rg1f, record
#    FROM rec011  
#   WHERE rcity = :ls_rcity and rdate = :ls_rdate
#  ;
	
# OPEN C_race ;

# FETCH C_race INTO :ls_rcity, :ls_rdate, :i_rno, :i_gate, :ls_rs1f, :ls_r1c, :ls_r2c, :ls_r3c, :ls_r4c, :ls_rg3f, :ls_rg2f, :ls_rg1f, :ls_record ;

# DO WHILE SQLCA.SQLCODE = 0 
	
# 	i_s1f = f_s2t( ls_rs1f )
# 	i_r1c =  f_s2t( ls_r1c ) 
# 	i_r2c =  f_s2t( ls_r2c ) 
# 	i_r3c =  f_s2t( ls_r3c ) 
# 	i_r4c =  f_s2t( ls_r4c ) 
# 	i_g3f =  f_s2t( ls_rg3f ) 
# 	i_g2f =  ( f_s2t( ls_rg3f ) +  f_s2t( ls_rg1f ) ) /2 			//	g2f 환산  (g3f + g1f) / 2
# 	ls_rg2f = f_t2s( i_g2f)													//	g2f 환산기록 스트링 변환
# 	i_g1f =  f_s2t( ls_rg1f ) 
# 	i_record =  f_s2t( ls_record )
	
# 	update rec011 set i_s1f = :i_s1f, i_r1c = :i_r1c, i_r2c = :i_r2c, i_r3c = :i_r3c, i_r4c = :i_r4c, i_g3f = :i_g3f, i_g2f = :i_g2f , i_g1f = :i_g1f, i_record = :i_record, rg2f = :ls_rg2f 
# 	 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :i_rno and gate = :i_gate ;
	 
# 	IF sqlca.sqlnrows > 0 THEN
# //		COMMIT ;
# 	ELSE
# 		ROLLBACK;
# 		MessageBox("알림", SQLCA.SQLErrText + ls_Record )
# 		Return -1
# 	END IF
	
# 	FETCH C_race INTO :ls_rcity, :ls_rdate, :i_rno, :i_gate, :ls_rs1f, :ls_r1c, :ls_r2c, :ls_r3c, :ls_r4c, :ls_rg3f, :ls_rg2f, :ls_rg1f, :ls_record ;
	
# LOOP

# CLOSE C_race ;

# COMMIT ;

# update rec011 a
#  set recent3 = ( select recent3 from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  recent5 = ( select recent5 from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  fast_r = ( select fast_r from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  slow_r = ( select slow_r from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  avg_r = ( select avg_r from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  convert_r = ( select convert_r from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  i_cycle = ( select i_cycle from The1.exp011 where rdate = a.rdate and rcity = a.rcity and rno = a.rno and gate = a.gate ) ,
 
#  r_pop = ( select r_pop from The1.exp011 where rdate = a.rdate and rcity = a.rcity and rno = a.rno and gate = a.gate ) ,
 
# gear1 = ( select gear1 from The1.exp012 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# gear2 = ( select gear2 from The1.exp012 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# treat1 = ( select treat1 from The1.exp012 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# treat2 = ( select treat2 from The1.exp012 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# reason = ( select reason from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),

# gap_b = ( select max(gap) from The1.rec011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.rank = rank - 1 ),

# jt_per = ( select jt_per from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# jt_cnt = ( select jt_cnt from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# jt_1st = ( select jt_1st from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# jt_2nd = ( select jt_2nd from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# jt_3rd = ( select jt_3rd from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# h_cnt = ( select count(*) from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno ) ,
# h_mare = ( select sum( if( h_sex = '암', 1, 0 )) from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno )
 
# // s1f_rank = ( select s1f_rank from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
# // g1f_rank = ( select g1f_rank from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate )
# where rcity = :ls_rcity and rdate = :ls_rdate
#  ;

# commit;

# update rec011
# set s1f_rank = replace( replace( substr( corners, 1, 2 ), '-', '') , ' ', '' ) * 1,
# g1f_rank = replace( replace( substr( corners, -2 ), '-', '') , ' ', '' ) * 1,
# g2f_rank = replace( replace( substr( corners, -5, 2 ), '-', '') , ' ', '' ) * 1,
# g3f_rank = replace( replace( substr( corners, -8, 2 ), '-', '') , ' ', '' ) * 1
# where rcity = :ls_rcity and rdate = :ls_rdate
# and rank <= 20
# and isnull(judge) 
 
# ;

# commit;


# update exp011 a
# set 
#  corners = ( select corners from rec011 where rdate = a.rdate and rcity = a.rcity and rno = a.rno and gate = a.gate ),
#  r_s1f = ( select substr(rs1f,-4)  from rec011 where rdate = a.rdate and rcity = a.rcity and rno = a.rno and gate = a.gate ),
#  r_g3f = ( select substr(rg3f,-4) from rec011 where rdate = a.rdate and rcity = a.rcity  and rno = a.rno and gate = a.gate ),
#  r_g1f = ( select substr(rg1f, -4) from rec011 where rdate = a.rdate and rcity = a.rcity  and rno = a.rno and gate = a.gate ),
#  alloc1r = ( select alloc1r from rec011 where rdate = a.rdate and rcity = a.rcity  and rno = a.rno and gate = a.gate ),
#  alloc3r = ( select alloc3r from rec011 where rdate = a.rdate and rcity = a.rcity  and rno = a.rno and gate = a.gate )
# where rcity = :ls_rcity and rdate = :ls_rdate
#  ;
# commit;


# update The1.rec010 a
# set r1_j1 = (select jockey from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank =  1 and gap = '') ,
# r1_j2 = (select jockey from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank =  1 and gap like '%동%' ),
# r2_j1 = (select jockey from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank =  2 and gap not like '%동%'),
# r2_j2 = (select jockey from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank =  2 and gap like '%동%' ),
# r3_j1 = (select jockey from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank =  3 and gap not like '%동%'),
# r3_j2 = (select jockey from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and rank =  3 and gap like '%동%' ),
# r2alloc1 = if(locate(' ', r2alloc) = 0, substr( r2alloc, 3), substr( r2alloc, 3, locate( ' ', r2alloc )-2)), 
# r2alloc2 = if(locate(' ', r2alloc) = 0, 0,substr( r2alloc, locate( ' ', r2alloc) + 3)), 
# r333alloc1 = if(locate(' ', r333alloc) = 0, substr( r333alloc, 4), substr( r333alloc, 4, locate( ' ', r333alloc )-3)),
# r333alloc2 = if(locate(' ', r333alloc) = 0, 0 , substr( r333alloc, locate( ' ', r333alloc) + 5))
# where a.rdate = :ls_rdate
# and a.sales is not null
# and a.sales > 100000000
# ;

# commit;

# update The1.rec010 a
# set jockeys = concat( r1_j1, ifnull(r1_j2, ''), ifnull(r2_j1, '') , ifnull(r2_j2, '') , ifnull(r3_j1, '') , ifnull(r3_j2, '') )
# where r1_j1 is not null
# and rdate = :ls_rdate
# ;

# commit;


# Return 1
# end function

# public function integer wf_convert_23 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_imdate, ls_rdate, ls_rday, ls_rcity, ls_grade, ls_dividing, ls_rname, ls_rcon1, ls_rcon2, ls_weather, ls_rstate, ls_rmoisture
# Long		ll_rno, ll_rseq, ll_distance
# Long		ll_prize, ll_prize1, ll_prize2, ll_prize3, ll_prize4, ll_prize5, ll_subprize1, ll_subprize2, ll_subprize3

# Long		ll_rank, ll_gate, ll_pos, ll_rating
# String		ls_horse, ls_birthplace, ls_sex, ls_age, ls_jockey, ls_trainer, ls_host
# Double	ld_handicap

# Long		ll_weight, ll_record
# String		ls_weight, ls_record, ls_gap, ls_corners, ls_iweight

# String		ls_g1f, ls_g3f, ls_s1f, ls_1corner, ls_2corner, ls_3corner, ls_4corner
# Long		ll_g1f, ll_g3f, ll_s1f, ll_1corner, ll_2corner, ll_3corner, ll_4corner
# String		ls_gsingle, ls_gdouble

# Double	ld_alloc
# String		ls_pair
# Long 		ll_pair1, ll_pair2

# Dec		ld_sale1, ld_sale2, ld_sale3, ld_sale4, ld_sale5, ld_sale6, ld_sale7, ld_sale8

# String		ls_r1alloc, ls_r3alloc, ls_r2alloc, ls_r12alloc, ls_r23alloc, ls_r333alloc, ls_r123alloc, ls_r4f, ls_r3f

# String		ls_furlong, ls_passage, ls_passage_t
# String		ls_passage_s1f, ls_passage_1c, ls_passage_2c, ls_passage_3c, ls_passage_4c, ls_passage_g1f

# Long		ll_seq				// rec013 rno seq

# String		ls_judge, ls_judge_reason, ls_audit_reason


# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )				//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		IF Left(ls_text,10) = '----------' THEN ll_handle = Mod(ll_handle + 1, 8)

# 		CHOOSE CASE ll_handle

# 			CASE 0					//경주 제반조건 설정을 읽어들인다.

# 				IF	Trim(Mid(ls_text,1,2)) = '제목'  THEN													//제    목
				
				
# 					ls_imdate = Mid(ls_text,6,12)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 					ls_rdate  = '20' + Mid(ls_imdate,1,2) + Mid(ls_imdate,4,2) + Mid(ls_imdate,7,2)	//경주일자
					
# 					select replace( :ls_rdate, ' ', '0' ) into :ls_rdate from dual ;
					
# 					ls_rday = Mid( ls_text, Pos( ls_text, ')' ) - 1, 1)									//	요일
					
# 					ll_rseq = Long (Mid( ls_text, Pos( ls_text, ')' ) + 5, 2)	)						//	제 몇차
																											
# 					ll_rno = Long(Mid(ls_text, Pos( ls_text, "경주") - 2,2))						//경주번호
					
					
					
# 				ELSEIF Left(ls_text,1) = '날' THEN														//(서울)
				
# 					ls_rcity = '서울'	

# 					ll_distance = 1000																//거리
# 					ls_grade = '주행검사'														//등급
# 					ls_dividing = '주행검사'
# 					ls_rname = '주행검사'														//경주명
					
# 					ls_weather =  Trim( Mid( ls_text, Pos( ls_text, ':' ) + 1, 6))			//날씨
# 					ls_rstate =  Trim( Mid( ls_text, Pos( ls_text, '주로상태 :' ) + 6, 4))
# 					ls_rmoisture = Trim( Mid( ls_text, Pos( ls_text, '(' ) - 1, 6))
					
# 					select rdate into :ls_rdate from rec010 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno ;
					
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 					ELSE
						
# 						INSERT INTO rec010  
# 								( rcity,   							rdate,   							rno,   							rday,   							rseq,   							distance,   						grade,   
# 								  dividing,   						rname,   							rcon1,   						rcon2,   							weather,   						rstate,   							rmoisture )  
# 						VALUES ( :ls_rcity,   					:ls_rdate,   						:ll_rno,   						:ls_rday,   						:ll_rseq,   						:ll_distance,   					:ls_grade,   
# 								  :ls_dividing,   					:ls_rname,   					:ls_rcon1,   					:ls_rcon2,   						:ls_weather,   					:ls_rstate,   						:ls_rmoisture )  ;
	
# 							IF SQLCA.SQLCODE <> 0 THEN
# 								MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 								ROLLBACK ;
# 								Return -1
# 							END IF					
# 							COMMIT;
# 						END IF

# 				END IF

# 			CASE 1								
# 			CASE 2						//경주순위 및 기수,조교사 마주 등을 읽어들인다.
				
# 				IF Left(ls_text,10) <> '----------' THEN 
					
# 					ll_rank = Long(Trim(Mid(ls_text,1,4)))
					
# 					ll_pos = Pos( ls_text, String(ll_rank))
# 					ll_gate = Long( Trim(Mid(ls_text, ll_pos + Len(String(ll_rank)), 7))	)									//게이트
					
# 					ls_text = Mid( ls_text,  ll_pos + Len(String(ll_rank)), 100 )
					
# 					ll_pos = Pos( ls_text, String(ll_gate))													//게이트 번호 위치 
# 					ls_horse = Trim(Mid(ls_text,ll_pos + Len(String(ll_gate)), 10))					//마필명
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ), 100) )
# 					ls_birthplace = Trim(Mid(ls_text, 1, 4)			)									//산지
										
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_birthplace ) + Len( ls_birthplace ), 100) )
# 					ls_sex = Trim( Mid( ls_text, 1, 2 ))													//성별
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_sex ) + Len( ls_sex ), 100) )
# 					ls_age = Trim(Mid(ls_text,1, 2))														//연령
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_age ) + Len( ls_age ), 100) )
# 					ld_handicap = Dec(Mid(ls_text,1, 2))													//부담중량
					
# 					IF Mid(ls_text,3, 1) = "+" THEN 														//추가 부담중량
# 						ld_handicap = ld_handicap + Dec(  Mid(ls_text,4, 3))
# 					ELSE
# 						ld_handicap = ld_handicap - Dec(  Mid(ls_text,4, 3))
# 					END IF
					
# 					ls_text = Trim( Mid( ls_text, 8, 100 ))
# 					ls_jockey = Trim(Mid(ls_text, 1, 4))													//기수
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey ) + Len( ls_jockey ), 100) )
# 					ls_trainer = Trim(Mid(ls_text, 1 ,6))													//조교사
					
# //					ls_host = Trim(Mid(ls_text, Pos(ls_text, ls_trainer) + 4, 10))										//마주
					
# //					ll_rating = Long(Trim(Mid(ls_text, Pos(ls_text, ls_host) + 10, 10)))

# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 					ELSE
					
# 						  INSERT INTO rec011  
# 									( rcity,              rdate,              rno,              gate,              rank,              horse,              birthplace,              h_sex,              h_age,              handycap,   
# 									  jockey,           joc_adv,           trainer,          host,              rating,						p_rank	  )  
# 						  VALUES ( :ls_rcity,     :ls_rdate,          	:ll_rno,           :ll_gate,          :ll_rank,           :ls_horse,          :ls_birthplace,          :ls_sex,            :ls_age,              :ld_handicap,   
# 									  :ls_jockey,       null,               :ls_trainer,       :ls_host,         :ll_rating,				0       )  ;
			  					
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","rec011 Insert Fail " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ))
							
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
						
# 						COMMIT;
# 					END IF
					

					

# 				END IF				
				
# 			CASE 3						//skip
# 			CASE 4						//마필기록 
					
# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					ll_rank = Long(Trim(Mid(ls_text,1, 2)))
					
# 					ll_pos = Pos( ls_text, String(ll_rank))
# 					ll_gate = Long( Trim(Mid(ls_text, ll_pos + Len(String(ll_rank)), 6)))									//게이트
					
# 					ls_text = Mid( ls_text,  ll_pos + Len(String(ll_rank)), 100 )
					
# 					ll_pos = Pos( ls_text, String(ll_gate))													//게이트 번호 위치 
# 					ls_horse = Trim(Mid(ls_text, ll_pos + Len(String(ll_gate)), 10))				//마필명
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ), 100) )
# 					ll_weight = Long( Trim( Mid(ls_text, 1, 3)) )											//마체중
					
# 					ls_iweight = ''																				//마체중 증감
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, String(ll_weight) ) + Len( String(ll_weight) ), 100) )
# 					ls_record = Trim(Mid(ls_text, 1, 6))													//기록(String)
					
# 					ll_record = f_change_s2t(ls_record)													//수치로 변환된 기록
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_record ) + Len( ls_record ), 100) )
# 					IF ll_rank = 1 THEN 
# 						ls_gap = ''
# 					ELSE
# 						ls_gap = Trim(Mid(ls_text, 1, 4))														//착차
# 					END IF
					
# //					ls_corners = Trim(Right(ls_text, 18))													//코너별 전개

# 					IF ls_gap = '' THEN 
# 						ls_judge =  Trim(Mid(ls_text, 1, 1))
# 					ELSE
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_gap ) + Len( ls_gap ), 100) )
# 						ls_judge = Trim(Mid(ls_text, 1, 1))													//	판정
# 					END IF
					
# 					IF ls_judge = '불'  or ls_judge = '유' THEN
						
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_judge ) + Len( ls_judge ), 100) )
# 						ls_judge_reason = Trim(Mid(ls_text, 1, 4))

# 						ls_audit_reason =  Trim(Mid(ls_text, 1, 10))
						
# 					ELSEIF  ls_judge = '합'  THEN
# 						ls_judge_reason = ""

# 					ELSE
# 						ls_judge = ""
# 						IF ls_gap = '출주취소' THEN 
# 							ls_judge_reason = Trim(Mid(ls_text, 1, 6)) 
# 						ELSE
# 							ls_judge_reason = ''
# 						END IF
						
# 					END IF

# 					ls_text = Trim( Right(ls_text,  10))
# 					ls_audit_reason = Trim( Mid( ls_text, Pos( ls_text, ' '), 10))
					
					
# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE rec011  
#      							SET h_weight = :ll_weight, 	w_change = :ls_iweight,		record = :ls_record,	i_record = :ll_record,	gap = :ls_gap,		corners = :ls_corners,
# 								       judge = :ls_judge,		judge_reason = :ls_judge_reason, 		audit_reason = :ls_audit_reason
#    							WHERE rec011.rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF

# 			CASE 5						//skip
# 			CASE 6						//코너별 전개기록

# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					ll_rank = Long(Trim(Mid(ls_text,1, 2)))
					
# 					ll_pos = Pos( ls_text, String(ll_rank))
# 					ll_gate = Long( Trim(Mid(ls_text, ll_pos + Len(String(ll_rank)), 6)))									//게이트
					
# 					ls_text = Mid( ls_text,  ll_pos + Len(String(ll_rank)), 100 )
					
# 					ll_pos = Pos( ls_text, String(ll_gate))													//게이트 번호 위치 
# 					IF ll_gate >= 10 THEN
# 						ls_g3f = Trim( Mid(ls_text, ll_pos + 2, 10))											//G3F(String)
# 					ELSE
# 						ls_g3f = Trim( Mid(ls_text, ll_pos + 1, 10))												//G3F(String)
# 					END IF
# 					ll_g3f = f_change_s2t(ls_g3f)													//G3F
					
# 					IF ll_rank > 90 THEN
# 						ls_s1f = ''
# 						ls_3corner = ''
# 						ls_4corner = ''
# 						ls_g1f = ''
# 						ls_corners = ''
# 					ELSE

# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_g3f) + 6, 100 ))
# 						ls_s1f = Trim( Mid(ls_text, 1, 6))														//S1F(String)
# 						ll_s1f = f_change_s2t(ls_s1f)													//S1F
						
# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_s1f) + 6, 100 ))
# 						ls_3corner = Trim( Mid(ls_text, 1, 6))
# 						ll_3corner = f_change_s2t(ls_3corner)
	
# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_3corner) + 6, 100 ))
# 						ls_4corner = Trim( Mid(ls_text, 1, 6))
# 						ll_4corner = f_change_s2t(ls_4corner)

# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_4corner) + 6, 100 ))
# 						ls_g1f = Trim( Mid(ls_text, 1, 6))														//S1F(String)
# 						ll_g1f = f_change_s2t(ls_g1f)													//S1F
						
# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_g1f) + 4, 100 ))
# 						ls_corners = Trim( Mid(ls_text, 1, 30)	)													//S1F(String)
						
	
# 					END IF
					
					

					
# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE rec011  
#      							SET rg3f = :ls_g3f, 	rs1f = :ls_s1f,		r1c = :ls_1corner,	r2c = :ls_2corner,	  r3c = :ls_3corner,		r4c = :ls_4corner,  rg1f = :ls_g1f,	corners = :ls_corners,
# 								  host = '심사'
#    							WHERE rec011.rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF
				
# //			CASE 7						//복승식 배당률 - 각 마필간 인기순위
# //				
# //				IF Left(ls_text,10) = '----------' OR Trim(ls_text) = '(복승식 배당률)' THEN 
# //					
# //				ELSE
# //					
# //					/*	1 et of 6 set */
# //					ls_pair =  Trim( Mid( ls_text, 1, 5 ))
# //					IF ls_pair <> '0- 0' THEN
# //						
# //						IF Len(ls_pair) = 4 THEN
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# //						ELSE
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# //						END IF
# //						
# //						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# //						ld_alloc = Dec(Mid( ls_text, 6, 8 ))
# //	
# //						INSERT INTO rec012  
# //							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# //						VALUES 
# //							( :ls_rdate,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
# //	
# ////						IF SQLCA.SQLCODE = -1 THEN
# ////							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# ////							ROLLBACK ;
# ////							Return -1
# ////						END IF		
# ////						COMMIT;
# //						
# //					END IF
# //					
# //					/*	2 set of 6 set */
# //					ls_pair =  Trim( Mid( ls_text, 14, 5 ))
# //					IF ls_pair <> '0- 0' THEN
# //						
# //						IF Len(ls_pair) = 4 THEN
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# //						ELSE
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# //						END IF
# //						
# //						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# //						ld_alloc = Dec(Mid( ls_text, 19, 8 ))
# //	
# //						INSERT INTO rec012  
# //							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# //						VALUES 
# //							( :ls_rdate,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
# //	
# ////						IF SQLCA.SQLCODE = -1 THEN
# ////							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# ////							ROLLBACK ;
# ////							Return -1
# ////						END IF		
# ////						COMMIT;
# //						
# //					END IF
# //					
# //					/*	3 set of 6 set */
# //					ls_pair =  Trim( Mid( ls_text, 28, 5 ))
# //					IF ls_pair <> '0- 0' THEN
# //						
# //						IF Len(ls_pair) = 4 THEN
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# //						ELSE
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# //						END IF
# //						
# //						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# //						ld_alloc = Dec(Mid( ls_text, 33, 8 ))
# //	
# //						INSERT INTO rec012  
# //							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# //						VALUES 
# //							( :ls_rdate,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
# //	
# ////						IF SQLCA.SQLCODE = -1 THEN
# ////							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# ////							ROLLBACK ;
# ////							Return -1
# ////						END IF		
# ////						COMMIT;
# //						
# //					END IF
# //					
# //					/*	4 set of 6 set */
# //					ls_pair =  Trim( Mid( ls_text, 42, 5 ))
# //					IF ls_pair <> '0- 0' THEN
# //						
# //						IF Len(ls_pair) = 4 THEN
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# //						ELSE
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# //						END IF
# //						
# //						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# //						ld_alloc = Dec(Mid( ls_text, 47, 8 ))
# //	
# //						INSERT INTO rec012  
# //							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# //						VALUES 
# //							( :ls_rdate,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
# //	
# ////						IF SQLCA.SQLCODE = -1 THEN
# ////							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# ////							ROLLBACK ;
# ////							Return -1
# ////						END IF		
# ////						COMMIT;
# //						
# //					END IF
# //					
# //					/*	5 set of 6 set */
# //					ls_pair =  Trim( Mid( ls_text, 56, 5 ))
# //					IF ls_pair <> '0- 0' THEN
# //						
# //						IF Len(ls_pair) = 4 THEN
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# //						ELSE
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# //						END IF
# //						
# //						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# //						ld_alloc = Dec(Mid( ls_text, 61, 8 ))
# //	
# //						INSERT INTO rec012  
# //							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# //						VALUES 
# //							( :ls_rdate,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
# //	
# ////						IF SQLCA.SQLCODE = -1 THEN
# ////							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# ////							ROLLBACK ;
# ////							Return -1
# ////						END IF		
# ////						COMMIT;
# //						
# //					END IF
# //					
# //					/*	6 set of 6 set */
# //					ls_pair =  Trim( Mid( ls_text, 70, 5 ))
# //					IF ls_pair <> '0- 0' THEN
# //						
# //						IF Len(ls_pair) = 4 THEN
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# //						ELSE
# //							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# //						END IF
# //						
# //						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# //						ld_alloc = Dec(Mid( ls_text, 75, 8 ))
# //	
# //						INSERT INTO rec012  
# //							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# //						VALUES 
# //							( :ls_rdate,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
# //	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
# //						
# //					END IF
# //
# //				END IF
# //		
# //			CASE 8						//해당경주 승식별 매출액
# //				
# //					IF Left(ls_text,3) = '매출액' THEN 
# //	
# //						ld_sale1 = Dec(Trim(Mid(ls_text,Pos(ls_text, "단식:") + 3, 15)))				//단식 매출액
# //						ld_sale2 = Dec(Trim(Mid(ls_text,Pos(ls_text, "연식:") + 3, 15)))				//연식 매출액
# //						ld_sale3 = Dec(Trim(Mid(ls_text,Pos(ls_text, "복식:") + 3, 15)))				//복식 매출액			
# //		
# //					ELSEIF Left(ls_text,2) = '복연' THEN 
# //						ld_sale4 = Dec(Trim(Mid(ls_text,Pos(ls_text, "복연:") + 3, 15)))				//연식 매출액
# //						ld_sale5 = Dec(Trim(Mid(ls_text,Pos(ls_text, "쌍식:") + 3, 15)))				//복식 매출액	
# //						ld_sale6 = Dec(Trim(Mid(ls_text,Pos(ls_text, "삼복:") + 3, 15)))				//복식 매출액	
# //					ELSEIF Left(ls_text,2) = '삼쌍' THEN 
# //						ld_sale7 = Dec(Trim(Mid(ls_text,Pos(ls_text, "삼쌍:") + 3, 15)))				//연식 매출액
# //						ld_sale8 = Dec(Trim(Mid(ls_text,Pos(ls_text, "합계:") + 3, 15)))				//복식 매출액	
# //					END IF
# //					
# //					UPDATE rec010  
# //						  SET sale1 = :ld_sale1,            sale2 = :ld_sale2,            sale3 = :ld_sale3,            sale4 = :ld_sale4,            sale5 = :ld_sale5,            sale6 = :ld_sale6,            sale7 = :ld_sale7,            sales = :ld_sale8
# //					 WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;
# //	
# //		
# //					IF SQLCA.SQLCODE = -1 THEN
# //						MessageBox("알림","rec010 Table Insert Fail!  Sales  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //						ROLLBACK ;
# //						Return -1
# //					END IF		
# //							
# //					COMMIT;
# //				
# //				
# //			CASE 9						//승식별 배당률
# //				
# //				IF Left(ls_text,3) = '배당률' THEN 
# //	
# //						ls_r1alloc = Trim(Mid(ls_text, Pos(ls_text, "단:") + 2, Pos(ls_text, "연:") - Pos(ls_text, "단:") -2 ))				//단식 배당률
# //						ls_r3alloc = Trim(Mid(ls_text, Pos(ls_text, "연:") + 2, Pos(ls_text, "복:") - Pos(ls_text, "연:") -2 ))				//연식 배당률
# //						ls_r2alloc = Trim(Mid(ls_text, Pos(ls_text, "복:") + 2, Pos(ls_text, "4F:") - Pos(ls_text, "복:") -2))					//복식 배당률			
# //						ls_r4f = Trim(Mid(ls_text, Pos(ls_text, "4F:") + 3, 10))																		//4F	
# //		
# //					ELSEIF Trim(Left(ls_text,3)) = '3F:' THEN 
# //						ls_r3f = Trim(Mid(ls_text,Pos(ls_text, "3F:") + 3, 10))				//3F
# //					ELSEIF Trim(Left(ls_text,2)) = '쌍:' THEN 
# //						ls_r12alloc = Trim(Mid(ls_text,Pos(ls_text, "쌍:") + 2, 10))				//쌍
# //					ELSEIF Left(ls_text,3) = '복연:' THEN 
# //						ls_r23alloc = Trim(Mid(ls_text,Pos(ls_text, "복연:") + 3, 25))				//연식 매출액
# //					ELSEIF Left(ls_text,3) = '삼복:' THEN 
# //						ls_r333alloc = Trim(Mid(ls_text,Pos(ls_text, "삼복:") + 3, 25))				//연식 매출액
# //					ELSEIF Left(ls_text,3) = '삼쌍:' THEN 
# //						ls_r123alloc = Trim(Mid(ls_text,Pos(ls_text, "삼쌍:") + 3, 25))				//연식 매출액
# //					END IF
# //					
# //					  UPDATE rec010  
# //						  SET r1alloc = :ls_r1alloc,   
# //								r3alloc = :ls_r3alloc,   
# //								r2alloc = :ls_r2alloc,   
# //								r12alloc = :ls_r12alloc,   
# //								r23alloc = :ls_r23alloc,   
# //								r333alloc = :ls_r333alloc,   
# //								r123alloc = :ls_r123alloc,   
# //								r3f = :ls_r3f,   
# //								r4f = :ls_r4f 
# //						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;
# //
# //					IF SQLCA.SQLCODE = -1 THEN
# //						MessageBox("알림","rec010 Table Insert Fail!  Sales  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //						ROLLBACK ;
# //						Return -1
# //					END IF		
# //							
# //					COMMIT;
# //
# //			CASE 10								//화롱타임,통과M,통과T
# //				
# //				IF Trim(Left(ls_text,4)) = '펄 롱:' THEN 
# //					ls_furlong = Trim(Mid(ls_text,Pos(ls_text, "펄 롱:") + 4, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = '통과M:' THEN 
# //					ls_passage = Trim(Mid(ls_text,Pos(ls_text, "통과M:") + 4, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = '통과T:' THEN 
# //					ls_passage_t = Trim(Mid(ls_text,Pos(ls_text, "통과T:") + 4, 100))
# //				END IF
# //					
# //					  UPDATE rec010  
# //						  SET furlong = :ls_furlong,
# //						  	    passage = :ls_passage,
# //								passage_t = :ls_passage_t
# //						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;
# //
# //					IF SQLCA.SQLCODE = -1 THEN
# //						MessageBox("알림","rec010 Table Insert Fail!  passage  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //						ROLLBACK ;
# //						Return -1
# //					END IF		
# //							
# //					COMMIT;
# //
# //			CASE 11								//코너별 통과순위
# //				
# //				
# ////				MessageBox("", Trim(Left(ls_text,4)))
# //				
# //				IF Trim(Left(ls_text,4)) = '통과순위' THEN 
# //					ls_passage_s1f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'C1 :' THEN 
# //					ls_passage_1c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'C2 :' THEN 
# //					ls_passage_2c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'C3 :' THEN 
# //					ls_passage_3c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'C4 :' THEN 
# //					ls_passage_4c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'G-1F' THEN 
# //					ls_passage_g1f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				END IF
# //					
# //					  UPDATE rec010  
# //						  SET passage_s1f = :ls_passage_s1f,
# //						  	    passage_1c = :ls_passage_1c,
# //								passage_2c = :ls_passage_2c,
# //								passage_3c = :ls_passage_3c,
# //								passage_4c = :ls_passage_4c,
# //								passage_g1f = :ls_passage_g1f
# //						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;
# //
# //					IF SQLCA.SQLCODE = -1 THEN
# //						MessageBox("알림","rec010 Table Insert Fail!  passage  " + SQLCA.SQLErrText + ls_passage_s1f )
# //						ROLLBACK ;
# //						Return -1
# //					END IF		
# //							
# //					COMMIT;
# //
# //			CASE 12							//Skip
# //			CASE 13							//특기사항
# //
# //				IF Trim(Left(ls_text,10)) <> '----------' THEN 
# //					
# //					IF Len(ls_text) > 1 THEN
# //					
# //						ll_seq = ll_seq + 1
# //						IF Trim( Left( ls_text, 2)) = '말' THEN
# //							ls_target = '말'
# //							ll_gate = Long( Trim( Mid( ls_text, 3, 10 ) ) )
# //						ELSE IF Trim( Left( ls_text, 2)) = '기수' THEN
# //							ls_target = '기수'
# //							ll_gate = Long( Trim( Mid( ls_text, 3, 10 ) ) )
# //						ELSE
# //							ls_target = ' '
# //							ll_gate = Long( Trim( Mid( ls_text, 3, 10 ) ) )
# //						END IF
# //							
# //							
# //					
# //						INSERT INTO rec013  
# //							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# //						VALUES 
# //							( :ls_rdate,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
# //	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
# //						
# //					END IF
# //					
# //				END IF
				
# 		END CHOOSE
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
   
# NEXT

# ipos = 0


# update rec010 set rmoisture = replace( replace(  replace(rmoisture, '%', ''), '(', ''), ')', '' )
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;

# commit ;


# Return 1
# end function

# public function integer wf_convert_71 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_imdate, ls_rdate, ls_rday, ls_rcity, ls_grade, ls_dividing, ls_rname, ls_rcon1, ls_rcon2, ls_weather, ls_rstate, ls_rmoisture
# Long		ll_rno, ll_rseq, ll_distance

# Long		ll_gate, ll_pos
# String		ls_horse, ls_gear1, ls_gear2, ls_blood1, ls_blood2, ls_treat1, ls_treat2


# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		IF Trim( Mid( ls_text, 1, 1)) = '─' THEN ll_handle =  ll_handle + 1

# 		CHOOSE CASE ll_handle

# 			CASE 0					//경주 제반조건 설정을 읽어들인다.

# 				IF	Trim(Mid(ls_text,1,3)) = '경주일'  THEN																	//	경주일
					
# 					ls_rcity = '서울'	
# 					ls_imdate = Mid(ls_text, 6, 10)																				//	날짜변환을 위해 임시로 저장 '98년06월07일'
# 					ls_rdate  = Mid(ls_imdate, 1, 4) + Mid(ls_imdate, 6, 2) + Mid(ls_imdate, 9, 2)			//	경주일자
# 					ll_rno = Long( Mid( ls_text, Pos( ls_text, ls_imdate ) + 10, 5))							

# 				END IF
				
# 				delete from exp012 where rcity = :ls_rcity and rdate = :ls_rdate  ;
# 				commit ;

# 			CASE 1								
# 			CASE 2						//경주순위 및 기수,조교사 마주 등을 읽어들인다.
				
# 					IF	Trim(Mid(ls_text,1,3)) = '경주일'  THEN																	//	경주일
					
# 						ll_handle = 0																									// Next Race init 
						
# 						ls_rcity = '서울'	
# 						ls_imdate = Mid(ls_text, 6, 10)																				//	날짜변환을 위해 임시로 저장 '98년06월07일'
# 						ls_rdate  = Mid(ls_imdate, 1, 4) + Mid(ls_imdate, 6, 2) + Mid(ls_imdate, 9, 2)			//	경주일자
# 						ll_rno = Long( Mid( ls_text, Pos( ls_text, ls_imdate ) + 10, 5))							
	
# 					END IF
				
# 				IF Long( Trim( Mid(ls_text, 1, 3) )) > 0 AND Long( Trim( Mid(ls_text, 1, 3) )) < 20 THEN

# 					ll_gate = Long( Trim(Mid(ls_text, 1, 3) ))																			//	게이트
# 					ls_horse = Trim(Mid(ls_text, Pos( ls_text, String(ll_gate)) + Len(String(ll_gate)), 10))					//	마필명

# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ), 100) )
					
# 					IF Long( Trim(Mid(ls_text, 1, 4))) > 2000 THEN																	//	보조장구1 check,   2000보다 크면 보조장구 없이 바로 폐출혈이나 진료사항 
							
# 						ls_gear1 = ''
						
# 						IF Long( Trim(Mid(ls_text, 11, 2))) > 0 THEN																//	폐출혈1 check, 폐출혈1이 있으면 
# 							ls_blood1 = Trim(Mid(ls_text, 1, 13))
# 							ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_blood1 ) + Len( ls_blood1 ), 100) )
							
# 							ls_treat1 = ls_text
# 						ELSE
							
# 							ls_blood1 = ''
# 							ls_treat1 = ls_text
							
# 						END IF
						
# 					ELSE
						
# 						ls_gear1 = Trim(Mid(ls_text, 1, 11))																			//	보조장구1이 있으면 
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_gear1 ) + Len( ls_gear1 ), 100) )
						
# 						IF Long( Trim(Mid(ls_text, 11, 2))) > 0 THEN																//	폐출혈1 check, 폐출혈1이 있으면 
# 							ls_blood1 = Trim(Mid(ls_text, 1, 13))
# 							ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_blood1 ) + Len( ls_blood1 ), 100) )
							
# 							ls_treat1 = ls_text
# 						ELSE
							
# 							ls_blood1 = ''
# 							ls_treat1 = ls_text
							
# 						END IF
						
# 					END IF

# 					select rdate into :ls_rdate from exp012 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate ;
					
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
					
					
						
						
# 					ELSE
						
# 						INSERT INTO exp012  
# 								( rcity,   				rdate,   			rno,			gate,				horse,			gear1,				blood1,			treat1   	 )  
# 						VALUES ( :ls_rcity,   		:ls_rdate,   		:ll_rno,		:ll_gate,			:ls_horse,		:ls_gear1,			:ls_blood1,		:ls_treat1  )  ;
	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
# 						COMMIT;
							
# 					END IF
					
# 				ELSE		// Second Line
					
# 					IF Long( Trim(Mid(ls_text, 1, 4))) > 2000 THEN																	//	보조장구2 check,   2000보다 크면 보조장구 없이 바로 폐출혈이나 진료사항 
							
# 						ls_gear2 = ''
						
# 						IF Long( Trim(Mid(ls_text, 11, 2))) > 0 THEN																//	폐출혈2 check, 폐출혈2이 있으면 
# 							ls_blood2 = Trim(Mid(ls_text, 1, 13))
# 							ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_blood2 ) + Len( ls_blood2 ), 100) )
							
# 							ls_treat2 = ls_text
# 						ELSE
							
# 							ls_blood2 = ''
# 							ls_treat2 = ls_text
							
# 						END IF
						
# 					ELSE
						
# 						ls_gear2 = Trim(Mid(ls_text, 1, 11))																			//	보조장구2이 있으면 
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_gear2 ) + Len( ls_gear2 ), 100) )
						
# 						IF Long( Trim(Mid(ls_text, 11, 2))) > 0 THEN																//	폐출혈2 check, 폐출혈2 이 있으면 
# 							ls_blood2 = Trim(Mid(ls_text, 1, 13))
# 							ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_blood2 ) + Len( ls_blood2 ), 100) )
							
# 							ls_treat2 = ls_text
# 						ELSE
							
# 							ls_blood2 = ''
# 							ls_treat2 = ls_text
							
# 						END IF
						
# 					END IF
					
# 					select rdate into :ls_rdate from exp012 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate ;
					 
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
					
# 						update exp012 set gear2 = :ls_gear2,				blood2 = :ls_blood2,			treat2 = :ls_treat2 
# 						where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate ;
						
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
# 						COMMIT;
						
# 					ELSE
# 					END IF
				
# 				END IF			
				
				
				
# 		END CHOOSE
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_b1 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_horse, ls_birthplace, ls_sex, ls_birth, ls_age, ls_grade, ls_team, ls_trainer, ls_host, ls_paternal, ls_maternal

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_rating

# Longlong		ll_tot_prize, ll_price

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		ls_horse = Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len(ls_horse), 300 ))
# 		ls_birthplace = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_birthplace ) + Len(ls_birthplace), 300 ))
# 		ls_sex= Trim( Mid( ls_text, 1, 1) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_sex ) + Len(ls_sex), 300 ))
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = ( Mid( ls_text, Pos( ls_text, ls_birth ) + Len(ls_birth), 300 ))
# 		ls_age = Trim( Mid( ls_text, 1, 2) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_age ) + Len(ls_age), 300 ))
# 		ls_grade = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_grade ) + Len(ls_grade), 300 ))
# 		ls_team = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_team ) + Len(ls_team), 300 ))
# 		ls_trainer = Trim( Mid( ls_text, 1, 3) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_trainer ) + Len(ls_trainer), 300 ))
# 		ls_host = Trim( Mid( ls_text, 1, 13) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_host ) + Len(ls_host), 300 ))
# 		ls_paternal = Trim( Mid( ls_text, 1, Pos( ls_text, '  ' )) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_paternal ) + Len(ls_paternal), 300 ))
# 		ls_maternal = Trim( Mid( ls_text, 1, Pos( ls_text, '  ' )) )

# 		ls_text =Right( ls_text, 63 )
# 		li_tot_race = Integer( Trim( Mid( ls_text, 1, 5 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 6, 5 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 11, 5 )))
# 		li_year_race = Integer( Trim( Mid( ls_text, 16, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 21, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 26, 5 )))
		
# 		ll_tot_prize = LongLong( Trim( Mid( ls_text, 31, 11 )))
# 		li_rating = LongLong( Trim( Mid( ls_text, 42, 11 )))
# 		ll_price = LongLong( Trim( Mid( ls_text, 53, 11 ))) * 1000
		
# 		select horse into :ls_horse from horse where rcity = :ls_rcity and horse = :ls_horse and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update horse set 	rcity = :ls_rcity,				age = :ls_age,						grade = :ls_grade,			team = :ls_team,				trainer = :ls_trainer,			
# 									host = :ls_host,				paternal = :ls_paternal,			maternal = :ls_maternal,	
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			
# 									year_race = :li_year_race,	year_1st = :li_year_2nd,			year_2nd = :li_year_2nd,	
# 									tot_prize = :ll_tot_prize,		rating = :li_rating,				price = :ll_price
# 			where rcity = :ls_rcity and horse = :ls_horse and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO horse  
# 							( rcity,			horse,			birthplace,				sex,			birth,				age,				grade,			team,				trainer,			host,				paternal,				maternal,
# 							  tot_race,		tot_1st,					tot_2nd,		year_race,		year_1st,			year_2nd,		tot_prize,			rating,			price	)  
# 				 VALUES ( :ls_rcity,		:ls_horse,		:ls_birthplace,			:ls_sex,		:ls_birth,			:ls_age,			:ls_grade,			:ls_team,			:ls_trainer,		:ls_host,			:ls_paternal,			:ls_maternal,
# 							  :li_tot_race,	:li_tot_1st,				:li_tot_2nd,	:li_year_race,		:li_year_1st,		:li_year_2nd,		:ll_tot_prize,		:li_rating,			:ll_price)  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_b2 ();
# String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_jockey, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race

# ll_lines = mle_krafile.LineCount()

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴


# SetNull (ls_LineText)	

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
 
# //FOR i = 1 TO ll_lines - 1
# //      
# //	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# //	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		ls_jockey = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey ) + Len(ls_jockey), 300 ))
# 		IF Trim( Mid( ls_text, 1, 3) ) = '미계약' THEN
# 			ls_team = '00'
# 		ELSE
# 			IF Trim( Mid( ls_text, 1, 1) ) = '프' THEN 
# 				ls_team = '프'
# 			ELSE
# 				ls_team = Trim( Mid( ls_text, 1, 2) )
# 			END IF
# 		END IF
		
# 		ls_text = Trim( Right(ls_text, 56) )
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
# 		ls_age = Trim( Mid( ls_text, 11, 2) )
# 		ls_debut= Trim( Mid( ls_text, 13, 10) )
		
# 		ls_load_in = Trim( Mid( ls_text, 23, 2) )
# 		ls_load_out = Trim( Mid( ls_text, 25, 2) )
		
# 		li_tot_race = Integer( Trim( Mid( ls_text, 27, 5 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 32, 5 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 37, 5 )))
# 		li_year_race = Integer( Trim( Mid( ls_text, 42, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 47, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 52, 5 )))
		
# 		select jockey into :ls_jockey from jockey where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update jockey set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			
# 									year_race = :li_year_race,	year_1st = :li_year_2nd,			year_2nd = :li_year_2nd
# 			where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO jockey  
# 							( rcity,			jockey,			birth,				team,				age,				debut,			load_in,				load_out,
# 							  tot_race,		tot_1st,			tot_2nd,			year_race,		year_1st,			year_2nd )  
# 				 VALUES ( :ls_rcity,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_year_race,	:li_year_1st,		:li_year_2nd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# //	IF i = 1 THEN
# //		// + 2의 의미는 ~n라인 변경 을 의미 한다.
# //     	// 선택된 텍스트 만큼의 길이값을 더한다.
# //		ipos = Len( mle_krafile.TextLine() ) + 2
# //	END IF
# //	
# //    ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT

# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP
   
# //NEXT

# ipos = 0

# Return 1


# end function

# public function integer wf_convert_b3 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_trainer, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		ls_trainer = Trim( Mid( ls_text, 1, 3) )
# 		ls_team = Trim( Mid( ls_text, 4, 2) )

# 		ls_birth= Trim( Mid( ls_text, 6, 10) )
# 		ls_age = Trim( Mid( ls_text, 16, 2) )
# 		ls_debut= Trim( Mid( ls_text, 18, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_debut ) + Len( ls_debut ) , 100 ))
		
# 		IF Len(ls_text) = 30 THEN
# 			li_tot_race = Integer( Trim( Mid( ls_text, 1, 5 )))
# 			li_tot_1st = Integer( Trim( Mid( ls_text, 6, 5 )))
# 			li_tot_2nd = Integer( Trim( Mid( ls_text, 11, 5 )))
# 			li_year_race = Integer( Trim( Mid( ls_text, 16, 5 )))
# 			li_year_1st = Integer( Trim( Mid( ls_text, 21, 5 )))
# 			li_year_2nd = Integer( Trim( Mid( ls_text, 26, 5 )))

# 		ELSE
# 			li_tot_race = Integer( Trim( Mid( ls_text, 1, 6 )))
# 			li_tot_1st = Integer( Trim( Mid( ls_text, 7, 5 )))
# 			li_tot_2nd = Integer( Trim( Mid( ls_text, 12, 5 )))
# 			li_year_race = Integer( Trim( Mid( ls_text, 17, 5 )))
# 			li_year_1st = Integer( Trim( Mid( ls_text, 22, 5 )))
# 			li_year_2nd = Integer( Trim( Mid( ls_text, 27, 5 )))
# 		END IF
		
# 		select trainer into :ls_trainer from trainer where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update trainer set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,					
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd
# 			where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO trainer  
# 							( rcity,			trainer,			birth,				team,				age,				debut,			
# 							  tot_race,		tot_1st,			tot_2nd,			year_race,		year_1st,			year_2nd )  
# 				 VALUES ( :ls_rcity,		:ls_trainer,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_year_race,	:li_year_1st,		:li_year_2nd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_b6 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_host, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut, ls_tot_race, ls_year_race, ls_text1, ls_text2

# Int			li_total, li_cancel, li_current

# LongLong		ll_tot_prize, ll_year_prize

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text = mle_krafile.TextLine () 
	
# //	li_LastLine = mle_krafile.SelectedLine ()
# //	ll_Pos += mle_krafile.LineLength ()

# 	IF Len( Trim( ls_text)) <> 0 and Left( ls_text, 1 ) <> '-' and Trim( Right(ls_text,2)) <> '상금' THEN 
	
# 		ls_host = Trim( Mid( ls_text, 1, 12) )
		
# 		ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_host) + Len(ls_host), 500 ))
# 		li_total = Integer( Trim( Mid( ls_text, 1, Pos(ls_text, '두') -  1) ) )
		
# 		ls_text = Trim( Mid( ls_text, Pos(ls_text, '두' ) + 1, 200 ))
# 		li_cancel =Integer( Trim( Mid( ls_text, 1, Pos(ls_text, '두') - 1 ) ))
		
# 		ls_text = Trim( Mid( ls_text, Pos(ls_text, '두' ) + 1, 200 ))
# 		li_current = Integer( Trim( Mid( ls_text, 1, Pos(ls_text, '두') - 1) ))

# 		ls_text = Trim( Mid( ls_text, Pos(ls_text, '두' ) + 1, 200 ))
# 		ls_debut= Trim( Mid( ls_text, 1, 10) )
		
		
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_debut ) + Len( ls_debut ) , 100 ))
# 		ls_year_race = Trim ( Mid( ls_text, 1, Pos(ls_text, ')' ) + 1 ))
		
# 		ls_text = Trim( Mid( ls_text,  Pos(ls_text, ')' ) + 1 , 100 ))
# 		ll_year_prize =  LongLong ( Trim( Mid( ls_text, 1, Pos(ls_text, ' ' )  )))

# 		ls_text = Trim( Mid( ls_text,  Pos(ls_text, ' ' ), 100 ))
# 		ls_tot_race = Trim( Mid( ls_text, 1, Pos(ls_text, ')' ) + 1 )) 
		
# 		ls_text = Trim( Mid( ls_text,  Pos(ls_text, ')' ) + 1 , 100 ))
# 		ll_tot_prize = LongLong( trim( Mid( ls_text, 1, 13  )))
		
# 		select host into :ls_host from host where rcity = :ls_rcity and host = :ls_host ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update host set 	h_total = :li_total,				h_cancel = :li_cancel,				h_current = :li_current,				debut = :ls_debut,			
# 							  		tot_race = :ls_tot_race,		tot_prize = :ll_tot_prize,			year_race = :ls_year_race,			year_prize = :ll_year_prize
# 			where rcity = :ls_rcity and host = :ls_host   ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_host )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO host  
# 							( rcity,			host,			h_total,				h_cancel,				h_current,				debut,			
# 							  tot_race,		tot_prize,			year_race,		year_prize )  
# 				 VALUES ( :ls_rcity,		:ls_host,		:li_total,				:li_cancel,				:li_current,				:ls_debut,		
# 							  :ls_tot_race,	:ll_tot_prize,		:ls_year_race,	:ll_year_prize )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_host )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1
# end function

# public function integer wf_convert_72 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_tdate, ls_horse, ls_team, ls_hospital, ls_disease

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_rating

# Longlong		ll_tot_prize, ll_price

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text = mle_krafile.TextLine () 
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		ls_tdate = Trim( Mid( ls_text, 1, 10) )
# 		ls_tdate = mid(ls_tdate, 1,4) + mid(ls_tdate, 6, 2) + mid(ls_tdate, 9,2)
# 		ls_horse = Trim( Mid( ls_text, 11, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len(ls_horse), 300 ))
# 		ls_team = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_team ) + Len(ls_team), 300 ))
# 		ls_hospital= Trim( Mid( ls_text, 1, Pos( ls_text, ' ' )) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_hospital ) + Len(ls_hospital), 300 ))
# 		ls_disease= Trim( Mid( ls_text, 1, 100) )
		
# 		select horse into :ls_horse from treat where rcity = :ls_rcity and tdate = :ls_tdate and horse = :ls_horse and team = :ls_team and hospital = :ls_hospital and disease = :ls_disease   ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update treat set 	team = :ls_team,				hospital = :ls_hospital,			disease = :ls_disease
# 			 where rcity = :ls_rcity  and tdate = :ls_tdate and horse = :ls_horse and team = :ls_team and hospital = :ls_hospital and disease = :ls_disease  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO treat  
# 							( rcity,			tdate,			horse,			team,			hospital,			disease    )  
# 				 VALUES ( :ls_rcity,		:ls_tdate,		:ls_horse,		:ls_team,		:ls_hospital,		:ls_disease )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
   
# LOOP

# Return 1
# end function

# public function integer wf_convert_55 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_rdate, ls_imdate
# String		ls_team, ls_trainer, ls_team_num, ls_horse, ls_rider, ls_in_time, ls_out_time, ls_t_time, ls_remark

# LongLong		ll_tot_prize, ll_year_prize

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN Return -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 

# 	IF Len( Trim(ls_text ) ) > 0 THEN 
	
# 		IF Left( ls_text, 2) = '제목' THEN
# 			ls_imdate = Mid(ls_text,6, 8)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 			ls_rdate  = '20' + Mid(ls_imdate,1,2) + Mid(ls_imdate,4,2) + Mid(ls_imdate,7,2)	//경주일자
			
# 		ELSEIF Long( Left( ls_text, 4) ) >= 1 THEN

# 			ls_team = Trim( Mid( ls_text, 5, 2) )
# 			ls_trainer = Trim( Mid( ls_text, 9, 3))
# 			ls_team_num = Trim( Mid( ls_text, 13, 2))
# 			ls_horse = Trim( Mid( ls_text, 16, 10))
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ) , 100 ))
# 			ls_rider = Trim ( Mid( ls_text, 1, 1 ))
			
# 			ls_in_time = Trim( Mid( ls_text, 5, 5))
# 			ls_out_time = Trim( Mid( ls_text, 15, 5))
# 			ls_t_time = Trim( Mid( ls_text, 27, 4))
# 			ls_remark = Trim( Mid( ls_text, 34, 100))
	
# 			select horse into :ls_horse from training where rcity = :ls_rcity and tdate = :ls_rdate and horse = :ls_horse  ;
						
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update training set 	team = :ls_team,				trainer = :ls_trainer,				team_num = :ls_team_num,				rider = :ls_rider,			
# 											in_time = :ls_in_time,			out_time = :ls_out_time,			t_time = :ls_t_time,						remark = :ls_remark
# 				 where rcity = :ls_rcity and tdate = :ls_rdate and horse = :ls_horse ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO training  
# 								( rcity,			tdate,			horse,				team,				trainer,				team_num,			
# 								  rider,		in_time,		out_time,			t_time,			remark )  
# 					 VALUES ( :ls_rcity,		:ls_rdate,		:ls_horse,			:ls_team,			:ls_trainer,			:ls_team_num,		
# 								  :ls_rider,	:ls_in_time,	:ls_out_time,		:ls_t_time,		:ls_remark )  ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
			
# 		END IF
	
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1
# end function

# public function string wf_gettext (integer ai_linenumber);
# integer  li_LastLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# ll_OrigPos = mle_krafile.SelectedStart ()
# ll_OrigLength = mle_krafile.SelectedLength ()
# ll_TextLength = Len (mle_krafile.Text)
# SetNull (ls_LineText)

# IF ai_LineNumber > mle_krafile.LineCount () THEN RETURN ls_LineText 

# mle_krafile.SelectText (ll_Pos, 0)

# DO WHILE mle_krafile.SelectedLine () < ai_LineNumber
	
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
	
# 	IF ll_Pos > ll_TextLength THEN 
# 		mle_krafile.SelectText (ll_OrigPos, ll_OrigLength)
# 		RETURN ls_LineText 
# 	END IF
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP
	
# LOOP

# ls_LineText = mle_krafile.TextLine ()
# mle_krafile.SelectText (ll_OrigPos, ll_OrigLength)

# RETURN ls_LineText
# end function

# public function integer wf_convert_b5 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_rdate, ls_imdate
# String		ls_team, ls_trainer, ls_team_num, ls_horse, ls_rider, ls_rider_k, ls_remark, ls_judge

# LongLong		ll_tot_prize, ll_year_prize

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
	
# //	li_LastLine = mle_krafile.SelectedLine ()
# //	ll_Pos += mle_krafile.LineLength ()

# 	IF Len( Trim(ls_text ) ) > 0 THEN 
	
# 		IF Left( ls_text, 2) = '제목' THEN
# 			ls_imdate = Mid(ls_text, 6, 13)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 			ls_rdate  = Mid(ls_imdate, 1, 4) + Mid(ls_imdate, 7, 2) + Mid(ls_imdate, 11, 2)	//경주일자
			
# 		ELSEIF Long( Left( ls_text, 6) ) >= 1 THEN
			
# 			IF ls_rdate >= '20230413' THEN
			
# 				ls_team = Trim( Mid( ls_text, 1, 6) )
# 				ls_team_num = Trim( Mid( ls_text, 10, 2))
# 				ls_horse = Trim( Mid( ls_text, 15, 10))
				
				
# 				ls_rider = Trim ( Mid( Trim(ls_text), 22, 15 ))
				
				
# 				ls_rider_k = ''
				
# 				ls_judge = Trim( Right( Trim(ls_text), 13))
				
# 			ELSE

# 				ls_team = Trim( Mid( ls_text, 1, 6) )
# 				ls_team_num = Trim( Mid( ls_text, 10, 2))
# 				ls_horse = Trim( Mid( ls_text, 15, 10))
				
# 				ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ) , 100 ))
# 				ls_rider = Trim ( Mid( ls_text, 1, Pos( ls_text, '(' ) - 1) )
				
# 				ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_rider ) + Len( ls_rider ) + 1 , 100 ))
# 				ls_rider_k = Trim ( Mid( ls_text, 1, Pos( ls_text, ')' ) - 1 ))
				
# 				ls_judge = Trim( Mid( ls_text, Pos( ls_text, ')' ) + 1, 50))
				
# 			END IF

# 			select horse into :ls_horse from start_train where rcity = :ls_rcity and tdate = :ls_rdate and horse = :ls_horse  ;
						
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update start_train set 	team = :ls_team,			team_num = :ls_team_num,				rider = :ls_rider,			
# 												rider_k = :ls_rider_k,		judge = :ls_judge
# 				 where rcity = :ls_rcity and tdate = :ls_rdate and horse = :ls_horse ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO start_train  
# 								( rcity,			tdate,			horse,				team,				team_num,			
# 								  rider,		rider_k,		judge )  
# 					 VALUES ( :ls_rcity,		:ls_rdate,		:ls_horse,			:ls_team,			:ls_team_num,		
# 								  :ls_rider,	:ls_rider_k,	:ls_judge )  ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
			
# 		END IF
	
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1



# end function

# public function integer wf_convert_b4 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows, ll_rno, ll_gate

# String		ls_rcity = '서울', ls_rdate, ls_imdate
# String		ls_team, ls_trainer, ls_team_num, ls_horse, ls_rider, ls_rider_k, ls_remark, ls_judge, ls_audit_reason,	ls_judge_reason 

# LongLong		ll_tot_prize, ll_year_prize

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 

# 	IF Len( Trim(ls_text ) ) > 0 THEN 
	
# 		IF Left( ls_text, 2) = '제목' THEN
# 			ls_imdate = Mid(ls_text, 6, 13)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 			ls_rdate  = Mid(ls_imdate, 1, 4) + Mid(ls_imdate, 7, 2) + Mid(ls_imdate, 11, 2)	//경주일자
			
# 			ll_rno = Long( Trim( Mid( ls_text, Pos( ls_text, '경주' ) -2, 2) ))
			
# 		ELSEIF Long( Left( ls_text, 4) ) >= 1 THEN

# 			ll_gate = Long( Trim( Mid( ls_text, 1, 4) ))
# 			ls_horse = Trim( Mid( ls_text, 8, 10))
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ) , 100 ))
# 			ls_audit_reason = Trim ( Mid( ls_text, 1, Pos( ls_text, ')' ) + 1) )
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_audit_reason ) + Len( ls_audit_reason ) + 1 , 100 ))
			
# 			IF Pos( ls_text, '(' ) = 0 THEN
# 				ls_rider = ''
# 				ls_rider_k = ''
				
# 				ls_text =  Trim( Mid( ls_text, 50, 100 ))
# 				ls_judge = Trim( Mid( ls_text, 1, 4))
# 				ls_judge_reason = Trim( Mid( ls_text, 8, 100 ))
# 			ELSE
# 				ls_rider = Trim ( Mid( ls_text, Pos( ls_text, '(' ) - 4, 4 ))
# 				ls_rider_k = Trim ( Mid( ls_text, Pos( ls_text, '(' ) + 1, Pos( ls_text, ')' ) - Pos( ls_text, '(' ) - 1 ))
				
# 				ls_text = Trim( Mid( ls_text, Pos( ls_text, '합격') - 2 , 100 ))
# 				ls_judge = Trim( Mid( ls_text, 1, 3))
				
# 				ls_judge_reason = Trim( Mid( ls_text, Pos( ls_text, ls_judge) + 3 , 100 ))
# 			END IF
			
# 			select horse into :ls_horse from start_audit where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
						
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update start_audit set 	rider = :ls_rider,			rider_k = :ls_rider_k,		audit_reason = :ls_audit_reason,		judge = :ls_judge,			judge_reason = :ls_judge_reason
# 				 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO start_audit  
# 								( rcity,			rdate,			rno,					gate,				horse,			
# 								  rider,		rider_k,		audit_reason,		judge,			judge_reason  )  
# 					 VALUES ( :ls_rcity,		:ls_rdate,		:ll_rno,				:ll_gate,			:ls_horse,			
# 								  :ls_rider,	:ls_rider_k,	:ls_audit_reason,	:ls_judge,			:ls_judge_reason )  ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
			
# 		END IF
	
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1



# end function

# public function integer wf_convert_b7 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_imdate
# String		ls_judge, ls_before, ls_after, ls_reason, ls_cdate, ls_host

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
	
# 	IF Mid( ls_text, 1, 4) = '----' THEN ll_handle = ll_handle + 1

# 	IF ll_handle = 2 and  Mid( ls_text, 1, 4) <> '----'  and Len( Trim( ls_text )) > 0 THEN 

# 			ls_before = Trim( Mid( Trim( ls_text ), 1, 10))
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_before ) + Len( ls_before ) , 100 ))
# 			ls_after = Trim ( Mid( ls_text, 1, 10 ))
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_after ) + Len( ls_after ) , 100 ))
			
# 			IF Long( Left( ls_text, 4)) > 0 THEN
# 				ls_host = ''
# 				ls_cdate = Trim( Mid( ls_text, 1, 10))
# 				ls_reason = Trim( Mid( ls_text, 11, 100))
# 			ELSE
# 				ls_host = Trim ( Mid( ls_text, 1, 14 ))
				
# 				ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_host ) + Len( ls_host ) , 100 ))
# 				ls_cdate = Trim( Mid( ls_text, 1, 10))
# 				ls_reason = Trim( Mid( ls_text, 11, 100))
# 			END IF

# 			select h_after into :ls_after from hname where rcity = :ls_rcity and h_before = :ls_before and h_after = :ls_after  ;
						
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update hname set 	host = :ls_host,			cdate = :ls_cdate,			reason = :ls_reason			
# 				 where rcity = :ls_rcity and h_before = :ls_before and h_after = :ls_after  ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_after )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO hname  
# 								( rcity,			h_before,			h_after,			host,				cdate,			reason )
# 					 VALUES ( :ls_rcity,		:ls_before,		:ls_after,			:ls_host,			:ls_cdate,		:ls_reason ) ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_after )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
	
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1



# end function

# public function integer wf_convert_b2_20180719 ();
# String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity, ls_jockey, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int		li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_year_3rd, li_tot_3rd

# ll_lines = mle_krafile.LineCount()

# integer  	li_LastLine, li_LineNumber, li_SelectedLine
# long 		ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string 	ls_LineText


# IF Mid( is_fname, 9,1) = 'p' THEN 
# 	ls_rcity = '부산'
# ELSEIF  Mid( is_fname, 9,1) = 's' THEN
# 	ls_rcity = '서울'
# ELSE
# 	ls_rcity = '서울'
# END IF

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()										//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)	

# String	ls_wdate		// 매주 데이터 입력된 일자
# Dec	ld_per

# ls_wdate = Mid(is_fname, 1, 8)

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
	 
# 	IF Len(Trim(ls_text)) > 0 and Left( ls_text,3) <> '---' and  Left( ls_text,3) <> '기수명'  THEN

# 		ls_jockey = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey ) + Len(ls_jockey), 300 ))
# 		IF Trim( Mid( ls_text, 1, 3) ) = '미계약' THEN
# 			ls_team = '00'
# 		ELSE
# 			IF Trim( Mid( ls_text, 1, 1) ) = '프' THEN 
# 				ls_team = '프'
# 			ELSE
# 				ls_team = Trim( Mid( ls_text, 1, 2) )
# 			END IF
# 		END IF
		
# 		ls_text = Trim( Right(ls_text, 84) )
		
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
# 		ls_age = Trim( Mid( ls_text, 13, 2) )
# 		ls_debut= Trim( Mid( ls_text, 17, 10) )
		
# 		ls_load_in = Trim( Mid( ls_text, 29, 2) )
# 		ls_load_out = Trim( Mid( ls_text, 34, 2) )
		
# 		li_tot_race = Integer( Trim( Mid( ls_text, 37, 10 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 47, 5 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 52, 5 )))
# 		li_tot_3rd = Integer( Trim( Mid( ls_text, 57, 5 )))
		
		
# 		li_year_race = Integer( Trim( Mid( ls_text, 63, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 68, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 73, 5 )))
# 		li_year_3rd = Integer( Trim( Mid( ls_text, 78, 5 )))
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 기수성적 입력 - 서울
# 		select jockey into :ls_jockey from letsrace.jockey where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update letsrace.jockey set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,	
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd
# 			where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO letsrace.jockey  
# 							( rcity,			jockey,			birth,				team,				age,				debut,			load_in,				load_out,
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,			year_3rd )  
# 				 VALUES ( :ls_rcity,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 기수성적 입력 - 부산
# 		select jockey into :ls_jockey from Busan.jockey where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update Busan.jockey set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,	
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd
# 			where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO Busan.jockey  
# 							( rcity,			jockey,			birth,				team,				age,				debut,			load_in,				load_out,
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,			year_3rd )  
# 				 VALUES ( :ls_rcity,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 주별 기수성적 입력 - 서울
# 		select jockey into :ls_jockey from letsrace.jockey_w where rcity = :ls_rcity and wdate = :ls_wdate and jockey = :ls_jockey and birth = :ls_birth  ;
		
# 		IF li_year_race = 0 or IsNull(li_year_race) THEN
# 			ld_per = 0
# 		ELSE
# 			ld_per = (li_year_1st +  li_year_2nd) * 100 /  li_year_race 
# 		END IF
		
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update letsrace.jockey_w set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,	
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd,
# 									year_per =  :ld_per
# 			where rcity = :ls_rcity and wdate = :ls_wdate 
# 			    and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO letsrace.jockey_w  
# 					  ( rcity,			wdate,		jockey,			birth,		team,			age,				debut,			load_in,		load_out,
# 					   tot_race,		tot_1st,	tot_2nd,		tot_3rd,	year_race,		year_1st,			year_2nd,		year_3rd, 	year_per )  
# 				 VALUES ( :ls_rcity,		:ls_wdate,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 					 :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd,  		 :ld_per ) ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 주별 기수성적 입력 - 부산
# 		select jockey into :ls_jockey from Busan.jockey_w where rcity = :ls_rcity and wdate = :ls_wdate and jockey = :ls_jockey and birth = :ls_birth  ;
		
# 		IF li_year_race = 0 or IsNull(li_year_race) THEN
# 			ld_per = 0
# 		ELSE
# 			ld_per = (li_year_1st +  li_year_2nd) * 100 /  li_year_race 
# 		END IF
		
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update Busan.jockey_w set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,	
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd,
# 									year_per =  :ld_per
# 			where rcity = :ls_rcity and wdate = :ls_wdate 
# 			    and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO Busan.jockey_w  
# 					  ( rcity,			wdate,		jockey,			birth,		team,			age,				debut,			load_in,		load_out,
# 					   tot_race,		tot_1st,	tot_2nd,		tot_3rd,	year_race,		year_1st,			year_2nd,		year_3rd, 	year_per )  
# 				 VALUES ( :ls_rcity,		:ls_wdate,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 					 :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd,  		 :ld_per ) ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
# 		///////////////////////////////////////////////////////////////////////////////
	  
# 	END IF

# //	IF i = 1 THEN
# //		// + 2의 의미는 ~n라인 변경 을 의미 한다.
# //     	// 선택된 텍스트 만큼의 길이값을 더한다.
# //		ipos = Len( mle_krafile.TextLine() ) + 2
# //	END IF
# //	
# //    ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT

# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP
   
# //NEXT

# ipos = 0

# Return 1


# end function

# public function integer wf_convert_b3_20180719 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_trainer, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_tot_3rd, li_year_3rd

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 and Left( ls_text,3) <> '---' and  Left( ls_text,3) <> '조교사' THEN

# 		ls_trainer = Trim( Mid( ls_text, 1, 5) )
# 		ls_team = Trim( Mid( ls_text, 7, 2) )

# 		ls_birth= Trim( Mid( ls_text, 11, 10) )
# 		ls_age = Trim( Mid( ls_text, 23, 2) )
# 		ls_debut= Trim( Mid( ls_text, 27, 10) )

# 		li_tot_race = Integer( Trim( Mid( ls_text, 38, 6 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 45, 6 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 50, 5 )))
# 		li_tot_3rd = Integer( Trim( Mid( ls_text, 55, 5 )))
		
# 		li_year_race = Integer( Trim( Mid( ls_text, 61, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 66, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 71, 5 )))
# 		li_year_3rd = Integer( Trim( Mid( ls_text, 76, 5 )))
		
# 		select trainer into :ls_trainer from trainer where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update trainer set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,					
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_3rd,			tot_2nd = :li_tot_3rd,
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd
# 			where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO trainer  
# 							( rcity,			trainer,			birth,				team,				age,				debut,			
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,		year_3rd )  
# 				 VALUES ( :ls_rcity,		:ls_trainer,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,			:li_year_race,	:li_year_1st,		:li_year_2nd,	:li_year_3rd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_b1_20180719 ();String		ls_text, ls_wdate
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_horse, ls_birthplace, ls_sex, ls_birth, ls_age, ls_grade, ls_team, ls_trainer, ls_host, ls_paternal, ls_maternal

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_rating, li_tot_3rd, li_year_3rd

# Longlong		ll_tot_prize, ll_price

# ls_wdate = Mid(is_fname, 1, 8)

# delete from horse
# where rcity = :ls_rcity ;
# commit ;


# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )				//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0  and Left( ls_text,2) <> '--' and  Left( ls_text,2) <> '마명'  THEN

# 		ls_horse = Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len(ls_horse), 300 ))
# 		ls_birthplace = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_birthplace ) + Len(ls_birthplace), 300 ))
# 		ls_sex= Trim( Mid( ls_text, 1, 1) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_sex ) + Len(ls_sex), 300 ))
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = ( Mid( ls_text, Pos( ls_text, ls_birth ) + Len(ls_birth), 300 ))
# 		ls_age = Trim( Mid( ls_text, 1, 3) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_age ) + Len(ls_age), 300 ))
# 		ls_grade = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_grade ) + Len(ls_grade), 300 ))
# 		ls_team = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_team ) + Len(ls_team), 300 ))
# 		ls_trainer = Trim( Mid( ls_text, 1, 3) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_trainer ) + Len(ls_trainer), 300 ))
# 		ls_host = Trim( Mid( ls_text, 1, 13) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_host ) + Len(ls_host), 300 ))
# 		ls_paternal = Trim( Mid( ls_text, 1, Pos( ls_text, '  ' )) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_paternal ) + Len(ls_paternal), 300 ))
# 		ls_maternal = Trim( Mid( ls_text, 1, Pos( ls_text, '  ' )) )

# 		ls_text = Right( ls_text, 74 )
# 		li_tot_race = Integer( Trim( Mid( ls_text, 1, 2 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 4, 6 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 10, 6 )))
# 		li_tot_3rd = Integer( Trim( Mid( ls_text, 16, 6 )))
		
# 		li_year_race = Integer( Trim( Mid( ls_text, 22, 6 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 28, 6 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 34, 6 )))
# 		li_year_3rd = Integer( Trim( Mid( ls_text, 40, 6 )))
		
# 		ll_tot_prize = LongLong( Trim( Mid( ls_text, 46, 12 )))
# 		li_rating = LongLong( Trim( Mid( ls_text, 58, 6 )))
# 		ll_price = LongLong( Trim( Mid( ls_text, 64, 12 ))) * 1000
		
# 		select horse into :ls_horse from horse where rcity = :ls_rcity and horse = :ls_horse and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update horse set 	rcity = :ls_rcity,				age = :ls_age,						grade = :ls_grade,			team = :ls_team,				trainer = :ls_trainer,			
# 									host = :ls_host,				paternal = :ls_paternal,			maternal = :ls_maternal,	
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,
# 									year_race = :li_year_race,		year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd,
# 									tot_prize = :ll_tot_prize,		rating = :li_rating,					price = :ll_price
# 			where rcity = :ls_rcity and horse = :ls_horse and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO horse  
# 							( rcity,			horse,			birthplace,				sex,			birth,				age,				grade,			team,				trainer,			host,				paternal,				maternal,
# 							  tot_race,		tot_1st,			tot_2nd,					tot_3rd,		year_race,		year_1st,			year_2nd,		year_3rd,		tot_prize,		rating,			price	)  
# 				 VALUES ( :ls_rcity,		:ls_horse,		:ls_birthplace,			:ls_sex,		:ls_birth,			:ls_age,			:ls_grade,		:ls_team,		:ls_trainer,		:ls_host,			:ls_paternal,			:ls_maternal,
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,				:li_tot_3rd,	:li_year_race,	:li_year_1st,		:li_year_2nd,	:li_year_3rd,	:ll_tot_prize,	:li_rating,		:ll_price)  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# delete from horse_w
# where rcity = :ls_rcity
# and wdate = :ls_wdate ;
# commit ;

# insert into horse_w
# 	(
# 		select rcity,	:ls_wdate,		horse,			birth,			birthplace,				sex,			age,				grade,			team,				trainer,			host,				paternal,				maternal,
# 							  tot_race,		tot_1st,			tot_2nd,					tot_3rd,		year_race,		year_1st,			year_2nd,		year_3rd,		tot_prize,		rating,			price
#   		from horse
# 	  	where rcity = :ls_rcity
# 		  and length(trim(horse)) > 0
#   	);
	  

# commit ;
 



# Return 1
# end function

# public function integer wf_convert_13 ();String		ls_text
# Long			ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows, ll_rno, ll_gate

# String		ls_rcity = '서울', ls_rdate, ls_imdate
# String		ls_team, ls_trainer, ls_team_num, ls_horse, ls_jockey_o, ls_jockey_n,	ls_reason 

# Dec				ld_handycap

# integer  	li_LastLine, li_LineNumber, li_SelectedLine
# long 			ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# String 		ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()								//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)												//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																					//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  Trim( mle_krafile.TextLine () )

# 	IF Pos( ls_text, 'R' ) > 0 and Len( Trim(ls_text ) ) > 0  and Long(  Mid(ls_text, 1, 4)  )  > 1000 THEN 
	
# 		IF Pos( ls_text, '.' ) > 0 THEN			// 기수변경 내역인지 check   (부담중량 55.0 )
		
# 			ls_rdate  = Mid(ls_text, 1, 4) + Mid(ls_text, 6, 2) + Mid(ls_text, 9, 2)	//경주일자
			
# 			ll_rno = Long( Trim( Mid( ls_text, Pos( ls_text, 'R' ) - 2, 2)) )
# 			ll_gate =  Long( Trim( Mid( ls_text, Pos( ls_text, 'R' ) + 3, 4)) )
# 			ls_horse =  Trim( Mid( ls_text, Pos( ls_text, 'R' ) + 7, 10) )
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ), 100 )) 													//말이름부터 시작하도록 조정
			
# 			ls_jockey_o = Trim( Left( Trim (Mid( ls_text, 10, 100 ) ), 6) )  												// 출마기수
			
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey_o ), 100 )) 											// 출마기수 이름부터 시작하도록 조정
			
# 			ls_jockey_n = Trim( Left( Trim (Mid( ls_text, 6, 100 ) ), 6) ) 													//		 변경기수
			
# 			ld_handycap = Dec( Trim( Mid( ls_text, Pos( ls_text, '.' ) - 3, 6 )) )					// 부담중량
# 			ls_reason = Trim( Mid( ls_text, Pos( ls_text, '.' ) + 2, 20 ))									// 변경사유
			
			
# 			//  기수변경 내역	/////////////////////////////////////////////
# 			select horse into :ls_horse from cancel_j where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
							
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update cancel_j set 	jockey_o = : ls_jockey_o,		jockey_n = :ls_jockey_n,		handycap = :ld_handycap,		reason = :ls_reason
# 					where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO cancel_j  
# 									( rcity,				rdate,			rno,					gate,				horse,				jockey_o,				jockey_n,				handycap,				reason  )  
# 				VALUES ( :ls_rcity,		:ls_rdate,		:ll_rno,				:ll_gate,			:ls_horse,		:ls_jockey_o,		:ls_jockey_n,		:ld_handycap,		:ls_reason )  ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
# 			/////////////////////////////////////////////
			
# 		ELSE
			
# 			IF Integer( Mid(ls_text, 1, 4) ) > 0 Then
# 				ls_rdate  = Mid(ls_text, 1, 4) + Mid(ls_text, 6, 2) + Mid(ls_text, 9, 2)			//경주일자
				
# 				ll_rno = Long( Trim( Mid( ls_text, Pos( ls_text, 'R' ) - 2, 2)) )
# 				ll_gate =  Long( Trim( Mid( ls_text, Pos( ls_text, 'R' ) + 3, 4)) )
			
# 				ls_horse =  Trim( Mid( ls_text, Pos( ls_text, 'R  ' ) + 7, 10) )
				
# 				ls_reason = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + 10, 20 ))								// 변경사유
				
				
# 				//  말 취소내역 /////////////////////////////////////////////
# 				select horse into :ls_horse from cancel_h where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
								
# 				IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
				
# 					update cancel_h set 	reason = :ls_reason
# 						where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
					
# 					IF SQLCA.SQLCODE <> 0 THEN
# 						MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 						ROLLBACK ;
# 						Return -1
# 					END IF					
# 					COMMIT;
					
# 				ELSE
				
# 					INSERT INTO cancel_h  
# 										( rcity,				rdate,			rno,					gate,					horse,				reason  )  
# 					VALUES ( :ls_rcity,		:ls_rdate,		:ll_rno,				:ll_gate,			:ls_horse,		:ls_reason )  ;
				
# 					IF SQLCA.SQLCODE <> 0 THEN
# 						MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 						ROLLBACK ;
# 						Return -1
# 					END IF					
# 					COMMIT;
					
# 				END IF
# 				/////////////////////////////////////////////
					
# 			END IF
					
# 		END IF
		
		
			
		
		
		
		
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1



# end function

# public function integer wf_convert_01 ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ll_handle,ll_handle1,  ll_rows, ll_pos

# String		ls_imdate, ls_rdate, ls_rday, ls_rcity = '서울', ls_grade, ls_dividing, ls_rname, ls_rcon1, ls_rcon2, ls_rtime, ls_rcount
# Long		ll_rno, ll_rseq, ll_distance
# Long		ll_prize, ll_prize1, ll_prize2, ll_prize3, ll_prize4, ll_prize5, ll_subprize1, ll_subprize2, ll_subprize3

# Long		ll_rank, ll_gate,  ll_rating
# String		ls_horse, ls_birthplace, ls_sex, ls_age, ls_advantage, ls_jockey, ls_trainer, ls_host
# Double		ld_handicap

# Longlong		ll_prize_tot, ll_prize_year, ll_prize_half

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_tot_3rd, li_year_3rd

# integer 	li_LastLine, li_LineNumber, li_SelectedLine
# long 		ll_TextLength, iPos = 1, ll_OrigPos, ll_OrigLength
# string 		ls_LineText


# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)												//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )				//포커스의 시작점을 가리킨다.  
#    ls_text = trim(mle_krafile.TextLine())		// 값을 가져 온다.
	
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		IF Left(ls_text,10) = '----------' THEN ll_handle = Mod(ll_handle + 1, 5)

# 		CHOOSE CASE ll_handle

# 			CASE 0					//경주 제반조건 설정을 읽어들인다.

# 				IF	Trim(Mid(ls_text,1,2)) = '제목'  THEN													//제    목
					
# 					ll_handle1 = 1
					
# 					ls_imdate = Mid(ls_text,6,12)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 					ls_rdate  = '20' + Mid(ls_imdate,1,2) + Mid(ls_imdate,4,2) + Mid(ls_imdate,7,2)	//경주일자
# 					ll_rseq = Long(Mid(ls_text,16,3))						// year seq
# 					ls_rday = Mid(ls_text, 23, 1)							// race day
																											
# 					ll_rno = Long(Mid(ls_text, 28, 3))														//경주번호
					
# 				ELSEIF ll_handle1 >= 1 AND Left(ls_text,10) <> '----------'  THEN														//(서울)
				
# 					IF ll_handle1 = 1  THEN
# 						ll_handle1 = 2
					
# 						ll_distance = Long(Mid(ls_text, 1, 4))										//거리
# 						ls_rcount = Trim(Mid(ls_text,pos(ls_text, '출전') + 3 , 2))

# 						ls_grade = Trim(Mid(ls_text, 17 ,pos(ls_text, '(') - 17))										//등급
# 						ls_rcon1 = Trim(Mid(ls_text,pos(ls_text, '(') + 1 ,12))
# 						ls_rcon2 = Trim(Mid(ls_text,pos(ls_text, ')' ) - 10  ,10))
						
# 						ls_rtime = Trim(Mid(ls_text,pos(ls_text, '출발') + 3 , 5))						

# 					ELSEIF ll_handle1 = 2  THEN													//(서울)
# 						ll_handle1 = 3
# 						ls_dividing = Trim(Mid(ls_text, 1, 10))																				//경주구분
# 						ls_rname = Trim(Mid(ls_text,pos(ls_text, ls_dividing) + len(ls_dividing),30))									//경주명
						
						
# 					ELSEIF ll_handle1 = 3  THEN
# 						ll_handle1 = 4
						
# 						ll_prize1 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize2 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize3 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize4 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize5 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
					
# //						MessageBox("", String(ll_prize1) + "---" + String(ll_prize2) + + "---" + String(ll_prize3) + "---" + String(ll_prize4) + "---" + String(ll_prize5)  )
						
# 						select rdate into :ls_rdate from exp010 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno ;
				
# 						IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 						ELSE
							
# 							INSERT INTO exp010  
#          									( rcity,              rdate,              rno,              rday,              rseq,              distance,              rcount,   
#            									  grade,            dividing,          rname,          rcon1,            rcon2,            rtime,       
# 											  r1award,         r2award,          r3award,        r4award,         r5award,   
#            									  sub1award,     sub2award,      sub3award )  
#   								 VALUES ( :ls_rcity,          :ls_rdate,          :ll_rno,          :ls_rday,          :ll_rseq,           :ll_distance,			:ls_rcount,
#           									  :ls_grade,        :ls_dividing,		  :ls_rname,		:ls_rcon1,        :ls_rcon2,		   :ls_rtime,
#            									  :ll_prize1,        :ll_prize2,          :ll_prize3,           :ll_prize4,              :ll_prize5,   
#            									  null,              null,              	  null )  ;
							
# 							IF SQLCA.SQLCODE <> 0 THEN
# 								MessageBox("알림","exp010 제반조건 " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 								ROLLBACK ;
# 								Return -1
								
# 							ELSE
								
# 								//	경주결과 입력 준비 - 실제 경주결과 입력 전 심판 정보 입력 준비 */
							
# 								INSERT INTO rec010  
# 										 ( rcity,         rdate,			rno    	)  
# 							   VALUES ( :ls_rcity,     :ls_rdate,		:ll_rno  )  ;
							  
									
# 								COMMIT;	
								
								
# 							END IF
							
							
# 							COMMIT;

# 						END IF
								
# 					ELSEIF ll_handle1 = 4  THEN
						
# 						ll_prize1 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize2 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize3 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
						
# 						update exp010 set  sub1award = :ll_prize1,     sub2award = :ll_prize2,      sub3award = :ll_prize3
# 						 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno ;
						 
# 						IF SQLCA.SQLCODE <> 0 THEN
# 								MessageBox("알림","exp010 부가상금  " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 								ROLLBACK ;
# 								Return -1
# 						END IF					
# 						COMMIT;
						 

# 					END IF

# 				END IF

# 			CASE 1		//	skip
# 			CASE 2
# 				ll_handle1 = 0			// 제반조건 라인 초기화
				
# 				IF Left(ls_text,10) <> '----------' THEN 
					
# 					ll_gate = Long(Trim(Mid(ls_text,1,4)))									//게이트
# 					ll_pos = Pos( ls_text, String(ll_gate))										//게이트 번호 위치 
# 					ls_horse = Trim(Mid(ls_text,ll_pos + Len(String(ll_gate)), 14))										//마필명
					
# 					IF Left( ls_horse, 1 ) = '★' THEN ls_horse = Trim( Mid( ls_horse, 2, 14))

# 					ll_pos = Pos(ls_text, ".")
# 					ls_birthplace = Trim(Mid(ls_text, ll_pos - 15, 6))									//산지
										
# 					ls_sex = Trim(Mid(ls_text, ll_pos - 9, 2))												//성별
# 					ls_age = Trim(Mid(ls_text, ll_pos - 6, 4))											//연령
					
# 					ld_handicap = Dec(Mid(ls_text, ll_pos - 2, 4))										//부담중량
					
# 					IF ls_rdate >= '20180719' THEN
						
# 						ls_advantage = Trim(Mid(ls_text, ll_pos + 5 , 4))									//감량 이점
# 						ls_jockey = Trim(Mid(ls_text, ll_pos + 9, 4))										//기수
						
# 					ELSE
						
# 						ls_advantage = Trim(Mid(ls_text, ll_pos + 4 , 4))									//감량 이점
# 						ls_jockey = Trim(Mid(ls_text, ll_pos + 8, 4))										//기수
						
# 					END IF
				
# //					IF Left(ls_jockey,1) = ')' THEN ls_jockey = Mid(ls_jockey, 2, 10)
					
# 					IF Len(ls_jockey) = 2 THEN
# 						ls_trainer = Trim(Mid(ls_text,  Pos(ls_text, ls_jockey) + 9 ,6))									//조교사
# 					ELSE
# 						ls_trainer = Trim(Mid(ls_text,  Pos(ls_text, ls_jockey) + 8 ,6))									//조교사
# 					END IF
					
# 					ls_host = Trim(Mid(ls_text, Pos(ls_text, ls_trainer) + 4, 16))										//마주
					
# 					ll_rating = Long(Trim(Mid(ls_text, Pos(ls_text, ls_host) + 10, 20)))
					

# 					select rdate into :ls_rdate from exp011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 					ELSE
					
# 						  INSERT INTO exp011  
# 							  ( rcity,              rdate,              rno,              gate,              horse,	birthplace,		h_sex,		h_age,		handycap,		jockey,		joc_adv,	trainer,		host,		rating  )  
# 						  VALUES ( :ls_rcity,     :ls_rdate,          	:ll_rno,           :ll_gate,        :ls_horse,     	:ls_birthplace,	:ls_sex, 	:ls_age,		:ld_handicap,		:ls_jockey,	:ls_advantage,	:ls_trainer,	:ls_host,	:ll_rating  )  ;
			  					
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","exp011 Insert Fail " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ))
# 							ROLLBACK ;
# 							Return -1
							
# 						ELSE
# 							//	경주결과 입력 준비 - 실제 경주결과 입력 전 복기 정보 입력 준비 */
							
# 							INSERT INTO rec011  
# 							  		 ( rcity,         rdate,              rno,              gate,			 	horse	)  
# 						   VALUES ( :ls_rcity,     :ls_rdate,          :ll_rno,          :ll_gate,			:ls_horse 	)  ;
						  
					 
# 							COMMIT;
							
# 						END IF					
						
# 						COMMIT;
						
# 					END IF

# 				END IF			

# 			CASE 3						//	skip
# 			CASE 4						//	수득상금 
					
# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					ll_gate = Long(Trim(Mid(ls_text,1,4)))										//	게이트
# 					ll_pos = Pos( ls_text, String(ll_gate))											//	게이트 번호 위치 
# 					ls_horse = Trim(Mid(ls_text, ll_pos + Len(String(ll_gate)), 14))			//	마필명
					
# 					IF ls_rdate >= '20180721' THEN						// 20180721 부터 출마표변경 -- 착순 3위까지 
					
# 						ls_text =  Right ( ls_text, 75 ) 
							
# 						ll_prize_tot = LongLong ( Left ( ls_text, 14) )
# 						ll_prize_year = LongLong ( Mid ( ls_text, 14+1, 14) )
# 						ll_prize_half = LongLong ( Mid ( ls_text, 14+1+14, 14) )
							
# 						ls_text =  Right ( ls_text, 32 ) 
# 						li_tot_1st = Integer(  Mid( ls_text , 1, 4) )
# 						li_tot_2nd = Integer(  Mid( ls_text, 5, 4) )
# 						li_tot_3rd = Integer(  Mid( ls_text, 9, 4) )
# 						li_tot_race = Integer(  Mid( ls_text, 13, 4) )
						
# 						ls_text =  Right ( ls_text, 16 )
# 						li_year_1st = Integer(  Mid( ls_text, 1, 4) )
# 						li_year_2nd = Integer(  Mid( ls_text, 5, 4) )
# 						li_year_3rd = Integer(  Mid( ls_text, 9, 4) )
# 						li_year_race = Integer(  Mid( ls_text, 13, 4) )
						
# 					ELSE
						
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, String(ls_horse))	+ Len(ls_horse) , 100) )			// 마필명 뒤를 잘라내서 수득상금 계산 준비
						
# 						IF Long( Left( ls_text, 1 )) = 0 THEN					//		수득상금이 0이면
# 							ll_prize_tot = 0
# 							ll_prize_year = 0
# 							ll_prize_half = 0
# 						ELSE
							
# 							IF Len( ls_text) = 65 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 13) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 13+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 13+1+14, 14) )
# 							ELSEIF Len( ls_text) = 63 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 11) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 11+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 11+1+14, 14) )
# 							ELSEIF Len( ls_text) = 62 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 10) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 10+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 10+1+14, 14) )
# 							ELSEIF Len( ls_text) = 61 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 9) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 9+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 9+1+14, 14) )
# 							ELSEIF Len( ls_text) = 60 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 8) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 8+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 8+1+14, 14) )
# 							END IF
							
# 						END IF
						
# 						ls_text =  Right ( ls_text, 22 ) 
# 						li_tot_1st = Integer(  Mid( ls_text , 1, 3) )
# 						li_tot_2nd = Integer(  Mid( ls_text, 4, 3) )
# 						li_tot_race = Integer(  Mid( ls_text, 7, 4) )
						
# 						ls_text =  Right ( ls_text, 10 )
# 						li_year_1st = Integer(  Mid( ls_text, 1, 3) )
# 						li_year_2nd = Integer(  Mid( ls_text, 4, 3) )
# 						li_year_race = Integer(  Mid( ls_text, 7, 4) )
						
						
# 					END IF
					
					
# //					IF ls_horse = '기모아런치' THEN MessageBox("",  Right ( ls_text, 22 ) + "---" + String( Len (Right ( ls_text, 22 )) ))
					
# 					select rdate into :ls_rdate from exp011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE exp011 a
#      							SET 	prize_tot = :ll_prize_tot,  	prize_year = :ll_prize_year,  	prize_half = :ll_prize_half ,
# 								      tot_1st = :li_tot_1st, 			tot_2nd = :li_tot_2nd, 			tot_race = :li_tot_race,	tot_3rd = :li_tot_3rd, 	year_3rd = :li_year_3rd, 
# 										year_1st = :li_year_1st, 		year_2nd = :li_year_2nd, 		year_race = :li_year_race
#    							WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF
				
# 		END CHOOSE
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#    ipos = ipos + Len( mle_krafile.TextLine() ) + 2

# NEXT


# update exp011 set horse = replace(  replace(horse, '[서]', ''), '[부]', '')
#  where rcity = :ls_rcity and rdate between DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 3),'%Y%m%d') and :ls_rdate
# ;
# commit ;

# update exp011 a set h_age = DATEDIFF ( cast( a.rdate as date), ( select cast( birth as date ) from horse where horse = a.horse ))/365, 
# s1f_rank = ( select avg(s1f_rank) from rec011 where horse = a.horse and rank <= 20 and isnull(judge) and rdate between date_format(DATE_ADD(a.rdate, INTERVAL - 365 DAY), '%Y%m%d') and a.rdate and rdate < a.rdate and substr( corners, -2 ) <> '99' and substr( corners, 1, 1 ) <> '-'),
# g1f_rank = ( select avg(g1f_rank) from rec011 where horse = a.horse and rank <= 20 and isnull(judge) and rdate between date_format(DATE_ADD(a.rdate, INTERVAL - 365 DAY), '%Y%m%d') and a.rdate and rdate < a.rdate and substr( corners, -2 ) <> '99' and substr( corners, 1, 1 ) <> '-'),
# g2f_rank = ( select avg(g2f_rank) from rec011 where horse = a.horse and rank <= 20 and isnull(judge) and rdate between date_format(DATE_ADD(a.rdate, INTERVAL - 365 DAY), '%Y%m%d') and a.rdate and rdate < a.rdate and substr( corners, -2 ) <> '99' and substr( corners, 1, 1 ) <> '-'),
# g3f_rank = ( select avg(g3f_rank) from rec011 where horse = a.horse and rank <= 20 and isnull(judge) and rdate between date_format(DATE_ADD(a.rdate, INTERVAL - 365 DAY), '%Y%m%d') and a.rdate and rdate < a.rdate and substr( corners, -2 ) <> '99' and substr( corners, 1, 1 ) <> '-') 
#  where rcity = :ls_rcity and rdate between DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 3),'%Y%m%d') and :ls_rdate
# ;
# commit ;


# update exp012 set horse = replace(  replace(horse, '[서]', ''), '[부]', '')
#  where rcity = :ls_rcity and rdate between DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 3),'%Y%m%d') and :ls_rdate
# ;
# commit ;

# update exp013 set horse = replace(  replace(horse, '[서]', ''), '[부]', '')
#  where rcity = :ls_rcity and rdate between DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 3),'%Y%m%d')and :ls_rdate
# ;
# commit ;

# Return 1
# end function

# public function integer wf_convert_01_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ll_handle,ll_handle1,  ll_rows, ll_pos

# String		ls_imdate, ls_rdate, ls_rday, ls_rcity = '부산', ls_grade, ls_dividing, ls_rname, ls_rcon1, ls_rcon2, ls_rtime, ls_rcount
# Long		ll_rno, ll_rseq, ll_distance
# Long		ll_prize, ll_prize1, ll_prize2, ll_prize3, ll_prize4, ll_prize5, ll_subprize1, ll_subprize2, ll_subprize3

# Long		ll_rank, ll_gate,  ll_rating
# String		ls_horse, ls_birthplace, ls_sex, ls_age, ls_advantage, ls_jockey, ls_trainer, ls_host
# Double		ld_handicap

# Longlong		ll_prize_tot, ll_prize_year, ll_prize_half

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_tot_3rd, li_year_3rd

# integer 	li_LastLine, li_LineNumber, li_SelectedLine
# long 		ll_TextLength, iPos = 1, ll_OrigPos, ll_OrigLength
# string 		ls_LineText


# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)												//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )				//포커스의 시작점을 가리킨다.  
#    ls_text = trim(mle_krafile.TextLine())		// 값을 가져 온다.
	
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		IF Left(ls_text,10) = '----------' THEN ll_handle = Mod(ll_handle + 1, 5)

# 		CHOOSE CASE ll_handle

# 			CASE 0					//경주 제반조건 설정을 읽어들인다.

# 				IF	Trim(Mid(ls_text,1,2)) = '제목'  THEN													//제    목
					
# 					ll_handle1 = 1
					
# 					ls_imdate = Mid(ls_text,6,12)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 					ls_rdate  = '20' + Mid(ls_imdate,1,2) + Mid(ls_imdate,4,2) + Mid(ls_imdate,7,2)	//경주일자
# 					ll_rseq = Long(Mid(ls_text,16,3))						// year seq
# 					ls_rday = Mid(ls_text, 23, 1)							// race day
																											
# 					ll_rno = Long(Mid(ls_text, 28, 3))														//경주번호
					
# 				ELSEIF ll_handle1 >= 1 AND Left(ls_text,10) <> '----------'  THEN														//(서울)
				
# 					IF ll_handle1 = 1  THEN
# 						ll_handle1 = 2
					
# 						ll_distance = Long(Mid(ls_text, 1, 4))										//거리
# 						ls_rcount = Trim(Mid(ls_text,pos(ls_text, '출전') + 3 , 2))

# 						ls_grade = Trim(Mid(ls_text, 17 ,pos(ls_text, '(') - 17))										//등급
# 						ls_rcon1 = Trim(Mid(ls_text,pos(ls_text, '(') + 1 ,12))
# 						ls_rcon2 = Trim(Mid(ls_text,pos(ls_text, ')' ) - 10  ,10))
						
# 						ls_rtime = Trim(Mid(ls_text,pos(ls_text, '출발') + 3 , 5))						

# 					ELSEIF ll_handle1 = 2  THEN													//(서울)
# 						ll_handle1 = 3
# 						ls_dividing = Trim(Mid(ls_text, 1, 10))																				//경주구분
# 						ls_rname = Trim(Mid(ls_text,pos(ls_text, ls_dividing) + len(ls_dividing),30))									//경주명
						
						
# 					ELSEIF ll_handle1 = 3  THEN
# 						ll_handle1 = 4
						
# 						ll_prize1 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize2 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize3 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize4 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize5 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
					
# //						MessageBox("", String(ll_prize1) + "---" + String(ll_prize2) + + "---" + String(ll_prize3) + "---" + String(ll_prize4) + "---" + String(ll_prize5)  )
						
# 						select rdate into :ls_rdate from exp010 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno ;
				
# 						IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 						ELSE
							
# 							INSERT INTO exp010  
#          									( rcity,              rdate,              rno,              rday,              rseq,              distance,              rcount,   
#            									  grade,            dividing,          rname,          rcon1,            rcon2,            rtime,       
# 											  r1award,         r2award,          r3award,        r4award,         r5award,   
#            									  sub1award,     sub2award,      sub3award )  
#   								 VALUES ( :ls_rcity,          :ls_rdate,          :ll_rno,          :ls_rday,          :ll_rseq,           :ll_distance,			:ls_rcount,
#           									  :ls_grade,        :ls_dividing,		  :ls_rname,		:ls_rcon1,        :ls_rcon2,		   :ls_rtime,
#            									  :ll_prize1,        :ll_prize2,          :ll_prize3,           :ll_prize4,              :ll_prize5,   
#            									  null,              null,              	  null )  ;
							
# 							IF SQLCA.SQLCODE <> 0 THEN
# 								MessageBox("알림","exp010 제반조건 " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 								ROLLBACK ;
# 								Return -1
								
# 							ELSE
# 								//	경주결과 입력 준비 - 실제 경주결과 입력 전 심판 정보 입력 준비 */
							
# 								INSERT INTO rec011  
# 										 ( rcity,         rdate,              rno 		)  
# 								VALUES ( :ls_rcity,     :ls_rdate,          :ll_rno 	)  ;
							  
						 
# 								COMMIT;
							
# 							END IF					
# 							COMMIT;

# 						END IF
								
# 					ELSEIF ll_handle1 = 4  THEN
						
# 						ll_prize1 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize2 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
# 						ls_text = Trim( Mid( ls_text, pos( ls_text, '원') + 1, 100 ))
# 						ll_prize3 = Long( Trim( Mid( ls_text, 1, pos( ls_text, '원') -1 )))
						
# 						update exp010 set  sub1award = :ll_prize1,     sub2award = :ll_prize2,      sub3award = :ll_prize3
# 						 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno ;
						 
# 						IF SQLCA.SQLCODE <> 0 THEN
# 								MessageBox("알림","exp010 부가상금  " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 								ROLLBACK ;
# 								Return -1
# 						END IF					
# 						COMMIT;
						 

# 					END IF

# 				END IF

# 			CASE 1		//	skip
# 			CASE 2
# 				ll_handle1 = 0			// 제반조건 라인 초기화
				
# 				IF Left(ls_text,10) <> '----------' THEN 
					
# 					ll_gate = Long(Trim(Mid(ls_text,1,4)))									//게이트
# 					ll_pos = Pos( ls_text, String(ll_gate))										//게이트 번호 위치 
# 					ls_horse = Trim(Mid(ls_text,ll_pos + Len(String(ll_gate)), 14))										//마필명
					
# 					IF Left( ls_horse, 1 ) = '★' THEN ls_horse = Trim( Mid( ls_horse, 2, 14))

# 					ll_pos = Pos(ls_text, ".")
# 					ls_birthplace = Trim(Mid(ls_text, ll_pos - 15, 6))									//산지
										
# 					ls_sex = Trim(Mid(ls_text, ll_pos - 9, 2))												//성별
# 					ls_age = Trim(Mid(ls_text, ll_pos - 6, 4))											//연령
					
# 					ld_handicap = Dec(Mid(ls_text, ll_pos - 2, 4))										//부담중량
					
					
# 					IF ls_rdate >= '20220114' THEN
# 						ls_advantage = Trim(Mid(ls_text, ll_pos + 5 , 4))									//감량 이점
# 						ls_jockey = Trim(Mid(ls_text, ll_pos + 9, 4))										//기수
						
# 					ELSEIF ls_rdate >=  '20220101' and ls_rdate <= '20220110' THEN
						
# 						ls_advantage = Trim(Mid(ls_text, ll_pos + 5 , 4))									//감량 이점
						
# 						IF LEFT(ls_advantage,1) = "(" THEN
# 							ls_jockey = Trim(Mid(ls_text, ll_pos + 9, 4))
# 						ELSE
# 							ls_advantage = ""	
# 							ls_jockey = Trim(Mid(ls_text, ll_pos + 7, 4))
# 						END IF
						
					
# 					ELSEIF ls_rdate >= '20180719' and ls_rdate <= '20211231' THEN
						
# 						ls_advantage = Trim(Mid(ls_text, ll_pos + 5 , 4))									//감량 이점
# 						ls_jockey = Trim(Mid(ls_text, ll_pos + 9, 4))										//기수
						
# 					ELSE
						
# 						ls_advantage = Trim(Mid(ls_text, ll_pos + 4 , 4))									//감량 이점
# 						ls_jockey = Trim(Mid(ls_text, ll_pos + 8, 4))										//기수
						
# 					END IF
				
# //					IF Left(ls_jockey,1) = ')' THEN ls_jockey = Mid(ls_jockey, 2, 10)
					
# 					IF Len(ls_jockey) = 2 THEN
# 						ls_trainer = Trim(Mid(ls_text,  Pos(ls_text, ls_jockey) + 9 ,6))									//조교사
# 					ELSE
# 						ls_trainer = Trim(Mid(ls_text,  Pos(ls_text, ls_jockey) + 8 ,6))									//조교사
# 					END IF
					
# 					ls_host = Trim(Mid(ls_text, Pos(ls_text, ls_trainer) + 4, 16))										//마주
					
# 					ll_rating = Long(Trim(Mid(ls_text, Pos(ls_text, ls_host) + 10, 20)))
					

# 					select rdate into :ls_rdate from exp011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 					ELSE
					
# 						  INSERT INTO exp011  
# 							  ( rcity,              rdate,              rno,              gate,              horse,	birthplace,		h_sex,		h_age,		handycap,		jockey,		joc_adv,	trainer,		host,		rating  )  
# 						  VALUES ( :ls_rcity,     :ls_rdate,          	:ll_rno,           :ll_gate,        :ls_horse,     	:ls_birthplace,	:ls_sex, 	:ls_age,		:ld_handicap,		:ls_jockey,	:ls_advantage,	:ls_trainer,	:ls_host,	:ll_rating  )  ;
			  					
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","exp011 Insert Fail " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ))
# 							ROLLBACK ;
# 							Return -1
							
# 						ELSE
							
# 							//	경주결과 입력 준비 - 실제 경주결과 입력 전 복기 정보 입력 준비 */
							
# 							INSERT INTO rec011  
# 							  		 ( rcity,         rdate,              rno,              gate,			 	horse	)  
# 						   VALUES ( :ls_rcity,     :ls_rdate,          :ll_rno,          :ll_gate,			:ls_horse 	)  ;
						  
					 
# 							COMMIT;
							
# 						END IF					
						
# 						COMMIT;
# 					END IF

# 				END IF			

# 			CASE 3						//	skip
# 			CASE 4						//	수득상금 
					
# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					ll_gate = Long(Trim(Mid(ls_text,1,4)))										//	게이트
# 					ll_pos = Pos( ls_text, String(ll_gate))											//	게이트 번호 위치 
# 					ls_horse = Trim(Mid(ls_text, ll_pos + Len(String(ll_gate)), 14))			//	마필명
					
# 					IF ls_rdate >= '20180721' THEN						// 20180721 부터 출마표변경 -- 착순 3위까지 
					
# 						ls_text =  Right ( ls_text, 75 ) 
							
# 						ll_prize_tot = LongLong ( Left ( ls_text, 14) )
# 						ll_prize_year = LongLong ( Mid ( ls_text, 14+1, 14) )
# 						ll_prize_half = LongLong ( Mid ( ls_text, 14+1+14, 14) )
							
# 						ls_text =  Right ( ls_text, 32 ) 
# 						li_tot_1st = Integer(  Mid( ls_text , 1, 4) )
# 						li_tot_2nd = Integer(  Mid( ls_text, 5, 4) )
# 						li_tot_3rd = Integer(  Mid( ls_text, 9, 4) )
# 						li_tot_race = Integer(  Mid( ls_text, 13, 4) )
						
# 						ls_text =  Right ( ls_text, 16 )
# 						li_year_1st = Integer(  Mid( ls_text, 1, 4) )
# 						li_year_2nd = Integer(  Mid( ls_text, 5, 4) )
# 						li_year_3rd = Integer(  Mid( ls_text, 9, 4) )
# 						li_year_race = Integer(  Mid( ls_text, 13, 4) )
						
# 					ELSE
						
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, String(ls_horse))	+ Len(ls_horse) , 100) )			// 마필명 뒤를 잘라내서 수득상금 계산 준비
						
# 						IF Long( Left( ls_text, 1 )) = 0 THEN					//		수득상금이 0이면
# 							ll_prize_tot = 0
# 							ll_prize_year = 0
# 							ll_prize_half = 0
# 						ELSE
							
# 							IF Len( ls_text) = 65 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 13) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 13+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 13+1+14, 14) )
# 							ELSEIF Len( ls_text) = 63 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 11) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 11+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 11+1+14, 14) )
# 							ELSEIF Len( ls_text) = 62 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 10) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 10+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 10+1+14, 14) )
# 							ELSEIF Len( ls_text) = 61 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 9) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 9+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 9+1+14, 14) )
# 							ELSEIF Len( ls_text) = 60 THEN
# 								ll_prize_tot = LongLong ( Left ( ls_text, 8) )
# 								ll_prize_year = LongLong ( Mid ( ls_text, 8+1, 14) )
# 								ll_prize_half = LongLong ( Mid ( ls_text, 8+1+14, 14) )
# 							END IF
							
# 						END IF
						
# 						ls_text =  Right ( ls_text, 22 ) 
# 						li_tot_1st = Integer(  Mid( ls_text , 1, 3) )
# 						li_tot_2nd = Integer(  Mid( ls_text, 4, 3) )
# 						li_tot_race = Integer(  Mid( ls_text, 7, 4) )
						
# 						ls_text =  Right ( ls_text, 10 )
# 						li_year_1st = Integer(  Mid( ls_text, 1, 3) )
# 						li_year_2nd = Integer(  Mid( ls_text, 4, 3) )
# 						li_year_race = Integer(  Mid( ls_text, 7, 4) )
						
						
# 					END IF
					
					
# //					IF ls_horse = '기모아런치' THEN MessageBox("",  Right ( ls_text, 22 ) + "---" + String( Len (Right ( ls_text, 22 )) ))
					
# 					select rdate into :ls_rdate from exp011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE exp011 a
#      							SET 	prize_tot = :ll_prize_tot,  	prize_year = :ll_prize_year,  	prize_half = :ll_prize_half ,
# 								      tot_1st = :li_tot_1st, 			tot_2nd = :li_tot_2nd, 			tot_race = :li_tot_race,	tot_3rd = :li_tot_3rd, 	year_3rd = :li_year_3rd, 
# 										year_1st = :li_year_1st, 		year_2nd = :li_year_2nd, 		year_race = :li_year_race
#    							WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF
				
# 		END CHOOSE
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#    ipos = ipos + Len( mle_krafile.TextLine() ) + 2

# NEXT


# update exp011 set horse = replace(  replace(horse, '[서]', ''), '[부]', '')
#  where rcity = :ls_rcity and rdate between DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 3),'%Y%m%d') and :ls_rdate
# ;
# commit ;

# update exp011 a set h_age = DATEDIFF ( cast( a.rdate as date), ( select cast( birth as date ) from horse where horse = a.horse ))/365, 
# s1f_rank = ( select avg(s1f_rank) from rec011 where horse = a.horse and rank <= 20 and isnull(judge) and rdate between date_format(DATE_ADD(a.rdate, INTERVAL - 99 DAY), '%Y%m%d') and a.rdate and rdate < a.rdate and substr( corners, -2 ) <>  '99' and substr( corners, 1, 1 ) <> '-'),
# g1f_rank = ( select avg(g1f_rank) from rec011 where horse = a.horse and rank <= 20 and isnull(judge) and rdate between date_format(DATE_ADD(a.rdate, INTERVAL - 99 DAY), '%Y%m%d') and a.rdate and rdate < a.rdate and substr( corners, -2 ) <> '99' and substr( corners, 1, 1 ) <> '-'),
# g2f_rank = ( select avg(g2f_rank) from rec011 where horse = a.horse and rank <= 20 and isnull(judge) and rdate between date_format(DATE_ADD(a.rdate, INTERVAL - 99 DAY), '%Y%m%d') and a.rdate and rdate < a.rdate and substr( corners, -2 ) <> '99' and substr( corners, 1, 1 ) <> '-'),
# g3f_rank = ( select avg(g3f_rank) from rec011 where horse = a.horse and rank <= 20 and isnull(judge) and rdate between date_format(DATE_ADD(a.rdate, INTERVAL - 99 DAY), '%Y%m%d') and a.rdate and rdate < a.rdate and substr( corners, -2 ) <> '99' and substr( corners, 1, 1 ) <> '-') 
#  where rcity = :ls_rcity and rdate between DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 3),'%Y%m%d') and :ls_rdate
# ;
# commit ;

# update exp012 set horse = replace(  replace(horse, '[서]', ''), '[부]', '')
#  where rcity = :ls_rcity and rdate between DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 3),'%Y%m%d') and :ls_rdate
# ;
# commit ;

# update exp013 set horse = replace(  replace(horse, '[서]', ''), '[부]', '')
#  where rcity = :ls_rcity and rdate between DATE_FORMAT( subdate( str_to_date( :ls_rdate, '%Y%m%d' ) , 3),'%Y%m%d')and :ls_rdate
# ;
# commit ;


# Return 1
# end function

# public function integer wf_convert_11_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_imdate, ls_rdate, ls_rday, ls_rcity, ls_grade, ls_dividing, ls_rname, ls_rcon1, ls_rcon2, ls_weather, ls_rstate, ls_rmoisture
# Long		ll_rno, ll_rseq, ll_distance
# Long		ll_prize, ll_prize1, ll_prize2, ll_prize3, ll_prize4, ll_prize5, ll_subprize1, ll_subprize2, ll_subprize3

# Long		ll_rank, ll_gate, ll_pos, ll_rating
# String		ls_horse, ls_birthplace, ls_sex, ls_age, ls_jockey, ls_trainer, ls_host
# Double	ld_handicap

# Long		ll_weight, ll_record
# String		ls_weight, ls_record, ls_gap, ls_corners, ls_iweight

# String		ls_g1f, ls_g3f, ls_s1f, ls_1corner, ls_2corner, ls_3corner, ls_4corner
# Long		ll_g1f, ll_g3f, ll_s1f, ll_1corner, ll_2corner, ll_3corner, ll_4corner
# String		ls_gsingle, ls_gdouble

# Double	ld_alloc
# String		ls_pair
# Long 		ll_pair1, ll_pair2

# Dec		ld_sale1, ld_sale2, ld_sale3, ld_sale4, ld_sale5, ld_sale6, ld_sale7, ld_sale8

# String		ls_r1alloc, ls_r3alloc, ls_r2alloc, ls_r12alloc, ls_r23alloc, ls_r333alloc, ls_r123alloc, ls_r4f, ls_r3f, ls_g2f

# String		ls_furlong, ls_passage, ls_passage_t
# String		ls_passage_s1f, ls_passage_1c, ls_passage_2c, ls_passage_3c, ls_passage_4c, ls_passage_g1f, ls_passage_8gf, ls_fast

# String		ls_passage_g8f

# Long		ll_seq				// rec013 rno seq


# String		ls_t_type, ls_t_detail, ls_t_reason, ls_t_horse, ls_t_jockey, ls_t_trainer, ls_t_sort
# Long		ll_t_gate    // 징계사유를 등록할 게이트 번호 , 이 번호로 기수와 조교사, 마필명을 가져온다.


# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )				//포커스의 시작점을 가리킨다.  
#     ls_text = trim(mle_krafile.TextLine())		// 값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		IF Left(ls_text,10) = '----------' THEN ll_handle = Mod(ll_handle + 1,14)

# 		CHOOSE CASE ll_handle

# 			CASE 0					//경주 제반조건 설정을 읽어들인다.

# 				IF	Trim(Mid(ls_text,1,2)) = '제목'  THEN													//제    목
				
# 					ls_imdate = Mid(ls_text,6,12)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 					ls_rdate  = '20' + Mid(ls_imdate,1,2) + Mid(ls_imdate,4,2) + Mid(ls_imdate,7,2)	//경주일자
# 					ls_rday = Mid(ls_text,16,1)
																											
# 					ll_rno = Long(Mid(ls_text,21,2))														//경주번호
					
# 				ELSEIF Left(ls_text,1) = '(' THEN												//(서울)
				
# 					ls_rcity = Mid(ls_text,2,2)	
# 					ll_rseq = Long(Mid(ls_text,7,2))
# 					ll_distance = Long(Mid(ls_text,11,4))											//거리
					
# //					ls_grade = Trim(Mid(ls_text, pos(ls_text, '등급') - 2, 4))								//등급
# //					ls_dividing = Trim(Mid(ls_text, pos(ls_text, '등급') + 2 ,9))
# //					ls_rname = Trim(Mid(ls_text, pos(ls_text, '경주명') + 6,30))							//경주명
					
# 					ls_grade = Trim(Mid(ls_text,17,4))										//등급
# 					IF ls_grade = '국OPE' THEN  ls_grade = '국OPEN'
# 					IF ls_grade = '혼OPE' THEN  ls_grade = '혼OPEN'
					
					
# 					ls_dividing = Trim(Mid(ls_text,pos(ls_text, ls_grade) + Len(ls_grade)   ,9))
# 					ls_rname = Trim(Mid(ls_text,pos(ls_text, '경주명') + 6,30))									//경주명
					
# //					SELECT rdate INTO :ls_rdate FROM rec010 									//기존 입력여부 확인 
# //					 WHERE rcity = :ls_rcity
# //					   AND rdate = :ls_rdate  
# //					   AND rno = :ll_rno ;
# //					 
# //					IF SQLCA.SQLNROWS > 0 THEN
# //						MessageBox("알림","이미 입력되어있는 데이타입니다. 데이타를 확인하십시오!")
# //						Return -1
# //					END IF

# 				ELSEIF Left(ls_text,4) = '경주조건' THEN																	//경주조건
					
# 					ls_rcon1 = Trim(Mid(ls_text,6,12))	
# 					ls_rcon2 = Trim(Mid(ls_text,19,Pos(ls_text,'날씨') - 19))									//경주조건

# 					ls_weather = Mid(ls_text,Pos(ls_text,'날씨') + 3,2)

# 					ls_rstate = Mid(ls_text,Pos(ls_text,'주로') + 3,2)
# 					ls_rmoisture = Trim(Mid(ls_text, Pos(ls_text,'주로') + 5,10))

# 				ELSEIF Left(ls_text,4) = '순위상금' THEN												//착순상금
					
# 					ll_prize1 = Dec(Trim(Mid(ls_text,6,7)))
# 					ll_prize2 = Dec(Trim(Mid(ls_text,16,7)))
# 					ll_prize3 = Dec(Trim(Mid(ls_text,26,7)))
# 					ll_prize4 = Dec(Trim(Mid(ls_text,36,7)))
# 					ll_prize5 = Dec(Trim(Mid(ls_text,46,7)))

# 				ELSEIF Left(ls_text,4) = '부가상금' THEN	 													//부가상금

# 					ll_subprize1 = Dec(Trim(Mid(ls_text,6,7)))
# 					ll_subprize2 = Dec(Trim(Mid(ls_text,16,7)))
# 					ll_subprize3 = Dec(Trim(Mid(ls_text,26,7)))

# 				END IF

# 			CASE 1						
				
# 					///////////////////////////////////////////////////////////////////////////
# 					////////// 경주제반조건 및 게이트별 마피및 기수,조교사 Insert /////////////
# 					///////////////////////////////////////////////////////////////////////////
					
# 				select rdate into :ls_rdate from rec010 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno ;
				
# 				IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
				
# 							UPDATE rec010  
# 						SET rday = :ls_rday,   				rseq = :ll_rseq,   			distance = :ll_distance,   			grade = :ls_grade,   
# 							 dividing = :ls_dividing,  	rname = :ls_rname,   		rcon1 = :ls_rcon1,   					rcon2 = :ls_rcon2,   				
# 							 weather = :ls_weather,   		rstate = :ls_rstate,   		rmoisture = :ls_rmoisture,   			rtime = null,   					
# 							 r1award = :ll_prize1,   		r2award = :ll_prize2,   	r3award = :ll_prize3,   				r4award = :ll_prize4,   				
# 							 r5award = :ll_prize5,   		sub1award = :ll_subprize1, sub2award = :ll_subprize2,				sub3award = :ll_subprize3 					
# 					 WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;
					 
# 					IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","경주 제반조건을 Update 하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 							ROLLBACK ;
# 							Return -1
# 					END IF
					
# 					COMMIT;
					
# 				ELSE
					
# 					INSERT INTO rec010  
# 							( rcity,   						rdate,   						rno,   						rday,   							rseq,   							distance,   					grade,   
# 							  dividing,   					rname,   						rcon1,   					rcon2,   						weather,   						rstate,   						rmoisture,   
# 							  rtime,   						r1award,   						r2award,   					r3award,   						r4award,   						r5award,   						sub1award,   
# 							  sub2award,   				sub3award,   					sale1,   					sale2,   						sale3,   						sale4,   						sale5,   
# 							  sale6,   						sale7,   						sales,   					r1alloc,   						r3alloc,   						r2alloc,   						r12alloc,   
# 							  r23alloc,   					r333alloc,   					r123alloc,   				passage_s1f,   				passage_1c,   					passage_2c,   				   passage_3c,   				
# 							  passage_4c,   				passage_g1f,   				r3f,   						 r4f,   							furlong,   						passage,   					   passage_t,   					
# 							  race_speed, r_judge )  
# 				  	VALUES ( :ls_rcity,   				:ls_rdate,   					:ll_rno,   					:ls_rday,   					:ll_rseq,   					:ll_distance,   				:ls_grade,   
# 							  :ls_dividing,   			:ls_rname,   					:ls_rcon1,   				:ls_rcon2,   					:ls_weather,   				:ls_rstate,   					:ls_rmoisture,   
# 							  null,   						:ll_prize1,   					:ll_prize2,   				:ll_prize3,   					:ll_prize4,   					:ll_prize5,   					:ll_subprize1,   
# 							  :ll_subprize2,   			:ll_subprize3,   				null,   						null,   							null,   							null,   							null,   							  
# 							  null,   						null,   							null,   						null,   							null,   							null,   							null,   							  
# 							  null,   						null,   							null,   					   null,   							null,   							null,   							null,   							  
# 							  null,   						null,   							null,   						null,   							null,   						   null,   							null,   							  
# 							  null, null )  ;

# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
# 						COMMIT;
# 					END IF
				
# 			CASE 2						//경주순위 및 기수,조교사 마주 등을 읽어들인다.
				
# 				IF Left(ls_text,10) <> '----------' THEN 
					
# 					IF Long( Right(Trim(Mid(ls_text,1,7)), 2) ) = 0 THEN 
# 						ll_rank = 99											//경주제외된 마필의 순위를 99로 지정한다
# 					ELSE
# 						ll_rank = Long(Trim(Mid(ls_text,1,4)))
# 					END IF
					
# 					IF ll_rank = 99 THEN 
# 						ll_gate = Long(Trim(Mid(ls_text,1,3)))									//게이트
# 						ls_horse = Trim(Mid(ls_text, Pos(ls_text, String(ll_gate)) + 2,11))										//마필명
# 					ELSE
# 						ll_gate = Long(Trim(Mid(ls_text,4,4)))									//게이트
# 						ls_horse = Trim(Mid(ls_text,9,11))										//마필명
# 					END IF
					
# 					IF Pos( ls_horse, ' ' ) > 0 THEN
# 						ls_horse = Mid( ls_horse, 1, Pos( ls_horse, ' ' ))
# 					END IF
					
# 					ll_pos = Pos(ls_text, ".")
# 					ls_birthplace = Trim(Mid(ls_text, ll_pos - 19,5))									//산지
										
# 					ls_sex = Trim(Mid(ls_text, ll_pos - 13, 2))											//성별
# 					ls_age = Trim(Mid(ls_text, ll_pos - 8, 4))											//연령
					
# 					ld_handicap = Dec(Mid(ls_text, ll_pos - 2, 4))										//부담중량
# 					ls_jockey = Trim(Mid(ls_text, ll_pos + 5, 4))										//기수
					
# 					ls_trainer = Trim(Mid(ls_text,  Pos(ls_text, ls_jockey) + 4 ,6))									//조교사
# 					ls_host = Trim(Mid(ls_text, Pos(ls_text, ls_trainer) + 4, 10))										//마주
					
# //					ll_rating = Long(Trim(Mid(ls_text, Pos(ls_text, ls_host) + 10, 12)))
# 					ll_rating = Long(Trim(Right(ls_text, 5)))
					
# 					IF ll_rank = 1 THEN 
# 						ll_prize = ll_prize1 + ll_subprize1
# 					ELSEIF ll_rank = 2 THEN 
# 						ll_prize = ll_prize2 + ll_subprize2
# 					ELSEIF ll_rank = 3 THEN 
# 						ll_prize = ll_prize3 + ll_subprize3
# 					ELSEIF ll_rank = 4 THEN 
# 						ll_prize = ll_prize4
# 					ELSEIF ll_rank = 5 THEN 
# 						ll_prize = ll_prize5
# 					ELSE
# 						ll_prize = 0
# 					END IF

# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
					
# 						UPDATE rec011  
# 							SET rank = :ll_rank,         horse = :ls_horse,          birthplace = :ls_birthplace,              h_sex = :ls_sex,              h_age = :ls_age,              
# 								 handycap = :ld_handicap, jockey = :ls_jockey,			trainer = :ls_trainer,        				host = :ls_host,              rating = :ll_rating				
# 						 WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate ;
						 
# 						IF SQLCA.SQLCODE <> 0 THEN
# 								MessageBox("알림","rec011 Update Fail " +  SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ))
# 								ROLLBACK ;
# 								Return -1
# 						END IF
						
# 						COMMIT;
					
# 					ELSE
					
# 						  INSERT INTO rec011  
# 									( rcity,          rdate,             rno,              	gate,              rank,              horse,              birthplace,              h_sex,              h_age,              handycap,   
# 									  jockey,         joc_adv,           trainer,          	host,              rating			  )  
# 						  VALUES ( :ls_rcity,     	:ls_rdate,         :ll_rno,           	:ll_gate,          :ll_rank,          :ls_horse,          :ls_birthplace,          :ls_sex,            :ls_age,            :ld_handicap,   
# 									  :ls_jockey,     null,              :ls_trainer,       	:ls_host,         	:ll_rating    )  ;
			  					
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","rec011 Insert Fail " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
						
# 						COMMIT;
# 					END IF

# 				END IF				
				
# 			CASE 3						//skip
# 			CASE 4						//마필기록 
					
# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					IF Long( Right(Trim(Mid(ls_text,1,7)), 2) ) = 0 THEN 
# 						ll_rank = 99											//경주제외된 마필의 순위를 99로 지정한다
# 					ELSE
# 						ll_rank = Long(Trim(Mid(ls_text,1,4)))
# 					END IF
					
# 					IF ll_rank = 99 THEN 
# 						ll_gate = Long(Trim(Mid(ls_text,1,3)))									//게이트
# 						ls_horse = Trim(Mid(ls_text, Pos(ls_text, String(ll_gate)) + 2,11))										//마필명
# //						MessageBox("", ls_horse)
# 					ELSE
# 						ll_gate = Long(Trim(Mid(ls_text,4,4)))									//게이트
# 						ls_horse = Trim(Mid(ls_text,9,11))										//마필명
# 					END IF
					
# 					ll_pos = Pos( ls_text, ":")
					
# 					IF ll_pos = 0 THEN
						
# 						ll_pos = Pos( ls_text, "(")
						
# 						ll_weight = Long(Mid(ls_text, ll_pos - 3, 3))										//마체중
# 						ls_iweight = Trim(Mid(ls_text,ll_pos + 1, 3))									//마체중 증감
# 						ls_record = '0:00.0'									//기록(String)
						
# 						ll_record = f_change_s2t(ls_record)										//수치로 변환된 기록
						
# 						ls_gap = Trim(Mid(ls_text, ll_pos + 14, 5))									//착차
# 						ls_corners = Trim(Right(ls_text, 19))									//코너별 전개
						
# 					ELSE
						
# 						ll_weight = Long(Mid(ls_text, ll_pos - 10, 3))										//마체중
# 						ls_iweight = Trim(Mid(ls_text,ll_pos - 6, 3))									//마체중 증감
# 						ls_record = Trim(Mid(ls_text, ll_pos -1, 6))										//기록(String)
						
# 						ll_record = f_change_s2t(ls_record)										//수치로 변환된 기록
						
# 						ls_gap = Trim(Mid(ls_text, ll_pos + 6, 7))									//착차
# 						ls_corners = Trim(Right(ls_text, 20))									//코너별 전개
						
# 					END IF
					
# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE rec011  
#      							SET h_weight = :ll_weight, 	w_change = :ls_iweight,		record = :ls_record,	i_record = :ll_record,	gap = :ls_gap,		corners = :ls_corners  
#    							WHERE rec011.rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF

# 			CASE 5						//skip
# 			CASE 6						//코너별 전개기록

# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					IF Len(Trim(Mid(ls_text,1,8))) <= 2 THEN
# 						ll_rank = 99	
						
						
# 					ELSE
# 						ll_rank = Long(Trim(Mid(ls_text,1,4)))
# 					END IF
					
# 					IF ll_rank = 99 THEN 
# 						ll_gate = Long(Trim(Mid(ls_text,1,2)))										//게이트
						
# 					ELSE
# 						ll_gate = Long(Trim(Mid(ls_text,4,4)))									//게이트
# 					END IF
					

# 					IF ll_rank = 99 THEN
# 						ls_g3f = ''
						
# 						ls_s1f = ''											//S1F(String)
# 						ls_1corner =''
# 						ls_2corner = ''
# 						ls_3corner = ''
# 						ls_4corner = ''
						

# 						ls_g1f = ''
# 						ls_g2f = ''
						
# 						//ls_gsingle = Trim(Mid(ls_text, ll_pos + 44, 6))						//단승식 배당(인기순위1)
# 						//ls_gdouble = Trim(Mid(ls_text, ll_pos + 52, 6))								//연승식 배당(인기순위2)
						
# 						ls_gsingle = Trim(Mid( Right(ls_text, 14), 1, 7 ))						//단승식 배당(인기순위1)
# 						ls_gdouble = Trim(Right(ls_text, 7))								//연승식 배당(인기순위2)
						

# 					ELSE
						
# 						ll_pos = Pos(ls_text, ".")
# 						ls_g3f = Mid(ls_text, ll_pos - 2, 4)											//G3F(String)
# 						ls_s1f =Trim( Mid(ls_text,ll_pos + 6, 6))												//S1F(String)
# 						ls_1corner = Mid(ls_text, ll_pos + 12, 6)
# 						ls_2corner = Mid(ls_text, ll_pos + 20, 6)
# 						ls_3corner = Mid(ls_text, ll_pos + 28, 6)
# 						ls_4corner = Mid(ls_text, ll_pos + 36, 6)
						

# 						ls_g2f = Trim(  Mid(ls_text, ll_pos + 46, 6) )
# 						ls_g1f = Trim(  Mid(ls_text, ll_pos + 52, 6) )
	
						
# 						ls_gsingle = Trim(Mid( Right(ls_text, 14), 1, 7 ))						//단승식 배당(인기순위1)
# 						ls_gdouble = Trim(Right(ls_text, 7))								//연승식 배당(인기순위2)
						
# 					END IF
					
					
# 					// select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
# 					select gap into :ls_gap from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
					
# 					IF right( ls_gap, 2) = '제외' or right( ls_gap, 2) = '취소' THEN
# 						ls_gsingle = ''
# 						ls_gdouble = ''
# 					END IF
					

				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE rec011  
#      							SET rg3f = :ls_g3f, 	rs1f = :ls_s1f,		r1c = :ls_1corner,	r2c = :ls_2corner,	  r3c = :ls_3corner,		r4c = :ls_4corner,  
# 								    rg1f = :ls_g1f,	alloc1r = :ls_gsingle, alloc3r = :ls_gdouble , rg2f  = :ls_g2f
#    							WHERE rec011.rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF
				
# 			CASE 77						//복승식 배당률 - 각 마필간 인기순위
				
# 				IF Left(ls_text,10) = '----------' OR Trim(ls_text) = '(복승식 배당률)' THEN 
					
# 				ELSE
					
# 					/*	1 et of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 1, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 6, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,	:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	2 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 14, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 19, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	3 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 28, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 33, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	4 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 42, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 47, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	5 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 56, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 61, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# //						COMMIT;
						
# 					END IF
					
# 					/*	6 set of 6 set */
# 					ls_pair =  Trim( Mid( ls_text, 70, 5 ))
# 					IF ls_pair <> '0- 0' THEN
						
# 						IF Len(ls_pair) = 4 THEN
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 1, 1 ))
# 						ELSE
# 							ll_pair1 = Long( Mid( ls_pair, Pos(ls_pair, '-') - 2, 2 ))
# 						END IF
						
# 						ll_pair2 = Long( Mid( ls_pair, Pos(ls_pair, '-') +1, 2 ))
# 						ld_alloc = Dec(Mid( ls_text, 75, 8 ))
	
# 						INSERT INTO rec012  
# 							( rcity, 		rdate,			rno,		pair1,			pair2,			pair,			alloc  )
# 						VALUES 
# 							( :ls_rcity,		:ls_rdate,		:ll_rno,	:ll_pair1,		:ll_pair2,		:ls_pair,		:ld_alloc	  	) ;
	
# 						IF SQLCA.SQLCODE = -1 THEN
# 							MessageBox("알림","rec012 Table Insert Fail! " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# 							ROLLBACK ;
# 							Return -1
# 						END IF		
# 						COMMIT;
						
# 					END IF

# 				END IF
		
# 			CASE 8						//해당경주 승식별 매출액
				
# 					IF Left(ls_text,3) = '매출액' THEN 
	
# 						ld_sale1 = Dec(Trim(Mid(ls_text,Pos(ls_text, "단식:") + 3, 15)))				//단식 매출액
# 						ld_sale2 = Dec(Trim(Mid(ls_text,Pos(ls_text, "연식:") + 3, 15)))				//연식 매출액
# 						ld_sale3 = Dec(Trim(Mid(ls_text,Pos(ls_text, "복식:") + 3, 15)))				//복식 매출액			
		
# 					ELSEIF Left(ls_text,2) = '복연' THEN 
# 						ld_sale4 = Dec(Trim(Mid(ls_text,Pos(ls_text, "복연:") + 3, 15)))				//연식 매출액
# 						ld_sale5 = Dec(Trim(Mid(ls_text,Pos(ls_text, "쌍식:") + 3, 15)))				//복식 매출액	
# 						ld_sale6 = Dec(Trim(Mid(ls_text,Pos(ls_text, "삼복:") + 3, 15)))				//복식 매출액	
# 					ELSEIF Left(ls_text,2) = '삼쌍' THEN 
# 						ld_sale7 = Dec(Trim(Mid(ls_text,Pos(ls_text, "삼쌍:") + 3, 15)))				//연식 매출액
# 						ld_sale8 = Dec(Trim(Mid(ls_text,Pos(ls_text, "합계:") + 3, 15)))				//복식 매출액	
# 					END IF
					
# 					UPDATE rec010  
# 						  SET sale1 = :ld_sale1,            sale2 = :ld_sale2,            sale3 = :ld_sale3,            sale4 = :ld_sale4,            sale5 = :ld_sale5,            sale6 = :ld_sale6,            sale7 = :ld_sale7,            sales = :ld_sale8
# 					 WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;
	
		
# 					IF SQLCA.SQLCODE = -1 THEN
# 						MessageBox("알림","rec010 Table Insert Fail!  Sales  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# 						ROLLBACK ;
# 						Return -1
# 					END IF		
							
# 					COMMIT;
				
				
# 			CASE 9						//승식별 배당률
				
# 				IF Left(ls_text,3) = '배당률' THEN 
	
# 						ls_r1alloc = Trim(Mid(ls_text, Pos(ls_text, "단:") + 2, Pos(ls_text, "연:") - Pos(ls_text, "단:") -2 ))				//단식 배당률
# 						ls_r3alloc = Trim(Mid(ls_text, Pos(ls_text, "연:") + 2, Pos(ls_text, "복:") - Pos(ls_text, "연:") -2 ))				//연식 배당률
# 						ls_r2alloc = Trim(Mid(ls_text, Pos(ls_text, "복:") + 2, Pos(ls_text, "4F:") - Pos(ls_text, "복:") -2))					//복식 배당률			
# 						ls_r4f = Trim(Mid(ls_text, Pos(ls_text, "4F:") + 3, 10))																		//4F	
		
# 					ELSEIF Trim(Left(ls_text,3)) = '3F:' THEN 
# 						ls_r3f = Trim(Mid(ls_text,Pos(ls_text, "3F:") + 3, 10))				//3F
# 					ELSEIF Trim(Left(ls_text,2)) = '쌍:' THEN 
# 						ls_r12alloc = Trim(Mid(ls_text,Pos(ls_text, "쌍:") + 2, 10))				//쌍
# 						ls_fast = Trim(right(ls_text,1))													//주로빠르기
# 					ELSEIF Left(ls_text,3) = '복연:' THEN 
# 						ls_r23alloc = Trim(Mid(ls_text,Pos(ls_text, "복연:") + 3, 25))				//연식 매출액
# 					ELSEIF Left(ls_text,3) = '삼복:' THEN 
# 						ls_r333alloc = Trim(Mid(ls_text,Pos(ls_text, "삼복:") + 3, 25))				//연식 매출액
# 					ELSEIF Left(ls_text,3) = '삼쌍:' THEN 
# 						ls_r123alloc = Trim(Mid(ls_text,Pos(ls_text, "삼쌍:") + 3, 25))				//연식 매출액
# 					END IF
					
# 					  UPDATE rec010  
# 						  SET r1alloc = :ls_r1alloc,   
# 								r3alloc = :ls_r3alloc,   
# 								r2alloc = :ls_r2alloc,   
# 								r12alloc = :ls_r12alloc,   
# 								r23alloc = :ls_r23alloc,   
# 								r333alloc = :ls_r333alloc,   
# 								r123alloc = :ls_r123alloc,   
# 								r3f = :ls_r3f,   
# 								r4f = :ls_r4f ,
# 								race_speed = :ls_fast
# 						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;

# 					IF SQLCA.SQLCODE = -1 THEN
# 						MessageBox("알림","rec010 Table Insert Fail!  Sales  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# 						ROLLBACK ;
# 						Return -1
# 					END IF		
							
# 					COMMIT;

# 			CASE 10								//화롱타임,통과M,통과T
				
# 				IF Trim(Left(ls_text,4)) = '펄 롱:' THEN 
# 					ls_furlong = Trim(Mid(ls_text,Pos(ls_text, "펄 롱:") + 4, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = '통과M:' THEN 
# 					ls_passage = Trim(Mid(ls_text,Pos(ls_text, "통과M:") + 4, 100))
# 				ELSEIF Trim(Left(ls_text,4)) = '통과T:' THEN 
# 					ls_passage_t = Trim(Mid(ls_text,Pos(ls_text, "통과T:") + 4, 100))
# 				END IF
					
# 					  UPDATE rec010  
# 						  SET furlong = :ls_furlong,
# 						  	    passage = :ls_passage,
# 								passage_t = :ls_passage_t
# 						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;

# 					IF SQLCA.SQLCODE = -1 THEN
# 						MessageBox("알림","rec010 Table Insert Fail!  passage  " + SQLCA.SQLErrText + ls_pair + ' ' + String(ll_pair1) + ' ' + String(ll_pair2) )
# 						ROLLBACK ;
# 						Return -1
# 					END IF		
							
# 					COMMIT;

# 			CASE 11								//코너별 통과순위
				
				
# //				MessageBox("", Trim(Left(ls_text,4)))
				
# //				IF Trim(Left(ls_text,4)) = '통과순위' THEN 
# //					ls_passage_s1f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'C1 :' THEN 
# //					ls_passage_1c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'C2 :' THEN 
# //					ls_passage_2c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'C3 :' THEN 
# //					ls_passage_3c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'C4 :' THEN 
# //					ls_passage_4c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				ELSEIF Trim(Left(ls_text,4)) = 'G-1F' THEN 
# //					ls_passage_g1f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# //				END IF

					
# 				IF Trim(Left(ls_text,4)) = '통과순위' THEN 
# 					ls_passage_s1f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,5)) = 'G8F :' THEN 
# 					ls_passage_g8f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,5)) = 'G6F :' THEN 
# 					ls_passage_1c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,5)) = 'G4F :' THEN 
# 					ls_passage_2c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,5)) = 'G3F :' THEN 
# 					ls_passage_3c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,5)) = 'G2F :' THEN 
# 					ls_passage_4c = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				ELSEIF Trim(Left(ls_text,5)) = 'G1F :' THEN 
# 					ls_passage_g1f = Trim(Mid(ls_text,Pos(ls_text, ":") + 1, 100))
# 				END IF
				
# 					  UPDATE rec010  
# 						  SET passage_s1f = :ls_passage_s1f,
# 						   	passage_g8f = :ls_passage_g8f,					/* 부산경마 only */
# 						  	    passage_1c = :ls_passage_1c,
# 								passage_2c = :ls_passage_2c,
# 								passage_3c = :ls_passage_3c,
# 								passage_4c = :ls_passage_4c,
# 								passage_g1f = :ls_passage_g1f
# 						WHERE rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno ;

# 					IF SQLCA.SQLCODE = -1 THEN
# 						MessageBox("알림","rec010 Table Insert Fail!  passage  " + SQLCA.SQLErrText + ls_passage_s1f )
# 						ROLLBACK ;
# 						Return -1
# 					END IF		
							
# 					COMMIT;

# 			CASE 12							//Skip
# 			CASE 13							//특기사항

# //		ls_t_type, ls_t_detail, ls_t_reason

# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					IF Len(ls_text) >= 3 THEN
						
# 						ls_t_type = Trim(Mid(ls_text, 25, 9))	
						
# 						ls_t_sort = Trim(Mid(ls_text, 1, 5))	
						
# 						ll_t_gate = Integer(Trim(Mid(ls_text, 5, 5)))
						
# 						select horse, jockey, trainer into :ls_t_horse, :ls_t_jockey, :ls_t_trainer from rec011 where rcity = :ls_rcity and  rdate = :ls_rdate and rno = :ll_rno and gate = :ll_t_gate ;
						
# 						IF ls_t_type = '과태금' THEN
							
# 							ls_t_detail = Trim(Mid(ls_text, 25 + 9, 20 ))	
# 							ls_t_reason = Trim(Mid(ls_text, 25 + 9 + 20 , 100))	
							
# 						ELSEIF Mid(ls_t_type,3,2) = '정지' THEN
							
# 							ll_pos = Pos( ls_text, ")")
# 							ls_t_detail = Trim(Mid(ls_text, Pos( ls_text, "(") - 5, Pos( ls_text, ")") - Pos( ls_text, "(") + 5 +1 ))	
# 							ls_t_reason = Trim(Mid(ls_text, ll_pos + 1 , 100))	
							
# 						ELSE
							
# 							ls_t_detail = ''
# 							ls_t_reason = Trim(Mid(ls_text, 27 + 9 + 20 , 100))	
							
# 						END IF
						
# 						IF ls_t_type = '경주부' or ls_t_type = '경주부적' or ls_t_type = '경주부적격' THEN ls_t_type = '경주부적격마' 
# 						IF ls_t_type = '주행심'  THEN ls_t_type = '주행심사' 
# 						IF ls_t_type = '주행중'  THEN ls_t_type = '주행중지' 
# 						IF ls_t_type = '출발심'  THEN ls_t_type = '출발심사' 
# 						IF ls_t_type = '출전정'  THEN ls_t_type = '출전정지' 
# 						IF ls_t_type = '출전제'  THEN ls_t_type = '출전제외' 
# 						IF ls_t_type = '출전취'  THEN ls_t_type = '출전취소' 
						
					
# 						INSERT INTO rec015  
# 							( rcity, 	rdate,		rno,		gate,		t_sort,		 horse,		t_type,		t_detail,		t_reason, 		jockey,		trainer ,		t_text )
# 						VALUES 
# 							( :ls_rcity,	:ls_rdate,	:ll_rno,	:ll_t_gate,	:ls_t_sort,		:ls_t_horse,		:ls_t_type,		:ls_t_detail,		:ls_t_reason, 	:ls_t_jockey,		:ls_t_trainer,	:ls_text ) ;
	
# //						IF SQLCA.SQLCODE = -1 THEN
# //							MessageBox("알림","rec015 Table Insert Fail! " + SQLCA.SQLErrText + ls_t_horse  + ' ' +  ls_t_type )
# //							ROLLBACK ;
# //							Return -1
# //						END IF		
# 						COMMIT;
						
# 					END IF
					
# 				END IF
				
# 		END CHOOSE
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
   
# NEXT

# ipos = 0

# /* 인기도 update */
# For i = 1 to ll_rno
	
# 	IF wf_update_pop11( ls_rcity, ls_rdate, i ) = -1 Then EXIT
	
# NEXT

# update rec011 a
#       set horse = replace(  replace(horse, '[서]', ''), '[부]', ''), 
#            distance_w = ( select distance from rec010 where rcity = a.rcity and rdate = a.rdate and rno = a.rno ) 
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;

# update rec011 a set distance_w = ( select distance from rec010 where rcity = a.rcity and rdate = a.rdate and a.rno = rno )  
#  where rcity = :ls_rcity and rdate = :ls_rdate 
#  ;
# commit ;

# update rec011
#       set jockey_w = f_jockey_w( rdate, jockey), 
#            burden_w =  f_burden_w(rdate, handycap, distance_w,jockey) 
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;

# update rec015 set horse = replace(  replace(horse, '[서]', ''), '[부]', '')
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;

# update rec010 set rmoisture = replace( replace(  replace(rmoisture, '%', ''), '(', ''), ')', '' )
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;



# update exp011 a 
#      set r_rank  = ( select rank from rec011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ) ,
# 		  r_record  = ( select record from rec011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ) ,
# 		  ir_record  = ( select i_record from rec011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# 		  h_weight =  ( select concat(h_weight, ' ', w_change) from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate  ),
# 		  alloc1r =  ( select alloc1r from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate  ) ,
#      	  alloc3r =  ( select alloc3r from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate  ) 
		  
		  
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;

# String	ls_rs1f, ls_r1c,  ls_r2c, ls_r3c, ls_r4c, ls_rg3f, ls_rg2f, ls_rg1f
# Integer	i_rno, i_gate

# Integer	i_s1f, i_r1c, i_r2c, i_r3c, i_r4c, i_g3f, i_g2f, i_g1f, i_record

# DECLARE C_race CURSOR FOR  
#  SELECT rcity, rdate, rno, gate, rs1f, r1c, r2c, r3c, r4c, rg3f, rg2f, rg1f, record
#    FROM rec011  
#   WHERE rcity = :ls_rcity and rdate = :ls_rdate
#  ;
	
# OPEN C_race ;

# FETCH C_race INTO :ls_rcity, :ls_rdate, :i_rno, :i_gate, :ls_rs1f, :ls_r1c, :ls_r2c, :ls_r3c, :ls_r4c, :ls_rg3f, :ls_rg2f, :ls_rg1f, :ls_record ;

# DO WHILE SQLCA.SQLCODE = 0 
	
# 	i_s1f =  f_s2t( ls_rs1f )
# 	i_r1c =  f_s2t( ls_r1c ) 
# 	i_r2c =  f_s2t( ls_r2c ) 
# 	i_r3c =  f_s2t( ls_r3c ) 
# 	i_r4c =  f_s2t( ls_r4c ) 
# 	i_g3f =  f_s2t( ls_rg3f ) 
	
# //	i_g2f =  ( f_s2t( ls_rg3f ) +  f_s2t( ls_rg1f ) ) /2 			//	g2f 환산  (g3f + g1f) / 2
# //	ls_rg2f = f_t2s( i_g2f)													//	g2f 환산기록 스트링 변환

# 	i_g2f =  f_s2t( ls_rg2f ) 
	
	
# 	i_g1f =  f_s2t( ls_rg1f ) 
# 	i_record =  f_s2t( ls_record )
	
# 	update rec011 set i_s1f = :i_s1f, i_r1c = :i_r1c, i_r2c = :i_r2c, i_r3c = :i_r3c, i_r4c = :i_r4c, i_g3f = :i_g3f, 
# 							i_g2f = :i_g2f , 
# 							i_g1f = :i_g1f, 
# 							i_record = :i_record
							
# 	 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :i_rno and gate = :i_gate ;
	 
# 	IF sqlca.sqlnrows > 0 THEN
# //		COMMIT ;
# 	ELSE
# 		ROLLBACK;
# 		MessageBox("알림", SQLCA.SQLErrText + ls_Record )
# 		Return -1
# 	END IF
	
# 	FETCH C_race INTO :ls_rcity, :ls_rdate, :i_rno, :i_gate, :ls_rs1f, :ls_r1c, :ls_r2c, :ls_r3c, :ls_r4c, :ls_rg3f, :ls_rg2f, :ls_rg1f, :ls_record ;
	
# LOOP

# CLOSE C_race ;

# COMMIT ;


# update rec011 a
#  set recent3 = ( select recent3 from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  recent5 = ( select recent5 from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  fast_r = ( select fast_r from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  slow_r = ( select slow_r from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  avg_r = ( select avg_r from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  convert_r = ( select convert_r from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
#  i_cycle = ( select i_cycle from The1.exp011 where rdate = a.rdate and rcity = a.rcity and rno = a.rno and gate = a.gate ),
 
#  r_pop = ( select r_pop from The1.exp011 where rdate = a.rdate and rcity = a.rcity and rno = a.rno and gate = a.gate ) ,
 
 
# gear1 = ( select gear1 from The1.exp012 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# gear2 = ( select gear2 from The1.exp012 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# treat1 = ( select treat1 from The1.exp012 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# treat2 = ( select treat2 from The1.exp012 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# reason = ( select reason from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),

# gap_b = ( select max(gap) from The1.rec011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.rank = rank - 1 ),

# jt_per = ( select jt_per from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# jt_cnt = ( select jt_cnt from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# jt_1st = ( select jt_1st from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# jt_2nd = ( select jt_2nd from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# jt_3rd = ( select jt_3rd from The1.exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ),
# h_cnt = ( select count(*) from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno ) ,
# h_mare = ( select sum( if( h_sex = '암', 1, 0 )) from The1.rec011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno )

# // s1f_rank = ( select s1f_rank from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate ),
# // g1f_rank = ( select g1f_rank from The1.exp011 where rcity = a.rcity and rdate = a.rdate and rno = a.rno and gate = a.gate )
# where rcity = :ls_rcity and rdate = :ls_rdate
#  ;

# commit;


# update rec011
# set s1f_rank = replace( replace( substr( corners, 1, 2 ), '-', '') , ' ', '' ) * 1,
# g1f_rank = replace( replace( substr( corners, -2 ), '-', '') , ' ', '' ) * 1,
# g2f_rank = replace( replace( substr( corners, -5, 2 ), '-', '') , ' ', '' ) * 1,
# g3f_rank = replace( replace( substr( corners, -8, 2 ), '-', '') , ' ', '' ) * 1
# where rcity = :ls_rcity and rdate = :ls_rdate
# and rank <= 20
# and isnull(judge) 
# ;

# commit;


# update exp011 a
# set 
#  corners = ( select corners from rec011 where rdate = a.rdate and rcity = a.rcity and rno = a.rno and gate = a.gate ),
#  r_s1f = ( select substr(rs1f,-4)  from rec011 where rdate = a.rdate and rcity = a.rcity and rno = a.rno and gate = a.gate ),
#  r_g3f = ( select substr(rg3f,-4) from rec011 where rdate = a.rdate and rcity = a.rcity  and rno = a.rno and gate = a.gate ),
#  r_g1f = ( select substr(rg1f, -4) from rec011 where rdate = a.rdate and rcity = a.rcity  and rno = a.rno and gate = a.gate ),
#  alloc1r = ( select alloc1r from rec011 where rdate = a.rdate and rcity = a.rcity  and rno = a.rno and gate = a.gate ),
#  alloc3r = ( select alloc3r from rec011 where rdate = a.rdate and rcity = a.rcity  and rno = a.rno and gate = a.gate )
# where rcity = :ls_rcity and rdate = :ls_rdate
#  ;
# commit;

# Return 1
# end function

# public function integer wf_convert_13_busan ();String		ls_text
# Long			ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows, ll_rno, ll_gate

# String		ls_rcity = '부산', ls_rdate, ls_imdate
# String		ls_team, ls_trainer, ls_team_num, ls_horse, ls_jockey_o, ls_jockey_n,	ls_reason 

# Dec				ld_handycap

# integer  	li_LastLine, li_LineNumber, li_SelectedLine
# long 			ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# String 		ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()								//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)												//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																					//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  Trim( mle_krafile.TextLine () )

# 	IF Pos( ls_text, 'R' ) > 0 and Len( Trim(ls_text ) ) > 0  and Long(  Mid(ls_text, 1, 4)  )  > 1000 THEN 
	
# 		IF Pos( ls_text, '.' ) > 0 THEN			// 기수변경 내역인지 check   (부담중량 55.0 )
		
# 			ls_rdate  = Mid(ls_text, 1, 4) + Mid(ls_text, 6, 2) + Mid(ls_text, 9, 2)	//경주일자
			
# 			ll_rno = Long( Trim( Mid( ls_text, Pos( ls_text, 'R' ) - 2, 2)) )
# 			ll_gate =  Long( Trim( Mid( ls_text, Pos( ls_text, 'R' ) + 3, 4)) )
# 			ls_horse =  Trim( Mid( ls_text, Pos( ls_text, 'R' ) + 7, 10) )
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ), 100 )) 													//말이름부터 시작하도록 조정
			
# 			ls_jockey_o = Trim( Left( Trim (Mid( ls_text, 10, 100 ) ), 6) )  												// 출마기수
			
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey_o ), 100 )) 											// 출마기수 이름부터 시작하도록 조정
			
# 			ls_jockey_n = Trim( Left( Trim (Mid( ls_text, 6, 100 ) ), 6) ) 													//		 변경기수
			
# 			ld_handycap = Dec( Trim( Mid( ls_text, Pos( ls_text, '.' ) - 3, 6 )) )					// 부담중량
# 			ls_reason = Trim( Mid( ls_text, Pos( ls_text, '.' ) + 2, 20 ))									// 변경사유
			
			
# 			//  기수변경 내역	/////////////////////////////////////////////
# 			select horse into :ls_horse from cancel_j where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
							
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update cancel_j set 	jockey_o = : ls_jockey_o,		jockey_n = :ls_jockey_n,		handycap = :ld_handycap,		reason = :ls_reason
# 					where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO cancel_j  
# 									( rcity,				rdate,			rno,					gate,				horse,				jockey_o,				jockey_n,				handycap,				reason  )  
# 				VALUES ( :ls_rcity,		:ls_rdate,		:ll_rno,				:ll_gate,			:ls_horse,		:ls_jockey_o,		:ls_jockey_n,		:ld_handycap,		:ls_reason )  ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
# 			/////////////////////////////////////////////
			
# 		ELSE
			
# 			IF Integer( Mid(ls_text, 1, 4) ) > 0 Then
# 				ls_rdate  = Mid(ls_text, 1, 4) + Mid(ls_text, 6, 2) + Mid(ls_text, 9, 2)			//경주일자
				
# 				ll_rno = Long( Trim( Mid( ls_text, Pos( ls_text, 'R' ) - 2, 2)) )
# 				ll_gate =  Long( Trim( Mid( ls_text, Pos( ls_text, 'R' ) + 3, 4)) )
			
# 				ls_horse =  Trim( Mid( ls_text, Pos( ls_text, 'R  ' ) + 7, 10) )
				
# 				ls_reason = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + 10, 20 ))								// 변경사유
				
				
# 				//  말 취소내역 /////////////////////////////////////////////
# 				select horse into :ls_horse from cancel_h where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
								
# 				IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
				
# 					update cancel_h set 	reason = :ls_reason
# 						where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
					
# 					IF SQLCA.SQLCODE <> 0 THEN
# 						MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 						ROLLBACK ;
# 						Return -1
# 					END IF					
# 					COMMIT;
					
# 				ELSE
				
# 					INSERT INTO cancel_h  
# 										( rcity,				rdate,			rno,					gate,					horse,				reason  )  
# 					VALUES ( :ls_rcity,		:ls_rdate,		:ll_rno,				:ll_gate,			:ls_horse,		:ls_reason )  ;
				
# 					IF SQLCA.SQLCODE <> 0 THEN
# 						MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 						ROLLBACK ;
# 						Return -1
# 					END IF					
# 					COMMIT;
					
# 				END IF
# 				/////////////////////////////////////////////
					
# 			END IF
					
# 		END IF
		
		
			
		
		
		
		
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1



# end function

# public function integer wf_convert_23_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_imdate, ls_rdate, ls_rday, ls_rcity, ls_grade, ls_dividing, ls_rname, ls_rcon1, ls_rcon2, ls_weather, ls_rstate, ls_rmoisture
# Long		ll_rno, ll_rseq, ll_distance
# Long		ll_prize, ll_prize1, ll_prize2, ll_prize3, ll_prize4, ll_prize5, ll_subprize1, ll_subprize2, ll_subprize3

# Long		ll_rank, ll_gate, ll_pos, ll_rating
# String		ls_horse, ls_birthplace, ls_sex, ls_age, ls_jockey, ls_trainer, ls_host
# Double	ld_handicap

# Long		ll_weight, ll_record
# String		ls_weight, ls_record, ls_gap, ls_corners, ls_iweight

# String		ls_g1f, ls_g3f, ls_s1f, ls_1corner, ls_2corner, ls_3corner, ls_4corner
# Long		ll_g1f, ll_g3f, ll_s1f, ll_1corner, ll_2corner, ll_3corner, ll_4corner
# String		ls_gsingle, ls_gdouble

# Double	ld_alloc
# String		ls_pair
# Long 		ll_pair1, ll_pair2

# Dec		ld_sale1, ld_sale2, ld_sale3, ld_sale4, ld_sale5, ld_sale6, ld_sale7, ld_sale8

# String		ls_r1alloc, ls_r3alloc, ls_r2alloc, ls_r12alloc, ls_r23alloc, ls_r333alloc, ls_r123alloc, ls_r4f, ls_r3f

# String		ls_furlong, ls_passage, ls_passage_t
# String		ls_passage_s1f, ls_passage_1c, ls_passage_2c, ls_passage_3c, ls_passage_4c, ls_passage_g1f

# Long		ll_seq				// rec013 rno seq

# String		ls_judge, ls_judge_reason, ls_audit_reason


# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )				//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		IF Left(ls_text,10) = '----------' THEN ll_handle = Mod(ll_handle + 1, 8)

# 		CHOOSE CASE ll_handle

# 			CASE 0					//경주 제반조건 설정을 읽어들인다.

# 				IF	Trim(Mid(ls_text,1,2)) = '제목'  THEN													//제    목
				
				
# 					ls_imdate = Mid(ls_text,6,12)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 					ls_rdate  = '20' + Mid(ls_imdate,1,2) + Mid(ls_imdate,4,2) + Mid(ls_imdate,7,2)	//경주일자
					
# 					select replace( :ls_rdate, ' ', '0' ) into :ls_rdate from dual ;
					
# 					ls_rday = Mid( ls_text, Pos( ls_text, ')' ) - 1, 1)									//	요일
					
# 					ll_rseq = Long (Mid( ls_text, Pos( ls_text, ')' ) + 5, 2)	)						//	제 몇차
																											
# 					ll_rno = Long(Mid(ls_text, Pos( ls_text, "경주") - 2,2))						//경주번호
					
					
					
# 				ELSEIF Left(ls_text,1) = '날' THEN														//(서울)
				
# 					ls_rcity = '부산'	

# 					ll_distance = 1000																//거리
# 					ls_grade = '주행검사'														//등급
# 					ls_dividing = '주행검사'
# 					ls_rname = '주행검사'														//경주명
					
# 					ls_weather =  Trim( Mid( ls_text, Pos( ls_text, ':' ) + 1, 6))			//날씨
# 					ls_rstate =  Trim( Mid( ls_text, Pos( ls_text, '주로상태 :' ) + 6, 4))
# 					ls_rmoisture = Trim( Mid( ls_text, Pos( ls_text, '(' ) - 1, 6))
					
# 					select rdate into :ls_rdate from rec010 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno ;
					
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 					ELSE
						
# 						INSERT INTO rec010  
# 								( rcity,   							rdate,   							rno,   							rday,   							rseq,   							distance,   						grade,   
# 								  dividing,   						rname,   							rcon1,   						rcon2,   							weather,   						rstate,   							rmoisture )  
# 						VALUES ( :ls_rcity,   					:ls_rdate,   						:ll_rno,   						:ls_rday,   						:ll_rseq,   						:ll_distance,   					:ls_grade,   
# 								  :ls_dividing,   					:ls_rname,   					:ls_rcon1,   					:ls_rcon2,   						:ls_weather,   					:ls_rstate,   						:ls_rmoisture )  ;
	
# 							IF SQLCA.SQLCODE <> 0 THEN
# 								MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 								ROLLBACK ;
# 								Return -1
# 							END IF					
# 							COMMIT;
# 						END IF

# 				END IF

# 			CASE 1								
# 			CASE 2						//경주순위 및 기수,조교사 마주 등을 읽어들인다.
				
# 				IF Left(ls_text,10) <> '----------' THEN 
					
# 					ll_rank = Long(Trim(Mid(ls_text,1,4)))
					
# 					ll_pos = Pos( ls_text, String(ll_rank))
# 					ll_gate = Long( Trim(Mid(ls_text, ll_pos + Len(String(ll_rank)), 7))	)									//게이트
					
# 					ls_text = Mid( ls_text,  ll_pos + Len(String(ll_rank)), 100 )
					
# 					ll_pos = Pos( ls_text, String(ll_gate))													//게이트 번호 위치 
# 					ls_horse = Trim(Mid(ls_text,ll_pos + Len(String(ll_gate)), 10))					//마필명
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ), 100) )
# 					ls_birthplace = Trim(Mid(ls_text, 1, 4)			)									//산지
										
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_birthplace ) + Len( ls_birthplace ), 100) )
# 					ls_sex = Trim( Mid( ls_text, 1, 2 ))													//성별
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_sex ) + Len( ls_sex ), 100) )
# 					ls_age = Trim(Mid(ls_text,1, 2))														//연령
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_age ) + Len( ls_age ), 100) )
# 					ld_handicap = Dec(Mid(ls_text,1, 2))													//부담중량
					
# 					IF Mid(ls_text,3, 1) = "+" THEN 														//추가 부담중량
# 						ld_handicap = ld_handicap + Dec(  Mid(ls_text,4, 3))
# 					ELSE
# 						ld_handicap = ld_handicap - Dec(  Mid(ls_text,4, 3))
# 					END IF
					
# 					ls_text = Trim( Mid( ls_text, 8, 100 ))
# 					ls_jockey = Trim(Mid(ls_text, 1, 4))													//기수
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey ) + Len( ls_jockey ), 100) )
# 					ls_trainer = Trim(Mid(ls_text, 1 ,6))													//조교사
					
# //					ls_host = Trim(Mid(ls_text, Pos(ls_text, ls_trainer) + 4, 10))										//마주
					
# //					ll_rating = Long(Trim(Mid(ls_text, Pos(ls_text, ls_host) + 10, 10)))

# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 					ELSE
					
# 						  INSERT INTO rec011  
# 									( rcity,              rdate,              rno,              gate,              rank,              horse,              birthplace,              h_sex,              h_age,              handycap,   
# 									  jockey,           joc_adv,           trainer,          host,              rating,			p_rank			  )  
# 						  VALUES ( :ls_rcity,     :ls_rdate,          	:ll_rno,           :ll_gate,          :ll_rank,           :ls_horse,          :ls_birthplace,          :ls_sex,            :ls_age,              :ld_handicap,   
# 									  :ls_jockey,       null,               :ls_trainer,       :ls_host,         :ll_rating,	0       )  ;
			  					
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","rec011 Insert Fail " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
						
# 						COMMIT;
# 					END IF

# 				END IF				
				
# 			CASE 3						//skip
# 			CASE 4						//마필기록 
					
# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					ll_rank = Long(Trim(Mid(ls_text,1, 2)))
					
# 					ll_pos = Pos( ls_text, String(ll_rank))
# 					ll_gate = Long( Trim(Mid(ls_text, ll_pos + Len(String(ll_rank)), 6)))									//게이트
					
# 					ls_text = Mid( ls_text,  ll_pos + Len(String(ll_rank)), 100 )
					
# 					ll_pos = Pos( ls_text, String(ll_gate))													//게이트 번호 위치 
# 					ls_horse = Trim(Mid(ls_text, ll_pos + Len(String(ll_gate)), 10))				//마필명
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ), 100) )
# 					ll_weight = Long( Trim( Mid(ls_text, 1, 3)) )											//마체중
					
# 					ls_iweight = ''																				//마체중 증감
					
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, String(ll_weight) ) + Len( String(ll_weight) ), 100) )
# 					ls_record = Trim(Mid(ls_text, 1, 6))													//기록(String)
					
# 					ll_record = f_change_s2t(ls_record)													//수치로 변환된 기록
					
# 					ls_text = Mid( ls_text, Pos( ls_text, ls_record ) + Len( ls_record ), 100) 
					
# 					ls_gap = Trim( Mid( ls_text, 1,7 )) 
					
# 					IF ls_gap = ''  THEN 

# 						ls_judge =  Mid(Trim(ls_text), 1, 1)
# 					ELSE
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_gap ) + Len( ls_gap ), 100) )
# 						ls_judge = Trim(Mid(ls_text, 1, 1))													//	판정
# 					END IF
					
# //					ls_text = Mid( ls_text, Pos( ls_text, ls_judge ) + Len( ls_judge ), 100) 
					
# 					IF  ls_judge = '합'  or ls_judge = '연' THEN
# 						ls_judge_reason = ""
# 						ls_audit_reason = Trim( Right(ls_text,  10))
# 					ELSE 
						
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_judge ) + Len( ls_judge ), 100) )
# 						ls_judge_reason = Trim(Mid(ls_text, 1, 5))

# 						ls_audit_reason =  Trim(Mid(ls_text, 6, 10))
						
# 					END IF

# //					ls_text = Trim( Right(ls_text,  10))
# //					ls_audit_reason = Trim( Mid( ls_text, Pos( ls_text, ' '), 10))
					
					
# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE rec011  
#      							SET h_weight = :ll_weight, 	w_change = :ls_iweight,		record = :ls_record,	i_record = :ll_record,	gap = :ls_gap,		corners = :ls_corners,
								
# 								       judge = :ls_judge,		judge_reason = :ls_judge_reason, 		audit_reason = :ls_audit_reason
#    							WHERE rec011.rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF

# 			CASE 5						//skip
# 			CASE 6						//코너별 전개기록

# 				IF Trim(Left(ls_text,10)) <> '----------' THEN 
					
# 					ll_rank = Long(Trim(Mid(ls_text,1, 2)))
					
# 					ll_pos = Pos( ls_text, String(ll_rank))
# 					ll_gate = Long( Trim(Mid(ls_text, ll_pos + Len(String(ll_rank)), 6)))									//게이트
					
# 					ls_text = Mid( ls_text,  ll_pos + Len(String(ll_rank)), 100 )
					
# 					ll_pos = Pos( ls_text, String(ll_gate))													//게이트 번호 위치 
# 					IF ll_gate >= 10 THEN
# //						ls_g3f = Trim( Mid(ls_text, ll_pos + 2, 10))											//G3F(String)
# 						ls_corners = Trim( Mid(ls_text, ll_pos + 2, 20))									//ls_corners(String)
# 					ELSE
# //						ls_g3f = Trim( Mid(ls_text, ll_pos + 1, 10))												//G3F(String)
# 						ls_corners = Trim( Mid(ls_text, ll_pos + 1, 20))									//ls_corners(String)
# 					END IF
					
# //					ll_g3f = f_change_s2t(ls_g3f)													//G3F
					
# 					IF ll_rank > 90 THEN
# 						ls_s1f = ''
# 						ls_3corner = ''
# 						ls_4corner = ''
# 						ls_g1f = ''
# 						ls_g3f = ''

# 					ELSE

# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_corners ) + 15, 100 ))
# 						ls_s1f = Trim( Mid(ls_text, 1, 6))														//S1F(String)
# 						ll_s1f = f_change_s2t(ls_s1f)																//S1F
						
# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_s1f) + 6, 100 ))					//400
# 						ls_3corner = Trim( Mid(ls_text, 1, 6))
# 						ll_3corner = f_change_s2t(ls_3corner)
	
# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_3corner) + 6, 100 ))			//G400
# 						ls_4corner = Trim( Mid(ls_text, 1, 6))
# 						ll_4corner = f_change_s2t(ls_4corner)

# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_4corner) + 6, 100 ))
# 						ls_g3f = Trim( Mid(ls_text, 1, 6))														//S1F(String)
# 						ll_g3f = f_change_s2t(ls_g3f)																//S1F
						
# 						ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_g3f) + 6, 100 ))
# 						ls_g1f = Trim( Mid(ls_text, 1, 10)	)													//G3F(String)
# 						ll_g1f = f_change_s2t(ls_g1f)																//G3F
						
	
# 					END IF
					
					

					
# 					select rdate into :ls_rdate from rec011 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인

# 						  UPDATE rec011  
#      							SET rg3f = :ls_g3f, 	rs1f = :ls_s1f,		r1c = :ls_1corner,	r2c = :ls_2corner,	  r3c = :ls_3corner,		r4c = :ls_4corner,  rg1f = :ls_g1f,	corners = :ls_corners,
# 								  host = '심사'
#    							WHERE rec011.rcity = :ls_rcity  and rdate = :ls_rdate and  rno = :ll_rno and gate = :ll_gate    ;

	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno) + ' ' + String(ll_gate ) + ls_horse)
# 							ROLLBACK ;
# 							Return -1
# 						END IF	
						
# 						COMMIT;
						
# 					END IF
					
# 				END IF
				

				
# 		END CHOOSE
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
   
# NEXT

# ipos = 0

# update rec010 set rmoisture = replace( replace(  replace(rmoisture, '%', ''), '(', ''), ')', '' )
#  where rcity = :ls_rcity and rdate = :ls_rdate
# ;
# commit ;


# Return 1
# end function

# public function integer wf_convert_55_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_rdate, ls_imdate
# String		ls_team, ls_trainer, ls_team_num, ls_horse, ls_rider, ls_in_time, ls_out_time, ls_t_time, ls_remark

# LongLong		ll_tot_prize, ll_year_prize

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN Return -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 

# 	IF Len( Trim(ls_text ) ) > 0 THEN 
	
# 		IF Left( ls_text, 2) = '제목' THEN
# 			ls_imdate = Mid(ls_text,6, 8)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 			ls_rdate  = '20' + Mid(ls_imdate,1,2) + Mid(ls_imdate,4,2) + Mid(ls_imdate,7,2)	//경주일자
			
# 		ELSEIF Long( Left( ls_text, 4) ) >= 1 THEN

# 			ls_team = Trim( Mid( ls_text, 5, 2) )
# 			ls_trainer = Trim( Mid( ls_text, 9, 3))
# 			ls_team_num = Trim( Mid( ls_text, 13, 2))
# 			ls_horse = Trim( Mid( ls_text, 16, 10))
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ) , 100 ))
# 			ls_rider = Trim ( Mid( ls_text, 1, 1 ))
			
# 			ls_in_time = Trim( Mid( ls_text, 5, 5))
# 			ls_out_time = Trim( Mid( ls_text, 15, 5))
# 			ls_t_time = Trim( Mid( ls_text, 27, 4))
# 			ls_remark = Trim( Mid( ls_text, 34, 100))
	
# 			select horse into :ls_horse from training where rcity = :ls_rcity and tdate = :ls_rdate and horse = :ls_horse  ;
						
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update training set 	team = :ls_team,				trainer = :ls_trainer,				team_num = :ls_team_num,				rider = :ls_rider,			
# 											in_time = :ls_in_time,			out_time = :ls_out_time,			t_time = :ls_t_time,						remark = :ls_remark
# 				 where rcity = :ls_rcity and tdate = :ls_rdate and horse = :ls_horse ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO training  
# 								( rcity,			tdate,			horse,				team,				trainer,				team_num,			
# 								  rider,		in_time,		out_time,			t_time,			remark )  
# 					 VALUES ( :ls_rcity,		:ls_rdate,		:ls_horse,			:ls_team,			:ls_trainer,			:ls_team_num,		
# 								  :ls_rider,	:ls_in_time,	:ls_out_time,		:ls_t_time,		:ls_remark )  ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
			
# 		END IF
	
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1
# end function

# public function integer wf_convert_71_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_imdate, ls_rdate, ls_rday, ls_rcity, ls_grade, ls_dividing, ls_rname, ls_rcon1, ls_rcon2, ls_weather, ls_rstate, ls_rmoisture
# Long		ll_rno, ll_rseq, ll_distance

# Long		ll_gate, ll_pos
# String		ls_horse, ls_gear1, ls_gear2, ls_blood1, ls_blood2, ls_treat1, ls_treat2


# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		IF Trim( Mid( ls_text, 1, 1)) = '─' THEN ll_handle =  ll_handle + 1

# 		CHOOSE CASE ll_handle

# 			CASE 0					//경주 제반조건 설정을 읽어들인다.

# 				IF	Trim(Mid(ls_text,1,3)) = '경주일'  THEN																	//	경주일
					
# 					ls_rcity = '부산'	
# 					ls_imdate = Mid(ls_text, 6, 10)																				//	날짜변환을 위해 임시로 저장 '98년06월07일'
# 					ls_rdate  = Mid(ls_imdate, 1, 4) + Mid(ls_imdate, 6, 2) + Mid(ls_imdate, 9, 2)			//	경주일자
# 					ll_rno = Long( Mid( ls_text, Pos( ls_text, ls_imdate ) + 10, 5))							

# 				END IF
				
# 				delete from exp012 where rcity = :ls_rcity and rdate = :ls_rdate  ;
# 				commit ;

# 			CASE 1								
# 			CASE 2						//경주순위 및 기수,조교사 마주 등을 읽어들인다.
				
# 					IF	Trim(Mid(ls_text,1,3)) = '경주일'  THEN																	//	경주일
					
# 						ll_handle = 0																									// Next Race init 
						
# 						ls_rcity = '부산'	
# 						ls_imdate = Mid(ls_text, 6, 10)																				//	날짜변환을 위해 임시로 저장 '98년06월07일'
# 						ls_rdate  = Mid(ls_imdate, 1, 4) + Mid(ls_imdate, 6, 2) + Mid(ls_imdate, 9, 2)			//	경주일자
# 						ll_rno = Long( Mid( ls_text, Pos( ls_text, ls_imdate ) + 10, 5))							
	
# 					END IF
				
# 				IF Long( Trim( Mid(ls_text, 1, 3) )) > 0 AND Long( Trim( Mid(ls_text, 1, 3) )) < 20 THEN

# 					ll_gate = Long( Trim(Mid(ls_text, 1, 3) ))																			//	게이트
# 					ls_horse = Trim(Mid(ls_text, Pos( ls_text, String(ll_gate)) + Len(String(ll_gate)), 10))					//	마필명

# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ), 100) )
					
# 					IF Long( Trim(Mid(ls_text, 1, 4))) > 2000 THEN																	//	보조장구1 check,   2000보다 크면 보조장구 없이 바로 폐출혈이나 진료사항 
							
# 						ls_gear1 = ''
						
# 						IF Long( Trim(Mid(ls_text, 11, 2))) > 0 THEN																//	폐출혈1 check, 폐출혈1이 있으면 
# 							ls_blood1 = Trim(Mid(ls_text, 1, 13))
# 							ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_blood1 ) + Len( ls_blood1 ), 100) )
							
# 							ls_treat1 = ls_text
# 						ELSE
							
# 							ls_blood1 = ''
# 							ls_treat1 = ls_text
							
# 						END IF
						
# 					ELSE
						
# 						ls_gear1 = Trim(Mid(ls_text, 1, 11))																			//	보조장구1이 있으면 
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_gear1 ) + Len( ls_gear1 ), 100) )
						
# 						IF Long( Trim(Mid(ls_text, 11, 2))) > 0 THEN																//	폐출혈1 check, 폐출혈1이 있으면 
# 							ls_blood1 = Trim(Mid(ls_text, 1, 13))
# 							ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_blood1 ) + Len( ls_blood1 ), 100) )
							
# 							ls_treat1 = ls_text
# 						ELSE
							
# 							ls_blood1 = ''
# 							ls_treat1 = ls_text
							
# 						END IF
						
# 					END IF

# 					select rdate into :ls_rdate from exp012 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate ;
					
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
# 					ELSE
						
# 						INSERT INTO exp012  
# 								( rcity,   				rdate,   			rno,			gate,				horse,			gear1,				blood1,			treat1   	 )  
# 						VALUES ( :ls_rcity,   		:ls_rdate,   		:ll_rno,		:ll_gate,			:ls_horse,		:ls_gear1,			:ls_blood1,		:ls_treat1  )  ;
	
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
# 						COMMIT;
							
# 					END IF
					
# 				ELSE		// Second Line
					
# 					IF Long( Trim(Mid(ls_text, 1, 4))) > 2000 THEN																	//	보조장구2 check,   2000보다 크면 보조장구 없이 바로 폐출혈이나 진료사항 
							
# 						ls_gear2 = ''
						
# 						IF Long( Trim(Mid(ls_text, 11, 2))) > 0 THEN																//	폐출혈2 check, 폐출혈2이 있으면 
# 							ls_blood2 = Trim(Mid(ls_text, 1, 13))
# 							ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_blood2 ) + Len( ls_blood2 ), 100) )
							
# 							ls_treat2 = ls_text
# 						ELSE
							
# 							ls_blood2 = ''
# 							ls_treat2 = ls_text
							
# 						END IF
						
# 					ELSE
						
# 						ls_gear2 = Trim(Mid(ls_text, 1, 11))																			//	보조장구2이 있으면 
# 						ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_gear2 ) + Len( ls_gear2 ), 100) )
						
# 						IF Long( Trim(Mid(ls_text, 11, 2))) > 0 THEN																//	폐출혈2 check, 폐출혈2 이 있으면 
# 							ls_blood2 = Trim(Mid(ls_text, 1, 13))
# 							ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_blood2 ) + Len( ls_blood2 ), 100) )
							
# 							ls_treat2 = ls_text
# 						ELSE
							
# 							ls_blood2 = ''
# 							ls_treat2 = ls_text
							
# 						END IF
						
# 					END IF
					
# 					select rdate into :ls_rdate from exp012 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate ;
					 
# 					IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
					
# 						update exp012 set gear2 = :ls_gear2,				blood2 = :ls_blood2,			treat2 = :ls_treat2 
# 						where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate ;
						
# 						IF SQLCA.SQLCODE <> 0 THEN
# 							MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_rdate + ' ' + String(ll_rno))
# 							ROLLBACK ;
# 							Return -1
# 						END IF					
# 						COMMIT;
						
# 					ELSE
# 					END IF
				
# 				END IF			
				
				
				
# 		END CHOOSE
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_72_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_tdate, ls_horse, ls_team, ls_hospital, ls_disease

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_rating

# Longlong		ll_tot_prize, ll_price

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text = mle_krafile.TextLine () 
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		ls_tdate = Trim( Mid( ls_text, 1, 10) )
# 		ls_tdate = mid(ls_tdate, 1,4) + mid(ls_tdate, 6, 2) + mid(ls_tdate, 9,2)
# 		ls_horse = Trim( Mid( ls_text, 11, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len(ls_horse), 300 ))
# 		ls_team = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_team ) + Len(ls_team), 300 ))
# 		ls_hospital= Trim( Mid( ls_text, 1, Pos( ls_text, ' ' )) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_hospital ) + Len(ls_hospital), 300 ))
# 		ls_disease= Trim( Mid( ls_text, 1, 100) )
		
# 		select horse into :ls_horse from treat where rcity = :ls_rcity and tdate = :ls_tdate and horse = :ls_horse and team = :ls_team and hospital = :ls_hospital and disease = :ls_disease   ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update treat set 	team = :ls_team,				hospital = :ls_hospital,			disease = :ls_disease
# 			 where rcity = :ls_rcity  and tdate = :ls_tdate and horse = :ls_horse and team = :ls_team and hospital = :ls_hospital and disease = :ls_disease  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO treat  
# 							( rcity,			tdate,			horse,			team,			hospital,			disease    )  
# 				 VALUES ( :ls_rcity,		:ls_tdate,		:ls_horse,		:ls_team,		:ls_hospital,		:ls_disease )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
   
# LOOP

# Return 1
# end function

# public function integer wf_convert_b1_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_horse, ls_birthplace, ls_sex, ls_birth, ls_age, ls_grade, ls_team, ls_trainer, ls_host, ls_paternal, ls_maternal

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_rating

# Longlong		ll_tot_prize, ll_price

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		ls_horse = Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len(ls_horse), 300 ))
# 		ls_birthplace = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_birthplace ) + Len(ls_birthplace), 300 ))
# 		ls_sex= Trim( Mid( ls_text, 1, 1) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_sex ) + Len(ls_sex), 300 ))
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = ( Mid( ls_text, Pos( ls_text, ls_birth ) + Len(ls_birth), 300 ))
# 		ls_age = Trim( Mid( ls_text, 1, 2) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_age ) + Len(ls_age), 300 ))
# 		ls_grade = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_grade ) + Len(ls_grade), 300 ))
# 		ls_team = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_team ) + Len(ls_team), 300 ))
# 		ls_trainer = Trim( Mid( ls_text, 1, 3) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_trainer ) + Len(ls_trainer), 300 ))
# 		ls_host = Trim( Mid( ls_text, 1, 13) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_host ) + Len(ls_host), 300 ))
# 		ls_paternal = Trim( Mid( ls_text, 1, Pos( ls_text, '  ' )) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_paternal ) + Len(ls_paternal), 300 ))
# 		ls_maternal = Trim( Mid( ls_text, 1, Pos( ls_text, '  ' )) )

# 		ls_text =Right( ls_text, 63 )
# 		li_tot_race = Integer( Trim( Mid( ls_text, 1, 5 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 6, 5 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 11, 5 )))
# 		li_year_race = Integer( Trim( Mid( ls_text, 16, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 21, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 26, 5 )))
		
# 		ll_tot_prize = LongLong( Trim( Mid( ls_text, 31, 11 )))
# 		li_rating = LongLong( Trim( Mid( ls_text, 42, 11 )))
# 		ll_price = LongLong( Trim( Mid( ls_text, 53, 11 ))) * 1000
		
# 		select horse into :ls_horse from horse where rcity = :ls_rcity and horse = :ls_horse and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update horse set 	rcity = :ls_rcity,				age = :ls_age,						grade = :ls_grade,			team = :ls_team,				trainer = :ls_trainer,			
# 									host = :ls_host,				paternal = :ls_paternal,			maternal = :ls_maternal,	
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			
# 									year_race = :li_year_race,	year_1st = :li_year_2nd,			year_2nd = :li_year_2nd,	
# 									tot_prize = :ll_tot_prize,		rating = :li_rating,				price = :ll_price
# 			where rcity = :ls_rcity and horse = :ls_horse and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO horse  
# 							( rcity,			horse,			birthplace,				sex,			birth,				age,				grade,			team,				trainer,			host,				paternal,				maternal,
# 							  tot_race,		tot_1st,					tot_2nd,		year_race,		year_1st,			year_2nd,		tot_prize,			rating,			price	)  
# 				 VALUES ( :ls_rcity,		:ls_horse,		:ls_birthplace,			:ls_sex,		:ls_birth,			:ls_age,			:ls_grade,			:ls_team,			:ls_trainer,		:ls_host,			:ls_paternal,			:ls_maternal,
# 							  :li_tot_race,	:li_tot_1st,				:li_tot_2nd,	:li_year_race,		:li_year_1st,		:li_year_2nd,		:ll_tot_prize,		:li_rating,			:ll_price)  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_b1_20180719_busan ();String		ls_text, ls_wdate
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_horse, ls_birthplace, ls_sex, ls_birth, ls_age, ls_grade, ls_team, ls_trainer, ls_host, ls_paternal, ls_maternal

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_rating, li_tot_3rd, li_year_3rd

# Longlong		ll_tot_prize, ll_price

# ls_wdate = Mid(is_fname, 1, 8)

# delete from horse
# where rcity = :ls_rcity ;
# commit ;

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )				//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0  and Left( ls_text,2) <> '--' and  Left( ls_text,2) <> '마명'  THEN

# 		ls_horse = Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len(ls_horse), 300 ))
# 		ls_birthplace = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_birthplace ) + Len(ls_birthplace), 300 ))
# 		ls_sex= Trim( Mid( ls_text, 1, 1) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_sex ) + Len(ls_sex), 300 ))
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = ( Mid( ls_text, Pos( ls_text, ls_birth ) + Len(ls_birth), 300 ))
# 		ls_age = Trim( Mid( ls_text, 1, 3) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_age ) + Len(ls_age), 300 ))
# 		ls_grade = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_grade ) + Len(ls_grade), 300 ))
# 		ls_team = Trim( Mid( ls_text, 1, 2) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_team ) + Len(ls_team), 300 ))
# 		ls_trainer = Trim( Mid( ls_text, 1, 3) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_trainer ) + Len(ls_trainer), 300 ))
# 		ls_host = Trim( Mid( ls_text, 1, 13) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_host ) + Len(ls_host), 300 ))
# 		ls_paternal = Trim( Mid( ls_text, 1, Pos( ls_text, '  ' )) )
	
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_paternal ) + Len(ls_paternal), 300 ))
# 		ls_maternal = Trim( Mid( ls_text, 1, Pos( ls_text, '  ' )) )

# 		ls_text =Right( ls_text, 74 )
# 		li_tot_race = Integer( Trim( Mid( ls_text, 1, 2 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 4, 6 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 10, 6 )))
# 		li_tot_3rd = Integer( Trim( Mid( ls_text, 16, 6 )))
		
# 		li_year_race = Integer( Trim( Mid( ls_text, 22, 6 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 28, 6 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 34, 6 )))
# 		li_year_3rd = Integer( Trim( Mid( ls_text, 40, 6 )))
		
# 		ll_tot_prize = LongLong( Trim( Mid( ls_text, 46, 12 )))
# 		li_rating = LongLong( Trim( Mid( ls_text, 58, 6 )))
# 		ll_price = LongLong( Trim( Mid( ls_text, 64, 12 ))) * 1000
		
# 		select horse into :ls_horse from horse where rcity = :ls_rcity and horse = :ls_horse and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update horse set 	rcity = :ls_rcity,				age = :ls_age,						grade = :ls_grade,			team = :ls_team,				trainer = :ls_trainer,			
# 									host = :ls_host,				paternal = :ls_paternal,			maternal = :ls_maternal,	
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd,
# 									tot_prize = :ll_tot_prize,		rating = :li_rating,					price = :ll_price
# 			where rcity = :ls_rcity and horse = :ls_horse and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO horse  
# 							( rcity,			horse,			birthplace,				sex,			birth,				age,				grade,			team,				trainer,			host,				paternal,				maternal,
# 							  tot_race,		tot_1st,			tot_2nd,					tot_3rd,		year_race,		year_1st,			year_2nd,		year_3rd,		tot_prize,		rating,			price	)  
# 				 VALUES ( :ls_rcity,		:ls_horse,		:ls_birthplace,			:ls_sex,		:ls_birth,			:ls_age,			:ls_grade,		:ls_team,		:ls_trainer,		:ls_host,			:ls_paternal,			:ls_maternal,
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,				:li_tot_3rd,	:li_year_race,	:li_year_1st,		:li_year_2nd,	:li_year_3rd,	:ll_tot_prize,	:li_rating,		:ll_price)  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림","경주 제반조건을 Insert하는데 실패하였습니다! " + SQLCA.SqlErrtext + " " +  ls_horse )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# delete from horse_w
# where rcity = :ls_rcity
# and wdate = :ls_wdate ;
# commit ;

# insert into horse_w
# 	(
# 		select rcity,	:ls_wdate,		horse,			birth,			birthplace,				sex,			age,				grade,			team,				trainer,			host,				paternal,				maternal,
# 							  tot_race,		tot_1st,			tot_2nd,					tot_3rd,		year_race,		year_1st,			year_2nd,		year_3rd,		tot_prize,		rating,			price
#   		from horse
# 		where rcity = :ls_rcity 
# 		and length(trim(horse)) > 0
#   	);
	  
# commit ;

# Return 1
# end function

# public function integer wf_convert_b2_busan ();
# String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_jockey, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race

# ll_lines = mle_krafile.LineCount()

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴


# SetNull (ls_LineText)	

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
 
# //FOR i = 1 TO ll_lines - 1
# //      
# //	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# //	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		ls_jockey = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey ) + Len(ls_jockey), 300 ))
# 		IF Trim( Mid( ls_text, 1, 3) ) = '미계약' THEN
# 			ls_team = '00'
# 		ELSE
# 			IF Trim( Mid( ls_text, 1, 1) ) = '프' THEN 
# 				ls_team = '프'
# 			ELSE
# 				ls_team = Trim( Mid( ls_text, 1, 2) )
# 			END IF
# 		END IF
		
# 		ls_text = Trim( Right(ls_text, 56) )
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
# 		ls_age = Trim( Mid( ls_text, 11, 2) )
# 		ls_debut= Trim( Mid( ls_text, 13, 10) )
		
# 		ls_load_in = Trim( Mid( ls_text, 23, 2) )
# 		ls_load_out = Trim( Mid( ls_text, 25, 2) )
		
# 		li_tot_race = Integer( Trim( Mid( ls_text, 27, 5 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 32, 5 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 37, 5 )))
# 		li_year_race = Integer( Trim( Mid( ls_text, 42, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 47, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 52, 5 )))
		
# 		select jockey into :ls_jockey from jockey where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update jockey set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			
# 									year_race = :li_year_race,	year_1st = :li_year_2nd,			year_2nd = :li_year_2nd
# 			where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO jockey  
# 							( rcity,			jockey,			birth,				team,				age,				debut,			load_in,				load_out,
# 							  tot_race,		tot_1st,			tot_2nd,			year_race,		year_1st,			year_2nd )  
# 				 VALUES ( :ls_rcity,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_year_race,	:li_year_1st,		:li_year_2nd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# //	IF i = 1 THEN
# //		// + 2의 의미는 ~n라인 변경 을 의미 한다.
# //     	// 선택된 텍스트 만큼의 길이값을 더한다.
# //		ipos = Len( mle_krafile.TextLine() ) + 2
# //	END IF
# //	
# //    ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT

# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP
   
# //NEXT

# ipos = 0

# Return 1


# end function

# public function integer wf_convert_b2_20180719_busan ();
# String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity, ls_jockey, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_year_3rd, li_tot_3rd

# ll_lines = mle_krafile.LineCount()

# IF Mid( is_fname, 9,1) = 'p' THEN 
# 	ls_rcity = '부산'
# ELSEIF  Mid( is_fname, 9,1) = 's' THEN
# 	ls_rcity = '서울'
# ELSE
# 	ls_rcity = '서울'
# END IF

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()										//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)	

# String	ls_wdate		// 매주 데이터 입력된 일자
# Dec	ld_per

# ls_wdate = Mid(is_fname, 1, 8)

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
	 
# 	IF Len(Trim(ls_text)) > 0 and Left( ls_text,3) <> '---' and  Left( ls_text,3) <> '기수명'  THEN

# 		ls_jockey = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey ) + Len(ls_jockey), 300 ))
# 		IF Trim( Mid( ls_text, 1, 3) ) = '미계약' THEN
# 			ls_team = '00'
# 		ELSE
# 			IF Trim( Mid( ls_text, 1, 1) ) = '프' THEN 
# 				ls_team = '프'
# 			ELSE
# 				ls_team = Trim( Mid( ls_text, 1, 2) )
# 			END IF
# 		END IF
		
# 		ls_text = Trim( Right(ls_text, 84) )
		
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
# 		ls_age = Trim( Mid( ls_text, 13, 2) )
# 		ls_debut= Trim( Mid( ls_text, 17, 10) )
		
# 		ls_load_in = Trim( Mid( ls_text, 29, 2) )
# 		ls_load_out = Trim( Mid( ls_text, 34, 2) )
		
# 		li_tot_race = Integer( Trim( Mid( ls_text, 37, 10 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 47, 5 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 52, 5 )))
# 		li_tot_3rd = Integer( Trim( Mid( ls_text, 57, 5 )))
		
		
# 		li_year_race = Integer( Trim( Mid( ls_text, 63, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 68, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 73, 5 )))
# 		li_year_3rd = Integer( Trim( Mid( ls_text, 78, 5 )))
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 기수성적 입력 - 서울
# 		select jockey into :ls_jockey from letsrace.jockey where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update letsrace.jockey set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,	
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd
# 			where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO letsrace.jockey  
# 							( rcity,			jockey,			birth,				team,				age,				debut,			load_in,				load_out,
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,			year_3rd )  
# 				 VALUES ( :ls_rcity,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 기수성적 입력 - 부산
# 		select jockey into :ls_jockey from Busan.jockey where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update Busan.jockey set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,	
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd
# 			where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO Busan.jockey  
# 							( rcity,			jockey,			birth,				team,				age,				debut,			load_in,				load_out,
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,			year_3rd )  
# 				 VALUES ( :ls_rcity,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 주별 기수성적 입력 - 서울
# 		select jockey into :ls_jockey from letsrace.jockey_w where rcity = :ls_rcity and wdate = :ls_wdate and jockey = :ls_jockey and birth = :ls_birth  ;
		
# 		IF li_year_race = 0 or IsNull(li_year_race) THEN
# 			ld_per = 0
# 		ELSE
# 			ld_per = (li_year_1st +  li_year_2nd) * 100 /  li_year_race 
# 		END IF
		
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update letsrace.jockey_w set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,	
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd,
# 									year_per =  :ld_per
# 			where rcity = :ls_rcity and wdate = :ls_wdate 
# 			    and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO letsrace.jockey_w  
# 					  ( rcity,			wdate,		jockey,			birth,		team,			age,				debut,			load_in,		load_out,
# 					   tot_race,		tot_1st,	tot_2nd,		tot_3rd,	year_race,		year_1st,			year_2nd,		year_3rd, 	year_per )  
# 				 VALUES ( :ls_rcity,		:ls_wdate,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 					 :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd,  		 :ld_per ) ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 주별 기수성적 입력 - 부산
# 		select jockey into :ls_jockey from Busan.jockey_w where rcity = :ls_rcity and wdate = :ls_wdate and jockey = :ls_jockey and birth = :ls_birth  ;
		
# 		IF li_year_race = 0 or IsNull(li_year_race) THEN
# 			ld_per = 0
# 		ELSE
# 			ld_per = (li_year_1st +  li_year_2nd) * 100 /  li_year_race 
# 		END IF
		
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update Busan.jockey_w set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,			
# 									load_in = :ls_load_in,			load_out = :ls_load_out,			
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,	
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd,
# 									year_per =  :ld_per
# 			where rcity = :ls_rcity and wdate = :ls_wdate 
# 			    and jockey = :ls_jockey and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO Busan.jockey_w  
# 					  ( rcity,			wdate,		jockey,			birth,		team,			age,				debut,			load_in,		load_out,
# 					   tot_race,		tot_1st,	tot_2nd,		tot_3rd,	year_race,		year_1st,			year_2nd,		year_3rd, 	year_per )  
# 				 VALUES ( :ls_rcity,		:ls_wdate,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 					 :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd,  		 :ld_per ) ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
# 		///////////////////////////////////////////////////////////////////////////////
	  
# 	END IF

# //	IF i = 1 THEN
# //		// + 2의 의미는 ~n라인 변경 을 의미 한다.
# //     	// 선택된 텍스트 만큼의 길이값을 더한다.
# //		ipos = Len( mle_krafile.TextLine() ) + 2
# //	END IF
# //	
# //    ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT

# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP
   
# //NEXT

# ipos = 0

# Return 1


# end function

# public function integer wf_convert_b3_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_trainer, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 THEN

# 		ls_trainer = Trim( Mid( ls_text, 1, 3) )
# 		ls_team = Trim( Mid( ls_text, 4, 2) )

# 		ls_birth= Trim( Mid( ls_text, 6, 10) )
# 		ls_age = Trim( Mid( ls_text, 16, 2) )
# 		ls_debut= Trim( Mid( ls_text, 18, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_debut ) + Len( ls_debut ) , 100 ))
		
# 		IF Len(ls_text) = 30 THEN
# 			li_tot_race = Integer( Trim( Mid( ls_text, 1, 5 )))
# 			li_tot_1st = Integer( Trim( Mid( ls_text, 6, 5 )))
# 			li_tot_2nd = Integer( Trim( Mid( ls_text, 11, 5 )))
# 			li_year_race = Integer( Trim( Mid( ls_text, 16, 5 )))
# 			li_year_1st = Integer( Trim( Mid( ls_text, 21, 5 )))
# 			li_year_2nd = Integer( Trim( Mid( ls_text, 26, 5 )))

# 		ELSE
# 			li_tot_race = Integer( Trim( Mid( ls_text, 1, 6 )))
# 			li_tot_1st = Integer( Trim( Mid( ls_text, 7, 5 )))
# 			li_tot_2nd = Integer( Trim( Mid( ls_text, 12, 5 )))
# 			li_year_race = Integer( Trim( Mid( ls_text, 17, 5 )))
# 			li_year_1st = Integer( Trim( Mid( ls_text, 22, 5 )))
# 			li_year_2nd = Integer( Trim( Mid( ls_text, 27, 5 )))
# 		END IF
		
# 		select trainer into :ls_trainer from trainer where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update trainer set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,					
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd
# 			where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO trainer  
# 							( rcity,			trainer,			birth,				team,				age,				debut,			
# 							  tot_race,		tot_1st,			tot_2nd,			year_race,		year_1st,			year_2nd )  
# 				 VALUES ( :ls_rcity,		:ls_trainer,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_year_race,	:li_year_1st,		:li_year_2nd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_b3_20180719_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_trainer, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_tot_3rd, li_year_3rd

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 and Left( ls_text,3) <> '---' and  Left( ls_text,3) <> '조교사' THEN

# 		ls_trainer = Trim( Mid( ls_text, 1, 5) )
# 		ls_team = Trim( Mid( ls_text, 7, 2) )

# 		ls_birth= Trim( Mid( ls_text, 11, 10) )
# 		ls_age = Trim( Mid( ls_text, 23, 2) )
# 		ls_debut= Trim( Mid( ls_text, 27, 10) )

# 		li_tot_race = Integer( Trim( Mid( ls_text, 38, 6 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 45, 6 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 50, 5 )))
# 		li_tot_3rd = Integer( Trim( Mid( ls_text, 55, 5 )))
		
# 		li_year_race = Integer( Trim( Mid( ls_text, 61, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 66, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 71, 5 )))
# 		li_year_3rd = Integer( Trim( Mid( ls_text, 76, 5 )))
		
# 		select trainer into :ls_trainer from trainer where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update trainer set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,					
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_3rd,			tot_2nd = :li_tot_3rd,
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd
# 			where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO trainer  
# 							( rcity,			trainer,			birth,				team,				age,				debut,			
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,		year_3rd )  
# 				 VALUES ( :ls_rcity,		:ls_trainer,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,			:li_year_race,	:li_year_1st,		:li_year_2nd,	:li_year_3rd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_b4_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows, ll_rno, ll_gate

# String		ls_rcity = '부산', ls_rdate, ls_imdate
# String		ls_team, ls_trainer, ls_team_num, ls_horse, ls_rider, ls_rider_k, ls_remark, ls_judge, ls_audit_reason,	ls_judge_reason 

# LongLong		ll_tot_prize, ll_year_prize

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 

# 	IF Len( Trim(ls_text ) ) > 0 THEN 
	
# 		IF Left( ls_text, 2) = '제목' THEN
# 			ls_imdate = Mid(ls_text, 6, 13)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 			ls_rdate  = Mid(ls_imdate, 1, 4) + Mid(ls_imdate, 7, 2) + Mid(ls_imdate, 11, 2)	//경주일자
			
# 			ll_rno = Long( Trim( Mid( ls_text, Pos( ls_text, '경주' ) -2, 2) ))
			
# 		ELSEIF Long( Left( ls_text, 4) ) >= 1 THEN

# 			ll_gate = Long( Trim( Mid( ls_text, 1, 4) ))
# 			ls_horse = Trim( Mid( ls_text, 8, 10))
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ) , 100 ))
# 			ls_audit_reason = Trim ( Mid( ls_text, 1, Pos( ls_text, ')' ) + 1) )
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_audit_reason ) + Len( ls_audit_reason ) + 1 , 100 ))
			
# 			IF Pos( ls_text, '(' ) = 0 THEN
# 				ls_rider = ''
# 				ls_rider_k = ''
				
# 				ls_text =  Trim( Mid( ls_text, 50, 100 ))
# 				ls_judge = Trim( Mid( ls_text, 1, 4))
# 				ls_judge_reason = Trim( Mid( ls_text, 8, 100 ))
# 			ELSE
# 				ls_rider = Trim ( Mid( ls_text, Pos( ls_text, '(' ) - 4, 4 ))
# 				ls_rider_k = Trim ( Mid( ls_text, Pos( ls_text, '(' ) + 1, Pos( ls_text, ')' ) - Pos( ls_text, '(' ) - 1 ))
				
				
# 				IF Pos( ls_text, '합격') > 0 THEN
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, '합격') - 2 , 100 ))
# 					ls_judge = Trim( Mid( ls_text, 1, 4))
					
# 					ls_judge_reason = Trim( Mid( ls_text, Pos( ls_text, ls_judge) + 3 , 100 ))
					
# 				ELSEIF Pos( ls_text, '취소') > 0 THEN
# 					ls_text = Trim( Mid( ls_text, Pos( ls_text, '취소') - 3 , 100 ))
# 					ls_judge = Trim( Mid( ls_text, 1, 4))
					
# 					ls_judge_reason = Trim( Mid( ls_text, Pos( ls_text, ls_judge) + 4 , 100 ))
					
# 				ELSE
# 					ls_judge_reason = '프로그램 수정 필요'
					
# 				END IF
				
# 			END IF
			
# 			select horse into :ls_horse from start_audit where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
						
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update start_audit set 	rider = :ls_rider,			rider_k = :ls_rider_k,		audit_reason = :ls_audit_reason,		judge = :ls_judge,			judge_reason = :ls_judge_reason
# 				 where rcity = :ls_rcity and rdate = :ls_rdate and rno = :ll_rno and gate = :ll_gate  ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO start_audit  
# 								( rcity,			rdate,			rno,					gate,				horse,			
# 								  rider,		rider_k,		audit_reason,		judge,			judge_reason  )  
# 					 VALUES ( :ls_rcity,		:ls_rdate,		:ll_rno,				:ll_gate,			:ls_horse,			
# 								  :ls_rider,	:ls_rider_k,	:ls_audit_reason,	:ls_judge,			:ls_judge_reason )  ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
			
# 		END IF
	
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1



# end function

# public function integer wf_convert_b5_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_rdate, ls_imdate
# String		ls_team, ls_trainer, ls_team_num, ls_horse, ls_rider, ls_rider_k, ls_remark, ls_judge

# LongLong		ll_tot_prize, ll_year_prize

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
	
# //	li_LastLine = mle_krafile.SelectedLine ()
# //	ll_Pos += mle_krafile.LineLength ()

# 	IF Len( Trim(ls_text ) ) > 0 THEN 
	
# 		IF Left( ls_text, 2) = '제목' THEN
# 			ls_imdate = Mid(ls_text, 6, 13)													//날짜변환을 위해 임시로 저장 '98년06월07일'
# 			ls_rdate  = Mid(ls_imdate, 1, 4) + Mid(ls_imdate, 7, 2) + Mid(ls_imdate, 11, 2)	//경주일자
			
# 		ELSEIF Long( Left( ls_text, 6) ) >= 1 THEN

# 			IF ls_rdate >= '20230413' THEN
			
# 				ls_team = Trim( Mid( ls_text, 1, 6) )
# 				ls_team_num = Trim( Mid( ls_text, 10, 2))
# 				ls_horse = Trim( Mid( ls_text, 15, 10))
				
				
# 				ls_rider = Trim ( Mid( Trim(ls_text), 22, 15 ))
				
				
# 				ls_rider_k = ''
				
# 				ls_judge = Trim( Right( Trim(ls_text), 14))
				
# 			ELSE

# 				ls_team = Trim( Mid( ls_text, 1, 6) )
# 				ls_team_num = Trim( Mid( ls_text, 10, 2))
# 				ls_horse = Trim( Mid( ls_text, 15, 10))
				
# 				ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_horse ) + Len( ls_horse ) , 100 ))
# 				ls_rider = Trim ( Mid( ls_text, 1, Pos( ls_text, '(' ) - 1) )
				
# 				ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_rider ) + Len( ls_rider ) + 1 , 100 ))
# 				ls_rider_k = Trim ( Mid( ls_text, 1, Pos( ls_text, ')' ) - 1 ))
				
# 				ls_judge = Trim( Mid( ls_text, Pos( ls_text, ')' ) + 1, 50))
				
# 			END IF

# 			select horse into :ls_horse from start_train where rcity = :ls_rcity and tdate = :ls_rdate and horse = :ls_horse  ;
						
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update start_train set 	team = :ls_team,			team_num = :ls_team_num,				rider = :ls_rider,			
# 												rider_k = :ls_rider_k,		judge = :ls_judge
# 				 where rcity = :ls_rcity and tdate = :ls_rdate and horse = :ls_horse ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO start_train  
# 								( rcity,			tdate,			horse,				team,				team_num,			
# 								  rider,		rider_k,		judge )  
# 					 VALUES ( :ls_rcity,		:ls_rdate,		:ls_horse,			:ls_team,			:ls_team_num,		
# 								  :ls_rider,	:ls_rider_k,	:ls_judge )  ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_horse )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
			
# 		END IF
	
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1



# end function

# public function integer wf_convert_b6_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_host, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut, ls_tot_race, ls_year_race, ls_text1, ls_text2

# Int			li_total, li_cancel, li_current

# LongLong		ll_tot_prize, ll_year_prize

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text = mle_krafile.TextLine () 
	
# //	li_LastLine = mle_krafile.SelectedLine ()
# //	ll_Pos += mle_krafile.LineLength ()

# 	IF Len( Trim( ls_text)) <> 0 and  Left( ls_text, 1 ) <> '-' and Trim( Right(ls_text,2)) <> '상금' THEN 
	
# 		ls_host = Trim( Mid( ls_text, 1, 12) )
		
# 		ls_text = Trim( Mid( ls_text, Pos(ls_text, ls_host) + Len(ls_host), 500 ))
# 		li_total = Integer( Trim( Mid( ls_text, 1, Pos(ls_text, '두') -  1) ) )
		
# 		ls_text = Trim( Mid( ls_text, Pos(ls_text, '두' ) + 1, 200 ))
# 		li_cancel =Integer( Trim( Mid( ls_text, 1, Pos(ls_text, '두') - 1 ) ))
		
# 		ls_text = Trim( Mid( ls_text, Pos(ls_text, '두' ) + 1, 200 ))
# 		li_current = Integer( Trim( Mid( ls_text, 1, Pos(ls_text, '두') - 1) ))

# 		ls_text = Trim( Mid( ls_text, Pos(ls_text, '두' ) + 1, 200 ))
# 		ls_debut= Trim( Mid( ls_text, 1, 10) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_debut ) + Len( ls_debut ) , 100 ))
# 		ls_year_race = Trim ( Mid( ls_text, 1, Pos(ls_text, ')' ) + 1 ))
		
# 		ls_text = Trim( Mid( ls_text,  Pos(ls_text, ')' ) + 1 , 100 ))
# 		ll_year_prize =  LongLong ( Trim( Mid( ls_text, 1, Pos(ls_text, ' ' )  )))

# 		ls_text = Trim( Mid( ls_text,  Pos(ls_text, ' ' ), 100 ))
# 		ls_tot_race = Trim( Mid( ls_text, 1, Pos(ls_text, ')' ) + 1 )) 
		
# 		ls_text = Trim( Mid( ls_text,  Pos(ls_text, ')' ) + 1 , 100 ))
# 		ll_tot_prize = LongLong( trim( Mid( ls_text, 1, 13  )))
		
# 		select host into :ls_host from host where rcity = :ls_rcity and host = :ls_host ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update host set 	h_total = :li_total,				h_cancel = :li_cancel,				h_current = :li_current,				debut = :ls_debut,			
# 							  		tot_race = :ls_tot_race,		tot_prize = :ll_tot_prize,			year_race = :ls_year_race,			year_prize = :ll_year_prize
# 			where rcity = :ls_rcity and host = :ls_host   ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_host )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO host  
# 							( rcity,			host,			h_total,				h_cancel,				h_current,				debut,			
# 							  tot_race,		tot_prize,			year_race,		year_prize )  
# 				 VALUES ( :ls_rcity,		:ls_host,		:li_total,				:li_cancel,				:li_current,				:ls_debut,		
# 							  :ls_tot_race,	:ll_tot_prize,		:ls_year_race,	:ll_year_prize )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_host )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1
# end function

# public function integer wf_convert_b7_busan ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, j, ipos, jpos, kpos, ll_handle, ll_rows

# String		ls_rcity = '부산', ls_imdate
# String		ls_judge, ls_before, ls_after, ls_reason, ls_cdate, ls_host

# integer  li_LastLine, li_LineNumber, li_SelectedLine
# long ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string ls_LineText

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()									//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)																	//	리턴할 문자 초기화 

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
	
# 	IF Mid( ls_text, 1, 4) = '----' THEN ll_handle = ll_handle + 1

# 	IF ll_handle = 2 and  Mid( ls_text, 1, 4) <> '----'  and Len( Trim( ls_text )) > 0 THEN 

# 			ls_before = Trim( Mid( Trim( ls_text ), 1, 10))
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_before ) + Len( ls_before ) , 100 ))
# 			ls_after = Trim ( Mid( ls_text, 1, 10 ))
			
# 			ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_after ) + Len( ls_after ) , 100 ))
			
# 			IF Long( Left( ls_text, 4)) > 0 THEN
# 				ls_host = ''
# 				ls_cdate = Trim( Mid( ls_text, 1, 10))
# 				ls_reason = Trim( Mid( ls_text, 11, 100))
# 			ELSE
# 				ls_host = Trim ( Mid( ls_text, 1, 14 ))
				
# 				ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_host ) + Len( ls_host ) , 100 ))
# 				ls_cdate = Trim( Mid( ls_text, 1, 10))
# 				ls_reason = Trim( Mid( ls_text, 11, 100))
# 			END IF

# 			select h_after into :ls_after from hname where rcity = :ls_rcity and h_before = :ls_before and h_after = :ls_after  ;
						
# 			IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
			
# 				update hname set 	host = :ls_host,			cdate = :ls_cdate,			reason = :ls_reason			
# 				 where rcity = :ls_rcity and h_before = :ls_before and h_after = :ls_after  ;
				
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_after )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			ELSE
			
# 				INSERT INTO hname  
# 								( rcity,			h_before,			h_after,			host,				cdate,			reason )
# 					 VALUES ( :ls_rcity,		:ls_before,		:ls_after,			:ls_host,			:ls_cdate,		:ls_reason ) ;
			
# 				IF SQLCA.SQLCODE <> 0 THEN
# 					MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_after )
# 					ROLLBACK ;
# 					Return -1
# 				END IF					
# 				COMMIT;
				
# 			END IF
	
# 	END IF
		
# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP

# Return 1



# end function

# public function integer wf_update_11_busan (string as_rdate);String		ls_rcity, ls_rdate, ls_rs1f, ls_r1c,  ls_r2c, ls_r3c, ls_r4c, ls_rg3f, ls_rg2f, ls_rg1f, ls_record
# Integer	i_rno, i_gate

# Integer	i_s1f, i_r1c, i_r2c, i_r3c, i_r4c, i_g3f, i_g2f, i_g1f, i_record

# DECLARE C_race CURSOR FOR  
#  SELECT rcity, rdate, rno, gate, rs1f, r1c, r2c, r3c, r4c, rg3f, rg2f, rg1f, record
#    FROM rec011  
#   WHERE rcity = '부산' and rdate = :as_rdate
#  ;
	
# OPEN C_race ;

# FETCH C_race INTO :ls_rcity, :ls_rdate, :i_rno, :i_gate, :ls_rs1f, :ls_r1c, :ls_r2c, :ls_r3c, :ls_r4c, :ls_rg3f, :ls_rg2f, :ls_rg1f, :ls_record ;

# DO WHILE SQLCA.SQLCODE = 0 
	
# 	i_s1f =  f_s2t( ls_rs1f )
	
# 	i_r1c =  f_s2t( ls_r1c ) 
# 	i_r2c =  f_s2t( ls_r2c ) 
# 	i_r3c =  f_s2t( ls_r3c ) 
# 	i_r4c =  f_s2t( ls_r4c ) 
# 	i_g3f =  f_s2t( ls_rg3f ) 
# //	i_g2f =  ( f_s2t( ls_rg3f ) +  f_s2t( ls_rg1f ) ) /2 			//	g2f 환산  (g3f + g1f) / 2

# 	i_g2f =  f_s2t( ls_rg2f ) 

# //	ls_rg2f = f_t2s( i_g2f)													//	g2f 환산기록 스트링 변환


# 	i_g1f =  f_s2t( ls_rg1f ) 
# 	i_record =  f_s2t( ls_record )
	
# 	update rec011 set i_s1f = :i_s1f, i_r1c = :i_r1c, i_r2c = :i_r2c, i_r3c = :i_r3c, i_r4c = :i_r4c, i_g3f = :i_g3f, i_g2f = :i_g2f , i_g1f = :i_g1f, i_record = :i_record
# 	 where rcity = '부산' and rdate = :as_rdate and rno = :i_rno and gate = :i_gate ;
	 
# 	IF sqlca.sqlnrows > 0 THEN
# //		COMMIT ;
# 	ELSE
# 		ROLLBACK;
# 		MessageBox("알림", SQLCA.SQLErrText + ls_Record )
# 		Return -1
# 	END IF
	
# 	FETCH C_race INTO :ls_rcity, :ls_rdate, :i_rno, :i_gate, :ls_rs1f, :ls_r1c, :ls_r2c, :ls_r3c, :ls_r4c, :ls_rg3f, :ls_rg2f, :ls_rg1f, :ls_record ;
	
# LOOP

# CLOSE C_race ;

# COMMIT ;


# return 1
# end function

# public function integer wf_convert_b2_jockey ();
# String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity, ls_jockey, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int		li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_year_3rd, li_tot_3rd

# ll_lines = mle_krafile.LineCount()

# integer  	li_LastLine, li_LineNumber, li_SelectedLine
# long 		ll_TextLength, ll_Pos = 1, ll_OrigPos, ll_OrigLength
# string 	ls_LineText


# IF Mid( is_fname, 9,1) = 'p' THEN 
# 	ls_rcity = '부산'
# ELSEIF  Mid( is_fname, 9,1) = 's' THEN
# 	ls_rcity = '서울'
# ELSE
# 	ls_rcity = '서울'
# END IF

# li_LineNumber = mle_krafile.LineCount()
# IF li_LineNumber = 0 THEN RETURN -1 

# ll_OrigPos = mle_krafile.SelectedStart ()											//	컨트롤 안에 선택된 텍스트의 첫번째 문자위치 리턴
# ll_OrigLength = mle_krafile.SelectedLength ()										//	컨트롤 내 문자들의 총수와 선택된 문자 내 길이를 리턴
# ll_TextLength = Len (mle_krafile.Text)											//	선택된 문자 길이 리턴
# SetNull (ls_LineText)	

# String	ls_wdate		// 매주 데이터 입력된 일자
# Dec		ld_per, ld_3per

# ls_wdate = Mid(is_fname, 1, 8)

# DO WHILE mle_krafile.SelectedLine () < li_LineNumber
	
# 	mle_krafile.SelectText (ll_Pos, 0)
	
# 	DO WHILE mle_krafile.SelectedLine () = li_LastLine
# 		ll_Pos ++
# 		IF ll_Pos > ll_TextLength THEN 
# 			EXIT
# 		END IF
# 		mle_krafile.SelectText (ll_Pos, 0)
# 	LOOP

# 	ls_text =  mle_krafile.TextLine () 
	 
# 	IF Len(Trim(ls_text)) > 0 and Left( ls_text,3) <> '---' and  Left( ls_text,3) <> '기수명'  THEN

# 		ls_jockey = Trim( Mid( ls_text, 1, 4) )
		
# 		ls_text = Trim( Mid( ls_text, Pos( ls_text, ls_jockey ) + Len(ls_jockey), 300 ))
# 		IF Trim( Mid( ls_text, 1, 3) ) = '미계약' THEN
# 			ls_team = '00'
# 		ELSE
# 			IF Trim( Mid( ls_text, 1, 1) ) = '프' THEN 
# 				ls_team = '프'
# 			ELSE
# 				ls_team = Trim( Mid( ls_text, 1, 2) )
# 			END IF
# 		END IF
		
# 		ls_text = Trim( Right(ls_text, 84) )
		
# 		ls_birth= Trim( Mid( ls_text, 1, 10) )
# 		ls_age = Trim( Mid( ls_text, 13, 2) )
# 		ls_debut= Trim( Mid( ls_text, 17, 10) )
		
# 		ls_load_in = Trim( Mid( ls_text, 29, 2) )
# 		ls_load_out = Trim( Mid( ls_text, 34, 2) )
		
# 		li_tot_race = Integer( Trim( Mid( ls_text, 37, 10 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 47, 5 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 52, 5 )))
# 		li_tot_3rd = Integer( Trim( Mid( ls_text, 57, 5 )))
		
		
# 		li_year_race = Integer( Trim( Mid( ls_text, 63, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 68, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 73, 5 )))
# 		li_year_3rd = Integer( Trim( Mid( ls_text, 78, 5 )))
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 기수성적 입력 
		
# 		delete from jockey where rcity = :ls_rcity and jockey = :ls_jockey and birth = :ls_birth  ;
					
			
# 		INSERT INTO jockey  
# 						( rcity,			jockey,			birth,				team,				age,				debut,			load_in,				load_out,
# 						  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,			year_3rd )  
# 			 VALUES ( :ls_rcity,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 						  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd )  ;
	
# 		IF SQLCA.SQLCODE <> 0 THEN
# 			MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 			ROLLBACK ;
# 			Return -1
# 		END IF					
# 		COMMIT;
			

		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 주별 기수성적 입력 
# 		delete from jockey_w where rcity = :ls_rcity and wdate = :ls_wdate and jockey = :ls_jockey and birth = :ls_birth  ;
		
# 		IF li_year_race = 0 or IsNull(li_year_race) THEN
# 			ld_per = 0
# 			ld_3per = 0
# 		ELSE
# 			ld_per = (li_year_1st +  li_year_2nd) * 100 /  li_year_race 
# 			ld_3per = (li_year_1st +  li_year_2nd + li_year_3rd) * 100 /  li_year_race 
# 		END IF
		
# 		INSERT INTO jockey_w  
# 				  ( rcity,			wdate,		jockey,			birth,		team,			age,				debut,			load_in,		load_out,
# 					tot_race,		tot_1st,	tot_2nd,		tot_3rd,	year_race,		year_1st,			year_2nd,		year_3rd, 	year_per, year_3per )  
# 			 VALUES ( :ls_rcity,		:ls_wdate,		:ls_jockey,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		:ls_load_in,			:ls_load_out,
# 				 :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,		:li_year_race,	:li_year_1st,		:li_year_2nd ,		:li_year_3rd,  		 :ld_per, 	:ld_3per ) ;
	
# 		IF SQLCA.SQLCODE <> 0 THEN
# 			MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_jockey )
# 			ROLLBACK ;
# 			Return -1
# 		END IF					
# 		COMMIT;
			
	  
# 	END IF

# //	IF i = 1 THEN
# //		// + 2의 의미는 ~n라인 변경 을 의미 한다.
# //     	// 선택된 텍스트 만큼의 길이값을 더한다.
# //		ipos = Len( mle_krafile.TextLine() ) + 2
# //	END IF
# //	
# //    ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT

# 	li_LastLine = mle_krafile.SelectedLine ()
# 	ll_Pos += mle_krafile.LineLength ()
		
# LOOP
   
# //NEXT

# ipos = 0


# update The1.jockey_w a
# set wrace = tot_race - ( select tot_race from The1.jockey_w where jockey = a.jockey and wdate = ( select max(wdate) from The1.jockey_w where wdate < a.wdate ) ),
# w1st = tot_1st - ( select tot_1st from The1.jockey_w where jockey = a.jockey and wdate = ( select max(wdate) from The1.jockey_w where wdate < a.wdate ) ),
# w2nd = tot_2nd - ( select tot_2nd from The1.jockey_w where jockey = a.jockey and wdate = ( select max(wdate) from The1.jockey_w where wdate < a.wdate ) ),
# w3rd = tot_3rd - ( select tot_3rd from The1.jockey_w where jockey = a.jockey and wdate = ( select max(wdate) from The1.jockey_w where wdate < a.wdate ) )
# where wdate = :ls_wdate
# ;
# commit;

# Return 1


# end function

# public function integer wf_update_11 (string as_rcity, string as_rdate);String		ls_rcity, ls_rdate, ls_rs1f, ls_r1c,  ls_r2c, ls_r3c, ls_r4c, ls_rg3f, ls_rg2f, ls_rg1f, ls_record
# Integer	i_rno, i_gate

# Integer	i_s1f, i_r1c, i_r2c, i_r3c, i_r4c, i_g3f, i_g2f, i_g1f, i_record

# DECLARE C_race CURSOR FOR  
#  SELECT rcity, rdate, rno, gate, rs1f, r1c, r2c, r3c, r4c, rg3f, rg2f, rg1f, record
#    FROM rec011  
#   WHERE rcity = :as_rcity and rdate = :as_rdate
#  ;
	
# OPEN C_race ;

# FETCH C_race INTO :ls_rcity, :ls_rdate, :i_rno, :i_gate, :ls_rs1f, :ls_r1c, :ls_r2c, :ls_r3c, :ls_r4c, :ls_rg3f, :ls_rg2f, :ls_rg1f, :ls_record ;

# DO WHILE SQLCA.SQLCODE = 0 
	
# 	i_s1f = f_s2t( ls_rs1f )
# 	i_r1c =  f_s2t( ls_r1c ) 
# 	i_r2c =  f_s2t( ls_r2c ) 
# 	i_r3c =  f_s2t( ls_r3c ) 
# 	i_r4c =  f_s2t( ls_r4c ) 
# 	i_g3f =  f_s2t( ls_rg3f ) 
# 	i_g2f =  ( f_s2t( ls_rg3f ) +  f_s2t( ls_rg1f ) ) /2 			//	g2f 환산  (g3f + g1f) / 2
# 	ls_rg2f = f_t2s( i_g2f)													//	g2f 환산기록 스트링 변환
# 	i_g1f =  f_s2t( ls_rg1f ) 
# 	i_record =  f_s2t( ls_record )
	
# 	update rec011 set i_s1f = :i_s1f, i_r1c = :i_r1c, i_r2c = :i_r2c, i_r3c = :i_r3c, i_r4c = :i_r4c, i_g3f = :i_g3f, i_g2f = :i_g2f , i_g1f = :i_g1f, i_record = :i_record, rg2f = :ls_rg2f 
# 	 where rcity = :as_rcity and rdate = :as_rdate and rno = :i_rno and gate = :i_gate ;
	 
# 	IF sqlca.sqlnrows > 0 THEN
# //		COMMIT ;
# 	ELSE
# 		ROLLBACK;
# 		MessageBox("알림", SQLCA.SQLErrText + ls_Record )
# 		Return -1
# 	END IF
	
# 	FETCH C_race INTO :ls_rcity, :ls_rdate, :i_rno, :i_gate, :ls_rs1f, :ls_r1c, :ls_r2c, :ls_r3c, :ls_r4c, :ls_rg3f, :ls_rg2f, :ls_rg1f, :ls_record ;
	
# LOOP

# CLOSE C_race ;

# COMMIT ;


# return 1
# end function

# public function integer wf_update_pop11 (string as_rcity, string as_rdate, integer ai_rno);////////////////////////////////////////////////////////////////////////
# //  Temp Rank Insert
# ////////////////////////////////////////////////////////////////////////
# Dec		i_complex
# Integer	i_rrank, i_rank, i_gate, ll_cnt


# select count(*) into :ll_cnt 
#   from rec011  
#  where rcity = :as_rcity
#     AND rdate = :as_rdate 
#     AND rno = :ai_rno;
	 
# IF ll_cnt = 0 THEN return 1

# DECLARE C_rank CURSOR FOR  
#  SELECT rank, gate
#    FROM rec011
#   WHERE rcity = :as_rcity
#     AND rdate = :as_rdate 
#     AND rno = :ai_rno
# 	 AND rank < 90
#   ORDER BY alloc1r*1    ASC, alloc3r*1     ASC ;

# OPEN C_rank ;

# FETCH C_rank INTO :i_rrank, :i_gate  ;

# IF SQLCA.SQLCODE <> 0 THEN
# 	ROLLBACK;
# 	MessageBox("알림",SQLCA.SQLErrText + "인기도 Rank 설정 중 에러발생!" + as_rcity + as_rdate + String(ai_rno ) )
# 	Return -1
# END IF

# DO WHILE SQLCA.SQLCODE = 0
	
# 	i_rank = i_rank + 1

# 	UPDATE rec011  a															//인기도 순위 Update
# 	  SET pop_rank = :i_rank,
# 	      p_rank = ( select rank from exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ) ,
# 			p_record = ( select complex from exp011 where a.rcity = rcity and a.rdate = rdate and a.rno = rno and a.gate = gate ) 
# 	WHERE  rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno AND gate = :i_gate   ;
		

# 	FETCH C_rank INTO :i_rrank, :i_gate  ;
	
# LOOP

# CLOSE C_rank;

# UPDATE rec011  															//가상 순위 Update
#   SET pop_rank = rank
# WHERE rcity = :as_rcity and rdate = :as_rdate AND rno = :ai_rno AND rank >= 90   ;


# COMMIT;
# ////////////////////////////////////////////////////////////////////////
# end function

# public function integer w_convert_b3_trainer ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity = '서울', ls_trainer, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_tot_3rd, li_year_3rd

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 and Left( ls_text,3) <> '---' and  Left( ls_text,3) <> '조교사' THEN

# 		ls_trainer = Trim( Mid( ls_text, 1, 5) )
# 		ls_team = Trim( Mid( ls_text, 7, 2) )

# 		ls_birth= Trim( Mid( ls_text, 11, 10) )
# 		ls_age = Trim( Mid( ls_text, 23, 2) )
# 		ls_debut= Trim( Mid( ls_text, 27, 10) )

# 		li_tot_race = Integer( Trim( Mid( ls_text, 38, 6 )))
# 		li_tot_1st = Integer( Trim( Mid( ls_text, 45, 6 )))
# 		li_tot_2nd = Integer( Trim( Mid( ls_text, 50, 5 )))
# 		li_tot_3rd = Integer( Trim( Mid( ls_text, 55, 5 )))
		
# 		li_year_race = Integer( Trim( Mid( ls_text, 61, 5 )))
# 		li_year_1st = Integer( Trim( Mid( ls_text, 66, 5 )))
# 		li_year_2nd = Integer( Trim( Mid( ls_text, 71, 5 )))
# 		li_year_3rd = Integer( Trim( Mid( ls_text, 76, 5 )))
		
# 		select trainer into :ls_trainer from trainer where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update trainer set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,					
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_3rd,			tot_2nd = :li_tot_3rd,
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd
# 			where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO trainer  
# 							( rcity,			trainer,			birth,				team,				age,				debut,			
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,		year_3rd )  
# 				 VALUES ( :ls_rcity,		:ls_trainer,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,			:li_year_race,	:li_year_1st,		:li_year_2nd,	:li_year_3rd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# Return 1
# end function

# public function integer wf_convert_b3_trainer ();String		ls_text
# Long		ll_fp, ll_readhandle, ll_lines, i, ipos, ll_handle, ll_rows

# String		ls_rcity, ls_trainer, ls_birth, ls_team, ls_load_in, ls_load_out, ls_age, ls_debut, ls_wdate

# Int			li_tot_1st, li_tot_2nd, li_tot_race, li_year_1st, li_year_2nd, li_year_race, li_tot_3rd, li_year_3rd
# Dec			ld_per, ld_3per

# ls_wdate = Mid( is_fname, 1,8)

# IF ls_wdate < '20180719' THEN
# 	MessageBox("","20180719 이후 데이터만 입력가능합니다")
# 	return -1
# END IF

# IF Mid( is_fname, 9,1) = 'p' THEN 
# 	ls_rcity = '부산'
# ELSEIF  Mid( is_fname, 9,1) = 's' THEN
# 	ls_rcity = '서울'
# ELSE
# 	ls_rcity = '서울'
# END IF

# ll_lines = mle_krafile.LineCount()
 
# FOR i = 1 TO ll_lines - 1
      
# 	mle_krafile.SelectText( ipos, 0 )					//	포커스의 시작점을 가리킨다.  
# 	ls_text = trim(mle_krafile.TextLine())			//	값을 가져 온다.
	 
# 	IF Len(Trim(ls_text)) > 0 and Left( ls_text,3) <> '---' and  Left( ls_text,3) <> '조교사' THEN

# 		ls_trainer = Trim( Mid( ls_text, 1, 5) )
		
# 		IF Len(ls_trainer) = 2 THEN
# 			ls_team = Trim( Mid( ls_text, 8, 2) )

# 			ls_birth= Trim( Mid( ls_text, 12, 10) )
# 			ls_age = Trim( Mid( ls_text, 24, 2) )
# 			ls_debut= Trim( Mid( ls_text, 28, 10) )
	
# 			li_tot_race = Integer( Trim( Mid( ls_text, 39, 6 )))
# 			li_tot_1st = Integer( Trim( Mid( ls_text, 46, 6 )))
# 			li_tot_2nd = Integer( Trim( Mid( ls_text, 51, 5 )))
# 			li_tot_3rd = Integer( Trim( Mid( ls_text, 56, 5 )))
			
# 			li_year_race = Integer( Trim( Mid( ls_text, 62, 5 )))
# 			li_year_1st = Integer( Trim( Mid( ls_text, 67, 5 )))
# 			li_year_2nd = Integer( Trim( Mid( ls_text, 72, 5 )))
# 			li_year_3rd = Integer( Trim( Mid( ls_text, 77, 5 )))
			
# 		ELSE
# 			ls_team = Trim( Mid( ls_text, 7, 2) )
	
# 			ls_birth= Trim( Mid( ls_text, 11, 10) )
# 			ls_age = Trim( Mid( ls_text, 23, 2) )
# 			ls_debut= Trim( Mid( ls_text, 27, 10) )
	
# 			li_tot_race = Integer( Trim( Mid( ls_text, 38, 6 )))
# 			li_tot_1st = Integer( Trim( Mid( ls_text, 45, 6 )))
# 			li_tot_2nd = Integer( Trim( Mid( ls_text, 50, 5 )))
# 			li_tot_3rd = Integer( Trim( Mid( ls_text, 55, 5 )))
			
# 			li_year_race = Integer( Trim( Mid( ls_text, 61, 5 )))
# 			li_year_1st = Integer( Trim( Mid( ls_text, 66, 5 )))
# 			li_year_2nd = Integer( Trim( Mid( ls_text, 71, 5 )))
# 			li_year_3rd = Integer( Trim( Mid( ls_text, 76, 5 )))
# 		END IF
		
# 		select trainer into :ls_trainer from trainer where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update trainer set 	age = :ls_age,					team = :ls_team,					debut = :ls_debut,					
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd
# 			where rcity = :ls_rcity and trainer = :ls_trainer and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO trainer  
# 							( rcity,			trainer,			birth,				team,				age,				debut,			
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,		year_3rd )  
# 				 VALUES ( :ls_rcity,		:ls_trainer,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,			:li_year_race,	:li_year_1st,		:li_year_2nd,	:li_year_3rd )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
		
		
# 		///////////
		
# 		///////////////////////////////////////////////////////////////////////////////
# 		// 주별 기수성적 입력 
		
# 		IF li_year_race = 0 or IsNull(li_year_race) THEN
# 			ld_per = 0
# 			ld_3per = 0
# 		ELSE
# 			ld_per = (li_year_1st +  li_year_2nd) * 100 /  li_year_race 
# 			ld_3per = (li_year_1st +  li_year_2nd + li_year_3rd) * 100 /  li_year_race 
# 		END IF
		
		
# 		select trainer into :ls_trainer from trainer_w where rcity = :ls_rcity and wdate = :ls_wdate and trainer = :ls_trainer and birth = :ls_birth  ;
					
# 		IF sqlca.sqlnrows > 0 THEN //	입력여부 확인
		
# 			update trainer_w set age = :ls_age,					team = :ls_team,					debut = :ls_debut,					
# 							  		tot_race = :li_tot_race,		tot_1st = :li_tot_1st,				tot_2nd = :li_tot_2nd,			tot_3rd = :li_tot_3rd,
# 									year_race = :li_year_race,	year_1st = :li_year_1st,			year_2nd = :li_year_2nd,	year_3rd = :li_year_3rd,
# 									year_per = :ld_per, 	year_3per = :ld_3per
# 			where rcity = :ls_rcity and wdate = :ls_wdate and trainer = :ls_trainer and birth = :ls_birth  ;
			
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		ELSE
		
# 			INSERT INTO trainer_w
# 							( rcity,			wdate, trainer,			birth,				team,				age,				debut,			
# 							  tot_race,		tot_1st,			tot_2nd,			tot_3rd,			year_race,		year_1st,			year_2nd,		year_3rd , year_per, year_3per)  
# 				 VALUES ( :ls_rcity,		:ls_wdate, :ls_trainer,		:ls_birth,			:ls_team,		:ls_age,			:ls_debut,		
# 							  :li_tot_race,	:li_tot_1st,		:li_tot_2nd,		:li_tot_3rd,			:li_year_race,	:li_year_1st,		:li_year_2nd,	:li_year_3rd, :ld_per, :ld_3per )  ;
		
# 			IF SQLCA.SQLCODE <> 0 THEN
# 				MessageBox("알림", SQLCA.SqlErrtext + " " +  ls_trainer )
# 				ROLLBACK ;
# 				Return -1
# 			END IF					
# 			COMMIT;
			
# 		END IF
# 		///////////
		
		
	  
# 	END IF

# 	IF i = 1 THEN
# 		// + 2의 의미는 ~n라인 변경 을 의미 한다.
#      	// 선택된 텍스트 만큼의 길이값을 더한다.
# 		ipos = Len( mle_krafile.TextLine() ) + 2
# 	END IF
	
#     ipos = ipos + Len( mle_krafile.TextLine() ) + 2
	
# //	IF i = 120 THEN EXIT
   
# NEXT

# ipos = 0

# update The1.trainer_w a
# set wrace = tot_race - ( select tot_race from The1.trainer_w where trainer = a.trainer and wdate = ( select max(wdate) from The1.trainer_w where wdate < a.wdate ) ),
# w1st = tot_1st - ( select tot_1st from The1.trainer_w where trainer = a.trainer and wdate = ( select max(wdate) from The1.trainer_w where wdate < a.wdate ) ),
# w2nd = tot_2nd - ( select tot_2nd from The1.trainer_w where trainer = a.trainer and wdate = ( select max(wdate) from The1.trainer_w where wdate < a.wdate ) ),
# w3rd = tot_3rd - ( select tot_3rd from The1.trainer_w where trainer = a.trainer and wdate = ( select max(wdate) from The1.trainer_w where wdate < a.wdate ) )
# where wdate = :ls_wdate
# ;
# commit;

# Return 1
# end function

# on w_kradata_input.create
# int iCurrent
# call super::create
# this.dw_1=create dw_1
# this.mle_krafile=create mle_krafile
# this.cb_1=create cb_1
# this.cb_2=create cb_2
# this.cb_3=create cb_3
# this.em_from=create em_from
# this.em_to=create em_to
# this.ddlb_status=create ddlb_status
# this.ddlb_fcode=create ddlb_fcode
# this.st_1=create st_1
# this.st_2=create st_2
# this.st_3=create st_3
# this.st_4=create st_4
# this.cb_4=create cb_4
# this.rb_s=create rb_s
# this.rb_b=create rb_b
# this.rb_t=create rb_t
# iCurrent=UpperBound(this.Control)
# this.Control[iCurrent+1]=this.dw_1
# this.Control[iCurrent+2]=this.mle_krafile
# this.Control[iCurrent+3]=this.cb_1
# this.Control[iCurrent+4]=this.cb_2
# this.Control[iCurrent+5]=this.cb_3
# this.Control[iCurrent+6]=this.em_from
# this.Control[iCurrent+7]=this.em_to
# this.Control[iCurrent+8]=this.ddlb_status
# this.Control[iCurrent+9]=this.ddlb_fcode
# this.Control[iCurrent+10]=this.st_1
# this.Control[iCurrent+11]=this.st_2
# this.Control[iCurrent+12]=this.st_3
# this.Control[iCurrent+13]=this.st_4
# this.Control[iCurrent+14]=this.cb_4
# this.Control[iCurrent+15]=this.rb_s
# this.Control[iCurrent+16]=this.rb_b
# this.Control[iCurrent+17]=this.rb_t
# end on

# on w_kradata_input.destroy
# call super::destroy
# destroy(this.dw_1)
# destroy(this.mle_krafile)
# destroy(this.cb_1)
# destroy(this.cb_2)
# destroy(this.cb_3)
# destroy(this.em_from)
# destroy(this.em_to)
# destroy(this.ddlb_status)
# destroy(this.ddlb_fcode)
# destroy(this.st_1)
# destroy(this.st_2)
# destroy(this.st_3)
# destroy(this.st_4)
# destroy(this.cb_4)
# destroy(this.rb_s)
# destroy(this.rb_b)
# destroy(this.rb_t)
# end on

# event open;call super::open;
# dw_1.SetTransObject(SQLCA)
# //dw_2.SetTransObject(SQLCA)


# em_from.Text = String(Today() ,'2024.11.01')
# em_to.Text = String(Today() ,'yyyy.mm.dd')

# ddlb_status.SelectItem("% All",1)
# ddlb_fcode.SelectItem("% All", 1)
# end event

# type uo_progress from w_sheet`uo_progress within w_kradata_input
# end type

# type dw_1 from datawindow within w_kradata_input
# integer x = 32
# integer y = 412
# integer width = 3561
# integer height = 3484
# integer taborder = 40
# boolean bringtotop = true
# string title = "none"
# string dataobject = "d_kradata_list"
# boolean hscrollbar = true
# boolean vscrollbar = true
# boolean livescroll = true
# end type

# event clicked;Long	ll_row
# Blob	lb_fcontents
# String	ls_fname, ls_fcontents
# Int 	li_fn

# IF row <= 0 THEN Return


# SelectRow(0,False)
# SelectRow(row, True)



# ls_fname = GetItemString(row, "fname")


# SELECTBLOB fcontents  
#   INTO :lb_fcontents  FROM krafile  
#  WHERE fname =:ls_fname
#  USING SQLCA ;
 
# mle_krafile.Text = String( lb_fcontents, EncodingANSI! )

# end event

# type mle_krafile from multilineedit within w_kradata_input
# integer x = 3602
# integer y = 416
# integer width = 3561
# integer height = 3484
# integer taborder = 50
# boolean bringtotop = true
# integer textsize = -10
# integer weight = 400
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = fixed!
# fontfamily fontfamily = modern!
# string facename = "나눔고딕코딩"
# long textcolor = 33554432
# string text = "      Contents"
# boolean hscrollbar = true
# boolean vscrollbar = true
# boolean autohscroll = true
# boolean autovscroll = true
# boolean hideselection = false
# end type

# type cb_1 from commandbutton within w_kradata_input
# integer x = 59
# integer y = 200
# integer width = 503
# integer height = 108
# integer taborder = 30
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# string text = "New File Input"
# end type

# event clicked;String		ls_rdate, ls_fcode, ls_fname, ls_fcontents, ls_fstatus, ls_today
# String		ls_path, ls_file[], ls_text
# Int			i, li_cnt
# Long		ll_row, ll_fp, ll_read, ll_existed

# Blob		lb_image 
# DateTime	ldt_today

# IF	GetFileOpenName("파일선택", ls_path, ls_file[],"TXT", "Text Files (*.TXT),*.TXT," + "Doc Files (*.RPT),*.RPT")  <> 1 THEN Return -1

# dw_1.Reset()

# li_cnt = UpperBound(ls_file)

# FOR i = 1 TO li_cnt
	
# 	ll_fp = FileOpen(ls_file[i], TextMode!)
	
# 	IF ll_fp = -1 THEN
# 		MessageBox("File Open Error","Can't Open file : " )
# 		Return
# 	END IF
	
# 	ll_read = FileReadEx(ll_fp, lb_image)
	
# 	ls_rdate = mid(ls_file[i], 1,8)
# 	ls_fname = ls_file[i]
	
# 	IF mid(ls_fname, 9,5) = 'dacom' THEN
# 		ls_fcode =  mid(ls_fname, 14,2)
# 	ELSE
# 		ls_fcode =  mid(ls_fname, 11,2)
# 	END IF
	
# 	/* input check */
# 	select fstatus into :ls_fstatus from kradata
# 	 where fname = :ls_fname ;

# 	IF SQLCA.SQLNROWS > 0 THEN		// not found
		
# 		delete from kradata
# 		 where fname = :ls_fname ;
# 		 commit;
		 
# 	ELSEIF SQLCA.SQLCODE = -1 THEN
# 		MessageBox("File Open Error", SQLCA.SQLErrText )
# 		FileClose (ll_fp )
# 		Return
# 	END IF
	 
# 	ll_row = dw_1.InsertRow(0)
# 	dw_1.ScrollToRow(ll_row)

# 	dw_1.SetItem(ll_row, "No", ll_row)
# 	dw_1.SetItem(ll_row, "fname", ls_fname)
# 	dw_1.SetItem(ll_row, "rdate", ls_rdate)
# 	dw_1.SetItem(ll_row, "fcode", ls_fcode)
# 	dw_1.SetItem(ll_row, "fstatus", "S")
	
# 	ldt_today = DateTime(today(), Now())
# 	dw_1.SetItem(ll_row, "in_date", ldt_today)
	
# 	dw_1.AcceptText()
	
# 	Insert into kradata  ( fname,              fcontents,              rdate,              fcode,              fstatus,              in_date )  
# 			values ( :ls_fname,              null,              :ls_rdate,              :ls_fcode,              'S',            :ldt_today ) ;
# 	IF SQLCA.SQLCODE = 0 THEN 
# 		COMMIT;
# 	ELSE
# 		MessageBox("Error", SQLCA.SQLErrText)
# 		ROLLBACK;
# 	END IF
	
# //	MessageBox("", len(lb_image))
	
# 	 Updateblob kradata 
# 		 set fcontents = :lb_image  // image : 그림이 저장될 필드 
# 	  where fname = :ls_fname
# 	  using SQLCA;
	
# 	IF SQLCA.SQLCode = 0 THEN 
# 		COMMIT;
# 		dw_1.SetItem(ll_row, "fstatus", "I")
# 		dw_1.AcceptText()
		
# 		update kradata set fstatus = "I" where fname = :ls_fname ;
# 		IF SQLCA.SQLCODE = 0 THEN 
# 			COMMIT;
# 		ELSE
# 			MessageBox("Error", SQLCA.SQLErrText)
# 			ROLLBACK;
# 		END IF
		
# 	ELSE 
# 		ROLLBACK;
# 	 	MessageBox("","저장 실패!!") 
# 	END IF
		
# 	FileClose (ll_fp )

# NEXT

# end event

# type cb_2 from commandbutton within w_kradata_input
# integer x = 1134
# integer y = 200
# integer width = 411
# integer height = 108
# integer taborder = 20
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# string text = "Search"
# end type

# event clicked;String		ls_OldSQL, ls_CurrentSQL, ls_Where
# String		ls_from, ls_to, ls_status, ls_fcode, ls_rcity


# dw_1.Reset()

# ls_OldSQL = dw_1.GetSqlSelect()

# ls_CurrentSQL = ls_OldSQL + " Where 1 =1 "

# ls_from = Mid(em_from.Text,1,4) + Mid(em_from.Text,6,2) + Mid(em_from.Text,9,2)
# ls_to = Mid(em_to.Text,1,4) + Mid(em_to.Text,6,2) + Mid(em_to.Text,9,2)
# ls_status = Mid(ddlb_status.Text,1,1)
# ls_fcode = Mid(ddlb_fcode.Text,1,2)

# IF rb_t.Checked = True THEN
# 	ls_rcity = '%'
# ELSEIF rb_s.Checked = True THEN
# 	ls_rcity = '서울'
# ELSEIF rb_b.Checked = True THEN
# 	ls_rcity = '부산'
# END IF


# ls_CurrentSQL = ls_CurrentSQL + " AND Left( Right( fname , 6), 2) like '" + ls_rcity + "'"
# ls_CurrentSQL = ls_CurrentSQL + " AND rdate >= '" + ls_from + "'"
# ls_CurrentSQL = ls_CurrentSQL + " AND rdate <= '" + ls_to + "'"
# ls_CurrentSQL = ls_CurrentSQL + " AND fstatus like '" + ls_status + "'"
# ls_CurrentSQL = ls_CurrentSQL + " AND fcode like '" + Trim(ls_fcode) + "'"


# dw_1.SetSQLSelect(ls_CurrentSQL)
# dw_1.Retrieve()
# dw_1.SEtSQLSelect(ls_OldSQL)

# dw_1.ResetUpdate()
# end event

# type cb_3 from commandbutton within w_kradata_input
# integer x = 1915
# integer y = 200
# integer width = 727
# integer height = 108
# integer taborder = 40
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# string text = "Convert"
# end type

# event clicked;String		ls_fcode, ls_check, ls_fname, ls_rdate, ls_rcity
# Long		ll_cnt, ll_row, ll_return
# Blob		lb_fcontents

# ll_cnt = dw_1.RowCount()

# FOR ll_row = 1 TO ll_cnt
	
# 	ls_check = dw_1.GetItemString(ll_row, "rcheck")
	
# 	IF ls_check = 'Y' THEN
		
# 		ls_fname = dw_1.GetItemString(ll_row, "fname")
		
# 		is_fname = ls_fname						//	파일명을 인스턴트 변수에 저장. 주별 기수 복승율 저장용    wf_convert_b2()   20180719 after

# 		SELECTBLOB fcontents  
# 		  INTO :lb_fcontents  FROM kradata
# 		 WHERE fname =:ls_fname
# 		 USING SQLCA ;
		 
# 		mle_krafile.Text = String(lb_fcontents, EncodingANSI!)
		
# 		ls_fcode = dw_1.GetItemString(ll_row, "fcode")
# 		ls_rdate = dw_1.GetItemString(ll_row, "rdate")
		
# 		ls_rcity = dw_1.GetItemString(ll_row, "city")
		
# 		IF ls_rcity = '서울' THEN
			
# 			CHOOSE CASE ls_fcode
	
# 				CASE  '11' 							//	race result
# 					ll_return = wf_convert_11()
# 				CASE '01' 							//	race expect
# 					ll_return = wf_convert_01()
# 				CASE '55' 							//	training
# 					ll_return = wf_convert_55()
# 				CASE '71' 							//	able text 
# 					ll_return = wf_convert_71()
# 				CASE '72' 							//	horse treat
# 					ll_return = wf_convert_72()
# 				CASE '23' 							//	gear
# 					ll_return = wf_convert_23()
# 				CASE '13' 							//	마필취소 및 기수변경 내역
# 					ll_return = wf_convert_13()
# 				CASE 'b1' 							//	horse Info
# 					IF ls_rdate >= '20180719' THEN
# 						ll_return = wf_convert_b1_20180719()
# 					ELSE
# 						ll_return = wf_convert_b1()
# 					END IF
					
# 				CASE 'b2' 							//	jockey Info
# 					IF ls_rdate >= '20180719' THEN
# 						ll_return = wf_convert_b2_jockey()
# 					ELSE
# 						ll_return = wf_convert_b2()
# 					END IF
					
					
# 				CASE 'b3' 							//	trainer Info
# 					IF ls_rdate >= '20180719' THEN
# 						ll_return = wf_convert_b3_trainer()
# 					ELSE
# 						ll_return = wf_convert_b3()
# 					END IF
# 				CASE 'b4' 							//	Start Training
# 					ll_return = wf_convert_b4()
# 				CASE 'b5' 							//	Start Audit
# 					ll_return = wf_convert_b5()
# 				CASE 'b6' 							//	host Info
# 					ll_return = wf_convert_b6()
# 				CASE 'b7' 							//	horse name change Info
# 					ll_return = wf_convert_b7()
			
# 			END CHOOSE
			
# 		ELSEIF ls_rcity = '부산' THEN
			
# 			CHOOSE CASE ls_fcode
	
# 				CASE  '11' 							//	race result
# 					ll_return = wf_convert_11_busan()
# 				CASE '01' 							//	race expect
# 					ll_return = wf_convert_01_busan()
# 				CASE '55' 							//	training
# 					ll_return = wf_convert_55_busan()
# 				CASE '71' 							//	able text 
# 					ll_return = wf_convert_71_busan()
# 				CASE '72' 							//	horse treat
# 					ll_return = wf_convert_72_busan()
# 				CASE '23' 							//	gear
# 					ll_return = wf_convert_23_busan()
# 				CASE '13' 							//		마필취소 및 기수변경 내역
# 					ll_return = wf_convert_13_busan()
# 				CASE 'b1' 							//	horse Info
# 					IF ls_rdate >= '20180719' THEN
# 						ll_return = wf_convert_b1_20180719_busan()
# 					ELSE
# 						ll_return = wf_convert_b1_busan()
# 					END IF
					
# 				CASE 'b2' 							//	jockey Info
# 					IF ls_rdate >= '20180719' THEN
# 						ll_return = wf_convert_b2_jockey()
# 					ELSE
# 						ll_return = wf_convert_b2_busan()
# 					END IF
					
					
# 				CASE 'b3' 							//	trainer Info
# 					IF ls_rdate >= '20180719' THEN
# 						ll_return = wf_convert_b3_trainer()
# 					ELSE
# 						ll_return = wf_convert_b3_busan()
# 					END IF
# 				CASE 'b4' 							//	Start Training
# 					ll_return = wf_convert_b4_busan()
# 				CASE 'b5' 							//	Start Audit
# 					ll_return = wf_convert_b5_busan()
# 				CASE 'b6' 							//	host Info
# 					ll_return = wf_convert_b6_busan()
# 				CASE 'b7' 							//	horse name change Info
# 					ll_return = wf_convert_b7_busan()
			
# 			END CHOOSE
			
# 		ELSE
			
# 			MessageBox("", ls_rcity)
			
# 		END IF
				
			
# 		IF ll_return = 1 THEN
# 			dw_1.SetItem( ll_row, "fstatus", "F")
# 			dw_1.AcceptText()
# 				update kradata set fstatus = "F" where fname = :ls_fname ;
# 			IF SQLCA.SQLCODE = 0 THEN 
# 				COMMIT;
# 			ELSE
# 				MessageBox("Error", SQLCA.SQLErrText)
# 				ROLLBACK;
# 			END IF
# 		ELSE
# 			dw_1.SetItem( ll_row, "fstatus", "E")
# 			update kradata set fstatus = "E" where fname = :ls_fname ;
# 			IF SQLCA.SQLCODE = 0 THEN 
# 				COMMIT;
# 			ELSE
# 				MessageBox("Error", SQLCA.SQLErrText)
# 				ROLLBACK;
# 			END IF
# 		END IF

# 	END IF
	
	
# NEXT

# COMMIT ;



# //FOR ll_row = 1 TO ll_cnt
# //	
# //	ls_check = dw_1.GetItemString(ll_row, "rcheck")
# //	
# //	IF ls_check = 'Y' THEN
# //		
# //		ls_fname = dw_1.GetItemString(ll_row, "fname")
# //
# //		SELECTBLOB fcontents  
# //		  INTO :lb_fcontents  FROM krafile  
# //		 WHERE fname =:ls_fname
# //		 USING SQLCA ;
# //		 
# //		mle_krafile.Text = String(lb_fcontents, EncodingANSI!)
# //		
# //		ls_fcode = dw_1.GetItemString(ll_row, "fcode")
# //		
# //		
# //		CHOOSE CASE ls_fcode
# //
# //			CASE  '11' 							//	race result
# //				ll_return = wf_update_11( Mid( ls_fname, 1, 8) )
# //			
# //
# //				
# //		END CHOOSE
# //			
# //			
# //		IF ll_return = 1 THEN
# //			dw_1.SetItem( ll_row, "fstatus", "C")
# //			dw_1.AcceptText()
# //				update krafile set fstatus = "C" where fname = :ls_fname ;
# //			IF SQLCA.SQLCODE = 0 THEN 
# //				COMMIT;
# //			ELSE
# //				MessageBox("Error", SQLCA.SQLErrText)
# //				ROLLBACK;
# //			END IF
# //		ELSE
# //			dw_1.SetItem( ll_row, "fstatus", "D")
# //			update krafile set fstatus = "D" where fname = :ls_fname ;
# //			IF SQLCA.SQLCODE = 0 THEN 
# //				COMMIT;
# //			ELSE
# //				MessageBox("Error", SQLCA.SQLErrText)
# //				ROLLBACK;
# //			END IF
# //		END IF
# //
# //	END IF
# //NEXT
# //
# //COMMIT ;




# end event

# type em_from from editmask within w_kradata_input
# integer x = 1509
# integer y = 72
# integer width = 517
# integer height = 92
# integer taborder = 40
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

# type em_to from editmask within w_kradata_input
# integer x = 2126
# integer y = 72
# integer width = 517
# integer height = 92
# integer taborder = 50
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

# type ddlb_status from dropdownlistbox within w_kradata_input
# integer x = 3131
# integer y = 72
# integer width = 594
# integer height = 588
# integer taborder = 60
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# string item[] = {"% All","S Start","I Input","E Error","F Finish"}
# borderstyle borderstyle = stylelowered!
# end type

# type ddlb_fcode from dropdownlistbox within w_kradata_input
# integer x = 3131
# integer y = 204
# integer width = 594
# integer height = 1156
# integer taborder = 50
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# boolean sorted = false
# boolean vscrollbar = true
# integer limit = 15
# string item[] = {"% All","01 Race Expect","11 Race Result","13 Cancel List ","23 Able Test","55 Training","71 Race Gear","72 Horse Treat","b1 Horse","b2 Jockey","b3 Trainer","b4 Start Audit","b5 Start Train","b6 Host","b7 Name Change","","","","",""}
# integer accelerator = 48
# borderstyle borderstyle = stylelowered!
# end type

# type st_1 from statictext within w_kradata_input
# integer x = 1115
# integer y = 88
# integer width = 366
# integer height = 52
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "Race Date :"
# alignment alignment = right!
# boolean focusrectangle = false
# end type

# type st_2 from statictext within w_kradata_input
# integer x = 2030
# integer y = 100
# integer width = 91
# integer height = 52
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

# type st_3 from statictext within w_kradata_input
# integer x = 2697
# integer y = 88
# integer width = 411
# integer height = 52
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

# type st_4 from statictext within w_kradata_input
# integer x = 2697
# integer y = 228
# integer width = 411
# integer height = 52
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# long textcolor = 33554432
# long backcolor = 67108864
# string text = "fcode :"
# alignment alignment = right!
# boolean focusrectangle = false
# end type

# type cb_4 from commandbutton within w_kradata_input
# integer x = 599
# integer y = 200
# integer width = 498
# integer height = 108
# integer taborder = 30
# boolean bringtotop = true
# integer textsize = -9
# integer weight = 700
# fontcharset fontcharset = hangeul!
# fontpitch fontpitch = variable!
# fontfamily fontfamily = modern!
# string facename = "나눔바른고딕"
# string text = "전체선택"
# end type

# event clicked;Long		ll_row, i , ll_RowCount


# ll_RowCount = dw_1.RowCount()
# FOR i = 1 TO ll_RowCount
# 	dw_1.SetItem( i, "rcheck", "Y")
# NEXT

# dw_1.AcceptText()
# end event

# type rb_s from radiobutton within w_kradata_input
# integer x = 352
# integer y = 76
# integer width = 279
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

# type rb_b from radiobutton within w_kradata_input
# integer x = 626
# integer y = 76
# integer width = 279
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

# type rb_t from radiobutton within w_kradata_input
# integer x = 73
# integer y = 76
# integer width = 279
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

