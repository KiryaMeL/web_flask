# routes/categories.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Category, User

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
