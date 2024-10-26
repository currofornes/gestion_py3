from django import forms
from .models import ItemHorario
from django.forms.widgets import Select

class ItemHorarioForm(forms.ModelForm):
    class Meta:
        model = ItemHorario
        fields = ['tramo', 'dia', 'materia', 'unidad', 'aula']
        widgets = {
            'tramo': Select(attrs={'class': 'form-control select2_Tramo'}),
            'dia': Select(attrs={'class': 'form-control select2_Dia'}),
            'materia': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad': Select(attrs={'class': 'form-control select2_Unidad'}),
            'aula': Select(attrs={'class': 'form-control select2_Aula'}),
        }

