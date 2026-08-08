from django import forms

class ConsolidationForm(forms.Form):
    start_date = forms.DateField(
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    end_date = forms.DateField(
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    
