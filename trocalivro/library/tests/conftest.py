from pytest_factoryboy import register
from .factories import UserFactory, ProfileFactory, BookFactory

register(UserFactory)
register(ProfileFactory)
register(BookFactory)
