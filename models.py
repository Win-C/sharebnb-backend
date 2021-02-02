"""SQLAlchemy models for sharebnb."""

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

DEFAULT_USER_IMAGE = "/static/images/default-pic.png"
DEFAULT_LOCATION_IMAGE = "/static/images/default-pic.png"

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    username = db.Column(
        db.String(length=50),
        primary_key=True,
    )

    bio = db.Column(
        db.Text,
        nullable=False,
        default="",
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    first_name = db.Column(
        db.String(length=50),
        nullable=False,
    )

    last_name = db.Column(
        db.String(length=50),
        nullable=False,
    )

    image_url = db.Column(
        db.Text,
        nullable=False,
        default=DEFAULT_USER_IMAGE,
    )

    location = db.Column(
        db.Text,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    is_admin = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    messages = db.relationship('Message', order_by='Message.timestamp.desc()')

    def __repr__(self):
        return f"""<User #{self.username}:
                    {self.first_name},
                    {self.last_name},
                    {self.email}>"""

    @classmethod
    def signup(cls,
               username,
               first_name,
               last_name,
               email,
               password,
               image_url=DEFAULT_USER_IMAGE,
               ):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    @classmethod
    def identity(cls, payload):
        """ Identifies user from JWT payload """

        username = payload['username']
        return cls.query.filter_by(username=username).first()


class Message(db.Model):
    """An individual message."""

    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    body = db.Column(
        db.Text,
        nullable=False,
    )

    sent_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    read_at = db.Column(
        db.DateTime,
    )

    to_user = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete='CASCADE'),
        nullable=False,
    )

    from_user = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete='CASCADE'),
        nullable=False,
    )

    def __repr__(self):
        return f"""<Message #{self.id}:
                    {self.to_user},
                    {self.from_user},
                    {self.sent_at}>"""

    user = db.relationship('User')


class Listing(db.Model):
    """An individual listing."""

    __tablename__ = 'listings'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    photo = db.Column(
        db.Text,
        nullable=False,
        default=DEFAULT_LOCATION_IMAGE,
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
    )

    title = db.Column(
        db.Text,
        nullable=False,
        default=DEFAULT_LOCATION_IMAGE,
    )

    description = db.Column(
        db.Text,
        nullable=False,
        default="",
    )

    beds = db.Column(
        db.Integer,
        nullable=False,
    )

    rooms = db.Column(
        db.Integer,
        nullable=False,
    )

    bathrooms = db.Column(
        db.Integer,
        nullable=False,
    )

    latitude = db.Column(
        db.Float,
        nullable=False,
    )

    longitude = db.Column(
        db.Float,
        nullable=False,
    )

    created_by = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete='CASCADE'),
        nullable=False,
    )

    rented_by = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete='CASCADE'),
    )

    def __repr__(self):
        return f"""<Listing #{self.id}:
                    {self.price},
                    {self.created_by},
                    {self.latitude},
                    {self.longitude}>"""

    user = db.relationship('User')


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
