import logging
from abc import ABCMeta, abstractmethod, abstractproperty
from django.conf import settings


class TokensStorageAbstractBase(object):

    __metaclass__ = ABCMeta

    only_this = False

    @abstractproperty
    def name(self):
        pass

    @abstractmethod
    def get_tokens(self):
        pass

    @abstractmethod
    def update_tokens(self):
        pass

    @abstractmethod
    def refresh_tokens(self):
        pass

    def __init__(self, provider, *args, **kwargs):
        self.provider = provider
        self.logger = self.get_logger()

    def get_from_context(self, name):
        key = '_'.join([self.name, name])
        context = getattr(settings, 'SOCIAL_API_CALL_CONTEXT', None)
        if context and self.provider in context and key in context[self.provider]:
            return context[self.provider][key]

    def get_logger(self):
        return logging.getLogger('%s_api' % self.provider)

