from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Sum, Count, Exists, OuterRef, Q
from django.conf import settings

from inicio_sesion.models import usuarios, bitacora, supervisores_encargados, personal_limpieza, despachadores, vigilantes
from asignaciones.models import asignacion_equipo, movimiento_equipo, equipos, entrega_equipos

import os
from django.utils import timezone

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
)

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, legal

from xml.sax.saxutils import escape

# GESTIONAR ASIGNACIÓN DE EQUIPOS

# EMPLEADOS REGISTRADOS

def empleados_registrados(request):
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "No se encontró la identificación del supervisor.",
            "icon": "warning"
        })

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "No se encontró un supervisor activo asociado a la sesión.",
            "icon": "warning"
        })

    id_turno = supervisor.id_turno_id

    limpieza = personal_limpieza.objects.filter(
        id_usuario=OuterRef("pk"),
        id_turno_id=id_turno,
        vigencia=True
    )

    despachador = despachadores.objects.filter(
        id_usuario=OuterRef("pk"),
        id_turno_id=id_turno,
        vigencia=True
    )

    vigilante = vigilantes.objects.filter(
        id_usuario=OuterRef("pk"),
        id_turno_id=id_turno,
        vigencia=True
    )

    empleados = (
        usuarios.objects
        .annotate(
            es_limpieza=Exists(limpieza),
            es_despachador=Exists(despachador),
            es_vigilante=Exists(vigilante)
        )
        .filter(
            Q(es_limpieza=True) |
            Q(es_despachador=True) |
            Q(es_vigilante=True)
        )
        .order_by("apellidos", "nombres")
    )

    datos = [
        {
            "id_usuario": empleado.id_usuario,
            "nombres": empleado.nombres,
            "apellidos": empleado.apellidos,
            "cedula_identidad": empleado.cedula_identidad,
            "perfil": (
                "Personal de limpieza" if empleado.es_limpieza
                else "Despachador" if empleado.es_despachador
                else "Vigilante"
            )
        }
        for empleado in empleados
    ]

    return JsonResponse(datos, safe=False)

# EQUIPOS REGISTRADOS

def equipos_registrados_supervisor(request):
    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=request.session.get("cedula_identidad"),
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "No se encontró un supervisor activo.",
            "icon": "warning"
        })

    equipos_lista = (
        entrega_equipos.objects
        .filter(
            supervisor_encargado=supervisor,
            estado="ASIGNADO",
            cantidad_disponible__gt=0
        )
        .values(
            "id_equipo_id",
            "id_equipo__nombre",
            "id_equipo__codigo",
            "id_equipo__id_categoria__nombre",
            "id_equipo__observacion"
        )
        .annotate(
            cantidad_total=Sum("cantidad_entregada"),
            cantidad_disponible=Sum("cantidad_disponible")
        )
        .order_by("id_equipo__nombre")
    )

    datos = [
        {
            "id_equipo": equipo["id_equipo_id"],
            "nombre": equipo["id_equipo__nombre"],
            "codigo": equipo["id_equipo__codigo"],
            "categoria": equipo["id_equipo__id_categoria__nombre"],
            "cantidad_total": equipo["cantidad_total"],
            "cantidad_disponible": equipo["cantidad_disponible"],
            "observacion": (
                equipo["id_equipo__observacion"]
                if equipo["id_equipo__observacion"]
                else "Sin observación"
            )
        }
        for equipo in equipos_lista
    ]

    return JsonResponse(datos, safe=False)

# CANTIDAD DISPONIBLE DEL EQUIPO SELECCIONADO Y LA OBSERVACIÓN DE LA ASIGNACIÓN DEL EMPLEADO

def datos_equipo_seleccionado(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        })

    cedula_supervisor = request.session.get("cedula_identidad")
    id_equipo = request.POST.get("id_equipo", "").strip()
    id_usuario = request.POST.get("id_usuario", "").strip()

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "No se encontró la identificación del supervisor.",
            "icon": "warning"
        })

    if not id_equipo.isdigit() or int(id_equipo) <= 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Equipo inválido",
            "descripcion": "Debe seleccionar un equipo válido.",
            "icon": "warning"
        })
    
    if not id_usuario.isdigit() or int(id_usuario) <= 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Empleado requerido",
            "descripcion": "Debe seleccionar un empleado válido.",
            "icon": "warning"
        })

    supervisor = (
        supervisores_encargados.objects
        .filter(
            id_usuario__cedula_identidad=cedula_supervisor,
            vigencia=True
        )
        .select_related("id_turno")
        .first()
    )

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "El supervisor no existe o está inactivo.",
            "icon": "warning"
        })

    id_turno = supervisor.id_turno_id

    empleado_valido = usuarios.objects.filter(
        pk=int(id_usuario)
    ).filter(
        Q(personal_limpieza__id_turno_id=id_turno, personal_limpieza__vigencia=True) |
        Q(despachador__id_turno_id=id_turno, despachador__vigencia=True) |
        Q(vigilante__id_turno_id=id_turno, vigilante__vigencia=True)
    ).exists()

    if not empleado_valido:
        return JsonResponse({
            "estado": "fallo",
            "title": "Empleado no autorizado",
            "descripcion": (
                "El empleado no pertenece al turno del supervisor "
                "o su perfil está inactivo."
            ),
            "icon": "warning"
        })

    entrega = (
        entrega_equipos.objects
        .select_related(
            "id_equipo",
            "id_equipo__id_categoria",
            "supervisor_encargado"
        )
        .filter(
            id_equipo_id=int(id_equipo),
            supervisor_encargado=supervisor,
            estado="ASIGNADO",
            cantidad_disponible__gt=0
        )
        .order_by("id_entrega")
        .first()
    )

    if not entrega:
        return JsonResponse({
            "estado": "fallo",
            "title": "Equipo no disponible",
            "descripcion": (
                "El equipo no tiene entregas disponibles "
                "asociadas al supervisor."
            ),
            "icon": "warning"
        })

    asignacion_existente = (
        asignacion_equipo.objects
        .filter(
            id_usuario_id=int(id_usuario),
            id_entrega__id_equipo_id=entrega.id_equipo_id
        )
        .exclude(estado="FINALIZADO")
        .select_related("id_entrega", "id_entrega__id_equipo")
        .order_by("-fecha_entrega")
        .first()
    )

    return JsonResponse({
        "estado": "exito",
        "datos": {
            "id_entrega": entrega.id_entrega,
            "id_equipo": entrega.id_equipo_id,
            "equipo": entrega.id_equipo.nombre,
            "codigo": entrega.id_equipo.codigo,
            "categoria": entrega.id_equipo.id_categoria.nombre,
            "cantidad_disponible": entrega.cantidad_disponible,
            "observacion": (
                asignacion_existente.observacion
                if asignacion_existente else ""
            ),
            "cantidad_asignada_previamente": (
                asignacion_existente.cantidad_asignada
                if asignacion_existente else 0
            ),
            "id_asignacion": (
                asignacion_existente.id_asignacion
                if asignacion_existente else None
            )
        }
    })
 
# REGISTRAR LA ASIGNACIÓN DEL EQUIPO

