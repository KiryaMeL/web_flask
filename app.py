from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config
from models import db
from routes.posts import posts_bp
from routes.comments import comments_bp
from routes.auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация JWT
    jwt = JWTManager(app)

    # Инициализация базы данных
    db.init_app(app)

    # Инициализация миграций
    migrate = Migrate(app, db)

    # Регистрация blueprintов
    app.register_blueprint(posts_bp, url_prefix='/api')
    app.register_blueprint(comments_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # CLI команды для миграций
    @app.cli.command('db-init')
    def db_init():
        """Инициализация миграций"""
        import os
        if not os.path.exists('migrations'):
            os.system('flask db init')
            print("Миграции инициализированы")

    # JWT колбэки
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Missing authorization token'}), 401

    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    # Создание таблиц при первом запуске
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8088)
