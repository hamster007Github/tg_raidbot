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
    def __init__(self, host, db_name, username, password, port=3306):
        self._db_connection = None
        self._host = host
        self._port = port
        self._db_name = db_name
        self._username = username
        self._password = password

    def __del__(self):
        self._disconnect()

    def _connect(self):
        try:
            # only create new connection, if not already a connection was created before
            if self._db_connection is None:
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
            self._db_connection.close()
            self._db_connection = None

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
    def __init__(self, db_host, db_port, db_name, db_username, db_password):
        self._dbconnector = DbConnector(host=db_host, port=db_port, db_name=db_name, username=db_username, password=db_password)

    def __del__(self):
        del self._dbconnector

    def get_raids(self, raidlevel_list, unknown_raids:bool = True, geofence: str = None):
        if geofence is not None:
            sql_geofence = f"AND ST_CONTAINS(st_geomfromtext('POLYGON(({geofence}))') , point(lat,lon))"
        else:
            # if no geofence provided: get all raids from DB without area limitation
            sql_geofence = ""
        if not unknown_raids:
            # if unknown_raids == True: provide only "hatched" raids, where raidpokemon is known (pokemon_id != 0)
            sql_unknown_raids = "AND raid_pokemon_id <> 0"
        else:
            sql_unknown_raids = ""
        raidlevel_str = ','.join([str(x) for x in raidlevel_list])
        sql_query = f"SELECT name AS gym_name, raid_level, raid_pokemon_id, raid_battle_timestamp, raid_end_timestamp, raid_pokemon_move_1 AS atk_fast, raid_pokemon_move_2 AS atk_charge, lat, lon FROM gym WHERE UNIX_TIMESTAMP() < raid_end_timestamp AND raid_level IN ({raidlevel_str}) {sql_geofence} {sql_unknown_raids} ORDER BY raid_spawn_timestamp;"
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