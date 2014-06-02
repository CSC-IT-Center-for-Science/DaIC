import zmq
import json
import logging
from datetime import datetime

from daic.utils import config_to_db_session
from daic.models import Base

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

    def _poll_sock(self, sock, timeout):
        poll = zmq.Poller()
        poll.register(sock, zmq.POLLIN)
        socks = dict(poll.poll(timeout))
        if sock in socks:
            return (True, sock.recv_string())
        else:
            return (False, None)

    def _dispatch_command(self, msg):
        if 'cmd' in msg:
            cmd = msg['cmd']
            try:
                method = getattr(self, 'handle_%s' % cmd)
                response = method(**msg)
                return response
            except AttributeError:
                logging.warn("Invalid cmd message received")
                return json.dumps({'error': 'unknown command'})
        else:
            return json.dumps({'error': 'invalid command'})

    def handle_active(self, **options):
        return json.dumps(dict([(k, "%s" % v.get('updated')) for k, v
                                in self.clients.items()]))

    def handle_list_files(self, **options):
        connector = options.get('connector')
        if connector in self.clients:
            request = {'cmd': 'list:files'}
            client_sock = self.clients[connector].get('sock')
            if client_sock:
                client_sock.send_string(json.dumps(request))
                status, resp = self._poll_sock(client_sock, POLL_TIMEOUT)
                if status:
                    encoded = json.loads(resp)
                    return json.dumps(encoded)
                else:
                    logging.warn("no response from connector")
                    client_sock.setsockopt(zmq.LINGER, 0)
                    client_sock.close()
                    self.clients.pop(connector)
                    return json.dumps([])
            else:
                return json.dumps([])

    def handle_pong(self, **options):
        if 'id' in options:
            id = options['id']
            if id not in self.clients:
                self.clients[id] = {}
                if 'endpoint' in options:
                    endpoint = options['endpoint']
                    sock = self.ctx.socket(zmq.REQ)
                    try:
                        sock.connect(endpoint)
                        self.clients[id]['sock'] = sock
                    except zmq.error.ZMQError:
                        logging.warn("received invalid endpoint", endpoint)
            self.clients[id]['updated'] = datetime.utcnow()

    def loop(self):
        prev = now = datetime.utcnow()
        while True:
            try:
                socks = dict(self.poller.poll(POLL_TIMEOUT))
            except KeyboardInterrupt:
                break

            now = datetime.utcnow()

            if self.ctl in socks:
                raw = self.ctl.recv_string()
                msg = json.loads(raw)
                response = self._dispatch_command(msg)
                self.ctl.send_string(response)

            if self.sync in socks:
                raw = self.sync.recv_string()
                msg = json.loads(raw)
                response = self._dispatch_command(msg)

            if (now - prev).total_seconds() > IDLE_TIMEOUT:
                self.clients = self.prune_dead_clients(now, self.clients)
                logging.warn("Publishing message: ping")
                self.publisher.send_string(json.dumps({'cmd': 'ping'}))
                prev = now

    def prune_dead_clients(self, ts_now, clients):
        result = {}
        for client, d in clients.items():
            if 'updated' in d:
                last_update = d['updated']
                if (ts_now - last_update).total_seconds() < 10:
                    result[client] = d
        return result
