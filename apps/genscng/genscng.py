import argparse
import json
import queue
import time
import datetime

from apps.genscng.aiconnector import AIConnector
from apps.genscng.frameplayer import FramePlayer

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
    parser.add_argument("-t", "--track", type=str, required=False,
                        help="path to a base image name corresponding to track (sequence of images)")
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
    parser.add_argument("-l", "--llm", type=str, required=False,
                        help="Ollama model (default is ministral-3:3b")
    parser.add_argument("-v", "--vlm", type=str, required=False,
                        help="Ollama vision model (default is llava:13b")


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
        self.track = None
        self.output = "output"
        self.stablediffusion = "http://127.0.0.1:7860"
        self.sduser = "user"
        self.sdpassw = "password"
        self.rounds = 1
        self.llm = "ministral-3:3b"
        self.vlm="llava:13b"
        
        if parse:
            args = p2p_argparse()
            self.uid = args.uid
            self.name = args.name
            self.bind = args.bind
            self.address = args.address
            self.seeduid = args.seeduid
            self.seedaddress = args.seedaddress
            self.llm = args.llm or "ministral-3:3b"
            self.vlm = args.vlm or "llava:13b"
            if args.image:
                self.image = args.image
            if args.track:
                self.track = args.track
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
    def imageSeq(self, image=None, inputscene=None):
        if image:
            print(datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") + " USER [INPUT] " + self.overlay.uuid + " " + image)
            localscene = self.aiconnector.imgToTxt(imagefile=image, placeholder=True)
            print(datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") + " USER [TACSIT] " + self.overlay.uuid + " " + json.dumps(localscene))
            self.overlay.communicator.broadcast(json.dumps(localscene))
            if len(inputscene) == 0:
                mergescene = localscene
            else:
                mergescene = self.aiconnector.sceneMerge(inputscene, localscene)
            while not self.pending_messages.empty():
                message_json = self.pending_messages.get()
                mergescene = self.aiconnector.sceneMerge(mergescene, message_json)
        return mergescene


    # ------
    def run(self):
        mergescene = dict()

        if self.track:
            frameplayer = FramePlayer(filename=self.track)
            fnext = frameplayer.next()
            while fnext:
                mergescene = self.imageSeq(image=fnext, inputscene=mergescene)
                fnext = frameplayer.next()

        if self.image:
            for i in range(self.rounds):
                mergescene = self.imageSeq(image=self.image, inputscene=mergescene)

        #prompt=json.dumps(mergescene)
        #self.aiconnector.sendTo1111(prompt=prompt, output=self.output + "." + self.overlay.name + ".png")


    
# ------------------------------------------------------------------------------


if __name__ == "__main__":

    genscng = GenScnG()

    genscng.run()

    genscng.terminate()
    
    exit(0)
