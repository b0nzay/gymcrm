from django.db import models
from django.contrib.auth.models import AbstractUser

from .managers import UserManager

from django.core.validators import FileExtensionValidator

import secrets

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

    birth_date = models.DateField(
        null=True,
        blank=True
    )

    photo = models.ImageField(
        upload_to='users/photos/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    medical_notes = models.TextField(
        null=True,
        blank=True
    )

    USERNAME_FIELD = 'phone'

    REQUIRED_FIELDS = []

    def __str__(self):
        return f'phone: {self.phone}, role: {self.role}'

class AccessCode(models.Model):
    code = models.CharField(max_length=8, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} ({'active' if self.is_active else 'inactive'})"

    @classmethod
    def generate(cls, length=8):
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def rotate(cls, new_code=None):
        cls.objects.filter(is_active=True).update(is_active=False)
        return cls.objects.create(code=new_code or cls.generate())

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).order_by('-created_at').first()


class StaffNote(models.Model):
    client = models.ForeignKey(User, related_name='client_notes', limit_choices_to={'role': User.Role.CLIENT}, on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='author_notes', limit_choices_to={'role__in': [User.Role.TRAINER, User.Role.ADMIN]}, on_delete=models.SET_NULL, null=True)
    text = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author}: {self.text}. Создана в {self.created_at}'