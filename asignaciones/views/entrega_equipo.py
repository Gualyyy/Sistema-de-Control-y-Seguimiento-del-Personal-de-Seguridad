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
                equipos__entregas_supervisores__supervisor_encargado_id=int(id_supervisor)
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
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    id_supervisor = request.POST.get("supervisor", "").strip()
    id_categoria = request.POST.get("categoria", "").strip()

    if not id_supervisor.isdigit() or not id_categoria.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos inválidos",
            "descripcion": "Debe seleccionar un supervisor y una categoría válidos.",
            "icon": "warning"
        }, status=400)

    entregas = (
        entrega_equipos.objects
        .select_related(
            "id_equipo",
            "id_equipo__id_categoria"
        )
        .filter(
            supervisor_encargado_id=int(id_supervisor),
            id_equipo__id_categoria_id=int(id_categoria)
        ).exclude(
            motivo_incidencia="ERROR_HUMANO"
        ).order_by("-fecha_entrega")
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
            "descripcion": "No se encontraron equipos para el supervisor y la categoría seleccionados.",
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
            .filter(estado="ASIGNADO")
            .exclude(motivo_incidencia="ERROR_HUMANO")
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

# CORREGIR EL REGISTRO DEL EQUIPO ENTREGADO (ERROR_HUMANO)

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
            "warning",
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

    if tipo_correccion not in ("ACTUALIZAR", "ERROR_HUMANO"):
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

            # Verificar que la sesión corresponde a un administrador.
            encargados_administrativos.objects.get(
                id_usuario__cedula_identidad=cedula_administrador
            )

            # Bloquear la entrega durante la corrección.
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

            asignaciones = (
                asignacion_equipo.objects
                .filter(id_entrega=entrega)
                .aggregate(
                    pendiente=Sum(
                        ExpressionWrapper(
                            F("cantidad_asignada") -
                            F("cantidad_devuelta"),
                            output_field=IntegerField()
                        )
                    )
                )
            )

            cantidad_asignada = max(
                0,
                asignaciones["pendiente"] or 0
            )

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

                # Calcular las unidades disponibles para asignar.
                entrega.cantidad_disponible = (
                    cantidad_nueva - cantidad_asignada
                )

                entrega.observacion = observacion_entrega

                campos_actualizados = [
                    "cantidad_entregada",
                    "cantidad_disponible",
                    "observacion"
                ]

            else:  # ERROR_HUMANO

                if cantidad_asignada > 0:
                    return respuesta(
                        "fallo",
                        "Equipo asignado al personal",
                        (
                            f"No se puede devolver la entrega porque existen "
                            f"{cantidad_asignada} unidades pendientes de devolución "
                            f"por parte del personal."
                        ),
                        "warning"
                    )

                equipo = (
                    equipos.objects
                    .select_for_update()
                    .get(pk=entrega.id_equipo_id)
                )

                cantidad_inventario_anterior = equipo.cantidad_disponible
                cantidad_devolver = entrega.cantidad_disponible

                if cantidad_devolver <= 0:
                    return respuesta(
                        "fallo",
                        "Sin equipos para devolver",
                        "La entrega no tiene unidades disponibles para devolver.",
                        "warning"
                    )

                # Devolver las unidades al inventario general.
                equipo.cantidad_disponible = (
                    cantidad_inventario_anterior + cantidad_devolver
                )

                equipo.save(update_fields=["cantidad_disponible"])

                # Registrar el movimiento del inventario.
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

                # Marcar la entrega como procesada para impedir nuevas asignaciones.
                entrega.cantidad_entregada = 0
                entrega.cantidad_disponible = 0
                entrega.motivo_incidencia = "ERROR_HUMANO"
                entrega.observacion = observacion_entrega

                campos_actualizados = [
                    "cantidad_entregada",
                    "cantidad_disponible",
                    "motivo_incidencia",
                    "observacion"
                ]

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
                f"Intente nuevamente {e}."
            ),
            "error"
        )

# REPORTES PDF

