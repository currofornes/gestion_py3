from django import forms
from django.forms import ModelForm, ModelChoiceField
from centro.models import Profesores
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput, DateInput, Textarea, TextInput, Select, \
    SelectDateWidget, CheckboxInput

from datetime import date
import datetime

from convivencia.widgets import DatePickerInput
from tde.models import IncidenciasTic


class IncidenciaTicProfeForm(forms.ModelForm):
    profesor = forms.ModelChoiceField(
        queryset=Profesores.objects.all().order_by("Apellidos"),
        widget=forms.HiddenInput()
    )

    class Meta:
        model = IncidenciasTic
        fields = "__all__"
        exclude = ('curso_academico',)
        widgets = {
            'fecha': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'aula': forms.Select(attrs={'class': 'form-control select2_Aula'}),
            'prioridad': forms.Select(attrs={'class': 'form-control select2_Prioridad'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'elementos': forms.SelectMultiple(attrs={'class': 'form-control select2_Elementos', 'multiple':'multiple'}),
        }

    def __init__(self, *args, **kwargs):
        super(IncidenciaTicProfeForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['profesor'].initial = self.instance.profesor
        else:
            self.fields['fecha'].initial = datetime.date.today()  # Establecer la fecha de hoy como valor inicial

        self.fields['fecha'].required = True  # Asegura que el campo sea obligatorio
        self.fields['profesor'].required = True
        self.fields['aula'].required = True
        self.fields['prioridad'].required = True
        self.fields['comentario'].required = True
        self.fields['elementos'].required = False


