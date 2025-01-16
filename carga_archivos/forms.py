from django import forms
from centro.models import Niveles, CursoAcademico



class CargaCalificacionesSeneca(forms.Form):
    ArchivoZip = forms.FileField(
        label="Archivo ZIP",
        widget=forms.FileInput(attrs={'class': 'custom-file-input'}),
        help_text="Selecciona un archivo ZIP con las calificaciones (sin las pendientes)."
    )
    CursoAcademico = forms.ModelChoiceField(
        queryset=CursoAcademico.objects.all(),
        label="Curso Académico",
        widget=forms.Select(attrs={'class': 'form-control select2_CursoAcademico'}),
        help_text="Selecciona un curso académico"
    )
    Convocatoria = forms.ChoiceField(
        choices=(
            ('EVI', 'Evaluación inicial'),
            ('1EV', '1ª Evaluación'),
            ('2EV', '2ª Evaluacion'),
            ('3EV', '3ª Evaluacion'),
            ('FFP', 'Final FP'),
            ('Ord', 'Ordinaria'),
            ('Ext', 'Extraordinaria')
        ),
        label="Convocatoria",
        widget=forms.Select(attrs={'class': 'form-control select2_Convocatoria'}),
        help_text="Selecciona la convocatoria"
    )

class CargaRegAlumSeneca(forms.Form):
    ArchivoCSV = forms.FileField(
        label="Archivo CSV",
        widget=forms.FileInput(attrs={'class': 'custom-file-input'}),
        help_text="Selecciona un archivo con los datos del alumnado (RegAlum)"
    )
    CursoAcademico = forms.ModelChoiceField(
        queryset=CursoAcademico.objects.all(),
        label="Curso Académico",
        widget=forms.Select(attrs={'class': 'form-control select2_CursoAcademico'}),
        help_text="Selecciona un curso académico"
    )

class CargaAdmisionSeneca(forms.Form):
    ArchivoCSV_1_ESO = forms.FileField(
        label="Archivo CSV 1º ESO",
        widget=forms.FileInput(attrs={'class': 'custom-file-input'}),
        help_text="Selecciona un archivo con los datos de admisión del del alumnado de 1º ESO"
    )
    ArchivoCSV_1_BTO_CyT = forms.FileField(
        label="Archivo CSV 1º BTO CyT",
        widget=forms.FileInput(attrs={'class': 'custom-file-input'}),
        help_text="Selecciona un archivo con los datos de admisión del del alumnado de 1º BTO CyT"
    )
    ArchivoCSV_1_BTO_HyCS = forms.FileField(
        label="Archivo CSV 1º BTO HyCS",
        widget=forms.FileInput(attrs={'class': 'custom-file-input'}),
        help_text="Selecciona un archivo con los datos de admisión del del alumnado de 1º BTO HyCS"
    )
    CursoAcademico = forms.ModelChoiceField(
        queryset=CursoAcademico.objects.all(),
        label="Curso Académico",
        widget=forms.Select(attrs={'class': 'form-control select2_CursoAcademico'}),
        help_text="Selecciona un curso académico"
    )