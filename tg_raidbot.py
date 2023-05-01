#!/usr/local/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
* Import
****************************************
'''
from typing import Dict, List
# time handling
import time
from datetime import datetime, timedelta
# os functions (path, ...)
import os
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
from msgidcache import MsgIdCache
from cfg import Cfg

'''
****************************************
* Global variables
****************************************
'''
log = logging.getLogger(__name__)
cfg = Cfg(os.path.dirname(__file__) + "/config.toml")

'''
****************************************
* Classes
****************************************
'''
#****************************************
# Class: RaidChannel
#****************************************
class RaidChannel():
    def __init__(self, raidconfig):
        self.chat_id = raidconfig["chat_id"]
        self.message_thread_id = raidconfig["message_thread_id"]
        self.raidlevel_list = raidconfig["raidlevel_list"]
        self.eggs = raidconfig["eggs"]
        self.raidlevel_grouping = raidconfig["raidlevel_grouping"]
        self.geofence = raidconfig["geofence"]
        self.order_time_reverse = raidconfig["order_time_reverse"]
        self.pin_msg = raidconfig["pin_msg"]

#****************************************
# Class: TelegramRaidbot
#****************************************
class TelegramRaidbot():
    def __init__(self):
        self.raidchannel_list = []
        self._msgidcache = MsgIdCache()

    def _send_new_tg_msg(self, chat_id:str, msg:str, message_thread_id:int=0, pin_msg:bool=True) -> None:
        try:
            if message_thread_id != 0:
                response = self._tgapi.send_message_thread(chat_id=chat_id, text=msg, message_thread_id=message_thread_id)
            else:
                response = self._tgapi.send_message(chat_id=chat_id, text=msg)
            log.debug(f"send new msg, response:{response}")
            if response["ok"]:
                msg_id = response["result"]["message_id"]
                self._msgidcache.set_message_id(chat_id, message_thread_id, msg_id)
                if pin_msg:
                    log.debug(f"pin new message...")
                    result = self._tgapi.pin_message(chat_id = chat_id, message_id = msg_id)
                    # delete pin info message below pinned status message
                    log.debug(f"delete pin info message...")
                    result = self._tgapi.delete_message(chat_id = chat_id, message_id = msg_id + 1)
        except Exception as e:
            log.exception(f"Exception '{type(e)}' in send_new_raid_msg()")

    def update_tg_raid_msg(self, raidchannel:RaidChannel, msg:str) -> None:
        msg = SimpleTelegramApi.util_smart_trim_text(msg, trim_end_str = cfg.tmpl_msglimit_reached_msg)
        # no old message to update found -> send new message
        message_id = self._msgidcache.get_message_id(raidchannel.chat_id, raidchannel.message_thread_id)
        if message_id is None:
            #send new message
            self._send_new_tg_msg(chat_id=raidchannel.chat_id, msg=msg, message_thread_id=raidchannel.message_thread_id, pin_msg=raidchannel.pin_msg)
        # update old message
        else:
            try:
                response = self._tgapi.edit_message(chat_id=raidchannel.chat_id, message_id=message_id, text=msg)
                log.debug(f"edit msg, response:{response}")
                if response is not None and not self._tgapi.is_response_ok(response):
                    # we got a valid response, but error reported -> we need to create new message
                    log.warning(f"update raid msg failed for chat_id:'{raidchannel.chat_id}' -> send new message...")
                    self._send_new_tg_msg(chat_id=raidchannel.chat_id, msg=msg, message_thread_id=raidchannel.message_thread_id, pin_msg=raidchannel.pin_msg)
            except Exception as e:
                log.exception(f"Exception '{type(e)}' in update_raid_msg()")

    def convert_timestamp_to_str(self, timestamp:int, stringformat:str="%H:%M") -> str:
        return datetime.fromtimestamp(timestamp).strftime(stringformat)

    def create_raid_msg(self, raidinfo_list:List[Dict]) -> str:
        new_raid_msg = ""
        if raidinfo_list:
            for raidinfo in raidinfo_list:
                # get all keyword data
                v_time_start = self.convert_timestamp_to_str(raidinfo['raid_battle_timestamp'], cfg.format_time)
                v_time_end = self.convert_timestamp_to_str(raidinfo['raid_end_timestamp'], cfg.format_time)
                max_len = cfg.format_max_gymname_len
                if raidinfo['gym_name'] is None:
                    v_gym_name = cfg.format_unknown_gym_name
                else:
                    gym_name = raidinfo['gym_name']
                    v_gym_name = (gym_name[:(max_len-2)] + '..') if len(gym_name) > max_len else gym_name
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
                    new_raid_msg += Template(cfg.tmpl_raidegg_msg).safe_substitute(keywords) + "\n"
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
                    new_raid_msg += Template(cfg.tmpl_raid_msg).safe_substitute(keywords) + "\n"
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
                    # get raid data from scanner for each configurated raid level
                    raidinfo_list = self._scannerconnector.get_raids([raid_level], raidchannel.eggs, raidchannel.geofence, raidchannel.order_time_reverse)
                    if raidinfo_list:
                        # create message part for raid level
                        v_raidlvl_name = self._pogodata.get_raidlevel_name(raid_level, True)
                        v_raidlvl_emoji = self._get_raidlevel_emoji(raid_level)
                        keywords = dict(
                            raidlvl_name = v_raidlvl_name,
                            raidlvl_num = raid_level,
                            raidlvl_emoji = v_raidlvl_emoji
                        )
                        new_raid_msg += Template(cfg.tmpl_grouped_title_msg).safe_substitute(keywords) + "\n"
                        new_raid_msg += self.create_raid_msg(raidinfo_list)
            else:
                # raidlevel grouping not activated (false) -> get all raid data for all configurated raid level
                raidinfo_list = self._scannerconnector.get_raids(raidchannel.raidlevel_list, raidchannel.eggs, raidchannel.geofence, raidchannel.order_time_reverse)
                new_raid_msg = self.create_raid_msg(raidinfo_list)
            # check for empty raidmessage (no raids) -> send out 'tmpl_no_raid_msg' from config.toml
            if new_raid_msg == "":
                new_raid_msg = cfg.tmpl_no_raids_msg + "\n"
            # add actual date + time (so everyone can see when raid message was updated last time)
            new_raid_msg += f"\n\u23F1 {datetime.now().strftime('%d.%m.%y %H:%M')}"
            log.debug(f"new raid_msg (len:{len(new_raid_msg)}):\n{new_raid_msg}")
            self.update_tg_raid_msg(raidchannel, new_raid_msg)
        self._msgidcache.store_cache()
        log.debug("update_raids() done")

    def run(self):
        log.info("start...")
        # init
        try:
            self._msgidcache.restore_cache()
            cfg.load()
            for raidconfig in cfg.raidconfig_list:
                self.raidchannel_list.append(RaidChannel(raidconfig))
            #create scanner connector and tg interface
            self._scannerconnector = RdmConnector(db_host=cfg.db_host, db_port=cfg.db_port, db_name=cfg.db_name, db_username=cfg.db_user, db_password=cfg.db_password)
            self._tgapi = SimpleTelegramApi(cfg.api_token)
            self._pogodata = Pogodata(cfg.format_language)
            self._pogodata.update()
            last_pogodata_update = time.time()
        except KeyError:
            log.error("Config error during run() - init part")
            return
        except Exception:
            log.exception("Unexpected exception during run() - init part")
            return
        # cyclic functions
        while True:
            try:
                self.update_raids()
                if (time.time() - last_pogodata_update) > cfg.pogodata_update_cycle_in_s:
                    self._pogodata.update()
                    last_pogodata_update = time.time()
            except Exception as e:
                log.error("exception during run() cycle: ")
                log.exception(e)
            time.sleep(cfg.sleep_mainloop_in_s)

