from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from getpass import getpass
from os import getenv
from functools import wraps

import hashlib
import logging


def get_from_env_or_prompt(varname, echo=True):
    value = getenv(varname)
    if value is None:
        if echo:
            value = raw_input('%s not found in env. Please enter it: ' % varname)
        else:
            value = getpass('%s not found in env. Please enter it: ' % varname)
    return value


def config_to_db_session(config, Base):
    if config['database_dialect'] == 'sqlite':
        connect_string = 'sqlite://%s' % config['database_connect_string']
    else:
        connect_string = '%(dialect)s://%(user)s:%(password)s%(connect_string)s' % \
            {'dialect': config['database_dialect'],
             'user': get_from_env_or_prompt('DATABASE_USER'),
             'password': get_from_env_or_prompt('DATABASE_PASSWORD'),
             'connect_string': config['database_connect_string']}
    engine = create_engine(connect_string)

    if config['database_dialect'] == 'sqlite':
        def _fk_pragma_on_connect(dbapi_con, con_record):
            cursor = dbapi_con.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        event.listen(engine, 'connect', _fk_pragma_on_connect)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def calculate_sha1(fn):
    with open(fn, 'rb') as f:
        h = hashlib.sha1()
        for block in f:
            h.update(block)
        return h.hexdigest()


def func_debug(func):
    """ Debug function printing the function name upon function call
    """
    msg = func.__name__

    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.log(logging.DEBUG, "%s", msg)
        return func(*args, **kwargs)
    return wrapper
