import argparse
import os
import glob
import tqdm
import json
import time
import datetime
import base64
import requests
import uuid
import sys

from random import randint
from pydantic import BaseModel

from ollama import chat
from ollama import ChatResponse

from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler

from transformers import pipeline


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
    parser.add_argument("-l", "--llm", type=str, required=False,
                        help="AI model (default is ministral-3:3b)")
    parser.add_argument("-v", "--vlm", type=str, required=False,
                        help="AI vision model (default is llava:13b)")
    parser.add_argument("-c", "--clipmodel", type=str, required=False,
                        help="AI vision CLIP model to use with llamacpp runtime (mmproj file)")
    parser.add_argument("-r", "--runtime", type=str, required=False,
                        help="Inference runtime {ollama, llamacpp, transformers} (default is ollama)")
 
    return parser.parse_args()

# ------------------------------------------------------------------------------
#deprecated

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
                 sdpassw="password",
                 llm="ministral-3:3b",
                 vlm="llava:13b",
                 clipmodel="",
                 runtime="ollama"):

        self.targetdir = os.getcwd()
        self.iterations = 2
        self.filetypes = ('jpg', 'jpeg')
        self.stablediffusion = stablediffusion
        self.sduser = sduser
        self.sdpassw = sdpassw
        self.llm = llm
        self.vlm = vlm
        self.clipmodel = clipmodel
        self.runtime = runtime
        self.vlmprompt = 'You are observing your environment for unusual objects and events. Please list all objects, the location of the objects and the relationships between objects in the given picture:'

        if parse:
            args=ai_argparse()
            self.llm = args.llm or "ministral-3:3b"
            self.vlm = args.vlm or "llava:13b"
            self.clipmodel = args.clipmodel or ""
            self.runtime = args.runtime or "ollama"
            if args.targetdir:
                self.targetdir = args.targetdir
            if args.iterations:
                self.iterations = args.iterations

        self.targetdir = os.path.realpath(self.targetdir)



    def imgToTxtOllama(self, imagefile):
        response: ChatResponse = chat(
            model=self.vlm,
            messages=[
                {
                    'role': 'user',
                    'content': self.vlmprompt,
                    'images': [imagefile]
                },
            ],
        )
        return response.message.content


    def imgToTxtLlamaCpp(self, imagefile):
        chat_handler = Llava15ChatHandler(clip_model_path=self.clipmodel)
        llm = Llama(
            model_path=self.vlm,
            chat_handler=chat_handler,
            n_gpu_layers=-1,
            seed=randint(0, sys.maxsize),
            n_ctx=2048,
            verbose=False
        )
        response = llm.create_chat_completion(
            messages = [
                {"role": "system", "content": "You are an assistant who perfectly describes images."},
                {
                    "role": "user",
                    "content": [
                        {"type" : "text",
                         "text": self.vlmprompt},
                        {"type": "image_url",
                         "image_url": {"url": "file:"+imagefile} }
                    ]
                }
            ]
        )
        return str(response["choices"][0]["message"]["content"])


    def imgToTxtTransformers(self, imagefile):
        pipe = pipeline("image-text-to-text", model=self.vlm)
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": self.vlmprompt},
                    {"type": "image_url",
                     "image_url": {"url": imagefile}
                    }
                ]
            }
        ]
        out = pipe(text=messages)
        return str(out[0]['generated_text'][1]['content'])


    def imgToTxt(self, imagefile=None, placeholder=False, filtervlm=None):
        scenegraph = None
        if imagefile:
            if placeholder:
                jsonfile = os.path.splitext(imagefile)[0] + ".json"
                if os.path.isfile(jsonfile):
                    with open(jsonfile) as f:
                        jsondata = json.load(f)
                        if jsondata['descriptions']:
                            filterdesc=jsondata['descriptions']
                            if filtervlm:
                                filterdesc=next(d for d in jsondata['descriptions'] if d['model'] == filtervlm)
                            if len(filterdesc) > 0:
                                scenegraph = filterdesc[randint(0, len(filterdesc) - 1)]['content']
            if scenegraph is None:
                response = None
                if self.runtime == "transformers":
                    response = self.imgToTxtTransformers(imagefile)
                if self.runtime == "llamacpp":
                    response = self.imgToTxtLlamaCpp(imagefile)
                if self.runtime == "ollama":
                    response = self.imgToTxtOllama(imagefile)
                scenegraph = response

        return scenegraph



    def sceneMerge(self, sceneA=None, sceneB=None):
        scnmerge = None
        if sceneA and sceneB:
            response: ChatResponse = chat(
                model=self.llm,
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
                starttime=time.time()
                scenegraph = self.imgToTxt(imagefile=imagefile)
                inferencetime = int(time.time() - starttime)
                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
                jsonadd = json.loads('{"uuid": "'+str(uuid.uuid4())+'", "timestamp": "'+timestamp+'", "inferencetime_s": "'+str(inferencetime)+'", "runtime": "'+self.runtime+'", "model": "'+self.vlm.rsplit('/', 1)[-1]+'", "content": {}}')
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
