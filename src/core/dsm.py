
import uuid

from src.core.common import *
from src.core.communicator import *
from src.core.memory import LTS_Memory, LTS_Chunk

# ------------------------------------------------------------------------------

class LTS_DSM(LTS_BaseClass):

    def __init__(self, dsm_uuid=None, communicator=None, memory_capacity = 64):

        super().__init__("LTS_DSM")
        self.uuid = dsm_uuid or str(uuid.uuid4())

        logging.info("[DSM] "+self.uuid+" DSM running")

        self.communicator = communicator

        self.memory = LTS_Memory(memory_uuid=self.uuid,
                                 capacity = memory_capacity)


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
            logging.info("[DSM] "+self.uuid+" Writing chunk " + chunk_id + " in memory first touch")
            res = self.memory.firstTouch(chunk_id, self.uuid, content)
        return res
            

    def read(self, chunk_id):
        content = None
        chunk = self.memory.getChunk(chunk_id)
        if chunk:
            if chunk.content is not None:
                content = chunk.content
            else:
                if chunk.agent_uuid is not None and chunk.agent_uuid != self.uuid:
                    logging.info("[DSM] "+self.uuid+" Asking agent " + chunk.agent_uuid + " for chunk " + chunk.uuid)
                    message = LTS_Message(LTS_MessageType.DSM_CHUNK_GET,
                                          from_uuid=self.uuid, to_uuid=chunk.agent_uuid,
                                          content=chunk.toJSON())
                    response = self.communicator.sendMessage(chunk.agent_uuid, message)
                    chunk.fromJSON(response.content)
                    content = chunk.content
        else:
            logging.warning("[DSM] "+self.uuid+" Reading chunk " + chunk_id + " not in memory")
        return content


    def dispatchMessage(self, message):
        response = LTS_Message(LTS_MessageType.CORE_ACK,
                               from_uuid=self.uuid, to_uuid=message.from_uuid)

        if message.message_type == LTS_MessageType.DSM_CHUNK_ADVERTIZE:
            chunk = LTS_Chunk()
            chunk.fromJSON(message.content)
            self.memory.addChunk(chunk)
        elif message.message_type == LTS_MessageType.DSM_CHUNK_GET:
            chunkmd = LTS_Chunk()
            chunkmd.fromJSON(message.content)
            chunk = self.memory.getChunk(chunkmd.uuid)
            if chunk:
                response.content = chunk.toJSON()
            else:
                response.content = message.content
        else:
            logging.error("[DSM] "+self.uuid+" Receiving message from " + message.from_uuid + " with unknown DSM type " + str(message.message_type))

        return response



    
    def advertize(self, chunk_id):
        chunk = self.memory.getChunkMetadata(chunk_id)
        if chunk:
            message = LTS_Message(LTS_MessageType.DSM_CHUNK_ADVERTIZE, from_uuid=self.uuid,
                                  content=chunk.toJSON())
            self.communicator.broadcastMessage(message)

    
# ------------------------------------------------------------------------------



if __name__ == "__main__":
    
    exit(0)