def asignar_equipo_usuario(request):
    if request.method != "POST":
        return render(request, "Asignacion_Equipo/Supervisor_Encargado/asignar_equipo_usuario.html")

    id_usuario = request.POST.get("empleados_registrados", "").strip()
    id_equipo = request.POST.get("equipos_registrados", "").strip()
    observacion = request.POST.get("observacion_entrega", "").strip()
    cantidad = request.POST.get("cantidad_entrega", "").strip()

    campos = [
        (id_usuario, "Empleado", "Seleccione un empleado."),
        (id_equipo, "Equipo", "Seleccione un equipo."),
        (cantidad, "Cantidad", "Ingrese la cantidad que desea asignar.")
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    try:
        id_usuario = int(id_usuario)
        id_equipo = int(id_equipo)
        cantidad = int(cantidad)

        if id_usuario <= 0 or id_equipo <= 0 or cantidad <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos inválidos",
            "descripcion": "Seleccione un empleado y un equipo válidos, e ingrese una cantidad mayor que cero.",
            "icon": "warning"
        })

    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "Debe iniciar sesión nuevamente.",
            "icon": "warning"
        })

    try:
        with transaction.atomic():
            supervisor = (
                supervisores_encargados.objects
                .select_for_update()
                .filter(
                    id_usuario__cedula_identidad=cedula_supervisor,
                    vigencia=True
                )
                .first()
            )

            if not supervisor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Supervisor no encontrado",
                    "descripcion": "El supervisor encargado no existe o está inactivo.",
                    "icon": "warning"
                })

            info_usuario = usuarios.objects.filter(id_usuario=id_usuario).first()
            if not info_usuario:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Empleado no encontrado",
                    "descripcion": "El empleado seleccionado no existe.",
                    "icon": "warning"
                })

            info_equipo = equipos.objects.filter(id_equipo=id_equipo).first()
            if not info_equipo:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Equipo no encontrado",
                    "descripcion": "El equipo seleccionado no existe.",
                    "icon": "warning"
                })

            # Validar que el empleado tenga un perfil activo perteneciente al turno del supervisor.
            perfiles = [
                (personal_limpieza, "Personal de limpieza"),
                (despachadores, "Despachador"),
                (vigilantes, "Vigilante")
            ]

            perfil = None

            for modelo, nombre_perfil in perfiles:
                if modelo.objects.filter(
                    id_usuario=info_usuario,
                    id_turno_id=supervisor.id_turno_id,
                    vigencia=True
                ).exists():
                    perfil = nombre_perfil
                    break

            if not perfil:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Empleado no autorizado",
                    "descripcion": "El empleado no tiene un perfil activo en el turno de este supervisor.",
                    "icon": "warning"
                })

            # Bloquear las entregas que contienen existencias disponibles para este supervisor y equipo.
            inventario = list(
                entrega_equipos.objects
                .select_for_update()
                .filter(
                    supervisor_encargado=supervisor,
                    id_equipo=info_equipo,
                    estado="ASIGNADO",
                    cantidad_disponible__gt=0
                )
                .order_by("id_entrega")
            )

            cantidad_disponible = sum(
                entrega.cantidad_disponible
                for entrega in inventario
            )

            if cantidad_disponible < cantidad:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Cantidad insuficiente",
                    "descripcion": (
                        f"Existencias disponibles de {info_equipo.nombre}: "
                        f"{cantidad_disponible}. "
                        f"Cantidad solicitada: {cantidad}."
                    ),
                    "icon": "warning"
                })

            restante = cantidad

            for entrega in inventario:
                if restante == 0:
                    break

                cantidad_asignar = min(
                    entrega.cantidad_disponible,
                    restante
                )

                # Descontar exclusivamente de la entrega de la que salen las unidades.
                entrega.cantidad_disponible -= cantidad_asignar

                entrega.save(
                    update_fields=["cantidad_disponible"]
                )

                # Buscar una asignación todavía abierta para el mismo empleado y entrega.
                asignacion = (
                    asignacion_equipo.objects
                    .select_for_update()
                    .filter(
                        id_entrega=entrega,
                        id_usuario=info_usuario,
                        estado__in=["ASIGNADO", "PARCIAL"]
                    )
                    .first()
                )

                if asignacion:
                    asignacion.cantidad_asignada += cantidad_asignar

                    asignacion.estado = (
                        "PARCIAL"
                        if asignacion.cantidad_devuelta > 0
                        else "ASIGNADO"
                    )

                    if observacion:
                        asignacion.observacion = (
                            f"{asignacion.observacion}\n{observacion}"
                            if asignacion.observacion
                            else observacion
                        )

                    asignacion.save(
                        update_fields=[
                            "cantidad_asignada",
                            "estado",
                            "observacion"
                        ]
                    )

                else:
                    asignacion_equipo.objects.create(
                        id_entrega=entrega,
                        id_usuario=info_usuario,
                        observacion=observacion or "N/A",
                        cantidad_asignada=cantidad_asignar,
                        cantidad_devuelta=0,
                        estado="ASIGNADO",
                        motivo_incidencia="NINGUNA"
                    )

                restante -= cantidad_asignar

            bitacora.objects.create(
                id_usuario=supervisor.id_usuario,
                accion=(
                    f"Asignó {cantidad} unidad(es) de "
                    f"{info_equipo.nombre} a "
                    f"{info_usuario.nombres} "
                    f"{info_usuario.apellidos} "
                    f"({info_usuario.cedula_identidad}). "
                    f"Perfil: {perfil}."
                )
            )
        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Registro exitoso",
            "descripcion": "El equipo fue asignado correctamente al empleado."
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error al asignar",
            "descripcion": "No fue posible registrar la asignación. No se confirmaron los cambios."
        })
    
# BUSCAR TODOS LOS DATOS LA ASIGNACIÓN DEL EQUIPO

def buscar_datos_asignacion_equipo(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    id_asignacion = request.POST.get("id_asignacion", "").strip()
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "Debe iniciar sesión nuevamente.",
            "icon": "warning"
        })

    if not id_asignacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Asignación requerida",
            "descripcion": "Debe seleccionar una asignación.",
            "icon": "warning"
        })

    try:
        id_asignacion = int(id_asignacion)

        if id_asignacion <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El identificador de la asignación no es válido.",
            "icon": "warning"
        }, status=400)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no autorizado",
            "descripcion": "El supervisor no existe o está inactivo.",
            "icon": "warning"
        })

    try:
        asignacion = (
            asignacion_equipo.objects
            .select_related(
                "id_usuario",
                "id_entrega",
                "id_entrega__id_equipo",
                "id_entrega__id_equipo__id_categoria",
                "id_entrega__supervisor_encargado"
            )
            .get(
                id_asignacion=id_asignacion,
                id_entrega__supervisor_encargado=supervisor
            )
        )

    except asignacion_equipo.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Asignación no encontrada",
            "descripcion": "No existe la asignación o no pertenece a este supervisor.",
            "icon": "error"
        })

    empleado = asignacion.id_usuario
    id_turno = supervisor.id_turno_id

    empleado_valido = (
        personal_limpieza.objects.filter(
            id_usuario=empleado,
            id_turno_id=id_turno,
            vigencia=True
        ).exists()
        or despachadores.objects.filter(
            id_usuario=empleado,
            id_turno_id=id_turno,
            vigencia=True
        ).exists()
        or vigilantes.objects.filter(
            id_usuario=empleado,
            id_turno_id=id_turno,
            vigencia=True
        ).exists()
    )

    if not empleado_valido:
        return JsonResponse({
            "estado": "fallo",
            "title": "Empleado no autorizado",
            "descripcion": "El empleado no tiene un perfil activo en el turno de este supervisor.",
            "icon": "warning"
        })

    equipo = asignacion.id_entrega.id_equipo
    cantidad_pendiente = (
        asignacion.cantidad_asignada - asignacion.cantidad_devuelta
    )

    datos = {
        "id": asignacion.id_asignacion,
        "empleado": (
            f"{empleado.nombres} {empleado.apellidos}"
        ),
        "cedula": empleado.cedula_identidad,
        "equipo": equipo.nombre,
        "codigo": equipo.codigo,
        "categoria": equipo.id_categoria.nombre,
        "cantidad_asignada": asignacion.cantidad_asignada,
        "cantidad_devuelta": asignacion.cantidad_devuelta,
        "cantidad_pendiente": cantidad_pendiente,
        "fecha_entrega": timezone.localtime(
            asignacion.fecha_entrega
        ).strftime("%d/%m/%Y %H:%M"),
        "fecha_devolucion": (
            timezone.localtime(
                asignacion.fecha_devolucion
            ).strftime("%d/%m/%Y %H:%M")
            if asignacion.fecha_devolucion
            else "N/A"
        ),
        "estado": asignacion.get_estado_display(),
        "observacion": asignacion.observacion,
        "motivo_incidencia": asignacion.get_motivo_incidencia_display()
    }

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

