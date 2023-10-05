import os
import sys
import time


# Work like a charm
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

from dsr_model_sdk import DataSpireSDK

if __name__ == '__main__':
    sdk1 = DataSpireSDK(id= 'model-id-1', name='model-name-1', health_worker=True, target="http://localhost:8080")

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        sdk1.scheduler.shutdown()

    # sess = sdk1.newSession()
    # sess.start()