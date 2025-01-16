from django.urls import include, re_path, path
from . import views

urlpatterns = [
    path('faltas/<int:proto_id>/', views.faltas, name='faltas'),

    path('faltas_json/<int:proto_id>/', views.faltas_json, name='faltas_json'),

    path('amonestaciones/<int:alum_id>/', views.amonestaciones, name='amonestaciones'),

    path('amonestaciones_json/<int:alum_id>', views.amonestaciones_json, name='amonestaciones_json'),

]