# BUSCAR DATOS DE EQUIPO A DEVOLVER

def buscar_equipo_devolver(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    id_asignacion = request.POST.get("id_asignacion", "").strip()
    cedula_supervisor = request.session.get("cedula_identidad")

    # Validar sesión
    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "Debe iniciar sesión nuevamente.",
            "icon": "warning"
        }, status=401)

    # Validar identificador
    if not id_asignacion or not id_asignacion.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Asignación inválida",
            "descripcion": "Debe seleccionar una asignación válida.",
            "icon": "warning"
        })

    try:
        with transaction.atomic():

            # Buscar supervisor activo
            supervisor = (
                supervisores_encargados.objects
                .filter(
                    id_usuario__cedula_identidad=cedula_supervisor,
                    vigencia=True
                )
                .first()
            )

            if not supervisor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Acceso denegado",
                    "descripcion": (
                        "No tiene un perfil de supervisor encargado activo."
                    ),
                    "icon": "warning"
                }, status=403)

            # Obtener la asignación correspondiente al supervisor
            asignacion = (
                asignacion_equipo.objects
                .select_related(
                    "id_usuario",
                    "id_entrega",
                    "id_entrega__id_equipo",
                    "id_entrega__supervisor_encargado"
                )
                .filter(
                    id_asignacion=int(id_asignacion),
                    id_entrega__supervisor_encargado=supervisor
                )
                .first()
            )

            if not asignacion:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Asignación no encontrada",
                    "descripcion": (
                        "La asignación no existe o no pertenece "
                        "a su inventario."
                    ),
                    "icon": "error"
                })

            # Validar estado de la asignación
            if asignacion.estado not in ["ASIGNADO", "PARCIAL"]:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Asignación finalizada",
                    "descripcion": (
                        "Esta asignación ya fue completada y "
                        "no admite más devoluciones."
                    ),
                    "icon": "warning"
                })

            # Calcular cantidades reales
            cantidad_asignada = asignacion.cantidad_asignada
            cantidad_devuelta = asignacion.cantidad_devuelta

            cantidad_pendiente = (
                cantidad_asignada - cantidad_devuelta
            )

            if cantidad_pendiente <= 0:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sin equipos pendientes",
                    "descripcion": (
                        "No quedan unidades pendientes por devolver."
                    ),
                    "icon": "warning"
                })

            # Datos del empleado
            usuario = asignacion.id_usuario

            # Datos del equipo
            entrega = asignacion.id_entrega
            equipo = entrega.id_equipo

            datos_asignacion = {
                "id": asignacion.id_asignacion,
                "cedula": usuario.cedula_identidad,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "equipo": str(equipo),
                "cantidad_asignada": cantidad_asignada,
                "cantidad_devuelta": cantidad_devuelta,
                "cantidad_pendiente": cantidad_pendiente,
                "estado": asignacion.estado,
            }

        return JsonResponse({
            "estado": "exito",
            "title": "Asignación encontrada",
            "descripcion": "Datos de la asignación obtenidos correctamente.",
            "icon": "success",
            "asignacion": datos_asignacion
        })

    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "Error al buscar la asignación para devolución."
        )

        return JsonResponse({
            "estado": "fallo",
            "title": "Error interno",
            "descripcion": (
                "No fue posible consultar la asignación. "
                "Inténtelo nuevamente."
            ),
            "icon": "error"
        }, status=500)
    
# LISTAR EQUIPOS ASIGNADO DEL EMPLEADO

def equipos_asignado_usuario(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    id_usuario = request.POST.get("id_usuario", "").strip()
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "Debe iniciar sesión nuevamente.",
            "icon": "warning"
        }, status=401)

    if not id_usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Empleado no seleccionado",
            "descripcion": "Debe seleccionar un empleado.",
            "icon": "warning"
        }, status=400)

    try:
        id_usuario = int(id_usuario)

        if id_usuario <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El empleado seleccionado no es válido.",
            "icon": "warning"
        }, status=400)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no autorizado",
            "descripcion": "El supervisor no existe o está inactivo.",
            "icon": "warning"
        }, status=403)

    info_usuario = usuarios.objects.filter(
        id_usuario=id_usuario
    ).first()

    if not info_usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Empleado no encontrado",
            "descripcion": "No existe el empleado seleccionado.",
            "icon": "error"
        }, status=404)

    id_turno = supervisor.id_turno_id

    empleado_valido = (
        personal_limpieza.objects.filter(
            id_usuario=info_usuario,
            id_turno_id=id_turno,
            vigencia=True
        ).exists()
        or despachadores.objects.filter(
            id_usuario=info_usuario,
            id_turno_id=id_turno,
            vigencia=True
        ).exists()
        or vigilantes.objects.filter(
            id_usuario=info_usuario,
            id_turno_id=id_turno,
            vigencia=True
        ).exists()
    )

    if not empleado_valido:
        return JsonResponse({
            "estado": "fallo",
            "title": "Empleado no autorizado",
            "descripcion": "El empleado no tiene un perfil activo en el turno del supervisor.",
            "icon": "warning"
        }, status=403)

    equipos_usuario = (
        asignacion_equipo.objects
        .filter(
            id_usuario=info_usuario,
            id_entrega__supervisor_encargado=supervisor,
            estado__in=["ASIGNADO", "PARCIAL"]
        )
        .select_related(
            "id_usuario",
            "id_entrega",
            "id_entrega__id_equipo"
        )
        .order_by("-fecha_entrega")
    )

    datos = []

    for asignacion in equipos_usuario:
        datos.append({
            "id": asignacion.id_asignacion,
            "equipo": asignacion.id_entrega.id_equipo.nombre,
            "fecha_entrega": timezone.localtime(
                asignacion.fecha_entrega
            ).strftime("%d/%m/%Y %H:%M"),
            "cantidad": asignacion.cantidad_asignada,
            "cantidad_devuelta": asignacion.cantidad_devuelta,
            "cantidad_pendiente": (
                asignacion.cantidad_asignada
                - asignacion.cantidad_devuelta
            ),
            "estado": asignacion.get_estado_display()
        })

    if not datos:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin asignaciones",
            "descripcion": "El empleado no tiene equipos pendientes de devolución asignados por este supervisor.",
            "icon": "warning"
        })

    return JsonResponse({
        "estado": "exito",
        "equipos": datos
    })

# DEVOLUCIÓN DE EQUIPO

