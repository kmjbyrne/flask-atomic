import unittest

from flask_atomic.builder.cache import link
from flask_atomic.builder.cache import ROUTE_TABLE


class TestCache(unittest.TestCase):
    def setUp(self) -> None:
        # reset()
        pass

    @link(url='/', methods=['GET', 'POST'])
    def endpoint(self):
        return True

    def test_route_link(self):
        self.assertIsNotNone(ROUTE_TABLE.get('endpoint', None))
        self.assertEqual(ROUTE_TABLE.get('endpoint')[0][0], '/')
        self.assertEqual(ROUTE_TABLE.get('endpoint')[0][1], ['GET', 'POST'])
        self.assertTrue(getattr(self, list(ROUTE_TABLE.keys()).pop())())
