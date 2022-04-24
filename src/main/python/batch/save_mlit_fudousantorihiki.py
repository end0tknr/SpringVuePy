#!python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append( os.path.join(os.path.dirname(__file__), '../lib') )
from service.mlit_fudousantorihiki import MlitFudousanTorihikiService

master_xls = "b013.xls"
target_host = "http://www.e-stat.go.jp"

def main():
    fudosan_tochi_service = MlitFudousanTorihikiService()
    csv_infos = fudosan_tochi_service.download_master()
    print( csv_infos )
    
if __name__ == '__main__':
    main()
    
