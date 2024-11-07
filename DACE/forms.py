from django import forms
from .models import Actividades
from convivencia.widgets import DatePickerInput

class ActividadesForm(forms.ModelForm):
    class Meta:
        model = Actividades
        fields = [
            'Titulo',
            'Responsable',
            'FechaInicio',
            'Duracion',
            'MedidaDuracion',
            'UnidadesAfectadas',
            'Alumnado',
            'Profesorado',
            'CosteAlumnado',
            'DietasProfesorado'
        ]

        widgets = {
            'Titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'Responsable': forms.Select(attrs={'class': 'form-control select2_Responsable'}),
            'FechaInicio': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Duracion': forms.TextInput(attrs={'class': 'form-control'}),
            'MedidaDuracion': forms.Select(attrs={'class': 'form-control select2_MedidaDuracion'}),
        #     Qué widget uso para un select mútiple.
        }

        labels = {
            'Titulo': 'Título de la actividad',
            'Responsable': 'Profesorado responsable',
            'FechaInicio': 'Fecha de inicio',
            'Duracion': 'Duración',
        }


