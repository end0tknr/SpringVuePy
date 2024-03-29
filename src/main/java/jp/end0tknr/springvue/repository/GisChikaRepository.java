package jp.end0tknr.springvue.repository;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.SelectProvider;

import jp.end0tknr.springvue.entity.GisChikaEntity;
import jp.end0tknr.springvue.sql.GisChikaSqlProvider;

@Mapper
public interface GisChikaRepository {

    @SelectProvider(
            type=GisChikaSqlProvider.class,
            method="sqlFindByCoord" )
    List<GisChikaEntity> findByCoord(
    		@Param("coord") List<Double> coord);

}
