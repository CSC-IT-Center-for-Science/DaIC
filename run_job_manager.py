import zmq
import couchdb
import json
import random
import time
from datetime import datetime
POLL_TIMEOUT = 2



def loop(poller, receiver):
    prev = now = datetime.utcnow()
    while True:
        try:
            socks = dict(poller.poll(POLL_TIMEOUT))
        except KeyboardInterrupt:
            break

        now = datetime.utcnow()

        if receiver in socks:
            raw = receiver.recv_string()
            msg = json.loads(raw)
            print(msg)
            receiver.send_string("ok")
        time.sleep(1)


def main():
    couch = couchdb.Server()
    try:
        db = couch.create('jobs')
    except couchdb.http.PreconditionFailed:
        db = couch['jobs']

    try:
        db = couch.create('workers')
    except couchdb.http.PreconditionFailed:
        db = couch['workers']



    ctx = zmq.Context()
    sender = ctx.socket(zmq.PUSH)
    sender.bind('tcp://*:5557')

    receiver = ctx.socket(zmq.REP)
    receiver.bind('tcp://*:5678')

    poller = zmq.Poller()
    poller.register(receiver, zmq.POLLIN)
    
    loop(poller, receiver)

if __name__ == '__main__':
    main()
