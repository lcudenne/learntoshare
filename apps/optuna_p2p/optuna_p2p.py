import optuna
import argparse
import queue
import json
import logging

from src.core.common import LTS_Common
from src.core.agents import LTS_Agent


# ------------------------------------------------------------------------------

def objective_function_placeholder(trial):
    logging.info("Optuna objective function not implemented")
    return 0

# ------------------------------------------------------------------------------

class ObjectiveObjectPlaceholder:
    def __init__(self):
        logging.info("Optuna objective class not implemented")
        pass

    def __call__(self, trial):
        return 0

# ------------------------------------------------------------------------------


class OptunaP2P():

    def __init__(self, args,
                 objective_function=objective_function_placeholder,
                 objective_object=None,
                 study=None):
        self.objective_function = objective_function
        self.objective_object = objective_object
        self.study = study
        self.pending_trials = queue.Queue()
        LTS_Common()
        self.overlay = LTS_Agent(agent_uuid=args.uid,
                                 name=args.name,
                                 zmq_bind=args.bind,
                                 zmq_address=args.address,
                                 zmq_seed_uuid=args.seeduid,
                                 zmq_seed_address=args.seedaddress,
                                 dispatch_handler=self)
        self.ntrials_per_round = args.ntrials
        self.nrounds = args.nrounds
        print("LTS agent", self.overlay.toJSON())

    def terminate(self):
        self.overlay.terminate()

    def bestParamsTypes(self, best_params):
        param_types = dict()
        for param in best_params:
            if isinstance(best_params[param], float):
                param_types[param] = "float"
            elif isinstance(best_params[param], int):
                param_types[param] = "int"
            else:
                param_types[param] = "categorical"
        return param_types

    def dispatchMessage(self, message):
        content_json = json.loads(message.content)
        self.pending_trials.put(content_json)
        print("Received", content_json, "from", message.from_uuid)
        return None

    def objective(self, trial):
        return self.objective_function(trial)

    def optimize(self):
        if not self.study:
            self.study = optuna.create_study()
        
        for r in range(self.nrounds):
            
            # process incoming trials
            while not self.pending_trials.empty():
                trial_json = self.pending_trials.get()
                trial = self.study.ask()
                trial_value = float(trial_json["best_value"])
                trial_params = trial_json["best_params"]
                trial_types = trial_json["param_types"]

                for param in trial_params:
                    if trial_types[param] == "float":
                        trial.suggest_float(param,
                                            float(trial_params[param]), float(trial_params[param]))
                    elif trial_types[param] == "int":
                        trial.suggest_int(param,
                                          int(trial_params[param]), int(trial_params[param]))
                    else:
                        print("Warning: categorical distribution not supported. convert to int")

                self.study.tell(trial, trial_value)
                print("Add", trial_json, "to local Optuna optimization")
                
            # optimize locally
            if self.objective_object:
                self.study.optimize(self.objective_object, n_trials=self.ntrials_per_round)
            else:
                self.study.optimize(self.objective, n_trials=self.ntrials_per_round)
            print("Round {} best value: {} (params: {})\n".format(r, self.study.best_value, self.study.best_params))

            # broadcast best trial to other peers
            content = '{"best_value": ' + str(self.study.best_value) + ', "best_params": ' + str(self.study.best_params).replace("'", "\"") + ', "param_types": ' + str(self.bestParamsTypes(self.study.best_params)).replace("'", "\"") + '}'
            self.overlay.communicator.broadcast(content)


# ------------------------------------------------------------------------------


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog = 'optuna_p2p.py',
        description = 'Optimization skeleton using Optuna over the LTS peer-to-peer framework',
        epilog = 'https://github.com/lcudenne/learntoshare')

    parser.add_argument("-r", "--nrounds", type=int, default=0, required=False,
                        help="number of rounds, each round composed by t trials and a broadcast of the current best solution")
    parser.add_argument("-t", "--ntrials", type=int, default=0, required=False,
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

    optuna_agent = OptunaP2P(args=args, objective_function=objective_function_placeholder)
    optuna_agent.optimize()
    optuna_agent.terminate()

    optuna_agent = OptunaP2P(args=args, objective_object=ObjectiveObjectPlaceholder())
    optuna_agent.optimize()
    optuna_agent.terminate()

    exit(0)
