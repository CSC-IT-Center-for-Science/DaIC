try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': '',
    'author': 'CSC - IT Center for Science Ltd.',
    'url': 'http://www.csc.fi',
    'download_url': '',
    'author_email': '',
    'version': '0.1',
    'install_requires': ['nose', 'flask', 'sqlalchemy', 'flask-restful',
                         'flask-httpauth', 'pyzmq', 'requests'],
    'packages': ['daic'],
    'scripts': ['run_flask.py', 'manager.py', 'connector.py', 'ctl.py'],
    'name': 'daic'
}

setup(**config)
