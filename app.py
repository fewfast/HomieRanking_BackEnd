from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# โหลดค่าจาก .env
load_dotenv()

# Configurations
app = Flask(__name__)
CORS(app)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")  # ใช้คีย์ลับที่ตั้งใน .env
jwt = JWTManager(app)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db["users"]  # สมมติว่าเรามี collection ชื่อ "users"

# Endpoint: Signup (สร้างผู้ใช้ใหม่)
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    print(f"Received signup request with username: {username}, email: {email}, password: {password}")  # เพิ่ม log

    if not username or not email or not password:
        print("Missing required fields")  # เพิ่ม log
        return jsonify({"message": "Missing required fields"}), 400

    if users_collection.find_one({"email": email}):
        print(f"Email already exists: {email}")  # เพิ่ม log
        return jsonify({"message": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)

    new_user = {
        "username": username,
        "email": email,
        "password": hashed_password,
    }

    users_collection.insert_one(new_user)

    print(f"User created successfully: {email}")  # เพิ่ม log
    return jsonify({"message": "User created successfully!"}), 201

# Endpoint: Login (เข้าสู่ระบบ)
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Missing required fields"}), 400

    # ค้นหาผู้ใช้ตาม email
    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"message": "User not found"}), 404

    # ตรวจสอบรหัสผ่าน
    if not check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid password"}), 401

    # สร้าง JWT token
    access_token = create_access_token(identity={"email": user["email"], "username": user["username"]})

    return jsonify({
        "message": "Login successful",
        "access_token": access_token
    }), 200

# หน้าแรก
@app.route("/")
def home():
    return jsonify({"message": "Flask + MongoDB API Running!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)
