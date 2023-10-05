import json
import requests
from dsr_model_sdk.logger import logger
from dsr_model_sdk.message import healthMsg
from dsr_model_sdk.topics import retry_apdapter

def send_health_to_target(id, name, url):
    try:
        value= healthMsg() | {"id": id, "name": name}
        logger.info(f"Start delivery message to topic {url}")
        body = {
            "records": [
                {
                    "key": id,
                    "value": value
                }
            ]
        }
        session = retry_apdapter(retries=2)
        r = session.post(
            url,
            data=json.dumps(body),
            headers= {
                'Content-Type': 'application/vnd.kafka.json.v2+json',
                'accept': 'application/vnd.kafka.v2+json'
            },
            timeout=10,
            )
        r.raise_for_status()
        logger.info(str(r.status_code) + ' => ' + str(r.json()))
    except requests.exceptions.HTTPError as errh:
        logger.error("HTTP Error")
        logger.error(errh.args[0])
    except requests.exceptions.ReadTimeout as errrt:
        logger.error("Time out")
    except requests.exceptions.ConnectionError as conerr:
        logger.error("Connection error")
    except requests.exceptions.RequestException as errex:
        logger.error("Exception request")