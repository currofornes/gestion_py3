from django import forms
from .models import ItemGuardia

class ItemGuardiaForm(forms.ModelForm):
    class Meta:
        model = ItemGuardia
        fields = '__all__'  # O bien especificar los campos que quieres incluir
