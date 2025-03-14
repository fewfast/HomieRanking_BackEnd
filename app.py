from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import timedelta


# โหลดค่าจาก .env
load_dotenv()

# Configurations
app = Flask(__name__)
CORS(app)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")  # ใช้คีย์ลับที่ตั้งใน .env
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=365*10)
jwt = JWTManager(app)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db["users"]  # สมมติว่าเรามี collection ชื่อ "users"
data_collection = db["data"]  # เพิ่ม collection ชื่อ "data"

# ตั้งค่าการอัปโหลดไฟล์
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
        "password": hashed_password
    }

    users_collection.insert_one(new_user)

    print(f"User created successfully: {email}")  # เพิ่ม log
    return jsonify({"message": "User created successfully!"}), 201

# Endpoint: Login (เข้าสู่ระบบ)
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Missing required fields"}), 400

    user = users_collection.find_one({"username": username})
    if not user:
        return jsonify({"message": "User not found"}),

    # ตรวจสอบรหัสผ่าน
    if not check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid password"}), 401

    # สร้าง JWT token
    access_token = create_access_token(identity=username)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token
    }), 200

# หน้าแรก
@app.route("/")
def home():
    return jsonify({"message": "Flask + MongoDB API Running!"}), 200

# Endpoint: Upload
@app.route("/upload", methods=['POST'])
@jwt_required()
def upload():
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        # Log the current_user to verify its structure
        print(f"Current user: {current_user}")

        # Ensure images is a list
        images = data.get("images")
        if not isinstance(images, list):
            images = [images]

        # Ensure image_names is a list
        image_names = data.get("image_names")
        if not isinstance(image_names, list):
            image_names = [image_names]

        # Combine images and image_names into a list of dictionaries
        images_with_names = [{"image": img, "name": name} for img, name in zip(images, image_names)]

        new_quiz = {
            "title": data.get("title"),
            "description": data.get("description"),
            "categories": data.get("categories"),
            "thumbnail": data.get("thumbnail"),
            "images": images_with_names,
            "uploaded_by": current_user # Change to username
        }

        quiz_id = data_collection.insert_one(new_quiz).inserted_id

        new_quiz["_id"] = str(quiz_id)  # Convert ObjectId to string

        print(f"New quiz uploaded by {current_user['username']}: {new_quiz}")  # Add logging

        return jsonify(new_quiz), 201

    except Exception as e:
        print(f"Error: {e}")  # Log error
        return jsonify({"error": "Internal Server Error"}), 500

# Endpoint: Get Quizzes
@app.route("/get_quizzes", methods=["GET"])
@jwt_required()
def get_quizzes():
    try:
        quizzes = data_collection.find({}, {"_id": 1, "title": 1, "description": 1, "categories": 1, "thumbnail": 1, "images": 1, "uploaded_by": 1})
        quizzes_list = []
        for quiz in quizzes:
            quiz["_id"] = str(quiz["_id"])  # Convert ObjectId to string
            quizzes_list.append(quiz)
        return jsonify(quizzes_list), 200
    except Exception as error:
        print(f"Error getting quizzes: {error}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)