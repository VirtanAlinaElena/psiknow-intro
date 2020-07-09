import os 
from werkzeug.utils import secure_filename
from flask import Flask, render_template, url_for, request, redirect,  send_from_directory, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
from bs4 import BeautifulSoup
import requests
from requests import get
import getpass

UPLOAD_DIRECTORY = "/home/alina/Desktop/psiknow-intro/server-files"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_DIRECTORY'] = UPLOAD_DIRECTORY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    filehash = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

def sha1file(filepath):
    # This function calculates the sha1 hexdigest for a given file
    with open(filepath, "rb") as f:
        hash_sha1 = hashlib.sha1()
        for chunk in iter(lambda: f.read(2 ** 20), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()

# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'student' and request.form['password'] == 'student':
            return redirect('/download')
        else:
            if request.form['username'] == 'admin' and request.form['password'] == 'admin':
                return redirect ('/')
            else:
                error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return jsonify({"success:": False, "reason":'There was an issue adding your task'})

    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', tasks=tasks)

""" SERVER FUNCTIONALITIES """

@app.route("/upload-file", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        file = request.files["file"]
        if file.filename == '':
            print ('no filename')
            return redirect(request.url)
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_DIRECTORY'], filename))
            new_task = Todo(content=filename, filehash=sha1file(UPLOAD_DIRECTORY + "/" + filename))
            try:
                db.session.add(new_task)
                db.session.commit()
                return redirect('/')
            except:
                return jsonify({"success:": False, "reason":'There was an issue adding your file'})

    return redirect('/')


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        filename = secure_filename(task_to_delete.content)
        os.remove(os.path.join(app.config['UPLOAD_DIRECTORY'], filename))
        return redirect('/')
    except:
        return jsonify({"success": False, "reason": "There was a problem deleting that file."})


@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        file = request.files["file"]
        if file.filename == '':
            print ('no filename')
            return redirect(request.url)
        else:
            os.remove(os.path.join(app.config['UPLOAD_DIRECTORY'], task.content))
            task.content = file.filename
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_DIRECTORY'], filename))
            task.filehash = sha1file(UPLOAD_DIRECTORY + "/" + filename)
            try:
                db.session.commit()
                return redirect('/')
            except:
                return jsonify({"success": False, "reason": "here was an issue updating this file."})
    else:
        return render_template('update.html', task=task)

""" CLIENT FUNCTIONALITIES """

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    directory  = "/home/alina/Desktop/psiknow-intro/server-files"
    return send_from_directory(directory, filename, as_attachment=True)


@app.route('/download', methods=['GET'])
def download_all():
    domain = "http://127.0.0.1:5000"
    page = requests.get("http://127.0.0.1:5000/")
    html = page.text
    soup = BeautifulSoup(html, "html.parser")

    directory = "/home/" + getpass.getuser() + "/Downloads/client/"
    if not os.path.exists(directory):
        os.makedirs(directory)
    query = db.session.query(Todo)
    for task in query:
        samefile_found = False
        updatedfile_found = False
        for filename in os.listdir(directory):
            path = directory + filename
            if sha1file(path) == task.filehash:
                print("wtf")
                samefile_found = True
                break
            if filename == task.content and sha1file(path) != task.filehash:
                updatedfile_found = True
                with open(path, "wb") as f:
                    print("modify")
                    url = "/download/" + task.content
                    response = get(domain + url)
                    f.write(response.content)
                break
        
        if samefile_found == True or updatedfile_found == True:
            continue

        if samefile_found == False:
            path = directory + task.content
            with open(path, "wb") as f:
                print("write for the first time")
                url = "/download/" + task.content
                response = get(domain + url)
                f.write(response.content)

    return render_template('download.html')
    

if __name__ == "__main__":
    app.run(debug=True)