def devolucion_equipos_asignado(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    id_asignacion = request.POST.get("id_asignacion", "").strip()
    ci_usuario = request.POST.get("ci_usuario", "").strip()
    tipo_devolucion = request.POST.get("tipos_devolucion", "").strip()
    estado_devolucion = request.POST.get("estados_devolucion", "").strip()
    cantidad_devolver = request.POST.get("cantidad_devolver", "").strip()

    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "Debe iniciar sesión nuevamente.",
            "icon": "warning"
        }, status=401)

    if not id_asignacion.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Asignación inválida",
            "descripcion": "Debe indicar una asignación válida.",
            "icon": "warning"
        })

    if not ci_usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Empleado no indicado",
            "descripcion": "No se recibió la cédula del empleado.",
            "icon": "warning"
        })

    if tipo_devolucion not in ["DEVOLUCION", "CORRECCION"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo inválido",
            "descripcion": "Debe seleccionar un tipo de operación válido.",
            "icon": "warning"
        })

    try:
        with transaction.atomic():

            # 1. Validar al supervisor autenticado.
            supervisor = (
                supervisores_encargados.objects
                .select_for_update()
                .filter(
                    id_usuario__cedula_identidad=cedula_supervisor,
                    vigencia=True
                )
                .first()
            )

            if not supervisor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Acceso denegado",
                    "descripcion": (
                        "No tiene un perfil de supervisor encargado activo."
                    ),
                    "icon": "warning"
                }, status=403)

            # 2. Bloquear la asignación para evitar operaciones simultáneas.
            asignacion = (
                asignacion_equipo.objects
                .select_for_update()
                .select_related(
                    "id_usuario",
                    "id_entrega",
                    "id_entrega__id_equipo",
                    "id_entrega__supervisor_encargado"
                )
                .filter(
                    id_asignacion=int(id_asignacion),
                    id_entrega__supervisor_encargado=supervisor
                )
                .first()
            )

            if not asignacion:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Asignación no encontrada",
                    "descripcion": (
                        "La asignación no existe o no pertenece "
                        "a su inventario."
                    ),
                    "icon": "error"
                })

            if asignacion.id_usuario.cedula_identidad != ci_usuario:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Empleado no coincide",
                    "descripcion": (
                        "El empleado indicado no corresponde "
                        "a esta asignación."
                    ),
                    "icon": "warning"
                })

            if asignacion.estado not in ["ASIGNADO", "PARCIAL"]:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Asignación finalizada",
                    "descripcion": (
                        "Esta asignación ya no admite devoluciones."
                    ),
                    "icon": "warning"
                })

            # 3. Calcular la cantidad pendiente REAL en la base de datos.
            cantidad_pendiente = (
                asignacion.cantidad_asignada
                - asignacion.cantidad_devuelta
            )

            if cantidad_pendiente <= 0:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sin equipos pendientes",
                    "descripcion": (
                        "No existe cantidad pendiente por devolver."
                    ),
                    "icon": "warning"
                })

            # 4. Bloquear la entrega de origen.
            entrega = (
                entrega_equipos.objects
                .select_for_update()
                .get(id_entrega=asignacion.id_entrega_id)
            )

            # 5. Obtener al usuario que registra el movimiento.
            usuario_registro = usuarios.objects.filter(
                cedula_identidad=cedula_supervisor
            ).first()

            if not usuario_registro:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Usuario no encontrado",
                    "descripcion": (
                        "No se encontró el usuario que registra la operación."
                    ),
                    "icon": "error"
                })

            # 6. Procesar una corrección por error humano.
            if tipo_devolucion == "CORRECCION":

                cantidad = cantidad_pendiente
                estado = "BUEN_ESTADO"
                motivo_incidencia = "ERROR_HUMANO"

                nueva_disponibilidad = (
                    entrega.cantidad_disponible + cantidad
                )

                if nueva_disponibilidad > entrega.cantidad_entregada:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Inconsistencia de inventario",
                        "descripcion": (
                            "La corrección supera la cantidad disponible "
                            "permitida en la entrega del supervisor."
                        ),
                        "icon": "error"
                    })

                entrega.cantidad_disponible = nueva_disponibilidad
                entrega.save(update_fields=["cantidad_disponible"])

                asignacion.cantidad_devuelta = (
                    asignacion.cantidad_asignada
                )
                asignacion.estado = "FINALIZADO"
                asignacion.fecha_devolucion = timezone.now()

                asignacion.save(update_fields=[
                    "cantidad_devuelta",
                    "estado",
                    "fecha_devolucion"
                ])

            # 7. Procesar una devolución normal.
            else:

                if estado_devolucion not in [
                    "BUEN_ESTADO",
                    "DETERIORADO",
                    "DAÑADO"
                ]:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Estado inválido",
                        "descripcion": (
                            "Seleccione un estado válido para los equipos."
                        ),
                        "icon": "warning"
                    })

                try:
                    cantidad = int(cantidad_devolver)
                except (TypeError, ValueError):
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Cantidad inválida",
                        "descripcion": (
                            "La cantidad debe ser un número entero."
                        ),
                        "icon": "warning"
                    })

                # Nunca confiar únicamente en el máximo del HTML.
                if cantidad <= 0 or cantidad > cantidad_pendiente:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Cantidad inválida",
                        "descripcion": (
                            f"Solo puede devolver entre 1 y "
                            f"{cantidad_pendiente} unidades."
                        ),
                        "icon": "warning"
                    })

                estado = estado_devolucion
                motivo_incidencia = "NINGUNA"

                # Solo los equipos en buen estado vuelven
                # a estar disponibles en el inventario.
                if estado == "BUEN_ESTADO":

                    nueva_disponibilidad = (
                        entrega.cantidad_disponible + cantidad
                    )

                    if nueva_disponibilidad > entrega.cantidad_entregada:
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Inconsistencia de inventario",
                            "descripcion": (
                                "La devolución supera la cantidad "
                                "originalmente entregada al supervisor. "
                                "Verifique el inventario."
                            ),
                            "icon": "error"
                        })

                    entrega.cantidad_disponible = nueva_disponibilidad
                    entrega.save(update_fields=["cantidad_disponible"])

                # Actualizar el acumulado devuelto.
                asignacion.cantidad_devuelta += cantidad

                if (
                    asignacion.cantidad_devuelta
                    >= asignacion.cantidad_asignada
                ):
                    asignacion.cantidad_devuelta = (
                        asignacion.cantidad_asignada
                    )
                    asignacion.estado = "FINALIZADO"
                    asignacion.fecha_devolucion = timezone.now()
                else:
                    asignacion.estado = "PARCIAL"

                asignacion.save(update_fields=[
                    "cantidad_devuelta",
                    "estado",
                    "fecha_devolucion"
                ])

            # 8. Registrar el movimiento dentro de la misma transacción.
            movimiento_equipo.objects.create(
                id_asignacion=asignacion,
                usuario_registro=usuario_registro,
                cantidad=cantidad,
                tipo=tipo_devolucion,
                estado=estado,
                motivo_incidencia=motivo_incidencia
            )

            # 9. Calcular las cantidades actualizadas para el frontend.
            nueva_cantidad_pendiente = (
                asignacion.cantidad_asignada
                - asignacion.cantidad_devuelta
            )

            cantidad_disponible_actual = entrega.cantidad_disponible

        # La transacción ya se ha completado correctamente.
        return JsonResponse({
            "estado": "exito",
            "title": "Operación realizada",
            "descripcion": (
                "La corrección por error humano fue registrada correctamente."
                if tipo_devolucion == "CORRECCION"
                else "La devolución fue registrada correctamente."
            ),
            "icon": "success",
            "asignacion": {
                "id": asignacion.id_asignacion,
                "cantidad_asignada": asignacion.cantidad_asignada,
                "cantidad_devuelta": asignacion.cantidad_devuelta,
                "cantidad_pendiente": nueva_cantidad_pendiente,
                "estado": asignacion.estado,
                "fecha_devolucion": (
                    asignacion.fecha_devolucion.isoformat()
                    if asignacion.fecha_devolucion
                    else None
                )
            },
            "inventario": {
                "cantidad_disponible": cantidad_disponible_actual
            }
        })

    except entrega_equipos.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Entrega no encontrada",
            "descripcion": (
                "No se encontró la entrega de origen de la asignación."
            ),
            "icon": "error"
        })

    except Exception:
        # Registrar la excepción en los logs del servidor en producción.
        import logging
        logging.getLogger(__name__).exception(
            "Error al procesar la devolución de equipos."
        )

        return JsonResponse({
            "estado": "fallo",
            "title": "Error interno",
            "descripcion": (
                "Ocurrió un error al registrar la operación. "
                "Inténtelo nuevamente."
            ),
            "icon": "error"
        })

