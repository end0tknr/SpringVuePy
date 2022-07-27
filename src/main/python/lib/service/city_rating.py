#!python
# -*- coding: utf-8 -*-

from service.city_profile          import CityProfileService
from service.mlit_fudousantorihiki import MlitFudousanTorihikiService
from service.newbuild              import NewBuildService
from util.db import Db
import appbase
import datetime
import json
import re

logger = appbase.AppBase().get_logger()

class CityRatingService(CityProfileService):
    
    def __init__(self):
        pass
    
    def calc_save_ratings(self):

        profiles_hash = self.calc_city_profiles()
        profiles_hash = self.calc_fudousan_torihiki( profiles_hash )
        profiles_hash = self.calc_sales_count_by_city( profiles_hash )

        profiles_list = self.conv_ratings_to_list(profiles_hash)
        
        util_db = Db()
        util_db.bulk_update("city_profile",
                            ["pref","city"],
                            ["pref","city","rating"],
                            profiles_list )


    def calc_city_profiles(self):
        city_profile_service = CityProfileService()
        city_profiles = city_profile_service.get_all()
        
        profiles_hash = {}
        for city_profile in city_profiles:
            pref_city = city_profile["pref"] +"\t"+ city_profile["city"]
            
            profiles_hash[pref_city] = {
                "summary"           : city_profile["summary"],
                "build_year_summary": city_profile["build_year_summary"],
                "rating"            : city_profile["rating"] }

            for atri_key in ["家族世帯","家族世帯_変動"]:
                if atri_key in city_profile["summary"]:
                    profiles_hash[pref_city]["rating"][atri_key] = \
                        city_profile["summary"][atri_key]

            buy_new = 0
            if "入手_分譲" in city_profile["summary"] and \
               city_profile["summary"]["入手_分譲"]:
                buy_new = city_profile["summary"]["入手_分譲"]

            tmp_sum = 0
            for atri_key in ["入手_新築","入手_分譲","入手_建替"]:
                if not atri_key in city_profile["summary"]:
                    continue
                tmp_sum += city_profile["summary"][atri_key]

            if tmp_sum :
                profiles_hash[pref_city]["rating"]["buy_new_rate"] = \
                    round(buy_new/tmp_sum, 2)
            else:
                profiles_hash[pref_city]["rating"]["buy_new_rate"] = 0

        return profiles_hash

        
    def conv_ratings_to_list(self, profiles_hash):
        ret_datas = []

        for pref_city in profiles_hash.keys():
            (pref,city) = pref_city.split("\t")
            rating = profiles_hash[pref_city]["rating"]
            rating["pref"] = pref
            rating["city"] = city
            
            ret_data = {
                "pref" : pref,
                "city" : city,
                "rating":json.dumps(rating, ensure_ascii=False) }
            ret_datas.append( ret_data )

        return ret_datas
        

        
    def calc_sales_count_by_city(self, profiles_hash):
        newbuild_service = NewBuildService()
        sales_counts = newbuild_service.get_newest_sales_count_by_city()
        
        for sales_count in sales_counts:
            pref_city = sales_count["pref"] +"\t"+ sales_count["city"]

            if not pref_city in profiles_hash:
                continue

            profiles_hash[pref_city]["rating"]["discuss_days"] = 0
            if sales_count["discuss_days"]:
                profiles_hash[pref_city]["rating"]["discuss_days"] = \
                    round(10 / sales_count["discuss_days"],2)

            onsale_count = sales_count["onsale_count"]
            if not onsale_count:
                continue
            
            if not "sold_count" in profiles_hash[pref_city]["rating"]:
                continue
            
            sold_count = profiles_hash[pref_city]["rating"]["sold_count"]
            profiles_hash[pref_city]["rating"]["sold_onsale_count"] = \
                round(sold_count*10 / onsale_count,2)
        return profiles_hash

        
    def calc_fudousan_torihiki(self, profiles_hash):
        fudousan_torihiki_service = MlitFudousanTorihikiService()

        # 6ケ月前を基準に、年度の販売棟数を取得
        tmp_date = datetime.date.today() - datetime.timedelta(days=(30*6))
        pre_year = tmp_date.year
        if  1<=tmp_date.month and tmp_date.month<=3:
            pre_year -= 1

        year_q = [pre_year*10+1,pre_year*10+4]
        fudousan_torihikis = \
            fudousan_torihiki_service.get_city_sumed_summaries("newbuild",
                                                               year_q )
        for fudousan_torihiki in fudousan_torihikis:
            pref_city = fudousan_torihiki["pref"] +"\t"+ fudousan_torihiki["city"]

            if not pref_city in profiles_hash:
                continue

            sold_count = fudousan_torihiki["sold_count"]
            buy_new_rate = profiles_hash[pref_city]["rating"]["buy_new_rate"]

            profiles_hash[pref_city]["rating"]["sold_count"] = \
                round(sold_count * buy_new_rate,1)

            family_setai = profiles_hash[pref_city]["summary"]["家族世帯"]

            if family_setai:
                profiles_hash[pref_city]["rating"]["sold_family_setai"] = \
                    round(sold_count * 1000 / family_setai,2)
            else:
                profiles_hash[pref_city]["rating"]["sold_family_setai"] = 0

        return profiles_hash