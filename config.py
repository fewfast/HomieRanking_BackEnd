import os
from pymongo import MongoClient
from dotenv import load_dotenv

# โหลดค่าจาก .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE")
JWT_SECRET = os.getenv("JWT_SECRET")

# เชื่อมต่อ MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
