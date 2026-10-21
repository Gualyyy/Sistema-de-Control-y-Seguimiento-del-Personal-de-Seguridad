from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.views.decorators.cache import never_cache

from inicio_sesion.models import sesiones_usuario, bitacora, supervisores_encargados, personal_limpieza, despachadores, vigilantes
from asignaciones.models import categoria_equipo, equipos, entrega_equipos, asignacion_equipo
from incidencias.models import incidencia, tipo_incidencia, vigilante_incidencia

from inicio_sesion.views.autenticacion import validar_token_panel, crear_token_panel

# USUARIOS PANEL

def pagina_error_404(request, exception=None, **kwargs):
    return render(request, "inicio_sesion/404.html", { "es_404": True }, status=404)

@never_cache
def panel_usuario(request):

    if not request.session.get("usuario"):
        return redirect("inicio_sesion")

    token = request.session.get("panel_token")

    if not token or not validar_token_panel(token):
        token = crear_token_panel()

        request.session["panel_token"] = token
        request.session.save()

    return redirect(
        "panel_usuario_token",
        token=token
    )

@never_cache
def panel_usuario_token(request, token):

    if not request.session.get("usuario"):
        return redirect("inicio_sesion")

    session_token = request.session.get("panel_token")

    if (
        not session_token
        or token != session_token
        or not validar_token_panel(token)
    ):
        return redirect("inicio_sesion")

    response = render(
        request,
        "Panel/panel_usuario.html"
    )

    response["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response

# ESTADISTICAS DEL ENCARGADO ADMINISTRATIVO

def registros_sistema(request):
    total_supervisores = supervisores_encargados.objects.count()
    total_limpieza = personal_limpieza.objects.count()
    total_despachadores = despachadores.objects.count()
    total_vigilantes = vigilantes.objects.count()

    total_empleados = (
        total_supervisores
        + total_limpieza
        + total_despachadores
        + total_vigilantes
    )

    total_equipos = equipos.objects.count()

    total_incidencias = incidencia.objects.count()

    total_entregas = entrega_equipos.objects.count()

    return JsonResponse({
        "estado": "exito",
        "total_empleados": total_empleados,
        "total_equipos": total_equipos,
        "total_incidencias": total_incidencias,
        "total_entregas": total_entregas,
    })

def empleados_administrador(request):
    total_supervisores = supervisores_encargados.objects.count()
    total_limpieza = personal_limpieza.objects.count()
    total_despachadores = despachadores.objects.count()
    total_vigilantes = vigilantes.objects.count()

    total_empleados = (
        total_supervisores
        + total_limpieza
        + total_despachadores
        + total_vigilantes
    )

    return JsonResponse({
        "estado": "exito",
        "total_empleados": total_empleados,
        "total_supervisores": total_supervisores,
        "total_limpieza": total_limpieza,
        "total_despachadores": total_despachadores,
        "total_vigilantes": total_vigilantes,
    })
    
def bitacora_sistema(request):
    acciones_por_fecha = (
        bitacora.objects
        .annotate(fecha=TruncDate("fecha_hora"))
        .values("fecha")
        .annotate(total=Count("id_bitacora"))
        .order_by("fecha")
    )

    registros = [
        {
            "fecha": registro["fecha"].strftime("%d/%m/%Y"),
            "total": registro["total"]
        }
        for registro in acciones_por_fecha
    ]

    return JsonResponse({
        "estado": "exito",
        "acciones_por_fecha": registros
    })

def registro_equipo_categoria(request):
    categorias = (
        categoria_equipo.objects
        .annotate(total_equipos=Count("equipos__id_equipo"))
        .order_by("nombre")
    )

    registros = [
        {
            "categoria": categoria.nombre,
            "total": categoria.total_equipos
        }
        for categoria in categorias
    ]

    return JsonResponse({
        "estado": "exito",
        "categorias": registros
    })

def obtener_info_dispositivo(user_agent):
    user_agent = user_agent or ""

    # Sistema operativo
    if "Windows NT 10.0" in user_agent:
        sistema = "Windows 10/11"
    elif "Windows NT 6.3" in user_agent:
        sistema = "Windows 8.1"
    elif "Windows NT 6.1" in user_agent:
        sistema = "Windows 7"
    elif "Mac OS X" in user_agent:
        sistema = "macOS"
    elif "Android" in user_agent:
        sistema = "Android"
    elif "iPhone" in user_agent:
        sistema = "iOS"
    elif "iPad" in user_agent:
        sistema = "iPadOS"
    elif "Linux" in user_agent:
        sistema = "Linux"
    else:
        sistema = "Desconocido"

    # Navegador
    if "Edg/" in user_agent:
        navegador = "Microsoft Edge"
        version = user_agent.split("Edg/")[1].split(" ")[0]

    elif "OPR/" in user_agent:
        navegador = "Opera"
        version = user_agent.split("OPR/")[1].split(" ")[0]

    elif "Chrome/" in user_agent:
        navegador = "Google Chrome"
        version = user_agent.split("Chrome/")[1].split(" ")[0]

    elif "Firefox/" in user_agent:
        navegador = "Mozilla Firefox"
        version = user_agent.split("Firefox/")[1].split(" ")[0]

    elif "Safari/" in user_agent and "Chrome/" not in user_agent:
        navegador = "Safari"
        version = user_agent.split("Version/")[1].split(" ")[0]

    else:
        navegador = "Navegador desconocido"
        version = ""

    # Tipo de dispositivo
    if "Mobile" in user_agent or "Android" in user_agent:
        dispositivo = "Móvil"
    elif "iPad" in user_agent or "Tablet" in user_agent:
        dispositivo = "Tableta"
    else:
        dispositivo = "Computadora"

    return {
        "dispositivo": dispositivo,
        "sistema": sistema,
        "navegador": navegador,
        "version": version,
    }

# ESTADISTICAS DE LOS SUPERVISORES ENCARGADOS

def registro_sistema_supervisor(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar los registros."
        }, status=401)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula,
        vigencia=True
    ).select_related("id_turno").first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado vigente."
        }, status=404)

    turno = supervisor.id_turno

    total_limpieza = personal_limpieza.objects.filter(
        id_turno=turno,
        vigencia=True
    ).count()

    total_despachadores = despachadores.objects.filter(
        id_turno=turno,
        vigencia=True
    ).count()

    total_vigilantes = vigilantes.objects.filter(
        id_turno=turno,
        vigencia=True
    ).count()

    total_empleados = (
        + total_limpieza
        + total_despachadores
        + total_vigilantes
    )

    entregas = entrega_equipos.objects.filter(
        supervisor_encargado=supervisor,
        supervisor_encargado__id_turno=turno
    )

    total_equipos = entregas.aggregate(
        total=Sum("cantidad_entregada")
    )["total"] or 0

    total_incidencias = incidencia.objects.filter(
        id_supervisor=supervisor,
        id_turno=turno
    ).count()

    total_entregas = entregas.count()

    return JsonResponse({
        "estado": "exito",
        "title": "Registros del supervisor",
        "icon": "success",
        "descripcion": "Registros obtenidos correctamente.",
        "turno": str(turno),
        "total_empleados": total_empleados,
        "total_equipos": total_equipos,
        "total_incidencias": total_incidencias,
        "total_entregas": total_entregas
    })

