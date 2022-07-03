package jp.end0tknr.springvue.controller;

import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jp.end0tknr.springvue.entity.NewBuildSalesCountByCity;
import jp.end0tknr.springvue.entity.NewBuildSalesCountByPrice;
import jp.end0tknr.springvue.entity.NewBuildSalesCountByShop;
import jp.end0tknr.springvue.entity.NewBuildSalesCountByShopCity;
import jp.end0tknr.springvue.entity.NewBuildSalesCountByTown;
import jp.end0tknr.springvue.service.CityProfileService;
import jp.end0tknr.springvue.service.NewBuildService;

@RestController
@CrossOrigin
public class NewBuildRestController {

    @Autowired
    NewBuildService newBuildService;
    @Autowired
    CityProfileService cityProfileService;

    List<String> convStr2CalcDate(String dateStr) {
        SimpleDateFormat sdFormat = new SimpleDateFormat("yyyy-MM-dd");
        Date dateFrom = new Date();
		try {
	    	if(dateStr != null) {
	    		dateFrom = sdFormat.parse(dateStr);
	    	}
		} catch (ParseException e) {
			//e.printStackTrace();
		}

        Calendar calendar = Calendar.getInstance();
        calendar.setTime(dateFrom);
        calendar.add(Calendar.DAY_OF_MONTH, 6);
        Date dateTo = calendar.getTime();

        return Arrays.asList(
        		sdFormat.format(dateFrom),
        		sdFormat.format(dateTo) );
    }

    @RequestMapping("/api/newbuild/SalesCountByShop/{prefName}")
    public List<NewBuildSalesCountByShop> salesCountByShop(
    		@PathVariable("prefName") String prefName,
    		@RequestParam(value="date", required=false) String calcDateStr ){

    	List<String> calcDate = convStr2CalcDate(calcDateStr);

    	try {
			prefName = URLDecoder.decode(prefName, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
    	return newBuildService.getSalesCountByShop(
    			prefName,calcDate.get(0),calcDate.get(1) );
    }

    @RequestMapping("/api/newbuild/SalesCountByShopCity/{prefCityName}")
    public List<NewBuildSalesCountByShopCity> salesCountByShopCity(
    		@PathVariable("prefCityName") String prefCityName,
    		@RequestParam(value="date", required=false) String calcDateStr  ){

    	List<String> calcDate = convStr2CalcDate(calcDateStr);

    	try {
			prefCityName = URLDecoder.decode(prefCityName, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
    	String[] names = prefCityName.split("_");
    	return newBuildService.getSalesCountByShopCity(
    			names[0],names[1],calcDate.get(0),calcDate.get(1) );
    }

    @RequestMapping("/api/newbuild/SalesCountByCity/{prefName}")
    public List<NewBuildSalesCountByCity> salesCountByCity(
    		@PathVariable("prefName") String prefName,
    		@RequestParam(value="date", required=false) String calcDateStr  ){

    	List<String> calcDate = convStr2CalcDate(calcDateStr);

    	try {
			prefName = URLDecoder.decode(prefName, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
    	return newBuildService.getSalesCountByCity(
    			prefName,calcDate.get(0),calcDate.get(1) );
    }

    @RequestMapping("/api/newbuild/SalesCountByNearCity/{prefCityName}")
    public List<NewBuildSalesCountByCity> salesCountByNearCity(
    		@PathVariable("prefCityName") String prefCityName,
    		@RequestParam(value="date", required=false) String calcDateStr ){

    	List<String> calcDate = convStr2CalcDate(calcDateStr);

    	try {
    		prefCityName = URLDecoder.decode(prefCityName, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
    	String[] names = prefCityName.split("_");
    	return newBuildService.getSalesCountByNearCity(
    			names[0],names[1],calcDate.get(0),calcDate.get(1) );
    }

    @RequestMapping("/api/newbuild/SalesCountByTown/{prefCityName}")
    public List<NewBuildSalesCountByTown> salesCountByTown(
    		@PathVariable("prefCityName") String prefCityName,
    		@RequestParam(value="date", required=false) String calcDateStr ){

    	List<String> calcDate = convStr2CalcDate(calcDateStr);

    	try {
    		prefCityName = URLDecoder.decode(prefCityName, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}

    	String[] names = prefCityName.split("_");
    	return newBuildService.getSalesCountByTown(
    			names[0],names[1],calcDate.get(0),calcDate.get(1) );
    }

    @RequestMapping("/api/newbuild/SalesCountByPrice/{prefCityName}")
    public List<NewBuildSalesCountByPrice> salesCountByPrice(
    		@PathVariable("prefCityName") String prefCityName,
    		@RequestParam(value="date", required=false) String calcDateStr ){

    	List<String> calcDate = convStr2CalcDate(calcDateStr);

    	try {
    		prefCityName = URLDecoder.decode(prefCityName, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}

    	String[] names = prefCityName.split("_");
    	return newBuildService.getSalesCountByPrice(
    			names[0],names[1],calcDate.get(0),calcDate.get(1) );
    }

    @RequestMapping("/api/newbuild/CityProfile/{prefCityName}")
    public String cityProfile(
    		@PathVariable("prefCityName") String prefCityName ){

    	try {
			prefCityName = URLDecoder.decode(prefCityName, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
    	String[] names = prefCityName.split("_");

    	String cityProfile = cityProfileService.getCityProfile(names[0],names[1]);

    	return cityProfile;
    }

    @RequestMapping("/api/newbuild/NearCityProfiles/{prefCityName}")
    public List<String> nearCityProfiles (
    		@PathVariable("prefCityName") String prefCityName ){

    	try {
			prefCityName = URLDecoder.decode(prefCityName, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
    	String[] names = prefCityName.split("_");

    	List<String> cityProfile =
    			cityProfileService.getNearCityProfiles(
    					names[0],names[1] );
    	return cityProfile;
    }


}