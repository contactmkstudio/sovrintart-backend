from django.db import models

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class Announcement(models.Model):
    text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]


class BannerImages(models.Model):
    image_1 = models.TextField(blank=True, null=True)
    image_2 = models.TextField(blank=True, null=True)
    image_3 = models.TextField(blank=True, null=True)
    image_4 = models.TextField(blank=True, null=True)
    image_5 = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BannerImages #{self.pk}"


class EmailSubscription(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email