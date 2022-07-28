
import logging
import json

# ------------------------------------------------------------------------------

LTS_NAME="Learn to Share"
LTS_VERSION_MAJ=0
LTS_VERSION_MIN=1

# ------------------------------------------------------------------------------

class LTS_BaseClass():
    def __init__(self, class_name="unknown"):
        self.class_name = class_name
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


# ------------------------------------------------------------------------------

class LTS_Common():
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info(LTS_NAME + " v" + str(LTS_VERSION_MAJ) + "." + str(LTS_VERSION_MIN))
        
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    common = LTS_Common()
    exit(0)
