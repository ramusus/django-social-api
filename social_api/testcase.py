# -*- coding: utf-8 -*-
from django.test import TestCase
from django.conf import settings


class SocialApiTestCase(TestCase):
    _settings = None
    token = None
    provider = ''

    def setUp(self):
        context = getattr(settings, 'SOCIAL_API_CALL_CONTEXT', {})
        self._settings = dict(context)
        context.update({self.provider: {'token': self.token}})

    def tearDown(self):
        setattr(settings, 'SOCIAL_API_CALL_CONTEXT', self._settings)
