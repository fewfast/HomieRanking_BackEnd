from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import JWT_SECRET
from routes.auth_routes import auth_blueprint

app = Flask(__name__)
CORS(app)  # อนุญาตให้ React frontend ใช้งาน API
app.config["JWT_SECRET_KEY"] = JWT_SECRET
jwt = JWTManager(app)

# Register API Routes
app.register_blueprint(auth_blueprint, url_prefix="/api/auth")

@app.route("/")
def home():
    return jsonify({"message": "Flask Authentication API Running!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)

