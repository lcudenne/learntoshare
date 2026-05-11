import argparse
import os
import json

from pydantic import BaseModel

from ollama import chat
from ollama import ChatResponse

# ------------------------------------------------------------------------------

def tofind_argparse():

    parser = argparse.ArgumentParser(
        prog = 'Generative Scene Graph - tofind',
        description = 'Peer-to-peer Generative Scene Graph',
        epilog = 'https://github.com/lcudenne/learntoshare')

    parser.add_argument("-i", "--inputfile", type=str, required=False,
                        help="path to an input point of view namespace (without file extension)")
    parser.add_argument("-t", "--targetdir", type=str, required=False,
                        help="path to the target directory")
    parser.add_argument("-l", "--llm", type=str, required=False,
                        help="Ollama model (default is ministral-3:3b")

    return parser.parse_args()

# ------------------------------------------------------------------------------

class ToFindAnswer(BaseModel):
    answer: bool
    justification: str

# ------------------------------------------------------------------------------

class ToFind():

    def __init__(self):

        self.args = tofind_argparse()
        self.llm = self.args.llm or "ministral-3:3b"

    def isPresentRegExp(self, keyword=None, descjson=None):
        result = keyword.lower() in str(descjson).lower()
        return result, "Matching" + keyword.lower() + " in description"

    def isPresentLLM(self, keyword=None, descjson=None):
        response: ChatResponse = chat(
            model=self.llm,
            messages=[
                {
                    'role': 'user',
                    'content': 'Does the object ' + keyword + ' appears in the following description? Please answer by True or False with a justification. Description is ' + str(descjson)
                },
            ],
            format=ToFindAnswer.model_json_schema()
        )
        print(response.message.content)
        resjson = json.loads(response.message.content)
        return bool(resjson['answer']), str(resjson['justification'])

    def processSingleFile(self, inputfile=None):
        print("tofind input file " + self.args.inputfile)
        ispresent = list()
        if inputfile:
            jsondata = json.loads('{"header": {}, "descriptions": []}')
            jsonfile = inputfile + ".json"
            if os.path.isfile(jsonfile):
                with open(jsonfile) as f:
                    jsondata = json.load(f)
                    print(jsondata)
            tofindlist = list()
            tofindfile = inputfile.rsplit('_', 1)[0] + ".tofind"
            if os.path.isfile(tofindfile):
                with open(tofindfile) as f:
                    tofindlist = [line.rstrip() for line in f]
                    print(tofindlist)

            for description in jsondata["descriptions"]:
                descuuid = description["uuid"]
                for keyword in tofindlist:
                    answer, justification = self.isPresentRegExp(keyword=keyword, descjson=description)
                    ispresent.append([inputfile, descuuid, keyword, "regexp", answer, justification])
                    answer, justification = self.isPresentLLM(keyword=keyword, descjson=description)
                    ispresent.append([inputfile, descuuid, keyword, self.llm, answer, justification])

        print(ispresent)




    def process(self):
        if self.args.inputfile:
            self.processSingleFile(inputfile=self.args.inputfile)



        if self.args.targetdir:
            print("tofind directory" + self.args.targetdir)

# ------------------------------------------------------------------------------

if __name__ == "__main__":

    tofind = ToFind()
    
    tofind.process()
    
    exit(0)
