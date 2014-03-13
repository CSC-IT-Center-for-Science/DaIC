from flask import (Flask, abort, jsonify, request, send_from_directory)
from werkzeug.utils import secure_filename
from functools import wraps
import uuid
import os

from daic.utils import config_to_db_session
from daic.models import Base, Resource, UploadToken

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/flask'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def with_db_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(app.config['DB'], *args, **kwargs)
    return wrapper


@app.route('/')
def api_root():
    return '/v1'


@app.route('/v1')
def api_root_v1():
    return '''<ul>
    <li>/v1/containers [GET]</li>
    <li>/v1/containers/(container_id) [GET]</li>
    <li>/v1/containers/download/(container_id) [GET]</li>
    <li>/v1/containers/upload [POST]</li>
    <li>/v1/containers/token [GET, POST]</li>'''


@app.route('/v1/containers', methods=['GET', 'POST'])
@with_db_session
def api_list_containers(session):
    return jsonify({'status': 'ok',
                    'containers': [{'id': x.uuid, 'name': x.name}
                                   for x in session.query(Resource).all()]})


@with_db_session
def get_container(session, container_id):
    return session.query(Resource).filter_by(uuid=container_id).first()


@with_db_session
def get_container_token(session, container_token):
    return session.query(UploadToken).filter_by(uuid=container_token).first()


@app.route('/v1/containers/<container_id>')
def api_get_container(container_id):
    container = get_container(container_id)
    if container:
        return jsonify({'id': container.uuid,
                        'name': container.name})
    else:
        return jsonify({'status': 'error', 'reason': 'No such container'})


@app.route('/v1/containers/token', methods=['GET', 'POST'])
@with_db_session
def api_create_upload_token(session):
    token = UploadToken()
    token.uuid = uuid.uuid1().get_hex()
    session.add(token)
    session.commit()
    return jsonify({'id': token.uuid})


@app.route('/v1/containers/upload/<container_token>', methods=['GET', 'POST'])
@with_db_session
def api_put_container(session, container_token):
    container_token = get_container_token(container_token)
    if not container_token:
        return 'invalid container token'

    if request.method == 'POST':
        upload = request.files['file']
        if upload:
            filename = secure_filename(upload.filename)
            upload.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_uuid = uuid.uuid1().get_hex()
            resource = Resource()
            resource.name = filename
            resource.uuid = file_uuid
            session.add(resource)
            session.delete(container_token)
            session.commit()
        return jsonify({'id': file_uuid})
    else:
        return '''
            <!doctype html>
            <title>Upload new File</title>
            <h1>Upload new File</h1>
            <form action="" method=post enctype=multipart/form-data>
              <p><input type=file name=file>
                 <input type=submit value=Upload>
            </form>
        '''


@app.route('/v1/containers/download/<container_id>')
@with_db_session
def download_container(session, container_id):
    container = get_container(container_id)
    if container:
        return send_from_directory(UPLOAD_FOLDER, container.name)
    else:
        abort(404)


if __name__ == '__main__':
    import yaml
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    args = parser.parse_args()

    config = yaml.load(file(args.config_file))
    UPLOAD_FOLDER = config.get('uploap_folder', '/tmp')
    app.config['DB'] = config_to_db_session(config, Base)
    app.run(debug=config.get('debug'))
