from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Sum, Count, Exists, OuterRef
from django.conf import settings

from inicio_sesion.models import usuarios, perfil_usuario, equipos, bitacora, nacimiento

from .models import asignacion_equipo, movimiento_equipo

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

# GESTIONAR ASIGNACIÓN DE EQUIPOS

# EMPLEADOS REGISTRADOS

def empleados_registrados(request):
    registro_nacimiento = nacimiento.objects.filter(
        id_usuario=OuterRef("pk")
    )

    perfil_asignado = perfil_usuario.objects.filter(
        id_usuario=OuterRef("pk"),
        vigencia=True
    )

    empleados = (
        usuarios.objects
        .annotate(
            tiene_nacimiento=Exists(registro_nacimiento),
            tiene_perfil=Exists(perfil_asignado)
        )
        .filter(
            tiene_nacimiento=True,
            tiene_perfil=True
        )
    )

    perfiles_excluir = (
        perfil_usuario.objects
        .filter(vigencia=True)
        .values("id_usuario_id")
        .annotate(
            cantidad_perfiles=Count("id_perfil")
        )
        .filter(
            cantidad_perfiles=1
        )
    )

    usuarios_excluir = perfil_usuario.objects.filter(
        vigencia=True,
        id_perfil__perfil__in=[
            "Administrador(a)",
            "Supervisor Encargado"
        ],
        id_usuario_id__in=perfiles_excluir.values("id_usuario_id")
    ).values_list(
        "id_usuario_id",
        flat=True
    )

    empleados = empleados.exclude(
        id_usuario__in=usuarios_excluir
    )

    datos = [
        {
            "id_usuario": empleado.id_usuario,
            "nombres": empleado.nombres,
            "apellidos": empleado.apellidos,
            "cedula_identidad": empleado.cedula_identidad,
            "genero": empleado.genero,
            "estado_civil": empleado.estado_civil
        }
        for empleado in empleados
    ]

    return JsonResponse(datos, safe=False)

# PERFIL ASIGNDO

def perfiles_asignados(request):
    id_usuario = request.POST.get("id_usuario")

    if not id_usuario:
        return JsonResponse([], safe=False)

    perfiles_asignados = (
        perfil_usuario.objects
        .filter(
            id_usuario_id=id_usuario,
            vigencia=True
        )
        .exclude(
            id_perfil__perfil__in=[
                "Administrador(a)",
                "Supervisor Encargado"
            ]
        )
        .select_related("id_perfil")
    )

    datos = [
        {
            "id_perfil": perfil.id_perfil.id_perfil,
            "perfil": perfil.id_perfil.perfil
        }
        for perfil in perfiles_asignados
    ]

    return JsonResponse(datos, safe=False)

# EQUIPOS REGISTRADOS

def equipos_registrados(request):
    equipos_lista = (
        equipos.objects
        .filter(cantidad_disponible__gt=0)
        .select_related("id_categoria")
    )

    datos = [
        {
            "id_equipo": equipo.id_equipo,
            "nombre": equipo.nombre,
            "codigo": equipo.codigo,
            "categoria": equipo.id_categoria.nombre,
            "cantidad_total": equipo.cantidad_total,
            "cantidad_disponible": equipo.cantidad_disponible,
            "observacion": (
                equipo.observacion
                if equipo.observacion
                else "Sin observación"
            ),
        }
        for equipo in equipos_lista
    ]

    return JsonResponse(datos, safe=False)

# CANTIDAD DISPONIBLE DEL EQUIPO SELECCIONADO Y LA OBSERVACIÓN DE LA ASIGNACIÓN DEL EMPLEADO

def datos_equipo_seleccionado(request):
    if request.method == "POST":
        id_equipo = request.POST.get("id_equipo")
        id_usuario = request.POST.get("id_usuario")
        id_perfil = request.POST.get("id_perfil")

        if not id_equipo or not id_equipo.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "Debe seleccionar un equipo."
            })

        try:
            # DATOS DEL EQUIPO
            equipo = equipos.objects.get(id_equipo=id_equipo)

            datos_equipo = {
                "cantidad_disponible": equipo.cantidad_disponible
            }

            # DATOS DE LA ASIGNACIÓN
            datos_asignacion = {
                "observacion": "",
                "cantidad": 0
            }

            if id_usuario and id_perfil:
                asignacion = asignacion_equipo.objects.filter(
                    id_perfil_usuario__id_usuario_id=id_usuario,
                    id_perfil_usuario__id_perfil_id=id_perfil,
                    id_equipo_id=id_equipo,
                    estado="Asignado"
                ).first()

                if asignacion:
                    datos_asignacion = {
                        "observacion": asignacion.observacion,
                        "cantidad": (
                            asignacion.cantidad_asignada -
                            asignacion.cantidad_devuelta
                        )
                    }

            return JsonResponse({
                "estado": "exito",
                "equipo": datos_equipo,
                "asignacion": datos_asignacion
            })

        except equipos.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "El equipo no existe."
            })

