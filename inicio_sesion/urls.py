from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Foro
    path('', views.foro, name='foro'),
    path('historia/', views.historia, name='historia'),
    path('quienes_somos/', views.quienes_somos, name='quienes_somos'),
    path('contactanos/', views.contactanos, name='contactanos'),
    path('inicio_sesion/', views.inicio_sesion, name='inicio_sesion'),
    path('cerrar_sesion/', views.cerrar_sesion, name='cerrar_sesion'),    
    path('modo_incognito/', views.modo_incognito, name='modo_incognito'),

    # Validaciones
    path('validar_email/', views.validar_email, name='validar_email'),
    path('validar_nombre_usuario/', views.validar_nombre_usuario, name='validar_nombre_usuario'),
    path('validar_contrasenia/', views.validar_contrasenia, name='validar_contrasenia'),
    path('validar_ci/', views.validar_ci, name='validar_ci'),
    path('validar_telefono/', views.validar_telefono, name='validar_telefono'),

    path('panel_usuario/', views.panel_usuario, name='panel_usuario'),
    path('panel/<str:token>/', views.panel_usuario_token, name='panel_usuario_token'),

    # Registrar Empleados
    path('registro_usuarios/', views.registro_usuarios, name='registro_usuarios'),
    path('perfiles_disponibles/', views.perfiles_disponibles, name='perfiles_disponibles'),
    path('turnos_registrados/', views.turnos_registrados, name='turnos_registrados'),

    path('completar_registro/', views.completar_registro, name='completar_registro'),
    path('buscar_datos_pre_registrado/', views.buscar_datos_pre_registrado, name='buscar_datos_pre_registrado'),

    # Actualizar Empleados
    path('buscar_datos_usuario/', views.buscar_datos_usuario, name='buscar_datos_usuario'),
    path('actualizacion_datos_usuarios/', views.actualizacion_datos_usuarios, name='actualizacion_datos_usuarios'),

    # Visualizar Empleados
    path('visualizar_empleados/', views.visualizar_empleados, name='visualizar_empleados'),
    path('visualizacion_datos_usuarios/', views.visualizacion_datos_usuarios, name='visualizacion_datos_usuarios'), 

    # Visualizar Empleado de acuerdo del turno del Supervisor
    path('visualizar_empleado_supervisor/', views.visualizar_empleado_supervisor, name='visualizar_empleado_supervisor'), 
    path('lista_empleado_supervisor_pdf/', views.lista_empleado_supervisor_pdf, name='lista_empleado_supervisor_pdf'),
    
    path('lista_empleados_pdf/', views.lista_empleados_pdf, name='lista_empleados_pdf'),
    path('datos_empleados_pdf/', views.datos_empleados_pdf, name='datos_empleados_pdf'),
    
    # Supervisores Registrados
    path('supervisores_registrados/', views.supervisores_registrados, name='supervisores_registrados'),
    path('credenciales_supervisor/', views.credenciales_supervisor, name='credenciales_supervisor'),
    path('actualizar_credenciales_supervisor/', views.actualizar_credenciales_supervisor, name='actualizar_credenciales_supervisor'),
    path('bloquear_supervisor/', views.bloquear_supervisor, name='bloquear_supervisor'),
    path('supervisores_generales/', views.supervisores_generales, name='supervisores_generales'),

    # Seguridad del Sistema
    
    # Datos para visualizar y realizar reportes
    path('bitacora_registradas/', views.bitacora_registradas, name='bitacora_registradas'),
    path('visualizar_bitacora/', views.visualizar_bitacora, name='visualizar_bitacora'),

    # Modulos para visualizar los datos
    path('visualizar_inicio_sesion/', views.visualizar_inicio_sesion, name='visualizar_inicio_sesion'),
    path('inicios_sesiones_registradas/', views.inicios_sesiones_registradas, name='inicios_sesiones_registradas'),
    path('fechas_inicios_sesiones/', views.fechas_inicios_sesiones, name='fechas_inicios_sesiones'),

    path('visualizar_intentos_sesion/', views.visualizar_intentos_sesion, name='visualizar_intentos_sesion'),
    path('fechas_intentos_registrados/', views.fechas_intentos_registrados, name='fechas_intentos_registrados'),
    path('intentos_registrados/', views.intentos_registrados, name='intentos_registrados'),

    # Generar reportes PDF
    path('lista_inicios_sesiones_pdf/', views.lista_inicios_sesiones_pdf, name='lista_inicios_sesiones_pdf'),
    path('lista_intentos_sesion_pdf/', views.lista_intentos_sesion_pdf, name='lista_intentos_sesion_pdf'), 
    path('lista_bitacora_pdf/', views.lista_bitacora_pdf, name='lista_bitacora_pdf'),

    # Gestión de Perfiles
    path('perfiles_disponibles/', views.perfiles_disponibles, name='perfiles_disponibles'),

    path('perfiles_usuario_no_registrados/', views.perfiles_usuario_no_registrados, name='perfiles_usuario_no_registrados'),
    path('cantidad_perfiles_asignado/', views.cantidad_perfiles_asignado, name='cantidad_perfiles_asignado'),
    path('buscar_datos_asignacion/', views.buscar_datos_asignacion, name='buscar_datos_asignacion'),
    path('gestionar_perfiles_empleado/', views.gestionar_perfiles_empleado, name='gestionar_perfiles_empleado'),
    path('registrar_nueva_asignacion/', views.registrar_nueva_asignacion, name='registrar_nueva_asignacion'),
    path('actualizar_vigencia_perfil/', views.actualizar_vigencia_perfil, name='actualizar_vigencia_perfil'),
    path('cargar_perfiles_asignados/', views.cargar_perfiles_asignados, name='cargar_perfiles_asignados'),
    path('buscar_datos_perfil/', views.buscar_datos_perfil, name='buscar_datos_perfil'),

    path('datos_usuario_sistema/', views.datos_usuario_sistema, name='datos_usuario_sistema'),
    path('actualizar_datos_sistema/', views.actualizar_datos_sistema, name='actualizar_datos_sistema'),
    
    # Panel Usuario
    path('registros_sistema/', views.registros_sistema, name='registros_sistema'),
    path('empleados_administrador/', views.empleados_administrador, name='empleados_administrador'),
    path('bitacora_sistema/', views.bitacora_sistema, name='bitacora_sistema'),
    path('registro_equipo_categoria/', views.registro_equipo_categoria, name='registro_equipo_categoria'),
    
    path('registro_sistema_supervisor/', views.registro_sistema_supervisor, name='registro_sistema_supervisor'),
    path('empleados_supervisor_turno/', views.empleados_supervisor_turno, name='empleados_supervisor_turno'),
    path('equipos_entregados_supervisores/', views.equipos_entregados_supervisores, name='equipos_entregados_supervisores'),
    path('incidencias_ocurridos_supervisor/', views.incidencias_ocurridos_supervisor, name='incidencias_ocurridos_supervisor'),
    path('equipos_asignados_supervisor/', views.equipos_asignados_supervisor, name='equipos_asignados_supervisor'),
    
    path('ultimo_inicio_sesion/', views.ultimo_inicio_sesion, name='ultimo_inicio_sesion'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )