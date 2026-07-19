from django.db import models
from django.contrib.auth.models import AbstractUser

from .managers import UserManager

class User(AbstractUser):

    objects = UserManager()

    class Role(models.TextChoices):
        CLIENT = 'client', 'Client'
        TRAINER = 'trainer', 'Trainer'
        ADMIN = 'admin', 'Admin'

    username = None

    phone = models.CharField(
        max_length=20,
        unique=True
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT
    )

    USERNAME_FIELD = 'phone'

    REQUIRED_FIELDS = []

    def __str__(self):
        return f'phone: {self.phone}, role: {self.role}'