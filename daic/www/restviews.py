from flask import (abort, jsonify, request, send_from_directory)
from werkzeug.utils import secure_filename
from datetime import datetime

import logging
import json
import uuid
import os
import shutil

from daic.models import Container, Content, File, UploadToken
from daic.www import app, with_db_session, with_manager_socket
from daic.utils import calculate_sha1


@with_db_session
def get_container(session, container_uuid):
    return session.query(Container).filter_by(uuid=container_uuid).first()


@with_db_session
def get_file(session, container_uuid, file_uuid):
    container = get_container(container_uuid)
    if not container:
        abort(404)
    return session.query(File).filter_by(container=container.id,
                                         uuid=file_uuid).first()


@with_db_session
def get_container_token(session, container_token):
    return session.query(UploadToken).filter_by(uuid=container_token).first()


@with_db_session
def get_content(session, container_id, file_id):
    file_obj = get_file(container_id, file_id)
    if not file_obj:
        abort(404)
    content = session.query(Content).filter_by(id=file_obj.content).first()

    if not content:
        abort(500)
    return content


@with_db_session
def get_content_by_checksum(session, checksum):
    return session.query(Content).filter_by(checksum=checksum).first()


@with_db_session
def remove_file_object(session, file_obj):
    files = session.query(File).filter_by(content=file_obj.content).all()
    session.delete(file_obj)
    session.commit()

    if len(files) == 1:
        remove_content(session, file_obj)


def remove_content(session, file_obj):
    content = session.query(Content).filter_by(id=file_obj.content).first()
    try:
        path = os.path.join(app.config['CONTENT_FOLDER'], content.checksum)
        os.remove(path)
    except:
        logging.warn("Unable to remove path", path)
    session.delete(content)
    session.commit()


@app.route('/v1')
def api_root_v1():
    return jsonify({'version': 1})


@app.route('/v1/connectors', methods=['GET'])
@with_manager_socket
def api_list_connectors(socket):
    """
    Return a list of currently active connectors from manager process.
    XXX: REQ socket operations might hang if manager process is unavailable
    """
    command = {'cmd': 'active'}
    socket.send_string(json.dumps(command))
    resp = socket.recv_string()
    encoded = json.loads(resp)
    return json.dumps([{'id': k, 'updated': v} for k, v in encoded.items()])


@app.route('/v1/connectors/<connector_id>', methods=['GET'])
@with_manager_socket
def api_list_connector_files(socket, connector_id):
    """
    Return a list of local files from connector. Manager process is used as a
    proxy.
    XXX: REQ socket operations might hang if manager process is unavailable
    """
    command = {'cmd': 'list_files', 'connector': connector_id}
    socket.send_string(json.dumps(command))
    resp = socket.recv_string()
    encoded = json.loads(resp)
    for i in range(len(encoded)):
        encoded[i] = {'id': i, 'name': encoded[i]}
    return json.dumps(encoded)


@app.route('/v1/containers', methods=['GET'])
@with_db_session
def api_list_containers(session):
    """
    List all available containers.
    """
    return json.dumps([{'id': x.uuid, 'name': x.name}
                       for x in session.query(Container).all()])


@app.route('/v1/containers/<container_id>', methods=['GET'])
@app.route('/v1/containers/<container_id>/files', methods=['GET'])
@with_db_session
def api_get_container(session, container_id):
    """
    Return a container if a container with given id exists.
    """
    container = get_container(container_id)
    if container:
        files = [{'id': x.uuid, 'name': x.name} for x
                 in session.query(File).filter(File.container == container.id)]
        return jsonify({'id': container.uuid,
                        'name': container.name,
                        'files': files})
    else:
        return abort(404)


@app.route('/v1/containers/<container_id>/clone', methods=['POST'])
@with_db_session
def api_clone_container(session, container_id):
    containers = dict([(x.uuid, x) for x in session.query(Container).all()])

    if container_id not in containers:
        return abort(404)

    container = containers[container_id]

    cont_clone = Container()
    cont_clone.name = container.name
    cont_clone.create_ts = datetime.utcnow()

    session.add(cont_clone)
    session.commit()
    session.refresh(cont_clone)

    for obj in session.query(File).filter_by(container=container.id).all():
        file_clone = File()
        file_clone.name = obj.name
        file_clone.content = obj.content
        file_clone.container = cont_clone.id
        file_clone.meta = ""
        session.add(file_clone)
        session.commit()

    return jsonify({'uuid': cont_clone.uuid})


