#!/usr/local/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
* Import
****************************************
'''
# MYSQL database connection
import mysql.connector
from mysql.connector import Error
# logging
import logging

'''
****************************************
* Global variables
****************************************
'''
log = logging.getLogger(__name__)

'''
****************************************
* Classes
****************************************
'''

#****************************************
# Class: DbConnector
#****************************************
class DbConnector():
    def __init__(self, host:str, db_name:str, username:str, password:str, port:int=3306):
        self._db_connection = None
        self._host = host
        self._port = port
        self._db_name = db_name
        self._username = username
        self._password = password

    def __del__(self):
        log.debug("DbConnector: __del__")
        self._disconnect()

    def _connect(self):
        try:
            # only create new connection, if not already a connection is available
            if self._db_connection is None or not self._db_connection.is_connected():
                self._db_connection = mysql.connector.connect(
                    host = self._host,
                    port = self._port,
                    user = self._username,
                    passwd = self._password,
                    database = self._db_name
                )
                log.debug(f"DbConnector: SQL db connected successfully")
        except Error as e:
            log.error("DbConnector: SQL connection error.")
            log.exception("Exception info:")
        return self._db_connection

    def _disconnect(self):
        if self._db_connection is not None:
            log.debug("DbConnector: disconnect")
            self._db_connection.close()

    def execute_query(self, query, commit=False, disconnect=True):
        result = None
        try:
            connection = self._connect()
            cursor = connection.cursor(dictionary=True)
            log.debug(f"DbConnector: SQL query '{query}'...")
            cursor.execute(query)
            if commit:
                result = connection.commit()
            else:
                result = cursor.fetchall()
            if disconnect:
                self._disconnect()
            cursor.close()
            log.debug(f"DbConnector: SQL query successfully executed")
            log.debug(f"DbConnector: SQL query result: {result}")
        except Error as e:
            log.error("DbConnector: SQL query error.")
            log.exception("Exception info:")
            self._disconnect()
            return None

        return result

#****************************************
# Class: RdmConnector
#****************************************
class RdmConnector():
    def __init__(self, db_host:str, db_port:int, db_name:str, db_username:str, db_password:str):
        self._dbconnector = DbConnector(host=db_host, port=db_port, db_name=db_name, username=db_username, password=db_password)

    def __del__(self):
        del self._dbconnector

    def get_raids(self, raidlevel_list, unknown_raids:bool = True, geofence:str = None, order_time_reverse:bool = False):
        sql_order = "DESC" if order_time_reverse else "ASC"
        sql_geofence = "" if geofence is None else f"AND ST_CONTAINS(st_geomfromtext('POLYGON(({geofence}))') , point(lat,lon))"
        sql_unknown_raids = "" if unknown_raids else "AND raid_pokemon_id <> 0"
        raidlevel_str = ','.join([str(raidlevel) for raidlevel in raidlevel_list])

        sql_query = f"SELECT name AS gym_name, raid_level, raid_pokemon_id, raid_battle_timestamp, raid_end_timestamp, raid_pokemon_move_1 AS atk_fast, raid_pokemon_move_2 AS atk_charge, lat, lon FROM gym WHERE UNIX_TIMESTAMP() < raid_end_timestamp AND raid_level IN ({raidlevel_str}) {sql_geofence} {sql_unknown_raids} ORDER BY raid_spawn_timestamp {sql_order};"
        dbreturn = self._dbconnector.execute_query(sql_query)
        return dbreturn

'''
#****************************************
# Class: MadConnector
#****************************************
class MadConnector():
    def __init__(self, db_host, db_port, db_name, db_username, db_password):
        self._dbconnector = DbConnector(host=db_host, port=db_port, db_name=db_name, username=db_username, password=db_password)

    def __del__(self):
        del self._dbconnector

    def get_raids(self, raidlevel_list, unknown_raids:bool = True, geofence: str = None):
        #@TODO: add MAD support
        pass;
'''