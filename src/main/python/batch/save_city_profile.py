#!python3
# -*- coding: utf-8 -*-

import getopt
import os
import sys
sys.path.append( os.path.join(os.path.dirname(__file__), '../lib') )

from service.city_profile       import CityProfileService

def main():
    city_profile_service = CityProfileService()
    profiles = city_profile_service.calc_profiles()
    city_profile_service.save_profiles( profiles )

if __name__ == '__main__':
    main()
