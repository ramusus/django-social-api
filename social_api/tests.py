# -*- coding: utf-8 -*-
import mock
from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from social.apps.django_app.default.models import UserSocialAuth
from oauth_tokens.factories import AccessTokenFactory, UserCredentialsFactory
from oauth_tokens.models import AccessTokenGettingError
from vkontakte_api.api import VkontakteApi

from .api import override_api_context
from .exceptions import CallsLimitError


TOKEN = 'b492c0a63455412b67c579422119da1bf73ce07e3bf28f18fa8446c2441844eee57232ca15b7229122dd2'


def raise_error(*args, **kwargs):
    raise AccessTokenGettingError


class SocialApiUnitTest(TestCase):

    def test_override_api_context(self):
        with self.settings(SOCIAL_API_CALL_CONTEXT={}):
            self.assertEqual(settings.SOCIAL_API_CALL_CONTEXT, {})
            with override_api_context('vkontakte', user=1):
                self.assertEqual(settings.SOCIAL_API_CALL_CONTEXT, {'vkontakte': {'user': 1}})
                with override_api_context('vkontakte', token='abc'):
                    self.assertEqual(settings.SOCIAL_API_CALL_CONTEXT, {'vkontakte': {'user': 1, 'token': 'abc'}})

    def test_social_auth_user_argument(self):
        user = get_user_model().objects.create(username='user')
        for i in range(0, 10):
            AccessTokenFactory(provider='vkontakte')
        UserSocialAuth.objects.create(user=get_user_model().objects.create(), uid=2, provider='vk-oauth2',
                                      extra_data='{"access_token": "qwewekrjhshe", "expires": null, "id": null}')
        UserSocialAuth.objects.create(user=user, uid=1, provider='vk-oauth2',
                                      extra_data='{"access_token": "%s", "expires": null, "id": null}' % TOKEN)

        with override_api_context('vkontakte', social_auth_user=user):
            api = VkontakteApi()
            (self.assertEqual(api.get_token(), TOKEN) for i in range(0, 10))

    def test_oauth_tokens_tag_argument(self):
        user_cr = UserCredentialsFactory()
        user_cr.tags.add('tag')
        AccessTokenFactory(provider='vkontakte', access_token=TOKEN, user_credentials=user_cr)
        for i in range(0, 10):
            AccessTokenFactory(provider='vkontakte')
        UserSocialAuth.objects.create(user=get_user_model().objects.create(), uid=1, provider='vk-oauth2',
                                      extra_data='{"access_token": "qwewekrjhshe", "expires": null, "id": null}')

        with override_api_context('vkontakte', oauth_tokens_tag='tag'):
            api = VkontakteApi()
            (self.assertEqual(api.get_token(), TOKEN) for i in range(0, 10))

    def test_get_tokens(self):
        for i in range(0, 5):
            token = AccessTokenFactory(provider='vkontakte')
        api = VkontakteApi()
        self.assertEqual(len(api.get_tokens()), 5)

        api.used_access_tokens = [token.access_token]
        for i in range(0, 100):
            self.assertNotEqual(api.get_token(), token.access_token)

        for i in range(0, 5):
            UserSocialAuth.objects.create(user=get_user_model().objects.create(username=i), uid=i,
                                          provider='vk-oauth2', extra_data='{"access_token": "qwewekrjhshe"}')
        self.assertEqual(len(api.get_tokens()), 10)

    @mock.patch('oauth_tokens.models.AccessToken.objects.fetch', side_effect=raise_error)
    def test_oauth_tokens_update_tokens(self, fetch):

        api = VkontakteApi()
        with self.assertRaises(CallsLimitError):
            api.update_tokens()

        self.assertTrue(fetch.called)
        self.assertEqual(fetch.call_count, 5)

        # TODO: when we update_tokens of new instance, counter is still max, that's wrong
        api = VkontakteApi()
        with self.assertRaises(CallsLimitError):
            api.update_tokens()
        # self.assertEqual(fetch.call_count, 10)
