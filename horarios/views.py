from collections import OrderedDict, defaultdict
from sqlite3 import IntegrityError

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, CreateView

from centro.models import Cursos, Aulas
from centro.views import group_check_prof, group_check_prof_or_guardia, group_check_je
from .forms import ItemHorarioForm, CopiarHorarioForm
from .models import Profesores, ItemHorario

@login_required(login_url='/')
@user_passes_test(group_check_prof_or_guardia, login_url='/')
def horario_profesor_view(request):
    profesor_id = request.GET.get('profesor')  # Obtener el ID del profesor seleccionado desde el GET
    profesores = Profesores.objects.filter(Baja=False)  # Lista de todos los profesores para el desplegable

    items_horario = None
    if profesor_id:
        profesor = Profesores.objects.get(id=profesor_id)
        if profesor.SustitutoDe:
            profesor_id = profesor.SustitutoDe.id


        # Filtrar los horarios por el profesor seleccionado y ordenar por día y tramo
        items_horario = ItemHorario.objects.filter(profesor_id=profesor_id).order_by('dia', 'tramo')

    # Crear un diccionario para el horario
    horario = {tramo: {dia: [] for dia in range(1, 6)} for tramo in range(1, 8)}
    tramos = ['1ª hora', '2ª hora', '3ª hora', 'RECREO', '4ª hora', '5ª hora', '6ª hora']

    # Diccionario para almacenar las unidades y sus materias
    unidades_dict = {}

    if items_horario:
        # Rellenar el diccionario con los ítems del horario
        for item in items_horario:
            # Si ya existen items para este tramo y día, añadimos las unidades
            for existing_item in horario[item.tramo][item.dia]:
                if (existing_item.profesor == item.profesor and
                        existing_item.materia == item.materia and
                        existing_item.aula == item.aula):
                    # Añadimos la nueva unidad al campo virtual 'unidades_combinadas'
                    existing_item.unidades_combinadas += f", {item.unidad}"
                    break
            else:
                # Si no hay coincidencias, añadimos el ítem nuevo con la unidad inicial
                item.unidades_combinadas = str(item.unidad)  # Inicializar el campo virtual
                horario[item.tramo][item.dia].append(item)

            # Llenar el diccionario de unidades y materias
            if "GUARDIA" not in str(item.unidad).upper() and "GUARDIA" not in str(item.materia).upper():
                unidad_id = item.unidad.id
                unidad_nombre = item.unidad.Curso
                materia_nombre = item.materia

                # Si la unidad ya está en el diccionario, añadimos la materia si no está
                if unidad_id in unidades_dict:
                    if materia_nombre not in unidades_dict[unidad_id]['materias']:
                        unidades_dict[unidad_id]['materias'].append(materia_nombre)
                else:
                    # Crear una nueva entrada para la unidad con su nombre y una lista de materias
                    unidades_dict[unidad_id] = {'nombre': unidad_nombre, 'materias': [materia_nombre]}

    # Ordenar las unidades por su ID
    unidades_dict = OrderedDict(sorted(unidades_dict.items()))

    # Formatear el listado de unidades y materias para el contexto
    unidades_materias = [
        {'unidad': unidad_data['nombre'], 'materias': ', '.join(unidad_data['materias'])}
        for unidad_id, unidad_data in unidades_dict.items()
    ]

    context = {
        'profesores': profesores,
        'horario': horario,
        'tramos': tramos,  # Pasar el rango de tramos al contexto
        'dias': range(1, 6),  # Pasar el rango de días al contexto
        'menu_horarios': True,
        'unidades_materias': unidades_materias
    }
    return render(request, 'horario_profesor.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_prof, login_url='/')
def mihorario(request):

    if not hasattr(request.user, 'profesor'):
        return render(request, 'error.html', {'message': 'No tiene un perfil de profesor asociado.'})

    profesor = request.user.profesor

    items_horario = None
    if profesor:

        if profesor.SustitutoDe:
            profesor = profesor.SustitutoDe

        # Filtrar los horarios por el profesor seleccionado y ordenar por día y tramo
        items_horario = ItemHorario.objects.filter(profesor=profesor).order_by('dia', 'tramo')

    # Crear un diccionario para el horario
    horario = {tramo: {dia: [] for dia in range(1, 6)} for tramo in range(1, 8)}
    tramos = ['1ª hora', '2ª hora', '3ª hora', 'RECREO', '4ª hora', '5ª hora', '6ª hora']

    if items_horario:
        # Rellenar el diccionario con los ítems del horario
        for item in items_horario:
            # Si ya existen items para este tramo y día, añadimos las unidades
            for existing_item in horario[item.tramo][item.dia]:
                if (existing_item.profesor == item.profesor and
                        existing_item.materia == item.materia and
                        existing_item.aula == item.aula):
                    # Añadimos la nueva unidad al campo virtual 'unidades_combinadas'
                    existing_item.unidades_combinadas += f", {item.unidad}"
                    break
            else:
                # Si no hay coincidencias, añadimos el ítem nuevo con la unidad inicial
                item.unidades_combinadas = str(item.unidad)  # Inicializar el campo virtual
                horario[item.tramo][item.dia].append(item)

    context = {
        'profesor': profesor,
        'horario': horario,
        'tramos': tramos,  # Pasar el rango de tramos al contexto
        'dias': range(1, 6),  # Pasar el rango de días al contexto
        'menu_horarios': True
    }
    return render(request, 'mihorario.html', context)

@login_required(login_url='/')
@user_passes_test(group_check_prof_or_guardia, login_url='/')
def horario_curso_view(request):
    curso_id = request.GET.get('curso')  # Obtener el ID del curso seleccionado desde el GET
    cursos = Cursos.objects.all()  # Lista de todos los cursos para el desplegable

    items_horario = None
    profesores_materias = defaultdict(list)
    tutor = None

    if curso_id:
        # Filtrar los horarios por el curso seleccionado y ordenar por día y tramo
        items_horario = ItemHorario.objects.filter(
            Q(unidad_id=curso_id) & Q(profesor__Baja=False)
        ).order_by('dia', 'tramo')

        # Obtener el curso y su tutor
        curso = Cursos.objects.filter(id=curso_id).first()
        if curso and curso.Tutor:
            tutor = curso.Tutor  # Asignar el tutor del curso

        # Agrupar profesores y materias en el curso
        for item in items_horario:
            if item.profesor and item.materia:  # Asegurarse de que hay un profesor y una materia en el ItemHorario
                profesores_materias[item.profesor].append(item.materia)

    # Crear un diccionario para el horario
    horario = {tramo: {dia: [] for dia in range(1, 6)} for tramo in range(1, 8)}
    tramos = ['1ª hora', '2ª hora', '3ª hora', 'RECREO', '4ª hora', '5ª hora', '6ª hora']

    if items_horario:
        # Rellenar el diccionario con los ítems del horario
        for item in items_horario:
            horario[item.tramo][item.dia].append(item)

    # Convertir materias en una lista única por profesor
    profesores_materias = {profesor: ', '.join(set(materias)) for profesor, materias in profesores_materias.items()}

    context = {
        'cursos': cursos,
        'horario': horario,
        'tramos': tramos,  # Pasar el rango de tramos al contexto
        'dias': range(1, 6),  # Pasar el rango de días al contexto
        'profesores_materias': profesores_materias,
        'tutor': tutor,
        'menu_horarios': True
    }
    return render(request, 'horario_grupo.html', context)

class EditarHorarioProfesorView(ListView):
    model = ItemHorario
    template_name = 'editar_horario_profesor.html'
    context_object_name = 'items_horario'

    def get_queryset(self):
        profesor_id = self.kwargs['profesor_id']
        return ItemHorario.objects.filter(profesor__id=profesor_id).order_by('dia', 'tramo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profesor'] = get_object_or_404(Profesores, id=self.kwargs['profesor_id'])
        context['form'] = ItemHorarioForm()  # Pasar el formulario al contexto
        return context


class UpdateHorarioView(UpdateView):
    model = ItemHorario
    form_class = ItemHorarioForm  # El formulario que usas para editar
    template_name = 'editar_item_horario.html'

    def get_success_url(self):
        # Obtener el ID del profesor desde el objeto ItemHorario actualizado
        profesor_id = self.object.profesor.id
        # Redirigir a la vista 'editar_horario_profesor' pasando el profesor_id
        return reverse_lazy('editar_horario_profesor', kwargs={'profesor_id': profesor_id})

    def form_valid(self, form):
        # Aquí puedes realizar alguna acción antes de guardar, si es necesario
        return super().form_valid(form)

class DeleteHorarioView(DeleteView):
    model = ItemHorario
    template_name = 'confirmar_eliminar_horario.html'  # Plantilla de confirmación
    success_url = reverse_lazy('editar_horario_profesor')  # Redirige a la vista de editar el horario después de eliminar

    def get_success_url(self):
        # Redirige a la página de edición del profesor específico
        return reverse_lazy('editar_horario_profesor', kwargs={'profesor_id': self.object.profesor.id})


class CrearItemHorarioView(CreateView):
    model = ItemHorario
    form_class = ItemHorarioForm
    template_name = 'editar_horario_profesor.html'

    def form_valid(self, form):
        # Guarda el nuevo ítem de horario
        try:
            item = form.save(commit=False)
            item.profesor = get_object_or_404(Profesores,
                                              id=self.kwargs['profesor_id'])  # Asegurarse de asignar el profesor
            item.save()
        except IntegrityError:
            print("Ya existe un ItemHorario igual")

        # Si la solicitud es AJAX, devolvemos un JSON con los datos del nuevo ítem
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            data = {
                'id': item.id,
                'tramo': item.get_tramo_display(),
                'dia': item.get_dia_display(),
                'materia': item.materia,
                'aula': item.aula.Aula
            }
            return JsonResponse(data)

        return super().form_valid(form)

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def aulas_libres(request):
    # Obtener todas las aulas que no contengan las palabras clave
    aulas = Aulas.objects.exclude(
        Aula__icontains='Maleta'
    ).exclude(
        Aula__icontains='Carro'
    ).exclude(
        Aula__icontains='Moodle'
    ).exclude(
        Aula__icontains='Otros'
    ).exclude(
        Aula__icontains='profesores'
    ).exclude(
        Aula__icontains='Dpto'
    ).exclude(
        Aula__icontains='Biblioteca'
    ).exclude(
        Aula__icontains='familias'
    ).exclude(
        Aula__icontains='Laboratorio'
    ).exclude(
        Aula__icontains='Convivencia'
    ).exclude(
        Aula__icontains='Música'
    ).exclude(
        Aula__icontains='Taller'
    )

    tramos = ['1ª hora', '2ª hora', '3ª hora', 'RECREO', '4ª hora', '5ª hora', '6ª hora']

    # Obtener todos los ítems de horario
    items_horario = ItemHorario.objects.all()

    # Crear un diccionario para las aulas libres
    horario_aulas_libres = {tramo: {dia: [] for dia in range(1, 6)} for tramo in range(1, 8)}

    # Llenar el diccionario de aulas libres
    for aula in aulas:
        for tramo in range(1, 8):
            if tramo == 4:
                continue
            for dia in range(1, 6):
                # Comprobar si la aula está ocupada en el tramo y día específicos
                if not items_horario.filter(aula=aula, tramo=tramo, dia=dia).exists():
                    horario_aulas_libres[tramo][dia].append(aula)

    context = {
        'aulas_libres': horario_aulas_libres,
        'tramos': tramos,
        'dias': range(1, 6),
        'menu_horarios': True
    }


    return render(request, 'aulas_libres.html', context)

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def copiar_horario(request):
    if request.method == 'POST':
        form = CopiarHorarioForm(request.POST)
        if form.is_valid():

            profe_origen = form.cleaned_data['ProfesorOrigen']
            profe_destino = form.cleaned_data['ProfesorDestino']

            # Copiar horario
            try:
                horario_origen = ItemHorario.objects.filter(profesor=profe_origen)

                # Borrar horario del profesor de destino antes de copiar
                ItemHorario.objects.filter(profesor=profe_destino).delete()

                items_nuevos = []
                for item in horario_origen:
                    nuevo_item = ItemHorario(
                        tramo=item.tramo,
                        dia=item.dia,
                        profesor=profe_destino,
                        unidad=item.unidad,
                        aula=item.aula,
                        materia=item.materia
                    )
                    items_nuevos.append(nuevo_item)

                ItemHorario.objects.bulk_create(items_nuevos)

                print(f"Horario de {profe_origen} copiado exitosamente a {profe_destino}.")
                context = {'form': form, 'profe_origen': profe_origen, 'profe_destino': profe_destino, 'exito': True}
            except ObjectDoesNotExist as e:
                print(f"Error: {e}")
                context = {'form': form, 'exito': False, 'error': e}

        else:
            context = {'form': form, 'exito': False, 'error': form.errors}
    else:
        form = CopiarHorarioForm()
        context = {'form': form}

    return render(request, 'copiar_horario.html', context)

