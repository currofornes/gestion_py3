from django import forms
from centro.models import Cursos, Departamentos, Areas, Profesores, MomentoRevisionLibros, RevisionLibroAlumno


class UnidadForm(forms.Form):
    Unidad = forms.ModelChoiceField(queryset=Cursos.objects.all(), empty_label=None,widget=forms.Select(attrs={'class': "form-control select2_unidad",'onchange': 'this.form.submit();'}))

class DepartamentosForm(forms.Form):
    Areas = forms.ModelChoiceField(queryset=Areas.objects.all(),required=False,widget=forms.Select(attrs={'class': "form-control select2_area", 'onchange': 'this.form.submit();'}))
    Departamento = forms.ModelChoiceField(queryset=Departamentos.objects.order_by('Nombre'), required=False,widget=forms.Select(attrs={'class': "form-control select2_departamento", 'onchange': 'this.form.submit();'}))

    def __init__(self, *args, **kwargs):
        super(DepartamentosForm, self).__init__(*args, **kwargs)
        if "Areas" in args[0] and args[0]["Areas"]!="":
            areas=Areas.objects.get(id=args[0]["Areas"])
            self.fields['Departamento']. queryset= areas.Departamentos.all()
            self.fields['Departamento'].initial=args[0]["Departamento"]

# Curro Jul 24: Defino el form UnidadProfe
class UnidadProfeForm(forms.Form):
    Unidad = forms.ModelChoiceField(queryset=Cursos.objects.all(), empty_label=None, widget=forms.Select(
        attrs={'class': "form-control select2_unidad", 'onchange': 'this.form.submit();'}))

    def __init__(self, *args, **kwargs):
        profesor = kwargs.pop('profesor', None)
        super(UnidadProfeForm, self).__init__(*args, **kwargs)
        if "Cursos" in args[0] and args[0]["Cursos"] != "":
            cursos = args[0]["Cursos"]
            self.fields['Unidad'].queryset = cursos
            if "Unidad" in args[0] and args[0]["Unidad"] != "":
                self.fields['Unidad'].initial = args[0]["Unidad"]

        def label_from_instance(obj):
            label = u"{} {}".format(obj.Curso, u" (Tutoria)" if obj.Tutor == profesor else u"")
            return label

        self.fields['Unidad'].label_from_instance = label_from_instance


class UnidadesProfeForm(forms.Form):
    Unidad = forms.ModelChoiceField(queryset=Cursos.objects.none(), empty_label=None, required=False,
                                    widget=forms.Select(
                                            attrs={'class': "form-control select2_unidad",
                                               'onchange': 'this.form.submit(); setFormTrigger("Unidad");'}))
    UnidadResto = forms.ModelChoiceField(queryset=Cursos.objects.none(), empty_label=None, required=False,
                                         widget=forms.Select(
                                             attrs={'class': "form-control select2_unidad_resto",
                                                    'onchange': 'this.form.submit(); setFormTrigger("UnidadResto");'}))

    FormTrigger = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        profesor = kwargs.pop('profesor', None)
        curso_academico = kwargs.pop('curso_academico', None)  # Obtenemos el curso académico actual
        super(UnidadesProfeForm, self).__init__(*args, **kwargs)

        if profesor and curso_academico:
            # Obtener los cursos en los que el profesor imparte materias en el curso académico especificado
            cursos_profesor = Cursos.objects.filter(
                materiaimpartida__profesor=profesor,
                materiaimpartida__curso_academico=curso_academico
            ).order_by('Curso')

            # Obtener los cursos restantes (donde el profesor no esté asignado)
            cursos_resto = Cursos.objects.exclude(
                materiaimpartida__profesor=profesor,
                materiaimpartida__curso_academico=curso_academico
            ).order_by('Curso')

            # Asignamos los resultados a los campos
            self.fields['Unidad'].queryset = cursos_profesor
            self.fields['UnidadResto'].queryset = cursos_resto

            # Establecer valores iniciales, si se proporcionan
            if "Unidad" in args[0] and args[0]["Unidad"] != "":
                self.fields['Unidad'].initial = args[0]["Unidad"]
            if "UnidadResto" in args[0] and args[0]["UnidadResto"] != "":
                self.fields['UnidadResto'].initial = args[0]["UnidadResto"]

        def label_from_instance(obj):
            # Etiqueta personalizada para mostrar el curso y si el profesor es tutor
            label = u"{} {}".format(obj.Curso, u" (Tutoria)" if obj.Tutor == profesor else u"")
            return label

        self.fields['Unidad'].label_from_instance = label_from_instance
        self.fields['Unidad'].label = "Mis Unidades"
        self.fields['UnidadResto'].label = "Resto de Unidades"



