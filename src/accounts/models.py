from django.db import models


class Account(models.Model):
    BANK = 'bank'
    CARD = 'card'
    TYPE_CHOICES = [(BANK, 'Bank'), (CARD, 'Credit Card')]

    PRIVATE = 'private'
    JOINT = 'joint'
    OWNERSHIP_CHOICES = [(PRIVATE, 'Private'), (JOINT, 'Joint')]

    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    ownership = models.CharField(max_length=10, choices=OWNERSHIP_CHOICES)
    folder_path = models.CharField(max_length=500, blank=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['account_type', 'name']
