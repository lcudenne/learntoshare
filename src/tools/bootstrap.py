import argparse
import os
import random
import socket
import uuid
from faker import Faker


# ------------------------------------------------------------------------------

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))
        ipa = s.getsockname()[0]
    except Exception:
        ipa = '127.0.0.1'
    finally:
        s.close()
    return ipa

# ------------------------------------------------------------------------------

def topologyStar(f, lines, selfuid, ipa, listenport):
    cmd=""
    if len(lines) == 0:
        f.write("--seedaddress tcp://" + ipa + ":" + listenport + " --seeduid " + selfuid + "\n")
    else:
        cmd=lines[0]
    return cmd

def topologyChain(f, lines, selfuid, ipa, listenport):
    cmd=""
    if len(lines) > 0:
        cmd=lines[-1]
    f.write("--seedaddress tcp://" + ipa + ":" + listenport + " --seeduid " + selfuid + "\n")
    return cmd

def topologyCluster(f, lines, selfuid, ipa, listenport, nclusters):
    cmd=""
    if len(lines) >= nclusters:
        cmd=lines[random.randrange(0, len(lines))]
    else:
        if len(lines) > 0:
            cmd=lines[-1]
        f.write("--seedaddress tcp://" + ipa + ":" + listenport + " --seeduid " + selfuid + "\n")
    return cmd


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'bootstrap.py',
        description = 'learntoshare overlay bootstrap',
        epilog = 'https://github.com/lcudenne/learntoshare')
    parser.add_argument("-t", "--topology", type=str, default="star", required=False,
                        help="overlay bootstrap topology {star|chain|cluster} (default is star)")
    parser.add_argument("-i", "--minport", type=int, default=10000, required=False,
                        help="TCP port range: minimum value (default is 10000)")
    parser.add_argument("-a", "--maxport", type=int, default=12000, required=False,
                        help="TCP port range: maximum value, excluded (default is 12000)")
    parser.add_argument("-c", "--nclusters", type=int, default=2, required=False,
                        help="number of clusters (default is 2)")
    args = parser.parse_args()

    selfuid = str(uuid.uuid4())
    fake = Faker()
    selfname = fake.first_name()
    ipa = get_ip()
    listenport = str(random.randrange(args.minport, args.maxport))
    cmd="--uid " + selfuid + " --name " + selfname + " --bind tcp://*:" + listenport + " --address tcp://" + ipa + ":" + listenport
    
    with open("lts_bootstrap_lock_file", "a+") as f:
        fd = f.fileno()
        os.lockf(fd, os.F_LOCK, 0)
        f.seek(0)
        lines = f.readlines()
        
        if args.topology == "chain":
            cmd = cmd + " " + topologyChain(f, lines, selfuid, ipa, listenport)
        if args.topology == "star":
            cmd = cmd + " " + topologyStar(f, lines, selfuid, ipa, listenport)
        if args.topology == "cluster":
            cmd = cmd + " " + topologyCluster(f, lines, selfuid, ipa, listenport, args.nclusters)
        
    print(cmd)

    exit(0)
