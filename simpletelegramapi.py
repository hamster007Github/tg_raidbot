#!/usr/local/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
* Import
****************************************
'''
import json
# url handling
import urllib
import requests
# logging
import logging

'''
****************************************
* Global variables
****************************************
'''
log = logging.getLogger(__name__)
MAX_MSG_LEN = 3000

'''
****************************************
* Classes
****************************************
'''
class SimpleTelegramApi:
    def __init__(self, api_token:str) -> None:
        self._base_url = self._get_base_url(api_token)

    def _get_base_url(self, api_token:str) -> str:
        return "https://api.telegram.org/bot{}/".format(api_token)

    def _send_request(self, command:str) -> str:
        request_url = self._base_url + command
        response = requests.get(request_url)
        decoded_response = response.content.decode("utf8")
        return decoded_response

    def _util_limit_msg_len(self, text:str) -> str:
        trimmed_text = (text[:(MAX_MSG_LEN-2)] + '..') if len(text) > MAX_MSG_LEN else text
        return trimmed_text

    def is_response_ok(self, response) -> bool:
        result = False
        try:
            if isinstance(response, dict):
                if not response["ok"]:
                    error_code = response["error_code"]
                    description = response["description"]
                    if error_code == 400 and description == "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message":
                        result = True
                    else:
                        result = False
                else:
                    result = True
        except Exception:
            log.error(f"Can't check_response. Response seems not matching with TG API")
            result = False
        return result

    def send_message(self, chat_id:int, text:str, parse_mode="HTML"):
        try:
            text = self._util_limit_msg_len(urllib.parse.quote_plus(text))
            response = self._send_request("sendMessage?text={}&chat_id={}&parse_mode={}".format(text, chat_id, parse_mode))
            response = json.loads(response)
            if not response["ok"]:
                error_code = response["error_code"]
                description = response["description"]
                log.warning(f"send_message failed for chat_id:'{chat_id}'. error_code:{error_code} description:{description}")
        except Exception:
            log.error(f"Can't communicate with TG server. Most likely communication issues.")
            response = None
        return response

    def edit_message(self, chat_id:int, message_id:int, text:str, parse_mode="HTML"):
        try:
            text = self._util_limit_msg_len(urllib.parse.quote_plus(text))
            response = self._send_request("editMessageText?chat_id={}&message_id={}&parse_mode={}&text={}".format(chat_id, message_id, parse_mode, text))
            response = json.loads(response)
            if not response["ok"]:
                error_code = response["error_code"]
                description = response["description"]
                if error_code == 400 and description == "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message":
                    pass
                else:
                    log.warning(f"edit_message failed for chat_id:'{chat_id}'. error_code:{error_code} description:{description}")
        except Exception:
            log.error(f"Can't communicate with TG server. Most likely communication issues.")
            response = None
        return response

    def delete_message(self, chat_id:int, message_id:int):
        try:
            response = self._send_request("deleteMessage?chat_id={}&message_id={}".format(chat_id, message_id))
            response = json.loads(response)
            if not response["ok"]:
                error_code = response["error_code"]
                description = response["description"]
                log.warning(f"delete_message failed for chat_id:'{chat_id}'. error_code:{error_code} description:{description}")
        except Exception:
            log.error(f"Can't communicate with TG server. Most likely communication issues.")
            response = None
        return response

    def pin_message(self, chat_id:int, message_id:int, disable_notification="True"):
        try:
            response = self._send_request("pinChatMessage?chat_id={}&message_id={}&disable_notification={}".format(chat_id, message_id, disable_notification))
            response = json.loads(response)
            if not response["ok"]:
                error_code = response["error_code"]
                description = response["description"]
                log.warning(f"pin_message failed for chat_id:'{chat_id}'. error_code:{error_code} description:{description}")
        except Exception:
            log.error(f"Can't communicate with TG server. Most likely communication issues.")
            response = None
        return response

    def get_message(self):
        response = self._send_request("getUpdates")
        response = json.loads(response)
        return response
