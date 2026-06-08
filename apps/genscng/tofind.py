import argparse
import os
import glob
import json
import datetime

from pydantic import BaseModel

from ollama import chat
from ollama import ChatResponse

import plotly.express as px
import pandas as pd

# ------------------------------------------------------------------------------

def tofind_argparse():

    parser = argparse.ArgumentParser(
        prog = 'Generative Scene Graph - tofind',
        description = 'Peer-to-peer Generative Scene Graph',
        epilog = 'https://github.com/lcudenne/learntoshare')

    parser.add_argument("-i", "--inputfile", type=str, required=False,
                        help="path to an input point of view namespace (without file extension)")
    parser.add_argument("-d", "--logdir", type=str, required=False,
                        help="path to the directory containing genscy log files")
    parser.add_argument("-l", "--llm", type=str, required=False,
                        help="Ollama model (default is ministral-3:3b)")
    parser.add_argument("-k", "--keywords", nargs='+', default=[], required=False,
                        help="list of keywords/objects to be detected in descriptions")

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
            if self.args.keywords:
                tofindlist = self.args.keywords
            else:
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


    def toTimestamp(self, logsplit=None):
        return datetime.datetime.strptime(logsplit[0]+" "+logsplit[1], "%Y-%m-%d %H:%M:%S").timestamp()


    def processLogFiles(self, logdir=None):
        print("tofind directory" + self.args.logdir)
        eventlist = []
        tofindlist = self.args.keywords
        for logfile in glob.glob(self.args.logdir + "/*.log"):
            print("processing " + logfile)
            if os.path.isfile(logfile):
                with open(logfile) as f:
                    start_date = 0
                    end_date = 0
                    for logline in f:
                        logsplit = logline.split(' ', 5)
                        if "Agent running" in logline:
                            start_date = self.toTimestamp(logsplit)
                        if "Agent terminating" in logline:
                            end_date = self.toTimestamp(logsplit)
                    f.seek(0)
                    for logline in f:
                        logsplit = logline.split(' ', 5)
                        if "TACSIT" in logline:
                            eventlist.append(dict(File=logfile,
                                                  Agent=logsplit[4],
                                                  Start=self.toTimestamp(logsplit),
                                                  End=self.toTimestamp(logsplit)+1,
                                                  Keyword="TACSIT"))
                            for keyword in tofindlist:
                                answer, justification = self.isPresentRegExp(keyword=keyword, descjson=json.loads(logsplit[5]))
                                if not answer:
                                    answer, justification = self.isPresentLLM(keyword=keyword, descjson=json.loads(logsplit[5]))
                                if answer:
                                    eventlist.append(dict(File=logfile,
                                                          Agent=logsplit[4],
                                                          Start=self.toTimestamp(logsplit),
                                                          End=end_date,
                                                          Keyword=keyword))

        print(eventlist)
        if eventlist:
            df = pd.DataFrame(eventlist)
            df['Start'] = pd.to_datetime(df['Start'], unit='s')
            df['End'] = pd.to_datetime(df['End'], unit='s')
            fig = px.timeline(df, x_start="Start", x_end="End", y="Agent", color="Keyword")
            fig.update_yaxes(autorange="reversed")
            fig.show()


    def process(self):
        if self.args.inputfile:
            self.processSingleFile(inputfile=self.args.inputfile)

        if self.args.logdir:
            self.processLogFiles(logdir=self.args.logdir)

# ------------------------------------------------------------------------------

if __name__ == "__main__":

    tofind = ToFind()
    
    tofind.process()
    
    exit(0)
