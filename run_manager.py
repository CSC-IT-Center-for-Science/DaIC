import argparse
import yaml

from daic.manager import DaICManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    args = parser.parse_args()

    config = yaml.load(open(args.config_file))

    manager = DaICManager(config)
    manager.setup_zmq()
    manager.setup_db()
    manager.loop()

if __name__ == '__main__':
    main()