def empleados_supervisor_turno(request):
    cedula = request.session.get("cedula_identidad")
    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar los empleados."
        }, status=401)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula,
        vigencia=True
    ).select_related("id_turno").first()
    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado vigente."
        }, status=404)

    turno = supervisor.id_turno

    cantidad_limpieza = personal_limpieza.objects.filter(
        id_turno=turno,
        vigencia=True
    ).count()

    cantidad_despachadores = despachadores.objects.filter(
        id_turno=turno,
        vigencia=True
    ).count()

    cantidad_vigilantes = vigilantes.objects.filter(
        id_turno=turno,
        vigencia=True
    ).count()

    total_empleados = (
        cantidad_limpieza
        + cantidad_despachadores
        + cantidad_vigilantes
    )

    return JsonResponse({
        "estado": "exito",
        "title": "Empleados del turno",
        "icon": "success",
        "descripcion": "Cantidad de empleados obtenida correctamente.",
        "turno": str(turno),
        "cantidad_limpieza": cantidad_limpieza,
        "cantidad_despachadores": cantidad_despachadores,
        "cantidad_vigilantes": cantidad_vigilantes,
        "total_empleados": total_empleados
    })

def equipos_entregados_supervisores(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar los equipos."
        }, status=401)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula,
        vigencia=True
    ).select_related("id_turno").first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado vigente."
        }, status=404)

    equipos_entregados = entrega_equipos.objects.filter(
        supervisor_encargado=supervisor,
        supervisor_encargado__id_turno=supervisor.id_turno,
        estado="ASIGNADO"
    )

    equipos_por_categoria = (
        equipos_entregados
        .values(
            "id_equipo__id_categoria",
            "id_equipo__id_categoria__nombre"
        )
        .annotate(
            cantidad_registros=Count("id_entrega"),
            cantidad_equipos=Sum("cantidad_entregada")
        )
        .order_by("id_equipo__id_categoria__nombre")
    )

    cantidad_registros = equipos_entregados.count()

    cantidad_equipos = equipos_entregados.aggregate(
        total=Sum("cantidad_entregada")
    )["total"] or 0

    return JsonResponse({
        "estado": "exito",
        "title": "Equipos entregados por categoría",
        "icon": "success",
        "descripcion": "Cantidad de equipos obtenida correctamente.",
        "turno": str(supervisor.id_turno),
        "cantidad_registros": cantidad_registros,
        "cantidad_equipos": cantidad_equipos,
        "categorias": [
            {
                "id_categoria": categoria["id_equipo__id_categoria"],
                "nombre": categoria["id_equipo__id_categoria__nombre"],
                "cantidad_registros": categoria["cantidad_registros"],
                "cantidad_equipos": categoria["cantidad_equipos"] or 0
            }
            for categoria in equipos_por_categoria
        ]
    })

