import argparse
import os
import glob
import tqdm
import json
import time
import datetime

from pydantic import BaseModel

from ollama import chat
from ollama import ChatResponse


# ------------------------------------------------------------------------------

def pop_argparse():

    parser = argparse.ArgumentParser(
        prog = 'Multiview to text',
        description = 'Populate text labels from multiview image database. Image naming must be scnXXX_povYYY.jpeg (or any valid image format/extension) with XXX and YYY arbitrary numbers identifying the scene number and the point of view number in the scene.',
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

    def __init__(self, parse=False):
        self.targetdir = os.getcwd()
        self.iterations = 2
        self.filetypes = ('jpg', 'jpeg')
        if parse:
            args=pop_argparse()
            if args.targetdir:
                self.targetdir = args.targetdir
            if args.iterations:
                self.iterations = args.iterations
        self.targetdir = os.path.realpath(self.targetdir)


    def imgToTxt(self, image=None):
        scenegraph = None
        if image:
            response: ChatResponse = chat(
                model='llava:13b',
                messages=[
                    {
                        'role': 'user',
                        'content': 'Please list all objects, the location of the objects and the relationships between objects using bullet points:',
                        'images': [image]
                    },
                ],
                format=SceneDesc.model_json_schema()
            )
            scenegraph = json.loads(response.message.content)
        return scenegraph

        
    def run(self):
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
                scenegraph = self.imgToTxt(image=imagefile)
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

    aiconnector.run()

    exit(0)
