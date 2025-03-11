from models.user_model import users_collection

# ดึง Users ทั้งหมด
def get_all_users():
    return list(users_collection.find({}, {"_id": 0}))  # เอาเฉพาะ field ที่ต้องการ

# เพิ่ม User ใหม่
def create_user(data):
    users_collection.insert_one(data)
    return {"message": "User created successfully"}
