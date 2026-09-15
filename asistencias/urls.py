from django.urls import path
from inicio_sesion import views as inicio_view
from asistencias import views as asistencia_view

urlpatterns = [
    path('registrar_asistencia/', inicio_view.autenticado_required(asistencia_view.registrar_asistencia), name='registrar_asistencia'),
]