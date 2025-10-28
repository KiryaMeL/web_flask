from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

db = SQLAlchemy()

# Роли
ROLE_COMMENTER = "commenter"
ROLE_WRITER = "writer"
ROLE_ADMIN = "admin"

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship("User", backref="role", lazy=True)

    @staticmethod
    def ensure_defaults():
        for r in (ROLE_COMMENTER, ROLE_WRITER, ROLE_ADMIN):
            if not Role.query.filter_by(name=r).first():
                db.session.add(Role(name=r))
        db.session.commit()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))

    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)

    def set_password(self, password):
        """Установка хэшированного пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)

    def generate_tokens(self):
        """Генерация access и refresh токенов"""
        return {
            'access_token': create_access_token(identity=str(self.id)),
            'refresh_token': create_refresh_token(identity=str(self.id))
        }

    def can_comment(self): return self.role and self.role.name in [ROLE_COMMENTER, ROLE_WRITER, ROLE_ADMIN]
    def can_write(self): return self.role and self.role.name in [ROLE_WRITER, ROLE_ADMIN]
    def  is_admin(self): return self.role and self.role.name == ROLE_ADMIN

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            "role": self.role.name if self.role else None,
            "is_active": self.is_active,
        }


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    posts = db.relationship("Post", back_populates="category", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "posts_count": len(self.posts) if self.posts else 0
        }


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Исправленная привязка к категории
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship("Category", back_populates="posts")

    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else self.created_at.isoformat(),
            'comments_count': len(self.comments),
            'author': self.author.username if self.author else None,
            'user_id': self.user_id,
            "author_role": self.author.role.name if self.author and self.author.role else None,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None
        }


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'created_at': self.created_at.isoformat(),
            'post_id': self.post_id
        }

