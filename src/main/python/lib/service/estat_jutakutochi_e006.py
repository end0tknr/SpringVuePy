#!python
# -*- coding: utf-8 -*-

#refer to
#  https://www.e-stat.go.jp/stat-search/files
#    ?layout=datalist&toukei=00200522&tstat=000001127155&cycle=0
#      &tclass1=000001129435&tclass2=000001129436

# 住宅の種類，建て方，建築の時期，建物の構造，階数 6-3
#    住宅の所有の関係(5区分)，建築の時期(7区分)別住宅数
#    －全国，都道府県，市区町村

from service.city import CityService
import re
import service.estat_jutakutochi

download_url = \
    "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031865679&fileKind=0"
insert_cols = ["pref","city",
               "build_year",            #建築時期
               "total",                 #総数
               "owned_house",           #持ち家
               "rented_house",          #借家
               ]
insert_sql  = "INSERT INTO estat_jutakutochi_e006 (%s) VALUES %s"
logger = None

class EstatJutakuTochiE006Service(
        service.estat_jutakutochi.EstatJutakuTochiService):

    def __init__(self):
        global logger
        logger = self.get_logger()

    def get_download_url(self):
        return download_url
    
    def get_insert_cols(self):
        return insert_cols
    
    def get_insert_sql(self):
        return insert_sql

    def load_wsheet( self, wsheet ):
        
        city_service = CityService()
        ret_data = []
        row_no = 12
        re_compile = re.compile("^\d\d_")

        while row_no < wsheet.max_row :
            city_code_name_str = wsheet.cell(column=6, row=row_no).value
            city_code_name = city_code_name_str.split("_")
            city_code_name[1] = city_code_name[1].replace("\s","")
            
            if row_no % 100 == 0:
                logger.info( "%d %s" % (row_no,city_code_name[1]))
            
            city_def = city_service.find_def_by_code_city(city_code_name[0],
                                                          city_code_name[1])
            if not city_def or not city_def["city"]:
                row_no += 1
                continue
            
            # 例. 02_1971～1980年 -> 1971～1980年
            build_year = wsheet.cell(column=8, row=row_no).value
            build_year = re_compile.sub("",build_year)
            
            new_info = {
                "pref"         : city_def["pref"],
                "city"         : city_def["city"],
                "build_year"   : build_year,
                "total"        : wsheet.cell(column=9, row=row_no).value,
                "owned_house"  : wsheet.cell(column=10, row=row_no).value,
                "rented_house" : wsheet.cell(column=11,row=row_no).value,
            }
            for atri_key in new_info:
                if new_info[atri_key] == "-":
                    new_info[atri_key] = None

            ret_data.append(new_info)
            row_no += 1
            
        return ret_data