# REGISTRAR LA ASIGNACIÓN DEL EQUIPO

def asignar_equipo_usuario(request):
    if request.method == "POST":
        id_usuario = request.POST.get("empleados_registrados")
        id_perfil = request.POST.get("perfiles_asignados")
        id_equipo = request.POST.get("equipos_registrados")
        observacion = request.POST.get("observacion_entrega")
        cantidad = request.POST.get("cantida_entrega")

        campos = [
            (
                id_usuario,
                "Empleado",
                "Por favor, seleccione uno de los empleados que se encuentra en el primer control."
            ),
            (
                id_equipo,
                "Equipo",
                "Por favor, seleccione uno de los equipos que se encuentra en el primer control."
            ),
            (
                cantidad,
                "Cantidad",
                "Por favor, ingrese la cantidad de equipo entregado."
            ),
        ]

        for valor, campo, mensaje in campos:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        if not observacion:
            observacion = "N/A"

        try:
            cantidad = int(cantidad)

            if cantidad <= 0:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Cantidad inválida",
                    "descripcion": "La cantidad debe ser mayor a 0.",
                    "icon": "warning"
                })

            with transaction.atomic():

                info_equipo = equipos.objects.get(
                    id_equipo=id_equipo
                )

                if info_equipo.cantidad_disponible < cantidad:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Cantidad insuficiente",
                        "descripcion": (
                            f"No hay suficientes {info_equipo.nombre} "
                            f"disponibles. Solo hay "
                            f"{info_equipo.cantidad_disponible}."
                        )
                    })

                info_usuario = usuarios.objects.get(
                    id_usuario=id_usuario
                )

                perfil_asignado = perfil_usuario.objects.get(
                    id_usuario=info_usuario,
                    id_perfil=id_perfil
                )

                asignacion_existente = (
                    asignacion_equipo.objects
                    .filter(
                        id_perfil_usuario=perfil_asignado,
                        id_equipo=info_equipo,
                        estado__in=["Asignado", "Parcial"]
                    )
                    .first()
                )

                if asignacion_existente:

                    asignacion_existente.cantidad_asignada += cantidad
                    asignacion_existente.observacion = observacion

                    asignacion_existente.save(
                        update_fields=[
                            "cantidad_asignada",
                            "observacion"
                        ]
                    )

                else:

                    asignacion_equipo.objects.create(
                        id_perfil_usuario=perfil_asignado,
                        id_equipo=info_equipo,
                        observacion=observacion,
                        cantidad_asignada=cantidad,
                        cantidad_devuelta=0,
                        estado="Asignado"
                    )

                info_equipo.cantidad_disponible -= cantidad

                info_equipo.save(
                    update_fields=["cantidad_disponible"]
                )

                info_usuario2 = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )

                accion = (
                    f"Registrar la asignación del equipo "
                    f"al empleado {info_usuario.nombres} "
                    f"{info_usuario.apellidos} "
                    f"{info_usuario.cedula_identidad} "
                    f"{info_equipo.nombre}"
                )

                bitacora.objects.create(
                    id_usuario=info_usuario2,
                    accion=accion
                )

                return JsonResponse({
                    "estado": "exito",
                    "icon": "success",
                    "title": "Registro exitoso",
                    "descripcion": (
                        "Se asignó exitosamente el equipo "
                        "al empleado."
                    )
                })

        except ValueError:
            return JsonResponse({
                "estado": "fallo",
                "title": "Cantidad inválida",
                "descripcion": "La cantidad debe ser un número entero válido.",
                "icon": "warning"
            })

        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Empleado no encontrado",
                "descripcion": "El empleado seleccionado no existe.",
                "icon": "warning"
            })

        except perfil_usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil no encontrado",
                "descripcion": "El perfil seleccionado no pertenece al empleado.",
                "icon": "warning"
            })

        except equipos.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Equipo no encontrado",
                "descripcion": "El equipo seleccionado no existe.",
                "icon": "warning"
            })

        except Exception as e:
            print(e)

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "Ocurrió un error al registrar "
                    "la asignación."
                )
            })
        
    return render(request, "asignar_equipo_usuario.html")

# BUSCAR TODOS LOS DATOS LA ASIGNACIÓN DEL EQUIPO

