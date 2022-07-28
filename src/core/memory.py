

from src.core.common import *

# ------------------------------------------------------------------------------

class LTS_Chunk(LTS_BaseClass):

    def __init__(self, unique_id, agent_uuid=None, version=0, content=None):
        super().__init__("LTS_Chunk")
        self.unique_id = unique_id
        self.agent_uuid = agent_uuid
        self.version = version
        self.content = content

    def fromJSON(self, chunk_str):
        obj = json.loads(chunk_str)
        self.unique_id = obj['unique_id']
        self.agent_uuid = obj['agent_uuid']
        self.version = obj['version']
        self.content = obj['content']

    def copyMetadata(self, chunk):
        self.agent_uuid = chunk.agent_uuid
        self.version = chunk.version

# ------------------------------------------------------------------------------

class LTS_Memory(LTS_BaseClass):

    def __init__(self, uuid=None, capacity = 1, name="main_memory"):
        super().__init__("LTS_Memory")
        self.uuid = uuid
        self.name = name
        self.capacity = capacity
        self.memory = dict()
        logging.info("Creating memory " + str(self.uuid) + " (" + self.name + ") with capacity " + str(self.capacity))

    def addChunk(self, chunk):
        res = None
        if len(self.memory) < self.capacity:
            self.memory[chunk.unique_id] = chunk
            res = chunk.unique_id
        return res

    def getChunk(self, unique_id):
        chunk = None
        if unique_id in self.memory:
            chunk = self.memory[unique_id]
        return chunk

    def getChunkMetadata(self, unique_id):
        chunkmd = None
        if unique_id in self.memory:
            chunk = self.memory[unique_id]
            chunkmd = LTS_Chunk(unique_id)
            chunkmd.copyMetadata(chunk)
        return chunkmd

    def removeChunk(self, unique_id):
        chunk = self.getChunk(unique_id)
        if chunk:
            del self.memory[unique_id]
        return chunk

    def firstTouch(self, unique_id, agent_uuid, content):
        chunk = LTS_Chunk(unique_id, agent_uuid=agent_uuid, content=content)
        return self.addChunk(chunk)
    
    def toString(self):
        res = "LTS_Memory {"
        for key, chunk in self.memory.items():
            res = res + str(key) + ", "
        res = res + "}"
        return res





if __name__ == "__main__":
    common = LTS_Common()

    chunk = LTS_Chunk(42)
    print(chunk.toJSON())
    memory = LTS_Memory()
    memory.addChunk(chunk)
    print(memory.toJSON())
    print(memory.toString())
    memory.addChunk(chunk)
    print(memory.toJSON())
    print(memory.toString())
    memory.removeChunk(chunk.unique_id)
    print(memory.toJSON())
    print(memory.toString())

    chunk2 = LTS_Chunk(0)
    chunk2.fromJSON("{\n    \"agent_uuid\": \"1062dd51-d234-426c-9009-cb9b1a67b42f\",\n    \"class_name\": \"LTS_Chunk\",\n    \"content\": \"64\",\n    \"unique_id\": \"x\",\n    \"version\": 1\n}")
    print(chunk2.toJSON())

    
    exit(0)
