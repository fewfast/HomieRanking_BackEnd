from flask import Flask, render_template
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://HomieRanking:9NZWKcQB4HWCdjUc@mydb.uxw7p.mongodb.net/?retryWrites=true&w=majority&appName=mydb"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html", title="Hello")
