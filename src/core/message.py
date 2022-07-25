
from enum import Enum

from src.core.common import *


# ------------------------------------------------------------------------------

class LTS_MessageType(str, Enum):
    NONE="NONE"
    ACK="ACK"
    RESPONSE="RESPONSE"
    TERMINATE="TERMINATE"
    DHT_GET_PEER="DHT_GET_PEER"
    DHT_SUBSCRIBE="DHT_SUBSCRIBE"
    DHT_SEARCH_PEER="DHT_SEARCH_PEER"

# ------------------------------------------------------------------------------

class LTS_Message(LTS_BaseClass):

    def __init__(self, message_type, content, from_uuid=None, to_uuid=None):

        super().__init__("LTS_Message")
        self.message_type = message_type
        self.content = content
        self.from_uuid = from_uuid
        self.to_uuid = to_uuid

    def fromJSON(self, message_str):
        obj = json.loads(message_str)
        self.message_type = obj['message_type']
        self.content = obj['content']
        self.from_uuid = obj['from_uuid']
        self.to_uuid = obj['to_uuid']
        
# ------------------------------------------------------------------------------



if __name__ == "__main__":
    common = LTS_Common()

    m = LTS_Message(LTS_MessageType.TERMINATE, "terminate")
    print(m.toJSON())

    exit(0)
