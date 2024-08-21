#!/usr/local/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
* Import
****************************************
'''
import argparse
import sys
import logging
from mappingpylib import loggercfg
from tg_raidbot import TelegramRaidbot

'''
****************************************
* Constants
****************************************
'''

'''
****************************************
* Global variables
****************************************
'''
log = logging.getLogger() # root logger

'''
****************************************
* Classes
****************************************
'''

'''
****************************************
* Module functions
****************************************
'''
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-lc', '--log-level-console', default='INFO', choices=loggercfg.VALID_LOGLEVEL, required=False, help='set log level for console. Default:INFO')
    parser.add_argument('-lf', '--log-level-file', default='NONE', choices=loggercfg.VALID_LOGLEVEL_FILE, required=False, help='set log level for logfile. Default:NONE')
    args = parser.parse_args()
    file_loglevel = args.log_level_file
    console_loglevel = args.log_level_console
    if not loggercfg.is_valid_loglevel(console_loglevel):
        console_loglevel = "INFO"
    if not loggercfg.is_valid_loglevel(file_loglevel):
        file_loglevel = None
    loggercfg.config_logger(log, console_loglevel = console_loglevel, file_loglevel = file_loglevel, file_name = "tg_raidbot.log")

    try:
        log.info(f"Start TelegramRaidbot...")
        telegramRaidbot = TelegramRaidbot()
        #@TODO: add additional startup functions
    except Exception:
        log.error(f"Error in startup of TelegramRaidbot (__init__). Check configuration.")
        log.exception("Exception info:")
    else:
        telegramRaidbot.run()

'''
****************************************
* main functions
****************************************
'''
if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        log.warning(f"Script stopped by external stop signal (e.g. CTRL+c)")
        sys.exit(1)
    except Exception as e:
        log.exception(f"unexpected exception in main()")
        sys.exit(2)

