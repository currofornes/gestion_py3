from django import forms
from django.forms.widgets import Select

from .models import ItemHorario

from centro.models import Profesores


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

class CopiarHorarioForm(forms.Form):
    ProfesorOrigen = forms.ModelChoiceField(
        queryset=Profesores.objects.filter(Baja=False).all(),
        label="Profesor/a de origen",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control select2_ProfesorOrigen'}),
    )
    ProfesorDestino = forms.ModelChoiceField(
        queryset=Profesores.objects.filter(Baja=False).all(),
        label="Profesor/a de destino",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control select2_ProfesorDestino'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        origen = cleaned_data.get("ProfesorOrigen")
        destino = cleaned_data.get("ProfesorDestino")

        if origen == destino:
            raise forms.ValidationError("El profesor de origen y destino no pueden ser el mismo.")

        return cleaned_data