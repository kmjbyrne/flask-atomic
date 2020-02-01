from flask import jsonify
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from flask_electron.common.exceptions import MissingConfigurationValue
from flask_electron.dao.base import BaseDAO
from flask_electron.sqlalchemy.models.user.user import BaseUser

PASSWORD_MIN = 8


class UserDAO(BaseDAO):
    json = False

    def __init__(self, model=BaseUser):
        super().__init__(model)
        self.user = None
        self.model = model

    def save(self, instance):
        self.model = instance
        instance.password = self.encrypt_user_password(instance.password)
        super().save(instance)

    def validate(self, username, password):
        if len(username) < 3:
            return 'Username must be at least 3 characters in length', 406

        if self.get_one_by(self.model.username.name, username):
            return 'Username already exists in database.', 409

        if len(password) < PASSWORD_MIN:
            return 'Password must contain at least {} characters'.format(PASSWORD_MIN), 406

        return True

    def create(self, payload):
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

        self.user = self.user.create(payload)
        self.user.save()
        return self.user

    def encrypt_user_password(self, password, config):
        """
        Take the existing user password and generate a sha hash of the password. Encrypt before storing in DB
        :return: None
        """

        if config.get('SECRET_KEY') is None:
            raise MissingConfigurationValue('SECRET_KEY')

        self.model.password = generate_password_hash(password)
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
