import hashlib
import os
from bs4 import BeautifulSoup
import requests
from requests import get
from app import db, Todo, sha1file
import getpass

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
    