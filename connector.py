import zmq
import uuid
import json
import requests


def main(config):
    rest_endpoint = config['rest_endpoint']
    id = uuid.uuid1()
    ctx = zmq.Context()
    subsock = ctx.socket(zmq.SUB)
    subsock.connect('tcp://localhost:5555')
    subsock.setsockopt(zmq.SUBSCRIBE, b'')

    reqsock = ctx.socket(zmq.PUSH)
    reqsock.connect('tcp://localhost:5566')

    pong_msg = {
        'msg': 'pong',
        'id': id.get_hex(),
        'status': 'ok'
    }

    while True:
        raw = subsock.recv()
        print "Q:", raw
        msg = json.loads(raw)
        if msg.get('cmd') == b'ping':
            reqsock.send(json.dumps(pong_msg))
        elif msg.get('cmd') == 'fetch:container':
            container_id = msg.get('container')
            print "Fetching file with id: %s" % container_id
            r = requests.get("%s/containers/%s" % (rest_endpoint,
                                                   container_id))
            resp = r.json()
            filename = resp.get('filename')
            r = requests.get("%s/containers/download/%s" % (rest_endpoint,
                                                            container_id))
            file_path = '/tmp/connector/%s-%s-%s' % (id.get_hex(),
                                                     container_id,
                                                     filename)
            with open(file_path, 'wb') as fd:
                for chunk in r.iter_content(1024):
                    fd.write(chunk)
            print "File stored locally with path: %s" % file_path
        else:
            reqsock.send(json.dumps(''.join(reversed([x for x in msg]))))


if __name__ == '__main__':
    import argparse
    import yaml
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    args = parser.parse_args()

    config = yaml.load(file(args.config_file))
    main(config)
