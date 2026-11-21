from django.shortcuts import render
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, F, IntegerField, ExpressionWrapper, Exists, OuterRef
from django.conf import settings

from inicio_sesion.models import usuarios, bitacora, encargados_administrativos, supervisores_encargados

from asignaciones.models import asignacion_equipo, categoria_equipo, equipos, historial_entrega_equipo, entrega_equipos, historial_inventario_equipo

import os
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter, landscape

# ENTREGA DE EQUIPOS A LOS SUPERVISORES ENCARGADOS

# FILTRO O DATOS REGISTRAR O BUSCAR

def supervisores_registrados(request):
    try:
        supervisores = supervisores_encargados.objects.filter(
            vigencia=True
        ).select_related(
            "id_usuario",
            "id_turno"
        ).order_by(
            "id_turno__nombre",
            "id_usuario__nombres"
        )

        datos = [
            {
                "id_supervisor": supervisor.id_supervisor,
                "id_usuario": supervisor.id_usuario.id_usuario,
                "nombres": supervisor.id_usuario.nombres,
                "apellidos": supervisor.id_usuario.apellidos,
                "nombre_completo": (
                    f"{supervisor.id_usuario.nombres} "
                    f"{supervisor.id_usuario.apellidos}"
                ),
                "cedula": supervisor.id_usuario.cedula_identidad,
                "turno": supervisor.id_turno.nombre,
                "id_turno": supervisor.id_turno.id_turno,
                "vigencia": supervisor.vigencia
            }
            for supervisor in supervisores
        ]

        return JsonResponse({
            "estado": "exito",
            "supervisores": datos,
            "total": len(datos)
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": (
                "Ocurrio un error al momento de visualizar los supervisores"
                f" {e}"
            ),
            "icon": "warning"
        })

def categorias_equipos_entregados(request):
    if request.method == "POST":
        id_supervisor = request.POST.get("supervisores_encargados", "").strip()

        if not id_supervisor:
            return JsonResponse({
                "estado": "fallo",
                "title": "Campo requerido",
                "descripcion": "Debe seleccionar un supervisor.",
                "icon": "warning"
            })

        if not id_supervisor.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Dato inválido",
                "descripcion": "El supervisor seleccionado no es válido.",
                "icon": "warning"
            })

        categorias = (
            categoria_equipo.objects
            .filter(
                equipos__entregas_supervisores__supervisor_encargado_id=int(id_supervisor),
                equipos__entregas_supervisores__estado="ASIGNADO"
            )
            .distinct()
            .order_by("nombre")
        )

        datos = [
            {
                "id_categoria": categoria.id_categoria,
                "nombre": categoria.nombre
            }
            for categoria in categorias
        ]

        return JsonResponse({
            "estado": "exito",
            "categorias": datos
        })

def equipos_entregados(request):

    id_supervisor = request.POST.get("supervisor", "").strip()
    id_categoria = request.POST.get("categoria", "").strip()

    if not id_supervisor.isdigit() or not id_categoria.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos inválidos",
            "descripcion": "Debe seleccionar un supervisor y una categoría válidos.",
            "icon": "warning"
        })

    entregas = (
        entrega_equipos.objects
        .select_related(
            "id_equipo",
            "id_equipo__id_categoria"
        )
        .filter(
            supervisor_encargado_id=int(id_supervisor),
            id_equipo__id_categoria_id=int(id_categoria),
            estado="ASIGNADO"
        )
        .exclude(
            motivo_incidencia="ERROR_HUMANO"
        )
        .order_by("-fecha_entrega")
    )

    datos = []

    for entrega in entregas:
        resultado = entrega.asignaciones_personal.aggregate(
            cantidad_asignada=Sum(
                ExpressionWrapper(
                    F("cantidad_asignada") - F("cantidad_devuelta"),
                    output_field=IntegerField()
                )
            )
        )

        cantidad_asignada = max(
            0,
            resultado["cantidad_asignada"] or 0
        )

        cantidad_entregada = entrega.cantidad_entregada

        cantidad_disponible = max(
            0,
            cantidad_entregada - cantidad_asignada
        )

        datos.append({
            "id_entrega": entrega.id_entrega,
            "id_equipo": entrega.id_equipo_id,
            "nombre": entrega.id_equipo.nombre,
            "categoria": entrega.id_equipo.id_categoria.nombre,
            "cantidad_entregada": cantidad_entregada,
            "cantidad_asignada": cantidad_asignada,
            "cantidad_disponible": cantidad_disponible,
            "observacion": entrega.observacion or "",
            "estado": entrega.estado
        })

    if not datos:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin resultados",
            "descripcion": "No se encontraron equipos asignados al supervisor y la categoría seleccionados.",
            "icon": "info"
        })

    return JsonResponse({
        "estado": "exito",
        "equipos": datos
    })

