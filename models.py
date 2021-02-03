"""SQLAlchemy models for sharebnb."""

# from datetime import datetime

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
        nullable=False
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

    # messages = db.relationship('Message', order_by='Message.timestamp.desc()')

    created_listings = db.relationship('Listing', foreign_keys='Listing.created_by', backref="creator")
    rented_listings = db.relationship('Listing', foreign_keys='Listing.rented_by', backref="renter")

    # TODO: Add toMessages and fromMessages relationship of User to another username


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
               location=""
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
            location=location
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
    
    def serialize(self):
        """ Serialize User object to dictionary """

        return {
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "image_url": self.image_url,
            "email": self.email,
            "bio": self.bio,
            "location": self.location,
            "is_admin": self.is_admin
        }


# class Message(db.Model):
#     """An individual message."""

#     __tablename__ = 'messages'

#     id = db.Column(
#         db.Integer,
#         primary_key=True,
#     )

#     body = db.Column(
#         db.Text,
#         nullable=False,
#     )

#     sent_at = db.Column(
#         db.DateTime,
#         nullable=False,
#         default=datetime.utcnow(),
#     )

#     read_at = db.Column(
#         db.DateTime,
#     )

#     to_user = db.Column(
#         db.String,
#         db.ForeignKey('users.username', ondelete='CASCADE'),
#         nullable=False,
#     )

#     from_user = db.Column(
#         db.String,
#         db.ForeignKey('users.username', ondelete='CASCADE'),
#         nullable=False,
#     )

#     def __repr__(self):
#         return f"""<Message #{self.id}:
#                     {self.to_user},
#                     {self.from_user},
#                     {self.sent_at}>"""

#     user = db.relationship('User')


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

    latitude = db.Column(
        db.Float,
        nullable=False,
    )

    longitude = db.Column(
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
    def create(cls,
               title,
               created_by,
               price,
               longitude,
               latitude,
               beds,
               rooms,
               bathrooms,
               description=None,
               photo=None
               ):
        """Create listing and adds listing to system."""

        listing = Listing(
            title=title,
            description=description,
            created_by=created_by,
            photo=photo,
            price=price,
            longitude=longitude,
            latitude=latitude,
            beds=beds,
            rooms=rooms,
            bathrooms=bathrooms
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
                "latitude": self.latitude,
                "longitude": self.longitude,
            }

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "photo": self.photo,
            "price": float(self.price),
            "latitude": self.latitude,
            "longitude": self.longitude,
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
