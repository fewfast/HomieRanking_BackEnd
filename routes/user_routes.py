from flask import Blueprint, jsonify, request
from services.user_service import get_all_users, create_user

user_blueprint = Blueprint("users", __name__)

@user_blueprint.route("/", methods=["GET"])
def get_users():
    users = get_all_users()
    return jsonify(users), 200

@user_blueprint.route("/", methods=["POST"])
def add_user():
    data = request.json
    response = create_user(data)
    return jsonify(response), 201
