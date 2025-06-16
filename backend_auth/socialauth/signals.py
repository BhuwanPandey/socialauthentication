from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from .models import Profile
import requests
from django.core.files import File
from django.core.files.base import ContentFile
from django.contrib.auth.models import User


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        try:
            Profile.objects.create(
                user=instance
            )
        except Exception as e:
            print(e)


@receiver(post_save, sender=SocialAccount)
def create_profile_avatar(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        profile, _ = Profile.objects.get_or_create(user=user)
        try:
            image_url = instance.extra_data.get("picture") or instance.extra_data.get("avatar_url")
            if image_url:
                resp = requests.get(image_url, timeout=5)
                resp.raise_for_status()
                file_name = f"{user.username}.png"
                image_file = ContentFile(resp.content)
                profile.avatar.save(file_name, File(image_file), save=True)
        except Exception as e:
            print(e)