def supervisores_entregado_equipos(request):
    supervisores = (
        supervisores_encargados.objects
        .filter(
            equipos_recibidos_supervisor__estado="ASIGNADO"
        )
        .select_related(
            "id_usuario",
            "id_turno"
        )
        .distinct()
        .order_by(
            "id_usuario__nombres",
            "id_usuario__apellidos"
        )
    )

    datos = [
        {
            "id_supervisor": supervisor.id_supervisor,
            "nombre": (
                f"{supervisor.id_usuario.nombres} "
                f"{supervisor.id_usuario.apellidos}"
            ),
            "cedula": supervisor.id_usuario.cedula_identidad,
            "turno": supervisor.id_turno.nombre
        }
        for supervisor in supervisores
    ]

    if not datos:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin resultados",
            "descripcion": "No hay supervisores con equipos en estado ASIGNADO.",
            "icon": "info"
        })

    return JsonResponse({
        "estado": "exito",
        "supervisores": datos
    })

# REGISTRAR EQUIPOS ENTREGADOS

def equipos_registrados(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    categoria = request.POST.get("categoria", "").strip()

    entregas_error_humano = entrega_equipos.objects.filter(
        id_equipo_id=OuterRef("pk"),
        motivo_incidencia="ERROR_HUMANO"
    )

    consulta = (
        equipos.objects
        .select_related("id_categoria")
        .annotate(
            tiene_error_humano=Exists(entregas_error_humano)
        )
        .filter(
            activo=True,
            cantidad_disponible__gt=0,
            tiene_error_humano=False
        )
        .order_by("nombre")
    )

    if categoria:
        if not categoria.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Categoría inválida",
                "descripcion": "La categoría seleccionada no es válida.",
                "icon": "warning"
            })

        consulta = consulta.filter(
            id_categoria_id=int(categoria)
        )

    datos = [
        {
            "id_equipo": equipo.id_equipo,
            "nombre": equipo.nombre,
            "codigo": equipo.codigo,
            "categoria": equipo.id_categoria.nombre,
            "cantidad_disponible": equipo.cantidad_disponible,
            "observacion": equipo.observacion or "",
            "fecha_registro": (
                equipo.fecha_registro.strftime("%d/%m/%Y %H:%M")
                if equipo.fecha_registro else ""
            )
        }
        for equipo in consulta
    ]

    return JsonResponse({
        "estado": "exito",
        "equipos": datos
    })

@transaction.atomic
def registrar_entrega_equipos(request):
    if request.method != "POST":
        return render(request, "Entrega_Equipos/Administrador/registrar_entrega.html")

    cedula_administrador = request.session.get("cedula_identidad")

    id_supervisor = request.POST.get("supervisores_encargados", "").strip()
    id_categoria = request.POST.get("categoria_equipos", "").strip()
    id_equipo = request.POST.get("equipos_entregar", "").strip()
    cantidad_texto = request.POST.get("cantidad_equipo", "").strip()
    observacion = request.POST.get("observacion_entrega", "").strip()

    if not cedula_administrador:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al usuario actual. Inicie sesión nuevamente.",
            "icon": "error"
        })

    if not id_supervisor or not id_categoria or not id_equipo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "descripcion": "Debe seleccionar el supervisor, la categoría y el equipo.",
            "icon": "warning"
        })

    if not cantidad_texto.isdigit() or int(cantidad_texto) <= 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cantidad inválida",
            "descripcion": "La cantidad a entregar debe ser un número entero mayor que cero.",
            "icon": "warning"
        })

    cantidad = int(cantidad_texto)

    if not observacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Observación requerida",
            "descripcion": "Debe indicar la observación de la entrega.",
            "icon": "warning"
        })

    administrador = (
        encargados_administrativos.objects
        .filter(
            id_usuario__cedula_identidad=cedula_administrador,
            vigencia=True
        )
        .first()
    )

    if not administrador:
        return JsonResponse({
            "estado": "fallo",
            "title": "Acceso no autorizado",
            "descripcion": "El usuario actual no corresponde a un encargado administrativo vigente.",
            "icon": "error"
        })

    supervisor = (
        supervisores_encargados.objects
        .filter(
            id_supervisor=id_supervisor,
            vigencia=True
        )
        .first()
    )

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no válido",
            "descripcion": "El Supervisor Encargado seleccionado no existe o está inhabilitado.",
            "icon": "warning"
        })

    equipo = (
        equipos.objects
        .select_for_update()
        .filter(
            id_equipo=id_equipo,
            id_categoria=id_categoria,
            activo=True
        )
        .first()
    )

    if not equipo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Equipo no válido",
            "descripcion": "El equipo no existe, está inactivo o no pertenece a la categoría seleccionada.",
            "icon": "warning"
        })

    cantidad_anterior = equipo.cantidad_disponible

    if cantidad > cantidad_anterior:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cantidad no disponible",
            "descripcion": (
                f"Solo hay {cantidad_anterior} "
                "unidad(es) disponible(s) de este equipo."
            ),
            "icon": "warning"
        })

    cantidad_nueva = cantidad_anterior - cantidad

    entrega = entrega_equipos.objects.create(
        supervisor_encargado=supervisor,
        id_equipo=equipo,
        cantidad_entregada=cantidad,
        cantidad_disponible=cantidad,
        observacion=observacion,
        estado="ASIGNADO",
        motivo_incidencia="NINGUNA"
    )

    equipo.cantidad_disponible = cantidad_nueva
    equipo.save(update_fields=["cantidad_disponible"])

    historial_inventario_equipo.objects.create(
        id_equipo=equipo,
        tipo_movimiento="ENTREGA",
        cantidad_anterior=cantidad_anterior,
        cantidad_movimiento=-cantidad,
        cantidad_nueva=cantidad_nueva,
        activo_anterior=equipo.activo,
        activo_nuevo=equipo.activo,
        observacion=(
            f"Entrega de {cantidad} unidad(es) al supervisor "
            f"{supervisor.id_usuario.nombres} "
            f"{supervisor.id_usuario.apellidos}. "
            f"Entrega registrada con ID {entrega.pk}. "
            f"Observación: {observacion}"
        )
    )

    info_usuario = administrador.id_usuario

    bitacora.objects.create(
        id_usuario=info_usuario,
        nombre_modulo="Entrega de equipos",
        cargo_usuario=request.session.get("perfil", "No especificado"),
        accion=(
            f"Entrega de {cantidad} unidad(es) del equipo "
            f"{equipo.nombre} ({equipo.codigo}) al supervisor "
            f"{supervisor.id_usuario.nombres} "
            f"{supervisor.id_usuario.apellidos}. "
            f"Cantidad disponible anterior: {cantidad_anterior}; "
            f"cantidad entregada: {cantidad}; "
            f"cantidad disponible actual: {cantidad_nueva}. "
            f"ID de entrega: {entrega.pk}. "
            f"Observación: {observacion}."
        )
    )

    return JsonResponse({
        "estado": "exito",
        "title": "Entrega registrada",
        "descripcion": (
            "La entrega del equipo fue registrada correctamente "
            "y el movimiento quedó guardado en el historial del inventario."
        ),
        "icon": "success"
    })