def buscar_datos_asignacion_equipo(request):
    if request.method == "POST":
        id_asignacion = request.POST.get("id_asignacion")

        try:
            asignacion = (
                asignacion_equipo.objects
                .select_related(
                    "id_perfil_usuario",
                    "id_perfil_usuario__id_usuario",
                    "id_perfil_usuario__id_perfil",
                    "id_equipo",
                    "id_equipo__id_categoria"
                )
                .get(id_asignacion=id_asignacion)
            )

            cantidad_pendiente = (
                asignacion.cantidad_asignada - asignacion.cantidad_devuelta
            )

            datos = {
                "id": asignacion.id_asignacion,
                "empleado": (
                    f"{asignacion.id_perfil_usuario.id_usuario.nombres} "
                    f"{asignacion.id_perfil_usuario.id_usuario.apellidos}"
                ),
                "cedula": (
                    asignacion
                    .id_perfil_usuario
                    .id_usuario
                    .cedula_identidad
                ),
                "equipo": asignacion.id_equipo.nombre,
                "codigo": asignacion.id_equipo.codigo,
                "categoria": asignacion.id_equipo.id_categoria.nombre,
                "cantidad_asignada": (
                    asignacion.cantidad_asignada
                ),
                "cantidad_devuelta": (
                    asignacion.cantidad_devuelta
                ),
                "cantidad_pendiente": cantidad_pendiente,
                "fecha_entrega": (
                    timezone.localtime(
                        asignacion.fecha_entrega
                    ).strftime("%d/%m/%Y %H:%M")
                ),
                "fecha_devolucion": (
                    timezone.localtime(
                        asignacion.fecha_devolucion,
                        timezone.get_current_timezone()
                    ).strftime("%d/%m/%Y %H:%M")
                    if asignacion.fecha_devolucion
                    else "N/A"
                ),
                "estado": asignacion.get_estado_display(),
            }

            return JsonResponse(datos)

        except asignacion_equipo.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": (
                    "No existe el registro de asignación."
                ),
                "icon": "error"
            })

# BUSCAR DATOS DE EQUIPO A DEVOLVER

def buscar_equipo_devolver(request):
    if request.method == "POST":
        id_asignacion = request.POST.get("id_asignacion")

        if not id_asignacion:
            return JsonResponse({
                "estado": "fallo",
                "title": "Dato vacío",
                "descripcion": (
                    "No se recibió el identificador "
                    "de la asignación."
                ),
                "icon": "warning"
            })

        try:
            asignacion = (
                asignacion_equipo.objects
                .select_related(
                    "id_perfil_usuario",
                    "id_perfil_usuario__id_usuario",
                    "id_perfil_usuario__id_perfil",
                    "id_equipo",
                    "id_equipo__id_categoria"
                )
                .get(id_asignacion=id_asignacion)
            )

            usuario = asignacion.id_perfil_usuario.id_usuario

            cantidad_pendiente = (
                asignacion.cantidad_asignada
                - asignacion.cantidad_devuelta
            )

            return JsonResponse({
                "estado": "exito",
                "asignacion": {
                    "id": asignacion.id_asignacion,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula": usuario.cedula_identidad,
                    "perfil": (
                        asignacion
                        .id_perfil_usuario
                        .id_perfil
                        .perfil
                    ),
                    "equipo": asignacion.id_equipo.nombre,
                    "codigo": asignacion.id_equipo.codigo,
                    "categoria": (
                        asignacion
                        .id_equipo
                        .id_categoria
                        .nombre
                    ),
                    "cantidad_asignada": (
                        asignacion.cantidad_asignada
                    ),
                    "cantidad_devuelta": (
                        asignacion.cantidad_devuelta
                    ),
                    "cantidad_pendiente": cantidad_pendiente,
                    "estado": (
                        asignacion.get_estado_display()
                    ),
                    "fecha_entrega": (
                        timezone.localtime(
                            asignacion.fecha_entrega
                        ).strftime("%d/%m/%Y %H:%M")
                    ),
                    "fecha_devolucion": (
                        timezone.localtime(
                            asignacion.fecha_devolucion,
                            timezone.get_current_timezone()
                        ).strftime("%d/%m/%Y %H:%M")
                        if asignacion.fecha_devolucion
                        else "N/A"
                    ),
                    "observacion": asignacion.observacion,
                }
            })

        except asignacion_equipo.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "No encontrado",
                "descripcion": (
                    "La asignación de equipo no existe."
                ),
                "icon": "warning"
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": str(e),
                "icon": "error"
            })

# LISTAR EQUIPOS ASIGNADO DEL EMPLEADO

