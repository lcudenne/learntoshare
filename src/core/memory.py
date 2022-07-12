

from src.core.common import *

# ------------------------------------------------------------------------------

class LTS_Chunk(LTS_BaseClass):

    def __init__(self, unique_id):
        super().__init__("LTS_Chunk")
        self.unique_id = unique_id
        self.content = None

# ------------------------------------------------------------------------------

class LTS_Memory(LTS_BaseClass):

    def __init__(self, capacity = 1, name="main_memory"):
        super().__init__("LTS_Memory")
        self.capacity = capacity
        self.memory = dict()
        logging.info("Creating memory with capacity " + str(self.capacity))

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
    
    def removeChunk(self, unique_id):
        chunk = self.getChunk(unique_id)
        if chunk:
            del self.memory[unique_id]
        return chunk
    
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

    exit(0)
