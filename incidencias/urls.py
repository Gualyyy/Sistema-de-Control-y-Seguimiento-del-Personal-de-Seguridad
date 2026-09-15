from django.urls import path
from inicio_sesion import views as inicio_view
from incidencias import views as incidencia_view

urlpatterns = [
    path('tipos_incidencias/', inicio_view.autenticado_required(incidencia_view.tipos_incidencias), name='tipos_incidencias'),
    path('fechas_incidencias/', inicio_view.autenticado_required(incidencia_view.fechas_incidencias), name='fechas_incidencias'),

    path('incidencias_vigilante/', inicio_view.autenticado_required(incidencia_view.incidencias_vigilante), name='incidencias_vigilante'),
    path('gestionar_incidencias/', inicio_view.autenticado_required(incidencia_view.gestionar_incidencias), name='gestionar_incidencias'),
    path('registrar_incidencias/', inicio_view.autenticado_required(incidencia_view.registrar_incidencias), name='registrar_incidencias'),

    path('buscar_datos_incidencia/', inicio_view.autenticado_required(incidencia_view.buscar_datos_incidencia), name='buscar_datos_incidencia'),
    path('modificar_datos_incidencia/', inicio_view.autenticado_required(incidencia_view.modificar_datos_incidencia), name='modificar_datos_incidencia'),
    
    path('gestion_incidencia_admin/', inicio_view.autenticado_required(incidencia_view.gestion_incidencia_admin), name='gestion_incidencia_admin'),
    path('incidencias_recibidos_vigilantes/', inicio_view.autenticado_required(incidencia_view.incidencias_recibidos_vigilantes), name='incidencias_recibidos_vigilantes'),
    path('buscar_incidencia/', inicio_view.autenticado_required(incidencia_view.buscar_incidencia), name='buscar_incidencia'),
    path('registrar_solucion/', inicio_view.autenticado_required(incidencia_view.registrar_solucion), name='registrar_solucion'),

    path('historial_soluciones_admin/', inicio_view.autenticado_required(incidencia_view.historial_soluciones_admin), name='historial_soluciones_admin'),
    path('historial_soluciones/', inicio_view.autenticado_required(incidencia_view.historial_soluciones), name='historial_soluciones'),

    path('lista_incidencias_pdf/', inicio_view.autenticado_required(incidencia_view.lista_incidencias_pdf), name='lista_incidencias_pdf'),
    path('detalle_incidencia_pdf/', inicio_view.autenticado_required(incidencia_view.detalle_incidencia_pdf), name='detalle_incidencia_pdf'),
]