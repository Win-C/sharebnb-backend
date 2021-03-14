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

        hashed_pwd = bcrypt.generate_password_hash(
                            form.password.data
                            ).decode('UTF-8')

        user = User(
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=hashed_pwd,
            image_url=DEFAULT_USER_IMAGE,
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

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey('listings.id', ondelete="CASCADE"),
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

    # listing_thread = db.relationship('Listing',
    #                                  foreign_keys="Listing.id",
    #                                  backref="sent_messages")

    def __repr__(self):
        return f"""<Message #{self.id}:
                    {self.to_user},
                    {self.from_user},
                    {self.sent_at}>"""

    @classmethod
    def find_all(cls, from_user, to_user, listing_id):
        """ Given from_user and to_user, query for all messages.
            Order by timestamp descending
            Limit by 100
        """

        messages = cls.query.filter(
                                    Message.from_user == from_user,
                                    Message.to_user == to_user,
                            ).order_by(
                                Message.sent_at.desc()
                            ).limit(
                                100
                            ).all()
        return messages

    @classmethod
    def find_by_listing(cls, listing_id, from_username):
        """ Given listing_id and from_username, query for all messages.
            Order by timestamp descending
            Limit by 100
        """

        messages = cls.query.filter(
                                    Message.listing_id == listing_id,
                                    Message.from_user == from_username,
                            ).order_by(
                                Message.sent_at.desc()
                            ).limit(
                                100
                            ).all()
        return messages

    @classmethod
    def create(cls, form):
        """Create message and add message to database."""

        message = Message(
            body=form.body.data,
            from_user=form.from_user.data,
            to_user=form.to_user.data,
            listing_id=form.listing_id.data,
            sent_at=datetime.now(),
        )

        db.session.add(message)
        return message

    def serialize(self):
        """ Serialize message object to dictionary. """

        return {
            "body": self.body,
            "from_user": self.from_user,
            "to_user": self.to_user,
            "listing_id": self.listing_id,
            "sent_at": self.sent_at,
            "read_at": self.read_at,
        }


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

    sent_messages = db.relationship('Message',
                                    foreign_keys="Message.listing_id",
                                    backref="listing_thread")

    def __repr__(self):
        return f"""<Listing #{self.id}:
                    {self.price},
                    {self.created_by},
                    {self.latitude},
                    {self.longitude}>"""

    @classmethod
    def find_all(cls, search_params):
        """ Given search inputs, query and return all listings.  """

        search_query = cls.query

        for key in search_params:
            if key == 'max_price' and search_params.get(key):
                search_query = search_query.filter(
                    Listing.price < search_params[key]
                    )
            if key == 'longitude' and search_params.get(key):
                search_query = search_query.filter(
                    Listing.longitude == search_params[key]
                    )
            if key == 'latitude' and search_params.get(key):
                search_query = search_query.filter(
                    Listing.latitude == search_params[key]
                    )
            if key == 'beds' and search_params.get(key):
                search_query = search_query.filter(
                    Listing.beds == search_params[key]
                    )
            if key == 'bathrooms' and search_params.get(key):
                search_query = search_query.filter(
                    Listing.bathrooms == search_params[key]
                    )

        listings = search_query.all()
        return listings

    @classmethod
    def create(cls, form):
        """Create listing and adds listing to database."""

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

    @classmethod
    def convert_inputs(self, inputs):
        """ Converts search parameter inputs into correct type. """

        search_params = {}
        max_price = inputs.get("max_price", None)
        longitude = inputs.get("longitude", None)
        latitude = inputs.get("latitude", None)
        beds = inputs.get("beds", None)
        bathrooms = inputs.get("bathrooms", None)

        if max_price:
            search_params["max_price"] = int(max_price)

        if longitude:
            search_params["longitude"] = float(longitude)

        if latitude:
            search_params["latitude"] = float(latitude)

        if beds:
            search_params["beds"] = int(beds.split(".")[0])

        if bathrooms:
            search_params["bathrooms"] = int(bathrooms.split(".")[0])

        return search_params

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

    def update(self, form):
        """ Update fields of self if key in form """

        self.title = form.title.data
        self.description = form.description.data
        self.photo = form.photo.data
        self.price = form.price.data
        self.longitude = form.longitude.data
        self.latitude = form.latitude.data
        self.beds = form.beds.data
        self.rooms = form.rooms.data
        self.bathrooms = form.bathrooms.data
        self.created_by = form.created_by.data
        self.rented_by = form.rented_by.data


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
