from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
from database import create_user, get_user, get_products, user_exists

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = 'ebe21d2e9aff749e653adc71537186a6ded909c43c72948cfaf2f6c6ccdadfa5'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 1800
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 86400 

jwt = JWTManager(app)

UPLOAD_FOLDER = './products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/products/<path:filename>')
def get_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename), 200

# Хешування пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Реєстрація
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = hash_password(data.get('password'))
    image = data.get('image')
    status = "0"

    if user_exists(email):
        return jsonify(message='User with this email already exists'), 400

    try:
        create_user(email, password, name, image, status)
        return jsonify(message='User created successfully'), 201
    except Exception as e:
        return jsonify(message='User creation failed', error=str(e)), 400

# Логін
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = hash_password(data.get('password'))

    user = get_user(email, password)

    if user[2] == password:
        access_token = create_access_token(identity=user[3])
        refresh_token  = create_access_token(identity=user[3])
        return jsonify(access_token=access_token, refresh_token=refresh_token, name=user[3], image=user[4], status=user[5]), 200
    else:
        return jsonify(message='Invalid email or password'), 401

@app.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token), 200

# Захищений роут
@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(message=f"Welcome {current_user}"), 200

@app.route('/api/products', methods=['POST'])
def products():
    products = get_products()
    if products:
        product_list = []
        for product in products:
            product_data = {
                'id_products': product[0],
                'name': product[1],
                'image': product[2],
                'price': product[3],
                'short_description': product[4],
                'description': product[5] 
            }
            product_list.append(product_data)
        return jsonify(product_list), 200
    else:
        return jsonify(error="No products found"), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
