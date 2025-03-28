from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import timedelta
from bson import ObjectId

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
    password = data.get("password")
    profile = data.get("profile", "")
    wallpaper = data.get("wallpaper", "")
    description_profile = data.get("description_profile", "")
    following = data.get("following", [])

    print(f"Received signup request with username: {username}, password: {password}")  # เพิ่ม log

    if not username or not password:
        print("Missing required fields")  # เพิ่ม log
        return jsonify({"message": "Missing required fields"}), 400

    if users_collection.find_one({"username": username}):
        print(f"Username already exists: {username}")  # เพิ่ม log
        return jsonify({"message": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)

    new_user = {
        "username": username,
        "password": hashed_password,
        "profile": profile,
        "wallpaper": wallpaper,
        "description_profile": description_profile,
        "following": following
    }

    users_collection.insert_one(new_user)

    print(f"User created successfully: {username}")  # เพิ่ม log
    return jsonify({"message": "Successfully!"}), 201

# Endpoint: Login (เข้าสู่ระบบ)
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Missing required fields"}), 400

    # ค้นหาผู้ใช้ตาม username
    user = users_collection.find_one({"username": username})
    if not user:
        return jsonify({"message": "User not found"}), 404

    # ตรวจสอบรหัสผ่าน
    if not check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid password"}), 401

    # สร้าง JWT token
    access_token = create_access_token(identity=username)

    user_profile = {
        "_id": str(user["_id"]),
        "username": user["username"],
        "profile": user.get("profile"),
        "wallpaper": user.get("wallpaper"),
        "description_profile": user.get("description_profile"),
        "following": user.get("following")
    }

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": user_profile
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
            "uploaded_by": current_user 
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
def get_quizzes():
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "uploaded_by",
                    "foreignField": "username",  # เพราะตอนนี้ uploaded_by คือ username ที่ได้จาก get_jwt_identity()
                    "as": "uploader"
                }
            },
            {"$unwind": "$uploader"},
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "description": 1,
                    "categories": 1,
                    "thumbnail": 1,
                    "images": 1,
                    "uploaded_by": 1,
                    "uploader.username": 1,
                    "uploader.profile": 1,
                    "uploader.description_profile": 1,
                    "uploader.wallpaper": 1,
                    "uploader._id": 1,
                    "uploader.following": 1 
                } # จะมีข้อมูลจาก content + ข้อมูลของคนที่ลง content
            }
        ]
        quizzes = list(data_collection.aggregate(pipeline))
        for quiz in quizzes:
            # Convert ObjectId to string
            quiz["_id"] = str(quiz["_id"]) 
            quiz["uploader"]["_id"] = str(quiz["uploader"]["_id"])
            

        return jsonify(quizzes), 200
    except Exception as error:
        print(f"Error getting quizzes: {error}")
        return jsonify({"error": "Internal Server Error"}), 500

# Endpoint: Update Quiz by ID
@app.route("/update_quiz/<string:_id>", methods=["PUT"])
@jwt_required()
def update_quiz(_id):
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        # Validate input data
        if not data:
            return jsonify({"message": "No data provided"}), 400

        # Find the quiz by _id
        quiz = data_collection.find_one({"_id": ObjectId(_id)})
        if not quiz:
            return jsonify({"message": "Quiz not found"}), 404

       # Combine images and image_names into a list of dictionaries
        images = data.get("images", [])
        image_names = data.get("image_names", [])
        images_with_names = [{"image": img, "name": name} for img, name in zip(images, image_names)]

        # Update the quiz fields
        updated_quiz = {
        "title": data.get("title", quiz["title"]),
        "description": data.get("description", quiz["description"]),
        "categories": data.get("categories", quiz["categories"]),
        "thumbnail": data.get("thumbnail", quiz["thumbnail"]),
        "images": images_with_names,
        }   

        # Update the quiz in the database
        result = data_collection.update_one({"_id": ObjectId(_id)}, {"$set": updated_quiz})

        if result.modified_count == 0:
            return jsonify({"message": "No changes made to the quiz"}), 200

        updated_quiz["_id"] = str(quiz["_id"])  # Convert ObjectId to string

        return jsonify(updated_quiz), 200

    except Exception as error:
        print(f"Error updating quiz: {error}")
        return jsonify({"error": "Internal Server Error"}), 500
    
