
import uuid
import threading

from time import sleep

from src.core.common import *
from src.core.communicator import *

# ------------------------------------------------------------------------------

class LTS_Agent(LTS_BaseClass):

    def __init__(self, agent_uuid, name=None,
                 zmq_bind="tcp://*:5555", zmq_address="tcp://localhost:5555",
                 zmq_seed_uuid=None, zmq_seed_address=None, zmq_recv_timeout_sec=10,
                 running = True,
                 dispatch_handler = None):

        super().__init__("LTS_Agent")
        self.uuid = agent_uuid
        self.name = name
        if not self.name:
            self.name = str(agent_uuid)

        self.dispatch_handler = dispatch_handler

        self.communicator = LTS_Communicator(self.uuid, self.name,
                                             zmq_bind, zmq_address,
                                             zmq_seed_uuid, zmq_seed_address,
                                             zmq_recv_timeout_sec)

        self.running_lock = threading.Lock()
        self.setRunning(running)

        if self.getRunning():
            self.pid = threading.Thread(target=self.run)
            self.pid.start()


    def toJSON(self):
        res = '{"class_name": "LTS_Agent", "uuid": "'+self.uuid+'", "name": "'+self.name+'", "communicator": '+self.communicator.toJSON()+'}'
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
        logging.info("Agent " + self.uuid + " (" + self.name + ") running on " + self.communicator.zmq_address)
        while self.getRunning():
            self.communicator.zmq_socket_rep.RCVTIMEO = self.communicator.zmq_recv_timeout
            data_recv = None
            try:
                data_recv = self.communicator.zmq_socket_rep.recv_string()
            except zmq.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    logging.info("Agent " + self.uuid + " (" + self.name + ") recv timeout")
                    self.setRunning(False)
            if data_recv:
                message = self.communicator.processMessage(data_recv)
                response = self.dispatchMessage(message)
                self.communicator.zmq_socket_rep.send_string(response.toJSON())

        logging.info("Agent " + self.uuid + " (" + self.name + ") terminating")




    def dispatchMessage(self, message):
        logging.info("Agent " + self.uuid + " (" + self.name + ") received message " + str(message.message_type) + " from " + message.from_uuid)
        response = LTS_Message(LTS_MessageType.CORE_ACK,
                               from_uuid=self.uuid, to_uuid=message.from_uuid)

        if message.message_type == LTS_MessageType.CORE_TERMINATE:
            self.terminate()

        elif message.message_type == LTS_MessageType.DHT_GET_PEER:
            response = self.communicator.dht.dispatchGetPeer(message)

        elif message.message_type == LTS_MessageType.DHT_SUBSCRIBE:
            content_json = json.loads(message.content)
            if content_json and 'uuid' in content_json:
                self.communicator.dht.add(content_json['uuid'], content_json['address'])
                logging.info("Agent " + self.uuid + " (" + self.name + ") added " + content_json['uuid'] + " (" + content_json['address'] + ") to DHT")

        elif message.message_type.startswith("DSM_"):
            if self.dispatch_handler:
                response = self.dispatch_handler.dispatchMessage(message)
            else:
                logging.error("Agent " + self.uuid + " (" + self.name + ") received message from " + message.from_uuid + " with DSM type " + str(message.message_type) + " but no dispatch handler is set")


        else:
            logging.error("Agent " + self.uuid + " (" + self.name + ") received message from " + message.from_uuid + " with unknown type " + str(message.message_type))
            self.terminate()

        return response
            



    def terminate(self):
        message = LTS_Message(LTS_MessageType.CORE_TERMINATE,
                              from_uuid=self.uuid)
        self.communicator.broadcast(message)
        self.setRunning(False)



        

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
    new_uuid = bob.communicator.populate()
    bob.communicator.subscribe(new_uuid)
    
    sleep(4)
    alice.terminate()
    
    print(charles.toJSON())
    print(alice.toJSON())
    print(bob.toJSON())
    
    exit(0)
