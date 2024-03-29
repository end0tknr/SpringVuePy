package jp.end0tknr.springvue.repository;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.SelectProvider;

import jp.end0tknr.springvue.entity.GisTochiRiyoShousaiEntity;
import jp.end0tknr.springvue.sql.GisTochiRiyoShousaiSqlProvider;

@Mapper
public interface GisTochiRiyoShousaiRepository {

    @SelectProvider(
            type=GisTochiRiyoShousaiSqlProvider.class,
            method="sqlFindByCoord" )
    List<GisTochiRiyoShousaiEntity> findByCoord(
    		@Param("coord") List<Double> coord);

}
