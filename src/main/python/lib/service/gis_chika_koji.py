#!python
# -*- coding: utf-8 -*-

from service.city      import CityService
import re
import service.gis

logger = None

youto_def = {
    # 最後の「_」も住居系に入れました
    "住居系":['1低専','2低専','1中専','2中専','1住居','2住居','準住居','_'],
    "商業系":['商業','近商'],
    "工業系":['工業','準工','工専']}

class GisChikaKojiService(service.gis.GisService):

    def __init__(self):
        global logger
        logger = self.get_logger()
        

    def modify_pref_cities(self):
        logger.info("start")
        
        city_service = CityService()
        org_datas = self.get_pref_cities_for_modiry()
        for org_data in org_datas:
            new_data = city_service.parse_pref_city(org_data["org_address"])
            self.save_pref_cities(org_data["gid"],new_data[0],new_data[1])
            
    def save_pref_cities(self,gid,pref,city):
        sql = """
UPDATE gis_chika_koji
SET pref=%s, city=%s
WHERE gid=%s
"""
        sql_args = (pref,city,gid)
        with self.db_connect() as db_conn:
            with self.db_cursor(db_conn) as db_cur:
                try:
                    db_cur.execute(sql,sql_args)
                except Exception as e:
                    logger.error(e)
                    logger.error(sql)
                    return False
        return True

            
    def get_pref_cities_for_modify(self):

        sql = """
SELECT
  gid,
  l01_023 as org_address
FROM gis_chika_koji
WHERE pref is null or city is null;
"""
        ret_data = []
        
        with self.db_connect() as db_conn:
            with self.db_cursor(db_conn) as db_cur:
                try:
                    db_cur.execute(sql)
                except Exception as e:
                    logger.error(e)
                    logger.error(sql)
                    return []
                
                for ret_row in  db_cur.fetchall():
                    ret_row = dict( ret_row )
                    ret_row["org_address"] = \
                        ret_row["org_address"].replace("　","").replace(" ","")
                    ret_data.append( ret_row )
                
        return ret_data
    
    def get_youto_group(self,org_youto):

        for youto_group, youtos in youto_def.items():
            if org_youto in youtos:
                return youto_group
        return "?"
    
        
    def get_union_vals(self):
        sql = """
select
  pref, city, l01_047 as youto,
  l01_006::integer as price
from gis_chika_koji
union
  select
    pref,city,l02_046 as youto,
    l02_006 as price
  from gis_chika
"""
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

                pref_city = "\t".join([ret_row["pref"], ret_row["city"]])
                if not pref_city in ret_data_tmp:
                    ret_data_tmp[pref_city] = {}

                youto = ret_row["youto"]
                youto_group = self.get_youto_group(youto)
                
                if not youto in ret_data_tmp[pref_city]:
                    ret_data_tmp[pref_city][youto] = {"price":0,"count":0}
                    
                ret_data_tmp[pref_city][youto]["price"] += ret_row["price"]
                ret_data_tmp[pref_city][youto]["count"] += 1

                if not youto_group in ret_data_tmp[pref_city]:
                    ret_data_tmp[pref_city][youto_group] = {"price":0,"count":0}

                ret_data_tmp[pref_city][youto_group]["price"] += ret_row["price"]
                ret_data_tmp[pref_city][youto_group]["count"] += 1

        ret_datas = []
        for pref_city_str,youto_groups in ret_data_tmp.items():
            pref_city = pref_city_str.split("\t")
            ret_data = {"pref":pref_city[0], "city":pref_city[1]}
            
            for youto_group, vals in youto_groups.items():
                ret_data[youto_group] = int( vals["price"] / vals["count"] )
                
            ret_datas.append(ret_data)
            
        return ret_datas

    def find_by_lnglat(self,lng,lat,youto_group):
        
        if (not lng and not lat):
            logger.warning("lng lat is null")
            return {}

        
        sql ="""
SELECT
  gck.pref, gck.city, gck.l01_047 as youto,
  gck.l01_006::integer as price,
  gck.lng, gck.lat,
  gck.l01_045 as station,
  gck.l01_046::int as from_station,
  ST_Distance(gck.geom,ST_PointFromText('POINT(%s %s)') )  AS st_distance
FROM gis_chika_koji gck
WHERE  gck.lng BETWEEN (%s - %s) AND (%s + %s) AND
       gck.lat BETWEEN (%s - %s) AND (%s + %s) AND
       l01_047 in %s
UNION
  SELECT
    gc.pref,gc.city,gc.l02_046 as youto,
    gc.l02_006 as price,
    gc.lng, gc.lat,
    gc.l02_044 as station,
    gc.l02_045 as from_station,
    ST_Distance(gc.geom,ST_PointFromText('POINT(%s %s)') )  AS st_distance
  FROM gis_chika gc
  WHERE gc.lng BETWEEN (%s - %s) AND (%s + %s) AND
        gc.lat BETWEEN (%s - %s) AND (%s + %s) AND
       l02_046 in %s
ORDER BY st_distance
LIMIT 1;
"""
        limit_deg  = 0.01
        sql_args  = (lng, lat,
                     lng, limit_deg, lng, limit_deg,
                     lat, limit_deg, lat, limit_deg,
                     tuple(youto_def[youto_group]),
                     lng, lat,
                     lng, limit_deg, lng, limit_deg,
                     lat, limit_deg, lat, limit_deg,
                     tuple(youto_def[youto_group]) )
        db_conn = self.db_connect()
        ret_data = {}
        with self.db_cursor(db_conn) as db_cur:
            try:
                db_cur.execute(sql,sql_args)
            except Exception as e:
                logger.error(e)
                logger.error(sql)
                return {}

            ret_rows =  db_cur.fetchall()
            if len(ret_rows) == 0:
                return {}

            ret_row = dict( ret_rows[0] )
            ret_row["st_distance"] = round(ret_row["st_distance"], 4)
            return ret_row
