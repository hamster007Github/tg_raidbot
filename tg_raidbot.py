#!/usr/local/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
* Import
****************************************
'''
# time handling
import time
from datetime import datetime, timedelta
# os functions (path, ...)
import os
#import sys
# other
from string import Template
# .ini config parser and datacache
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import json
# logging
import logging
# tg_raidbot modules
from pogodata import Pogodata
from simpletelegramapi import SimpleTelegramApi
from scannerconnector import RdmConnector

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
# Class: RaidChannel
#****************************************
class RaidChannel():
    def __init__(self, chat_id:str, raidlevel_list:int, eggs:bool, raidlevel_grouping:bool = False, geofence:str = None):
        self.chat_id = chat_id
        self.raidlevel_list = raidlevel_list
        self.eggs = eggs
        self.raidlevel_grouping = raidlevel_grouping
        self.geofence = geofence

    def get_geofence(self) -> str:
        '''
        if self.geofence_name is not None and self._geofence is None:
            #get geofence coodinates
            #@TODO: koji support
            pass
        '''
        return self.geofence

#****************************************
# Class: TelegramRaidbot
#****************************************
class TelegramRaidbot():
    def __init__(self):
        self._rootdir = os.path.dirname(os.path.abspath(__file__))
        self.raidchannel_list = []
        self._msgid_cache = {}
        self._load_msgid_cache()
        if not self._load_config_parameter(self._rootdir + "/config.toml"):
            return 2

    def _load_config_parameter(self, filepath:str) -> bool:
        # load configuration from toml configuration file
        try:
            with open(filepath, "rb") as f:
                config = tomllib.load(f)
            log.info(f"config: {config}")
        except Exception as e:
            log.error("exception during _load_config_parameter() load tomlfile")
            log.exception(e)
            return False

        try:
            # general setting
            cfg_general = config.get("general")
            self._sleep_mainloop_in_s = cfg_general["raidupdate_cycle_in_s"]
            self._pogodata_update_cycle_in_s = cfg_general["pogodata_update_cycle_in_h"] * 3600
            self._cfg_api_token = cfg_general["token"]
            if self._cfg_api_token is None:
                log.error("no 'token' found in config file")
                return False
            # section [db]: database setting
            cfg_db = config.get("db")
            self._cfg_db_host = cfg_db["host"]
            self._cfg_db_port = cfg_db["port"]
            self._cfg_db_name = cfg_db["name"]
            self._cfg_db_user = cfg_db["user"]
            self._cfg_db_password = cfg_db["password"]
            # section [format]
            cfg_format = config.get("format")
            self._cfg_format_language = cfg_format["language"]
            self._cfg_format_max_gymname_len = cfg_format["max_gymname_len"]
            self._cfg_format_time = cfg_format["time_format"]
            # section [template]
            cfg_templates = config.get("templates")
            self._cfg_format_no_raids_msg = cfg_templates["tmpl_no_raid_msg"]
            self._cfg_tmpl_grouped_title_msg = Template(cfg_templates["tmpl_grouped_title_msg"])
            self._cfg_tmpl_raid_msg = Template(cfg_templates["tmpl_raid_msg"])
            self._cfg_tmpl_raidegg_msg = Template(cfg_templates["tmpl_raidegg_msg"])
            # section [raidconfig]
            cfg_raidconfig_array = config.get("raidconfig")
            for raidconfig in cfg_raidconfig_array:
                chat_id = raidconfig['chat_id']
                raidlevel_list = raidconfig['raidlevel']
                eggs = raidconfig['eggs']
                raidlevel_grouping = raidconfig['raidlevel_grouping']
                if 'geofence' in raidconfig.keys():
                    geofence = raidconfig['geofence']
                else:
                    geofence = None
                self.raidchannel_list.append(RaidChannel(chat_id, raidlevel_list, eggs, raidlevel_grouping, geofence))
        except Exception:
            log.exception("Error in parsing configuration. Check your config.toml")
            return False
        return True

    def _load_msgid_cache(self):
        try:
            f = open(".msgid_cache", "r")
            self._msgid_cache = json.load(f)
            log.info(f"load .msgid_cache: {self._msgid_cache}")
            f.close()
        except Exception as e:
            log.warning(f"can't load .msgid_cache. exception:{e}")
 
    def _save_msgid_cache(self):
        try:
            f = open(".msgid_cache", "w")
            json.dump(self._msgid_cache, f)
            log.debug(f"save .msgid_cache: {self._msgid_cache}")
            f.close()
        except Exception as e:
            log.exception(f"Exception '{type(e)}' in _save_msgid_cache()") 

    def _send_new_tg_msg(self, chat_id:str, msg:str, pin_msg:bool=True) -> None:
        try:
            response = self._tgapi.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")
            log.debug(f"send new msg, response:{response}")
            if response["ok"]:
                msg_id = response["result"]["message_id"]
                self._msgid_cache.update({chat_id: msg_id})
                if pin_msg:
                    log.debug(f"pin new message...")
                    result = self._tgapi.pin_message(chat_id = chat_id, message_id = msg_id)
                    # delete pin info message below pinned status message
                    log.debug(f"delete pin info message...")
                    result = self._tgapi.delete_message(chat_id = chat_id, message_id = msg_id + 1)
        except Exception as e:
            log.exception(f"Exception '{type(e)}' in send_new_raid_msg()")

    def update_tg_raid_msg(self, chat_id:str, msg:str) -> None:
        # no old message to update found -> send new message
        if chat_id not in self._msgid_cache.keys():
            #send new message
            self._send_new_tg_msg(chat_id, msg)
        # update old message
        else:
            try:
                response = self._tgapi.edit_message(chat_id=chat_id, message_id=self._msgid_cache[chat_id], text=msg, parse_mode="HTML")
                log.debug(f"edit msg, response:{response}")
                if response is not None and not self._tgapi.is_response_ok(response):
                    # we got a valid response, but error reported -> we need to create new message
                    log.warning(f"update raid msg failed for chat_id:'{chat_id}' -> send new message and pin again...")
                    self._send_new_tg_msg(chat_id, msg)
            except Exception as e:
                log.exception(f"Exception '{type(e)}' in update_raid_msg()")

    def convert_timestamp_to_str(self, timestamp:int, stringformat:str="%H:%M") -> str:
        return datetime.fromtimestamp(timestamp).strftime(stringformat)

    def create_raid_msg(self, raidinfo_list) -> str:
        new_raid_msg = ""
        if raidinfo_list:
            for raidinfo in raidinfo_list:
                # get start and end time
                v_time_start = self.convert_timestamp_to_str(raidinfo['raid_battle_timestamp'], self._cfg_format_time)
                v_time_end = self.convert_timestamp_to_str(raidinfo['raid_end_timestamp'], self._cfg_format_time)
                max_len = self._cfg_format_max_gymname_len
                v_gym_name = (raidinfo['gym_name'][:(max_len-2)] + '..') if len(raidinfo['gym_name']) > max_len else raidinfo['gym_name']
                v_lat = raidinfo['lat']
                v_lon = raidinfo['lon']
                v_gmaps_url = f"https://maps.google.de/?q={v_lat:.6f},{v_lon:.6f}"
                v_raidlevel_name = self._pogodata.get_raidlevel_name(raidinfo['raid_level'])
                v_raidlevel_num = raidinfo['raid_level']
                v_raidlvl_emoji = self._get_raidlevel_emoji(v_raidlevel_num)
                keywords = dict(
                    raidlvl_name = v_raidlevel_name,
                    raidlvl_num = v_raidlevel_num,
                    raidlvl_emoji = v_raidlvl_emoji,
                    time_start = v_time_start,
                    time_end = v_time_end,
                    gym_name = v_gym_name,
                    gmaps_url = v_gmaps_url,
                    lat = v_lat,
                    lon = v_lon
                )
                # Raid-egg?
                if raidinfo['raid_pokemon_id'] == 0:
                    # Raid-egg
                    new_raid_msg += self._cfg_tmpl_raidegg_msg.safe_substitute(keywords) + "\n"
                else:
                    #calculate additional keywords (started raid only)
                    v_atk_fast = self._pogodata.get_move_name(raidinfo['atk_fast'])
                    v_atk_charge = self._pogodata.get_move_name(raidinfo['atk_charge'])
                    v_pokemon_name = self._pogodata.get_pokemon_name(raidinfo['raid_pokemon_id'])
                    keywords.update(
                        atk_fast = v_atk_fast,
                        atk_charge = v_atk_charge,
                        pokemon_name = v_pokemon_name
                    )
                    new_raid_msg += self._cfg_tmpl_raid_msg.safe_substitute(keywords) + "\n"
        return new_raid_msg

    def _get_raidlevel_emoji(self, raidlevel:int) -> str:
        raidlevel_emoji = ["0️⃣","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        emoji = "❔"
        try:
            if raidlevel >= 0 and raidlevel <= 10:
                emoji = raidlevel_emoji[raidlevel]
        except Exception:
            pass
        return emoji

    def update_raids(self):
        log.debug("update_raids()...")
        for raidchannel in self.raidchannel_list:
            new_raid_msg = ""
            if raidchannel.raidlevel_grouping:
                # raidlevel grouping activated (true)
                for raid_level in raidchannel.raidlevel_list:
                    raidinfo_list = self._scannerconnector.get_raids([raid_level], raidchannel.eggs, raidchannel.get_geofence())
                    if raidinfo_list:
                        v_raidlvl_name = self._pogodata.get_raidlevel_name(raid_level, True)
                        v_raidlvl_emoji = self._get_raidlevel_emoji(raid_level)
                        keywords = dict(
                            raidlvl_name = v_raidlvl_name,
                            raidlvl_num = raid_level,
                            raidlvl_emoji = v_raidlvl_emoji
                        )
                        new_raid_msg += self._cfg_tmpl_grouped_title_msg.safe_substitute(keywords) + "\n"
                        new_raid_msg += self.create_raid_msg(raidinfo_list)
            else:
                # raidlevel grouping not activated (false)
                raidinfo_list = self._scannerconnector.get_raids(raidchannel.raidlevel_list, raidchannel.eggs, raidchannel.get_geofence())
                new_raid_msg = self.create_raid_msg(raidinfo_list)
            # check for empty raidmessage (no raids) -> send out 'tmpl_no_raid_msg' from config.toml
            if new_raid_msg == "":
                new_raid_msg = self._cfg_format_no_raids_msg + "\n"
            # add actual date + time (so everyone can see when raid message was updated last time)
            new_raid_msg += f"\n\u23F1 {datetime.now().strftime('%d.%m.%y %H:%M')}"
            log.debug(f"new raid_msg (len:{len(new_raid_msg)}):\n{new_raid_msg}")
            self.update_tg_raid_msg(raidchannel.chat_id, new_raid_msg)
        self._save_msgid_cache()
        log.debug("update_raids() done")

    def run(self):
        log.info("start...")
        # init
        try:
            #create scanner connector and tg interface
            self._scannerconnector = RdmConnector(db_host=self._cfg_db_host, db_port=self._cfg_db_port, db_name=self._cfg_db_name, db_username=self._cfg_db_user, db_password=self._cfg_db_password)
            self._tgapi = SimpleTelegramApi(self._cfg_api_token)
            self._pogodata = Pogodata(self._cfg_format_language)
            self._pogodata.update()
            last_pogodata_update = time.time()
        except Exception:
            log.exception("exception during run() init. Check configuration.")
            return
        # cyclic functions
        while True:
            try:
                self.update_raids()
                if (time.time() - last_pogodata_update) > self._pogodata_update_cycle_in_s:
                    self._pogodata.update()
                    last_pogodata_update = time.time()
            except Exception as e:
                log.error("exception during run() cycle: ")
                log.exception(e)
            time.sleep(self._sleep_mainloop_in_s)