# EQUIPOS ASIGNADOS

def gestionar_asignaciones_equipos(request):
    if request.method != "POST":
        return render(request, "Asignacion_Equipo/Supervisor_Encargado/gestion_asignacion.html")

    cedula_supervisor = request.session.get("cedula_identidad")
    if not cedula_supervisor:
        return JsonResponse({
            "consulta": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al supervisor de la sesión.",
            "icon": "error"
        }, status=401)

    supervisor = (
        supervisores_encargados.objects
        .filter(
            id_usuario__cedula_identidad=cedula_supervisor,
            vigencia=True
        )
        .first()
    )
    if not supervisor:
        return JsonResponse({
            "consulta": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "No se encontró un supervisor encargado activo.",
            "icon": "error"
        }, status=403)

    nacionalidad = request.POST.get("nacionalidad", "").strip()
    cedula = request.POST.get("cedula", "").strip()
    categoria = request.POST.get("categoria", "").strip()

    asignaciones = (
        asignacion_equipo.objects
        .select_related(
            "id_usuario",
            "id_entrega",
            "id_entrega__id_equipo",
            "id_entrega__id_equipo__id_categoria",
            "id_entrega__supervisor_encargado"
        )
        .filter(
            id_entrega__supervisor_encargado=supervisor
        )
        .exclude(
            motivo_incidencia="ERROR_HUMANO"
        )
        .exclude(
            id_entrega__estado__in=["DAÑADO", "DETERIORADO"]
        )
        .order_by("-fecha_entrega", "-id_asignacion")
    )

    if nacionalidad and cedula:
        asignaciones = asignaciones.filter(
            id_usuario__cedula_identidad=f"{nacionalidad}-{cedula}"
        )
    elif cedula:
        asignaciones = asignaciones.filter(
            id_usuario__cedula_identidad__endswith=f"-{cedula}"
        )

    if categoria:
        asignaciones = asignaciones.filter(
            id_entrega__id_equipo__id_categoria_id=categoria
        )

    datos = []

    for asignacion in asignaciones:
        usuario = asignacion.id_usuario
        equipo = asignacion.id_entrega.id_equipo

        cantidad_pendiente = max(
            asignacion.cantidad_asignada - asignacion.cantidad_devuelta,
            0
        )

        datos.append({
            "id": asignacion.id_asignacion,
            "empleado": f"{usuario.nombres} {usuario.apellidos}",
            "cedula": usuario.cedula_identidad,
            "equipo": equipo.nombre,
            "codigo": equipo.codigo,
            "categoria": equipo.id_categoria.nombre,
            "fecha_entrega": (
                timezone.localtime(asignacion.fecha_entrega).strftime(
                    "%d/%m/%Y %H:%M"
                )
                if asignacion.fecha_entrega else ""
            ),
            "fecha_devolucion": (
                timezone.localtime(asignacion.fecha_devolucion).strftime(
                    "%d/%m/%Y %H:%M"
                )
                if asignacion.fecha_devolucion else ""
            ),
            "cantidad_asignada": asignacion.cantidad_asignada,
            "cantidad_devuelta": asignacion.cantidad_devuelta,
            "cantidad_pendiente": cantidad_pendiente,
            "estado": asignacion.get_estado_display(),
            "observacion": asignacion.observacion
        })

    return JsonResponse(datos, safe=False)

# VISUALIZAR ASIGNACIONES POR PARTE ADMINISTRATIVA

def visualizar_asignaciones_admin(request):
    return render(request, "Asignacion_Equipo/Encargado_Administrativo/visualizar_asignaciones.html")

def asignaciones_equipos_admin(request):
    nacionalidad = request.POST.get("nacionalidad", "").strip()
    cedula = request.POST.get("cedula_identidad", "").strip()
    categoria = request.POST.get("categorias_registradas", "").strip()

    asignaciones = (
        asignacion_equipo.objects
        .select_related(
            "id_usuario",
            "id_entrega",
            "id_entrega__id_equipo",
            "id_entrega__id_equipo__id_categoria",
            "id_entrega__supervisor_encargado",
            "id_entrega__supervisor_encargado__id_usuario"
        )
        .exclude(estado="FINALIZADO")
        .order_by("-fecha_entrega")
    )

    if nacionalidad:
        asignaciones = asignaciones.filter(
            id_usuario__nacionalidad__iexact=nacionalidad
        )

    if cedula:
        asignaciones = asignaciones.filter(
            id_usuario__cedula_identidad__icontains=cedula
        )

    if categoria:
        if not categoria.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Categoría inválida",
                "descripcion": (
                    "La categoría de equipo seleccionada "
                    "no es válida."
                ),
                "icon": "warning"
            })

        asignaciones = asignaciones.filter(
            id_entrega__id_equipo__id_categoria_id=int(categoria)
        )

    datos = []

    for asignacion in asignaciones:
        usuario = asignacion.id_usuario
        entrega = asignacion.id_entrega
        equipo = entrega.id_equipo
        supervisor = entrega.supervisor_encargado

        datos.append({
            "id_asignacion": asignacion.id_asignacion,
            "id_usuario": usuario.id_usuario,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "cedula_identidad": usuario.cedula_identidad,
            "nacionalidad": getattr(
                usuario, "nacionalidad", ""
            ),
            "equipo": equipo.nombre,
            "codigo_equipo": equipo.codigo,
            "id_categoria": equipo.id_categoria_id,
            "categoria": equipo.id_categoria.nombre,
            "supervisor": (
                f"{supervisor.id_usuario.nombres} "
                f"{supervisor.id_usuario.apellidos}"
                if supervisor and supervisor.id_usuario
                else "No disponible"
            ),
            "cantidad_asignada": asignacion.cantidad_asignada,
            "cantidad_devuelta": asignacion.cantidad_devuelta,
            "cantidad_en_posesion": (
                asignacion.cantidad_asignada
                - asignacion.cantidad_devuelta
            ),
            "estado": asignacion.get_estado_display(),
            "motivo_incidencia": asignacion.get_motivo_incidencia_display(),
            "fecha_entrega": (
                timezone.localtime(
                    asignacion.fecha_entrega
                ).strftime("%d/%m/%Y %H:%M")
                if asignacion.fecha_entrega
                else "No registrada"
            ),
            "observacion": (
                asignacion.observacion or "Sin observaciones"
            )
        })

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin asignaciones",
            "descripcion": (
                "No existen asignaciones de equipos "
                "que coincidan con los filtros seleccionados."
            ),
            "icon": "warning",
            "asignaciones": []
        })

    return JsonResponse({
        "estado": "exito",
        "asignaciones": datos
    })

