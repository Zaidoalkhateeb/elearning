from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	class Role(models.TextChoices):
		INSTRUCTOR = 'instructor', 'Instructor'
		STUDENT = 'student', 'Student'

	role = models.CharField(max_length=32, choices=Role.choices, default=Role.STUDENT)
	token_version = models.PositiveIntegerField(default=0)
