from django.urls import path
from inicio_sesion import views as inicio_view
from asignaciones import views as asignacion_view

urlpatterns = [
    path('empleados_registrados/', inicio_view.autenticado_required(asignacion_view.empleados_registrados), name='empleados_registrados'),
    path('equipos_registrados/', inicio_view.autenticado_required(asignacion_view.equipos_registrados), name='equipos_registrados'),
    path('perfiles_asignados/', inicio_view.autenticado_required(asignacion_view.perfiles_asignados), name='perfiles_asignados'),
    path('asignar_equipo_usuario/', inicio_view.autenticado_required(asignacion_view.asignar_equipo_usuario), name='asignar_equipo_usuario'),

    path('visualizar_asignacion_equipo/', inicio_view.autenticado_required(asignacion_view.visualizar_asignacion_equipo), name='visualizar_asignacion_equipo'),
    path('buscar_datos_asignacion_equipo/', inicio_view.autenticado_required(asignacion_view.buscar_datos_asignacion_equipo), name='buscar_datos_asignacion_equipo'),
    path('equipos_asignado_usuario/', inicio_view.autenticado_required(asignacion_view.equipos_asignado_usuario), name='equipos_asignado_usuario'),
    path('datos_equipo_seleccionado/', inicio_view.autenticado_required(asignacion_view.datos_equipo_seleccionado), name='datos_equipo_seleccionado'),
    path('devolucion_equipos_asignado/', inicio_view.autenticado_required(asignacion_view.devolucion_equipos_asignado), name='devolucion_equipos_asignado'),

    path('buscar_equipo_devolver/', inicio_view.autenticado_required(asignacion_view.buscar_equipo_devolver), name='buscar_equipo_devolver'),

    path('visualizar_devoluciones/', inicio_view.autenticado_required(asignacion_view.visualizar_devoluciones), name='visualizar_devoluciones'),
    path('fechas_historial_devolucion/', inicio_view.autenticado_required(asignacion_view.fechas_historial_devolucion), name='fechas_historial_devolucion'),
    path('perfil_historial_devolucion/', inicio_view.autenticado_required(asignacion_view.perfil_historial_devolucion), name='perfil_historial_devolucion'),

    path('lista_historial_devolucion_pdf/', inicio_view.autenticado_required(asignacion_view.lista_historial_devolucion_pdf), name='lista_historial_devolucion_pdf'),

    path('bloqueo_empleado/', inicio_view.autenticado_required(inicio_view.bloqueo_empleado), name='bloqueo_empleado'),

    path('lista_asignaciones_pdf/', inicio_view.autenticado_required(asignacion_view.lista_asignaciones_pdf), name='lista_asignaciones_pdf'),
    path('datos_asignacion_pdf/', inicio_view.autenticado_required(asignacion_view.datos_asignacion_pdf), name='datos_asignacion_pdf'),
]