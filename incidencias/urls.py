from django.urls import path
from incidencias import views as incidencia_view

urlpatterns = [
    path('tipos_incidencias/', incidencia_view.tipos_incidencias, name='tipos_incidencias'),
    path('fechas_incidencias/', incidencia_view.fechas_incidencias, name='fechas_incidencias'),
    path('vigilantes_registrados/', incidencia_view.vigilantes_registrados, name='vigilantes_registrados'),

    path('incidencias_vigilante/', incidencia_view.incidencias_vigilante, name='incidencias_vigilante'),
    path('gestionar_incidencias/', incidencia_view.gestionar_incidencias, name='gestionar_incidencias'),
    path('registrar_incidencias/', incidencia_view.registrar_incidencias, name='registrar_incidencias'),

    path('buscar_datos_incidencia/', incidencia_view.buscar_datos_incidencia, name='buscar_datos_incidencia'),
    path('modificar_datos_incidencia/', incidencia_view.modificar_datos_incidencia, name='modificar_datos_incidencia'),
    
    path('gestion_incidencia_administrativo/', incidencia_view.gestion_incidencia_administrativo, name='gestion_incidencia_administrativo'),
    path('incidencias_recibidos_vigilantes/', incidencia_view.incidencias_recibidos_vigilantes, name='incidencias_recibidos_vigilantes'),
    path('buscar_incidencia/', incidencia_view.buscar_incidencia, name='buscar_incidencia'),

    path('lista_incidencias_pdf/', incidencia_view.lista_incidencias_pdf, name='lista_incidencias_pdf'),
    path('lista_incidencias_admin_pdf/', incidencia_view.lista_incidencias_admin_pdf, name='lista_incidencias_admin_pdf'),
]