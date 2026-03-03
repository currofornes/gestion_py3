from django import forms
from django.db import transaction, IntegrityError
from django.forms import ModelForm, ModelChoiceField

from absentismo.models import Actuaciones, InformeFM, InformeSSC
from centro.models import Profesores, CursoAcademico, PeriodosLectivos
from centro.utils import get_current_academic_year
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

# class CargaInformeFaltasSeneca(forms.Form):
#     InformePDF = forms.FileField()
#     Protocolo = forms.HiddenInput()
#
#     widgets = {
#         'InformePDF': forms.FileInput(attrs={'class': 'custom-file-input'}),
#         'Protocolo': forms.HiddenInput(),
#     }

class CargaFaltasCSVForm(forms.Form):
    curso_academico = forms.ModelChoiceField(
        queryset=CursoAcademico.selector(),
        label="Curso Académico",
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    archivo_csv = forms.FileField(
        label="Archivo CSV",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )

class ResumenFaltasForm(forms.Form):
    curso_academico = forms.ModelChoiceField(
        queryset=CursoAcademico.selector(),
        label="Curso Académico",
        widget=forms.Select(attrs={'class': 'form-select select2', 'onchange': 'this.form.submit()'})
    )
    periodos = forms.ModelMultipleChoiceField(
        queryset=PeriodosLectivos.objects.none(),
        label="Seleccionar Periodos",
        widget=forms.SelectMultiple(attrs={'class': 'form-select select2-multiple'})
    )

    def __init__(self, *args, **kwargs):
        curso_id = kwargs.pop('curso_id', None)
        super().__init__(*args, **kwargs)
        if curso_id:
            # Filtramos periodos por el calendario asociado al curso
            self.fields['periodos'].queryset = PeriodosLectivos.objects.filter(
                calendario_lectivo__curso_academico_id=curso_id
            ).order_by('inicio')

# Definimos un widget que soporte múltiples archivos
class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

# Definimos el campo que usará ese widget
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

from django import forms
from .models import InformeFM, InformeSSC, ProtocoloAbs


class InformeFMForm(forms.ModelForm):
    class Meta:
        model = InformeFM
        exclude = ['protocolo', 'ultima_modificacion']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'informe_actuaciones': forms.Textarea(attrs={'rows': 5}),
            'valoracion_educativa': forms.Textarea(attrs={'rows': 5}),
            'comparecencia_menor': forms.Textarea(attrs={'rows': 3}),
            'llamadas_citaciones': forms.Textarea(attrs={'rows': 3}),
            'comparecencia_tutores_legales': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'hermanos_centro': '¿Tiene hermanos en el centro?',
            'hermanos_absentistas': '¿Algún hermano es absentista?',
            'finalizado': 'Marcar como finalizado',
        }


class InformeSSCForm(forms.ModelForm):
    class Meta:
        model = InformeSSC
        exclude = ['protocolo', 'ultima_modificacion']
        widgets = {
            'fecha_derivacion': forms.DateInput(attrs={'type': 'date'}),
            'med_observaciones': forms.Textarea(attrs={'rows': 3}),
            'fam_observaciones': forms.Textarea(attrs={'rows': 3}),
            'act_tutor': forms.Textarea(attrs={'rows': 3}),
            'act_eoe': forms.Textarea(attrs={'rows': 3}),
            'act_equipo_dir': forms.Textarea(attrs={'rows': 3}),
            'act_motivos_familia': forms.Textarea(attrs={'rows': 3}),
            'ind_observaciones': forms.Textarea(attrs={'rows': 3}),
            'otra_info': forms.Textarea(attrs={'rows': 3}),
        }