def datos_asignacion_admin(request):
    if request.method == "POST":
        id_asignacion = request.POST.get("id_asignacion", "").strip()

        if not id_asignacion.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Asignación inválida",
                "icon": "warning",
                "descripcion": "Debe seleccionar una asignación válida."
            })

        try:
            asignacion = (
                asignacion_equipo.objects
                .select_related(
                    "id_usuario",
                    "id_entrega",
                    "id_entrega__id_equipo",
                    "id_entrega__id_equipo__id_categoria"
                )
                .get(id_asignacion=int(id_asignacion))
            )

            usuario = asignacion.id_usuario
            equipo = asignacion.id_entrega.id_equipo

            fecha_entrega = (
                timezone.localtime(asignacion.fecha_entrega).strftime("%d/%m/%Y %H:%M:%S")
                if asignacion.fecha_entrega
                else "No registrada"
            )

            fecha_devolucion = (
                timezone.localtime(asignacion.fecha_devolucion).strftime("%d/%m/%Y %H:%M:%S")
                if asignacion.fecha_devolucion
                else "Pendiente"
            )

            return JsonResponse({
                "estado": "exito",
                "asignacion": {
                    "id_asignacion": asignacion.id_asignacion,
                    "empleado": f"{usuario.nombres} {usuario.apellidos}",
                    "cedula_empleado": usuario.cedula_identidad,
                    "nombre_equipo": equipo.nombre,
                    "codigo_equipo": equipo.codigo,
                    "categoria_equipo": equipo.id_categoria.nombre,
                    "fecha_entrega": fecha_entrega,
                    "fecha_devolucion": fecha_devolucion,
                    "cantidad_devuelto": asignacion.cantidad_devuelta,
                    "cantidad_equipo": asignacion.cantidad_asignada,
                    "estado_equipo": asignacion.get_estado_display()
                }
            })

        except asignacion_equipo.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Asignación no encontrada",
                "icon": "warning",
                "descripcion": "La asignación solicitada no existe."
            })

# REPORTES PDF

# LISTAR LOS EQUIPOS ASIGNADOS DEL EMPLEADO PARA GENERAR PDF

def lista_asignaciones_pdf(request):
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "No se encontró la identificación del supervisor.",
            "icon": "warning"
        })

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "No se encontró un supervisor activo asociado a la sesión.",
            "icon": "warning"
        })

    id_turno = supervisor.id_turno_id
    categoria = request.POST.get("categoria", "").strip()

    asignaciones = (
        asignacion_equipo.objects
        .filter(
            id_entrega__supervisor_encargado=supervisor,
            id_entrega__supervisor_encargado__id_turno_id=id_turno
        )
        .select_related(
            "id_usuario",
            "id_entrega",
            "id_entrega__supervisor_encargado",
            "id_entrega__id_equipo",
            "id_entrega__id_equipo__id_categoria"
        )
        .order_by("-fecha_entrega")
    )

    if categoria:
        asignaciones = asignaciones.filter(
            id_entrega__id_equipo__id_categoria_id=categoria
        )

    datos = []

    for asignacion in asignaciones:
        usuario = asignacion.id_usuario
        equipo = asignacion.id_entrega.id_equipo

        datos.append({
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "cedula": usuario.cedula_identidad,
            "equipo": equipo.nombre,
            "codigo": equipo.codigo,
            "categoria": equipo.id_categoria.nombre,
            "fecha_entrega": (
                timezone.localtime(asignacion.fecha_entrega).strftime("%d/%m/%Y %H:%M")
                if asignacion.fecha_entrega
                else ""
            ),
            "fecha_devolucion": (
                timezone.localtime(asignacion.fecha_devolucion).strftime("%d/%m/%Y %H:%M")
                if asignacion.fecha_devolucion
                else "Pendiente"
            ),
            "cantidad": asignacion.cantidad_asignada,
            "estado": asignacion.get_estado_display(),
        })

    # RESPUESTA PDF
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="lista_asignaciones_equipos.pdf"'
    )

    estilo_encabezado = ParagraphStyle(
        "estilo_encabezado",
        fontName="Times-Bold",
        fontSize=9,
        leading=10,
        alignment=1,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "estilo_celda",
        fontName="Times-Roman",
        fontSize=8,
        leading=9,
        alignment=1,
        wordWrap="CJK"
    )

    estilo_mensaje = ParagraphStyle(
        "estilo_mensaje",
        fontName="Times-Bold",
        fontSize=11,
        leading=14,
        alignment=1
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=25,
        leftMargin=25,
        topMargin=130,
        bottomMargin=30
    )

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    # DATOS TABLA
    datos_tabla = [
        [
            Paragraph(
                "LISTA DE EQUIPOS ASIGNADOS",
                estilo_encabezado
            ),
            "",
            "",
            "",
            "",
            ""
        ],
        [
            Paragraph("ID", estilo_encabezado),
            Paragraph("SUPERVISOR ENCARGADO", estilo_encabezado),
            Paragraph("EQUIPO", estilo_encabezado),
            Paragraph("FECHA ENTREGA", estilo_encabezado),
            Paragraph("FECHA DEVOLUCIÓN", estilo_encabezado),
            Paragraph("ESTADO", estilo_encabezado),
        ],
    ]

    if datos:
        for numero, dato in enumerate(datos, start=1):
            datos_tabla.append([
                Paragraph(str(numero), estilo_celda),
                Paragraph(
                    f"{dato['nombres']} {dato['apellidos']}",
                    estilo_celda
                ),
                Paragraph(dato["equipo"], estilo_celda),
                Paragraph(dato["fecha_entrega"], estilo_celda),
                Paragraph(dato["fecha_devolucion"], estilo_celda),
                Paragraph(dato["estado"], estilo_celda),
            ])
    else:
        datos_tabla.append([
            Paragraph(
                "No se encontraron registros de equipos asignados para la categoría seleccionada.",
                estilo_mensaje
            ),
            "",
            "",
            "",
            "",
            ""
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[
            35,
            140,
            105,
            95,
            95,
            70
        ],
        repeatRows=2
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 8),
        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    # ELEMENTOS
    elementos = [tabla]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_lista_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_lista_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_lista_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    # LOGO
    x_logo = 30
    y_logo = letter[1] - 150

    ancho_logo = 160
    alto_logo = 160

    canvas.drawImage(
        ruta_logo,
        x_logo,
        y_logo,
        width=ancho_logo,
        height=alto_logo,
        preserveAspectRatio=True,
        mask="auto"
    )

    # TITULO EMPRESA
    x_titulo = 185
    y_titulo = letter[1] - 80

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))

    canvas.drawString(
        x_titulo,
        y_titulo,
        "EMPRESA HIELO CAIPE C.A"
    )

    # FECHA EN ESPAÑOL
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]

    fecha = timezone.now()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    # FECHA
    x_fecha = 210
    y_fecha = letter[1] - 120

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(colors.HexColor("#072F3F"))

    canvas.drawString(
        x_fecha,
        y_fecha,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

# DATOS DE LA ASIGNACION DEL EQUIPO PARA GENERAR PDF

def datos_asignacion_pdf(request):
    id_asignacion = request.POST.get("id_asignacion", "").strip()

    if not id_asignacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "No se indicó la asignación.",
            "icon": "error"
        })

    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "No se encontró la identificación del supervisor.",
            "icon": "warning"
        })

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "No se encontró un supervisor activo asociado a la sesión.",
            "icon": "warning"
        })

    id_turno = supervisor.id_turno_id

    try:
        asignacion = (
            asignacion_equipo.objects
            .select_related(
                "id_usuario",
                "id_entrega",
                "id_entrega__supervisor_encargado",
                "id_entrega__id_equipo",
                "id_entrega__id_equipo__id_categoria"
            )
            .get(
                id_asignacion=id_asignacion,
                id_entrega__supervisor_encargado=supervisor,
                id_entrega__supervisor_encargado__id_turno_id=id_turno
            )
        )

    except asignacion_equipo.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Asignación no encontrada",
            "descripcion": "La asignación no existe o no corresponde al supervisor autenticado y su turno.",
            "icon": "error"
        })

    usuario = asignacion.id_usuario
    equipo = asignacion.id_entrega.id_equipo

    datos_asignacion = [
        ["Empleado:", f"{usuario.nombres} {usuario.apellidos}"],
        ["Cédula de Identidad:", usuario.cedula_identidad],
        ["Equipo:", equipo.nombre],
        ["Código del Equipo:", equipo.codigo],
        ["Categoría:", equipo.id_categoria.nombre],
        ["Cantidad:", str(asignacion.cantidad_asignada)],
        [
            "Fecha de Entrega:",
            timezone.localtime(asignacion.fecha_entrega).strftime("%d/%m/%Y %H:%M")
            if asignacion.fecha_entrega else ""
        ],
        [
            "Fecha de Devolución:",
            timezone.localtime(asignacion.fecha_devolucion).strftime("%d/%m/%Y %H:%M")
            if asignacion.fecha_devolucion else "Pendiente"
        ],
        ["Estado:", asignacion.get_estado_display()],
        ["Observación:", asignacion.observacion or "Sin observación"],
    ]

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="asignacion_{asignacion.id_asignacion}.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=110,
        bottomMargin=30
    )

    datos_tabla = [["DATOS DE LA ASIGNACIÓN", ""]]
    datos_tabla.extend(datos_asignacion)

    tabla = Table(
        datos_tabla,
        colWidths=[150, 340],
        splitByRow=1
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
        ("FONTNAME", (0, 1), (0, -1), "Times-Bold"),
        ("FONTSIZE", (0, 1), (0, -1), 10),

        ("FONTNAME", (1, 1), (1, -1), "Times-Roman"),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.black),
        ("FONTSIZE", (1, 1), (1, -1), 10),

        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    documento.build(
        [tabla],
        onFirstPage=lambda canvas, documento:
            encabezado_datos_pdf(canvas, documento, ruta_logo),
        onLaterPages=lambda canvas, documento:
            encabezado_datos_pdf(canvas, documento, ruta_logo)
    )

    return response

