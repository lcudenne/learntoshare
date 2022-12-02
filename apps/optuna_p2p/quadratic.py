import optuna
import argparse

from apps.optuna_p2p.optuna_p2p import OptunaP2P

# ------------------------------------------------------------------------------

def optimize_function(trial):
    x = trial.suggest_float("x", -100, 100)
    y = trial.suggest_int("y", -1, 1)
    return x**2 + y

# ------------------------------------------------------------------------------


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog = 'optuna_p2p.py',
        description = 'Optimization skeleton using Optuna over the LTS peer-to-peer framework',
        epilog = 'https://github.com/lcudenne/learntoshare')

    parser.add_argument("-r", "--nrounds", type=int, default=4, required=False,
                        help="number of rounds, each round composed by n trials and a broadcast of the current best solution")
    parser.add_argument("-t", "--ntrials", type=int, default=10, required=False,
                        help="number of trials per round")
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
    

    args = parser.parse_args()

    optuna_agent = OptunaP2P(args=args, optimize_function=optimize_function)
    optuna_agent.optimize()
    
    optuna_agent.terminate()
    
    exit(0)
