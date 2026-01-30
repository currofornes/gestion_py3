from django import forms
from django.core.exceptions import ObjectDoesNotExist
from .models import InformeDepartamento, AsignacionMateriaDepartamento, CampanaTransito
from centro.models import Materia, Centros, CursoAcademico


class InformeDepartamentoForm(forms.ModelForm):
    class Meta:
        model = InformeDepartamento
        fields = ['centro_origen', 'materia', 'cuestiones_generales', 'fortalezas', 'debilidades']
        widgets = {
            'cuestiones_generales': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'fortalezas': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'debilidades': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.campana = kwargs.pop('campana', None)
        self.user = kwargs.pop('user', None)  # Recibimos el usuario

        super().__init__(*args, **kwargs)

        if self.campana and self.user:
            # 1. Filtramos Centros
            self.fields['centro_origen'].queryset = self.campana.centros_origen.all()

            # 2. Filtramos Materias (NUEVA LÓGICA)
            try:
                # Obtenemos el perfil de profesor del usuario
                profesor = self.user.profesor
                # Obtenemos su departamento
                mi_departamento = profesor.Departamento

                # Buscamos en la tabla de asignación qué materias tocan a este departamento en esta campaña
                materias_ids = AsignacionMateriaDepartamento.objects.filter(
                    campana=self.campana,
                    departamento=mi_departamento
                ).values_list('materia_id', flat=True)

                # Filtramos el QuerySet de materia
                self.fields['materia'].queryset = Materia.objects.filter(id__in=materias_ids)

            except ObjectDoesNotExist:
                # Si el usuario no es profesor o no tiene departamento, no ve materias
                self.fields['materia'].queryset = self.fields['materia'].queryset.none()

        else:
            self.fields['centro_origen'].queryset = self.fields['centro_origen'].queryset.none()
            self.fields['materia'].queryset = self.fields['materia'].queryset.none()


class DescargarInformeForm(forms.Form):
    curso = forms.ModelChoiceField(
        queryset=CursoAcademico.objects.all().order_by('-año_inicio'),
        label="Curso Académico",
        widget=forms.Select(attrs={'class': 'form-control select2-simple', 'onchange': 'this.form.submit();'})
    )

    campana = forms.ModelChoiceField(
        queryset=CampanaTransito.objects.none(),
        label="Campaña de Tránsito",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2-simple', 'onchange': 'this.form.submit();'})
    )

    centro = forms.ModelChoiceField(
        queryset=Centros.objects.none(),
        label="Centro de Origen",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2-simple'})
    )

    def __init__(self, *args, **kwargs):
        # Capturamos datos iniciales si vienen en el POST o GET para filtrar
        data = kwargs.get('data')
        super().__init__(*args, **kwargs)

        # Lógica de filtrado en cascada
        if data:
            curso_id = data.get('curso')
            campana_id = data.get('campana')

            if curso_id:
                try:
                    # Filtrar campañas por curso seleccionado
                    self.fields['campana'].queryset = CampanaTransito.objects.filter(curso_academico_id=curso_id)
                except (ValueError, TypeError):
                    pass

            if campana_id:
                try:
                    # Filtrar centros por campaña seleccionada
                    campana = CampanaTransito.objects.get(id=campana_id)
                    self.fields['centro'].queryset = campana.centros_origen.all()
                except (ValueError, TypeError, CampanaTransito.DoesNotExist):
                    pass


class RendimientoDepartamentosForm(forms.Form):
    curso = forms.ModelChoiceField(
        queryset=CursoAcademico.objects.all().order_by('-año_inicio'),
        label="Curso Académico",
        widget=forms.Select(attrs={'class': 'form-control select2-simple', 'onchange': 'this.form.submit();'})
    )

    campana = forms.ModelChoiceField(
        queryset=CampanaTransito.objects.none(),
        label="Campaña de Tránsito",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2-simple'})
    )

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data')
        super().__init__(*args, **kwargs)

        if data and data.get('curso'):
            try:
                self.fields['campana'].queryset = CampanaTransito.objects.filter(
                    curso_academico_id=data.get('curso')
                )
            except (ValueError, TypeError):
                pass


class InformeHistoricoForm(forms.ModelForm):
    # Campos de selección de contexto
    curso = forms.ModelChoiceField(
        queryset=CursoAcademico.objects.all().order_by('-año_inicio'),
        label="Curso Académico",
        widget=forms.Select(attrs={'class': 'form-control select2-simple', 'onchange': 'this.form.submit();'})
    )

    campana_seleccion = forms.ModelChoiceField(
        queryset=CampanaTransito.objects.none(),
        label="Campaña de Tránsito",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2-simple', 'onchange': 'this.form.submit();'})
    )

    centro_seleccion = forms.ModelChoiceField(
        queryset=Centros.objects.none(),
        label="Centro de Origen",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2-simple', 'onchange': 'this.form.submit();'})
    )

    materia_seleccion = forms.ModelChoiceField(
        queryset=Materia.objects.none(),
        label="Materia",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2-simple', 'onchange': 'this.form.submit();'})
    )

    class Meta:
        model = InformeDepartamento
        fields = ['cuestiones_generales', 'fortalezas', 'debilidades']
        widgets = {
            'cuestiones_generales': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'fortalezas': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'debilidades': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lógica de filtrado dinámico de los desplegables
        data = self.data if self.data else {}

        # 1. Filtrar Campañas por Curso
        curso_id = data.get('curso')
        if curso_id:
            self.fields['campana_seleccion'].queryset = CampanaTransito.objects.filter(curso_academico_id=curso_id)

        # 2. Filtrar Centros y Materias por Campaña
        campana_id = data.get('campana_seleccion')
        if campana_id:
            try:
                campana = CampanaTransito.objects.get(id=campana_id)
                self.fields['centro_seleccion'].queryset = campana.centros_origen.all()
                self.fields['materia_seleccion'].queryset = campana.materias_implicadas.all().order_by(
                    'abr')
            except CampanaTransito.DoesNotExist:
                pass
