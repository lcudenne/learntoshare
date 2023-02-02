# Optuna Peer-to-peer (P2P) examples

[Optuna](https://github.com/optuna/optuna) is an automatic hyperparameter optimization software framework, particularly designed for machine learning.
Distributing Optuna among computing nodes allows to explore more solutions (hereinafter referred to as trials) or significantly decrease the compute time.
The Optuna builtin approach relies on a centralized database server onto which instances of the optimizer share results and best values. This has shown to limit the scalability of the system when coping with hundreds of optimizing instances for a high number of trials.

In this approach, we propose a fully decentralized system in which optimizing instances eventually share their best values using group communication protocols.


## Cold start

Set your virtual environment.

```bash
$ cd apps/optuna_p2p
$ virtualenv -p python3 venv
$ source venv/bin/activate
(venv) $ pip install -r ../../requirements.txt
(venv) $ pip install -r requirements.txt
```

Test the Optuna P2P skeleton.

```bash
(venv) $ PYTHONPATH+=../../ python3 ./optuna_p2p.py
```

This should start a P2P agent, create an Optuna study and terminate.


## Distributed computing principle and Optuna

The P2P network is a set of loosely connected processes (peers). Each
peer creates a local Optuna study. Unlike the in-house Optuna
distributed implementation, peers do not report to a centralized SQL
server. Instead, they eventually broadcast the best parameters to
other peers.

### P2P bootstrap

Peers are defined by a unique identifier (UID) and a TCP address used
for inbound connections. They can be deployed at any time and in any
order in the system. While the first deployed peer (usually called
`seed`) is standalone, other peers have to know the UID and the TCP
address of an other peer to join the network. They will later discover
other peers to build the neighborhood.

### Optimization loop

Each Optuna peer runs `r` rounds. Each round is composed by the following steps:
1. Pending trials (best values and best parameters) received from other peers are added to the local Optuna study,
2. The local `study.optimize` method is called with the user-defined objective function and the given number of trials `t`,
3. The current best value and best parameters are broadcasted to other peers.

During all these steps, incoming trials are placed within a pending
queue (thread-safe). This avoids any synchronization between peers
that could hang the local optimization process.

## Hello world (`quadratic.py`)

The following example is a quadratic function optimization as
presented in the Optuna documentation
[quadratic_simple.py](https://github.com/optuna/optuna-examples/blob/main/quadratic_simple.py).

Use the `--help` argument for the list of options.
```bash
(venv) $ PYTHONPATH+=../../ python3 quadratic.py --help
```

### About the code

The objective function is written by the user. It takes an Optuna
trial as a single mandatory parameter and returns a float which is the
result of the optimization function. You can use any name to define
this function.

```python
def objective_function(trial):
    x = trial.suggest_float("x", -100, 100)
    y = trial.suggest_int("y", -1, 1)
    return x**2 + y
```

In the `__main__` function, an OptunaP2P agent is instantiated with
several arguments and a reference to the user-defined optimization
function. This step bootstraps the P2P network. The `optimize` method
starts the optimization loop for `r` rounds of `t` trials. Finally,
the `terminate` method asks for a distributed termination of the P2P
overlay.


```python
    optuna_agent = OptunaP2P(parse=True, objective_function=objective_function)
    optuna_agent.optimize()
    optuna_agent.terminate()
```

Note that it is also possible to use an Optimize Class instead of a function:

```python
    optuna_agent = OptunaP2P(parse=True, objective_object=ObjectiveObject(at_pow=2))
```

### Colocated deployment

Several peers can be deployed on the same machine provided they use
different TCP ports. The latter example can be deployed using two
terminals (`$1` and `$2`).

```bash
(venv) $1 PYTHONPATH+=../../ python3 quadratic.py -u seed -r 10
```
```bash
(venv) $2 PYTHONPATH+=../../ python3 quadratic.py -b tcp://*:5556 -a tcp://localhost:5556 -s seed -d tcp://localhost:5555 -r 10
```

