import argparse
import json
import queue

from apps.genscng.aiconnector import AIConnector

from src.core.common import LTS_Common
from src.core.agents import LTS_Agent


# ------------------------------------------------------------------------------

def p2p_argparse():

    parser = argparse.ArgumentParser(
        prog = 'Generative Scene Graph',
        description = 'Peer-to-peer Generative Scene Graph',
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
    parser.add_argument("-i", "--image", type=str, required=False,
                        help="path to an input single image")
    parser.add_argument("-o", "--output", type=str, required=False,
                        help="path to the output image (default is $PWD/output)")
    parser.add_argument("-r", "--rounds", type=int, required=False,
                        help="number of rounds for consensus")
    parser.add_argument("-j", "--stablediffusion", type=str, required=False,
                        help="http address to automatic1111 stable diffusion service (default is http://127.0.0.1:7860)")
    parser.add_argument("-w", "--sduser", type=str, required=False,
                        help="username for automatic1111 stable diffusion service (default is user)")
    parser.add_argument("-p", "--sdpassw", type=str, required=False,
                        help="password for automatic1111 stable diffusion service (default is password)")

    return parser.parse_args()


    

# ------------------------------------------------------------------------------

class GenScnG():

    def __init__(self, parse=True):

        self.uid = None
        self.name = None
        self.bind = None
        self.address = None
        self.seeduid = None
        self.seedaddress = None
        self.image = None
        self.output = "output"
        self.stablediffusion = "http://127.0.0.1:7860"
        self.sduser = "user"
        self.sdpassw = "password"
        self.rounds = 1
        
        if parse:
            args = p2p_argparse()
            self.uid = args.uid
            self.name = args.name
            self.bind = args.bind
            self.address = args.address
            self.seeduid = args.seeduid
            self.seedaddress = args.seedaddress
            if args.image:
                self.image = args.image
            if args.output:
                self.output = args.output
            if args.stablediffusion:
                self.stablediffusion = args.stablediffusion
            if args.sduser:
                self.sduser = args.sduser
            if args.sdpassw:
                self.sdpassw = args.sdpassw
            if args.rounds:
                self.rounds = args.rounds


        self.pending_messages = queue.Queue()

        LTS_Common()
        self.overlay = LTS_Agent(agent_uuid=self.uid,
                                 name=self.name,
                                 zmq_bind=self.bind,
                                 zmq_address=self.address,
                                 zmq_seed_uuid=self.seeduid,
                                 zmq_seed_address=self.seedaddress,
                                 dispatch_handler=self)
        print(self.overlay.toJSON())

        self.aiconnector = AIConnector(stablediffusion=self.stablediffusion, sduser=self.sduser, sdpassw=self.sdpassw)

    def terminate(self):
        self.overlay.terminate()

        
    def dispatchMessage(self, message):
        content_json = json.loads(message.content)
        self.pending_messages.put(content_json)
        print("Received", content_json, "from", message.from_uuid)
        return None

    # ------
    def objSearch(self, txtdesc, keywords):
        searchres = None
        return searchres


    # ------
    def run(self):
        mergescene = dict()
        for i in range(self.rounds):
            localscene = self.aiconnector.imgToTxt(imagefile=self.image, placeholder=True)
            self.overlay.communicator.broadcast(json.dumps(localscene))
            if len(mergescene) == 0:
                mergescene = localscene
            else:
                mergescene = self.aiconnector.sceneMerge(mergescene, localscene)
            while not self.pending_messages.empty():
                message_json = self.pending_messages.get()
                mergescene = self.aiconnector.sceneMerge(mergescene, message_json)
        prompt=json.dumps(mergescene)
        self.aiconnector.sendTo1111(prompt=prompt, output=self.output + "." + self.overlay.name + ".png")


    
# ------------------------------------------------------------------------------


if __name__ == "__main__":

    genscng = GenScnG()

    # TODO: remove once broadcast/merge is implemented
    # if genscng.image:
    #     sceneA = genscng.aiconnector.imgToTxt(genscng.image)
    #     sceneB = genscng.aiconnector.imgToTxt(genscng.image)
    #     sceneC = genscng.aiconnector.sceneMerge(sceneA, sceneB)
    #     genscng.aiconnector.sendTo1111(sceneC)

    genscng.run()

    genscng.terminate()
    
    exit(0)
