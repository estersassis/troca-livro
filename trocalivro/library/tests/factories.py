import factory
from django.contrib.auth import get_user_model
from library.models import Profile, Book, StatusBook

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Faker("sentence", nb_words=3)
    owner = factory.SubFactory(ProfileFactory)
    status = StatusBook.AVAILABLE.value
