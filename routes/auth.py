# routes/auth.py
from flask import Blueprint, request, jsonify
from models import db, User
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request
)
from utils.validators import validate_user_data

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    data = request.get_json()

    # Валидация данных
    is_valid, errors = validate_user_data(data)
    if not is_valid:
        return jsonify({'errors': errors}), 400

    # Проверка уникальности
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    try:
        # Создание пользователя
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        # Генерация токенов
        tokens = user.generate_tokens()

        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(),
            'tokens': tokens
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Аутентификация пользователя"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Поиск пользователя по username или email
    user = User.query.filter(
        (User.username == data.get('login')) |
        (User.email == data.get('login'))
    ).first()

    if not user or not user.check_password(data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403

    # Генерация токенов
    tokens = user.generate_tokens()

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'tokens': tokens
    })


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Обновление access token с помощью refresh token"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if not user or not user.is_active:
        return jsonify({'error': 'Invalid token'}), 401

    new_access_token = create_access_token(identity=current_user_id)

    return jsonify({
        'access_token': new_access_token
    })


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Получение профиля текущего пользователя"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    return jsonify(user.to_dict())
