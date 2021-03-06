from flask import Flask
from functools import wraps

app = Flask(__name__)


def with_db_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(app.config['DB'], *args, **kwargs)
    return wrapper


def with_manager_socket(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(app.config['zmqreqsock'], *args, **kwargs)
    return wrapper

import daic.www.restviews
import daic.www.views
