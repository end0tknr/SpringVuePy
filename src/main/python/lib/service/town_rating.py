#!python
# -*- coding: utf-8 -*-

from service.city_profile           import CityProfileService
from service.kokusei_population_h06 import KokuseiPopulationH06Service
from service.mlit_fudousantorihiki  import MlitFudousanTorihikiService
from service.newbuild               import NewBuildService
from service.town                   import TownService
from util.db import Db
import appbase
import datetime
import json
import numpy as np

logger = appbase.AppBase().get_logger()

class TownRatingService(TownService):
    
    def __init__(self):
        pass

    def calc_save_ratings_2(self):
        profiles_hash = self.calc_town_profiles()
        profiles_hash = self.calc_city_profiles( profiles_hash )
        profiles_hash = self.calc_kokusei_population( profiles_hash )
        profiles_hash = self.calc_fudousan_torihiki_2( profiles_hash )
        profiles_hash = self.calc_sales_count_by_town_2( profiles_hash )
        profiles_hash = self.calc_sales_count_by_shop_2( profiles_hash )
        
        profiles_list = self.conv_ratings_to_list(profiles_hash)
        
        util_db = Db()
        util_db.bulk_update("town_profile",
                            ["pref","city","town"],
                            ["pref","city","town","rating"],
                            profiles_list )
        
    def calc_save_ratings(self):
        profiles_hash = self.calc_town_profiles()
        profiles_hash = self.calc_city_profiles( profiles_hash )
        profiles_hash = self.calc_kokusei_population( profiles_hash )
        profiles_hash = self.calc_fudousan_torihiki( profiles_hash )
        profiles_hash = self.calc_sales_count_by_town( profiles_hash )
        profiles_hash = self.calc_sales_count_by_shop( profiles_hash )

        profiles_list = self.conv_ratings_to_list(profiles_hash)
        
        util_db = Db()
        util_db.bulk_update("town_profile",
                            ["pref","city","town"],
                            ["pref","city","town","rating"],
                            profiles_list )


    def conv_ratings_to_list(self, profiles_hash):
        ret_datas = []

        for pref_city_town in profiles_hash.keys():
            (pref,city,town) = pref_city_town.split("\t")
            rating = profiles_hash[pref_city_town]["rating"]
            rating["pref"] = pref
            rating["city"] = city
            rating["town"] = town
            
            ret_data = {
                "pref" : pref,
                "city" : city,
                "town" : town,
                "rating":json.dumps(rating, ensure_ascii=False) }
            ret_datas.append( ret_data )

        return ret_datas
    
    def calc_fudousan_torihiki_2(self, profiles_hash):
        fudousan_torihiki_service = MlitFudousanTorihikiService()
        
        # 6ケ月前を基準に、年度の販売棟数を取得
        tmp_date = datetime.date.today() - datetime.timedelta(days=(30*6))
        pre_year = tmp_date.year
        if  1<=tmp_date.month and tmp_date.month<=3:
            pre_year -= 1

        years = [pre_year-1, pre_year]
        fudousan_torihikis = \
            fudousan_torihiki_service.get_town_years("newbuild",years )
        # 差値算出用
        sold_counts = []

        for fudousan_torihiki in fudousan_torihikis:
            pref_city_town = "\t".join([fudousan_torihiki["pref"],
                                        fudousan_torihiki["city"],
                                        fudousan_torihiki["town"] ])

            if not pref_city_town in profiles_hash:
                continue

            buy_new_rate = 0
            if "buy_new_rate" in profiles_hash[pref_city_town]["rating"]:
                buy_new_rate = \
                    profiles_hash[pref_city_town]["rating"]["buy_new_rate"]

            count_new = "sold_count_" + str(years[1])
            price_new = "sold_price_" + str(years[1])
            count_pre = "sold_count_" + str(years[0])

            profiles_hash[pref_city_town]["rating"]["sold_count"] = 0
            if count_new in fudousan_torihiki:
                profiles_hash[pref_city_town]["rating"]["sold_count"] = \
                    round(fudousan_torihiki[count_new] * buy_new_rate,1)

            profiles_hash[pref_city_town]["rating"]["sold_price"] = 0
            if price_new in fudousan_torihiki:
                profiles_hash[pref_city_town]["rating"]["sold_price"] = \
                    round(fudousan_torihiki[price_new] / 1000000)
                
            if count_pre in fudousan_torihiki:
                profiles_hash[pref_city_town]["rating"]["sold_count_diff"] = \
                    profiles_hash[pref_city_town]["rating"]["sold_count"] - \
                    fudousan_torihiki[count_pre] * buy_new_rate
                profiles_hash[pref_city_town]["rating"]["sold_count_diff"] = \
                    round(
                        profiles_hash[pref_city_town]["rating"]["sold_count_diff"],
                        1 )

            family_setai = 0
            if not "家族世帯" in profiles_hash[pref_city_town]["rating"] or \
               not profiles_hash[pref_city_town]["rating"]["家族世帯"]:
                continue
                
            # 以下の 1000は、標準偏差算出で桁溢れ?を防ぐ為のものです
            sold_counts.append(
                profiles_hash[pref_city_town]["rating"]["sold_count"] * 1000 / \
                profiles_hash[pref_city_town]["rating"]["家族世帯"] )
                
        np_scores = np.array( sold_counts )
        tmp_mean = np.mean(np_scores)   # 平均
        tmp_std = np.std( sold_counts ) # 標準偏差
        
        for pref_city_town, profile_tmp in profiles_hash.items():
            if not "sold_count" in profile_tmp["rating"] or \
               not "家族世帯" in profile_tmp["rating"] or \
               not profile_tmp["rating"]["家族世帯"] :
                continue
            
            # 以下の 1000は、標準偏差算出で桁溢れ?を防ぐ為のものです
            tmp_count = \
                profile_tmp["rating"]["sold_count"] * 1000 / \
                profile_tmp["rating"]["家族世帯"]
            # 偏差値算出
            profile_tmp["rating"]["ss_sold_count"] = \
                round( (tmp_count - tmp_mean) / tmp_std * 10 + 50 )
    
        return profiles_hash


    def calc_fudousan_torihiki(self, profiles_hash):
        fudousan_torihiki_service = MlitFudousanTorihikiService()
        
        # 6ケ月前を基準に、年度の販売棟数を取得
        tmp_date = datetime.date.today() - datetime.timedelta(days=(30*6))
        pre_year = tmp_date.year
        if  1<=tmp_date.month and tmp_date.month<=3:
            pre_year -= 1

        years = [pre_year-1, pre_year]
        fudousan_torihikis = \
            fudousan_torihiki_service.get_town_years("newbuild",years )
        for fudousan_torihiki in fudousan_torihikis:
            pref_city_town = "\t".join([fudousan_torihiki["pref"],
                                        fudousan_torihiki["city"],
                                        fudousan_torihiki["town"] ])

            if not pref_city_town in profiles_hash:
                continue

            buy_new_rate = 0
            if "buy_new_rate" in profiles_hash[pref_city_town]["rating"]:
                buy_new_rate = \
                    profiles_hash[pref_city_town]["rating"]["buy_new_rate"]

            count_new = "sold_count_" + str(years[1])
            price_new = "sold_price_" + str(years[1])
            count_pre = "sold_count_" + str(years[0])

            profiles_hash[pref_city_town]["rating"]["sold_count"] = 0
            if count_new in fudousan_torihiki:
                profiles_hash[pref_city_town]["rating"]["sold_count"] = \
                    round(fudousan_torihiki[count_new] * buy_new_rate,1)

            profiles_hash[pref_city_town]["rating"]["sold_price"] = 0
            if price_new in fudousan_torihiki:
                profiles_hash[pref_city_town]["rating"]["sold_price"] = \
                    round(fudousan_torihiki[price_new] / 1000000)
                
            if count_pre in fudousan_torihiki:
                profiles_hash[pref_city_town]["rating"]["sold_count_diff"] = \
                    profiles_hash[pref_city_town]["rating"]["sold_count"] - \
                    fudousan_torihiki[count_pre] * buy_new_rate
                profiles_hash[pref_city_town]["rating"]["sold_count_diff"] = \
                    round(
                        profiles_hash[pref_city_town]["rating"]["sold_count_diff"],
                        1 )

            sold_count   = profiles_hash[pref_city_town]["rating"]["sold_count"]
            family_setai = 0
            if "家族世帯" in profiles_hash[pref_city_town]["rating"]:
                family_setai = profiles_hash[pref_city_town]["rating"]["家族世帯"]
                
            profiles_hash[pref_city_town]["rating"]["sold_family_setai"] = 0
            if family_setai:
                profiles_hash[pref_city_town]["rating"]["sold_family_setai"] = \
                    round(sold_count * 1000 / family_setai,2)
                
        return profiles_hash


    def calc_kokusei_population(self, profiles_hash):
        kokusei_population_service = KokuseiPopulationH06Service()
        setai_infos = kokusei_population_service.get_all_2020_2015()

        for setai_info in setai_infos:
            pref_city_town = "\t".join([ setai_info["pref"],
                                         setai_info["city"],
                                         setai_info["town"] ])
            if not pref_city_town in profiles_hash:
                continue
            
            profiles_hash[pref_city_town]["rating"]["家族世帯"] = \
                setai_info["family_setai"]
            profiles_hash[pref_city_town]["rating"]["家族世帯_変動"] = \
                setai_info["family_setai"] - setai_info["family_setai_2015"]

        return profiles_hash
             
    def calc_city_profiles(self, profiles_hash):
        city_profile_service = CityProfileService()
        city_profiles = city_profile_service.get_all()

        city_profiles_hash = {}
        for city_profile in city_profiles:
            pref_city = city_profile["pref"] +"\t"+ city_profile["city"]

            city_profiles_hash[pref_city] = {
                "summary"           : city_profile["summary"],
                "build_year_summary": city_profile["build_year_summary"],
                "rating"            : city_profile["rating"] }

        for pref_city_town in profiles_hash:
            (pref,city,town) = pref_city_town.split("\t")
            pref_city = pref +"\t"+ city

            if pref_city in city_profiles_hash and \
               "rating"  in city_profiles_hash[pref_city]:

                if "buy_new_rate" in city_profiles_hash[pref_city]["rating"]:
                    profiles_hash[pref_city_town]["rating"]["buy_new_rate"] = \
                        city_profiles_hash[pref_city]["rating"]["buy_new_rate"]
                if "kodate_rate" in city_profiles_hash[pref_city]["rating"]:
                    profiles_hash[pref_city_town]["rating"]["kodate_rate"] = \
                        city_profiles_hash[pref_city]["rating"]["kodate_rate"]
                
        return profiles_hash
                
        
    def calc_town_profiles(self):
        town_service = TownService()
        town_profiles = town_service.get_all()
 
        profiles_hash = {}
        for town_profile in town_profiles:
            pref_city_town = "\t".join([town_profile["pref"],
                                        town_profile["city"],
                                        town_profile["town"] ])

            profiles_hash[pref_city_town] = {
                "summary":town_profile["summary"], "rating":{"land_price":0} }

            if "price" in profiles_hash[pref_city_town]["summary"]:
                profiles_hash[pref_city_town]["rating"]["land_price"] = \
                    round(profiles_hash[pref_city_town]["summary"]["price"] / 10000)
            
        return profiles_hash


    def calc_sales_count_by_town_2(self, profiles_hash):
        newbuild_service = NewBuildService()
        sales_counts = newbuild_service.get_newest_sales_count_by_town()
        # 差値算出用
        standard_score ={
            "discuss_days":{"scores":[],"no_scores":[],"mean":None,"std":None},
            "onsale_count":{"scores":[],"no_scores":[],"mean":None,"std":None} }
        
        for sales_count in sales_counts:
            pref_city_town = "\t".join([ sales_count["pref"],
                                         sales_count["city"],
                                         sales_count["town"] ])
            if not pref_city_town in profiles_hash:
                continue
            
            if not "sold_count" in profiles_hash[pref_city_town]["rating"]:
                continue
            sold_count = profiles_hash[pref_city_town]["rating"]["sold_count"]

            for atri_key in ["discuss_days","onsale_count"]:
                profiles_hash[pref_city_town]["rating"][atri_key] = \
                    sales_count[atri_key]
                
                if atri_key in ["onsale_count"]:
                    if sales_count[atri_key]:
                        standard_score[atri_key]["scores"].append(
                            sold_count / sales_count[atri_key] )
                else:
                    standard_score[atri_key]["scores"].append(
                        sales_count[atri_key] )

        for atri_key,ss_score in standard_score.items():
            ss_score["np_scores"] = np.array( ss_score["scores"] )
            ss_score["mean"] = np.mean(ss_score["np_scores"] ) # 平均
            ss_score["std"]  = np.std( ss_score["np_scores"] ) # 標準偏差

        for pref_city, profile_tmp in profiles_hash.items():

            if not "sold_count" in profiles_hash[pref_city]["rating"]:
                continue
            sold_count = profiles_hash[pref_city]["rating"]["sold_count"]
            
            for atri_key,ss_score in standard_score.items():
                if not atri_key in profile_tmp["rating"]:
                    continue
                tmp_mean  = ss_score["mean"]
                tmp_std   = ss_score["std"]
                tmp_count = profile_tmp["rating"][atri_key]
                if not tmp_count:
                    continue

                if atri_key in ["onsale_count"]:
                    tmp_count = sold_count / tmp_count
                
                # 偏差値算出
                profile_tmp["rating"]["ss_"+atri_key] = \
                    round( (tmp_count - tmp_mean) / tmp_std * 10 + 50 )
                    
        return profiles_hash


    def calc_sales_count_by_town(self, profiles_hash):
        newbuild_service = NewBuildService()
        sales_counts = newbuild_service.get_newest_sales_count_by_town()
        
        for sales_count in sales_counts:
            pref_city_town = "\t".join([ sales_count["pref"],
                                         sales_count["city"],
                                         sales_count["town"] ])
            if not pref_city_town in profiles_hash:
                continue

            profiles_hash[pref_city_town]["rating"]["discuss_days"] = 0
            if sales_count["discuss_days"]:
                profiles_hash[pref_city_town]["rating"]["discuss_days"] = \
                    round(10 / sales_count["discuss_days"],2)

            onsale_count = sales_count["onsale_count"]
            if not onsale_count:
                continue
            
            if not "sold_count" in profiles_hash[pref_city_town]["rating"]:
                continue
            
            sold_count = profiles_hash[pref_city_town]["rating"]["sold_count"]
            profiles_hash[pref_city_town]["rating"]["sold_onsale_count"] = \
                round(sold_count*10 / onsale_count,2)
        return profiles_hash


    def calc_sales_count_by_shop(self, profiles_hash):
        newbuild_service = NewBuildService()
        sales_counts = newbuild_service.get_newest_sales_count_by_shop_town()
        
        for sales_count in sales_counts:
            pref_city = "\t".join([ sales_count["pref"],
                                    sales_count["city"],
                                    sales_count["town"] ])

            if not pref_city in profiles_hash:
                continue

            if not "sold_count" in profiles_hash[pref_city]["rating"]:
                continue
            
            sold_count = profiles_hash[pref_city]["rating"]["sold_count"]
            profiles_hash[pref_city]["rating"]["onsale_shop"] = sales_count["shop"]
            
            profiles_hash[pref_city]["rating"]["sold_onsale_shop"] = \
                round(sold_count*5 / sales_count["shop"], 2)
        return profiles_hash

    
    def calc_sales_count_by_shop_2(self, profiles_hash):
        newbuild_service = NewBuildService()
        sales_counts = newbuild_service.get_newest_sales_count_by_shop_town()
        # 差値算出用
        standard_score ={
            "onsale_shop":{"scores":[],"no_scores":[],"mean":None,"std":None} }
        
        for sales_count in sales_counts:
            pref_city = "\t".join([ sales_count["pref"],
                                    sales_count["city"],
                                    sales_count["town"] ])

            if not pref_city in profiles_hash:
                continue

            if not "sold_count" in profiles_hash[pref_city]["rating"]:
                continue
            
            sold_count = profiles_hash[pref_city]["rating"]["sold_count"]
            profiles_hash[pref_city]["rating"]["onsale_shop"] = sales_count["shop"]
            
            for atri_key,ss_score in standard_score.items():
                ss_score["scores"].append(
                    sold_count/profiles_hash[pref_city]["rating"]["onsale_shop"])

            for atri_key,ss_score in standard_score.items():
                ss_score["np_scores"] = np.array( ss_score["scores"] )
                ss_score["mean"] = np.mean(ss_score["np_scores"] ) # 平均
                ss_score["std"]  = np.std( ss_score["np_scores"] ) # 標準偏差

        for pref_city, profile_tmp in profiles_hash.items():

            if not "sold_count" in profiles_hash[pref_city]["rating"]:
                continue
            sold_count = profiles_hash[pref_city]["rating"]["sold_count"]
            
            for atri_key,ss_score in standard_score.items():
                if not atri_key in profile_tmp["rating"]:
                    continue
                tmp_mean  = ss_score["mean"]
                tmp_std   = ss_score["std"]
                tmp_count = sold_count / profile_tmp["rating"][atri_key]
                
                # 偏差値算出
                profile_tmp["rating"]["ss_"+atri_key] = \
                    round( (tmp_count - tmp_mean) / tmp_std * 10 + 50 )

        return profiles_hash

    
