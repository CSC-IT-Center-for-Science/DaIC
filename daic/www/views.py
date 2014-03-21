from flask import render_template
from daic.www import app


@app.route('/')
def containers():
    return render_template('containerlist.html')


@app.route('/containers/<container_id>')
def files_in_container(container_id):
    return render_template('filelist.html', container=container_id)


@app.route('/connectors')
def connectors():
    return render_template('connectorlist.html')


@app.route('/connectors/<connector_id>')
def connector_local_files(connector_id):
    return render_template('connectorfilelist.html', connector=connector_id)
