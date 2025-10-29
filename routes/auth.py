# routes/auth.py
from flask import Blueprint, request, jsonify
from models import db, User, Role
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request
)
from utils.validators import validate_user_data
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import ROLE_COMMENTER, ROLE_WRITER, ROLE_ADMIN

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
        # Создание пользователя
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])

        # Проверяем, есть ли роль "commenter"
        default_role = Role.query.filter_by(name="commenter").first()

        if not default_role:
            # Если нет, создаём все роли
            from models import ROLE_COMMENTER, ROLE_WRITER, ROLE_ADMIN
            for r in (ROLE_COMMENTER, ROLE_WRITER, ROLE_ADMIN):
                if not Role.query.filter_by(name=r).first():
                    db.session.add(Role(name=r))
            db.session.commit()  # сохраняем роли

            # ещё раз получаем роль "commenter", теперь она точно есть
            default_role = Role.query.filter_by(name="commenter").first()

        # Назначаем пользователю роль
        user.role = default_role

        # Сохраняем пользователя
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
        print(e)
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


@auth_bp.route("/set_role", methods=["POST"])
@jwt_required()
def set_role():
    """
    Назначить пользователю роль.
    Доступ: только admin.
    Body: { "user_id": 123, "role": "writer" }
    """
    # кто делает запрос
    current_user = User.query.get_or_404(int(get_jwt_identity()))
    if not current_user.is_admin():
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}
    user_id = data.get("user_id")
    role_name = (data.get("role") or "").strip().lower()

    if not user_id or role_name not in {ROLE_COMMENTER, ROLE_WRITER, ROLE_ADMIN}:
        return jsonify({
            "error": "Bad request",
            "message": f"role must be one of: {ROLE_COMMENTER}, {ROLE_WRITER}, {ROLE_ADMIN}"
        }), 400

    user = User.query.get_or_404(int(user_id))
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        # на случай пустой таблицы – создадим дефолтные роли
        for r in (ROLE_COMMENTER, ROLE_WRITER, ROLE_ADMIN):
            Role.query.filter_by(name=r).first() or db.session.add(Role(name=r))
        db.session.commit()
        role = Role.query.filter_by(name=role_name).first()

    user.role = role
    db.session.commit()

    return jsonify({
        "message": "Role updated",
        "user": user.to_dict()
    }), 200


@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """Список пользователей (только админ), с фильтром и пагинацией"""
    current_user = User.query.get_or_404(int(get_jwt_identity()))
    if not current_user.is_admin():
        return jsonify({"error": "Access denied"}), 403

    q = (request.args.get('q') or '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = User.query
    if q:
        query = query.filter(db.or_(User.username.ilike(f'%{q}%'), User.email.ilike(f'%{q}%')))
    query = query.order_by(db.desc(User.created_at))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = [u.to_dict() for u in pagination.items]
    return jsonify({
        "users": users,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    })
