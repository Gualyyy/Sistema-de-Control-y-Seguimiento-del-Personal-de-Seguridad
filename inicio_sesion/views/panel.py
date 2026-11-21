from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate, Coalesce, TruncMonth
from django.views.decorators.cache import never_cache
from django.utils import timezone

from decimal import Decimal, ROUND_HALF_UP
from django.db.models import DecimalField

from inicio_sesion.models import sesiones_usuario, bitacora, supervisores_encargados, personal_limpieza, despachadores, vigilantes, encargados_administrativos, atencion_cliente, cliente
from asignaciones.models import categoria_equipo, equipos, entrega_equipos, asignacion_equipo
from incidencias.models import incidencia, tipo_incidencia, vigilante_incidencia
from ventas.models import venta, pago, cuenta_destino_pago, producto, detalle_venta

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

# ESTADISTICAS DEL PROPIETARIO

def registros_sistema_propietario(request):
    total_supervisores = supervisores_encargados.objects.count()
    total_limpieza = personal_limpieza.objects.count()
    total_despachadores = despachadores.objects.count()
    total_vigilantes = vigilantes.objects.count()
    total_atencion_cliente = atencion_cliente.objects.count()
    total_administradores = encargados_administrativos.objects.count()

    total_empleados = (
        total_supervisores
        + total_limpieza
        + total_despachadores
        + total_vigilantes
        + total_atencion_cliente
        + total_administradores
    )

    total_equipos = equipos.objects.count()
    total_incidencias = incidencia.objects.count()
    total_entregas = entrega_equipos.objects.count()

    return JsonResponse({
        "estado": "exito",
        "total_empleados": total_empleados,
        "total_supervisores": total_supervisores,
        "total_limpieza": total_limpieza,
        "total_despachadores": total_despachadores,
        "total_vigilantes": total_vigilantes,
        "total_atencion_cliente": total_atencion_cliente,
        "total_administradores": total_administradores,
        "total_equipos": total_equipos,
        "total_incidencias": total_incidencias,
        "total_entregas": total_entregas,
    })

# ESTADISTICAS DEL ENCARGADO ADMINISTRATIVO

def registros_sistema(request):
    total_supervisores = supervisores_encargados.objects.count()
    total_limpieza = personal_limpieza.objects.count()
    total_despachadores = despachadores.objects.count()
    total_vigilantes = vigilantes.objects.count()
    total_atencion_cliente = atencion_cliente.objects.count()

    total_empleados = (
        total_supervisores
        + total_limpieza
        + total_despachadores
        + total_vigilantes
        + total_atencion_cliente
    )

    total_equipos = equipos.objects.count()
    total_incidencias = incidencia.objects.count()
    total_entregas = entrega_equipos.objects.count()

    return JsonResponse({
        "estado": "exito",
        "total_empleados": total_empleados,
        "total_supervisores": total_supervisores,
        "total_limpieza": total_limpieza,
        "total_despachadores": total_despachadores,
        "total_vigilantes": total_vigilantes,
        "total_atencion_cliente": total_atencion_cliente,
        "total_equipos": total_equipos,
        "total_incidencias": total_incidencias,
        "total_entregas": total_entregas,
    })

