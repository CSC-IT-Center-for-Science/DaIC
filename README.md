DaIC
====

File broker PoC

## Installation ##

1. `git clone https://github.com/CSC-IT-Center-for-Science/DaIC.git`
2. cd DaIC
3. mkvirtualenv my_virtual_env
4. pip install -r requirements.txt
> This will install ZMQ bindings for Python. ZMQ is prefferred to be installed
> in the system separately. If this is not the case the PyZMQ will try to
> compile and install libzmq as a Python extension. This requires development
> files for your Python installation to be installed as well as essential build
> tools for C++.


## System components ##

### REST/Web interface ###

python run_flask.py config.yaml

### Manager ###

`python run_manager.py config.yaml`

### Connectors ###

`python connector.py config.yaml --endpoint "tcp://<address>:<port>" --data_dir <path>`
