from django import forms
from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'ownership', 'folder_path', 'enabled']
        widgets = {
            'folder_path': forms.TextInput(attrs={
                'placeholder': '/absolute/path/to/private_data/incoming/account_folder',
                'class': 'form-control',
                'size': 60,
            }),
        }
