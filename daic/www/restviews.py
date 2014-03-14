from flask import (abort, jsonify, request, send_from_directory)
from werkzeug.utils import secure_filename

import json
import uuid
import os

from daic.models import Resource, UploadToken
from daic.www import app, with_db_session


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
    return json.dumps([{'id': x.uuid, 'name': x.name}
                       for x in session.query(Resource).all()],
                      indent=4)


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
        return send_from_directory(app.config['UPLOAD_FOLDER'], container.name)
    else:
        abort(404)
