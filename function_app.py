import azure.functions as func
import datetime
import json
import logging
import requests
import os
import sys
from sys import path
import constants as const
import helper as hp
from okta_log_collector import OktaLogCollector
import storage_account as acc

# dir_path = os.path.dirname(os.path.realpath(__file__))
# sys.path.insert(0, dir_path)

app = func.FunctionApp()
oktaLog = OktaLogCollector()
@app.timer_trigger(schedule="*/30 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def MyTimerTrigger1(myTimer: func.TimerRequest) -> None:
    logging.info('Python timer trigger function executing uploaded using zip.')
    if myTimer.past_due:
        logging.info('The timer is past due!')
    
    oktaLog.collect_logs()
    logging.info('Python timer trigger function executed.')
