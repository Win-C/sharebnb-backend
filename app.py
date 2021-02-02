import os

from flask import Flask, render_template, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp

# from forms import UserAddForm, UserEditForm, LoginForm, MessageForm
from models import db, connect_db, User, Message, Listing

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///sharebnb-dev'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)

#####################
# Testing JWT
@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    # if CURR_USER_KEY in session:
    #     g.user = User.query.get(session[CURR_USER_KEY])
    if request.header.get("authorization", None):
        # JWT verify the Bearer token 
        print("set g.user")
    else:
        g.user = None


def do_login(user):
    """Log in user by returning token for future auth checking."""

    jwt = JWT(app, User.authenticate, User.identity)
    return (jsonify(token=jwt), 200)


@app.route('/signup', methods=["POST"])
def signup():
    """Handle user signup.
    TODO: Get basic signup/etc done
    Create new user and add to DB. Returns a JWT token which can be used to authenticate 
    further requests,  { status_code: 201, token }

    If form not valid, returns JSON error messages like,  { status_code: 404, errors }
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            errors = ["Username already taken"]
            return (jsonify(errors=errors), 400)

        return do_login(user)


    else:
        errors = []
        for field in form:
            for error in field.errors:
                errors.push(error)
        return(jsonify(errors=errors), 400)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


##############################################################################
# General user routes:

@app.route('/users')
def users_list():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)
    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/edit', methods=["GET", "POST"])
def user_edit():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = g.user
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data or "/static/images/default-pic.png"
            user.header_image_url = form.header_image_url.data or "/static/images/warbler-hero.jpg"
            user.bio = form.bio.data

            db.session.commit()
            return redirect(f"/users/{user.id}")

        flash("Wrong password, please try again.", 'danger')

    return render_template('users/edit.html', form=form, user_id=user.id)


@app.route('/users/delete', methods=["POST"])
def user_delete():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

##############################################################################
# Messages routes:

@app.route('/messages', methods=["GET"])
def messages_list():

@app.route('/messages/<int:message_id>', methods=["GET"])
def message_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)

@app.route('/messages/new', methods=["GET", "POST"])
def message_add():

@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def message_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")

##############################################################################
# General user routes:

@app.route('/listings')
def listings_list():

@app.route('/listings/<int:listing_id>')
def listing_show(listing_id):

@app.route('/listings', methods=["POST"])
def listing_create():

@app.route('/listings/:id', methods=["PATCH"])
def listing_edit():

@app.route('/listings/delete', methods=["POST"])


##############################################################################
# after each request

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response