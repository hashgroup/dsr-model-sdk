# DataSpire Model SDK

Support AI Engineer an easy way to send the event of AI Model to Kafka topic

## Quick Starts

<div class="termy">

```console
$ pip install dsr-model-sdk

---> 100%
```

</div>

## Example

* Create a file `main.py` with:

```Python
dsr_sdk = DataSpireSDK(id= 'model-id-1',name='model-name-1', health_worker=True, target="kafka-bridge.local")

@app.post("/predict")
def processing(request: Request):
    # Start request 
    sess = dsr_sdk.newSession()
    sess.start(req: request)

    result = {"Result": "result"}
    
    # End request 
    sess.completed(req: request, data=result)
    sess.close()

    return result
```

* Can also send error and processing:

```Python
# Just created one time
dsr_sdk = DataSpireSDK(id= 'model-id-1',name='model-name-1', health_worker=True, target="kafka-bride.local")

@app.post("/predict")
def processing(request: Request):
    # Start request 
    sess = dsr_sdk.newSession()
    sess.start(request)

    result = None

    try:
        sess.processing(req: request, data={"current": 1, "total": 10000})
        sess.processing(req: request, data={"current": 100, "total": 10000})
        sess.processing(req: request, data={"current": 1000, "total": 10000})
        sess.processing(req: request, data={"current": 9999, "total": 10000})

        result = {"Result": "result"}
        # End request 
    except Exception:
        sess.failed(req: request, error={"Exception Error": "Data input format validated failed..."})
    finally:
        sess.close()
    
    return result
```
