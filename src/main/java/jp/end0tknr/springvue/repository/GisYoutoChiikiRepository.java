package jp.end0tknr.springvue.repository;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.SelectProvider;

import jp.end0tknr.springvue.entity.GisYoutoChiikiEntity;
import jp.end0tknr.springvue.sql.GisYoutoChiikiSqlProvider;

@Mapper
public interface GisYoutoChiikiRepository {

    @SelectProvider(
            type=GisYoutoChiikiSqlProvider.class,
            method="sqlFindByCoord" )
    List<GisYoutoChiikiEntity> findByCoord(
    		@Param("coord") List<Double> coord);

}
