import argparse
import os
import glob
import tqdm
import json
import time
import datetime
import base64
import requests

from random import randint
from pydantic import BaseModel

from ollama import chat
from ollama import ChatResponse


# ------------------------------------------------------------------------------

def ai_argparse():

    parser = argparse.ArgumentParser(
        prog = 'Multiview to text',
        description = 'Populate text labels from multiview image database.',
        epilog = 'https://github.com/lcudenne/learntoshare')

    parser.add_argument("-t", "--targetdir", type=str, required=False,
                        help="path to the target directory to populate multiview scenes with labels")
    parser.add_argument("-n", "--iterations", type=int, required=False,
                        help="number of iterations for each image (default is 2)")

 
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

class AIConnector():

    def __init__(self, parse=False,
                 stablediffusion="http://127.0.0.1:7860",
                 sduser="user",
                 sdpassw="password"):

        self.targetdir = os.getcwd()
        self.iterations = 2
        self.filetypes = ('jpg', 'jpeg')
        self.stablediffusion = stablediffusion
        self.sduser = sduser
        self.sdpassw = sdpassw

        if parse:
            args=ai_argparse()
            if args.targetdir:
                self.targetdir = args.targetdir
            if args.iterations:
                self.iterations = args.iterations

        self.targetdir = os.path.realpath(self.targetdir)


    def imgToTxt(self, imagefile=None, placeholder=False):
        scenegraph = None
        if imagefile:
            if placeholder:
                jsonfile = os.path.splitext(imagefile)[0] + ".json"
                if os.path.isfile(jsonfile):
                    with open(jsonfile) as f:
                        jsondata = json.load(f)
                        if jsondata['descriptions']:
                            if len(jsondata['descriptions']) > 0:
                                scenegraph = jsondata['descriptions'][randint(0, len(jsondata['descriptions']) - 1)]
            if scenegraph is None:
                response: ChatResponse = chat(
                    model='llava:13b',
                    messages=[
                        {
                            'role': 'user',
                            'content': 'Please list all objects, the location of the objects and the relationships between objects using bullet points:',
                            'images': [imagefile]
                        },
                    ],
                    format=SceneDesc.model_json_schema()
                )
                scenegraph = json.loads(response.message.content)

        return scenegraph



    def sceneMerge(self, sceneA=None, sceneB=None):
        scnmerge = None
        if sceneA and sceneB:
            response: ChatResponse = chat(
                model='phi3:14b',
                messages=[
                {
                    'role': 'user',
                    'content': 'Please merge the common elements of the following two scene descriptions into plain text. The first description is ' + str(sceneA) + '. The second description is ' + str(sceneB)
                },
                ],
                format=SceneDesc.model_json_schema()
            )
            print(response.message.content)
            scnmerge = response.message.content
            print(SceneDesc.model_validate_json(response.message.content))
        return scnmerge



    def sendTo1111(self, prompt, output):
        payload = {
            "prompt": prompt,
            "steps": 20
        }
        response = requests.post(url=self.stablediffusion + "/sdapi/v1/txt2img", json=payload, auth=(self.sduser, self.sdpassw))
        res_json = response.json()
        if "images" in res_json:
            with open(output, 'wb') as f:
                f.write(base64.b64decode(res_json['images'][0]))


    def populate(self):
        print("Populating " + self.targetdir)
        filelist = []
        for ftype in self.filetypes:
            filelist.extend(glob.glob(self.targetdir + '/*.' + ftype, recursive=True))
        for imagefile in tqdm.tqdm(filelist, desc="Status"):
            jsondata = json.loads('{"header": {}, "descriptions": []}')
            jsonfile = os.path.splitext(imagefile)[0] + ".json"
            if os.path.isfile(jsonfile):
                with open(jsonfile) as f:
                    jsondata = json.load(f)
            for i in tqdm.trange(self.iterations, desc=os.path.basename(imagefile)):
                scenegraph = self.imgToTxt(imagefile=imagefile)
                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
                jsonadd = json.loads('{"timestamp": "'+timestamp+'", "content": {}}')
                jsonadd['content'] = scenegraph
                jsondata['descriptions'].append(jsonadd)
            jsonobject = json.dumps(jsondata, indent=4)
            with open(jsonfile, "w") as f:
                f.write(jsonobject)

                    
# ------------------------------------------------------------------------------


if __name__ == "__main__":

    aiconnector = AIConnector(parse=True)

    aiconnector.populate()

    exit(0)
