import os
import sys

# Work like a charm
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

from dsr_model_sdk import DataSpireSDK

class TestDataSpireSDK():
    id = 'data-spire-sdk-1'
    name = 'object-detectio'
    sdk1 = DataSpireSDK(id=id, name=name, health_worker=True)

    def test_singleton(self):
        """
        There is only one DataSpireSDK class can be created
        """
        sdk1 = self.sdk1
        sdk2 = DataSpireSDK(id='data-spire-sdk-2', health_worker=True)
        assert sdk1.id == sdk2.id

    def test_only_one_health_worker(self):
        """
        There is only one health worker can run
        """
        sdk1 = self.sdk1
        sdk1.start_health_worker()
        assert sdk1.ping_worker == 1

    def test_create_difference_session(self):
        """
        Should create difference sessions each time  
        """
        sdk = self.sdk1
        sess1 = sdk.newSession()
        sess2 = sdk.newSession()
        assert sess1.session["id"] != sess2.session['id']