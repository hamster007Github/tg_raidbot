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
        """get TG bot API base url including bot token"""

        return "https://api.telegram.org/bot{}/".format(api_token)

    def _send_request(self, command:str) -> str:
        """send TG bot API https request and return https response"""

        request_url = self._base_url + command
        response = requests.get(request_url)
        decoded_response = response.content.decode("utf8")
        return decoded_response

    def _limit_text_len(self, text:str) -> str:
        """trim text to <= MAX_MSG_LEN"""

        if len(text) > MAX_MSG_LEN:
            # trim to max len - trim_end_str
            trimmed_text = text[:(MAX_MSG_LEN-1)]
        else:
            trimmed_text = text
        return trimmed_text

    def _create_send_msg_request(self, chat_id:str, text:str, parse_mode:str) -> str:
        """create a telegram bot API url request string"""

        text = urllib.parse.quote_plus(self._limit_text_len(text))
        request = f"sendMessage?text={text}&chat_id={chat_id}&parse_mode={parse_mode}"
        return request

    @staticmethod
    def util_smart_trim_text(text:str, trim_end_str:str="...", trim_str:str="\n") -> str:
        """smart trim text to <= MAX_MSG_LEN until next trim_str substring (default: new line) was found.
        Insert a trim_end_str substring at the end of the text to mark text as trimmed."""

        if len(text) > MAX_MSG_LEN:
            # trim to max len - trim_end_str
            trimmed_text = text[:(MAX_MSG_LEN-len(trim_end_str))]
            # trim to last found trim_str
            index = trimmed_text.rfind(trim_str)
            trimmed_text = trimmed_text[:index]
            # mark trimmed message with trim_end_str substring
            trimmed_text += trim_end_str
        else:
            trimmed_text = text
        return trimmed_text

    def is_response_ok(self, response:dict) -> bool:
        """check response of a message and return interpretation"""

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
            log.exception(f"Can't check_response. Response seems not matching with TG API")
            result = False
        return result

    def send_message(self, chat_id:str, text:str, parse_mode="HTML"):
        """send a new text message into a chat"""

        try:
            request = self._create_send_msg_request(chat_id, text, parse_mode)
            response = self._send_request(request)
            response = json.loads(response)
            if not response["ok"]:
                error_code = response["error_code"]
                description = response["description"]
                log.warning(f"send_message failed for chat_id:'{chat_id}'. error_code:{error_code} description:{description}")
        except Exception:
            log.exception(f"send_message: can't communicate with TG server. Most likely communication issues.")
            response = None
        return response

    def send_message_thread(self, chat_id:str, message_thread_id:int, text:str, parse_mode="HTML") -> dict:
        """send a new text message into a topic(message thread) of a chat"""

        try:
            request = self._create_send_msg_request(chat_id, text, parse_mode)
            request += f"&message_thread_id={message_thread_id}"
            response = self._send_request(request)
            response = json.loads(response)
            if not response["ok"]:
                error_code = response["error_code"]
                description = response["description"]
                log.warning(f"send_message_thread failed for chat_id:'{chat_id}' message_thread_id:'{message_thread_id}'. error_code:{error_code} description:{description}")
        except Exception:
            log.exception(f"send_message_thread: can't communicate with TG server. Most likely communication issues.")
            response = None
        return response

    def edit_message(self, chat_id:str, message_id:int, text:str, parse_mode="HTML") -> dict:
        """edit a text message from a chat"""

        try:
            text = urllib.parse.quote_plus(self._limit_text_len(text))
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
            log.exception(f"edit_message: can't communicate with TG server. Most likely communication issues.")
            response = None
        return response

    def delete_message(self, chat_id:str, message_id:int) -> dict:
        """delete a message from a chat"""

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

    def pin_message(self, chat_id:str, message_id:int, disable_notification:bool="True") -> dict:
        """pin a message in a chat"""

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
