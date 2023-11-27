from datetime import datetime
from enum import Enum
import json
import uuid
from fastapi import Request
import requests
import threading

from dsr_model_sdk.logger import logger
from dsr_model_sdk.message import MessageType
from dsr_model_sdk.topics import EVENT_TOPIC, RESULT_TOPIC, retry_apdapter

EventType = Enum('EventType', ['PREDICT_START', 'PREDICT_PROCESSING', 'PREDICT_FAILED', 'PREDICT_COMPLETED'])

class Session:
    session: dict

    def __init__(
            self,
            sdk_metadata: dict,
            target: str,
            storage_target: str,
            timeout: float = 10,
            test_client = None,
            dev_mode: bool = False, 
        ) -> None:
            self.sdk_metadata = sdk_metadata
            self.storage_target = storage_target
            self.target = target
            self.session = {
                "id":  uuid.uuid4().hex,
                "start": f"{datetime.now()}",
                "end": None
            }
            self.thread = None
            self.timeout = timeout
            self.closed = False
            self.test_client = test_client # Only using for testing
            self.dev_mode = dev_mode

    def start(self, req: Request):
        logger.info(f"Start new session {self.session['id']}")

        body = {
            "type": MessageType.EVENT.name, 
            "session": self.session,
            "data" : {
                "event": EventType.PREDICT_START.name,
            },
            "extra": {
                "headers": dict(req.headers)
            },
            "session": self.session
        }

        return self._delivery(EVENT_TOPIC,  self.sdk_metadata | body)
    
    def processing(self, req: Request, data: dict = {}):
        body = {
            "type": MessageType.EVENT.name,
            "session": self.session,
            "data" : {
                "event": EventType.PREDICT_PROCESSING.name,
            } | data,
            "extra": {
                "headers": dict(req.headers)
            },
        }

        return self._delivery(EVENT_TOPIC,  self.sdk_metadata | body)
    
    def completed(self, req: Request, data: dict = {}):
        self.session["end"] = f"{datetime.now()}"
        body = {
            "type": MessageType.EVENT.name,
            "session": self.session,
            "data" : {
                "event": EventType.PREDICT_COMPLETED.name,
                "result": {} | data
            },
            "extra": {
                "headers": dict(req.headers)
            },
        }

        return self._delivery(EVENT_TOPIC,  self.sdk_metadata | body)
    
    def failed(self, req: Request, error: dict = {}):
        self.session["end"] = f"{datetime.now()}"
        body = {
            "type": MessageType.EVENT.name,
            "session": self.session,
            "data" : {
                "event": EventType.PREDICT_FAILED.name,
                "error": {} | error
            },
            "extra": {
                "headers": dict(req.headers)
            },
        }

        return self._delivery(EVENT_TOPIC,  self.sdk_metadata | body)
    
    def result(self, req: Request, json: dict = None, path: str = None):
        body = {
            "type": MessageType.RESULT.name,
            "session": self.session,
            "data" : {
                "json": json,
                "path": path,
            },
            "extra": {
                "headers": dict(req.headers)
            },
        }

        return self._delivery(RESULT_TOPIC,  self.sdk_metadata | body)
    
    def close(self):
        self.closed = True

    def _delivery(self, topic: str, data: dict, wait: bool = True):
        if self.closed:
            logger.warning("Session is closed")
            return None
        
        if self.dev_mode:
            logger.warning("Session in dev mode so request does not delivery")
            return None


        params = "?async=false" if wait else "?async=true"
        url = f"{self.target}/topics/{topic}" + params
        body = {
             "records": [
                {
                    "key": self.sdk_metadata['id'],
                    "value": data
                }
             ]
        }

        if self.test_client != None:
            r = self.test_client.post(url=f'/topics/{topic}', content=json.dumps(data))
            return r.json()
        
        # Async call
        self.thread = threading.Thread(target=self._executeRemote, args=[url, body], daemon=True)
        self.thread.start()
        return None
        # self._executeRemote(url, body)
    
    def _executeRemote(self, url:str, body: dict) -> None:
        try:
            logger.info(f"Start delivery message to topic {url}")
            session = retry_apdapter(retries=5)
            r = session.post(
                url,
                data=json.dumps(body),
                headers= {
                    'Content-Type': 'application/vnd.kafka.json.v2+json',
                    'accept': 'application/vnd.kafka.v2+json'
                },
                timeout=self.timeout,
                )
            r.raise_for_status()
            logger.info("Start delivery status_code: "+ str(r.status_code))
            logger.debug("Debug body: "+ str(body))
        except requests.exceptions.HTTPError as errh:
            logger.error("HTTP Error")
            logger.error(errh.args[0])
        except requests.exceptions.ReadTimeout as errrt:
            logger.error("Time out")
        except requests.exceptions.ConnectionError as conerr:
            logger.error("Connection error")
        except requests.exceptions.RequestException as errex:
            logger.error("Exception request")

    def s3_sts_credential(self, req: Request):
        try:
            tenant = req.headers.get("X-Tenant", None)
            if tenant is None:
                raise KeyError('Can not found X-Tenant in request header')

            url = f"{self.storage_target}/credential/ai"
            body = {
                "tenant": tenant
            }    
            session = retry_apdapter(retries=5)
            r = session.post(
                url,
                data=json.dumps(body),
                timeout=self.timeout,
            )
            r.raise_for_status()
            logger.info("Get STS Credential success: "+ str(r.status_code))
            logger.debug("Body: "+ str(body))
            return r.json()
        except KeyError as kerr:
            logger.error('Can not found X-Tenant in request header')
        except requests.exceptions.HTTPError as errh:
            logger.error("HTTP Error")
            logger.error(errh.args[0])
        except requests.exceptions.ReadTimeout as errrt:
            logger.error("Time out")
        except requests.exceptions.ConnectionError as conerr:
            logger.error("Connection error")
        except requests.exceptions.RequestException as errex:
            logger.error("Exception request")


        