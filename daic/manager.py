import zmq
import json
from datetime import datetime

from daic.utils import config_to_db_session
from daic.models import Base, File, Container, Content

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
                    self.ctl.send(json.dumps(dict([(k, "%s" % v.get('updated'))
                                  for k, v in self.clients.items()])))
                elif msg.get('cmd') == 'list:files':
                    connector = msg.get('connector')
                    if connector in self.clients:
                        request = {'cmd': 'list:files'}
                        self.clients[connector]['sock'].send(json.dumps(request))
                        resp = self.clients[connector]['sock'].recv()
                        encoded = json.loads(resp)
                        print encoded
                        self.ctl.send(json.dumps(encoded))
                    else:
                        self.ctl.send("invalid command")
                else:
                    self.ctl.send("unknown command")

            if self.sync in socks:
                raw = self.sync.recv()
                print "PullRq", raw
                msg = json.loads(raw)
                if 'id' in msg and msg.get('msg') == 'pong':
                    if msg['id'] not in self.clients:
                        self.clients[msg['id']] = {}
                        if 'endpoint' in msg:
                            sock = self.ctx.socket(zmq.REQ)
                            sock.connect(msg['endpoint'])
                            self.clients[msg['id']]['sock'] = sock
                        else:
                            continue
                    self.clients[msg['id']]['updated'] = datetime.utcnow()

                if 'id' in msg and msg.get('cmd') == 'ui:delete-file':
                    print "Deleted file", msg.get('id')

            if (now - prev).total_seconds() > IDLE_TIMEOUT:
                self.clients = self.prune_dead_clients(now, self.clients)
                print "Publishing message: ping"
                self.publisher.send(json.dumps({'cmd': 'ping'}))
                prev = now

    def prune_dead_clients(self, ts_now, clients):
        result = {}
        for client, d in clients.items():
            if 'updated' in d:
                last_update = d['updated']
                if (ts_now - last_update).total_seconds() < 10:
                    result[client] = d
        return result
