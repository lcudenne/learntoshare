import argparse
import json
import requests
import base64

from ollama import chat
from ollama import ChatResponse
from pydantic import BaseModel

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
    parser.add_argument("-j", "--stablediffusion", type=str, required=False,
                        help="http address to automatic1111 stable diffusion service (default is http://127.0.0.1:7860)")
    parser.add_argument("-w", "--sduser", type=str, required=False,
                        help="username for automatic1111 stable diffusion service (default is user)")
    parser.add_argument("-p", "--sdpassw", type=str, required=False,
                        help="password for automatic1111 stable diffusion service (default is password)")
    parser.add_argument("-o", "--output", type=str, required=False,
                        help="path to the output image (default is output.png)")

    return parser.parse_args()


# ------------------------------------------------------------------------------


class SceneObj(BaseModel):
    object: str
    properties: str
    location: str
    color: str

class SceneDesc(BaseModel):
    point_of_view: str
    lightning: str
    objects: list[SceneObj]
    

# ------------------------------------------------------------------------------

class GenScnG():

    def __init__(self, parse=False,
                 uid=None,
                 name=None,
                 bind=None,
                 address=None,
                 seeduid=None,
                 seedaddress=None,
                 stablediffusion="http://127.0.0.1:7860",
                 sduser="user",
                 sdpassw="password",
                 output="output.png"):

        self.uid = uid
        self.name = name
        self.bind = bind
        self.address = address
        self.seeduid = seeduid
        self.seedaddress = seedaddress
        self.stablediffusion = stablediffusion
        self.sduser = sduser
        self.sdpassw = sdpassw
        self.output = output
        
        if parse:
            args = p2p_argparse()
            self.uid = args.uid
            self.name = args.name
            self.bind = args.bind
            self.address = args.address
            self.seeduid = args.seeduid
            self.seedaddress = args.seedaddress
            if args.stablediffusion:
                self.stablediffusion = args.stablediffusion
            if args.sduser:
                self.sduser = args.sduser
            if args.sdpassw:
                self.sdpassw = args.sdpassw
            if args.output:
                self.output = args.output

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

    # ------
    def imgToGraph(self, imgurl=None):
        scenegraph = None
        if imgurl:
            response: ChatResponse = chat(
                model='llava:13b',
                messages=[
                    {
                        'role': 'user',
                        'content': 'Please list all objects, the location of the objects and the relationships between objects using bullet points:',
                        'images': [imgurl]
                    },
                ],
                format=SceneDesc.model_json_schema()
            )
            print(response.message.content)
            scenegraph = response.message.content
            print(SceneDesc.model_validate_json(response.message.content))
        return scenegraph

    # ------
    def objSearch(self, txtdesc, keywords):
        searchres = None
        return searchres

    # ------
    def sceneMerge(self, sceneA=None, sceneB=None):
        scnmerge = None
        if sceneA and sceneB:
            response: ChatResponse = chat(
                model='phi3:14b',
                messages=[
                {
                    'role': 'user',
                    'content': 'Can you merge the common elements of the following two scene descriptions into plain text? The first description is ' + str(sceneA) + '. The second description is ' + str(sceneB)
                },
                ],
                format=SceneDesc.model_json_schema()
            )
            print(response.message.content)
            scnmerge = response.message.content
            print(SceneDesc.model_validate_json(response.message.content))
        return scnmerge


    # ------
    def sendTo1111(self, prompt):
        payload = {
            "prompt": prompt,
            "steps": 20
        }
        response = requests.post(url=self.stablediffusion + "/sdapi/v1/txt2img", json=payload, auth=(self.sduser, self.sdpassw))
        res_json = response.json()
        if "images" in res_json:
            with open(self.output, 'wb') as f:
                f.write(base64.b64decode(res_json['images'][0]))
            
    
# ------------------------------------------------------------------------------


if __name__ == "__main__":

    args = p2p_argparse()
    imgurl = None
    if args.image:
        imgurl = args.image

    genscng = GenScnG(parse=True)

    if imgurl:
        sceneA = genscng.imgToGraph(imgurl)
        sceneB = genscng.imgToGraph(imgurl)
        sceneC = genscng.sceneMerge(sceneA, sceneB)
        genscng.sendTo1111(sceneC)

    genscng.terminate()
    
    exit(0)