def empleados_administrador(request):
    total_supervisores = supervisores_encargados.objects.count()
    total_limpieza = personal_limpieza.objects.count()
    total_despachadores = despachadores.objects.count()
    total_vigilantes = vigilantes.objects.count()
    total_atencion_cliente = atencion_cliente.objects.count()

    total_clientes = cliente.objects.count()

    total_empleados = (
        total_supervisores
        + total_limpieza
        + total_despachadores
        + total_vigilantes
        + total_atencion_cliente
    )

    return JsonResponse({
        "estado": "exito",
        "total_empleados": total_empleados,
        "total_supervisores": total_supervisores,
        "total_limpieza": total_limpieza,
        "total_despachadores": total_despachadores,
        "total_vigilantes": total_vigilantes,
        "total_atencion_cliente": total_atencion_cliente,
        "total_clientes": total_clientes,
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

# ESTADISTICAS PROPIETARIO

def perfiles_sistema(request):
    perfiles = {
        "encargado_administrativo": encargados_administrativos.objects.filter(vigencia=True).count(),
        "cliente": cliente.objects.count(),
        "atencion_cliente": atencion_cliente.objects.filter(vigencia=True).count(),
        "supervisor_encargado": supervisores_encargados.objects.filter(vigencia=True).count(),
        "personal_limpieza": personal_limpieza.objects.filter(vigencia=True).count(),
        "despachador": despachadores.objects.filter(vigencia=True).count(),
        "vigilante": vigilantes.objects.filter(vigencia=True).count(),
    }

    return JsonResponse({
        "estado": "exito",
        "perfiles": perfiles
    })

def incidencia_ocurridas(request):
    incidencias = (
        incidencia.objects
        .annotate(fecha=TruncDate("fecha_hora"))
        .values("fecha")
        .annotate(cantidad=Count("id_incidencia"))
        .order_by("fecha")
    )

    datos = [
        {
            "fecha": registro["fecha"].strftime("%Y-%m-%d"),
            "cantidad": registro["cantidad"]
        }
        for registro in incidencias
    ]

    return JsonResponse({
        "estado": "exito",
        "incidencias": datos
    })

# DATOS DEL SISTEMA ATENCIÓN AL CLIENTE

def registro_sistema_atencion_cliente(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar los registros."
        }, status=401)
    
    total_clientes = cliente.objects.count()

    estadisticas_ventas = venta.objects.aggregate(
        total_ventas=Count("id_venta"),
        ventas_rechazadas=Count("id_venta", filter=Q(estado=venta.Estado.RECHAZADA)),
        ventas_en_espera=Count("id_venta", filter=Q(estado=venta.Estado.BORRADOR)),
        ventas_en_confirmacion=Count("id_venta", filter=Q(estado=venta.Estado.PENDIENTE_CONFIRMACION)),
        ventas_confirmadas=Count("id_venta", filter=Q(estado=venta.Estado.CONFIRMADA))
    )

    total_ventas_bolivares = venta.objects.filter(
        estado=venta.Estado.CONFIRMADA
    ).aggregate(
        total=Coalesce(
            Sum("total"),
            Decimal("0.00")
        )
    )["total"]

    ventas_confirmadas = venta.objects.filter(
        estado=venta.Estado.CONFIRMADA
    ).values_list(
        "total",
        "tasa_cambio"
    )

    total_ventas_dolares = Decimal("0.00")

    for monto_bolivares, tasa_cambio in ventas_confirmadas:

        if tasa_cambio and tasa_cambio > 0:
            total_ventas_dolares += monto_bolivares / tasa_cambio

    total_ventas_dolares = total_ventas_dolares.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    estadisticas_cuentas = cuenta_destino_pago.objects.aggregate(

        total_cuentas=Count("id_cuenta_destino"),

        total_pago_movil=Count(
            "id_cuenta_destino",
            filter=(
                Q(id_metodo_pago__nombre__icontains="móvil") |
                Q(id_metodo_pago__nombre__icontains="movil")
            )
        ),

        total_transferencias=Count(
            "id_cuenta_destino",
            filter=Q(
                id_metodo_pago__nombre__icontains="transferencia"
            )
        )
    )

    total_productos = producto.objects.count()

    return JsonResponse({

        "estado": "exito",
        "title": "Registros de atención al cliente",
        "icon": "success",
        "descripcion": "Registros obtenidos correctamente.",

        # Clientes
        "total_clientes": total_clientes,

        # Ventas
        "total_ventas": estadisticas_ventas["total_ventas"],
        "ventas_rechazadas": estadisticas_ventas["ventas_rechazadas"],
        "ventas_en_espera": estadisticas_ventas["ventas_en_espera"],
        "ventas_en_confirmacion": estadisticas_ventas["ventas_en_confirmacion"],
        "ventas_confirmadas": estadisticas_ventas["ventas_confirmadas"],

        # Cuentas y métodos de pago
        "total_cuentas": estadisticas_cuentas["total_cuentas"],
        "total_pago_movil": estadisticas_cuentas["total_pago_movil"],
        "total_transferencias": estadisticas_cuentas["total_transferencias"],

        # Productos
        "total_productos": total_productos,

        # Importes de ventas confirmadas
        "total_ventas_bolivares": float(total_ventas_bolivares),
        "total_ventas_dolares": float(total_ventas_dolares)

    })

# EVOLUCIÓN DE VENTAS

def evolucion_ventas(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar las estadísticas."
        }, status=401)

    try:

        fecha_actual = timezone.localdate()

        # Primer día del mes de hace 11 meses.
        mes_inicial = fecha_actual.month - 11
        anio_inicial = fecha_actual.year

        while mes_inicial <= 0:
            mes_inicial += 12
            anio_inicial -= 1

        fecha_inicio = fecha_actual.replace(
            year=anio_inicial,
            month=mes_inicial,
            day=1
        )

        # Ventas confirmadas agrupadas por mes.
        registros = (
            venta.objects
            .filter(
                estado=venta.Estado.CONFIRMADA,
                fecha_venta__date__gte=fecha_inicio,
                fecha_venta__date__lte=fecha_actual
            )
            .annotate(
                mes=TruncMonth("fecha_venta")
            )
            .values("mes")
            .annotate(
                total_ventas=Sum("total")
            )
            .order_by("mes")
        )

        meses = [
            "Enero", "Febrero", "Marzo", "Abril",
            "Mayo", "Junio", "Julio", "Agosto",
            "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        datos_meses = {}

        for registro in registros:

            fecha = registro["mes"]

            clave = f"{fecha.year}-{fecha.month:02d}"

            datos_meses[clave] = float(
                registro["total_ventas"] or 0
            )

        etiquetas = []
        valores = []

        # Generar los últimos 12 meses, incluso cuando no tengan ventas.
        anio = fecha_inicio.year
        mes = fecha_inicio.month

        for _ in range(12):

            clave = f"{anio}-{mes:02d}"

            etiquetas.append(
                f"{meses[mes - 1]} {anio}"
            )

            valores.append(
                datos_meses.get(clave, 0)
            )

            mes += 1

            if mes > 12:
                mes = 1
                anio += 1

        return JsonResponse({
            "estado": "exito",
            "title": "Estadísticas de ventas",
            "icon": "success",
            "descripcion": "Evolución de las ventas obtenida correctamente.",
            "etiquetas": etiquetas,
            "valores": valores
        })

    except Exception as error:
        print("Error en evolucion_ventas:", error)

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar",
            "icon": "error",
            "descripcion": "No fue posible obtener la evolución de las ventas."
        }, status=500)

