#!python
# -*- coding: utf-8 -*-

#refer to
#  https://www.e-stat.go.jp/stat-search/files
#    ?layout=datalist&toukei=00200522&tstat=000001127155&cycle=0
#      &tclass1=000001129435&tclass2=000001129436

# 持ち家の増改築・改修工事,高齢者等のための設備工事,
# 耐震改修工事,耐震診断の有無,リフォーム工事の状況 157-3
#   住宅の建築の時期(7区分)，2014年以降の住宅の増改築
#   ・改修工事等(8区分)別持ち家数－全国，都道府県，市区町村

from service.city import CityService
import re
import service.estat_jutakutochi

download_url = \
    "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031904617&fileKind=0"
insert_cols = ["pref","city",
               "build_year",
               "reform_plan",
               "reform_kitchen_bath",
               "reform_floor_inner_wall",
               "reform_roof_outer_wall",
               "reform_pillar_basic",
               "reform_insulation",
               "reform_other"
               ]
insert_sql  = "INSERT INTO estat_jutakutochi_g157 (%s) VALUES %s"
re_compile_build_year_str = [re.compile("(\d+)～(\d+)年"),
                             re.compile("(\d+)年以前")]
logger = None

class EstatJutakuTochiG157Service(
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
        re_compile = re.compile("^\d+_")
        row_no = 0
        
        for row_vals in wsheet.iter_rows(min_row=12, values_only=True):
            row_vals = list(row_vals)
            
            city_code_name_str = row_vals[5]
            city_code_name = city_code_name_str.split("_")
            city_code_name[1] = city_code_name[1].replace("\s","")
            city_code_name[1] = city_code_name[1].replace("　","")

            city_def = city_service.find_def_by_code_city(city_code_name[0],
                                                          city_code_name[1])
            if not city_def or not city_def["city"]:
                row_no += 1
                continue
            
            if row_no % 100 == 0:
                logger.info( "%d %s" % (row_no,city_code_name[1]))

            # 住宅の建築の時期
            if row_vals[ 7] =="00_総数":
                continue

            # 例 02_1971～1980年 -> 1971～1980年
            build_year = re_compile.sub("",row_vals[7])

            for col_no in [10,11,12,13,14,15,16]:
                if row_vals[col_no] == "-":
                    row_vals[col_no] = 0

            new_info = {
                "pref"          :city_def["pref"],
                "city"          :city_def["city"],
                "build_year"    :build_year,
                "reform_plan"            :row_vals[10],
                "reform_kitchen_bath"    :row_vals[11],
                "reform_floor_inner_wall":row_vals[12],
                "reform_roof_outer_wall" :row_vals[13],
                "reform_pillar_basic"    :row_vals[14],
                "reform_insulation"      :row_vals[15],
                "reform_other"           :row_vals[16],
            }

            ret_data.append(new_info)
            row_no += 1
            
        return ret_data
    
    
    def get_group_by_city(self):
        sql = "select * from estat_jutakutochi_g157"
        
        ret_data_tmp = {}
        
        db_conn = self.db_connect()
        with self.db_cursor(db_conn) as db_cur:
            try:
                db_cur.execute(sql)
            except Exception as e:
                logger.error(e)
                logger.error(sql)
                return []
            
            for ret_row in  db_cur.fetchall():
                ret_row = dict( ret_row )

                if not ret_row["city"]:
                    continue
                
                pref_city = "%s\t%s" % ( ret_row["pref"],ret_row["city"])
                if not pref_city in ret_data_tmp:
                    ret_data_tmp[pref_city] = {}

                build_year = self.parse_build_year_str( ret_row["build_year"] )

                if not build_year in ret_data_tmp[pref_city]:
                    ret_data_tmp[pref_city][build_year] = {}

                del ret_row["pref"]
                del ret_row["city"]
                del ret_row["build_year"]

                ret_data_tmp[pref_city][build_year] = ret_row

        ret_datas = []
        for pref_city, ret_data in ret_data_tmp.items():
            (ret_data["pref"],ret_data["city"]) = pref_city.split("\t")
            ret_datas.append(ret_data)
            
        return ret_datas
        
    def parse_build_year_str(self,year_str):

        re_result = re_compile_build_year_str[0].search(year_str)
        if re_result:
            return "%s\t%s" % ( re_result.group(1),re_result.group(2) )
        
        re_result = re_compile_build_year_str[1].search(year_str)
        if re_result:
            return "%s\t%s" % ( 0,re_result.group(1) )

        logger.error( year_str )
        return None
    

