import argparse
import os
import json

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

    return parser.parse_args()


# ------------------------------------------------------------------------------

class ToFind():

    def __init__(self):

        self.args = tofind_argparse()


    def processSingleFile(self, inputfile=None):
        print("tofind input file " + self.args.inputfile)
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