# PRODUCTOS MÁS VENDIDOS

def productos_mas_vendidos(request):

    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar las estadísticas."
        }, status=401)

    try:

        registros = (
            detalle_venta.objects
            .filter(
                id_venta__estado=venta.Estado.CONFIRMADA
            )
            .values(
                "id_producto__nombre",
                "id_producto__codigo"
            )
            .annotate(
                cantidad_vendida=Sum("cantidad")
            )
            .order_by("-cantidad_vendida")[:10]
        )

        etiquetas = []
        valores = []

        for registro in registros:

            nombre = registro["id_producto__nombre"]
            codigo = registro["id_producto__codigo"]

            etiquetas.append(
                f"{nombre} ({codigo})"
            )

            valores.append(
                float(registro["cantidad_vendida"] or 0)
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Productos más vendidos",
            "icon": "success",
            "descripcion": "Productos más vendidos obtenidos correctamente.",
            "etiquetas": etiquetas,
            "valores": valores
        })

    except Exception as error:

        print("Error en productos_mas_vendidos:", error)

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar",
            "icon": "error",
            "descripcion": "No fue posible obtener los productos más vendidos."
        }, status=500)

# DATOS DEL SISTEMA CLIENTE

def registro_sistema_cliente(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar sus registros."
        }, status=401)

    # IDENTIFICAR CLIENTE
    cliente_actual = cliente.objects.filter(
        id_usuario__cedula_identidad=cedula
    ).first()

    if not cliente_actual:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró el registro del cliente."
        }, status=404)

    ventas_cliente = venta.objects.filter(
        id_cliente=cliente_actual
    )

    total_compras = ventas_cliente.count()

    compras_rechazadas = ventas_cliente.filter(
        estado=venta.Estado.RECHAZADA
    ).count()

    compras_en_espera = ventas_cliente.filter(
        estado=venta.Estado.BORRADOR
    ).count()

    compras_en_confirmacion = ventas_cliente.filter(
        estado=venta.Estado.PENDIENTE_CONFIRMACION
    ).count()

    compras_confirmadas = ventas_cliente.filter(
        estado=venta.Estado.CONFIRMADA
    ).count()

    pagos_cliente = pago.objects.filter(
        id_venta__id_cliente=cliente_actual,
        estado=pago.Estado.REGISTRADO
    )

    total_pago_movil = pagos_cliente.filter(
        Q(id_metodo_pago__nombre__icontains="móvil") |
        Q(id_metodo_pago__nombre__icontains="movil")
    ).count()

    total_transferencias = pagos_cliente.filter(
        id_metodo_pago__nombre__icontains="transferencia"
    ).count()

    # ==========================================
    # RESPUESTA JSON
    # ==========================================

    resultado = {
        "estado": "exito",
        "title": "Registro del cliente",
        "icon": "success",
        "descripcion": "Estadísticas del cliente obtenidas correctamente.",

        # Compras
        "total_compras": total_compras,
        "compras_rechazadas": compras_rechazadas,
        "compras_en_espera": compras_en_espera,
        "compras_confirmadas": compras_confirmadas,

        # Métodos de pago
        "total_pago_movil": total_pago_movil,
        "total_transferencias": total_transferencias
    }

    return JsonResponse(resultado)

