from fastapi import  FastAPI, Request
from fastapi.testclient import TestClient
import pytest

from dsr_model_sdk.dsr_sdk import DataSpireSDK
from dsr_model_sdk.topics import EVENT_TOPIC, RESULT_TOPIC
from dsr_model_sdk.message import MessageType

target = "http://localhost:8080" # Kafka Brigde endpoint
kapp = FastAPI()

@kapp.post(f"/topics/{EVENT_TOPIC}")
async def eventTopic(request: Request):
    body = await request.json()
    if body["type"] == MessageType.EVENT.name and body["data"] != None:
        return body["data"]
    
    if body["type"] == MessageType.RESULT.name and body["data"] != None:
        return body["data"]
    
    return {"message": "eventTopic"}

@kapp.post(f"/topics/{RESULT_TOPIC}")
async def resultTopic(request: Request):
    body = await request.json()
    if body["type"] == MessageType.RESULT.name and body["data"] != None:
        return body["data"]
    
    return {"message": "resultTopic"}

kclient = TestClient(kapp)

sdk1 = DataSpireSDK(id= 'model-id-1', name='model-name-1', health_worker=False, target=target, 
                    test_client=kclient
                    )

app = FastAPI()
@app.get("/ping")
def ping():
    return {"message": "Hello World"}

@app.post("/start-session")
def start_session(request: Request):
    sess = sdk1.newSession()
    r = sess.start(request)
    if sess.thread != None:
        sess.thread.join()
    return r

@app.post("/processing")
def processing(request: Request):
    sess = sdk1.newSession()
    sess.start(request)
    if sess.thread != None:
        sess.thread.join()

    r = sess.processing(request=request, data={"message": "I'm Procession"})
    if sess.thread != None:
        sess.thread.join()
    return r

@app.post("/completed")
def completed(request: Request):
    sess = sdk1.newSession()

    sess.start(request)
    if sess.thread != None:
        sess.thread.join()

    r = sess.processing(request=request, data={"message": "I'm Procession"})
    if sess.thread != None:
        sess.thread.join()

    r = sess.completed(request=request, data={"message": "this is the result"})
    if sess.thread != None:
        sess.thread.join()

    return r

@app.post("/failed")
def failed(request: Request):
    sess = sdk1.newSession()

    sess.start(request)
    if sess.thread != None:
        sess.thread.join()

    r = sess.processing(request=request, data={"message": "I'm Procession"})
    if sess.thread != None:
        sess.thread.join()

    r = sess.failed(request=request, error={"message": "this is a failed request"})
    if sess.thread != None:
        sess.thread.join()

    sess.close()
    r = sess.processing(request=request, data={"message": "I'm Procession"})
    assert sess.closed == True

    return r


@app.post("/result")
def result(request: Request):
    sess = sdk1.newSession()

    sess.start(request)
    if sess.thread != None:
        sess.thread.join()

    r = sess.processing(request=request, data={"message": "I'm Procession"})
    if sess.thread != None:
        sess.thread.join()

    r = sess.result(request=request, path="s3://result")
    sess.close()
    assert sess.closed == True

    return r

client = TestClient(app)

# ===========================
def test_ping():
    response = client.get("/ping", headers={"Authorization": "Other foobar"})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Hello World"}

def test_start_sesssion():
    response = client.post("/start-session", headers={"Authorization": "Other foobar"})
    if response != None and response.json() != None:
        assert response.status_code == 200, response.text
        assert response.json() == {'event': 'PREDICT_START'}

def test_processing_event():
    response = client.post("/processing", headers={"Authorization": "Other foobar"})
    if response != None and response.json() != None:
        assert response.status_code == 200, response.text
        assert response.json() == {'event': 'PREDICT_PROCESSING', "message": "I'm Procession"}

def test_completed_event():
    response = client.post("/completed", headers={"Authorization": "Other foobar"})
    if response != None and response.json() != None:
        assert response.status_code == 200, response.text
        assert response.json() == {'event': 'PREDICT_COMPLETED', "result":{"message": "this is the result"}}

def test_failed_event():
    response = client.post("/failed", headers={"Authorization": "Other foobar"})
    if response != None and response.json() != None:
        assert response.status_code == 200, response.text
        assert response.json() == {'event': 'PREDICT_FAILED', "error":{"message": "this is a failed request"}}

def test_session_close():
    response = client.post("/failed", headers={"Authorization": "Other foobar"})
    assert response.status_code == 200, response.text
    assert response.json() == None

def test_send_result():
    response = client.post("/result", headers={"Authorization": "Other foobar"})
    assert response.status_code == 200, response.text
    assert response.json() == {'path': "s3://result", 'json': None}
