import argparse
import json

from time import sleep

from src.core.common import LTS_Common
from src.core.agents import LTS_Agent

# ------------------------------------------------------------------------------

def p2pskel_argparse():

    parser = argparse.ArgumentParser(
        prog = 'P2P Skeleton',
        description = 'P2P Skeleton',
        epilog = 'https://github.com/lcudenne/learntoshare')

    parser.add_argument("-u", "--uid", type=str, required=False,
                        help="unique id for this agent (default a random uuid4)")
    parser.add_argument("-n", "--name", type=str, required=False,
                        help="name of the agent (default is the uid)")
    parser.add_argument("-b", "--bind", type=str, required=False,
                        help="agent network bind address for incoming messages (default is tcp://*:5555)")
    parser.add_argument("-a", "--address", type=str, required=False,
                        help="agent network address to be used by other peers (default is tcp://localhost:5555)")
    parser.add_argument("-s", "--seeduid", type=str, required=False,
                        help="unique id of the seed used to bootstrap the P2P overlay (default is our own uid)")
    parser.add_argument("-d", "--seedaddress", type=str, required=False,
                        help="network address of the seed to bootstrap the P2P overlay (default is our own address)")

    return parser.parse_args()


# ------------------------------------------------------------------------------


class P2PSkel():

    def __init__(self, parse=False,
                 uid=None,
                 name=None,
                 bind=None,
                 address=None,
                 seeduid=None,
                 seedaddress=None):

        if parse:
            args = p2pskel_argparse()
            self.uid = args.uid
            self.name = args.name
            self.bind = args.bind
            self.address = args.address
            self.seeduid = args.seeduid
            self.seedaddress = args.seedaddress
        else:
            self.uid = uid
            self.name = name
            self.bind = bind
            self.address = address
            self.seeduid = seeduid
            self.seedaddress = seedaddress

        LTS_Common()
        self.overlay = LTS_Agent(agent_uuid=self.uid,
                                 name=self.name,
                                 zmq_bind=self.bind,
                                 zmq_address=self.address,
                                 zmq_seed_uuid=self.seeduid,
                                 zmq_seed_address=self.seedaddress,
                                 dispatch_handler=self)
        print(self.overlay.toJSON())

    def terminate(self):
        self.overlay.terminate()

    def dispatchMessage(self, message):
        content_json = json.loads(message.content)
        print("Received", content_json, "from", message.from_uuid)
        return None



# ------------------------------------------------------------------------------


if __name__ == "__main__":

    p2pskel = P2PSkel(parse=True)
    
    sleep(8)

    p2pskel.terminate()
    
    exit(0)
