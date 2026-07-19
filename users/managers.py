from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(self, phone, password, **extra_fields):

        if not phone:
            raise ValueError("Номер телефона обязателен")

        user = self.model(
            phone=phone,
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, phone, password, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(
            phone=phone,
            password=password,
            **extra_fields
        )

