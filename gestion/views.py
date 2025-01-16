import os
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponseForbidden, FileResponse
from django.shortcuts import render,redirect
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection

from centro.utils import importar_profesores
from centro.views import is_tutor
from gestion.forms import CustomPasswordChangeForm, QueryForm


# Create your views here.

# Vista de cambio de contraseña
@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa después del cambio de contraseña
            messages.success(request, 'Tu contraseña se ha cambiado con éxito.')
            # Actualiza el campo en el modelo Profesores
            if hasattr(request.user, 'profesor'):
                request.user.profesor.password_changed = True
                request.user.profesor.save()
            return redirect('index')  # Redirige al índice o a otra vista adecuada
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'cambiar_password.html', {'form': form})


@login_required
def cambiar_password_custom(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa después del cambio de contraseña
            messages.success(request, 'Tu contraseña se ha cambiado con éxito.')
            # Actualiza el campo en el modelo Profesores
            if hasattr(request.user, 'profesor'):
                request.user.profesor.password_changed = True
                request.user.profesor.save()
            return redirect('index')  # Redirige al índice o a otra vista adecuada
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'cambiar_password_custom.html', {'form': form})

# Curro Jul 24: Simplifico el index y dejo la logica para el login_view
@login_required(login_url='/login/')
def index(request):
    #if not request.user.groups.filter(name__in=['jefatura de estudios']):
    if not request.user.is_superuser:
        # Verifica si el usuario ha cambiado su contraseña
        if not hasattr(request.user, 'profesor') or not request.user.profesor.password_changed:
            return redirect(reverse('cambiar_password'))  # Redirige a la vista de cambio de contraseña
    return render(request, 'index.html')

@login_required(login_url='/')
def salir(request):
    logout(request)
    return redirect('/')

# Curro Jul 24: Defino la vista para el login
def login_view(request):
    context = {'next': request.GET.get('next', '/')}
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            #if not user.groups.filter(name__in=['jefatura de estudios']):
            if not user.is_superuser:
                # Verifica si el usuario tiene un perfil de Profesor y si debe cambiar la contraseña
                if hasattr(user, 'profesor') and not user.profesor.password_changed:
                    return redirect(reverse('cambiar_password'))

            next_url = request.POST.get("next", "/")
            return redirect(next_url)
        else:
            context['error'] = True

    return render(request, 'login.html', context)


def descargar_base_datos(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para descargar la base de datos.")

    # Ruta al archivo de la base de datos
    db_path = settings.DATABASES['default']['NAME']
    response = FileResponse(open(db_path, 'rb'), as_attachment=True, filename=os.path.basename(db_path))
    return response


@staff_member_required
def cargar_qry(request):
    result = None
    error = None
    columnas = None
    if request.method == "POST":
        form = QueryForm(request.POST)
        if form.is_valid():
            print("hola")
            print(form.cleaned_data)
            query = form.cleaned_data["query"]

            print(query)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    if query.strip().lower().startswith("select"):
                        columnas = [col[0] for col in cursor.description]
                        print(columnas)
                        columnas = cursor.description
                        result = cursor.fetchall()
            except Exception as e:
                error = str(e)
        else:
            print("Algo falla!")
            print(form.errors)
            print(form.cleaned_data)
    else:
        form = QueryForm()

    return render(request, "cargar_qry.html", {"form": form, "result": result, "columnas": columnas, "error": error})