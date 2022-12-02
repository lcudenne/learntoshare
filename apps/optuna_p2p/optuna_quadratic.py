import optuna
import argparse
import queue
import json

from time import sleep

from src.core.common import LTS_Common
from src.core.agents import LTS_Agent



# ------------------------------------------------------------------------------


class OptunaAgent():

    def __init__(self, args):
        self.pending_trials = queue.Queue()
        LTS_Common()
        overlay = LTS_Agent(agent_uuid=args.uid,
                            name=args.name,
                            zmq_bind=args.bind,
                            zmq_address=args.address,
                            zmq_seed_uuid=args.seeduid,
                            zmq_seed_address=args.seedaddress,
                            dispatch_handler=self)
        self.overlay = overlay
        self.ntrials_per_round = args.ntrials
        self.nrounds = args.nrounds
        print("LTS agent", self.overlay.toJSON())

    def terminate(self):
        self.overlay.terminate()

    def dispatchMessage(self, message):
        content_json = json.loads(message.content)
        self.pending_trials.put(content_json)
        print("Received", content_json, "from", message.from_uuid)
        return None

    def objective(self, trial):
        x = trial.suggest_float("x", -100, 100)
        y = trial.suggest_int("y", -1, 1)
        return x**2 + y

    def optimize(self):
        study = optuna.create_study()
        
        for r in range(self.nrounds):
            
            # process incoming trials
            while not self.pending_trials.empty():
                trial_json = self.pending_trials.get()
                trial = study.ask()
                trial_value = trial_json["best_value"]
                trial_params = trial_json["best_params"]
                # for param in trial_params:
                #    trial.storage.get_trial_params(trial._trial_id)[param] = trial_params[param]
                trial.suggest_float("x", trial_params["x"], float(trial_params["x"]))
                trial.suggest_int("y", int(trial_params["y"]), int(trial_params["y"]))
                study.tell(trial, float(trial_value))
                print("Add", trial_json, "to local Optuna optimization")
                
            # optimize locally
            study.optimize(self.objective, n_trials=self.ntrials_per_round)
            print("Round {} best value: {} (params: {})\n".format(r, study.best_value, study.best_params))
            sleep(2)
            content = '{"best_value": ' + str(study.best_value) + ', "best_params": ' + str(study.best_params).replace("'", "\"") + '}'
            
            # broadcast best trial to other peers
            self.overlay.communicator.broadcast(content)

        
# ------------------------------------------------------------------------------


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog = 'optuna_quadratic.py',
        description = 'Quadratic optimization using Optuna over the LTS peer-to-peer framework',
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

    optuna_agent = OptunaAgent(args=args)
    optuna_agent.optimize()
    
    optuna_agent.terminate()
    
    exit(0)
