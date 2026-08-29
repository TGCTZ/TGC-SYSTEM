"""Factories for accounts."""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Builds a User with a usable password ('password')."""

    class Meta:
        model = User
        django_get_or_create = ("username",)
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Faker("email")
    password = factory.PostGenerationMethodCall("set_password", "password")
