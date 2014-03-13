import zmq
import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--command')
    parser.add_argument('--container')
    args = parser.parse_args()
    cmd = args.command
    container = args.container

    encoded = {'cmd': cmd}
    if container:
        encoded['container'] = container

    print "Rq:", cmd
    ctx = zmq.Context()
    sock = ctx.socket(zmq.REQ)
    sock.connect('tcp://localhost:5678')
    sock.send(json.dumps(encoded))
    resp = sock.recv()
    print "Rs:", resp

if __name__ == '__main__':
    main()
