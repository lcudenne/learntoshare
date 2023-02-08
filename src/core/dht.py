
import threading

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
        self.dht_lock = threading.Lock()

    def add(self, uuid, zmq_address, latency_us=0):
        entry = LTS_DHTEntry(uuid, zmq_address, latency_us)
        self.dht_lock.acquire()
        self.dht[uuid] = entry
        self.dht_lock.release()
        logging.info("[DHT] "+self.uuid+" Peer DHT ADD " + uuid + " " + zmq_address)

    def remove(self, uuid):
        res = None
        self.dht_lock.acquire()
        if uuid in self.dht:
            res = self.dht[uuid]
            logging.info("[DHT] "+self.uuid+" Peer DHT REMOVE " + uuid + " " + res.zmq_address)
            del self.dht[uuid]
        self.dht_lock.release()
        return res

    def getAddress(self, uuid):
        res = None
        self.dht_lock.acquire()
        if uuid in self.dht:
            res = self.dht[uuid].zmq_address
        self.dht_lock.release()
        return res

    def getLatency(self, uuid):
        res = None
        self.dht_lock.acquire()
        if uuid in self.dht:
            res = self.dht[uuid].latency_us
        self.dht_lock.release()
        return res

    def setLatency(self, uuid, latency_us):
        res = None
        self.dht_lock.acquire()
        if uuid in self.dht:
            res = self.dht[uuid].latency_us
            self.dht[uuid].latency_us = latency_us
        self.dht_lock.release()
        return res

    def getPeerBestLatency(self, avoid_uuid=None):
        best_latency = None
        best_address = None
        best_uuid = None
        self.dht_lock.acquire()
        for key, value in self.dht.items():
            if key != avoid_uuid and key != self.uuid and (best_latency is None or (value.latency_us < best_latency and value.latency_us != 0)):
                best_latency = value.latency_us
                best_address = value.zmq_address
                best_uuid = key
        self.dht_lock.release()
        return best_uuid, best_address

    def getUuidList(self):
        res = list()
        self.dht_lock.acquire()        
        for key, _ in self.dht.items():
            if key != self.uuid:
                res.append(key)
        self.dht_lock.release()
        return res

    
    def toJSON(self):
        res = '{"class_name": "LTS_DHT", "dht": {'
        i = 0
        self.dht_lock.acquire()
        for key, value in self.dht.items():
            res = res + '"'+str(key)+'": {"uuid": "'+str(value.uuid)+'", "zmq_address": "'+str(value.zmq_address)+'", "latency_us": '+str(value.latency_us)+', "timestamp_create": "'+str(value.timestamp_create)+'"}'
            i = i + 1
            if i < len(self.dht):
                res = res + ', '
        res = res + '}}'
        self.dht_lock.release()
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
