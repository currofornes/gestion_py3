from datetime import datetime

from django import forms
from django.forms import ModelForm, ModelChoiceField
from convivencia.models import Amonestaciones, Sanciones
from centro.models import Profesores, CursoAcademico
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput, DateInput, Textarea, TextInput, Select, \
    SelectDateWidget, CheckboxInput
from django.contrib.admin.widgets import AdminDateWidget


from convivencia.widgets import DatePickerInput, ClockPickerInput


class AmonestacionForm(forms.ModelForm):
    # Profesor = ModelChoiceField(Profesores.objects.all().order_by("Apellidos"), empty_label=None)
    class Meta:
        model = Amonestaciones
        fields = "__all__"
        # exclude = ('Enviado',)
        widgets = {
            'IdAlumno': HiddenInput(),
            'Fecha': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Hora': Select(attrs={'class': 'form-control select2_Hora'}),
            'Tipo': Select(attrs={'class': 'form-control select2_TipoParte'}),
            'Profesor': Select(attrs={'class': 'form-control select2_Profesor'}),
            'Comentario': Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'Enviado': CheckboxInput(attrs={'class': 'form-check-input'}),
            'DerivadoConvivencia': CheckboxInput(attrs={'class': 'i-checks'}),
            'ComunicadoFamilia': HiddenInput(),
            'FamiliarComunicado': forms.TextInput(attrs={'class': 'form-control'}),
            'FechaComunicado': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'HoraComunicado': ClockPickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Medio': forms.Select(attrs={'class': 'form-control select2_Medio', 'id': 'id_Medio'}),
            'TelefonoComunicado': forms.TextInput(attrs={'class': 'form-control'}),
            'ObservacionComunicado': Textarea(attrs={'class': 'form-control', 'rows': 4}),

        }
        labels = {
            'FechaComunicado': 'Fecha comunicación',
            'HoraComunicado': 'Hora comunicación',
            'FamiliarComunicado': 'Familiar',
            'TelefonoComunicado': 'Teléfono',
            'ObservacionComunicado': 'Observaciones',

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar el queryset del campo 'Profesor' para que solo muestre profesores que no están dados de baja
        self.fields['Profesor'].queryset = Profesores.objects.filter(Baja=False)
        self.fields['Tipo'].required = True
        self.fields['Medio'].required = True



class SancionForm(forms.ModelForm):
    class Meta:
        model = Sanciones
        fields = "__all__"
        widgets = {
            'IdAlumno': HiddenInput(),
            'Fecha': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Fecha_fin': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Comentario': Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'Sancion': TextInput(attrs={'class': 'form-control'}),
            'NoExpulsion': CheckboxInput(attrs={'class': 'form-check-input'}),
            # 'Comentario': TinyMCE(),

        }


class FechasForm(forms.Form):
    try:
        initial_fecha1 = Amonestaciones.objects.first().Fecha
    except:
        initial_fecha1 = datetime.today

    Fecha1 = forms.DateField(initial=initial_fecha1,
                             widget=DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))

    Fecha2 = forms.DateField(initial=datetime.today,
                             widget=DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))

    def __init__(self, *args, **kwargs):
        curso_academico = kwargs.pop('curso_academico', None)
        super(FechasForm, self).__init__(*args, **kwargs)

        # Establecer la fecha inicial en función del curso académico
        if curso_academico:
            try:
                initial_fecha1 = Amonestaciones.objects.filter(curso_academico=curso_academico).first().Fecha
            except AttributeError:
                initial_fecha1 = datetime.today()
        else:
            initial_fecha1 = datetime.today()

        self.fields['Fecha1'].initial = initial_fecha1



# Curro Jul 24: Anado formulario para el parte puesto por un profesor
class AmonestacionProfeForm(forms.ModelForm):
    Profesor = ModelChoiceField(Profesores.objects.all().order_by("Apellidos"), empty_label=None,
                                widget=forms.HiddenInput())

    class Meta:
        model = Amonestaciones
        fields = "__all__"
        # exclude = ('Enviado',)
        widgets = {
            'IdAlumno': HiddenInput(),
            'Fecha': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Hora': Select(attrs={'class': 'form-control select2_Hora'}),
            'Tipo': Select(attrs={'class': 'form-control select2_TipoParte'}),
            'Comentario': Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'Enviado': CheckboxInput(attrs={'class': 'form-check-input'}),
            'DerivadoConvivencia': CheckboxInput(attrs={'class': 'i-checks'}),

            'ComunicadoFamilia': HiddenInput(),
            'FamiliarComunicado': forms.TextInput(attrs={'class': 'form-control'}),
            'FechaComunicado': DatePickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'HoraComunicado': ClockPickerInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'Medio': forms.Select(attrs={'class': 'form-control select2_Medio', 'id': 'id_Medio'}),
            'TelefonoComunicado': forms.TextInput(attrs={'class': 'form-control'}),
            'ObservacionComunicado': Textarea(attrs={'class': 'form-control', 'rows': 4}),

        }
        labels = {
            'FechaComunicado': 'Fecha comunicación',
            'HoraComunicado': 'Hora comunicación',
            'FamiliarComunicado': 'Familiar',
            'TelefonoComunicado': 'Teléfono',
            'ObservacionComunicado': 'Observaciones',

        }

    def __init__(self, *args, **kwargs):
        super(AmonestacionProfeForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['Profesor'].initial = self.instance.Profesor
        else:
            self.fields['Fecha'].initial = datetime.today()  # Establecer la fecha de hoy como valor inicial
        self.fields['Tipo'].required = True
        self.fields['Medio'].required = True

class ResumenForm(forms.Form):
    fecha = forms.DateField(widget=DatePickerInput(attrs={
        'class': 'form-control',
        'autocomplete': 'off',
        'aria-label': 'Fecha',
        'aria-describedby': 'basic-addon1',
        # 'onchange': 'this.form.submit();'
    }))

    TIPO_CHOICES = [
        ('amonestacion', 'Amonestación'),
        ('sancion', 'Sanción'),
    ]
    tipo = forms.ChoiceField(choices=TIPO_CHOICES, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
