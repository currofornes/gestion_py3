from django import forms
from centro.models import Cursos, Departamentos, Areas, Profesores


class UnidadForm(forms.Form):
    Unidad = forms.ModelChoiceField(queryset=Cursos.objects.order_by('Curso'), empty_label=None,widget=forms.Select(attrs={'class': "form-control select2_unidad",'onchange': 'this.form.submit();'}))

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
    Unidad = forms.ModelChoiceField(queryset=Cursos.objects.order_by('Curso'), empty_label=None, widget=forms.Select(
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
        super(UnidadesProfeForm, self).__init__(*args, **kwargs)

        if profesor:
            cursos_profesor = Cursos.objects.filter(EquipoEducativo=profesor).order_by('Curso')
            cursos_resto = Cursos.objects.exclude(EquipoEducativo=profesor).order_by('Curso')
            self.fields['Unidad'].queryset = cursos_profesor
            self.fields['UnidadResto'].queryset = cursos_resto

            if "Unidad" in args[0] and args[0]["Unidad"] != "":
                self.fields['Unidad'].initial = args[0]["Unidad"]
            if "UnidadResto" in args[0] and args[0]["UnidadResto"] != "":
                self.fields['UnidadResto'].initial = args[0]["UnidadResto"]

        def label_from_instance(obj):
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