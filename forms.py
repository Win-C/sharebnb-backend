from wtforms.validators import DataRequired, Email, Length
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    DecimalField,
    FloatField,
    IntegerField,
    FileField,
)


class UserSignUpForm(FlaskForm):
    """Form for signing up users."""

    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First name', validators=[DataRequired()])
    last_name = StringField('Last name', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')
    location = StringField('Location')


class UserLoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class UserEditForm(FlaskForm):
    """ Edit user form """

    bio = StringField("Bio")
    first_name = StringField('First name')
    last_name = StringField('Last name')
    email = StringField('E-mail', validators=[Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')
    location = StringField('Location')


class MessageForm(FlaskForm):
    """Message form."""

    body = TextAreaField('Body', validators=[DataRequired()])
    to_user = StringField('to_user', validators=[DataRequired()])
    from_user = StringField('from_user', validators=[DataRequired()])


class ListingForm(FlaskForm):
    """Listing form."""

    title = TextAreaField('title', validators=[DataRequired()])
    description = TextAreaField('description')
    photo = FileField('photo')
    price = DecimalField('price', places=2, validators=[DataRequired()])
    longitude = FloatField('longitude', validators=[DataRequired()])
    latitude = FloatField('latitude', validators=[DataRequired()])
    beds = IntegerField('beds', validators=[DataRequired()])
    rooms = IntegerField('rooms', validators=[DataRequired()])
    bathrooms = IntegerField('bathrooms', validators=[DataRequired()])
    created_by = StringField('Created by', validators=[DataRequired()])


class ListingSearchForm(FlaskForm):
    """ Listing query args validator form """

    max_price = IntegerField('max_price')
    longitude = FloatField('longitude')
    latitude = FloatField('latitude')
    beds = IntegerField('beds')
    bathrooms = IntegerField('bathrooms')