def equipos_asignado_usuario(request):
    if request.method == "POST":
        id_usuario = request.POST.get("id_usuario")
        id_perfil = request.POST.get("id_perfil")

        try:
            perfil = perfil_usuario.objects.get(
                id_usuario=id_usuario,
                id_perfil=id_perfil,
                vigencia=True
            )

            # No permitir consultar Administrador(a)
            if perfil.id_perfil.perfil.lower() == "administrador(a)":
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Empleado Denegado",
                    "descripcion": "No se permite consultar este empleado.",
                    "icon": "error"
                })

            # Solo asignaciones vigentes
            equipos_usuario = (
                asignacion_equipo.objects
                .filter(
                    id_perfil_usuario=perfil,
                    estado__in=["Asignado", "Parcial"]
                )
                .select_related("id_equipo")
            )

            datos = []

            for asignacion in equipos_usuario:
                datos.append({
                    "id": asignacion.id_asignacion,
                    "equipo": asignacion.id_equipo.nombre,
                    "fecha_entrega": asignacion.fecha_entrega.strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    "cantidad": asignacion.cantidad
                })

            if not datos:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sin asignaciones",
                    "descripcion": "El empleado no tiene equipos asignados para corregir.",
                    "icon": "warning"
                })

            return JsonResponse({
                "estado": "exito",
                "equipos": datos
            })

        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "No encontrado",
                "descripcion": "No existe un empleado registrado.",
                "icon": "error"
            })

        except perfil_usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Sin perfil",
                "descripcion": "El empleado no tiene este perfil asignado.",
                "icon": "warning"
            })

# DEVOLUCIÓN DE EQUIPO

def devolucion_equipos_asignado(request):
    if request.method == "POST":
        id_asignacion = request.POST.get("id_asignacion")
        ci_usuario = request.POST.get("ci_usuario")
        tipos_devolucion = request.POST.get("tipos_devolucion")
        estados_devolucion = request.POST.get("estados_devolucion")
        cantidad_devolver = request.POST.get("cantidad")

        if not id_asignacion:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "No se recibió la asignación.",
                "icon": "error"
            })

        try:
            with transaction.atomic():
                asignacion = (
                    asignacion_equipo.objects
                    .select_for_update()
                    .select_related("id_equipo")
                    .get(id_asignacion=id_asignacion)
                )

                if asignacion.estado not in ["Asignado", "Parcial"]:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Asignación no disponible",
                        "descripcion": (
                            "Esta asignación ya fue finalizada y "
                            "no puede recibir otra devolución."
                        ),
                        "icon": "warning"
                    })

                cantidad_pendiente = (
                    asignacion.cantidad_asignada
                    - asignacion.cantidad_devuelta
                )

                if cantidad_pendiente <= 0:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Asignación finalizada",
                        "descripcion": (
                            "No existe cantidad pendiente por devolver."
                        ),
                        "icon": "warning"
                    })

                if tipos_devolucion not in ["DEVOLUCION", "CORRECCION"]:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Tipo inválido",
                        "descripcion": (
                            "Debe seleccionar un tipo de devolución válido."
                        ),
                        "icon": "warning"
                    })

                # CORRECCIÓN POR ERROR HUMANO
                if tipos_devolucion == "CORRECCION":
                    cantidad = cantidad_pendiente
                    estado = "ERROR_HUMANO"

                # DEVOLUCIÓN NORMAL
                else:
                    if estados_devolucion not in [
                        "DEVUELTO",
                        "DAÑADO",
                        "HURTADO",
                        "EXTRAVIADO"
                    ]:
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Estado inválido",
                            "descripcion": (
                                "Debe seleccionar un estado válido "
                                "para la devolución."
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
                                "La cantidad a devolver debe ser "
                                "un número entero."
                            ),
                            "icon": "warning"
                        })

                    if cantidad <= 0:
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Cantidad inválida",
                            "descripcion": (
                                "La cantidad debe ser mayor a cero."
                            ),
                            "icon": "warning"
                        })

                    if cantidad > cantidad_pendiente:
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Cantidad inválida",
                            "descripcion": (
                                f"La cantidad a devolver no puede ser "
                                f"mayor a la cantidad pendiente "
                                f"({cantidad_pendiente})."
                            ),
                            "icon": "warning"
                        })

                    estado = estados_devolucion

                equipo = (
                    equipos.objects
                    .select_for_update()
                    .get(id_equipo=asignacion.id_equipo.id_equipo)
                )

                # Actualizar inventario
                if estado in ["DEVUELTO", "ERROR_HUMANO"]:
                    equipo.cantidad_disponible += cantidad

                    if equipo.cantidad_disponible > equipo.cantidad_total:
                        equipo.cantidad_disponible = equipo.cantidad_total

                    equipo.save(
                        update_fields=["cantidad_disponible"]
                    )

                # Actualizar cantidad devuelta
                asignacion.cantidad_devuelta += cantidad

                nueva_cantidad_pendiente = (
                    asignacion.cantidad_asignada
                    - asignacion.cantidad_devuelta
                )

                if nueva_cantidad_pendiente == 0:
                    asignacion.estado = "Finalizado"
                    asignacion.fecha_devolucion = timezone.now()
                else:
                    asignacion.estado = "Parcial"

                asignacion.save(
                    update_fields=[
                        "cantidad_devuelta",
                        "estado",
                        "fecha_devolucion"
                    ]
                )

                usuario = usuarios.objects.get(
                    cedula_identidad=ci_usuario
                )

                movimiento_equipo.objects.create(
                    id_asignacion=asignacion,
                    usuario_registro=usuario,
                    cantidad=cantidad,
                    tipo=tipos_devolucion,
                    estado=estado
                )

            return JsonResponse({
                "estado": "exito",
                "title": "Operación realizada",
                "descripcion": (
                    "La devolución fue registrada correctamente."
                ),
                "icon": "success"
            })

        except asignacion_equipo.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Asignación no encontrada",
                "descripcion": "No existe la asignación indicada.",
                "icon": "error"
            })

        except Exception as error:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": str(error),
                "icon": "error"
            })

