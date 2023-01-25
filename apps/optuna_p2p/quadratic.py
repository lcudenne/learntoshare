import optuna
import argparse

from time import sleep

from apps.optuna_p2p.optuna_p2p import OptunaP2P

# ------------------------------------------------------------------------------

def objective_function(trial):
    x = trial.suggest_float("x", -100, 100)
    y = trial.suggest_int("y", -1, 1)
    # emulates a compute-intensive optimization function
    # to be able to run several P2P agents
    sleep(0.1)
    return x**2 + y


# ------------------------------------------------------------------------------

class ObjectiveObject:
    def __init__(self, at_pow: int):
        self.at_pow = at_pow

    def __call__(self, trial):
        x = trial.suggest_float("x", -100, 100)
        y = trial.suggest_int("y", -1, 1)
        # emulates a compute-intensive optimization function
        # to be able to run several P2P agents
        sleep(0.1)
        return x**self.at_pow + y

# ------------------------------------------------------------------------------


if __name__ == "__main__":

    optuna_agent = OptunaP2P(parse=True, objective_function=objective_function)
    optuna_agent.optimize()
    optuna_agent.terminate()

    optuna_agent = OptunaP2P(parse=True, objective_object=ObjectiveObject(at_pow=2))
    optuna_agent.optimize()
    optuna_agent.terminate()

    
    exit(0)