# EQUIPO ENTREGADOS REGISTRADOS

def entregas_equipos_registradas(request):
    if request.method == "POST":
        categoria = request.POST.get("categoria", "").strip()
        supervisor = request.POST.get("supervisor", "").strip()

        entregas = (
            entrega_equipos.objects
            .all()
            .select_related(
                "supervisor_encargado__id_usuario",
                "supervisor_encargado__id_turno",
                "id_equipo",
                "id_equipo__id_categoria"
            )
        )

        if categoria:
            entregas = entregas.filter(
                id_equipo__id_categoria_id=categoria
            )

        if supervisor:
            entregas = entregas.filter(
                supervisor_encargado_id=supervisor
            )

        entregas = entregas.order_by("-fecha_entrega")

        datos = []

        for entrega in entregas:
            datos.append({
                "id_entrega": entrega.id_entrega,
                "supervisor_encargado": (
                    f"{entrega.supervisor_encargado.id_usuario.nombres} "
                    f"{entrega.supervisor_encargado.id_usuario.apellidos}"
                ),
                "turno": entrega.supervisor_encargado.id_turno.nombre,
                "equipo": entrega.id_equipo.nombre,
                "codigo_equipo": entrega.id_equipo.codigo,
                "cantidad_entregada": entrega.cantidad_entregada,
                "cantidad_disponible": entrega.cantidad_disponible,
                "fecha_entrega": (
                    entrega.fecha_entrega.strftime("%d/%m/%Y %H:%M")
                    if entrega.fecha_entrega else ""
                ),
                "observacion": entrega.observacion or "",
                "estado": entrega.estado,
                "motivo_incidencia": entrega.motivo_incidencia
            })

        return JsonResponse({
            "estado": "exito",
            "entregas": datos
        })

