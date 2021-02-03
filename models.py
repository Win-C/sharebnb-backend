"""SQLAlchemy models for sharebnb."""

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

# TODO: reference to actual S3 bucket
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

    first_name = db.Column(
        db.String(length=50),
        nullable=False,
    )

    last_name = db.Column(
        db.String(length=50),
        nullable=False,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    image_url = db.Column(
        db.Text,
        nullable=False,
        default=DEFAULT_USER_IMAGE,
    )

    location = db.Column(
        db.Text,
        nullable=False
    )

    is_admin = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_listings = db.relationship('Listing',
                                       foreign_keys='Listing.created_by',
                                       backref="creator")
    rented_listings = db.relationship('Listing',
                                      foreign_keys='Listing.rented_by',
                                      backref="renter")

    sent_messages = db.relationship('Message',
                                    foreign_keys='Message.from_user',
                                    backref="sender")
    received_messages = db.relationship('Message',
                                        foreign_keys='Message.to_user',
                                        backref="recipient")

    def __repr__(self):
        return f"""<User #{self.username}:
                    {self.first_name},
                    {self.last_name},
                    {self.email}>"""

    @classmethod
    def signup(cls, form):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('UTF-8')

        user = User(
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=hashed_pwd,
            image_url=form.image_url.data or DEFAULT_USER_IMAGE,
            location=form.location.data or "",
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

    def serialize(self):
        """ Serialize User object to dictionary """

        return {
            "username": self.username,
            "bio": self.bio,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "image_url": self.image_url,
            "location": self.location,
            "is_admin": self.is_admin
        }

    def update(self, form):
        """ Update fields of self if key in form """

        self.bio = form.bio.data
        self.first_name = form.first_name.data
        self.last_name = form.last_name.data
        self.email = form.email.data
        self.image_url = form.image_url.data
        self.location = form.location.data


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


class Listing(db.Model):
    """An individual listing."""

    __tablename__ = 'listings'

    id = db.Column(
        db.Integer,
        primary_key=True,
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

    photo = db.Column(
        db.Text,
        nullable=False,
        default=DEFAULT_LOCATION_IMAGE,
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
    )

    longitude = db.Column(
        db.Float,
        nullable=False,
    )

    latitude = db.Column(
        db.Float,
        nullable=False,
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

    created_by = db.Column(
        db.String,
        db.ForeignKey('users.username', ondelete='CASCADE'),
        nullable=False
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

    @classmethod
    def find_all(cls, inputs):
        """ Given search inputs, query for all listings.  """

        base_query = cls.query

        for key in inputs:
            if key == 'max_price':
                base_query = base_query.filter(Listing.price < inputs[key])
            if key == 'longitude':
                base_query = base_query.filter(Listing.longitude == inputs[key])
            if key == 'latitude':
                base_query = base_query.filter(Listing.latitude == inputs[key])
            if key == 'beds':
                base_query = base_query.filter(Listing.beds == inputs[key])
            if key == 'bathrooms':
                base_query = base_query.filter(Listing.bathrooms == inputs[key])

        return base_query

    @classmethod
    def create(cls, form):
        """Create listing and adds listing to system."""

        listing = Listing(
            title=form.title.data,
            description=form.description.data or None,
            photo=form.photo.data or None,
            price=form.price.data,
            longitude=form.longitude.data,
            latitude=form.latitude.data,
            beds=form.beds.data,
            rooms=form.rooms.data,
            bathrooms=form.bathrooms.data,
            created_by=form.created_by.data,
        )

        db.session.add(listing)
        return listing

    def serialize(self, isDetailed):
        """ Serialize Listing object to dictionary
        price is a Numeric in db, but Decimal is not serializable,
        so converting to a float beforehand
        """

        if not isDetailed:
            return {
                "id": self.id,
                "title": self.title,
                "description": self.description,
                "photo": self.photo,
                "price": float(self.price),
                "longitude": self.longitude,
                "latitude": self.latitude,
            }

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "photo": self.photo,
            "price": float(self.price),
            "longitude": self.longitude,
            "latitude": self.latitude,
            "beds": self.beds,
            "rooms": self.rooms,
            "bathrooms": self.bathrooms,
            "created_by": self.created_by,
            "rented_by": self.rented_by
        }


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
