# String	ls_rcity, ls_from, ls_to, ls_flagdate

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
