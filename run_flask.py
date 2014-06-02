import zmq
import yaml
import argparse

from daic.www import app
from daic.models import Base
from daic.utils import config_to_db_session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    args = parser.parse_args()

    config = yaml.load(open(args.config_file))
    upload_folder = config.get('uploap_folder', '/tmp/flask')
    content_folder = config.get('content_folder', '/tmp/daic')

    ctx = zmq.Context()
    app.config['zmqsock'] = ctx.socket(zmq.PUSH)
    app.config['zmqsock'].connect('tcp://localhost:5566')

    app.config['zmqreqsock'] = ctx.socket(zmq.REQ)
    app.config['zmqreqsock'].connect('tcp://localhost:5678')

    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['CONTENT_FOLDER'] = content_folder
    app.config['DB'] = config_to_db_session(config, Base)
    app.run(debug=config.get('debug'))

if __name__ == '__main__':
    main()