# Endpoint:  Delete Quiz by ID
@app.route("/delete_quiz/<string:_id>", methods=["DELETE"])
@jwt_required()
def delete_quiz(_id):
    try:
        current_user = get_jwt_identity()

        # Find the quiz by _id
        quiz = data_collection.find_one({"_id": ObjectId(_id)})
        if not quiz:
            return jsonify({"message": "Quiz not found"}), 404

        # Check if the current user is the owner of the quiz
        if quiz["uploaded_by"] != current_user:
            return jsonify({"message": "You are not authorized to delete this quiz"}), 403

        # Delete the quiz from the database
        result = data_collection.delete_one({"_id": ObjectId(_id)})

        if result.deleted_count == 0:
            return jsonify({"message": "Failed to delete the quiz"}), 500

        return jsonify({"message": "Quiz deleted successfully"}), 200

    except Exception as error:
        print(f"Error deleting quiz: {error}")
        return jsonify({"error": "Internal Server Error"}), 500
    
# Endpoint: Update Profile by ID
@app.route("/update_profile/<string:_id>", methods=["PUT"])
@jwt_required()
def update_profile(_id):
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        # Validate input data
        if not data:
            return jsonify({"message": "No data provided"}), 400

        # หา user ที่มี id
        user = users_collection.find_one({"_id": ObjectId(_id)})
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Update profile fields
        updated_profile = {
            "description_profile": data.get("description_profile", user["description_profile"]),
            "profile": data.get("profile", user["profile"]),
            "wallpaper": data.get("wallpaper", user["wallpaper"]),
        }

        # Update the user profile in the database
        result = users_collection.update_one({"_id": ObjectId(_id)}, {"$set": updated_profile})

        if result.modified_count == 0:
            return jsonify({"message": "No changes made to the profile"}), 200

        updated_profile["_id"] = str(user["_id"])  # Convert ObjectId to string

        return jsonify(updated_profile), 200

    except Exception as error:
        print(f"Error updating profile: {error}")
        return jsonify({"error": "Internal Server Error"}), 500
    
#สำหรับ follow    
@app.route("/follow/<string:username_to_follow>", methods=["PUT"])
@jwt_required()
def follow_user(username_to_follow):
    current_user = get_jwt_identity()

    # ค้นหาผู้ใช้ที่ต้องการติดตาม
    user_to_follow = users_collection.find_one({"username": username_to_follow})
    if not user_to_follow:
        return jsonify({"message": "User to follow not found"}), 404

    # อัปเดตรายการ following ของผู้ใช้ปัจจุบัน
    users_collection.update_one(
        {"username": current_user},
        {"$addToSet": {"following": username_to_follow}}  # เพิ่ม username_to_follow ไปยัง following ของ current_user
    )

    return jsonify({"message": f"Now following {username_to_follow}!"}), 200   

#สำหรับกด unfollow
@app.route("/unfollow/<string:username_to_unfollow>", methods=["DELETE"])
@jwt_required()
def unfollow_user(username_to_unfollow):
    current_user = get_jwt_identity()

    # ค้นหาผู้ใช้ที่ต้องการยกเลิกการติดตาม
    user_to_unfollow = users_collection.find_one({"username": username_to_unfollow})
    if not user_to_unfollow:
        return jsonify({"message": "User to unfollow not found"}), 404

    # อัปเดตรายการ following ของผู้ใช้ปัจจุบัน
    users_collection.update_one(
        {"username": current_user},
        {"$pull": {"following": username_to_unfollow}}  # ลบ username_to_unfollow จาก following ของ current_user
    )

    return jsonify({"message": f"Unfollowed {username_to_unfollow}!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)