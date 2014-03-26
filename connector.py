import zmq
import uuid
import json
import requests
import os
import errno

POLL_TIMEOUT = 5


class Connector(object):
    def __init__(self, config):
        self.endpoint = config['endpoint']
        self.rest_endpoint = config['rest_endpoint']
        self.id = uuid.uuid1()

        self.ctx = zmq.Context()
        self.subscriber_sock = self.ctx.socket(zmq.SUB)
        self.subscriber_sock.connect('tcp://localhost:5555')
        self.subscriber_sock.setsockopt(zmq.SUBSCRIBE, b'')

        self.push_sock = self.ctx.socket(zmq.PUSH)
        self.push_sock.connect('tcp://localhost:5566')

        self.reply_sock = self.ctx.socket(zmq.REP)
        self.reply_sock.bind(self.endpoint)

        self.poller = zmq.Poller()
        self.poller.register(self.subscriber_sock, zmq.POLLIN)
        self.poller.register(self.reply_sock, zmq.POLLIN)

        self.data_dir = config['connector_data_dir']

        try:
            os.makedirs(self.data_dir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(self.data_dir):
                pass
            else:
                raise OSError("Unable to create directory")

    def run(self):
        while True:
            try:
                socks = dict(self.poller.poll(POLL_TIMEOUT))
            except KeyboardInterrupt:
                break

            if self.subscriber_sock in socks:
                raw = self.subscriber_sock.recv()
                print "Connector:SUB:", raw
                msg = json.loads(raw)
                if 'cmd' in msg:
                    cmd = msg['cmd']
                    try:
                        method = getattr(self, 'handle_%s' % cmd)
                    except AttributeError:
                        print "Invalid subscribe message received"
                    method(**msg)
                else:
                    print "Unknown msg", msg

            elif self.reply_sock in socks:
                raw = self.reply_sock.recv()
                print "Connector:REP", raw
                self.reply_sock.send(json.dumps(os.listdir(self.data_dir)))

    def _get_pong_msg(self):
        return {
            'cmd': 'pong',
            'id': self.id.get_hex(),
            'endpoint': self.endpoint,
            'status': 'ok'
        }

    def handle_ping(self, **options):
        self.push_sock.send(json.dumps(self._get_pong_msg()))

    def handle_fetch_file(self, **options):
        container_id = options.get('container_id')
        file_id = options.get('file_id')
        print "Fetching file with id: %s" % container_id
        r = requests.get("%s/containers/%s/files/%s" % (self.rest_endpoint,
                                                        container_id,
                                                        file_id))
        resp = r.json()
        filename = resp.get('filename')
        r = requests.get("%s/containers/download/%s" % (self.rest_endpoint,
                                                        container_id))
        file_path = '/tmp/connector/%s-%s-%s' % (self.id.get_hex(),
                                                 container_id,
                                                 filename)
        with open(file_path, 'wb') as fd:
            for chunk in r.iter_content(1024):
                fd.write(chunk)
        print "File stored locally with path: %s" % file_path


def main(config):
    connector = Connector(config)
    connector.run()


if __name__ == '__main__':
    import argparse
    import yaml
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    parser.add_argument('--data_dir')
    parser.add_argument('--endpoint')
    args = parser.parse_args()

    config = yaml.load(file(args.config_file))

    if args.data_dir:
        config['connector_data_dir'] = args.data_dir

    if args.endpoint:
        config['endpoint'] = args.endpoint

    main(config)
