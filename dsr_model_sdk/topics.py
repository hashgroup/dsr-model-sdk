from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter

HEALTH_TOPIC = "ai-health"
EVENT_TOPIC= "ai-event"
RESULT_TOPIC = "ai-result"

class RetryRequest(Retry):

    def __init__(self, backoff_max: int, **kwargs):
        super().__init__(**kwargs)
        self.DEFAULT_BACKOFF_MAX = backoff_max

    def new(self, **kwargs):
        return super().new(backoff_max=self.DEFAULT_BACKOFF_MAX, **kwargs)

def retry_apdapter(retries, session=None, backoff_factor=0.3):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        allowed_methods=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session