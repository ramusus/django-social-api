# -*- coding: utf-8 -*-
import logging
import socket
import sys
import time
import random
from abc import ABCMeta, abstractmethod, abstractproperty
from httplib import BadStatusLine, ResponseNotReady, IncompleteRead
from ssl import SSLError

from requests.exceptions import ConnectionError
from django.conf import settings

from .exceptions import NoActiveTokens
from .utils import get_storages, override_api_context

__all__ = ['NoActiveTokens', 'ApiAbstractBase', 'Singleton', 'override_api_context']


class ApiAbstractBase(object):
    __metaclass__ = ABCMeta

    consistent_token = None
    error_class_repeat = (SSLError, ConnectionError, socket.error, BadStatusLine, ResponseNotReady, IncompleteRead)
    sleep_repeat_error_messages = []

    recursion_count = 0

    method = None
    used_access_tokens = None

    def __init__(self):
        self.tokens = []
        self.used_access_tokens = []
        self.consistent_token = None
        self.logger = self.get_logger()
        self.api = None

    def set_context(self):
        # define context of call on each calling, becouse instanse is singleton
        self.consistent_token = None

        context = getattr(settings, 'SOCIAL_API_CALL_CONTEXT', None)
        if context and self.provider in context and 'token' in context[self.provider]:
            self.consistent_token = context[self.provider]['token']

    def call(self, method, *args, **kwargs):
        self.method = method
        self.set_context()

        try:
            token = self.get_token()
        except NoActiveTokens as e:
            return self.handle_error_no_active_tokens(e, *args, **kwargs)

        self.api = self.get_api(token)

        try:
            response = self.get_api_response(*args, **kwargs)
        except self.error_class as e:
            response = self.handle_error_message(e, *args, **kwargs)
            if response is not None:
                return response
            response = self.handle_error_code(e, *args, **kwargs)
        except self.error_class_repeat as e:
            response = self.handle_error_repeat(e, *args, **kwargs)
        except Exception as e:
            return self.log_and_raise(e, *args, **kwargs)

        return response

    def handle_error_no_active_tokens(self, e, *args, **kwargs):
        if self.used_access_tokens:
            # wait 1 sec and repeat with empty used_access_tokens
            self.logger.warning("Waiting 1 sec, because all active tokens are used, method: %s, recursion count: %d" %
                                (self.method, self.recursion_count))
            self.used_access_tokens = []
            return self.sleep_repeat_call(*args, **kwargs)
        else:
            self.logger.warning("Suddenly updating tokens, because no active access tokens and used_access_tokens "
                                "empty, method: %s, recursion count: %d" % (self.method, self.recursion_count))
            self.update_tokens()
            return self.repeat_call(*args, **kwargs)

    def handle_error_message(self, e, *args, **kwargs):
        # check if error message contains any of defined messages
        for message in self.sleep_repeat_error_messages:
            if message in str(e):
                return self.sleep_repeat_call(*args, **kwargs)
        return

    def handle_error_code(self, e, *args, **kwargs):
        # try to find method for handling exception by it's code
        try:
            return getattr(self, 'handle_error_code_%s' % self.get_error_code(e))(e, *args, **kwargs)
        except AttributeError:
            return self.log_and_raise(e, *args, **kwargs)

    def log_and_raise(self, e, *args, **kwargs):
        self.logger.error("Error '%s'. Method %s, args: %s, kwargs: %s, recursion count: %d" % (
            e, self.method, args, kwargs, self.recursion_count))
        error_class = type(e)
        raise error_class, e, sys.exc_info()[2]

    def get_error_code(self, e):
        return e.code

    def handle_error_repeat(self, e, *args, **kwargs):
        self.logger.error("Exception: '%s' registered while executing method %s with params %s, recursion count: %d"
                          % (e, self.method, kwargs, self.recursion_count))
        return self.sleep_repeat_call(*args, **kwargs)

    def sleep_repeat_call(self, *args, **kwargs):
        time.sleep(kwargs.pop('seconds', 1))
        return self.repeat_call(*args, **kwargs)

    def repeat_call(self, *args, **kwargs):
        self.recursion_count += 1
        return self.call(self.method, *args, **kwargs)

    def update_tokens(self):
        self.consistent_token = None
        for storage in get_storages(self.provider):
            storage.update_tokens()

    def refresh_tokens(self):
        self.consistent_token = None
        for storage in get_storages(self.provider):
            storage.refresh_tokens()

    def get_tokens(self):
        tokens = []
        for storage in get_storages(self.provider):
            storage_tokens = storage.get_tokens()
            if storage.only_this:
                return storage_tokens
            tokens += storage_tokens
        return tokens

    def get_token(self):
        if self.consistent_token and self.consistent_token not in self.used_access_tokens:
            return self.consistent_token

        self.tokens = self.get_tokens()

        if not self.tokens:
            self.update_tokens()
            self.tokens = self.get_tokens()
            if not self.tokens:
                raise NoActiveTokens("There is no active tokens for provider %s after updating" % self.provider)

        tokens = self.tokens
        if self.used_access_tokens:
            tokens = list(set(tokens).difference(set(self.used_access_tokens)))
            if not tokens:
                raise NoActiveTokens("There is no active tokens for provider %s, used_tokens: %s"
                                     % (self.provider, self.used_access_tokens))

        return random.choice(tokens)

    def get_logger(self):
        return logging.getLogger('%s_api' % self.provider)

    @abstractproperty
    def provider(self):
        pass

    @abstractproperty
    def error_class(self):
        pass

    @abstractmethod
    def get_api(self, token):
        pass

    @abstractmethod
    def get_api_response(self):
        pass


class Singleton(ABCMeta):
    """
    Singleton metaclass for API classes
    from here http://stackoverflow.com/a/33201/87535
    """

    def __init__(cls, name, bases, dictionary):
        super(Singleton, cls).__init__(name, bases, dictionary)
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance
