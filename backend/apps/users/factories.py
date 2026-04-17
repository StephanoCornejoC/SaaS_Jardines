"""Factory Boy factories for the users app."""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    first_name = factory.Faker("first_name", locale="es")
    last_name = factory.Faker("last_name", locale="es")
    role = "ADMIN_JARDIN"
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "TestPass1234")
        user = model_class.objects.create_user(*args, password=password, **kwargs)
        return user


class SuperadminFactory(UserFactory):
    role = "SUPERADMIN"
    is_staff = True
    is_superuser = True


class DirectorFactory(UserFactory):
    role = "DIRECTOR"


class SecretariaFactory(UserFactory):
    role = "SECRETARIA"


class ProfesorFactory(UserFactory):
    role = "PROFESOR"
