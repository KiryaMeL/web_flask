from flask import Blueprint, request, jsonify
from models import db, Post, Comment, User
from sqlalchemy.exc import IntegrityError
from utils.validators import validate_comment_data
from flask_jwt_extended import jwt_required, get_jwt_identity

comments_bp = Blueprint('comments', __name__)


@comments_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post_comments(post_id):
    """
    Получение всех комментариев для конкретного поста
    """
    # Проверяем существование поста
    Post.query.get_or_404(post_id)

    comments = Comment.query.filter_by(post_id=post_id).all()
    return jsonify([comment.to_dict() for comment in comments])


@comments_bp.route('/comments/posts/<int:post_id>', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    """
    Создание нового комментария для поста
    Требуемые поля в теле запроса (JSON):
    - text: текст комментария
    """

    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if not user.can_comment():
        return jsonify({"error": "Access denied"}), 403

    # Проверяем существование поста
    Post.query.get_or_404(post_id)

    data = request.get_json()

    # Валидируем данные
    is_valid, errors = validate_comment_data(data)
    if not is_valid:
        return jsonify({'errors': errors}), 400

    try:
        # Создаем новый комментарий
        data = request.get_json() or {}
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "text is required"}), 400

        new_comment = Comment(text=text, post_id=post_id, author_id=user_id)
        db.session.add(new_comment)
        db.session.commit()

        return jsonify(new_comment.to_dict()), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500


@comments_bp.route('/comments/<int:comment_id>', methods=['GET'])
@jwt_required()
def get_comment(comment_id):
    """
    Получение комментария по ID
    """
    comment = Comment.query.get_or_404(comment_id)
    return jsonify(comment.to_dict())


@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """
    Удаление комментария
    """
    comment = Comment.query.get_or_404(comment_id)

    # Проверка на то что есть права на создание
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.can_():
        return jsonify({"error": "Access denied"}), 403

    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': 'Comment deleted successfully'})

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500
