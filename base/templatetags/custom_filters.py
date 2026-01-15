from django import template

register = template.Library()


@register.filter
def t2s(value):      # 숫자기록을 타임으로 변환

    # CONCAT( mid( cast( (ai_record/60)/60 as char), 1, 1) , ':',  lpad( truncate( Mod((ai_record/60),60),0) , 2, '0' ), '.',  mid( CONCAT(Mod(ai_record,60)/6),1, 1) ) )
    ret = str(int((value/60)/60)) # + ":" +  str( value % 60)  #+ str(( value % 60)/6 )
    ret1 = str(int(value/60) % 60).zfill(2)
    ret2 = str(int( (value % 60 )/6))
    # print(ret, ret1, ret2, value)

    return ret + ' :' + ret1 + '.' + ret2


import re

@register.filter
def digits_only(value):
    if not value:
        return ""
    return "".join(re.findall(r"\d+", value))


@register.filter
def percent1(value):
    try:
        return f"{float(value) * 100:.1f}"
    except (TypeError, ValueError):
        return ""
