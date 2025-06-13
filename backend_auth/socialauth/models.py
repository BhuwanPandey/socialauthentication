from django.db import models
from django.contrib.auth.models import User


def profile_path(instance, filename): 
    return 'user_{0}/{1}'.format(instance.user.id, filename)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField( 
        default='profile/default.jpg', 
        upload_to = profile_path
    )
    bio = models.TextField()

    def __str__(self):
        return self.user.username
    