# EQUIPOS ASIGNADOS

def visualizar_asignacion_equipo(request):
    if request.method != "POST":
        return render(request, "visualizar_asignacion.html")

    nacionalidad = request.POST.get("nacionalidad", "").strip()
    cedula = request.POST.get("cedula", "").strip()
    categoria = request.POST.get("categoria", "").strip()

    asignaciones = (
        asignacion_equipo.objects
        .select_related(
            "id_perfil_usuario",
            "id_perfil_usuario__id_usuario",
            "id_perfil_usuario__id_perfil",
            "id_equipo",
            "id_equipo__id_categoria"
        )
        .order_by("-fecha_entrega")
    )

    # FILTRO POR CÉDULA
    if nacionalidad and cedula:
        asignaciones = asignaciones.filter(
            id_perfil_usuario__id_usuario__cedula_identidad=(
                f"{nacionalidad}-{cedula}"
            )
        )

    # FILTRO POR CATEGORÍA
    if categoria:
        asignaciones = asignaciones.filter(
            id_equipo__id_categoria_id=categoria
        )

    datos = []

    for asignacion in asignaciones:
        usuario = asignacion.id_perfil_usuario.id_usuario

        cantidad_pendiente = (
            asignacion.cantidad_asignada
            - asignacion.cantidad_devuelta
        )

        datos.append({
            "id": asignacion.id_asignacion,
            "empleado": (
                f"{usuario.nombres} "
                f"{usuario.apellidos}"
            ),
            "equipo": asignacion.id_equipo.nombre,
            "fecha_entrega": (
                asignacion.fecha_entrega.strftime(
                    "%d/%m/%Y %H:%M"
                )
            ),
            "fecha_devolucion": (
                asignacion.fecha_devolucion.strftime(
                    "%d/%m/%Y %H:%M"
                )
                if asignacion.fecha_devolucion
                else ""
            ),
            "cantidad_asignada": asignacion.cantidad_asignada,
            "cantidad_devuelta": asignacion.cantidad_devuelta,
            "cantidad_pendiente": cantidad_pendiente,
            "estado": asignacion.get_estado_display()
        })

    return JsonResponse(datos, safe=False)

# HISTORIAL DE DEVOLUCIONES

def fechas_historial_devolucion(request):
    movimientos = (
        movimiento_equipo.objects
        .filter(tipo="DEVOLUCION")
        .order_by("-fecha")
    )

    fechas = []

    for movimiento in movimientos:
        fecha = timezone.localtime(movimiento.fecha)

        fechas.append({
            "fecha": fecha.strftime("%Y-%m-%d"),
            "fecha_mostrar": fecha.strftime("%d/%m/%Y")
        })

    return JsonResponse({
        "estado": "exito",
        "fechas": fechas
    })

def perfil_historial_devolucion(request):

    perfiles = (
        asignacion_equipo.objects
        .filter(
            movimientos__tipo="DEVOLUCION",
            id_perfil_usuario__isnull=False
        )
        .values(
            "id_perfil_usuario__id_perfil_id",
            "id_perfil_usuario__id_perfil__perfil"
        )
        .distinct()
        .order_by(
            "id_perfil_usuario__id_perfil__perfil"
        )
    )

    datos = [
        {
            "id_perfil": perfil["id_perfil_usuario__id_perfil_id"],
            "perfil": perfil["id_perfil_usuario__id_perfil__perfil"]
        }
        for perfil in perfiles
    ]

    return JsonResponse({
        "estado": "exito",
        "perfiles": datos
    })

def visualizar_devoluciones(request):
    if request.method != "POST":
        return render(request, "historial_devoluciones.html")

    movimientos = (
        movimiento_equipo.objects
        .select_related(
            "id_asignacion",
            "id_asignacion__id_perfil_usuario",
            "id_asignacion__id_perfil_usuario__id_usuario",
            "id_asignacion__id_equipo",
            "id_asignacion__id_equipo__id_categoria",
            "usuario_registro"
        )
        .order_by("-fecha")
    )

    datos = []

    for movimiento in movimientos:

        asignacion = movimiento.id_asignacion
        usuario = asignacion.id_perfil_usuario.id_usuario
        equipo = asignacion.id_equipo

        datos.append({
            "id_movimiento": movimiento.id_movimiento,
            "empleado": (
                f"{usuario.nombres} "
                f"{usuario.apellidos}"
            ),
            "cedula": usuario.cedula_identidad,
            "equipo": equipo.nombre,
            "codigo": equipo.codigo,
            "categoria": equipo.id_categoria.nombre,
            "id_asignacion": asignacion.id_asignacion,
            "fecha_entrega": (
                timezone.localtime(
                    asignacion.fecha_entrega
                ).strftime("%d/%m/%Y %H:%M")
            ),
            "cantidad": movimiento.cantidad,
            "estado": movimiento.get_estado_display(),
            "fecha_devolucion": (
                timezone.localtime(
                    movimiento.fecha
                ).strftime("%d/%m/%Y %H:%M")
            ),
            "usuario_registro": (
                f"{movimiento.usuario_registro.nombres} "
                f"{movimiento.usuario_registro.apellidos}"
                if movimiento.usuario_registro
                else "N/A"
            )
        })

    return JsonResponse(datos, safe=False)

