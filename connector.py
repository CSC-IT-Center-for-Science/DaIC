import zmq
import uuid
import json
import requests
import os
import errno


POLL_TIMEOUT = 5


def main(config):
    endpoint = config['endpoint']
    rest_endpoint = config['rest_endpoint']
    id = uuid.uuid1()
    ctx = zmq.Context()
    subsock = ctx.socket(zmq.SUB)
    subsock.connect('tcp://localhost:5555')
    subsock.setsockopt(zmq.SUBSCRIBE, b'')

    reqsock = ctx.socket(zmq.PUSH)
    reqsock.connect('tcp://localhost:5566')
    repsock = ctx.socket(zmq.REP)
    repsock.bind(endpoint)

    pong_msg = {
        'msg': 'pong',
        'id': id.get_hex(),
        'endpoint': endpoint,
        'status': 'ok'
    }

    path = config['connector_data_dir']
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise OSError("Unable to create directory")

    poller = zmq.Poller()
    poller.register(subsock, zmq.POLLIN)
    poller.register(repsock, zmq.POLLIN)

    while True:
        try:
            socks = dict(poller.poll(POLL_TIMEOUT))
        except KeyboardInterrupt:
            break

        if subsock in socks:
            raw = subsock.recv()
            print "Connector:SUB:", raw
            msg = json.loads(raw)
            if msg.get('cmd') == b'ping':
                reqsock.send(json.dumps(pong_msg))
            elif msg.get('cmd') == 'report:localresource':
                if msg.get('connector_id') == id.get_hex():
                    os.listdir(config.data_dir)
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

        elif repsock in socks:
            raw = repsock.recv()
            print "Connector:REP", raw

            repsock.send(json.dumps(os.listdir(path)))

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
