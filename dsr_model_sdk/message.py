from enum import Enum
from datetime import datetime

MessageType = Enum('MessageType',['HEALTH', 'EVENT', 'RESULT'])

def healthMsg():
    return {
        "type": MessageType.HEALTH.name,
        "data": {
            "status": "health",
            "time": f"{datetime.now()}"
        }
    }