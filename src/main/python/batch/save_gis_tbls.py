#!python3
# -*- coding: utf-8 -*-

import getopt
import os
import sys
sys.path.append( os.path.join(os.path.dirname(__file__), '../lib') )

from service.city       import CityService
from service.gis        import GisService
from service.googlemap  import GoogleMapService
from service.zipcode    import ZipcodeService
from util.db            import Db

target_year = 2019

def main():
    gis_service = GisService()
    util_db = Db()
    
    data_names = gis_service.get_data_names()
    for data_name in data_names:
        print(data_name)

        if data_name != 'gis_youto_chiiki':
            continue

        index_page_url = gis_service.get_index_page_url(data_name)
        print( index_page_url )
        
        data_urls = gis_service.find_data_urls(index_page_url)
        select_cond = gis_service.get_select_data_cond(data_name)
        select_cond["year"] = target_year
        
        for data_url in data_urls:
            #print(data_url)
            chk_result = gis_service.chk_select_cond(select_cond,data_url)
            
            if not chk_result:
                continue
            
            print(data_url)
            #continue

            sqls = gis_service.download_master(data_url["url"], data_name )

            for sql in sqls:
                result = gis_service.insert_master_tbl( sql["insert"] )
                print( result )
            
        
if __name__ == '__main__':
    main()
    