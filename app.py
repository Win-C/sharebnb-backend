import os

from flask import Flask, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt_claims
)
from werkzeug.utils import secure_filename
from flask_cors import CORS

from upload_functions import (
    allowed_file, upload_file_obj, create_presigned_url
)

from forms import (
    UserSignUpForm,
    UserLoginForm,
    UserEditForm,
    ListingSearchForm,
    ListingCreateForm,
    ListingEditForm,
    MessageCreateForm,
)
from models import db, connect_db, User, Listing, Message
from botocore.exceptions import ClientError

# CURR_USER_KEY = "curr_user"
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(app.root_path, "upload")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///sharebnb')
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', "shhhhh!")
jwt = JWTManager(app)

app.config['WTF_CSRF_ENABLED'] = False

BUCKET = "sharebnb-aw-dev"
# BUCKET = "sharebnb-wchou"

toolbar = DebugToolbarExtension(app)

connect_db(app)


#########################################
# Testing uploads
# @app.route("/uploaded", methods=['POST'])
# def uploaded():
#     """ Testing upload files to S3 """

#     # upload object, don't need to save to disk
#     file = request.files['image_url']
#     try:
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             upload_file_obj(file, BUCKET, filename)

#             url = create_presigned_url(BUCKET, filename)
#             return(jsonify(message="File uploaded", url=url), 201)
#     except IntegrityError as e:
#         print(e)
#         errors = ["Username already taken"]
#         return (jsonify(errors=errors), 400)

##############################################################################
# JWT

# Called whenever create_access_token is used. Takes in object passed into
# create_access_token method. Defines what custom claims should be added to
# access token.
@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return {
        'username': user.username,
        'is_admin': user.is_admin,
        }

# Called whenever create_access_token is used. Takes in object passed into
# create_access_token method. Defines what identity of access token should be.
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.username

# test of JWT for protected routes
@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    payload = {
        'username': get_jwt_identity(),
        'is_admin': get_jwt_claims()['is_admin']
    }
    return jsonify(payload), 200

##############################################################################
# User signup/login/logout

# @app.before_request
# def add_user_to_g():
#     """If we're logged in, add curr user to Flask global."""

    # if CURR_USER_KEY in session:
    #     g.user = User.query.get(session[CURR_USER_KEY])
    # if request.header.get("authorization", None):
    # JWT verify the Bearer token
    #     print("set g.user")
    # else:
    #     g.user = None


def do_login(user):
    """Log in user by returning token for future auth checking.
    """

    access_token = create_access_token(identity=user)
    return (jsonify(token=access_token), 200)


@app.route('/signup', methods=["POST"])
def signup():
    """ Handle user signup. Create new user and add to DB.
        Takes in { user: {
                        username,
                        first_name,
                        last_name,
                        email,
                        password,
                        image_url (not required),
                        location (not required),
                        }}
        Returns a JWT token; otherwise, returns error messages
                { token } NOTE: change status code to 201?
    """

    user_data = request.form
    file = request.files.get('image_url')
    form = UserSignUpForm(formdata=user_data)

    if form.validate():
        try:
            user = User.signup(form)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_file_obj(file, BUCKET, filename)

                url = create_presigned_url(BUCKET, filename)
                user.image_url = url

            db.session.commit()

            return do_login(user)

        except IntegrityError:
            errors = ["Username already taken"]
            return (jsonify(errors=errors), 400)
        except ClientError:
            errors = ["Failure to upload image"]
            return (jsonify(errors=errors), 400)
    else:
        errors = []
        for field in form:
            for error in field.errors:
                errors.append(error)
        return (jsonify(errors=errors), 400)


@app.route('/login', methods=["POST"])
def login():
    """ Handle user login.
        Takes in { user: { username, password }}
        Returns JWT token if authenticated; otherwise, returns error messages
                 { token }
    """

    user_data = request.json.get("user")
    form = UserLoginForm(data=user_data)

    if form.validate():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            return do_login(user)

        return (jsonify(errors=["Invalid credentials."]), 401)
    else:
        errors = []
        for field in form:
            for error in field.errors:
                errors.append(error)
        return (jsonify(errors=errors), 400)


##############################################################################
# General user routes:

