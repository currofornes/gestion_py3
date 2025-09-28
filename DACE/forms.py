from django import forms
from django.forms import Textarea, ModelChoiceField

from centro.models import Profesores
from .models import Actividades, GastosActividad
from convivencia.widgets import DatePickerInput, ClockPickerInput


class ActividadesForm(forms.ModelForm):
    HoraSalida = forms.TimeField(
        required=False,
        input_formats=['%H:%M'],
        widget=ClockPickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )
    HoraLlegada = forms.TimeField(
        required=False,
        input_formats=['%H:%M'],
        widget=ClockPickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )

    class Meta:
        model = Actividades
        fields = [
            'Titulo',
            'Descripcion',
            'Responsable',
            'FechaInicio',
            'FechaFin',
            'HoraSalida',
            'HoraLlegada',
            'EnProgramacion'
        ]

        widgets = {
            'Titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'Descripcion': Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'Responsable': forms.Select(attrs={'class': 'form-control select2_Responsable'}),
            'FechaInicio': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'FechaFin': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'EnProgramacion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

        }

        labels = {
            'Titulo': 'Título de la actividad',
            'Responsable': 'Profesor/a responsable',
            'FechaInicio': 'Fecha de inicio',
            'FechaFin': 'Fecha de fin',
            'HoraSalida': 'Hora de salida',
            'HoraLlegada': 'Hora de llegada',
            'Descripcion': 'Descripción',
            'EnProgramacion': 'Incluido en PD',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar el queryset del campo 'Responsable' para que solo muestre profesores que no están dados de baja
        self.fields['Responsable'].queryset = Profesores.objects.filter(Baja=False)



class ActividadesCompletoForm(forms.ModelForm):
    HoraSalida = forms.TimeField(
        required=False,
        input_formats=['%H:%M'],
        widget=ClockPickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )
    HoraLlegada = forms.TimeField(
        required=False,
        input_formats=['%H:%M'],
        widget=ClockPickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )

    class Meta:
        model = Actividades
        fields = '__all__'
        exclude = ['UnidadesAfectadas']

        widgets = {
            'Titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'Descripcion': Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'Responsable': forms.Select(attrs={'class': 'form-control select2_Responsable'}),
            'FechaInicio': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'FechaFin': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'EnProgramacion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # 'Duracion': forms.TextInput(attrs={'class': 'form-control'}),
            # 'MedidaDuracion': forms.Select(attrs={'class': 'form-control select2_MedidaDuracion'}),
        #     Qué widget uso para un select mútiple.
        }

        labels = {
            'Titulo': 'Título de la actividad',
            'Responsable': 'Profesor/a responsable',
            'FechaInicio': 'Fecha de inicio',
            'FechaFin': 'Fecha de fin',
            'HoraSalida': 'Hora de salida',
            'HoraLlegada': 'Hora de llegada',
            'Descripcion': 'Descripción',
            'EnProgramacion': 'Incluido en PD',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar el queryset del campo 'Responsable' para que solo muestre profesores que no están dados de baja
        self.fields['Responsable'].queryset = Profesores.objects.filter(Baja=False)
        self.fields['Profesorado'].queryset = Profesores.objects.filter(Baja=False)

class GestionEconomicaActividadForm(forms.ModelForm):
    class Meta:
        model = Actividades
        fields = ['CosteAlumnado', 'AportacionCentro']

        labels = {
            'CosteAlumnado': 'Coste por alumno/a (€)',
            'AportacionCentro': 'Aportación Externa (€)',
        }

        widgets = {
            'CosteAlumnado': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 10.50'
            }),
            'AportacionCentro': forms.NumberInput(attrs={
                'class': 'form-control aportes_centro',
                'placeholder': 'Ej. 0.00'
            }),
        }

class GastosActividadForm(forms.ModelForm):
    class Meta:
        model = GastosActividad
        fields = ['concepto', 'importe', 'tipo']
        exclude = ['id']

        widgets = {
            'concepto': forms.TextInput(attrs={'class': 'form-control'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control importe'}),
            'tipo': forms.Select(attrs={'class': 'form-control tipo'}),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance and not self.instance.pk:
                self.fields['id'].required = False