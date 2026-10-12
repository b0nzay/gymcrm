from django.db import models
from django.contrib.auth.models import AbstractUser

from .managers import UserManager

import secrets


class User(AbstractUser):

    objects = UserManager()

    class Role(models.TextChoices):
        CLIENT = 'client', 'Client'
        TRAINER = 'trainer', 'Trainer'
        ADMIN = 'admin', 'Admin'

    username = models.CharField(max_length=32, unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f'username: {self.username}, role: {self.role}'

    @property
    def display_name(self):
        name = f'{self.first_name} {self.last_name}'.strip()
        return name or self.username


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


class ActivityLog(models.Model):
    actor = models.ForeignKey(
        User,
        related_name='activity_logs',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} at {self.created_at}'


def log_activity(actor, action, description=''):
    return ActivityLog.objects.create(
        actor=actor if actor and getattr(actor, 'is_authenticated', False) else None,
        action=action,
        description=description or '',
    )
