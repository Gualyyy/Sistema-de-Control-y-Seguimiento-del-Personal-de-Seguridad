from django.urls import path
from asignaciones import views as asignacion_view

urlpatterns = [
    # Asignación Equipos
    path('empleados_registrados/', asignacion_view.empleados_registrados, name='empleados_registrados'),
    path('equipos_registrados_supervisor/', asignacion_view.equipos_registrados_supervisor, name='equipos_registrados_supervisor'),
    path('asignar_equipo_usuario/', asignacion_view.asignar_equipo_usuario, name='asignar_equipo_usuario'),
   
    path('gestionar_asignaciones_equipos/', asignacion_view.gestionar_asignaciones_equipos, name='gestionar_asignaciones_equipos'),
    path('buscar_datos_asignacion_equipo/', asignacion_view.buscar_datos_asignacion_equipo, name='buscar_datos_asignacion_equipo'),
    path('datos_equipo_seleccionado/', asignacion_view.datos_equipo_seleccionado, name='datos_equipo_seleccionado'),
    path('devolucion_equipos_asignado/', asignacion_view.devolucion_equipos_asignado, name='devolucion_equipos_asignado'),

    path('buscar_equipo_devolver/', asignacion_view.buscar_equipo_devolver, name='buscar_equipo_devolver'),

    path('visualizar_asignaciones_admin/', asignacion_view.visualizar_asignaciones_admin, name='visualizar_asignaciones_admin'),
    path('asignaciones_equipos_admin/', asignacion_view.asignaciones_equipos_admin, name='asignaciones_equipos_admin'),
    path('datos_asignacion_admin/', asignacion_view.datos_asignacion_admin, name='datos_asignacion_admin'),
    
    path('lista_asignaciones_pdf_admin/', asignacion_view.lista_asignaciones_pdf_admin, name='lista_asignaciones_pdf_admin'),
    path('detalle_asignacion_pdf_admin/', asignacion_view.detalle_asignacion_pdf_admin, name='detalle_asignacion_pdf_admin'),

    path('lista_asignaciones_pdf/', asignacion_view.lista_asignaciones_pdf, name='lista_asignaciones_pdf'),
    path('datos_asignacion_pdf/', asignacion_view.datos_asignacion_pdf, name='datos_asignacion_pdf'),

    # Entrega Equipos
    path('registrar_entrega_equipos/', asignacion_view.registrar_entrega_equipos, name='registrar_entrega_equipos'),

    path('entregas_equipos_registradas/', asignacion_view.entregas_equipos_registradas, name='entregas_equipos_registradas'),
    path('busca_entrega_equipos/', asignacion_view.busca_entrega_equipos, name='busca_entrega_equipos'),
    
    path('equipos_entregados/', asignacion_view.equipos_entregados, name='equipos_entregados'),
    path('supervisores_entregado_equipos/', asignacion_view.supervisores_entregado_equipos, name='supervisores_entregado_equipos'),
    path('categorias_equipos_entregados/', asignacion_view.categorias_equipos_entregados, name='categorias_equipos_entregados'),
    path('correccion_entrega_equipos/', asignacion_view.correccion_entrega_equipos, name='correccion_entrega_equipos'),
    
    path('visualizar_entrega_equipos/', asignacion_view.visualizar_entrega_equipos, name='visualizar_entrega_equipos'),

    path('lista_entrega_equipos_pdf/', asignacion_view.lista_entrega_equipos_pdf, name='lista_entrega_equipos_pdf'),
    path('datos_entrega_equipo_pdf/', asignacion_view.datos_entrega_equipo_pdf, name='datos_entrega_equipo_pdf'),

    # Registrar Equipos
    path('categoria_registrados/', asignacion_view.categoria_registrados, name='categoria_registrados'),
    path('registros_equipos/', asignacion_view.registros_equipos, name='registros_equipos'),

    # Actualizar Equipos
    path('buscar_equipos/', asignacion_view.buscar_equipos, name='buscar_equipos'),
    path('actualizacion_equipos/', asignacion_view.actualizacion_equipos, name='actualizacion_equipos'),

    # Visualizar Equipos
    path('equipos_registrados/', asignacion_view.equipos_registrados, name='equipos_registrados'),
    path('visualizacion_equipos/', asignacion_view.visualizacion_equipos, name='visualizacion_equipos'),

    path('lista_equipos_pdf/', asignacion_view.lista_equipos_pdf, name='lista_equipos_pdf'),
    path('datos_equipos_pdf/', asignacion_view.datos_equipos_pdf, name='datos_equipos_pdf'),

    # Entrega Equipos
    path('categoria_equipo_recibido/', asignacion_view.categoria_equipo_recibido, name='categoria_equipo_recibido'),
    
    path('visualizar_equipos_supervisor/', asignacion_view.visualizar_equipos_supervisor, name='visualizar_equipos_supervisor'),
    
    path('datos_equipo_recibido/', asignacion_view.datos_equipo_recibido, name='datos_equipo_recibido'),
    
    path('lista_equipos_recibido_pdf/', asignacion_view.lista_equipos_recibido_pdf, name='lista_equipos_recibido_pdf'),
    path('datos_equipo_recibido_pdf/', asignacion_view.datos_equipo_recibido_pdf, name='datos_equipo_recibido_pdf'),
    
]