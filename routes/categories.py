# routes/categories.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Category, User, Post

categories_bp = Blueprint("categories", __name__)

@categories_bp.route("/", methods=["GET"])
def get_categories():
    q = request.args.get("q")
    query = Category.query
    if q:
        query = query.filter(Category.name.ilike(f"%{q}%"))
    return jsonify([c.to_dict() for c in query.all()])

@categories_bp.route("/", methods=["POST"])
@jwt_required()
def create_category():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.can_write():
        return jsonify({"error": "Access denied"}), 403
    data = request.get_json()
    category = Category(name=data["name"])
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@categories_bp.route("/<int:cat_id>/posts", methods=["GET"])
def get_category_posts(cat_id):
    """
    Получение всех постов определенной категории
    """
    category = Category.query.get_or_404(cat_id)

    # Параметры пагинации
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Запрос постов категории
    posts_query = Post.query.filter_by(category_id=cat_id).order_by(Post.created_at.desc())

    # Пагинация
    pagination = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items

    return jsonify({
        'category': category.to_dict(),
        'posts': [post.to_dict() for post in posts],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@categories_bp.route("/<int:cat_id>", methods=["PUT"])
@jwt_required()
def update_category(cat_id):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.can_write():
        return jsonify({"error": "Access denied"}), 403
    category = Category.query.get_or_404(cat_id)
    data = request.get_json()
    category.name = data.get("name", category.name)
    db.session.commit()
    return jsonify(category.to_dict())

@categories_bp.route("/<int:cat_id>", methods=["DELETE"])
@jwt_required()
def delete_category(cat_id):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.can_write():
        return jsonify({"error": "Access denied"}), 403
    category = Category.query.get_or_404(cat_id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Deleted"})
