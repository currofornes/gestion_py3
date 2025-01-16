# forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Old password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña antigua'})
    )
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nueva contraseña'})
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirma nueva contraseña'})
    )

class QueryForm(forms.Form):
    query = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'cols': 60}),
        label="Consulta SQL",
        help_text="Introduce una consulta SQL válida."
    )

    def __init__(self, *args, **kwargs):
        super(QueryForm, self).__init__(*args, **kwargs)
        self.fields['query'].required = False