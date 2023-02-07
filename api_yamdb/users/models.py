from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

ROLE_CHOICES = (
    ('user', 'user'),
    ('moderator', 'moderator'),
    ('admin', 'admin'),
)


class User(AbstractUser):
    username = models.CharField(
        'Username',
        db_index=True,
        max_length=150,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='Недопустимое имя пользователя'
        )]
    )
    email = models.EmailField(
        'Email',
        db_index=True,
        max_length=254,
        unique=True
    )
    first_name = models.CharField('First name', max_length=150, blank=True)
    last_name = models.CharField('Last name', max_length=150, blank=True)
    bio = models.TextField('Biography', max_length=1000, blank=True)
    role = models.CharField(
        'Role',
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,
        default='user'
    )

    class Meta:
        ordering = ('username',)

    def __str__(self):
        return self.username

    @property
    def is_user(self):
        return self.role == 'user'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_moderator(self):
        return self.role == 'moderator'
