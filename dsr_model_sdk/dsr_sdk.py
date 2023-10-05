from dsr_model_sdk.session import Session
from dsr_model_sdk.singleton import SingletonMeta
from dsr_model_sdk.logger import logger
from dsr_model_sdk.jobs import send_health_to_target
from dsr_model_sdk.topics import HEALTH_TOPIC
from apscheduler.schedulers.background import BackgroundScheduler

class DataSpireSDK(metaclass=SingletonMeta):
    """
    This is a thread-safe implementation of Singleton.
    """
    id: str
    ping_worker = 0
    scheduler = BackgroundScheduler()

    def __init__(
        self,
        id: str,
        name: str,
        health_worker: bool = True,
        test_client = None,
        dev_mode: bool = False, 
        target: str = "http://kafka-bridge-bridge-service.kafka.svc.cluster.local:8080"
    ) -> None:
        logger.info("Init DataSpire SDK")
        self.id = id
        self.name = name
        self.target = target
        self.test_client = test_client
        self.dev_mode = dev_mode
        if health_worker and dev_mode == False:
            self.scheduler.add_job(func=send_health_to_target, args=[self.id, self.name, self.target + "/topics/" + HEALTH_TOPIC], trigger='interval', seconds=20, max_instances=8)
            self.start_health_worker()
        
    def start_health_worker(self):
        if self.ping_worker > 0:
            logger.info("There is a health workder working")
            return
        else:
            self.scheduler.start()
            self.ping_worker += 1
            logger.info("Start worker send health message to target")

    def newSession(self) -> Session:
        return Session(sdk_metadata={"id": self.id, "name": self.name}, target=self.target, test_client=self.test_client, dev_mode=self.dev_mode)