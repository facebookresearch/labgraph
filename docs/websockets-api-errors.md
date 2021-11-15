# WebSockets API Error Codes

**`ErrorEvent`**
```
{
  "api_version": 0.1,
  "api_event": {
    "request_id": [REQUEST_ID],
    "error_event": {
      "error_code": [ERROR-CODE]
      "desc": [DESCRIPTION-OF-ERROR]
    }
  }
}
```
There are 7 possible official `error_code` s:

* `InvalidMessageFormat`: If an incoming message is not parsable an ErrorEvent message with this error_code is sent. The desc field will contain more information as to why the message was not parseable. There will be no request_id for all ErrorEvent messages with this code because there is no guarantee the client sent a request_id to begin with
* `MessageNotSupported`: If a client sends a message that is not a valid input message to LabGraph, an ErrorEvent message with this error_code is sent. There will be no request_id for all ErrorEvent messages with this code because there is no guarantee the client sent a request_id to begin with
* `StreamIDNotFound`: If an `EndStreamrequest` is sent for a stream that does not exist, an `ErrorEvent` message with this `error_code` is sent.
*`StreamIDAlreadyExists`: If a `StartStreamrequest` is sent with a `stream_id` that already exists in that particular stream, an `ErrorEvent` message with this `error_code` is sent.
*`NotTrained`: If a `StartStreamRequest` is sent for a stream that hasn't been trained, an `ErrorEvent` with this              `error_code` is sent.
*`StreamAlreadyRequested`: If a `StartStreamRequest` is sent for an input stream that has been requested by another session, an `ErrorEvent` message with this `error_code` is sent.
*`NonExistentStream`: If a `StartStreamRequest` sent for a stream that is not supported by LabGraph, an `ErrorEvent` message with this `error_code` is sent.
