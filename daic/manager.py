import zmq
import json
from datetime import datetime

from daic.utils import config_to_db_session
from daic.models import Base, Resource

POLL_TIMEOUT = 1000
IDLE_TIMEOUT = 5


class DaICManager(object):

    def __init__(self, config):
        self.ctx = zmq.Context()
        self.clients = {}
        self.config = config

    def setup_zmq(self):
        self.publisher = self.ctx.socket(zmq.PUB)
        self.publisher.bind('tcp://*:5555')

        self.ctl = self.ctx.socket(zmq.REP)
        self.ctl.bind('tcp://*:5678')

        self.sync = self.ctx.socket(zmq.PULL)
        self.sync.bind('tcp://*:5566')

        self.poller = zmq.Poller()
        self.poller.register(self.sync, zmq.POLLIN)
        self.poller.register(self.ctl, zmq.POLLIN)

    def setup_db(self):
        self.db = config_to_db_session(self.config, Base)

    def loop(self):
        prev = now = datetime.utcnow()
        while True:
            try:
                socks = dict(self.poller.poll(POLL_TIMEOUT))
            except KeyboardInterrupt:
                break

            now = datetime.utcnow()

            if self.ctl in socks:
                raw = self.ctl.recv()
                print "CtlRq", raw
                msg = json.loads(raw)
                # XXX: Implement proper parser and dispatcher
                if msg.get('cmd') == 'active':
                    self.ctl.send(json.dumps(dict([(k, "%s" % v)
                                  for k, v in self.clients.items()])))
                elif msg.get('cmd') == 'containers':
                    cs = [{'id': x.uuid, 'name': x.name} for x
                          in self.db.query(Resource).all()]
                    self.ctl.send(json.dumps(cs))
                elif msg.get('cmd') == 'clients:fetch':
                    container = msg.get('container')
                    if container in set([x.uuid for x
                                         in self.db.query(Resource).all()]):
                        cmd = {'cmd': 'fetch:container',
                               'container': container}
                        self.publisher.send(json.dumps(cmd))
                        self.ctl.send("ok")
                    else:
                        self.ctl.send("no such container")

            if self.sync in socks:
                raw = self.sync.recv()
                print "PullRq", raw
                msg = json.loads(raw)
                if 'id' in msg:
                    self.clients[msg['id']] = datetime.utcnow()

            if (now - prev).total_seconds() > IDLE_TIMEOUT:
                self.clients = self.prune_dead_clients(now, self.clients)
                print "Publishing message: ping"
                self.publisher.send(json.dumps({'cmd': 'ping'}))
                prev = now

    def prune_dead_clients(self, ts_now, clients):
        result = {}
        for client, last_update in clients.items():
            if (ts_now - last_update).total_seconds() < 10:
                result[client] = last_update
        return result
