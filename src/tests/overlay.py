import argparse
import random

from time import sleep

from src.core.common import LTS_Common
from src.core.agents import LTS_Agent



# ------------------------------------------------------------------------------


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog = 'overlay.py',
        description = 'Overlay building',
        epilog = 'https://github.com/lcudenne/learntoshare')

    parser.add_argument("-n", "--npeers", type=int, default=2, required=False,
                        help="number of peers")
    parser.add_argument("-p", "--baseport", type=int, default=5555, required=False,
                        help="TCP base port")
    args = parser.parse_args()


    peer_list = list()
    
    LTS_Common()

    net_address = "tcp://localhost:" + str(args.baseport)
    bind_address = "tcp://*:" + str(args.baseport)
    peer = LTS_Agent(zmq_bind=bind_address, zmq_address=net_address)
    peer_list.append(peer)

    seed_uuid = peer.uuid
    seed_address = peer.communicator.zmq_address
    
    for i in range(args.npeers):
        net_address = "tcp://localhost:" + str(args.baseport + i + 1)
        bind_address = "tcp://*:" + str(args.baseport + i + 1)
        seed_index = random.randint(0, len(peer_list) - 1)
        peer = LTS_Agent(zmq_bind=bind_address, zmq_address=net_address,
                         zmq_seed_uuid=peer_list[seed_index].uuid,
                         zmq_seed_address=peer_list[seed_index].communicator.zmq_address)
        peer_list.append(peer)

    sleep(20)
    peer.terminate()

        
    exit(0)
