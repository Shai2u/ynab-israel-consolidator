from django.db import models


class Identity(models.Model):
    owner_name = models.CharField(max_length=100)
    partner_name = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Identity'
