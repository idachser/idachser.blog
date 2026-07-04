import os
from unittest.mock import patch

from django.test import SimpleTestCase

from website.settings import env_bool


class EnvBoolTests(SimpleTestCase):
    def test_accepts_common_true_values(self):
        for value in ["True", "true", "TRUE", "1", "yes", "on"]:
            with patch.dict(os.environ, {"FLAG": value}):
                self.assertTrue(env_bool("FLAG"), value)

    def test_rejects_false_and_unknown_values(self):
        for value in ["False", "false", "0", "no", "off", "nonsense", ""]:
            with patch.dict(os.environ, {"FLAG": value}):
                self.assertFalse(env_bool("FLAG"), value)

    def test_uses_default_when_unset(self):
        environ = {k: v for k, v in os.environ.items() if k != "FLAG"}
        with patch.dict(os.environ, environ, clear=True):
            self.assertTrue(env_bool("FLAG", default=True))
            self.assertFalse(env_bool("FLAG", default=False))
