Django Social API
====================

[![PyPI version](https://badge.fury.io/py/django-vkontakte-api.png)](http://badge.fury.io/py/django-vkontakte-api) [![Build Status](https://travis-ci.org/ramusus/django-vkontakte-api.png?branch=master)](https://travis-ci.org/ramusus/django-vkontakte-api) [![Coverage Status](https://coveralls.io/repos/ramusus/django-vkontakte-api/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-vkontakte-api)

Django social networks API abstraction layer. Application allows to use family of social network API applications, such as:

* (django-facebook-api)[https://github.com/ramusus/django-facebook-api]
* (django-instagram-api)[https://github.com/ramusus/django-instagram-api]
* (django-twitter-api)[https://github.com/ramusus/django-twitter-api]
* (django-vkontakte-api)[https://github.com/ramusus/django-vkontakte-api]
* (django-odniklassniki-api)[https://github.com/ramusus/django-odniklassniki-api]

This application provides access tokens from different storages.

# Settings

Context of API calls. You can provide static tokens here in format {'facebook': {'token': '...'}}

    SOCIAL_API_CALL_CONTEXT = {}

You can temporary override this settings using context manager `override_api_context`:

    from social_api.api import override_api_context
    with override_api_context('facebook', context_key=context_value):
        api.call(..)

Available storages, you can add your own storages inherited from social_api.storages.base.TokensStorageAbstractBase

    SOCIAL_API_TOKENS_STORAGES = {
        'social_api.storages.oauthtokens.OAuthTokensStorage',
        'social_api.storages.social_auth.SocialAuthTokensStorage',
    }


# Storages

## Python Social Auth

(python-social-auth)[https://github.com/omab/python-social-auth] is an easy-to-setup social authentication/registration
mechanism with support for several frameworks and auth providers. Crafted using base code from django-social-auth,
it implements a common interface to define new authentication providers from third parties, and to bring support for
more frameworks and ORMs.

Mapping settings between provider codes {'social_api': 'social_auth'}

    SOCIAL_API_SOCIAL_AUTH_PROVIDERS_MAP = {
        'vkontakte': 'vk-oauth2',
        'instagram': 'instagram',
        'facebook': 'facebook',
        'odnoklassniki': 'odnoklassniki-oauth2',
        'twitter': 'twitter',
    }

If you want to make a API call by exact user, use `override_api_context` with `social_auth_user` argument:

    from social_api.api import override_api_context
    with override_api_context('facebook', social_auth_user=user):
        api.call(..)


## Django Oauth Tokens

(django-oauth-tokens)[https://github.com/ramusus/django-oauth-tokens] is application to make silent oauth
authentication from bunch of user credentials and collect access tokens. All user credentials could be stored in
settings or database and for each of them application request access token via Oauth mechanism. It's allowed to tag
any of user credentials.

If you want to make a API call with access token of tagged user credentials, use `override_api_context` with
`oauth_tokens_tag` argument:

    from social_api.api import override_api_context
    with override_api_context('facebook', oauth_tokens_tag='tag'):
        api.call(..)
