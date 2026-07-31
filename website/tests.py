import os
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from website.settings import env_bool, resolve_admin_url


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


class ResolveAdminUrlTests(SimpleTestCase):
    def test_requires_explicit_value_in_production(self):
        for value in [None, "", "   ", "/"]:
            with self.assertRaises(ImproperlyConfigured):
                resolve_admin_url(value, allow_default=False)

    def test_falls_back_to_default_outside_production(self):
        self.assertEqual(resolve_admin_url(None, True), "admin/")

    def test_normalizes_surrounding_slashes(self):
        for value in ["staffonly", "staffonly/", "/staffonly/"]:
            self.assertEqual(
                resolve_admin_url(value, False), "staffonly/", value
            )