def encabezado_datos_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    # LOGO
    x_logo = 30
    y_logo = letter[1] - 135

    ancho_logo = 140
    alto_logo = 140

    canvas.drawImage(ruta_logo, x_logo, y_logo, width=ancho_logo, height=alto_logo, preserveAspectRatio=True, mask="auto")

    # TITULO EMPRESA
    x_titulo = 185
    y_titulo = letter[1] - 70

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))
    canvas.drawString(x_titulo, y_titulo, "EMPRESA HIELO CAIPE C.A")

    # FECHA EN ESPAÑOL
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]

    fecha = timezone.now()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    # FECHA
    x_fecha = 210
    y_fecha = letter[1] - 110

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(colors.HexColor("#072F3F"))

    canvas.drawString(
        x_fecha,
        y_fecha,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

# LISTA DE ASIGNACIONES PARA EL ADMINISTRADOR

def lista_asignaciones_pdf_admin(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": (
                "Esta operación requiere una solicitud POST."
            ),
            "icon": "warning"
        }, status=405)

    nacionalidad = request.POST.get("nacionalidad", "").strip()
    cedula = request.POST.get("cedula_identidad", "").strip()
    categoria = request.POST.get("categorias_registradas", "").strip()

    asignaciones = (
        asignacion_equipo.objects
        .select_related(
            "id_usuario",
            "id_entrega",
            "id_entrega__id_equipo",
            "id_entrega__id_equipo__id_categoria",
            "id_entrega__supervisor_encargado",
            "id_entrega__supervisor_encargado__id_usuario"
        )
        .exclude(estado="FINALIZADO")
        .order_by("-fecha_entrega")
    )

    if nacionalidad:
        asignaciones = asignaciones.filter(
            id_usuario__nacionalidad__iexact=nacionalidad
        )

    if cedula:
        asignaciones = asignaciones.filter(
            id_usuario__cedula_identidad__icontains=cedula
        )

    if categoria:
        if not categoria.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Categoría inválida",
                "descripcion": (
                    "La categoría de equipo seleccionada "
                    "no es válida."
                ),
                "icon": "warning"
            })

        asignaciones = asignaciones.filter(
            id_entrega__id_equipo__id_categoria_id=int(categoria)
        )

    if not asignaciones.exists():
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin asignaciones",
            "descripcion": (
                "No existen asignaciones de equipos "
                "que coincidan con los filtros seleccionados."
            ),
            "icon": "warning"
        })

    datos = []

    for asignacion in asignaciones:
        usuario = asignacion.id_usuario
        entrega = asignacion.id_entrega
        equipo = entrega.id_equipo

        supervisor = entrega.supervisor_encargado

        nombre_supervisor = (
            f"{supervisor.id_usuario.nombres} "
            f"{supervisor.id_usuario.apellidos}"
            if supervisor and supervisor.id_usuario
            else "No disponible"
        )

        fecha_entrega = (
            timezone.localtime(
                asignacion.fecha_entrega
            ).strftime("%d/%m/%Y %H:%M")
            if asignacion.fecha_entrega
            else "No registrada"
        )

        cantidad_asignada = asignacion.cantidad_asignada
        cantidad_devuelta = asignacion.cantidad_devuelta

        datos.append({
            "id": asignacion.id_asignacion,
            "empleado": (
                f"{usuario.nombres} {usuario.apellidos}"
            ),
            "cedula": (
                f"{getattr(usuario, 'nacionalidad', '')}"
                f"{usuario.cedula_identidad}"
            ),
            "supervisor": nombre_supervisor,
            "equipo": equipo.nombre,
            "categoria": (
                equipo.id_categoria.nombre
                if equipo.id_categoria
                else "Sin categoría"
            ),
            "asignada": cantidad_asignada,
            "devuelta": cantidad_devuelta,
            "posesion": (
                cantidad_asignada - cantidad_devuelta
            ),
            "estado": asignacion.get_estado_display(),
            "fecha_entrega": fecha_entrega
        })

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="reporte_general_asignaciones.pdf"'
    )

    estilo_titulo = ParagraphStyle(
        "estilo_titulo",
        fontName="Times-Bold",
        fontSize=13,
        leading=15,
        alignment=1,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "estilo_encabezado",
        fontName="Times-Bold",
        fontSize=7,
        leading=8,
        alignment=1,
        textColor=colors.white,
        wordWrap="CJK"
    )

    estilo_celda = ParagraphStyle(
        "estilo_celda",
        fontName="Times-Roman",
        fontSize=7,
        leading=8,
        alignment=1,
        textColor=colors.black,
        wordWrap="CJK"
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=25,
        leftMargin=25,
        topMargin=120,
        bottomMargin=30
    )

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    datos_tabla = [
        [
            Paragraph(
                "REPORTE GENERAL DE ASIGNACIONES DE EQUIPOS",
                estilo_titulo
            ),
            "", "", "", "", "", "", "", "", "", ""
        ],
        [
            Paragraph("ID", estilo_encabezado),
            Paragraph("EMPLEADO", estilo_encabezado),
            Paragraph("CÉDULA", estilo_encabezado),
            Paragraph("SUPERVISOR", estilo_encabezado),
            Paragraph("EQUIPO", estilo_encabezado),
            Paragraph("CATEGORÍA", estilo_encabezado),
            Paragraph("ASIGNADA", estilo_encabezado),
            Paragraph("DEVUELTA", estilo_encabezado),
            Paragraph("EN POSESIÓN", estilo_encabezado),
            Paragraph("ESTADO", estilo_encabezado),
            Paragraph("FECHA DE ENTREGA", estilo_encabezado),
        ]
    ]

    for dato in datos:
        datos_tabla.append([
            Paragraph(
                escape(str(dato["id"])),
                estilo_celda
            ),
            Paragraph(
                escape(dato["empleado"]),
                estilo_celda
            ),
            Paragraph(
                escape(dato["cedula"]),
                estilo_celda
            ),
            Paragraph(
                escape(dato["supervisor"]),
                estilo_celda
            ),
            Paragraph(
                escape(dato["equipo"]),
                estilo_celda
            ),
            Paragraph(
                escape(dato["categoria"]),
                estilo_celda
            ),
            Paragraph(
                str(dato["asignada"]),
                estilo_celda
            ),
            Paragraph(
                str(dato["devuelta"]),
                estilo_celda
            ),
            Paragraph(
                str(dato["posesion"]),
                estilo_celda
            ),
            Paragraph(
                escape(dato["estado"]),
                estilo_celda
            ),
            Paragraph(
                escape(dato["fecha_entrega"]),
                estilo_celda
            )
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[
            25, 100, 60, 90, 85, 65,
            38, 38, 48, 65, 80
        ],
        repeatRows=2,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        ("BACKGROUND", (0, 1), (-1, 1),
         colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 7),
        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))

    elementos = [tabla]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_lista_admin_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_lista_admin_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_lista_admin_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    # LOGO
    ancho_pagina, alto_pagina = documento.pagesize
    x_logo = 80
    y_logo = alto_pagina - 160

    ancho_logo = 180
    alto_logo = 180

    canvas.drawImage(
        ruta_logo,
        x_logo,
        y_logo,
        width=ancho_logo,
        height=alto_logo,
        preserveAspectRatio=True,
        mask="auto"
    )

    # TITULO EMPRESA
    x_titulo = 270
    y_titulo = alto_pagina - 80

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))

    canvas.drawString(
        x_titulo,
        y_titulo,
        "EMPRESA HIELO CAIPE C.A"
    )

    # FECHA EN ESPAÑOL
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]

    fecha = timezone.now()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    # FECHA
    x_fecha = 300
    y_fecha = alto_pagina - 120

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(colors.HexColor("#072F3F"))

    canvas.drawString(
        x_fecha,
        y_fecha,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

def detalle_asignacion_pdf_admin(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": (
                "Esta operación requiere una solicitud POST."
            ),
            "icon": "warning"
        }, status=405)

    id_asignacion = request.POST.get("id_asignacion", "").strip()

    if not id_asignacion.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Asignación inválida",
            "descripcion": (
                "Debe seleccionar una asignación válida."
            ),
            "icon": "warning"
        })

    try:
        asignacion = (
            asignacion_equipo.objects
            .select_related(
                "id_usuario",
                "id_entrega",
                "id_entrega__id_equipo",
                "id_entrega__id_equipo__id_categoria",
                "id_entrega__supervisor_encargado",
                "id_entrega__supervisor_encargado__id_usuario"
            )
            .get(id_asignacion=int(id_asignacion))
        )

    except asignacion_equipo.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Asignación no encontrada",
            "descripcion": (
                "La asignación solicitada no existe."
            ),
            "icon": "warning"
        })

    usuario = asignacion.id_usuario
    entrega = asignacion.id_entrega
    equipo = entrega.id_equipo
    supervisor = entrega.supervisor_encargado

    nombre_empleado = (
        f"{usuario.nombres} {usuario.apellidos}"
    )

    cedula_empleado = (
        f"{getattr(usuario, 'nacionalidad', '')}"
        f"{usuario.cedula_identidad}"
    )

    nombre_supervisor = (
        f"{supervisor.id_usuario.nombres} "
        f"{supervisor.id_usuario.apellidos}"
        if supervisor and supervisor.id_usuario
        else "No disponible"
    )

    fecha_entrega = (
        timezone.localtime(
            asignacion.fecha_entrega
        ).strftime("%d/%m/%Y %H:%M:%S")
        if asignacion.fecha_entrega
        else "No registrada"
    )

    fecha_devolucion = (
        timezone.localtime(
            asignacion.fecha_devolucion
        ).strftime("%d/%m/%Y %H:%M:%S")
        if asignacion.fecha_devolucion
        else "Pendiente"
    )

    categoria = (
        equipo.id_categoria.nombre
        if equipo.id_categoria
        else "Sin categoría"
    )

    cantidad_asignada = asignacion.cantidad_asignada
    cantidad_devuelta = asignacion.cantidad_devuelta

    datos_asignacion = [    
        ("Empleado:", nombre_empleado),
        ("Cédula de identidad:", cedula_empleado),
        ("Supervisor encargado:", nombre_supervisor),
        ("Equipo:", equipo.nombre),
        ("Código del equipo:", equipo.codigo),
        ("Categoría:", categoria),
        ("Cantidad asignada:", cantidad_asignada),
        ("Cantidad devuelta:", cantidad_devuelta),
        (
            "Cantidad en posesión:",
            cantidad_asignada - cantidad_devuelta
        ),
        ("Fecha de entrega:", fecha_entrega),
        ("Fecha de devolución:", fecha_devolucion),
        ("Estado:", asignacion.get_estado_display()),
        (
            "Observación:",
            asignacion.observacion or "Sin observaciones"
        ),
    ]

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="detalle_asignacion_'
        f'{asignacion.id_asignacion}.pdf"'
    )

    estilo_titulo = ParagraphStyle(
        "estilo_titulo",
        fontName="Times-Bold",
        fontSize=13,
        leading=16,
        alignment=1,
        textColor=colors.white
    )

    estilo_etiqueta = ParagraphStyle(
        "estilo_etiqueta",
        fontName="Times-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white,
        wordWrap="CJK"
    )

    estilo_valor = ParagraphStyle(
        "estilo_valor",
        fontName="Times-Roman",
        fontSize=9,
        leading=12,
        textColor=colors.black,
        wordWrap="CJK"
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=90,
        bottomMargin=30
    )

    datos_tabla = [
        [
            Paragraph(
                "DETALLE DE LA ASIGNACIÓN DE EQUIPO",
                estilo_titulo
            ),
            ""
        ]
    ]

    for etiqueta, valor in datos_asignacion:
        datos_tabla.append([
            Paragraph(
                escape(str(etiqueta)),
                estilo_etiqueta
            ),
            Paragraph(
                escape(str(valor)),
                estilo_valor
            )
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[165, 355],
        repeatRows=1,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("BACKGROUND", (0, 1), (0, -1),
         colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (0, -1), colors.white),

        ("BACKGROUND", (1, 1), (1, -1), colors.white),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.black),

        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    documento.build(
        [tabla],
        onFirstPage=lambda canvas, documento:
            encabezado_detalle_asignacion_admin_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_detalle_asignacion_admin_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_detalle_asignacion_admin_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    # LOGO
    ancho_pagina, alto_pagina = documento.pagesize
    x_logo = 30
    y_logo = alto_pagina - 125

    ancho_logo = 160
    alto_logo = 160

    canvas.drawImage(ruta_logo, x_logo, y_logo, width=ancho_logo, height=alto_logo, preserveAspectRatio=True, mask="auto")

    # TITULO EMPRESA
    x_titulo = 180
    y_titulo = alto_pagina - 50

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))
    canvas.drawString(x_titulo, y_titulo, "EMPRESA HIELO CAIPE C.A")

    # FECHA EN ESPAÑOL
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]

    fecha = timezone.now()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    # FECHA
    x_fecha = 205
    y_fecha = alto_pagina - 90

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(colors.HexColor("#072F3F"))

    canvas.drawString(
        x_fecha,
        y_fecha,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()
