from flask import send_file
from daic.www import app


@app.route('/')
def index():
    return send_file(app.root_path+'/templates/index.html')