def busca_entrega_equipos(request):
    if request.method == "POST":
        id_entrega = request.POST.get("id_entrega", "").strip()

        if not id_entrega:
            return JsonResponse({
                "estado": "fallo",
                "title": "Dato requerido",
                "descripcion": "No se indicó la entrega que desea consultar.",
                "icon": "warning"
            })

        try:
            entrega = (
                entrega_equipos.objects
                .select_related(
                    "supervisor_encargado__id_usuario",
                    "supervisor_encargado__id_turno",
                    "id_equipo",
                    "id_equipo__id_categoria"
                )
                .get(id_entrega=id_entrega)
            )

            return JsonResponse({
                "estado": "exito",
                "entrega": {
                    "id_entrega": entrega.id_entrega,
                    "supervisor_encargado": (
                        f"{entrega.supervisor_encargado.id_usuario.nombres} "
                        f"{entrega.supervisor_encargado.id_usuario.apellidos}"
                    ),
                    "cedula_supervisor": (
                        entrega.supervisor_encargado.id_usuario.cedula_identidad
                    ),
                    "turno": entrega.supervisor_encargado.id_turno.nombre,
                    "equipo": entrega.id_equipo.nombre,
                    "codigo_equipo": entrega.id_equipo.codigo,
                    "categoria": entrega.id_equipo.id_categoria.nombre,
                    "cantidad_entregada": entrega.cantidad_entregada,
                    "cantidad_disponible": entrega.cantidad_disponible,
                    "fecha_entrega": (
                        entrega.fecha_entrega.strftime("%d/%m/%Y %H:%M")
                        if entrega.fecha_entrega else ""
                    ),
                    "observacion": entrega.observacion or "",
                    "estado": entrega.estado,
                    "motivo_incidencia": entrega.motivo_incidencia
                }
            })

        except entrega_equipos.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Entrega no encontrada",
                "descripcion": "La entrega solicitada no existe.",
                "icon": "warning"
            })

        except (ValueError, TypeError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Identificador inválido",
                "descripcion": "El identificador de la entrega no es válido.",
                "icon": "warning"
            })

def visualizar_entrega_equipos(request):
    return render(request, "Entrega_Equipos/Administrador/visualizar_entrega.html")

# HISTORIAL ENTREGAS DE EQUIPOS

def historial_entregas_equipos(request):
    if request.method != "POST":
        return render(request, "Entrega_Equipos/Administrador/historial_entrega.html")

    id_supervisor = request.POST.get("supervisor", "").strip()
    id_categoria = request.POST.get("categoria", "").strip()

    try:

        historial = historial_entrega_equipo.objects.select_related(
            "entrega_equipo",
            "entrega_equipo__supervisor_encargado",
            "entrega_equipo__supervisor_encargado__id_usuario",
            "entrega_equipo__supervisor_encargado__id_turno",
            "entrega_equipo__id_equipo",
            "entrega_equipo__id_equipo__id_categoria"
        )

        if id_supervisor:

            if not id_supervisor.isdigit():
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Supervisor inválido",
                    "icon": "warning",
                    "descripcion": "Debe seleccionar un supervisor válido."
                })

            supervisor = supervisores_encargados.objects.filter(
                id_supervisor=int(id_supervisor)
            ).first()

            if not supervisor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Supervisor no encontrado",
                    "icon": "warning",
                    "descripcion": "El supervisor seleccionado no existe."
                })

            historial = historial.filter(
                entrega_equipo__supervisor_encargado=supervisor
            )

        if id_categoria:

            if not id_categoria.isdigit():
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Categoría inválida",
                    "icon": "warning",
                    "descripcion": "Debe seleccionar una categoría válida."
                })

            categoria = categoria_equipo.objects.filter(
                id_categoria=int(id_categoria)
            ).first()

            if not categoria:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Categoría no encontrada",
                    "icon": "warning",
                    "descripcion": "La categoría seleccionada no existe."
                })

            historial = historial.filter(
                entrega_equipo__id_equipo__id_categoria=categoria
            )

        historial = historial.order_by("-fecha_actualizacion")

        datos_historial = []

        for registro in historial:

            entrega = registro.entrega_equipo
            equipo = entrega.id_equipo
            supervisor = entrega.supervisor_encargado
            usuario = supervisor.id_usuario

            datos_historial.append({
                "id_historial": registro.id_historial,
                "equipo": equipo.nombre,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "turno": supervisor.id_turno.nombre,
           })

        return JsonResponse({
            "estado": "exito",
            "historial": datos_historial
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar historial",
            "icon": "error",
            "descripcion": "No fue posible obtener el historial de entregas. Intente nuevamente."
        })

