import unittest

from flask_atomic.httputils.exceptions import HTTPException


class TestHttpUtilsExceptionModule(unittest.TestCase):

    def test_exception_constructor(self):
        # Nothing really to test here. More just to ++ coverage
        # Make sure that the function was actually called and that the
        # decorator is passing the function through as expected.
        exception = HTTPException('Failing blablabla', 500)
        self.assertEquals(exception.code, 500)
        self.assertEquals(exception.message, 'Failing blablabla')
