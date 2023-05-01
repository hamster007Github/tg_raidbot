#!/usr/local/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
* Import
****************************************
'''
# os functions (path, ...)
import os
import sys
# .ini config parser and datacache
import json
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
class MsgIdCache():
    def __init__(self, filename:str=".msgid_cache"):
        self._filename = filename
        self._msgid_cache_dict = {}
        pass

    def _create_key_string(self, chat_id:str, message_thread_id:int=0) -> str:
        """create key string"""
        if message_thread_id == 0:
            key = f"{chat_id}"
        else:
            key = f"{chat_id}:{message_thread_id}"
        return key

    def restore_cache(self) -> None:
        """load cachefile data into MsgIdCache dict"""
        try:
            f = open(self._filename, "r")
            msgid_cache_file = json.load(f)
            f.close()
            self._msgid_cache_dict = msgid_cache_file
            log.info(f"load .msgid_cache: {self._msgid_cache_dict}")
        except Exception as e:
            log.warning(f"can't load .msgid_cache. exception:{e}")

    def store_cache(self) -> None:
        """save MsgIdCache dict into cachefile"""
        try:
            f = open(self._filename, "w")
            json.dump(self._msgid_cache_dict, f)
            log.debug(f"save .msgid_cache: {self._msgid_cache_dict}")
            f.close()
        except Exception as e:
            log.warning(f"Exception '{type(e)}' in _save_msgid_cache_dict()")

    def set_message_id(self, chat_id:str, message_thread_id:int, message_id:int) -> None:
        """set message_id in MsgIdCache dict entry"""
        try:
            key = self._create_key_string(chat_id, message_thread_id)
            self._msgid_cache_dict.update({key: message_id})
        except Exception:
            log.exception(f"set_message_id() exception")

    def get_message_id(self, chat_id:str, message_thread_id:int=0) -> int:
        """get message_id from MsgIdCache dict entry"""
        message_id = None
        try:
            key = self._create_key_string(chat_id, message_thread_id)
            if key in self._msgid_cache_dict.keys():
                message_id = self._msgid_cache_dict[key]
        except Exception:
            log.exception(f"get_message_id() exception")
        return message_id

