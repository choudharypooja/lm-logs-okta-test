import json
import logging
import requests
from datetime import datetime, timedelta, timezone
import os
import validators
import storage_account
import constants as const
import helper as hp
from log_ingester import LogIngester
import msgspec_okta_event

OKTA_LOGS_ENDPOINT = "/api/v1/logs"
HTTP_PROTOCOL = "https://"
OKTA_EVENT_FILTER = "OKTA_EVENT_FILTER"
OKTA_EVENT_KEYWORD = "OKTA_EVENT_KEYWORD"
OKTA_NEXT_LINK = "okta_next_link"
RETRIES = "next_link_retries"
MAX_RETRIES = 3
BACK_FILL_DURATION_MINUTES = 2

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class OktaLogCollector:
    def __init__(self):
        self.domain = hp.get_attr_from_env(const.OKTA_DOMAIN)
        self.api_key = hp.get_required_attr_from_env(const.OKTA_API_KEY)
        self.log_ingester = LogIngester()
        self.back_fill_dur_min = BACK_FILL_DURATION_MINUTES
        self.retry_attempt = 0

    def get_domain(self):
        return self.domain
    
    def get_last_report_time(self):
        return datetime.now(timezone.utc) - timedelta(minutes=self.back_fill_dur_min)


    def get_next_link_s3_obj_key(self):
        return "nextLinkForOktaLogs-" + self.log_ingester.get_company_name() + "-" + self.domain

    def get_url_to_query(self):
        if url_data_json := storage_account.getOktaUrl(self.get_next_link_s3_obj_key()):

            try:
                logger.info("url_data_json read from s3 = %s", url_data_json)
                link = url_data_json[OKTA_NEXT_LINK]
                if validators.url(link) and int(url_data_json[RETRIES]) < MAX_RETRIES:
                    logger.info("valid link read from s3 with valid retries = %s", url_data_json[RETRIES])
                    self.retry_attempt = int(url_data_json[RETRIES])
                    return link
                else:
                    logger.info("Invalid URL or Max retries exceeded. Will attempt to back-fill now. URL=%s, "
                                "Retries=%s, Max-Retries allowed = %s",
                                link, url_data_json[RETRIES], MAX_RETRIES)
                    return self.build_log_fetching_url()
            except Exception as e:
                logger.error("Unable to read persisted url from S3. Error = %s", str(e))
                raise e
        else:
            return self.build_log_fetching_url()

    def build_log_fetching_url(self):
        base_url = HTTP_PROTOCOL + self.domain + OKTA_LOGS_ENDPOINT
        last_report_time = self.get_last_report_time().isoformat().replace("+00:00", 'Z')
        logger.info("LastReportTimeStamp being used as since = %s ", last_report_time)
        query_param = "?since=" + last_report_time + "&sortOrder=ASCENDING" + "&limit=1000"
        final_url = base_url + query_param
        logger.info("Fetching URL built from scratch = %s", final_url)
        return final_url
    
    def update_next_url_to_query(self, url, retry):
        if validators.url(url) and retry >= 0:
            link_data = {OKTA_NEXT_LINK: url, RETRIES: retry}
            logger.info("Updating s3 with data = %s", json.dumps(link_data))
            storage_account.updateOktaUrl(self.get_next_link_s3_obj_key(), json.dumps(link_data))
        else:
            logger.warning("Invalid URL or negative retry count. Not updating in s3. url = %s, retry = %s", url, retry)


    def collect_logs(self):
        url_for_fetching = self.get_url_to_query() #"https://logicmonitorpreview.oktapreview.com/api/v1/logs"
        logger.info("Using url to query logs at execution : %s", url_for_fetching)
        url_to_persist = url_for_fetching
        print("API_KEY OKTA "+self.api_key)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'SSWS {}'.format(self.api_key)
        }
        try:
            response = requests.request("GET", url_for_fetching, headers=headers)
            response.raise_for_status()
            logger.info("response.text "+response.text)
            self.log_ingester.ingest_to_lm_logs(msgspec_okta_event.loads(response.text))
            while response.links["next"]["url"]:
                next_url = response.links["next"]["url"]
                url_to_persist = next_url
                # persist url to s3 as soon as ingestion is successful
                logger.info("Updating next url to s3 after last successful ingestion : %s ", next_url)
                self.update_next_url_to_query(url_to_persist, 0)

                url_for_fetching = url_to_persist
                self.retry_attempt = 0
                response = requests.request("GET", response.links["next"]["url"], headers=headers)
                response.raise_for_status()
                if len(msgspec_okta_event.loads(response.text)) < 1:
                    logger.info("Reached last next link as no logs found this time. Stopping log collection.. ")
                    break
                else:
                    self.log_ingester.ingest_to_lm_logs(msgspec_okta_event.loads(response.text))

            logger.info("URL for fetching first : %s, url to persist at the ending : %s", url_for_fetching,
                        url_to_persist)
            url_to_persist = response.links["self"]["url"]

        except Exception as e:

             if url_to_persist == url_for_fetching:
                logger.error("Exception encountered. incrementing retry attempt. Error = %s", str(e))
                self.retry_attempt += 1
            # raise Exception('Error occurred during execution')
        finally:
            if url_to_persist == url_for_fetching:
                if self.retry_attempt > 0:
                    logger.warning("Retrying attempt found. Incrementing retry count for same url = %s, "
                                   "retry_attempt to persist = %s", url_to_persist, str(self.retry_attempt))
                    self.update_next_url_to_query(url_to_persist, self.retry_attempt)
                else:
                    logger.info("URL unchanged. Skipping update in s3.")
            else:
                logger.info("Updating next url in s3 to %s", url_to_persist)
                self.update_next_url_to_query(url_to_persist, 0)
            logger.info("Okta log collection completed ... ")
