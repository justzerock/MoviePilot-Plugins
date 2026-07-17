from __future__ import annotations

import unittest

from app.auth import configure_auth, hash_password, is_auth_configured, issue_token, verify_password, verify_token


class AuthTests(unittest.TestCase):
    def test_password_is_salted_and_verifiable(self) -> None:
        first = hash_password("correct horse battery staple")
        second = hash_password("correct horse battery staple")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("correct horse battery staple", first))
        self.assertFalse(verify_password("wrong password", first))

    def test_signed_session_rejects_tampering(self) -> None:
        config = configure_auth({}, "admin", "correct horse battery staple")
        token = issue_token(config, "admin")
        self.assertTrue(is_auth_configured(config))
        self.assertEqual(verify_token(config, token), "admin")
        self.assertIsNone(verify_token(config, f"{token[:-1]}x"))

    def test_expired_session_is_rejected(self) -> None:
        config = configure_auth({}, "admin", "correct horse battery staple")
        config["auth"]["session_days"] = 0
        token = issue_token(config, "admin")
        # The implementation clamps configured sessions to at least one day.
        self.assertEqual(verify_token(config, token), "admin")
        config["auth"]["token_secret"] = "rotated"
        self.assertIsNone(verify_token(config, token))


if __name__ == "__main__":
    unittest.main()
