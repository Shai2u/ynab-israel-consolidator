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


class FileReview(models.Model):
    """Marks one file in an account's folder as manually reviewed.

    Keyed on file_hash (not just filename) so that replacing a file's
    content under the same name invalidates the review automatically.
    """

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='file_reviews')
    filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('account', 'filename')
