from flask import jsonify
from flask import current_app
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from sqlalchemy_blender.database import db
from flask_atomic.dao import ModelDAO
from flask_atomic.orm.mixins.columns import CreationTimestampMixin
from flask_atomic.orm.mixins.columns import PrimaryKeyMixin

PASSWORD_MIN = 8


class BaseUser(PrimaryKeyMixin, CreationTimestampMixin, db.Model):
    __abstract__ = True
    username = db.Column(db.String(120), nullable=True, unique=True)
    forename = db.Column(db.String(120))
    surname = db.Column(db.String(120))
    password = db.Column(db.Text, nullable=False)
    admin = db.Column(db.String(5))

    def name(self):
        return '{} {}'.format(self.forename, self.surname)

    def check_user_password(self, password):
        """
        Takes a plain text password, then perform a decrypted password check.
        :param password: Plain text password input
        :return: True or False whether password is valid
        :rtype: bool
        """

        if check_password_hash(self.password, password):
            return True
        return False


class UserDAO(ModelDAO):
    json = False

    def __init__(self, model=BaseUser):
        super().__init__(model)
        self.user = None
        self.model = model

    def save(self, instance):
        self.model = instance
        instance.password = self.encrypt_user_password(instance.password)
        super().save(instance)

    def get(self, **kwargs):
        return super().get()

    def validate(self, username, password):
        if len(username) < 3:
            return 'Username must be at least 3 characters in length', 406

        if self.get_one_by(self.model.username.name, username):
            return 'Username already exists in database.', 409

        if len(password) < PASSWORD_MIN:
            return 'Password must contain at least {} characters'.format(PASSWORD_MIN), 406

        return True

    def post(self, payload):
        """
        Handles the main POST logic for new user.
        :param payload: input key/values for API view.
        :return: API dict response
        :rtype: dict
        """

        try:
            self.validate_arguments(payload)
        except ValueError as error:
            return jsonify(
                message=str(error),
                schema=list(self.model.keys())
            ), 400

        username = payload.get('username')
        password = payload.get('password')

        # Run value based validation and catch any failure notes.
        status = self.validate(username, password)
        if status is not True:
            # Unpack validation status tuple and respond with message and code
            message, code = status
            return jsonify(message=message), code

        user = self.create(payload)
        self.encrypt_user_password(user.password)
        self.user.persist()

        user = self.get_one_by(self.model.username.name, username)
        user = user.prepare(rel=False, exc=[self.model.password.name], json=True)
        return user

    def encrypt_user_password(self, password):
        """
        Take the existing user password and generate a sha hash of the password. Encrypt before storing in DB
        :return: None
        """

        if current_app.config.get('SECRET_KEY') is None:
            raise RuntimeError('SECRET_KEY missing')
        return generate_password_hash(password)

    def check_user_password(self, password):
        """
        Takes a plain text password, then perform a decrypted password check.
        :param password: Plain text password input
        :return: True or False whether password is valid
        :rtype: bool
        """

        if check_password_hash(self.model.password, password):
            return True
        return False