@app.route('/v1/containers/<container_id>/files/<file_id>', methods=['GET'])
@with_db_session
def api_get_file_from_container(session, container_id, file_id):
    """
    Return metadata associated with a file in given container.
    """
    resource = get_file(container_id, file_id)
    if not resource:
        abort(404)

    return jsonify(resource.to_dict())


@app.route('/v1/containers/<container_id>/files/<file_id>', methods=['POST'])
@with_db_session
def api_add_metadata_field(session, container_id, file_id):
    """
    Add or update fields in the metadata dictionary of a file object
    """
    params = dict(request.form.items())
    resource = get_file(container_id, file_id)
    try:
        meta = resource.meta
    except:
        meta = {}
    for k, v in params.items():
        if v:
            meta[k] = v
        elif k in meta and not v:
            meta.pop(k)
    resource.meta = meta
    session.merge(resource)
    session.commit()

    return jsonify(resource.to_dict())


@app.route('/v1/containers/token', methods=['GET', 'POST'])
@with_db_session
def api_create_upload_token(session):
    raise RuntimeError("Not implemented")


@app.route('/v1/containers', methods=['POST'])
@with_db_session
def api_create_container(session):
    """
    Create a new container with name given in form parameters.
    """
    if request.method == 'POST':
        params = dict(request.form.items())
        if 'name' in params:
            container = Container()
            container.name = params['name']
            container.create_ts = datetime.utcnow()
            session.add(container)
            session.commit()
            return jsonify({'uuid': container.uuid})
        else:
            abort(400)


@app.route('/v1/containers/<container_id>/files', methods=['POST'])
@with_db_session
def api_create_file(session, container_id):
    """
    Create a new file resource with data taken from form upload.
    XXX: Streamed upload and hash calculation are required for efficient
    uploads.
    """
    try:
        os.stat(app.config['UPLOAD_FOLDER'])
    except OSError:
        os.makedirs(app.config['UPLOAD_FOLDER'])

    try:
        os.stat(app.config['CONTENT_FOLDER'])
    except OSError:
        os.makedirs(app.config['CONTENT_FOLDER'])

    if request.method == 'POST':
        container = get_container(container_id)
        if not container:
            abort(404)
        upload = request.files['file']
        if upload:
            filename = secure_filename(upload.filename)
            tmp_name = uuid.uuid1().hex
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], tmp_name)
            upload.save(upload_path)

            checksum = calculate_sha1(upload_path)
            content = get_content_by_checksum(checksum)

            if not content:
                content = Content()
                content.checksum = checksum
                content.size = upload.content_length
                session.add(content)
                session.commit()
                session.refresh(content)
                content_path = os.path.join(app.config['CONTENT_FOLDER'],
                                            checksum)
                shutil.move(upload_path, content_path)

            file = File()
            file.name = filename
            file.container = container.id
            file.content = content.id

            session.add(file)
            session.commit()

            return jsonify({'id': file.uuid})
        else:
            abort(400)


@app.route('/v1/containers/<container_id>', methods=['DELETE'])
@with_db_session
def api_delete_container(session, container_id):
    """
    Delete given container if it exists. Remove any file resources in that
    container.
    """
    container = get_container(container_id)
    if not container:
        abort(404)

    for fileobj in session.query(File).filter(File.container == container.id):
        remove_file_object(fileobj)

    session.delete(container)
    session.commit()
    return jsonify({})


@app.route('/v1/containers/<container_id>/files/<file_id>', methods=['DELETE'])
@with_db_session
def api_delete_file(session, container_id, file_id):
    """
    Delete given file in given container.
    """
    container = get_container(container_id)
    file_obj = get_file(container_id, file_id)
    if not file_obj or not container:
        abort(404)
    if request.method == 'DELETE':
        remove_file_object(file_obj)
        app.config['zmqsock'].send(json.dumps({'cmd': 'ui:delete-file',
                                               'file_id': file_id,
                                               'container_id': container_id}))
    return jsonify({})


@app.route('/v1/containers/<container_id>/files/<file_id>/download')
@with_db_session
def api_download_file(session, container_id, file_id):
    """
    Get the file contents from a file resource in given container.
    """
    content = get_content(container_id, file_id)
    if content:
        return send_from_directory(app.config['CONTENT_FOLDER'],
                                   content.checksum)
    else:
        abort(404)
