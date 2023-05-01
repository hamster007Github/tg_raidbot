#!/usr/local/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
* Import
****************************************
'''
from typing import Dict, List
# data processing
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
# utils
from functools import reduce  # forward compatibility for Python 3
import operator
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

class Cfg():
    def __init__(self, filepath:str) -> None:
        self._config_filepath = filepath
        return

    @staticmethod
    def _get_value(cfg_dict:Dict, key_list:List[str], fallback=None):
        """Get nested TOML parameter by key list"""

        try:
            result = reduce(operator.getitem, key_list, cfg_dict)
        except Exception:
            if fallback is not None:
                log.info(f"Optional parameter '{key_list}' missing in configuration. Using default:'{fallback}'")
                result = fallback
            else:
                log.error(f"Mandatory parameter missing in configuration:'{key_list}'")
                raise KeyError
        return result

    @staticmethod
    def _get_array(cfg_dict:Dict, key_list:List[str]):
        """Get nested TOML array as python list"""

        try:
            result = reduce(operator.getitem, key_list, cfg_dict)
            if not isinstance(result, list):
                raise KeyError
        except Exception:
            log.error(f"Mandatory parameter array missing in configuration:'{key_list}")
            raise KeyError
        return result

    def _load_file(self) -> Dict:
        """load and decode TOML file"""

        toml_dict = None
        # load parameter from toml file
        try:
            with open(self._config_filepath, "rb") as f:
                toml_dict = tomllib.load(f)
        except tomllib.TOMLDecodeError:
            log.error("toml file can't be decoded. Check TOML syntax")
        except FileNotFoundError:
            log.error(f"Can't find file '{filepath}'. Check, if file exists")
        except Exception:
            log.exception("Unexpected exception at loading {filepath}")
        return toml_dict

    def load(self) -> None:
        """load TOML file and parse parameter

        All parameter will be available as public members of Cfg object. Function should be called only once on startup.

        Raises:
            KeyError: an error occurred during parsing configuration parameter (e.g. missing values, etc)
        """

        cfg_dict = self._load_file()
        if not isinstance(cfg_dict, dict):
            raise KeyError

        # [general]
        self.sleep_mainloop_in_s = Cfg._get_value(cfg_dict, ["general","raidupdate_cycle_in_s"], fallback=60)
        self.pogodata_update_cycle_in_s = Cfg._get_value(cfg_dict, ["general","pogodata_update_cycle_in_h"], fallback=24) * 3600
        self.api_token = Cfg._get_value(cfg_dict, ["general", "token"])

        # [db]: database setting
        self.db_host = Cfg._get_value(cfg_dict, ["db", "host"])
        self.db_name = Cfg._get_value(cfg_dict, ["db", "name"])
        self.db_user = Cfg._get_value(cfg_dict, ["db", "user"])
        self.db_password = Cfg._get_value(cfg_dict, ["db", "password"])
        self.db_port = Cfg._get_value(cfg_dict, ["db", "port"], fallback=3306)

        # [format]
        self.format_language = Cfg._get_value(cfg_dict, ["format", "language"], fallback="en")
        self.format_max_gymname_len = Cfg._get_value(cfg_dict, ["format", "max_gymname_len"], fallback = 27)
        self.format_time = Cfg._get_value(cfg_dict, ["format", "time_format"], fallback = "%H:%M")
        self.format_unknown_gym_name = Cfg._get_value(cfg_dict, ["format", "unknown_gym_name"], fallback = "N/A")

        # [templates]
        self.tmpl_msglimit_reached_msg = Cfg._get_value(cfg_dict, ["templates", "tmpl_msglimit_reached_msg"], fallback = "...")
        self.tmpl_no_raids_msg = Cfg._get_value(cfg_dict, ["templates", "tmpl_no_raid_msg"], fallback = "No raids")
        self.tmpl_grouped_title_msg = Cfg._get_value(cfg_dict, ["templates", "tmpl_grouped_title_msg"])
        self.tmpl_raid_msg = Cfg._get_value(cfg_dict, ["templates", "tmpl_raid_msg"])
        self.tmpl_raidegg_msg = Cfg._get_value(cfg_dict, ["templates", "tmpl_raidegg_msg"])

        # [[raidconfig]] tables
        self.raidconfig_list = []
        cfg_raidconfig_list = Cfg._get_array(cfg_dict, ["raidconfig"])
        for cfg_raidconfig in cfg_raidconfig_list:
            raidconfig_dict = {
                "chat_id": Cfg._get_value(cfg_raidconfig, ["chat_id"]),
                "raidlevel_list": Cfg._get_array(cfg_raidconfig, ["raidlevel"]),
                "message_thread_id": Cfg._get_value(cfg_raidconfig, ["message_thread_id"], fallback = 0),
                "eggs": Cfg._get_value(cfg_raidconfig, ["eggs"], fallback = True),
                "raidlevel_grouping": Cfg._get_value(cfg_raidconfig, ["raidlevel_grouping"], fallback = True),
                "geofence": Cfg._get_value(cfg_raidconfig, ["geofence"], fallback = ""),
                "order_time_reverse": Cfg._get_value(cfg_raidconfig, ["order_time_reverse"], fallback = False),
                "pin_msg": Cfg._get_value(cfg_raidconfig, ["pin_msg"], fallback = True)
            }
            self.raidconfig_list.append(raidconfig_dict)
