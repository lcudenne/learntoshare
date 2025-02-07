# Peer-to-peer Skeleton

Test the P2P skeleton locally on two different consoles.

```bash
(venv) $1 PYTHONPATH+=../../ python3 ./p2pskel.py -u seed
```

```bash
(venv) $2 PYTHONPATH+=../../ python3 ./p2pskel.py -b tcp://*:5556 -a tcp://localhost:5556 -s seed -d tcp://localhost:5555
```

