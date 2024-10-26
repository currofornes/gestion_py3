from django import forms
from django.db import transaction, IntegrityError
from django.forms import ModelForm, ModelChoiceField

from absentismo.models import Actuaciones
from centro.models import Profesores
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput, DateInput, Textarea, TextInput, Select, \
    SelectDateWidget, CheckboxInput

from datetime import date
import datetime

from convivencia.widgets import DatePickerInput
from tde.models import IncidenciasTic

class ActuacionProtocoloForm(forms.ModelForm):

    class Meta:
        model = Actuaciones
        exclude = ['Notificada']
        fields = "__all__"
        widgets = {
            'Protocolo': forms.HiddenInput(),
            'Fecha': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Tipo': forms.Select(attrs={'class': 'form-control select2_Tipo'}),
            'prioridad': forms.Select(attrs={'class': 'form-control select2_Prioridad'}),
            'Comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'Medio': forms.Select(attrs={'class': 'form-control select2_Medio', 'id':'id_Medio'}),
            'Telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'Telefono': 'Teléfono/s',
        }

    def __init__(self, *args, **kwargs):
        super(ActuacionProtocoloForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['Protocolo'].initial = self.instance.protocolo
        else:
            self.fields['Fecha'].initial = datetime.date.today()  # Establecer la fecha de hoy como valor inicial


    def save(self, commit=True):
        instance = super(ActuacionProtocoloForm, self).save(commit=False)

        # Lógica para evitar duplicados
        try:
            with transaction.atomic():
                # Verifica si existe ya una actuación con los mismos campos clave
                existing = Actuaciones.objects.filter(
                    Protocolo=instance.Protocolo,
                    Fecha=instance.Fecha,
                    Tipo=instance.Tipo,
                    Medio=instance.Medio,
                    Comentario=instance.Comentario
                ).exists()

                if not existing:
                    if instance.Medio != '1':  # Si el Medio no es 'Teléfono'
                        instance.Telefono = ''  # Vaciar el campo Teléfono

                    if commit:
                        instance.save()



        except IntegrityError:
            # Manejar el error de duplicado según sea necesario
            print("Ya existe una actuación con estos datos.")

        return instance

