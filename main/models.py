import logging
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

logger = logging.getLogger(__name__)


class AppUser(AbstractUser):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )

    def __str__(self):
        return f"{self.__class__.__name__}({self.id},'{self.username}')"
