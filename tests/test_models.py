# coding=utf-8
from unittest import TestCase
from chinaapi.utils import models
import time


class TokenTest(TestCase):
    def test_access_token(self):
        token = models.Token('token_string', time.time() + 60 * 60)
        self.assertFalse(token.is_expires)

    def test_access_token_without_expired_at(self):
        token = models.Token('token_string')
        self.assertFalse(token.is_expires)

    def test_empty_access_token(self):
        token = models.Token('')
        self.assertTrue(token.is_expires)

    def test_expired_access_token(self):
        token = models.Token('token_string', time.time() - 60 * 60)
        self.assertTrue(token.is_expires)

    def test_set_expires_in(self):
        token = models.Token('token_string', time.time() - 60 * 60)
        token.set_expires_in(10000)
        self.assertFalse(token.is_expires)


class UserTest(TestCase):
    def test_user(self):
        user = models.User('username', 'password')
        self.assertEqual('username', user.username)
        self.assertEqual('password', user.password)
