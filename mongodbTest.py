from flask import Flask, render_template
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

load_dotenv()
uri = os.getenv("MONGO_URI")

if not uri:
    raise ValueError("MONGO_URI is not set in the environment variables")

client = MongoClient(uri, server_api=ServerApi('1'))

# Test MongoDB connection and list all databases
try:
    client.admin.command('ping')
    print("Connected to MongoDB!")
    
    # Get all database names
    databases = client.list_database_names()
    print("Databases:", databases)
    print("--------------------------------------------------------------------------------------------------------------------------------------------")
except Exception as e:
    print(f"MongoDB Connection Error: {e}")
