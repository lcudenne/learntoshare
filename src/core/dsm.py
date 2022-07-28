
import uuid

from time import sleep

from src.core.common import *
from src.core.agents import LTS_Agent
from src.core.memory import LTS_Memory, LTS_Chunk
from src.core.message import *

# ------------------------------------------------------------------------------

class LTS_DSM(LTS_BaseClass):

    def __init__(self, name=None,
                 zmq_bind="tcp://*:5555", zmq_address="tcp://localhost:5555",
                 zmq_seed_uuid=None, zmq_seed_address=None, zmq_recv_timeout_sec=10,
                 memory_capacity = 64,
                 running = True):

        common = LTS_Common()
        super().__init__("LTS_DSM")
        self.uuid = str(uuid.uuid4())
        self.name = name
        if not self.name:
            self.name = str(uuid)

        self.agent = LTS_Agent(self.uuid, self.name,
                               zmq_bind, zmq_address,
                               zmq_seed_uuid, zmq_seed_address, zmq_recv_timeout_sec,
                               running, dispatch_handler=self)

        self.memory = LTS_Memory(uuid=self.uuid, name=self.name, capacity = memory_capacity)


    def toJSON(self):
        return "{}"




    def write(self, chunk_id, content):
        res = None
        chunk = self.memory.getChunk(chunk_id)
        if chunk:
            chunk.content = content
            chunk.version = chunk.version + 1
            res = chunk_id
        else:
            logging.info("DSM " + self.uuid + " (" + self.name + ") writes chunk " + chunk_id + " in memory first touch")
            res = self.memory.firstTouch(chunk_id, self.uuid, content)
        return res
            

    def read(self, chunk_id):
        content = None
        chunk = self.memory.getChunk(chunk_id)
        if chunk:
            content = chunk.content
        else:
            logging.warning("DSM " + self.uuid + " (" + self.name + ") reads chunk " + chunk_id + " not in memory")
        return content


    def dispatchMessage(self, message):
        response = LTS_Message(LTS_MessageType.CORE_ACK,
                               from_uuid=self.uuid, to_uuid=message.from_uuid)

        if message.message_type == LTS_MessageType.DSM_ADVERTIZE:
            chunk = LTS_Chunk(0)
            chunk.fromJSON(message.content)
            self.memory.addChunk(chunk)
        else:
            logging.error("DSM " + self.uuid + " (" + self.name + ") received message from " + message.from_uuid + " with unknown DSM type " + str(message.message_type))

        return response



    
    def advertize(self, chunk_id):
        chunk = self.memory.getChunkMetadata(chunk_id)
        if chunk:
            message = LTS_Message(LTS_MessageType.DSM_ADVERTIZE, from_uuid=self.uuid,
                                  content=chunk.toJSON())
            self.agent.communicator.broadcast(message)

    
# ------------------------------------------------------------------------------



if __name__ == "__main__":

    dsm = LTS_DSM("dsm_instance")
    dsm2 = LTS_DSM("dsm_instance2",
                   zmq_bind="tcp://*:5556", zmq_address="tcp://localhost:5556",
                   zmq_seed_uuid=dsm.uuid, zmq_seed_address="tcp://localhost:5555")

    dsm.write("x", "51")
    print(dsm.memory.toJSON())
    dsm.write("x", "64")
    print("x is", dsm.read("x"))
    print("y is", dsm.read("y"))


    print(dsm.memory.toJSON())
    sleep(4)    
    dsm2.write("x", "16")
    dsm2.advertize("x")
    print(dsm.memory.toJSON())

    
    exit(0)