class AsignarProfesoresDepartamentoForm(forms.Form):
    departamento = forms.ModelChoiceField(queryset=Departamentos.objects.all(), label="Selecciona un departamento")
    profesores = forms.ModelMultipleChoiceField(
        queryset=Profesores.objects.filter(Departamento__isnull=True, Baja=False),
        widget=forms.CheckboxSelectMultiple,
        label="Selecciona los profesores"
    )


class SeleccionRevisionForm(forms.Form):
    profesor = forms.ModelChoiceField(queryset=None)
    momento = forms.ModelChoiceField(queryset=MomentoRevisionLibros.objects.all())
    materia = forms.ModelChoiceField(queryset=None)
    libro = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        profesores_qs = kwargs.pop('profesores_qs')
        materias_qs = kwargs.pop('materias_qs')
        libros_qs = kwargs.pop('libros_qs')
        super().__init__(*args, **kwargs)
        self.fields['profesor'].queryset = profesores_qs
        self.fields['materia'].queryset = materias_qs
        self.fields['libro'].queryset = libros_qs

        self.fields['profesor'].widget.attrs.update({'class': 'form-control select2_Profesor'})
        self.fields['momento'].widget.attrs.update({'class': 'form-control select2_Momento'})
        self.fields['materia'].widget.attrs.update({'class': 'form-control select2_Materia'})
        self.fields['libro'].widget.attrs.update({'class': 'form-control select2_Libro'})

class SeleccionRevisionProfeForm(forms.Form):
    momento = forms.ModelChoiceField(queryset=MomentoRevisionLibros.objects.all())
    materia = forms.ModelChoiceField(queryset=None)
    libro = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        profesor = kwargs.pop('profesor')
        materias_qs = kwargs.pop('materias_qs')
        libros_qs = kwargs.pop('libros_qs')
        super().__init__(*args, **kwargs)

        self.profesor = profesor  # por si lo necesitas en clean() o save()

        self.fields['materia'].queryset = materias_qs
        self.fields['libro'].queryset = libros_qs

        self.fields['momento'].widget.attrs.update({'class': 'form-control select2_Momento'})
        self.fields['materia'].widget.attrs.update({'class': 'form-control select2_Materia'})
        self.fields['libro'].widget.attrs.update({'class': 'form-control select2_Libro'})

class RevisionLibroAlumnoForm(forms.ModelForm):
    class Meta:
        model = RevisionLibroAlumno
        fields = ['estado', 'observaciones']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].widget.attrs.update({'class': 'form-control'})
        self.fields['observaciones'].widget.attrs.update({'class': 'form-control'})

class ProfesorSustitutoForm(forms.Form):
    username = forms.CharField(max_length=150, label="Nombre de usuario")
    nombre = forms.CharField(max_length=20, label="Nombre")
    apellidos = forms.CharField(max_length=30, label="Apellidos")
    dni = forms.CharField(max_length=10, label="DNI")
    email = forms.EmailField(label="Correo electrónico")
    profesor_sustituido = forms.ModelChoiceField(
        queryset=Profesores.objects.filter(Baja=False),
        label="Profesor a sustituir"
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("El nombre de usuario ya existe.")
        return username