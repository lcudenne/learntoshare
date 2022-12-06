import zmq

from datetime import datetime


from src.core.common import *
from src.core.dht import LTS_DHT
from src.core.message import *


# ------------------------------------------------------------------------------

class LTS_Communicator(LTS_BaseClass):

    def __init__(self, comm_uuid, name,
                 zmq_bind="tcp://*:5555", zmq_address="tcp://localhost:5555",
                 zmq_seed_uuid=None, zmq_seed_address=None,
                 zmq_recv_timeout_sec=10):

        super().__init__("LTS_Communicator")
        self.uuid = comm_uuid
        self.name = name

        self.zmq_bind = zmq_bind
        self.zmq_address = zmq_address
        self.zmq_seed_uuid = zmq_seed_uuid
        self.zmq_seed_address = zmq_seed_address

        self.zmq_context = zmq.Context()
        self.zmq_socket_rep = self.zmq_context.socket(zmq.REP)
        self.zmq_socket_rep.bind(self.zmq_bind)
        self.zmq_recv_timeout = zmq_recv_timeout_sec * 1000

        self.dht = LTS_DHT(self.uuid)
        self.dht.add(self.uuid, self.zmq_address)
        if self.zmq_seed_uuid == self.uuid or self.zmq_seed_uuid is None:
            self.zmq_seed_uuid = self.uuid
            self.zmq_seed_address = self.zmq_address
        else:
            self.dht.add(self.zmq_seed_uuid, zmq_seed_address)
            self.subscribe(self.zmq_seed_uuid)


    def toJSON(self):
        res = '{"class_name": "LTS_Communicator", "uuid": "'+self.uuid+'", "zmq_bind": "'+self.zmq_bind+'", "zmq_address": "'+self.zmq_address+'", "zmq_seed_uuid": "'+self.zmq_seed_uuid+'", "zmq_seed_address": "'+self.zmq_seed_address+'", "dht": '+self.dht.toJSON()+'}'
        return json.dumps(json.loads(res), sort_keys=True, indent=4)


    
    def processMessage(self, message_str):
        message = LTS_Message(LTS_MessageType.CORE_NONE)
        message.fromJSON(message_str)
        return message


    
    def sendMessage(self, to_uuid, message):
        response = LTS_Message(LTS_MessageType.CORE_NONE)
        socket = self.zmq_context.socket(zmq.REQ)
        to_address = self.dht.getAddress(to_uuid)
        if to_address:
            socket.connect(to_address)
            start = datetime.now()
            socket.send_string(message.toJSON())
            socket.RCVTIMEO = self.zmq_recv_timeout
            data_recv = None
            try:
                data_recv = socket.recv_string()
            except zmq.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    logging.info("[COM] Agent " + self.uuid + " (" + self.name + ") recv timeout")
            if data_recv:
                response.fromJSON(data_recv)
                end = datetime.now()
                latency = end - start
                self.dht.setLatency(to_uuid, latency.microseconds)
                logging.info("[COM] Agent " + self.uuid + " (" + self.name + ") latency " + str(latency.microseconds) + " microseconds with " + to_uuid)

        else:
            logging.warning("[COM] Agent " + self.uuid + " (" + self.name + ") send to agent " + str(to_uuid) + " not in DHT")

        return response


    def send(self, to_uuid, content):
        message = LTS_Message(LTS_MessageType.USER_DEFINED, content=content,
                              from_uuid=self.uuid, to_uuid=to_uuid)
        return self.sendMessage(to_uuid, message)
    
    def broadcastMessage(self, message):
        for key, value in self.dht.dht.items():
            if value.uuid != self.uuid:
                message.to_uuid = value.uuid
                self.sendMessage(message.to_uuid, message)

    def broadcast(self, content):
        message = LTS_Message(LTS_MessageType.USER_DEFINED, content=content, from_uuid=self.uuid)
        self.broadcastMessage(message)

    # ask a peer for another peer
    def populate(self):
        best_uuid, _ = self.dht.getPeerBestLatency()
        message = LTS_Message(LTS_MessageType.DHT_GET_PEER,
                              from_uuid=self.uuid, to_uuid = best_uuid)
        response = self.sendMessage(message.to_uuid, message)
        response_json = json.loads(json.loads(response.toJSON())['content'])
        if response_json and 'uuid' in response_json:
            self.dht.add(response_json['uuid'], response_json['address'])
            logging.info("[NET] Agent " + self.uuid + " (" + self.name + ") added " + response_json['uuid'] + " (" + response_json['address'] + ") to DHT")
            return response_json['uuid']
        else:
            return None


    
    # send self uuid and address to an other peer to be added to its DHT
    def subscribe(self, to_uuid):
        message = LTS_Message(LTS_MessageType.DHT_SUBSCRIBE, '{"uuid": "' + self.uuid + '", "address": "' + self.zmq_address + '"}', from_uuid=self.uuid, to_uuid=to_uuid)
        response = self.sendMessage(message.to_uuid, message)


    

# ------------------------------------------------------------------------------



if __name__ == "__main__":
    common = LTS_Common()

    exit(0)