@app.route('/users/<username>')
@jwt_required
def user_show(username):
    """ Show user details.
        Returns => {
                    user: {
                            username,
                            bio,
                            first_name,
                            last_name,
                            email,
                            image_url,
                            location,
                            is_admin
                        }
                    }
        TODO: Auth required: admin or username equals logged in user
    """

    user = User.query.get_or_404(username)
    # TODO: grab messages for user inbox (to_user = user) and
    #       user outbox (from_user = user)
    # order messages by most recent from the database

    return (jsonify(user=user.serialize()), 200)

@app.route('/users/<username>/listings')
@jwt_required
def user_listings(username):
    """ Show user's created listings """

    user = User.query.get_or_404(username)
    created_listings = user.created_listings
    serialized = [
        listing.serialize(isDetailed=False)
        for listing in created_listings
    ]
    return (jsonify(listings=serialized), 200)

@app.route('/users/<username>/edit', methods=["PATCH"])
@jwt_required
def user_edit(username):
    """ Edit user profile.
        Takes in { user: {
                        bio,
                        first_name,
                        last_name,
                        email,
                        password,
                        image_url,
                        location
                        }}
        Returns => {
                user: {
                        username,
                        bio,
                        first_name,
                        last_name,
                        email,
                        image_url,
                        location,
                        is_admin
                    }
                }
        TODO: Auth required: admin or username equals logged in user
    """

    user = User.query.get_or_404(username)
    user_data = request.json.get("user")
    form = UserEditForm(data=user_data)

    if form.validate():
        if User.authenticate(username, form.password.data):
            user.update(form)
            db.session.commit()
            return (jsonify(user=user.serialize()), 200)
        else:
            return (jsonify(errors=["Invalid credentials"]), 401)
    else:
        errors = []
        for field in form:
            for error in field.errors:
                errors.append(error)
        return (jsonify(errors=errors), 400)


@app.route('/users/<username>/delete', methods=["DELETE"])
@jwt_required
def user_delete(username):
    """ Delete user.
        Returns { deleted: success }
        TODO: Auth required: admin or username equals logged in user
    """
    user = User.query.get_or_404(username)
    db.session.delete(user)
    db.session.commit()
    return (jsonify(delete="success"), 201)


##############################################################################
# Messages routes:

@app.route('/messages/<from_username>/<to_username>', methods=["GET"])
@jwt_required
def messages_list(from_username, to_username):
    """ Show messages between two users.
        Returns => {
                    messages: [{
                            body,
                            from_user,
                            to_user,
                            sent_at,
                            read_at,
                        },
                        ...]
                    }
        TODO: Auth required: to_user or from_user equals logged in user
    """
    User.query.get_or_404(from_username)
    User.query.get_or_404(to_username)

    messages = Message.find_all(from_username, to_username)
    serialized = [message.serialize() for message in messages]
    return (jsonify(messages=serialized), 200)

@app.route('/messages/<from_username>/<to_username>/add', methods=["POST"])
@jwt_required
def message_add(from_username, to_username):
    """ Create a message.
        Takes in { message: { body, from_user, to_user }}
        Returns => {
                    message: {
                            body,
                            from_user,
                            to_user,
                            sent_at,
                            read_at,
                        }
                    }
        TODO: Auth required: to_user or from_user equals logged in user
    """
    # from_username = User.query.get_or_404(from_username)
    # to_username = User.query.get_or_404(to_username)
    message_data = request.json.get("message")
    form = MessageCreateForm(data=message_data)

    if form.validate():
        message = Message.create(form)
        db.session.commit()
        return (jsonify(message=message.serialize()), 200)
    else:
        errors = []
        for field in form:
            for error in field.errors:
                errors.append(error)
        return (jsonify(errors=errors), 400)


##############################################################################
# General listing routes:

@app.route('/listings')
@jwt_required
def listings_list():
    """ Show listings based on query parameters of
        max price, longitude, latitude, number of beds, or number of bathrooms
        Returns => {
                listings: [
                    {
                        id,
                        title,
                        description,
                        photo,
                        price,
                        longitude,
                        latitude,
                    },
                    ...]
                }
        Auth required: user logged in
    """

    inputs = Listing.convert_inputs(request.args)
    form = ListingSearchForm(data=inputs)
    if form.validate():
        listings = Listing.find_all(inputs)
        serialized = [listing.serialize(
                        isDetailed=False
                        ) for listing in listings]
        return (jsonify(listings=serialized), 200)
    else:
        return (jsonify(errors=["Bad request"]), 400)


