from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, CreateView

from centro.models import Cursos
from .forms import ItemHorarioForm
from .models import Profesores, ItemHorario

def horario_profesor_view(request):
    profesor_id = request.GET.get('profesor')  # Obtener el ID del profesor seleccionado desde el GET
    profesores = Profesores.objects.filter(Baja=False)  # Lista de todos los profesores para el desplegable

    items_horario = None
    if profesor_id:
        # Filtrar los horarios por el profesor seleccionado y ordenar por día y tramo
        items_horario = ItemHorario.objects.filter(profesor_id=profesor_id).order_by('dia', 'tramo')

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
        'profesores': profesores,
        'horario': horario,
        'tramos': tramos,  # Pasar el rango de tramos al contexto
        'dias': range(1, 6),  # Pasar el rango de días al contexto
        'menu_horarios': True
    }
    return render(request, 'horario_profesor.html', context)


def mihorario(request):

    if not hasattr(request.user, 'profesor'):
        return render(request, 'error.html', {'message': 'No tiene un perfil de profesor asociado.'})

    profesor = request.user.profesor

    items_horario = None
    if profesor:
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


def horario_curso_view(request):
    curso_id = request.GET.get('curso')  # Obtener el ID del curso seleccionado desde el GET
    cursos = Cursos.objects.all()  # Lista de todos los cursos para el desplegable

    items_horario = None
    if curso_id:
        # Filtrar los horarios por el curso seleccionado y ordenar por día y tramo
        items_horario = ItemHorario.objects.filter(unidad_id=curso_id).order_by('dia', 'tramo')

    # Crear un diccionario para el horario
    horario = {tramo: {dia: [] for dia in range(1, 6)} for tramo in range(1, 8)}
    tramos = ['1ª hora', '2ª hora', '3ª hora', 'RECREO', '4ª hora', '5ª hora', '6ª hora']

    if items_horario:
        # Rellenar el diccionario con los ítems del horario
        for item in items_horario:
            horario[item.tramo][item.dia].append(item)

    context = {
        'cursos': cursos,
        'horario': horario,
        'tramos': tramos,  # Pasar el rango de tramos al contexto
        'dias': range(1, 6),  # Pasar el rango de días al contexto
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
        item = form.save(commit=False)
        item.profesor = get_object_or_404(Profesores,
                                          id=self.kwargs['profesor_id'])  # Asegurarse de asignar el profesor
        item.save()

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