from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.auth_service import signup, login

auth_blueprint = Blueprint("auth", __name__)

@auth_blueprint.route("/signup", methods=["POST"])
def user_signup():
    data = request.json
    return signup(data)

@auth_blueprint.route("/login", methods=["POST"])
def user_login():
    data = request.json
    return login(data)

# ✅ Protected Route: ดึงข้อมูล User (ต้องมี Token)
@auth_blueprint.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify({"message": "This is your profile", "user": current_user}), 200
