from datetime import datetime
from enum import Enum
import json
import uuid
from fastapi import Request
from fastapi.testclient import TestClient
import requests
import threading

from dsr_model_sdk.logger import logger
from dsr_model_sdk.message import MessageType
from dsr_model_sdk.topics import EVENT_TOPIC, RESULT_TOPIC, retry_apdapter

EventType = Enum('EventType', ['PREDICT_START', 'PREDICT_PROCESSING', 'PREDICT_FAILED', 'PREDICT_COMPLETED'])

class Session:
    session: dict
    test_client: TestClient

    def __init__(
            self,
            sdk_metadata: dict,
            target: str,
            timeout: float = 10,
            test_client: TestClient = None
        ) -> None:
            self.sdk_metadata = sdk_metadata
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

    def start(self, request: Request):
        logger.info(f"Start new session {self.session['id']}")

        body = {
            "type": MessageType.EVENT.name, 
            "session": self.session,
            "data" : {
                "event": EventType.PREDICT_START.name,
            },
            "extra": {
                "headers": dict(request.headers)
            },
            "session": self.session
        }

        return self._delivery(EVENT_TOPIC,  self.sdk_metadata | body)
    
    def processing(self, request: Request, data: dict = {}):
        body = {
            "type": MessageType.EVENT.name,
            "session": self.session,
            "data" : {
                "event": EventType.PREDICT_PROCESSING.name,
            } | data,
            "extra": {
                "headers": dict(request.headers)
            },
        }

        return self._delivery(EVENT_TOPIC,  self.sdk_metadata | body)
    
    def completed(self, request: Request, data: dict = {}):
        self.session["end"] = f"{datetime.now()}"
        body = {
            "type": MessageType.EVENT.name,
            "session": self.session,
            "data" : {
                "event": EventType.PREDICT_COMPLETED.name,
                "result": {} | data
            },
            "extra": {
                "headers": dict(request.headers)
            },
        }

        return self._delivery(EVENT_TOPIC,  self.sdk_metadata | body)
    
    def failed(self, request: Request, error: dict = {}):
        self.session["end"] = f"{datetime.now()}"
        body = {
            "type": MessageType.EVENT.name,
            "session": self.session,
            "data" : {
                "event": EventType.PREDICT_FAILED.name,
                "error": {} | error
            },
            "extra": {
                "headers": dict(request.headers)
            },
        }

        return self._delivery(EVENT_TOPIC,  self.sdk_metadata | body)
    
    def result(self, request: Request, json: dict = None, path: str = None):
        body = {
            "type": MessageType.RESULT.name,
            "session": self.session,
            "data" : {
                "json": json,
                "path": path,
            },
            "extra": {
                "headers": dict(request.headers)
            },
        }

        return self._delivery(RESULT_TOPIC,  self.sdk_metadata | body)
    
    def close(self):
        self.closed = True

    def _delivery(self, topic: str, data: dict, wait: bool = True):
        if self.closed:
            logger.warning("Session is closed")
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