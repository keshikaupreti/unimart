from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import UUIDModel


class User(AbstractUser, UUIDModel):
    email = models.EmailField(
        unique=True
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.username
