import zmq
import uuid
import threading

from datetime import datetime
from time import sleep

from src.core.common import *
from src.core.dht import LTS_DHT
from src.core.message import *
from src.core.memory import LTS_Memory

# ------------------------------------------------------------------------------

class LTS_Agent(LTS_BaseClass):

    def __init__(self, uuid, name=None,
                 zmq_bind="tcp://*:5555", zmq_address="tcp://localhost:5555",
                 zmq_seed_uuid=None, zmq_seed_address=None,
                 memory_capacity = 64,
                 running = True):

        super().__init__("LTS_Agent")
        self.uuid = uuid
        self.name = name
        if not self.name:
            self.name = str(uuid)

        self.zmq_bind = zmq_bind
        self.zmq_address = zmq_address
        self.zmq_seed_uuid = zmq_seed_uuid
        self.zmq_seed_address = zmq_seed_address

        self.zmq_context = zmq.Context()
        self.zmq_socket_rep = self.zmq_context.socket(zmq.REP)
        self.zmq_socket_rep.bind(self.zmq_bind)

        self.dht = LTS_DHT(self.uuid)
        self.dht.add(self.uuid, self.zmq_address)
        if self.zmq_seed_uuid == self.uuid:
            self.zmq_seed_address = self.zmq_address
        else:
            self.dht.add(self.zmq_seed_uuid, zmq_seed_address)

        self.memory = LTS_Memory(capacity = memory_capacity)

            
        self.running_lock = threading.Lock()
        self.setRunning(running)

        if self.getRunning():
            self.pid = threading.Thread(target=self.run)
            self.pid.start()


    def toJSON(self):
        res = '{"class_name": "LTS_Agent", "uuid": "'+self.uuid+'", "name": "'+self.name+'", "zmq_bind": "'+self.zmq_bind+'", "zmq_address": "'+self.zmq_address+'", "zmq_seed_uuid": "'+self.zmq_seed_uuid+'", "zmq_seed_address": "'+self.zmq_seed_address+'", "dht": '+self.dht.toJSON()+'}'
        return json.dumps(json.loads(res), sort_keys=True, indent=4)

    def getRunning(self):
        self.running_lock.acquire()
        res = self.running
        self.running_lock.release()
        return res

    def setRunning(self, running):
        self.running_lock.acquire()
        self.running = running
        self.running_lock.release()


    def run(self):
        logging.info("Agent " + self.uuid + " (" + self.name + ") running")
        while self.getRunning():
            message = self.processMessage(self.zmq_socket_rep.recv())
            response = self.dispatchMessage(message)
            self.zmq_socket_rep.send_string(response.toJSON())

        logging.info("Agent " + self.uuid + " (" + self.name + ") terminating")

    def processMessage(self, message_str):
        message = LTS_Message(LTS_MessageType.NONE, "{}")
        message.fromJSON(message_str)
        return message

    def dispatchMessage(self, message):
        response = LTS_Message(LTS_MessageType.ACK, "{}",
                               from_uuid=self.uuid, to_uuid=message.from_uuid)

        if message.message_type == LTS_MessageType.TERMINATE:
            self.terminate()

        elif message.message_type == LTS_MessageType.DHT_GET_PEER:
            response = self.dht.dispatchGetPeer(message)

        elif message.message_type == LTS_MessageType.DHT_SUBSCRIBE:
            content_json = json.loads(message.content)
            if content_json and 'uuid' in content_json:
                self.dht.add(content_json['uuid'], content_json['address'])
                logging.info("Agent " + self.uuid + " (" + self.name + ") added " + content_json['uuid'] + " (" + content_json['address'] + ") to DHT")

        else:
            logging.error("Agent " + self.uuid + " received message from " + message.from_uuid + " with unknown type " + str(message.message_type))
            response.content = "false"
            self.terminate()

        return response
            

    def sendMessage(self, to_uuid, message):
        response = LTS_Message(LTS_MessageType.NONE, "{}")
        socket = self.zmq_context.socket(zmq.REQ)
        to_address = self.dht.getAddress(to_uuid)
        if to_address:
            socket.connect(to_address)
            start = datetime.now()
            socket.send_string(message.toJSON())
            recv_str = socket.recv()
            response.fromJSON(recv_str)
            end = datetime.now()
            latency = end - start
            self.dht.setLatency(to_uuid, latency.microseconds)
            logging.info("Agent " + self.uuid + " (" + self.name + ") latency " + str(latency.microseconds) + " microseconds with " + to_uuid)
        else:
            logging.warning("Agent " + self.uuid + " send to agent " + to_uuid + " not in DHT")
        return response


    def terminate(self):
        message = LTS_Message(LTS_MessageType.TERMINATE, "{}",
                              from_uuid=self.uuid)
        for key, value in self.dht.dht.items():
            if value.uuid != self.uuid:
                message.to_uuid = value.uuid
                self.sendMessage(message.to_uuid, message)

        self.setRunning(False)

    # ask a peer for another peer
    def populate(self):
        best_uuid, _ = self.dht.getPeerBestLatency()
        message = LTS_Message(LTS_MessageType.DHT_GET_PEER, "{}",
                              from_uuid=self.uuid, to_uuid = best_uuid)
        response = self.sendMessage(message.to_uuid, message)
        response_json = json.loads(json.loads(response.toJSON())['content'])
        if response_json and 'uuid' in response_json:
            self.dht.add(response_json['uuid'], response_json['address'])
            logging.info("Agent " + self.uuid + " (" + self.name + ") added " + response_json['uuid'] + " (" + response_json['address'] + ") to DHT")
        return response_json['uuid']


    # send self uuid and address to an other peer to be added to its DHT
    def subscribe(self, to_uuid):
        message = LTS_Message(LTS_MessageType.DHT_SUBSCRIBE, '{"uuid": "' + self.uuid + '", "address": "' + self.zmq_address + '"}', from_uuid=self.uuid, to_uuid=to_uuid)
        response = self.sendMessage(message.to_uuid, message)
        

# ------------------------------------------------------------------------------



if __name__ == "__main__":
    common = LTS_Common()

    charles_uuid = str(uuid.uuid4())
    charles_address = "tcp://localhost:5555"
    charles = LTS_Agent(charles_uuid, "Charles", zmq_seed_uuid=charles_uuid)

    alice_uuid = str(uuid.uuid4())
    alice_address = "tcp://localhost:5556"
    alice = LTS_Agent(alice_uuid, "Alice",
                      zmq_bind="tcp://*:5556", zmq_address="tcp://localhost:5556",
                      zmq_seed_uuid=charles_uuid, zmq_seed_address=charles_address,
                      running = True)

    bob = LTS_Agent(str(uuid.uuid4()), "Bob",
                    zmq_bind="tcp://*:5557", zmq_address="tcp://localhost:5557",
                    zmq_seed_uuid=alice_uuid, zmq_seed_address=alice_address,
                    running = True)

    sleep(1)
    new_uuid = bob.populate()
    bob.subscribe(new_uuid)
    
    sleep(4)
    alice.terminate()
    
    print(charles.toJSON())
    print(alice.toJSON())
    print(bob.toJSON())
    
    exit(0)
