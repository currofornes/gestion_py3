from django.urls import re_path, path

from . import views

urlpatterns = [
	re_path(r'^historial/(?P<alum_id>[0-9]+)/(?P<prof>[a-z]*)$', views.historial),
	re_path(r'^historial_vigente/(?P<alum_id>[0-9]+)/(?P<prof>[a-z]*)$', views.historial_vigente),
	re_path(r'^(?P<tipo>[a-z]+)/(?P<alum_id>[0-9]+)$', views.parte),
	re_path(r'^resumen/', views.resumen, name='resumen'),  # Para GET sin parámetros
    re_path(r'^resumen/(?P<tipo>[a-z]+)/(?P<fecha>[0-9]+)/', views.resumen, name='resumen_con_parametros'),  # Para GET con parámetros
    #re_path(r'^resumen/(?P<tipo>[a-z]+)$', views.resumen),
	#re_path(r'^resumen/(?P<tipo>[a-z]+)/(?P<mes>[0-9]+)/(?P<ano>[0-9]+)$', views.resumen),
	re_path(r'^show/$', views.show, name='show_default'),
	#path('show/<str:tipo>/<int:mes>/<int:ano>/<int:dia>/', views.show, name='show'),
	path('show/<str:tipo>/<int:mes>/<int:ano>/<int:dia>/', views.show, name='show'),
	#re_path(r'^show/(?P<tipo>[a-z]+)/(?P<mes>[0-9]+)/(?P<ano>[0-9]+)/(?P<dia>[0-9]+)$', views.show),
	re_path(r'^estadistica$', views.estadisticas),
	# re_path(r'^alumnadosancionable$', views.alumnadosancionable),
	re_path(r'^estadistica/curso/(?P<curso>[0-9]+)$', views.estadisticas2),
	re_path(r'^grupos', views.grupos),
	re_path(r'^niveles', views.niveles),
	re_path(r'^alumnos', views.alumnos),
	re_path(r'^horas$', views.horas),
    re_path(r'^profesores$', views.profesores),
	re_path(r'^aulaconvivencia$', views.aulaconvivencia),
	# Curro Jul 24: Anado vista para permitir a un profesor anadir un parte
	re_path(r'^profe/(?P<tipo>[a-z]+)/(?P<alum_id>[0-9]+)$', views.parteprofe),

	re_path(r'^misamonestaciones/', views.misamonestaciones, name='misamonestaciones'),

	re_path(r'^amonestacionesprofe/(?P<profe_id>[0-9]+)', views.amonestacionesprofe, name='amonestacionesprofe'),

	re_path(r'^sancionesactivas$', views.sancionesactivas, name='sancionesactivas'),

	re_path(r'^alumnadosancionable$', views.alumnadosancionable, name='alumnadosancionable'),

	re_path(r'^reincorporacionsanciones$', views.sanciones_reincorporacion, name='sanciones_reincorporacion'),

	re_path(r'^ignorar/(?P<prop_id>[0-9]+)', views.ignorar_propuesta_sancion, name='ignorar'),




        	

	

]
