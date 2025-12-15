import factory
from factory.alchemy import SQLAlchemyModelFactory


class UserFactory(SQLAlchemyModelFactory):
    name = factory.Faker("name")
    username = factory.Faker("username")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if extracted:
            self.password = extracted
