import zmq
import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--command')
    parser.add_argument('--container')
    parser.add_argument('--connector')
    args = parser.parse_args()
    cmd = args.command
    container = args.container
    connector = args.connector

    encoded = {'cmd': cmd}
    if container:
        encoded['container'] = container

    if connector:
        encoded['connector'] = connector

    print "Rq:", cmd
    ctx = zmq.Context()
    sock = ctx.socket(zmq.REQ)
    sock.connect('tcp://localhost:5678')
    sock.send(json.dumps(encoded))
    resp = sock.recv()
    print "Rs:", resp

if __name__ == '__main__':
    main()
