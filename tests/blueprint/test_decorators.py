import unittest
from unittest import mock

from flask_atomic.blueprint.decorators import default_decorator


class TestDecoratorsModule(unittest.TestCase):

    def test_default_decorator(self):
        # Nothing really to test here. More just to ++ coverage
        # Make sure that the function was actually called and that the
        # decorator is passing the function through as expected.
        decorated_function = mock.MagicMock()
        default_decorator(decorated_function)()
        decorated_function.assert_called_once()
