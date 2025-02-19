# Peer-to-peer Skeleton

Test the P2P skeleton locally on two different consoles.

## Cold start

Set your virtual environment.

```bash
$ cd apps/optuna_p2p
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r ../../requirements.txt
(venv) $ pip install -r requirements.txt
```

Single instance:

```bash
(venv) $1 PYTHONPATH+=../../ python3 ./genscng.py -i /path/to/input/image
```



## Multi-agent

```bash
(venv) $1 PYTHONPATH+=../../ python3 ./genscng.py -u seed
```

```bash
(venv) $2 PYTHONPATH+=../../ python3 ./genscng.py -b tcp://*:5556 -a tcp://localhost:5556 -s seed -d tcp://localhost:5555
```

