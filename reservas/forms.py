from django import forms
from django.forms import ModelChoiceField

from centro.models import Profesores
from convivencia.widgets import DatePickerInput
from .models import Reservas

class ReservaForm(forms.ModelForm):
    periodicidad = forms.ChoiceField(
        choices=[('puntual', 'Puntual'), ('semanal', 'Semanal')],
        widget=forms.RadioSelect(attrs={'class': 'i-checks2'}),
        required=True,
        initial='puntual'
    )
    num_semanas = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'touchspin1', 'value': '1'}),
        label='Número de semanas'
    )

    tipo = forms.ChoiceField(
        choices=[('1', 'Espacio'), ('2', 'Recurso')],
        widget=forms.RadioSelect(attrs={'class': 'i-checks'}),
        required=True,
        initial='2'
    )

    class Meta:
        model = Reservas
        fields = ['Fecha', 'Reservable', 'periodicidad', 'num_semanas', 'tipo']
        widgets = {
            'Fecha': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Reservable': forms.Select(attrs={'class': 'form-control select2_Reservable'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        periodicidad = cleaned_data.get('periodicidad')
        num_semanas = cleaned_data.get('num_semanas')

        if periodicidad == 'semanal' and not num_semanas:
            self.add_error('num_semanas', 'Debe especificar el número de semanas para una reserva semanal.')
        return cleaned_data


class ReservaProfeForm(forms.ModelForm):

    periodicidad = forms.ChoiceField(
        choices=[('puntual', 'Puntual'), ('semanal', 'Semanal')],
        widget=forms.RadioSelect(attrs={'class': 'i-checks2'}),
        required=True,
        initial='puntual'
    )
    num_semanas = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'touchspin1', 'value': '1'}),
        label='Número de semanas'
    )

    tipo = forms.ChoiceField(
        choices=[('1', 'Espacio'), ('2', 'Recurso')],
        widget=forms.RadioSelect(attrs={'class': 'i-checks'}),
        required=True,
        initial='2'
    )

    class Meta:
        model = Reservas
        fields = ['Fecha', 'Profesor', 'Reservable', 'periodicidad', 'num_semanas', 'tipo']
        widgets = {
            'Fecha': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Reservable': forms.Select(attrs={'class': 'form-control select2_Reservable'}),
            'Profesor': forms.Select(attrs={'class': 'form-control select2_Profesor'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar el queryset del campo 'Profesor' para que solo muestre profesores que no están dados de baja
        self.fields['Profesor'].queryset = Profesores.objects.filter(Baja=False)

    def clean(self):
        cleaned_data = super().clean()
        periodicidad = cleaned_data.get('periodicidad')
        num_semanas = cleaned_data.get('num_semanas')

        if periodicidad == 'semanal' and not num_semanas:
            self.add_error('num_semanas', 'Debe especificar el número de semanas para una reserva semanal.')
        return cleaned_data