def detalle_historial_entrega(request):
    id_historial = request.POST.get("id_historial", "").strip()

    if not id_historial:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato requerido",
            "icon": "warning",
            "descripcion": "No se recibió el identificador del historial."
        })

    if not id_historial.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "icon": "warning",
            "descripcion": "El identificador del historial no es válido."
        })

    try:
        historial = historial_entrega_equipo.objects.select_related(
            "entrega_equipo",
            "entrega_equipo__supervisor_encargado",
            "entrega_equipo__supervisor_encargado__id_usuario",
            "entrega_equipo__supervisor_encargado__id_turno",
            "entrega_equipo__id_equipo",
            "entrega_equipo__id_equipo__id_categoria"
        ).get(id_historial=int(id_historial))

        entrega = historial.entrega_equipo
        supervisor = entrega.supervisor_encargado
        usuario = supervisor.id_usuario
        equipo = entrega.id_equipo

        return JsonResponse({
            "estado": "exito",
            "historial": {
                "id_historial": historial.id_historial,
                "id_entrega": entrega.id_entrega,

                "supervisor": {
                    "id_supervisor": supervisor.id_supervisor,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula": usuario.cedula_identidad,
                    "turno": supervisor.id_turno.nombre
                },

                "equipo": {
                    "id_equipo": equipo.id_equipo,
                    "nombre": equipo.nombre,
                    "codigo": equipo.codigo,
                    "categoria": equipo.id_categoria.nombre
                },

                "cantidad_entregada_anterior": historial.cantidad_entregada_anterior,
                "cantidad_entregada_nueva": historial.cantidad_entregada_nueva,

                "cantidad_disponible_anterior": historial.cantidad_disponible_anterior,
                "cantidad_disponible_nueva": historial.cantidad_disponible_nueva,

                "estado_anterior": historial.estado_anterior,
                "estado_nuevo": historial.estado_nuevo,

                "motivo_incidencia_anterior": historial.motivo_incidencia_anterior,
                "motivo_incidencia_nuevo": historial.motivo_incidencia_nuevo,

                "observacion_anterior": historial.observacion_anterior,
                "observacion_nueva": historial.observacion_nueva,

                "motivo_actualizacion": historial.motivo_actualizacion,

                "fecha_actualizacion": historial.fecha_actualizacion.strftime("%d/%m/%Y")
            }
        })

    except historial_entrega_equipo.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Historial no encontrado",
            "icon": "warning",
            "descripcion": "El registro de historial solicitado no existe."
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar el historial",
            "icon": "error",
            "descripcion": "No fue posible obtener los detalles del historial. Intente nuevamente."
        })

# CORREGIR EL REGISTRO DEL EQUIPO ENTREGADO (ERROR_HUMANO)

def tipo_correccion(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "mensaje": "Método de solicitud no permitido."
        }, status=405)

    id_equipo = request.POST.get("id_equipo", "").strip()

    if not id_equipo or not id_equipo.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "mensaje": "Debe seleccionar un equipo válido."
        })

    try:
        equipo = equipos.objects.get(id_equipo=int(id_equipo))

        # Verificar si existen unidades asignadas pendientes de devolución.
        asignado = asignacion_equipo.objects.filter(
            id_entrega__id_equipo=equipo,
            cantidad_asignada__gt=F("cantidad_devuelta")
        ).exists()

        return JsonResponse({
            "estado": "exito",
            "asignado": asignado,
            "equipo": {
                "id_equipo": equipo.id_equipo,
                "nombre": equipo.nombre,
                "codigo": equipo.codigo,
                "cantidad_disponible": equipo.cantidad_disponible,
                "categoria": equipo.id_categoria.nombre
            },
            "mensaje": (
                "El equipo tiene unidades asignadas al personal."
                if asignado
                else "El equipo no tiene unidades asignadas al personal."
            )
        })

    except equipos.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "mensaje": "El equipo seleccionado no existe."
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "mensaje": f"No fue posible consultar el equipo: {str(e)}"
        })

