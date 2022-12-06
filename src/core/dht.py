from datetime import datetime

from src.core.common import *
from src.core.message import *

# ------------------------------------------------------------------------------

class LTS_DHTEntry(LTS_BaseClass):

    def __init__(self, uuid, zmq_address, latency_us=0):
        super().__init__("LTS_DHTEntry")
        self.uuid = uuid
        self.zmq_address = zmq_address
        self.latency_us = latency_us
        self.timestamp_create = datetime.now()
        
# ------------------------------------------------------------------------------

class LTS_DHT(LTS_BaseClass):

    def __init__(self, dht_uuid):
        super().__init__("LTS_DHT")
        self.uuid = dht_uuid
        self.dht = dict()

    def add(self, uuid, zmq_address, latency_us=0):
        entry = LTS_DHTEntry(uuid, zmq_address, latency_us)
        self.dht[uuid] = entry
        logging.info("[DHT] Peer " + self.uuid + " DHT ADD " + uuid + " " + zmq_address)


    def getAddress(self, uuid):
        res = None
        if uuid in self.dht:
            res = self.dht[uuid].zmq_address
        return res

    def getLatency(self, uuid):
        res = None
        if uuid in self.dht:
            res = self.dht[uuid].latency_us
        return res

    def setLatency(self, uuid, latency_us):
        res = None
        if uuid in self.dht:
            res = self.dht[uuid].latency_us
            self.dht[uuid].latency_us = latency_us
        return res

    def getPeerBestLatency(self, avoid_uuid=None):
        best_latency = None
        best_address = None
        best_uuid = None
        for key, value in self.dht.items():
            if key != avoid_uuid and key != self.uuid and (best_latency is None or (value.latency_us < best_latency and value.latency_us != 0)):
                best_latency = value.latency_us
                best_address = value.zmq_address
                best_uuid = key
        return best_uuid, best_address
                
    def toJSON(self):
        res = '{"class_name": "LTS_DHT", "dht": {'
        i = 0
        for key, value in self.dht.items():
            res = res + '"'+str(key)+'": {"uuid": "'+str(value.uuid)+'", "zmq_address": "'+str(value.zmq_address)+'", "latency_us": '+str(value.latency_us)+', "timestamp_create": "'+str(value.timestamp_create)+'"}'
            i = i + 1
            if i < len(self.dht):
                res = res + ', '
        res = res + '}}'
        return json.dumps(json.loads(res), sort_keys=True, indent=4)

    def dispatchGetPeer(self, message: LTS_Message):
        best_uuid, best_address = self.getPeerBestLatency(avoid_uuid=message.from_uuid)
        if best_uuid:
            response = LTS_Message(LTS_MessageType.CORE_RESPONSE, '{"uuid": "' + best_uuid + '", "address": "' + best_address + '"}', from_uuid=message.to_uuid)
        else:
            response = LTS_Message(LTS_MessageType.CORE_NONE)
        return response
    

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    common = LTS_Common()

    exit(0)