@app.route('/listings/<int:listing_id>')
@jwt_required
def listing_show(listing_id):
    """ Show a listing.
        Returns => {
                    listing: {
                                id,
                                title,
                                description,
                                photo,
                                price,
                                longitude,
                                latitude,
                                beds,
                                rooms,
                                bathrooms,
                                created_by,
                                rented_by,
                            }
                    }
        Auth required: user logged in
    """

    listing = Listing.query.get_or_404(listing_id)
    return (jsonify(listing=listing.serialize(isDetailed=True)), 200)


@app.route('/listings/<int:listing_id>/messages', methods=["GET"])
@jwt_required
def listing_messages(listing_id):
    """ Show messages belonging to a listing thread
        Returns => {
                    messages: [{
                            body,
                            from_user,
                            to_user,
                            listing_id
                            sent_at,
                            read_at,
                        },
                        ...]
                    }
        TODO: Auth required: to_user or from_user equals logged in user
    """
    Listing.query.get_or_404(listing_id)

    auth_username = get_jwt_identity()
    all_messages = Message.find_by_listing(listing_id, auth_username)
    print("ALL MESSAGES: ", all_messages)
    serialized = [message.serialize() for message in all_messages]
    return (jsonify(messages=serialized), 200)


@app.route('/listings', methods=["POST"])
@jwt_required
def listing_create():
    """ Create a new listing.
        Takes in { listing: {
                            title,
                            description,
                            photo,
                            price,
                            longitude,
                            latitude,
                            beds,
                            rooms,
                            bathrooms,
                            created_by,
                            }}
        Returns => {
                    listing: {
                                id,
                                title,
                                description,
                                photo,
                                price,
                                longitude,
                                latitude,
                                beds,
                                rooms,
                                bathrooms,
                                created_by,
                                rented_by,
                            }
                    }
    TODO: Auth required: admin or logged in user
    """
    listing_data = request.json.get("listing")
    form = ListingCreateForm(data=listing_data)

    if form.validate():
        listing = Listing.create(form)
        db.session.commit()
        # TODO: reevaluate error with a try and except later
        return (jsonify(listing=listing.serialize(isDetailed=True)), 201)
    else:
        errors = []
        for field in form:
            for error in field.errors:
                errors.append(error)
        return (jsonify(errors=errors), 400)


@app.route('/listings/<int:listing_id>/edit', methods=["PATCH"])
@jwt_required
def listing_edit(listing_id):
    """ Edit listing.
        Takes in { listing: {
                            title,
                            description,
                            photo,
                            price,
                            longitude,
                            latitude,
                            beds,
                            rooms,
                            bathrooms,
                            created_by,
                            rented_by,
                            }}
        Returns => {
                    listing: {
                                id,
                                title,
                                description,
                                photo,
                                price,
                                longitude,
                                latitude,
                                beds,
                                rooms,
                                bathrooms,
                                created_by,
                                rented_by,
                            }
                    }
        TODO: Auth required: admin or created_by equals logged in user
    """

    listing = Listing.query.get_or_404(listing_id)
    listing_data = request.json.get("listing")
    form = ListingEditForm(data=listing_data)

    if form.validate():
        listing.update(form)
        db.session.commit()
        return (jsonify(listing=listing.serialize(isDetailed=True)), 200)

    else:
        errors = []
        for field in form:
            for error in field.errors:
                errors.append(error)
        return (jsonify(errors=errors), 400)


@app.route('/listings/<int:listing_id>/delete', methods=["DELETE"])
@jwt_required
def listing_delete(listing_id):
    """ Delete listing.
        Returns { deleted: success }
        TODO: Auth required: admin or created_by equals logged in user
    """
    listing = Listing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    return (jsonify(delete="success"), 201)


##############################################################################
# after each request

@app.after_request
def add_header(response):
    """ Add non-caching headers on every request. """

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
