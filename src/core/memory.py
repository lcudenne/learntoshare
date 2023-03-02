import uuid

from src.core.common import *

# ------------------------------------------------------------------------------

class LTS_Chunk(LTS_BaseClass):

    def __init__(self, chunk_uuid=None, agent_uuid=None, version=0, content=None):
        super().__init__("LTS_Chunk")
        if chunk_uuid:
            self.uuid = chunk_uuid
        else:
            self.uuid = str(uuid.uuid4())
        self.agent_uuid = agent_uuid
        self.version = version
        self.content = content

    def fromJSON(self, chunk_str):
        obj = json.loads(chunk_str)
        self.uuid = obj['uuid']
        self.agent_uuid = obj['agent_uuid']
        self.version = obj['version']
        self.content = obj['content']

    def copyMetadata(self, chunk):
        self.agent_uuid = chunk.agent_uuid
        self.version = chunk.version

# ------------------------------------------------------------------------------

class LTS_Memory(LTS_BaseClass):

    def __init__(self, memory_uuid=None, capacity = 1, name="main_memory"):
        super().__init__("LTS_Memory")
        self.uuid = memory_uuid
        self.name = name
        self.capacity = capacity
        self.memory = dict()
        logging.info("[MEM] "+self.uuid+" Memory with capacity " + str(self.capacity))

    def addChunk(self, chunk):
        res = None
        if len(self.memory) < self.capacity:
            self.memory[chunk.uuid] = chunk
            res = chunk.uuid
        return res

    def getChunk(self, uuid):
        chunk = None
        if uuid in self.memory:
            chunk = self.memory[uuid]
        return chunk

    def getChunkMetadata(self, uuid):
        chunkmd = None
        if uuid in self.memory:
            chunk = self.memory[uuid]
            chunkmd = LTS_Chunk(uuid)
            chunkmd.copyMetadata(chunk)
        return chunkmd

    def removeChunk(self, uuid):
        chunk = self.getChunk(uuid)
        if chunk:
            del self.memory[uuid]
        return chunk

    def firstTouch(self, uuid, agent_uuid, content):
        chunk = LTS_Chunk(uuid, agent_uuid=agent_uuid, content=content)
        return self.addChunk(chunk)
    
    def toString(self):
        res = "LTS_Memory {"
        for key, chunk in self.memory.items():
            res = res + str(key) + ", "
        res = res + "}"
        return res





if __name__ == "__main__":
    common = LTS_Common()

    chunk = LTS_Chunk()
    print(chunk.toJSON())
    memory = LTS_Memory()
    memory.addChunk(chunk)
    print(memory.toJSON())
    print(memory.toString())
    memory.addChunk(chunk)
    print(memory.toJSON())
    print(memory.toString())
    memory.removeChunk(chunk.uuid)
    print(memory.toJSON())
    print(memory.toString())

    chunk2 = LTS_Chunk()
    chunk2.fromJSON("{\n    \"agent_uuid\": \"1062dd51-d234-426c-9009-cb9b1a67b42f\",\n    \"class_name\": \"LTS_Chunk\",\n    \"content\": \"64\",\n    \"uuid\": \"x\",\n    \"version\": 1\n}")
    print(chunk2.toJSON())

    
    exit(0)