def correccion_entrega_equipos(request):
    if request.method != "POST":
        return render(request, "Entrega_Equipos/Administrador/correccion_entrega.html")

    cedula_administrador = request.session.get("cedula_identidad")

    id_supervisor = request.POST.get("supervisores_encargados", "").strip()
    id_categoria = request.POST.get("categoria_equipos", "").strip()
    id_entrega = request.POST.get("equipos_entregados", "").strip()
    tipo_correccion = request.POST.get("tipo_correccion", "").strip()
    cantidad_actualizar = request.POST.get("cantidad_actualizar", "").strip()
    observacion_entrega = request.POST.get("observacion_entrega", "").strip()
    motivo_correccion = request.POST.get("motivo_correccion", "").strip()

    def respuesta(estado, title, descripcion, icon):
        return JsonResponse({
            "estado": estado,
            "title": title,
            "descripcion": descripcion,
            "icon": icon
        })

    if not cedula_administrador:
        return respuesta(
            "fallo",
            "Sesión expirada",
            "Debe iniciar sesión nuevamente.",
            "warning"
        )

    campos = [
        (id_supervisor, "Supervisor Encargado", "Debe seleccionar un supervisor encargado."),
        (id_categoria, "Categoría de equipo", "Debe seleccionar una categoría de equipo."),
        (id_entrega, "Equipo entregado", "Debe seleccionar una entrega."),
        (tipo_correccion, "Tipo de corrección", "Debe seleccionar el tipo de corrección."),
        (motivo_correccion, "Motivo de corrección", "Debe indicar el motivo de la corrección."),
        (cantidad_actualizar, "Cantidad a actualizar", "Debe ingresar la cantidad."),
        (observacion_entrega, "Observación", "Debe ingresar la observación de la entrega."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return respuesta(
                "fallo",
                campo,
                mensaje,
                "warning"
            )

    if not all(
        valor.isdigit()
        for valor in (
            id_supervisor,
            id_categoria,
            id_entrega
        )
    ):
        return respuesta(
            "fallo",
            "Datos inválidos",
            "Los identificadores seleccionados no son válidos.",
            "warning"
        )

    if tipo_correccion not in ("ACTUALIZAR", "ERROR_HUMANO", "RETIRAR"):
        return respuesta(
            "fallo",
            "Tipo de corrección inválido",
            "Seleccione un tipo de corrección válido.",
            "warning"
        )

    if not cantidad_actualizar.isdigit():
        return respuesta(
            "fallo",
            "Cantidad inválida",
            "Ingrese una cantidad entera válida.",
            "warning"
        )

    cantidad_nueva = int(cantidad_actualizar)

    if cantidad_nueva <= 0:
        return respuesta(
            "fallo",
            "Cantidad inválida",
            "La cantidad debe ser mayor que cero.",
            "warning"
        )

    try:
        with transaction.atomic():

            encargados_administrativos.objects.get(
                id_usuario__cedula_identidad=cedula_administrador
            )

            entrega = (
                entrega_equipos.objects
                .select_for_update()
                .select_related(
                    "id_equipo",
                    "supervisor_encargado"
                )
                .get(
                    id_entrega=int(id_entrega),
                    supervisor_encargado_id=int(id_supervisor),
                    id_equipo__id_categoria_id=int(id_categoria)
                )
            )

            if entrega.estado != "ASIGNADO":
                return respuesta(
                    "fallo",
                    "Entrega no disponible",
                    "Solo se pueden corregir entregas en estado ASIGNADO.",
                    "warning"
                )

            # Consultar las unidades que siguen asignadas al personal.
            asignaciones = (
                asignacion_equipo.objects
                .filter(
                    id_entrega=entrega,
                    cantidad_asignada__gt=F("cantidad_devuelta")
                )
                .aggregate(
                    pendiente=Sum(
                        ExpressionWrapper(
                            F("cantidad_asignada") - F("cantidad_devuelta"),
                            output_field=IntegerField()
                        )
                    )
                )
            )

            cantidad_asignada = asignaciones["pendiente"] or 0

            # Guardar los datos anteriores para el historial.
            cantidad_anterior = entrega.cantidad_entregada
            disponible_anterior = entrega.cantidad_disponible
            estado_anterior = entrega.estado
            motivo_incidencia_anterior = entrega.motivo_incidencia
            observacion_anterior = entrega.observacion

            if cantidad_asignada > cantidad_anterior:
                return respuesta(
                    "fallo",
                    "Inconsistencia en la entrega",
                    (
                        "Las unidades que siguen asignadas al personal "
                        "superan la cantidad registrada en la entrega. "
                        "Debe revisar los registros antes de corregirla."
                    ),
                    "error"
                )

            cantidad_disponible_calculada = (
                cantidad_anterior - cantidad_asignada
            )

            if entrega.cantidad_disponible > entrega.cantidad_entregada:
                return respuesta(
                    "fallo",
                    "Inconsistencia en la entrega",
                    (
                        "La cantidad disponible supera la cantidad "
                        "originalmente entregada. Debe revisar los registros."
                    ),
                    "error"
                )

            # ACTUALIZAR
            if tipo_correccion == "ACTUALIZAR":

                if cantidad_nueva < cantidad_asignada:
                    return respuesta(
                        "fallo",
                        "Cantidad insuficiente",
                        (
                            f"La cantidad no puede ser inferior a las "
                            f"{cantidad_asignada} unidades que siguen "
                            f"asignadas al personal."
                        ),
                        "warning"
                    )

                if cantidad_nueva > cantidad_anterior:
                    return respuesta(
                        "fallo",
                        "Cantidad excedida",
                        (
                            f"La cantidad no puede superar las "
                            f"{cantidad_anterior} unidades originalmente "
                            f"entregadas al supervisor."
                        ),
                        "warning"
                    )

                entrega.cantidad_entregada = cantidad_nueva
                entrega.cantidad_disponible = cantidad_nueva - cantidad_asignada
                entrega.observacion = observacion_entrega

                campos_actualizados = [
                    "cantidad_entregada",
                    "cantidad_disponible",
                    "observacion"
                ]

            # RETIRAR: devolver la entrega del supervisor al inventario.
            elif tipo_correccion == "RETIRAR":

                if cantidad_asignada > 0:
                    return respuesta(
                        "fallo",
                        "Equipo asignado al personal",
                        (
                            f"No se puede retirar la entrega porque existen "
                            f"{cantidad_asignada} unidades asignadas a empleados "
                            f"que todavía no han sido devueltas."
                        ),
                        "warning"
                    )

                equipo = (
                    equipos.objects
                    .select_for_update()
                    .get(pk=entrega.id_equipo_id)
                )

                cantidad_devolver = cantidad_disponible_calculada

                if cantidad_devolver <= 0:
                    return respuesta(
                        "fallo",
                        "Sin equipos para devolver",
                        "La entrega no tiene unidades disponibles para devolver al inventario.",
                        "warning"
                    )

                cantidad_inventario_anterior = equipo.cantidad_disponible

                equipo.cantidad_disponible = (
                    cantidad_inventario_anterior + cantidad_devolver
                )

                equipo.save(update_fields=["cantidad_disponible"])

                historial_inventario_equipo.objects.create(
                    id_equipo=equipo,
                    tipo_movimiento="CORRECCION",
                    cantidad_anterior=cantidad_inventario_anterior,
                    cantidad_movimiento=cantidad_devolver,
                    cantidad_nueva=equipo.cantidad_disponible,
                    observacion=(
                        f"Retiro de entrega al supervisor. "
                        f"Entrega #{entrega.id_entrega}. "
                        f"Motivo: {motivo_correccion}. "
                        f"Observación: {observacion_entrega}"
                    )
                )

                entrega.cantidad_entregada = 0
                entrega.cantidad_disponible = 0
                entrega.estado = "RETIRADO"
                entrega.observacion = observacion_entrega

                campos_actualizados = [
                    "cantidad_entregada",
                    "cantidad_disponible",
                    "estado",
                    "observacion"
                ]

            # ERROR_HUMANO: devolver las unidades por error de registro,
            # conservando el estado ASIGNADO.
            elif tipo_correccion == "ERROR_HUMANO":

                if cantidad_asignada > 0:
                    return respuesta(
                        "fallo",
                        "Equipo asignado al personal",
                        (
                            f"No se puede corregir por error humano porque "
                            f"existen {cantidad_asignada} unidades pendientes "
                            f"de devolución por parte del personal."
                        ),
                        "warning"
                    )

                equipo = (
                    equipos.objects
                    .select_for_update()
                    .get(pk=entrega.id_equipo_id)
                )

                cantidad_devolver = cantidad_disponible_calculada

                if cantidad_devolver <= 0:
                    return respuesta(
                        "fallo",
                        "Sin equipos para devolver",
                        "La entrega no tiene unidades disponibles para devolver.",
                        "warning"
                    )

                cantidad_inventario_anterior = equipo.cantidad_disponible

                equipo.cantidad_disponible = (
                    cantidad_inventario_anterior + cantidad_devolver
                )

                equipo.save(update_fields=["cantidad_disponible"])

                historial_inventario_equipo.objects.create(
                    id_equipo=equipo,
                    tipo_movimiento="CORRECCION",
                    cantidad_anterior=cantidad_inventario_anterior,
                    cantidad_movimiento=cantidad_devolver,
                    cantidad_nueva=equipo.cantidad_disponible,
                    observacion=(
                        f"Devolución al inventario por error humano. "
                        f"Entrega #{entrega.id_entrega}. "
                        f"Motivo: {motivo_correccion}. "
                        f"Observación: {observacion_entrega}"
                    )
                )

                entrega.cantidad_entregada = 0
                entrega.cantidad_disponible = 0
                entrega.estado = "RETIRADO"
                entrega.motivo_incidencia = "ERROR_HUMANO"
                entrega.observacion = observacion_entrega

                campos_actualizados = [
                    "cantidad_entregada",
                    "cantidad_disponible",
                    "estado",
                    "motivo_incidencia",
                    "observacion"
                ]

            # Registrar el historial de la corrección.
            historial_entrega_equipo.objects.create(
                entrega_equipo=entrega,
                cantidad_entregada_anterior=cantidad_anterior,
                cantidad_entregada_nueva=entrega.cantidad_entregada,
                cantidad_disponible_anterior=disponible_anterior,
                cantidad_disponible_nueva=entrega.cantidad_disponible,
                estado_anterior=estado_anterior,
                estado_nuevo=entrega.estado,
                motivo_incidencia_anterior=motivo_incidencia_anterior,
                motivo_incidencia_nuevo=entrega.motivo_incidencia,
                observacion_anterior=observacion_anterior,
                observacion_nueva=entrega.observacion,
                motivo_actualizacion=motivo_correccion
            )

            entrega.save(update_fields=campos_actualizados)

        return respuesta(
            "exito",
            "Corrección registrada",
            "La corrección se guardó correctamente en el historial.",
            "success"
        )

    except encargados_administrativos.DoesNotExist:
        return respuesta(
            "fallo",
            "Administrador no encontrado",
            "No se encontró el encargado administrativo de la sesión.",
            "error"
        )

    except entrega_equipos.DoesNotExist:
        return respuesta(
            "fallo",
            "Entrega no encontrada",
            (
                "La entrega no corresponde al supervisor y la "
                "categoría seleccionados."
            ),
            "warning"
        )

    except Exception as e:
        return respuesta(
            "fallo",
            "Error inesperado",
            (
                "No fue posible registrar la corrección. "
                f"Intente nuevamente. {e}"
            ),
            "error"
        )

# REPORTES PDF

def datos_entrega_equipo_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    id_entrega = request.POST.get("id_entrega", "").strip()

    if not id_entrega:
        return JsonResponse({
            "estado": "fallo",
            "title": "Campo vacío",
            "descripcion": "Debe seleccionar una entrega para generar el reporte.",
            "icon": "warning"
        })

    try:
        entrega = (
            entrega_equipos.objects
            .select_related(
                "supervisor_encargado__id_usuario",
                "supervisor_encargado__id_turno",
                "id_equipo",
                "id_equipo__id_categoria"
            )
            .get(id_entrega=id_entrega)
        )

    except entrega_equipos.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Entrega no encontrada",
            "descripcion": "La entrega seleccionada no existe.",
            "icon": "warning"
        })

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El identificador de la entrega no es válido.",
            "icon": "warning"
        })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="entrega_equipo_{entrega.id_entrega}.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=135,
        bottomMargin=40
    )

    estilos = getSampleStyleSheet()

    estilo_encabezado = ParagraphStyle(
        "EncabezadoEntrega",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_campo = ParagraphStyle(
        "CampoEntrega",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.white
    )

    estilo_valor = ParagraphStyle(
        "ValorEntrega",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        textColor=colors.black,
        wordWrap="CJK"
    )

    def texto_seguro(valor, predeterminado="No especificado"):
        valor = str(valor).strip() if valor is not None else ""
        return escape(valor) if valor else predeterminado

    supervisor_obj = entrega.supervisor_encargado
    supervisor = supervisor_obj.id_usuario
    equipo = entrega.id_equipo
    turno = supervisor_obj.id_turno
    categoria = equipo.id_categoria

    nombre_supervisor = (
        f"{supervisor.nombres} {supervisor.apellidos}"
    ).strip()

    datos_entrega = [
        [
            Paragraph("Datos de la Entrega", estilo_encabezado),
            ""
        ],
        [
            Paragraph("Supervisor encargado", estilo_campo),
            Paragraph(texto_seguro(nombre_supervisor), estilo_valor)
        ],
        [
            Paragraph("Cédula del supervisor", estilo_campo),
            Paragraph(
                texto_seguro(supervisor.cedula_identidad),
                estilo_valor
            )
        ],
        [
            Paragraph("Turno", estilo_campo),
            Paragraph(
                texto_seguro(turno.nombre if turno else None),
                estilo_valor
            )
        ],
        [
            Paragraph("Equipo", estilo_campo),
            Paragraph(texto_seguro(equipo.nombre), estilo_valor)
        ],
        [
            Paragraph("Código del equipo", estilo_campo),
            Paragraph(texto_seguro(equipo.codigo), estilo_valor)
        ],
        [
            Paragraph("Categoría", estilo_campo),
            Paragraph(
                texto_seguro(categoria.nombre if categoria else None),
                estilo_valor
            )
        ],
        [
            Paragraph("Cantidad entregada", estilo_campo),
            Paragraph(str(entrega.cantidad_entregada), estilo_valor)
        ],
        [
            Paragraph("Cantidad disponible para asignar", estilo_campo),
            Paragraph(str(entrega.cantidad_disponible), estilo_valor)
        ],
        [
            Paragraph("Fecha de entrega", estilo_campo),
            Paragraph(
                entrega.fecha_entrega.strftime("%d/%m/%Y %H:%M")
                if entrega.fecha_entrega else "No especificada",
                estilo_valor
            )
        ],
        [
            Paragraph("Estado", estilo_campo),
            Paragraph(texto_seguro(entrega.estado), estilo_valor)
        ],
        [
            Paragraph("Motivo de incidencia", estilo_campo),
            Paragraph(
                texto_seguro(entrega.motivo_incidencia),
                estilo_valor
            )
        ],
        [
            Paragraph("Observación", estilo_campo),
            Paragraph(
                texto_seguro(entrega.observacion, "Sin observaciones"),
                estilo_valor
            )
        ]
    ]

    tabla_entrega = Table(
        datos_entrega,
        colWidths=[175, 320],
        hAlign="CENTER"
    )

    tabla_entrega.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#00445F")),
        ("BACKGROUND", (1, 1), (1, -1), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.black),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#58A5C4")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10)
    ]))

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    elementos = [
        tabla_entrega
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, doc: encabezado_datos_entrega_pdf(
            canvas, doc, ruta_logo
        ),
        onLaterPages=lambda canvas, doc: encabezado_datos_entrega_pdf(
            canvas, doc, ruta_logo
        )
    )

    return response

def encabezado_datos_entrega_pdf(canvas, documento, ruta_logo):
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
    y_titulo = letter[1] - 70

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

    fecha = datetime.now()

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