# 

def lista_historial_devolucion_pdf(request):
    fecha = request.POST.get("fecha", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    movimientos = (
        movimiento_equipo.objects
        .select_related(
            "id_asignacion",
            "id_asignacion__id_perfil_usuario",
            "id_asignacion__id_perfil_usuario__id_usuario",
            "id_asignacion__id_perfil_usuario__id_perfil",
            "id_asignacion__id_perfil_usuario__id_turno",
            "id_asignacion__id_equipo",
            "id_asignacion__id_equipo__id_categoria",
            "usuario_registro"
        )
        .order_by("-fecha")
    )

    # FILTRAR POR FECHA
    if fecha:
        movimientos = movimientos.filter(
            fecha__date=fecha
        )

    # FILTRAR POR PERFIL
    if perfil:
        movimientos = movimientos.filter(
            id_asignacion__id_perfil_usuario__id_perfil_id=perfil
        )

    datos = []

    for numero, movimiento in enumerate(movimientos, start=1):

        asignacion = movimiento.id_asignacion
        usuario = asignacion.id_perfil_usuario.id_usuario
        perfil_usuario = asignacion.id_perfil_usuario.id_perfil
        equipo = asignacion.id_equipo

        datos.append({
            "id": numero,
            "id_movimiento": movimiento.id_movimiento,
            "empleado": (
                f"{usuario.nombres} "
                f"{usuario.apellidos}"
            ),
            "cedula": usuario.cedula_identidad,
            "perfil": perfil_usuario.perfil,
            "equipo": equipo.nombre,
            "codigo": equipo.codigo,
            "categoria": equipo.id_categoria.nombre,
            "id_asignacion": asignacion.id_asignacion,
            "fecha_entrega": (
                timezone.localtime(
                    asignacion.fecha_entrega
                ).strftime("%d/%m/%Y %H:%M")
            ),
            "cantidad": movimiento.cantidad,
            "estado": movimiento.get_estado_display(),
            "fecha_devolucion": (
                timezone.localtime(
                    movimiento.fecha
                ).strftime("%d/%m/%Y %H:%M")
            )
        })

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="historial_devoluciones.pdf"'
    )

    estilo_encabezado = ParagraphStyle(
        "estilo_encabezado",
        fontName="Times-Bold",
        fontSize=12,
        leading=14,
        alignment=1,
        textColor=colors.white
    )

    estilo_titulo = ParagraphStyle(
        "estilo_titulo",
        fontName="Times-Bold",
        fontSize=15,
        leading=17,
        alignment=1,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "estilo_celda",
        fontName="Times-Roman",
        fontSize=12,
        leading=14,
        alignment=1,
        wordWrap="CJK"
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(legal),
        rightMargin=20,
        leftMargin=20,
        topMargin=140,
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
                "HISTORIAL DE DEVOLUCIONES",
                estilo_titulo
            ),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        [
            Paragraph("ID", estilo_encabezado),
            Paragraph("EMPLEADO", estilo_encabezado),
            Paragraph("PERFIL", estilo_encabezado),
            Paragraph("EQUIPO", estilo_encabezado),
            Paragraph("CATEGORÍA", estilo_encabezado),
            Paragraph("CANTIDAD", estilo_encabezado),
            Paragraph("ESTADO", estilo_encabezado),
            Paragraph("FECHA", estilo_encabezado),
        ]
    ]

    for dato in datos:
        datos_tabla.append([
            Paragraph(
                str(dato["id"]),
                estilo_celda
            ),
            Paragraph(
                dato["empleado"],
                estilo_celda
            ),
            Paragraph(
                dato["perfil"],
                estilo_celda
            ),
            Paragraph(
                dato["equipo"],
                estilo_celda
            ),
            Paragraph(
                dato["categoria"],
                estilo_celda
            ),
            Paragraph(
                str(dato["cantidad"]),
                estilo_celda
            ),
            Paragraph(
                dato["estado"],
                estilo_celda
            ),
            Paragraph(
                dato["fecha_devolucion"],
                estilo_celda
            ),
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[
            35,   # ID
            180,  # EMPLEADO
            85,   # PERFIL
            115,  # EQUIPO
            105,  # CATEGORÍA
            80,   # CANTIDAD
            95,   # ESTADO
            130   # FECHA
        ],
        repeatRows=2
    )

    tabla.setStyle(TableStyle([
        # ENCABEZADO PRINCIPAL
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0),
        colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, 0), (-1, 0),
        colors.white),

        ("ALIGN", (0, 0), (-1, 0),
        "CENTER"),

        ("VALIGN", (0, 0), (-1, 0),
        "MIDDLE"),

        # ENCABEZADO COLUMNAS
        ("BACKGROUND", (0, 1), (-1, 1),
        colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, 1), (-1, 1),
        colors.white),

        ("ALIGN", (0, 1), (-1, 1),
        "CENTER"),

        ("VALIGN", (0, 1), (-1, 1),
        "MIDDLE"),

        # CONTENIDO
        ("TEXTCOLOR", (0, 2), (-1, -1),
        colors.black),

        ("ALIGN", (0, 2), (-1, -1),
        "CENTER"),

        ("VALIGN", (0, 2), (-1, -1),
        "MIDDLE"),

        # BORDES
        ("GRID", (0, 0), (-1, -1),
        0.4, colors.grey),

        # ESPACIADO
        ("TOPPADDING", (0, 0), (-1, -1),
        7),

        ("BOTTOMPADDING", (0, 0), (-1, -1),
        7),

    ]))

    elementos = [
        tabla
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_historial_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_historial_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_historial_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(legal)

    # LOGO
    x_logo = 120
    y_logo = alto_pagina - 180

    ancho_logo = 220
    alto_logo = 220

    canvas.drawImage(
        ruta_logo,
        x_logo,
        y_logo,
        width=ancho_logo,
        height=alto_logo,
        preserveAspectRatio=True,
        mask="auto"
    )

    # CENTRO DE LA PÁGINA
    centro_pagina = ancho_pagina / 2

    # TITULO EMPRESA
    y_titulo = alto_pagina - 80

    canvas.setFont(
        "Times-Bold",
        22
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawCentredString(
        centro_pagina,
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

    fecha = timezone.localtime(
        timezone.now()
    )

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    # FECHA
    y_fecha = alto_pagina - 130

    canvas.setFont(
        "Times-Bold",
        14
    )

    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawCentredString(
        centro_pagina,
        y_fecha,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

# LISTAR LOS EQUIPOS ASIGNADOS DEL EMPLEADO PARA GENERAR PDF

def lista_asignaciones_pdf(request):
    categoria = request.POST.get("categoria", "").strip()

    asignaciones = (
        asignacion_equipo.objects
        .select_related(
            "id_perfil_usuario",
            "id_perfil_usuario__id_usuario",
            "id_perfil_usuario__id_perfil",
            "id_perfil_usuario__id_turno",
            "id_equipo",
            "id_equipo__id_categoria"
        )
        .order_by("-fecha_entrega")
    )

    # FILTRAR POR CATEGORÍA
    if categoria:
        asignaciones = asignaciones.filter(id_equipo__id_categoria_id=categoria)

    datos = []

    for asignacion in asignaciones:

        usuario = asignacion.id_perfil_usuario.id_usuario
        perfil = asignacion.id_perfil_usuario.id_perfil

        datos.append({
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "cedula": usuario.cedula_identidad,
            "perfil": perfil.perfil,
            "equipo": asignacion.id_equipo.nombre,
            "codigo": asignacion.id_equipo.codigo,
            "categoria": asignacion.id_equipo.id_categoria.nombre,
            "fecha_entrega": (
                timezone.localtime(
                    asignacion.fecha_entrega
                ).strftime("%d/%m/%Y %H:%M")
            ),
            "fecha_devolucion": (
                timezone.localtime(
                    asignacion.fecha_devolucion
                ).strftime("%d/%m/%Y %H:%M")
                if asignacion.fecha_devolucion
                else "Pendiente"
            ),
            "cantidad": asignacion.cantidad_asignada,
            "estado": asignacion.get_estado_display(),
        })

    # RESPUESTA PDF
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = ('inline; filename="lista_asignaciones_equipos.pdf"')

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
            Paragraph("EMPLEADO", estilo_encabezado),
            Paragraph("EQUIPO", estilo_encabezado),
            Paragraph("FECHA ENTREGA", estilo_encabezado),
            Paragraph("FECHA DEVOLUCIÓN", estilo_encabezado),
            Paragraph("ESTADO", estilo_encabezado),
        ],
    ]

    for numero, dato in enumerate(datos, start=1):
        datos_tabla.append([
            str(numero),
            Paragraph(
                f"{dato['nombres']} {dato['apellidos']}",
                estilo_celda
            ),
            Paragraph(
                dato["equipo"],
                estilo_celda
            ),
            Paragraph(
                dato["fecha_entrega"],
                estilo_celda
            ),
            Paragraph(
                dato["fecha_devolucion"],
                estilo_celda
            ),
            Paragraph(
                dato['estado'],
                estilo_celda
            ),
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[
            35,   # ID
            140,  # Empleado
            105,  # Equipo
            95,   # Fecha entrega
            95,   # Fecha devolución
            70    # Estado
        ],
        repeatRows=2
    )

    tabla.setStyle(TableStyle([
        # ENCABEZADO PRINCIPAL
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        # ENCABEZADO DE COLUMNAS
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 9),

        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        # CONTENIDO
        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 8),

        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),

        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        # BORDES
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # ESPACIADO
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

    ]))

    # ELEMENTOS
    elementos = [
        tabla
    ]

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

    try:
        asignacion = (
            asignacion_equipo.objects
            .select_related(
                "id_perfil_usuario",
                "id_perfil_usuario__id_usuario",
                "id_perfil_usuario__id_perfil",
                "id_equipo",
                "id_equipo__id_categoria"
            )
            .get(id_asignacion=id_asignacion)
        )

    except asignacion_equipo.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "No existe el registro de asignación.",
            "icon": "error"
        })

    # DATOS DEL EMPLEADO
    usuario = asignacion.id_perfil_usuario.id_usuario

    # DATOS DE LA ASIGNACIÓN
    datos_asignacion = [
        ["Empleado:",
         f"{usuario.nombres} {usuario.apellidos}"],

        ["Cédula de Identidad:",
         usuario.cedula_identidad],

        ["Perfil:",
         asignacion.id_perfil_usuario.id_perfil.perfil],

        ["Equipo:",
         asignacion.id_equipo.nombre],

        ["Código del Equipo:",
         asignacion.id_equipo.codigo],

        ["Categoría:",
         asignacion.id_equipo.id_categoria.nombre],

        ["Cantidad:",
         asignacion.cantidad_asignada],

        ["Fecha de Entrega:",
        (
            timezone.localtime(
                asignacion.fecha_entrega
            ).strftime("%d/%m/%Y %H:%M")
        )],

        ["Fecha de Devolución:",
         (
            timezone.localtime(
                asignacion.fecha_entrega
            ).strftime("%d/%m/%Y %H:%M")
             if asignacion.fecha_devolucion
             else "Pendiente"
         )],

        ["Estado:",
         asignacion.get_estado_display()],
    ]

    # RESPUESTA PDF
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="asignacion_{asignacion.id_asignacion}.pdf"'
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=110,
        bottomMargin=30
    )

    # TABLA
    datos_tabla = [
        ["DATOS DE LA ASIGNACIÓN", ""]
    ]

    datos_tabla.extend(datos_asignacion)

    tabla = Table(
        datos_tabla,
        colWidths=[150, 340],
        splitByRow=1
    )

    tabla.setStyle(TableStyle([

        # ENCABEZADO
        ("BACKGROUND",
         (0, 0),
         (-1, 0),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR",
         (0, 0),
         (-1, 0),
         colors.white),

        ("FONTNAME",
         (0, 0),
         (-1, 0),
         "Times-Bold"),

        ("FONTSIZE",
         (0, 0),
         (-1, 0),
         14),

        ("ALIGN",
         (0, 0),
         (-1, 0),
         "CENTER"),

        ("VALIGN",
         (0, 0),
         (-1, 0),
         "MIDDLE"),

        # UNIR ENCABEZADO
        ("SPAN",
         (0, 0),
         (-1, 0)),

        # CAMPOS
        ("BACKGROUND",
         (0, 1),
         (0, -1),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR",
         (0, 1),
         (0, -1),
         colors.white),

        ("FONTNAME",
         (0, 1),
         (0, -1),
         "Times-Bold"),

        ("FONTSIZE",
         (0, 1),
         (0, -1),
         10),

        # VALORES
        ("FONTNAME",
         (1, 1),
         (1, -1),
         "Times-Roman"),

        ("TEXTCOLOR",
         (1, 1),
         (1, -1),
         colors.black),

        ("FONTSIZE",
         (1, 1),
         (1, -1),
         10),

        # GENERAL
        ("ALIGN",
         (0, 1),
         (-1, -1),
         "LEFT"),

        ("VALIGN",
         (0, 0),
         (-1, -1),
         "MIDDLE"),

        ("GRID",
         (0, 0),
         (-1, -1),
         0.5,
         colors.grey),

        ("TOPPADDING",
         (0, 0),
         (-1, -1),
         7),

        ("BOTTOMPADDING",
         (0, 0),
         (-1, -1),
         7),

    ]))

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    # ELEMENTOS
    elementos = [
        tabla
    ]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_datos_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_datos_pdf(
                canvas,
                documento,
                ruta_logo
            )
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