def incidencias_ocurridos_supervisor(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar las incidencias."
        }, status=401)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula,
        vigencia=True
    ).select_related("id_turno").first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado vigente."
        }, status=404)

    incidencias_por_tipo = (
        tipo_incidencia.objects
        .annotate(
            cantidad=Count(
                "incidencias",
                filter=Q(
                    incidencias__id_supervisor=supervisor,
                    incidencias__id_turno=supervisor.id_turno
                )
            )
        )
        .order_by("nombre")
    )

    datos_incidencias = [
        {
            "id_tipo": tipo.id_tipo,
            "nombre": tipo.nombre,
            "cantidad": tipo.cantidad
        }
        for tipo in incidencias_por_tipo
    ]

    total_incidencias = sum(
        tipo["cantidad"]
        for tipo in datos_incidencias
    )

    return JsonResponse({
        "estado": "exito",
        "title": "Incidencias por tipo",
        "icon": "success",
        "descripcion": "Cantidad de incidencias obtenida correctamente.",
        "turno": str(supervisor.id_turno),
        "total_incidencias": total_incidencias,
        "incidencias_por_tipo": datos_incidencias
    })

def equipos_asignados_supervisor(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar los equipos."
        }, status=401)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula,
        vigencia=True
    ).select_related("id_turno").first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado vigente."
        }, status=404)

    asignaciones = asignacion_equipo.objects.filter(
        id_entrega__supervisor_encargado=supervisor,
        id_entrega__supervisor_encargado__id_turno=supervisor.id_turno
    ).exclude(
        estado="FINALIZADO"
    )

    equipos_por_categoria = (
        asignaciones
        .values(
            "id_entrega__id_equipo__id_categoria",
            "id_entrega__id_equipo__id_categoria__nombre"
        )
        .annotate(
            cantidad_asignada=Sum("cantidad_asignada"),
            cantidad_devuelta=Sum("cantidad_devuelta")
        )
        .order_by("id_entrega__id_equipo__id_categoria__nombre")
    )

    categorias = [
        {
            "id_categoria": registro[
                "id_entrega__id_equipo__id_categoria"
            ],
            "categoria": registro[
                "id_entrega__id_equipo__id_categoria__nombre"
            ],
            "cantidad_asignada": registro["cantidad_asignada"] or 0,
            "cantidad_devuelta": registro["cantidad_devuelta"] or 0,
            "cantidad_en_posesion": (
                (registro["cantidad_asignada"] or 0)
                - (registro["cantidad_devuelta"] or 0)
            )
        }
        for registro in equipos_por_categoria
    ]

    return JsonResponse({
        "estado": "exito",
        "title": "Equipos asignados por categoría",
        "icon": "success",
        "descripcion": "Cantidad de equipos obtenida correctamente.",
        "turno": str(supervisor.id_turno),
        "categorias": categorias
    })

# NOTIFICACIÓN DE SEGURIDAD

def ultimo_inicio_sesion(request):
    cedula = request.session.get("cedula_identidad")

    sesion_actual = request.session.session_key

    sesion = (
        sesiones_usuario.objects
        .filter(usuario__cedula_identidad=cedula)
        .exclude(session_key=sesion_actual)
        .order_by("-fecha_inicio")
        .first()
    )

    if not sesion:
        return JsonResponse({
            "estado": True,
            "sesion": None
        })

    dispositivo = obtener_info_dispositivo(
        sesion.info_general
    )

    return JsonResponse({
        "estado": True,
        "sesion": {
            "id_sesion": sesion.id_sesion,
            "fecha_inicio": sesion.fecha_inicio,
            "fecha_fin": sesion.fecha_fin,
            "activa": sesion.activa,
            "direccion_ip": sesion.direccion_ip,
            "dispositivo": dispositivo,
        }
    })