def banco_pago_compra(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar los registros."
        }, status=401)

    cliente_actual = cliente.objects.filter(
        id_usuario__cedula_identidad=cedula
    ).first()

    if not cliente_actual:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró el registro del cliente."
        }, status=404)

    bancos_cliente = pago.objects.filter(
        id_venta__id_cliente=cliente_actual,
        id_venta__estado=venta.Estado.CONFIRMADA,
        estado=pago.Estado.REGISTRADO
    ).exclude(
        banco_origen__exact=""
    ).values(
        "banco_origen"
    ).annotate(
        cantidad_pagos=Count("id_pago"),
        total_pagado=Sum("monto")
    ).order_by(
        "-cantidad_pagos"
    )

    bancos = []
    for banco in bancos_cliente:
        bancos.append({
            "banco": banco["banco_origen"],
            "cantidad_pagos": banco["cantidad_pagos"],
            "total_pagado": float(banco["total_pagado"] or 0)
        })

    return JsonResponse({
        "estado": "exito",
        "title": "Bancos utilizados",
        "icon": "success",
        "descripcion": "Bancos de origen de los pagos obtenidos correctamente.",

        "total_bancos": len(bancos),

        "bancos": bancos
    })

def productos_mas_comprados(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "Debe iniciar sesión para consultar los registros."
        }, status=401)

    try:

        productos = (
            detalle_venta.objects
            .filter(
                id_venta__estado="CONFIRMADA"
            )
            .values(
                "id_producto",
                "id_producto__nombre",
                "id_producto__codigo",
                "id_producto__id_categoria__nombre",
                "id_producto__id_unidad__nombre",
                "id_producto__id_unidad__abreviatura"
            )
            .annotate(
                cantidad_vendida=Coalesce(
                    Sum("cantidad"),
                    Decimal("0.000"),
                    output_field=DecimalField(
                        max_digits=14,
                        decimal_places=3
                    )
                ),
                total_ventas=Count(
                    "id_venta",
                    distinct=True
                ),
                ingresos_totales=Coalesce(
                    Sum("subtotal"),
                    Decimal("0.00"),
                    output_field=DecimalField(
                        max_digits=16,
                        decimal_places=2
                    )
                )
            )
            .order_by("-cantidad_vendida", "id_producto__nombre")[:10]
        )

        resultados = []

        for posicion, producto in enumerate(productos, start=1):

            resultados.append({
                "posicion": posicion,
                "id_producto": producto["id_producto"],
                "nombre": producto["id_producto__nombre"],
                "codigo": producto["id_producto__codigo"],
                "categoria": producto["id_producto__id_categoria__nombre"],
                "unidad": producto["id_producto__id_unidad__nombre"],
                "abreviatura": producto["id_producto__id_unidad__abreviatura"],
                "cantidad_vendida": str(producto["cantidad_vendida"]),
                "total_ventas": producto["total_ventas"],
                "ingresos_totales": str(producto["ingresos_totales"])
            })

        return JsonResponse({
            "estado": "exito",
            "title": "Productos más comprados",
            "icon": "success",
            "descripcion": "Estadísticas de productos obtenidas correctamente.",
            "total_productos": len(resultados),
            "productos": resultados
        })

    except Exception as e:

        print(f"Error al consultar productos más comprados: {e}")

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar estadísticas",
            "icon": "error",
            "descripcion": "No fue posible obtener los productos más comprados."
        }, status=500)

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
