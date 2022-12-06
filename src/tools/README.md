# Tools

## Building the communication graph (`draw_overlay.py`)

Install Python dependencies:

```bash
(venv) $ cd src/tools
(venv) $ pip install -r requirements.txt
```

Create a log file, for example:

```bash
(venv) $ PYTHONPATH+=../../ python3 ../tests/overlay.py &> log
```

Generate the connection graph:

```bash
(venv) $ PYTHONPATH+=../../ python3 ./draw_overlay.py -f log
```

The `-f`/`--logfiles` option accepts several arguments. For example:

```bash
(venv) $ PYTHONPATH+=../../ python3 ./draw_overlay.py -f path/to/log_peer0 path/to/log_peer1 path/to/log_peer2
```

