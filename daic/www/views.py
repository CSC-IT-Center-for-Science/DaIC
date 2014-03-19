from flask import render_template
from daic.www import app


@app.route('/')
def containers():
    return render_template('containerlist.html')


@app.route('/containers/<container_id>')
def files_in_container(container_id):
    return render_template('filelist.html', container=container_id)
