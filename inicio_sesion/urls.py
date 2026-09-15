from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_sesion, name='inicio_sesion'),
    path('cerrar_sesion/', views.autenticado_required(views.cerrar_sesion), name='cerrar_sesion'),
    
    path('registro_usuarios/', views.autenticado_required(views.registro_usuarios), name='registro_usuarios'),
    path('buscar_datos_pre_registrado/', views.autenticado_required(views.buscar_datos_pre_registrado), name='buscar_datos_pre_registrado'),
    path('completar_registro/', views.autenticado_required(views.completar_registro), name='completar_registro'),
    path('buscar_datos_usuario/', views.autenticado_required(views.buscar_datos_usuario), name='buscar_datos_usuario'),
    path('actualizacion_datos_usuarios/', views.autenticado_required(views.actualizacion_datos_usuarios), name='actualizacion_datos_usuarios'),
    path('visualizar_empleados/', views.autenticado_required(views.visualizar_empleados), name='visualizar_empleados'),
    path('visualizacion_datos_usuarios/', views.autenticado_required(views.visualizacion_datos_usuarios), name='visualizacion_datos_usuarios'),
    path('perfiles_disponibles/', views.autenticado_required(views.perfiles_disponibles), name='perfiles_disponibles'),
    path('turnos_registrados/', views.autenticado_required(views.turnos_registrados), name='turnos_registrados'),
    path('perfiles_registrados/', views.autenticado_required(views.perfiles_registrados), name='perfiles_registrados'),

    path('perfiles_usuario_no_registrados/', views.autenticado_required(views.perfiles_usuario_no_registrados), name='perfiles_usuario_no_registrados'),
    path('cantidad_perfiles_asignado/', views.autenticado_required(views.cantidad_perfiles_asignado), name='cantidad_perfiles_asignado'),
    path('buscar_datos_asignacion/', views.autenticado_required(views.buscar_datos_asignacion), name='buscar_datos_asignacion'),
    path('gestionar_perfiles_empleado/', views.autenticado_required(views.gestionar_perfiles_empleado), name='gestionar_perfiles_empleado'),
    path('registrar_nueva_asignacion/', views.autenticado_required(views.registrar_nueva_asignacion), name='registrar_nueva_asignacion'),
    path('actualizar_vigencia_perfil/', views.autenticado_required(views.actualizar_vigencia_perfil), name='actualizar_vigencia_perfil'),
    path('cargar_perfiles_asignados/', views.autenticado_required(views.cargar_perfiles_asignados), name='cargar_perfiles_asignados'),
    path('buscar_datos_perfil/', views.autenticado_required(views.buscar_datos_perfil), name='buscar_datos_perfil'),

    path('fechas_historial_asignaciones/', views.autenticado_required(views.fechas_historial_asignaciones), name='fechas_historial_asignaciones'),
    path('historial_perfiles/', views.autenticado_required(views.historial_perfiles), name='historial_perfiles'),

    path('categoria_registrados/', views.autenticado_required(views.categoria_registrados), name='categoria_registrados'),
    path('registros_equipos/', views.autenticado_required(views.registros_equipos), name='registros_equipos'),
    path('buscar_equipos/', views.autenticado_required(views.buscar_equipos), name='buscar_equipos'),
    path('visualizacion_equipos/', views.autenticado_required(views.visualizacion_equipos), name='visualizacion_equipos'),
    path('actualizacion_equipos/', views.autenticado_required(views.actualizacion_equipos), name='actualizacion_equipos'),

    path('panel_usuario/', views.autenticado_required(views.panel_usuario), name='panel_usuario'),
    path('panel/<str:token>/', views.autenticado_required(views.panel_usuario_token), name='panel_usuario_token'),

    path('empleados_registrados/', views.autenticado_required(views.empleados_registrados), name='empleados_registrados'),
    path('ultimo_inicio_sesion/', views.autenticado_required(views.ultimo_inicio_sesion), name='ultimo_inicio_sesion'),

    path('bitacora_registradas/', views.autenticado_required(views.bitacora_registradas), name='bitacora_registradas'),
    path('visualizar_bitacora/', views.autenticado_required(views.visualizar_bitacora), name='visualizar_bitacora'),

    path('visualizar_inicio_sesion/', views.autenticado_required(views.visualizar_inicio_sesion), name='visualizar_inicio_sesion'),
    path('inicios_sesiones_registradas/', views.autenticado_required(views.inicios_sesiones_registradas), name='inicios_sesiones_registradas'),
    path('fechas_inicios_sesiones/', views.autenticado_required(views.fechas_inicios_sesiones), name='fechas_inicios_sesiones'),

    path('visualizar_intentos_sesion/', views.autenticado_required(views.visualizar_intentos_sesion), name='visualizar_intentos_sesion'),
    path('fechas_intentos_registrados/', views.autenticado_required(views.fechas_intentos_registrados), name='fechas_intentos_registrados'),
    path('intentos_registrados/', views.autenticado_required(views.intentos_registrados), name='intentos_registrados'),

    path('empleado_perfil/', views.autenticado_required(views.empleado_perfil), name='empleado_perfil'),
    path('empleado_perfil_pdf/', views.autenticado_required(views.empleado_perfil_pdf), name='empleado_perfil_pdf'),
 
    path('validar_email/', views.autenticado_required(views.validar_email), name='validar_email'),
    path('validar_nombre_usuario/', views.autenticado_required(views.validar_nombre_usuario), name='validar_nombre_usuario'),
    path('validar_contrasenia/', views.autenticado_required(views.validar_contrasenia), name='validar_contrasenia'),
    path('validar_ci/', views.autenticado_required(views.validar_ci), name='validar_ci'),

    path('lista_historial_perfiles_pdf/', views.autenticado_required(views.lista_historial_perfiles_pdf), name='lista_historial_perfiles_pdf'),

    path('lista_inicios_sesiones_pdf/', views.autenticado_required(views.lista_inicios_sesiones_pdf), name='lista_inicios_sesiones_pdf'),

    path('lista_intentos_sesion_pdf/', views.autenticado_required(views.lista_intentos_sesion_pdf), name='lista_intentos_sesion_pdf'),
   
    path('lista_empleados_pdf/', views.autenticado_required(views.lista_empleados_pdf), name='lista_empleados_pdf'),
    path('datos_empleados_pdf/', views.autenticado_required(views.datos_empleados_pdf), name='datos_empleados_pdf'),

    path('lista_equipos_pdf/', views.autenticado_required(views.lista_equipos_pdf), name='lista_equipos_pdf'),
    path('datos_equipos_pnf/', views.autenticado_required(views.datos_equipos_pnf), name='datos_equipos_pnf'),

    path('lista_bitacora_pdf/', views.autenticado_required(views.lista_bitacora_pdf), name='lista_bitacora_pdf'),
]


