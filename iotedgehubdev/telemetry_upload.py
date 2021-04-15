# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import urllib.request as HTTPClient
import sys
import json

from applicationinsights import TelemetryClient
from applicationinsights.exceptions import enable
from applicationinsights.channel import SynchronousSender, SynchronousQueue, TelemetryChannel
from iotedgehubdev import decorators


class LimitedRetrySender(SynchronousSender):
    def __init__(self):
        super(LimitedRetrySender, self).__init__()

    def send(self, data_to_send):
        """ Override the default resend mechanism in SenderBase. Stop resend when it fails."""
        request_payload = json.dumps([a.write() for a in data_to_send])

        request = HTTPClient.Request(self._service_endpoint_uri, bytearray(request_payload, 'utf-8'),
                                     {'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8'})
        try:
            HTTPClient.urlopen(request, timeout=10)
        except Exception:  # pylint: disable=broad-except
            pass


@decorators.suppress_all_exceptions()
def upload(data_to_save):
    try:
        data_to_save = json.loads(data_to_save)
    except Exception:
        pass

    for instrumentation_key in data_to_save:
        client = TelemetryClient(instrumentation_key=instrumentation_key,
                                 telemetry_channel=TelemetryChannel(queue=SynchronousQueue(LimitedRetrySender())))
        enable(instrumentation_key)
        for record in data_to_save[instrumentation_key]:
            name = record['name']
            raw_properties = record['properties']
            properties = {}
            measurements = {}
            for k, v in raw_properties.items():
                if isinstance(v, str):
                    properties[k] = v
                else:
                    measurements[k] = v
            client.track_event(name, properties, measurements)
        client.flush()


if __name__ == '__main__':
    # If user doesn't agree to upload telemetry, this scripts won't be executed. The caller should control.
    upload(sys.argv[1])
