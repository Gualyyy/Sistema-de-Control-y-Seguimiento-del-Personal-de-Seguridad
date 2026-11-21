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
    path('cerrar_sesion/', views.cerrar_sesion, name='cerrar_sesion'),   

    path('inicio_sesion/', views.inicio_sesion, name='inicio_sesion'),
    path('menu_acceso/', views.menu_acceso, name='menu_acceso'),
    
    path('registrar_credenciales/', views.registrar_credenciales, name='registrar_credenciales'),
    path('validar_patron_contrasenia/', views.validar_patron_contrasenia, name='validar_patron_contrasenia'),
    path('empleado_sin_credenciales/', views.empleado_sin_credenciales, name='empleado_sin_credenciales'),

    path('enviar_codigo/', views.enviar_codigo, name='enviar_codigo'),
    path('reenviar_codigo/', views.reenviar_codigo, name='reenviar_codigo'),
    path('vigencia_codigo/', views.vigencia_codigo, name='vigencia_codigo'),
    path('enviar_usuario/', views.enviar_usuario, name='enviar_usuario'),
    
    path('buscar_usuario/', views.buscar_usuario, name='buscar_usuario'),
    path('correos_usuario/', views.correos_usuario, name='correos_usuario'),
    path('verificar_codigo/', views.verificar_codigo, name='verificar_codigo'),
    path('menu_recuperar_credenciales/', views.menu_recuperar_credenciales, name='menu_recuperar_credenciales'),
    path('cambiar_contrasenia/', views.cambiar_contrasenia, name='cambiar_contrasenia'),
    path('recuperar_nombre_usuario/', views.recuperar_nombre_usuario, name='recuperar_nombre_usuario'),
    
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
    path('perfiles_sin_turno_registrados/', views.perfiles_sin_turno_registrados, name='perfiles_sin_turno_registrados'),
    path('perfiles_disponibles_registro/', views.perfiles_disponibles_registro, name='perfiles_disponibles_registro'),
    
    path('turnos_registrados/', views.turnos_registrados, name='turnos_registrados'),

    path('completar_registro/', views.completar_registro, name='completar_registro'),
    path('buscar_datos_pre_registrado/', views.buscar_datos_pre_registrado, name='buscar_datos_pre_registrado'),

    # Actualizar Empleados
    path('buscar_datos_usuario/', views.buscar_datos_usuario, name='buscar_datos_usuario'),
    path('actualizacion_datos_usuarios/', views.actualizacion_datos_usuarios, name='actualizacion_datos_usuarios'),

    # Visualizar Empleados
    path('datos_empleado/', views.datos_empleado, name='datos_empleado'),
    path('visualizar_empleados/', views.visualizar_empleados, name='visualizar_empleados'),
    path('visualizacion_datos_usuarios/', views.visualizacion_datos_usuarios, name='visualizacion_datos_usuarios'), 

    # Visualizar Empleado de acuerdo del turno del Supervisor
    path('visualizar_empleado_supervisor/', views.visualizar_empleado_supervisor, name='visualizar_empleado_supervisor'), 
    path('lista_empleado_supervisor_pdf/', views.lista_empleado_supervisor_pdf, name='lista_empleado_supervisor_pdf'),
    
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
    path('lista_gastos_pdf/', views.lista_gastos_pdf, name='lista_gastos_pdf'),
    path(
        'datos_encargado_administrativo_pdf/',
        views.datos_encargado_administrativo_pdf,
        name='datos_encargado_administrativo_pdf'
    ),
    path('lista_clientes_pdf/', views.lista_clientes_pdf, name='lista_clientes_pdf'),

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
    
    path('actualizar_img_perfil/', views.actualizar_img_perfil, name='actualizar_img_perfil'),
    path('img_perfil_almacenado/', views.img_perfil_almacenado, name='img_perfil_almacenado'),
    
    path('datos_contacto_foro/', views.datos_contacto_foro, name='datos_contacto_foro'),
    path('reemplazar_contactos_foro/', views.reemplazar_contactos_foro, name='reemplazar_contactos_foro'),
    
    # Panel Usuario
    path('registros_sistema_propietario/', views.registros_sistema_propietario, name='registros_sistema_propietario'),
    path('registros_sistema/', views.registros_sistema, name='registros_sistema'),
    path('empleados_administrador/', views.empleados_administrador, name='empleados_administrador'),
    path('bitacora_sistema/', views.bitacora_sistema, name='bitacora_sistema'),
    path('registro_equipo_categoria/', views.registro_equipo_categoria, name='registro_equipo_categoria'),
    
    path('perfiles_sistema/', views.perfiles_sistema, name='perfiles_sistema'),
    path('incidencia_ocurridas/', views.incidencia_ocurridas, name='incidencia_ocurridas'),
    
    path('registro_sistema_atencion_cliente/', views.registro_sistema_atencion_cliente, name='registro_sistema_atencion_cliente'),
    path("evolucion_ventas/", views.evolucion_ventas, name="evolucion_ventas"),
    path("productos_mas_vendidos/", views.productos_mas_vendidos, name="productos_mas_vendidos"),
    
    path("registro_sistema_cliente/", views.registro_sistema_cliente, name="registro_sistema_cliente"),
    path("banco_pago_compra/", views.banco_pago_compra, name="banco_pago_compra"),
    path("productos_mas_comprados/", views.productos_mas_comprados, name="productos_mas_comprados"),

    path('registro_sistema_supervisor/', views.registro_sistema_supervisor, name='registro_sistema_supervisor'),
    path('empleados_supervisor_turno/', views.empleados_supervisor_turno, name='empleados_supervisor_turno'),
    path('equipos_entregados_supervisores/', views.equipos_entregados_supervisores, name='equipos_entregados_supervisores'),
    path('incidencias_ocurridos_supervisor/', views.incidencias_ocurridos_supervisor, name='incidencias_ocurridos_supervisor'),
    path('equipos_asignados_supervisor/', views.equipos_asignados_supervisor, name='equipos_asignados_supervisor'),
    
    path('ultimo_inicio_sesion/', views.ultimo_inicio_sesion, name='ultimo_inicio_sesion'),

    # Clientes
    path('validar_identificador/', views.validar_identificador, name='validar_identificador'),
    
    path('registrar_clientes_foro/', views.registrar_clientes_foro, name='registrar_clientes_foro'),

    path('buscar_datos_cliente/', views.buscar_datos_cliente, name='buscar_datos_cliente'),
    path('actualizar_clientes_ventas/', views.actualizar_clientes_ventas, name='actualizar_clientes_ventas'),
    
    path('visualizar_clientes_ventas/', views.visualizar_clientes_ventas, name='visualizar_clientes_ventas'),
    path('clientes_registrados_ventas/', views.clientes_registrados_ventas, name='clientes_registrados_ventas'),
    path('detalle_registro_cliente/', views.detalle_registro_cliente, name='detalle_registro_cliente'),
    path('bloqueo_cliente/', views.bloqueo_cliente, name='bloqueo_cliente'),
    
    path('clientes_registrados_pdf/', views.clientes_registrados_pdf, name='clientes_registrados_pdf'),
    path('detalle_cliente_pdf/', views.detalle_cliente_pdf, name='detalle_cliente_pdf'),

    # Encargado Administrativo
    path('existe_administrador/', views.existe_administrador, name='existe_administrador'), 
    path('registrar_administrador/', views.registrar_administrador, name='registrar_administrador'), 
    path('visualizar_administrador/', views.visualizar_administrador, name='visualizar_administrador'), 
    path('administrador_registrado/', views.administrador_registrado, name='administrador_registrado'), 
    path('gestionar_administrador/', views.gestionar_administrador, name='gestionar_administrador'), 
    path('datos_administrador/', views.datos_administrador, name='datos_administrador'), 
    path('actualizar_administrador/', views.actualizar_administrador, name='actualizar_administrador'),

    # Gastos realizado por la empresa
    path('categorias_gastos/', views.categorias_gastos, name='categorias_gastos'),
    path('registrar_gastos/', views.registrar_gastos, name='registrar_gastos'),
    path('gestion_gastos/', views.gestion_gastos, name='gestion_gastos'),
    path('visualizar_gastos/', views.visualizar_gastos, name='visualizar_gastos'),
    path('buscar_gasto/', views.buscar_gasto, name='buscar_gasto'),
    path('actualizar_datos_gasto/', views.actualizar_datos_gasto, name='actualizar_datos_gasto'), 
    
    # Reportes PDF
    path('validar_reporte_qr/', views.verificar_reporte_qr, name='verificar_reporte_qr'),
    path('reporte_sistema_administrador/', views.reporte_sistema_administrador, name='reporte_sistema_administrador'),
    path('lista_incidencias_pdf/', views.lista_incidencias_pdf, name='lista_incidencias_pdf'),
    path('lista_equipos_pdf/', views.lista_equipos_pdf, name='lista_equipos_pdf'), 
    path('lista_empleados_pdf/', views.lista_empleados_pdf, name='lista_empleados_pdf'),
    path('datos_empleados_pdf/', views.datos_empleados_pdf, name='datos_empleados_pdf'),
    path('lista_entrega_equipos_pdf/', views.lista_entrega_equipos_pdf, name='lista_entrega_equipos_pdf'),
    path('lista_asignaciones_pdf_admin/', views.lista_asignaciones_pdf_admin, name='lista_asignaciones_pdf_admin'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )