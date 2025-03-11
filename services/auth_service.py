from models.user_model import users_collection
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

# ✅ Signup: ลงทะเบียน User ใหม่
def signup(data):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "Username and Password are required!"}, 400

    # เช็คว่ามี user นี้อยู่แล้วหรือไม่
    if users_collection.find_one({"username": username}):
        return {"error": "Username already exists!"}, 400

    # เข้ารหัส password และบันทึกลง MongoDB
    hashed_password = generate_password_hash(password)
    users_collection.insert_one({"username": username, "password": hashed_password})

    return {"message": "User registered successfully!"}, 201

# ✅ Login: ตรวจสอบ username + password และสร้าง JWT Token
def login(data):
    username = data.get("username")
    password = data.get("password")

    user = users_collection.find_one({"username": username})

    if not user or not check_password_hash(user["password"], password):
        return {"error": "Invalid username or password!"}, 401

    # สร้าง JWT Token (หมดอายุใน 1 ชั่วโมง)
    access_token = create_access_token(identity=username, expires_delta=timedelta(hours=1))

    return {"message": "Login successful!", "token": access_token}, 200
