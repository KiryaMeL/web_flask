# comments.py
from flask import Blueprint, request, jsonify
from models import db, Post, Comment, User
from sqlalchemy.exc import IntegrityError
from utils.validators import validate_comment_data
from flask_jwt_extended import jwt_required, get_jwt_identity

comments_bp = Blueprint('comments', __name__)

# ✅ Список комментариев к посту (больше не конфликтует с get_post)
@comments_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    return jsonify([c.to_dict() for c in comments])

# ✅ Создание комментария к посту
@comments_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if not user.can_comment():
        return jsonify({"error": "Access denied"}), 403

    Post.query.get_or_404(post_id)
    data = request.get_json() or {}
    is_valid, errors = validate_comment_data(data)
    if not is_valid:
        return jsonify({'errors': errors}), 400

    try:
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text is required"}), 400
        new_comment = Comment(text=text, post_id=post_id, author_id=user_id)
        db.session.add(new_comment)
        db.session.commit()
        return jsonify(new_comment.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500

@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """
    Удаление комментария — доступно автору, admin и writer
    """
    comment = Comment.query.get_or_404(comment_id)
    user = User.query.get_or_404(int(get_jwt_identity()))

    # Проверяем роли
    user_role = getattr(user, 'role', None)
    if not (user.id == comment.author_id or user_role in ('admin', 'writer')):
        return jsonify({"error": "Access denied"}), 403

    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': 'Comment deleted successfully'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500

@comments_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """
    Редактирование комментария — доступно автору, admin и writer fs
    """
    data = request.get_json() or {}
    new_text = (data.get('text') or '').strip()
    if not new_text:
        return jsonify({"error": "Text is required"}), 400

    comment = Comment.query.get_or_404(comment_id)
    user = User.query.get_or_404(int(get_jwt_identity()))

    # Проверка прав
    user_role = getattr(user, 'role', None)
    if not (user.id == comment.author_id or user_role in ('admin', 'writer')):
        return jsonify({"error": "Access denied"}), 403

    comment.text = new_text
    db.session.commit()

    return jsonify({"message": "Comment updated successfully", "comment": comment.to_dict()})
