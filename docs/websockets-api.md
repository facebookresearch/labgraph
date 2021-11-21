# WebSockets API

WebSocket API is the preferred way to build up browser-based applications in LabGraph. The structure of this wiki can be found below:

* [**Connecting to LabGraph**](#connect)
* [**API Requests**](#API-Requests)
* [**API Errors**](#API-Errors)
* [**API Input/Output Streams**](#API-Input-Output-Streams)

API Requests and API Input Streams are sent to LabGraph, and API Output Streams are sent back to the application over WebSocket in JSON format. Documentation of our current APIs reside in the subpages to this wiki.


## Connecting to LabGraph

To **connect** an application to the API layer, your application should open a WebSocket at the port and IP that LabGraph is running on. The default IP is localhost, and the default port is 9000. When an application opens a WebSocket connection to LabGraph, an API Session is started, and API Messages can be sent to and from LabGraph and the application.

## API Requests
### Requesting API Output Streams

To open an input or output stream using **API-Requests**, applications should send a `StartStreamRequest` message, which specifies the name of the stream to be opened. Stream names are specified entirely in the config, and any LabGraph user may write transformers that take or output any API stream with any name, as long as that name is unique in the config.

**`StartStreamRequest`**
```
{
   "api_version": "0.1",
   "api_request": {
     "request_id": RequestId,
     "start_stream_request": {
       "stream_id": StreamId,
       "app_id": ApplicationName,
        StreamName: {
        }
     }
   }
}
```
* request_id: (integer) allows LabGraph to match the response to the request to the request itself. That is, the request_id in the in the response for any request will match the request_id sent in the request. Should be unique within a Session, but this is not enforced. Applies for all request types.
* stream_id: (string) uniquely identifies the stream within a Session and is set by the application.
* app_id: (string) optional, used in Terminal output of LabGraph to provide more information to users. Should identify the application making the request and is set by the application.
* StreamName: (string) This could either be the namespaced input or output stram name.

On receipt of a `StartStreamRequest`, LabGraph will send a `StartStreamEvent` back to the application. If there is an error, LabGraph will send back an `ErrorEvent` (API Errors) message. The format of a `StartStreamEvent` is the following:

**`StartStreamEvent`**
```
{
   "api_version": 0.1,
   "api_event": {
     "request_id": RequestId,
     "start_stream_event": {
       "stream_id": StreamId
     }
   }
 }
```
### Requesting API Output Streams

To end a stream, an application should either send an `EndStreamRequest` or terminate the WebSocket connection. The format of an `EndStreamRequest` is the following:

**`EndStreamRequest`**
```
{
   "api_version": 0.1,
   "api_request": {
     "request_id": RequestId,
     "end_stream_request": {
       "stream_id": StreamId
     }
   }
 }
```
* request_id: (integer) corresponds to the request_id used in the `StartStreamRequest`.
* stream_id: (string) corresponds to the stream_id used in the `StartStreamRequest`.

On receipt of an EndStreamRequest, LabGraph will send an EndStreamEvent back to the application. If there is an error, LabGraph will send back an ErrorEvent (Errors: Websocket APIs) message. The format of an EndStreamEvent is the following:

**`EndStreamEvent`**
```
{
   "api_version": 0.1,
   "api_event": {
     "request_id": RequestId,
     "end_stream_event": {
       "stream_id": StreamId
     }
   }
 }
```

## API Errors
LabGraph will send an error message to your application under a variety of circumstances. Error codes are listed and described here: API Error Codes (websockets-api-errors.md)

**`ErrorEvent`**
```
{
   "api_version": 0.1,
   "api_event": {
     "request_id": RequestId,
     "error_event": {
       "error_code": ErrorCode
       "desc": ErrorDescription
     }
   }
 }
```

## API Input/Output Streams
Input/Output stream messages should be sent in the following format, where individual samples must be JSON parsable.

**Input/Output `StreamBatch`**
```
{
  "api_version": 0.1,
  "stream_batch": {
    "stream_id": StreamId,
    StreamName: {
      "samples": [ArrayOfJSONObjects],
      "batch_num": BatchNum
    }
  }
}
```

## Example Usage
Step 1: Run WebSocket Server
```
python -m labgraph.websockets.ws_server.tests.test_server_local
```
Step 2: Run WebSocket Client
```
python -m labgraph.websockets.ws_client.tests.test_ws_node_client
```
Note: In case webSocket server has not been terminated properly, terminate the process using:
```
sudo pkill -9 python
```
