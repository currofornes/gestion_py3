from django import forms
from centro.models import Niveles, CursoAcademico, Centros

class AnalisisResultados(forms.Form):

    Convocatoria = forms.ChoiceField(
        choices=(
            ('1EV', '1ª Evaluación'),
            ('2EV', '2ª Evaluacion'),
            ('Ord', 'Ordinaria'),
        ),
        label="Convocatoria",
        widget=forms.Select(attrs={'class': 'form-control select2_Convocatoria'}),
        help_text="Selecciona la convocatoria"
    )

class AnalisisResultadosPorCentros1ESO(forms.Form):
    Convocatoria = forms.ChoiceField(
        choices=(
            ('1EV', '1ª Evaluación'),
            ('2EV', '2ª Evaluacion'),
            ('Ord', 'Ordinaria'),
        ),
        label="Convocatoria",
        widget=forms.Select(attrs={'class': 'form-control select2_Convocatoria'}),
        help_text="Selecciona la convocatoria"
    )
    Centros = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2_Centros', 'multiple': 'multiple'})
    )

    def __init__(self, *args, **kwargs):
        super(AnalisisResultadosPorCentros1ESO, self).__init__(*args, **kwargs)
        self.fields['Centros'].required = False
        centros = centros = Centros.objects.filter(Nombre__icontains='C.E.I.P.').order_by('Nombre').all()
        self.fields['Centros'].choices = [(c.pk, c.Nombre) for c in centros]

class AnalisisResultadosPorCentrosESO(forms.Form):
    Convocatoria = forms.ChoiceField(
        choices=(
            ('1EV', '1ª Evaluación'),
            ('2EV', '2ª Evaluacion'),
            ('Ord', 'Ordinaria'),
        ),
        label="Convocatoria",
        widget=forms.Select(attrs={'class': 'form-control select2_Convocatoria'}),
        help_text="Selecciona la convocatoria"
    )
    Cursos = forms.MultipleChoiceField(
        choices=(
            ('1º ESO', '1º de E.S.O.'),
            ('2º ESO', '2º de E.S.O.'),
            ('3º ESO', '3º de E.S.O.'),
            ('4º ESO', '4º de E.S.O.'),
        ),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2_Cursos', 'multiple': 'multiple'})
    )
    Centros = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2_Centros', 'multiple': 'multiple'})
    )

    def __init__(self, *args, **kwargs):
        super(AnalisisResultadosPorCentrosESO, self).__init__(*args, **kwargs)
        self.fields['Centros'].required = False
        centros = centros = Centros.objects.filter(Nombre__icontains='C.E.I.P.').order_by('Nombre').all()
        self.fields['Centros'].choices = [(c.pk, c.Nombre) for c in centros]