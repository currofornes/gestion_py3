"""gestion URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import include, re_path, path
from django.contrib import admin

from gestion.views import index, salir, login_view, cambiar_password, cambiar_password_custom, descargar_base_datos

urlpatterns = [

    path('admin/descargar-db/', descargar_base_datos, name='descargar_base_datos'),
    path('admin/', admin.site.urls),
    path('centro/', include('centro.urls')),
    path('convivencia/', include('convivencia.urls')),
    path('pdf/', include('pdf.urls')),
    path('',index, name='index'),
    path('logout/',salir),
    # Curro Jul 24:
    path(r'login/', login_view, name='login'),
    path('tde/', include('tde.urls')),
    path('absentismo/', include('absentismo.urls')),

    path('reservas/', include('reservas.urls')),

    path('guardias/', include('guardias.urls')),

    path('horarios/', include('horarios.urls')),

    path('DACE/', include('DACE.urls')),

    path('cambiar-password/', cambiar_password, name='cambiar_password'),
    path('cambiar-password-custom/', cambiar_password_custom, name='cambiar_password_custom'),



]