def lista_entrega_equipos_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    categoria = request.POST.get("categoria", "").strip()
    supervisor = request.POST.get("supervisor", "").strip()

    entregas = (
        entrega_equipos.objects
        .filter(estado="ASIGNADO")
        .exclude(motivo_incidencia="ERROR_HUMANO")
        .select_related(
            "supervisor_encargado__id_usuario",
            "supervisor_encargado__id_turno",
            "id_equipo",
            "id_equipo__id_categoria"
        )
    )

    if categoria.isdigit():
        entregas = entregas.filter(
            id_equipo__id_categoria_id=int(categoria)
        )

    if supervisor.isdigit():
        entregas = entregas.filter(
            supervisor_encargado_id=int(supervisor)
        )

    entregas = list(entregas.order_by("-fecha_entrega"))

    if not entregas:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin resultados",
            "descripcion": (
                "No existen entregas de equipos para generar el reporte "
                "con los filtros seleccionados."
            ),
            "icon": "info"
        })
    
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="entregas_equipos.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=25,
        leftMargin=25,
        topMargin=130,
        bottomMargin=30
    )

    estilos = getSampleStyleSheet()

    estilo_encabezado = ParagraphStyle(
        "EncabezadoEntregas",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaEntregas",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.black,
        wordWrap="CJK"
    )

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    datos_tabla = [
        [
            Paragraph("Reporte de Entrega de Equipos", estilo_encabezado),
            "", "", "", "", "", "", "", ""
        ],
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("Supervisor Encargado", estilo_encabezado),
            Paragraph("Cédula", estilo_encabezado),
            Paragraph("Turno", estilo_encabezado),
            Paragraph("Equipo", estilo_encabezado),
            Paragraph("Código", estilo_encabezado),
            Paragraph("Cant. Entregada", estilo_encabezado),
            Paragraph("Cant. Disponible", estilo_encabezado),
            Paragraph("Fecha de Entrega", estilo_encabezado)
        ]
    ]

    for numero, entrega in enumerate(entregas, start=1):
        supervisor_obj = entrega.supervisor_encargado
        usuario_supervisor = supervisor_obj.id_usuario

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(
                f"{usuario_supervisor.nombres} "
                f"{usuario_supervisor.apellidos}",
                estilo_celda
            ),
            Paragraph(
                str(usuario_supervisor.cedula_identidad or "No especificada"),
                estilo_celda
            ),
            Paragraph(
                supervisor_obj.id_turno.nombre or "No especificado",
                estilo_celda
            ),
            Paragraph(
                entrega.id_equipo.nombre or "No especificado",
                estilo_celda
            ),
            Paragraph(
                entrega.id_equipo.codigo or "No especificado",
                estilo_celda
            ),
            Paragraph(str(entrega.cantidad_entregada), estilo_celda),
            Paragraph(str(entrega.cantidad_disponible), estilo_celda),
            Paragraph(
                entrega.fecha_entrega.strftime("%d/%m/%Y %H:%M")
                if entrega.fecha_entrega else "No especificada",
                estilo_celda
            )
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[28, 125, 75, 65, 115, 70, 75, 75, 100],
        repeatRows=2,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 1), colors.white),
        ("FONTNAME", (0, 0), (-1, 1), "Times-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#58A5C4")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3)
    ]))

    elementos = [
        tabla
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, doc: encabezado_lista_entrega_equipos_pdf(
            canvas, doc, ruta_logo
        ),
        onLaterPages=lambda canvas, doc: encabezado_lista_entrega_equipos_pdf(
            canvas, doc, ruta_logo
        )
    )

    return response

def encabezado_lista_entrega_equipos_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    # LOGO
    x_logo = 30
    y_logo = landscape(letter)[1] - 150

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
    x_titulo = 255
    y_titulo = landscape(letter)[1] - 70

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))

    canvas.drawString(
        x_titulo,
        y_titulo,
        "EMPRESA HIELO CAIPE C.A"
    )

    # FECHA EN ESPAÑOL
    meses = [
        "Enero", "Febrero", "Marzo", "Abril",
        "Mayo", "Junio", "Julio", "Agosto",
        "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    fecha = datetime.now()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    # FECHA
    x_fecha = 280
    y_fecha = landscape(letter)[1] - 120

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(colors.HexColor("#072F3F"))

    canvas.drawString(
        x_fecha,
        y_fecha,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

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

