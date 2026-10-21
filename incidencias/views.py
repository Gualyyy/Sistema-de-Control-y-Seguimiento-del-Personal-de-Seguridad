from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from django.utils.dateparse import parse_datetime

from incidencias.models import tipo_incidencia, incidencia, vigilante_incidencia
from inicio_sesion.models import bitacora, supervisores_encargados, vigilantes

import os
from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, legal

# Create your views here.

def tipos_incidencias(request):
    tipos = tipo_incidencia.objects.order_by("nombre")

    datos = [
        {
            "id_tipo": tipo.id_tipo,
            "nombre": tipo.nombre
        }
        for tipo in tipos
    ]

    return JsonResponse(datos, safe=False)

def fechas_incidencias(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al usuario.",
            "icon": "warning"
        })

    try:
        supervisor = (
            supervisores_encargados.objects
            .select_related("id_usuario", "id_turno")
            .get(
                id_usuario__cedula_identidad=cedula,
                vigencia=True
            )
        )

        # Obtener las fechas de las incidencias
        # correspondientes al turno del supervisor
        fechas = (
            incidencia.objects
            .filter(
                id_turno_id=supervisor.id_turno_id,
                fecha_hora__isnull=False
            )
            .values_list("fecha_hora", flat=True)
            .order_by("-fecha_hora")
        )

        # Convertir las fechas a fechas locales y eliminar duplicados
        fechas_unicas = sorted(
            {
                timezone.localtime(fecha).date()
                for fecha in fechas
            },
            reverse=True
        )

        datos = [
            {
                "value": fecha.isoformat(),
                "texto": fecha.strftime("%d/%m/%Y")
            }
            for fecha in fechas_unicas
        ]

        return JsonResponse({
            "estado": "exito",
            "fechas": datos
        })

    except supervisores_encargados.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": (
                "No existe un supervisor encargado vigente "
                "asociado a la sesión."
            ),
            "icon": "warning"
        })
    
def vigilantes_registrados(request):
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "vacio",
            "vigilantes": []
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
            "estado": "vacio",
            "vigilantes": []
        })

    registros = (
        vigilantes.objects
        .filter(
            id_turno=supervisor.id_turno,
            vigencia=True
        )
        .select_related(
            "id_usuario",
            "id_turno"
        )
        .order_by(
            "id_usuario__apellidos",
            "id_usuario__nombres"
        )
    )

    vigilantes_registrados = [
        {
            "id_usuario": vigilante.id_usuario_id,
            "id_vigilante": vigilante.id_vigilante,
            "cedula": vigilante.id_usuario.cedula_identidad,
            "nombres": vigilante.id_usuario.nombres,
            "apellidos": vigilante.id_usuario.apellidos,
            "genero": vigilante.id_usuario.genero,
            "estado_civil": vigilante.id_usuario.estado_civil,
            "turno": vigilante.id_turno.nombre,
            "vigencia": vigilante.vigencia
        }
        for vigilante in registros
    ]

    if not vigilantes_registrados:
        return JsonResponse({
            "estado": "vacio",
            "vigilantes": []
        })

    return JsonResponse({
        "estado": "exito",
        "vigilantes": vigilantes_registrados
    })

# REGISTRAR

def registrar_incidencias(request):
    if request.method != "POST":
        return render(request, "Supervisor_Encargado/registrar_incidencias.html")

    cedula_supervisor = request.session.get("cedula_identidad")

    vigilante_registrado = request.POST.get("vigilantes_registrados", "").strip()
    fecha_hora_incidencia = request.POST.get("fecha_hora_incidencia", "").strip()
    tipo_incidencias = request.POST.get("tipos_incidencias", "").strip()
    titulo_incidencia = request.POST.get("titulo_incidencia", "").strip()
    descripcion_incidencia = request.POST.get("descripcion_incidencia", "").strip()

    # Validar la sesión
    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al supervisor autenticado.",
            "icon": "warning"
        })

    controles = [
        (vigilante_registrado, "Vigilante requerido", "Por favor, seleccione el vigilante involucrado."),
        (fecha_hora_incidencia, "Fecha y hora requeridas", "Por favor, ingrese la fecha y hora de la incidencia."),
        (tipo_incidencias, "Tipo de incidencia requerido", "Por favor, seleccione el tipo de incidencia."),
        (titulo_incidencia, "Título requerido", "Por favor, ingrese el título de la incidencia."),
        (descripcion_incidencia, "Descripción requerida", "Por favor, ingrese la descripción de la incidencia."),
    ]

    for valor, titulo, mensaje in controles:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": titulo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if len(titulo_incidencia) < 8 or len(titulo_incidencia) > 50:
        return JsonResponse({
            "estado": "fallo",
            "title": "Título no válido",
            "descripcion": "El título debe tener entre 8 y 50 caracteres.",
            "icon": "warning"
        })

    if len(descripcion_incidencia) > 400:
        return JsonResponse({
            "estado": "fallo",
            "title": "Descripción demasiado larga",
            "descripcion": "La descripción no puede superar los 400 caracteres.",
            "icon": "warning"
        })

    fecha_hora = parse_datetime(fecha_hora_incidencia)
    if fecha_hora is None:
        return JsonResponse({
            "estado": "fallo",
            "title": "Fecha no válida",
            "descripcion": "Ingrese una fecha y hora válidas.",
            "icon": "warning"
        })

    if timezone.is_naive(fecha_hora):
        fecha_hora = timezone.make_aware(
            fecha_hora,
            timezone.get_current_timezone()
        )

    try:
        with transaction.atomic():
            supervisor = (
                supervisores_encargados.objects
                .select_related("id_usuario", "id_turno")
                .get(
                    id_usuario__cedula_identidad=cedula_supervisor,
                    vigencia=True
                )
            )

            vigilante = (
                vigilantes.objects
                .select_related("id_usuario", "id_turno")
                .get(
                    id_vigilante=vigilante_registrado,
                    id_turno=supervisor.id_turno,
                    vigencia=True
                )
            )

            tipo_obj = tipo_incidencia.objects.get(
                id_tipo=tipo_incidencias
            )

            nueva_incidencia = incidencia.objects.create(
                id_supervisor=supervisor,
                id_turno=supervisor.id_turno,
                id_tipo=tipo_obj,
                titulo=titulo_incidencia,
                descripcion=descripcion_incidencia
            )

            vigilante_incidencia.objects.create(
                id_incidencia=nueva_incidencia,
                id_vigilante=vigilante
            )

            bitacora.objects.create(
                id_usuario=supervisor.id_usuario,
                accion=(
                    f"Registró la incidencia N.º "
                    f"{nueva_incidencia.id_incidencia}: "
                    f"'{titulo_incidencia}' - "
                    f"Tipo: {tipo_obj.nombre} - "
                    f"Vigilante: "
                    f"{vigilante.id_usuario.nombres} "
                    f"{vigilante.id_usuario.apellidos}"
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Incidencia registrada",
            "descripcion": "La incidencia se registró correctamente.",
            "icon": "success"
        })

    except supervisores_encargados.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no disponible",
            "descripcion": "No existe un supervisor vigente asociado a la sesión.",
            "icon": "warning"
        })

    except vigilantes.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Vigilante no disponible",
            "descripcion": (
                "El vigilante seleccionado no está vigente "
                "o no pertenece al turno del supervisor."
            ),
            "icon": "warning"
        })

    except tipo_incidencia.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo de incidencia no válido",
            "descripcion": "El tipo de incidencia seleccionado no está registrado.",
            "icon": "warning"
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al registrar",
            "descripcion": f"Ocurrió un error al registrar la incidencia {e}.",
            "icon": "error"
        })

# GESTIONAR
    
def gestionar_incidencias(request):
    return render(request, "Supervisor_Encargado/gestionar_incidencia.html")

def incidencias_vigilante(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "Esta consulta requiere una solicitud POST.",
            "icon": "warning"
        }, status=405)

    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al supervisor autenticado.",
            "icon": "error"
        })

    supervisor = (
        supervisores_encargados.objects
        .filter(
            id_usuario__cedula_identidad=cedula,
            vigencia=True
        )
        .select_related("id_turno")
        .first()
    )

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "No se encontró un Supervisor Encargado activo.",
            "icon": "error"
        })

    tipo_incidencia_id = request.POST.get(
        "tipo_incidencia", ""
    ).strip()

    fecha_incidencia = request.POST.get(
        "fecha_incidencia", ""
    ).strip()

    # Obtener las incidencias del turno del supervisor
    incidencias = (
        incidencia.objects
        .select_related(
            "id_tipo",
            "id_turno",
            "id_supervisor",
        )
        .prefetch_related(
            "varios_vigilantes__id_usuario",
            "varios_vigilantes__id_turno",
        )
        .filter(
            id_turno_id=supervisor.id_turno_id
        )
    )

    # Filtrar por tipo de incidencia
    if tipo_incidencia_id:
        if not tipo_incidencia_id.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Tipo de incidencia inválido",
                "descripcion": "El tipo de incidencia seleccionado no es válido.",
                "icon": "warning"
            })

        incidencias = incidencias.filter(
            id_tipo_id=int(tipo_incidencia_id)
        )

    # Filtrar por fecha
    if fecha_incidencia:
        try:
            fecha = datetime.strptime(
                fecha_incidencia, "%Y-%m-%d"
            ).date()
        except ValueError:
            return JsonResponse({
                "estado": "fallo",
                "title": "Fecha inválida",
                "descripcion": "La fecha seleccionada no tiene un formato válido.",
                "icon": "warning"
            })

        incidencias = incidencias.filter(
            fecha_hora__date=fecha
        )

    incidencias = incidencias.order_by("-fecha_hora")

    datos = []

    for registro in incidencias:
        vigilantes_asociados = list(
            registro.varios_vigilantes.all()
        )

        nombres_vigilantes = [
            f"{vigilante.id_usuario.nombres} "
            f"{vigilante.id_usuario.apellidos}"
            for vigilante in vigilantes_asociados
        ]

        datos.append({
            "id": registro.id_incidencia,
            "usuario": (
                ", ".join(nombres_vigilantes)
                if nombres_vigilantes
                else "No asignado"
            ),
            "turno": (
                registro.id_turno.nombre
                if registro.id_turno
                else "Sin turno"
            ),
            "tipo": registro.id_tipo.nombre,
            "fecha_hora": (
                timezone.localtime(
                    registro.fecha_hora
                ).strftime("%d/%m/%Y %H:%M")
                if registro.fecha_hora
                else ""
            ),
            "titulo": registro.titulo,
            "descripcion": registro.descripcion or ""
        })

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin incidencias",
            "descripcion": (
                "No existen incidencias que coincidan "
                "con los filtros seleccionados para su turno."
            ),
            "icon": "warning",
            "incidencias": []
        })

    return JsonResponse({
        "estado": "exito",
        "incidencias": datos
    })

def buscar_datos_incidencia(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "Esta operación requiere una solicitud POST.",
            "icon": "warning"
        }, status=405)

    id_incidencia = request.POST.get("id_incidencia", "").strip()

    cedula = request.session.get("cedula_identidad")

    # Validar la sesión del supervisor
    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al usuario.",
            "icon": "warning"
        })

    # Validar el identificador
    if not id_incidencia:
        return JsonResponse({
            "estado": "fallo",
            "title": "Incidencia no especificada",
            "descripcion": "No se recibió el identificador de la incidencia.",
            "icon": "warning"
        })

    if not id_incidencia.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El identificador de la incidencia no es válido.",
            "icon": "warning"
        })

    try:
        # Obtener al supervisor vigente y su turno
        supervisor = (
            supervisores_encargados.objects
            .select_related(
                "id_usuario",
                "id_turno"
            )
            .get(
                id_usuario__cedula_identidad=cedula,
                vigencia=True
            )
        )

        # Buscar la incidencia correspondiente al turno
        registro = (
            incidencia.objects
            .select_related(
                "id_tipo",
                "id_turno",
                "id_supervisor"
            )
            .get(
                id_incidencia=int(id_incidencia),
                id_turno_id=supervisor.id_turno_id
            )
        )

        # Preparar los datos para el formulario
        datos = {
            "id_incidencia": registro.id_incidencia,
            "id_tipo": registro.id_tipo_id,
            "tipo": registro.id_tipo.nombre,
            "fecha_hora": (
                timezone.localtime(
                    registro.fecha_hora
                ).strftime("%Y-%m-%dT%H:%M")
                if registro.fecha_hora
                else ""
            ),
            "titulo": registro.titulo,
            "descripcion": registro.descripcion or "",
            "solucion": registro.solucion or "",
            "fecha_cierre": (
                timezone.localtime(
                    registro.fecha_cierre
                ).strftime("%Y-%m-%dT%H:%M")
                if registro.fecha_cierre
                else ""
            ),
            "vigilantes": [
                {
                    "id_vigilante": vigilante.id_vigilante,
                    "id_usuario": vigilante.id_usuario_id,
                    "cedula": vigilante.id_usuario.cedula_identidad,
                    "nombres": vigilante.id_usuario.nombres,
                    "apellidos": vigilante.id_usuario.apellidos
                }
                for vigilante in registro.varios_vigilantes.select_related(
                    "id_usuario"
                ).all()
            ]
        }

        return JsonResponse({
            "estado": "exito",
            "incidencia": datos
        })

    except supervisores_encargados.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": (
                "No existe un supervisor encargado vigente "
                "asociado a la sesión."
            ),
            "icon": "warning"
        })

    except incidencia.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Incidencia no encontrada",
            "descripcion": (
                "La incidencia no existe o no pertenece "
                "al turno del supervisor autenticado."
            ),
            "icon": "warning"
        })
    
def modificar_datos_incidencia(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "Esta operación requiere una solicitud POST.",
            "icon": "warning"
        })

    id_incidencia = request.POST.get("id", "").strip()
    tipo = request.POST.get("tipos", "").strip()
    titulo = request.POST.get("titulo_m", "").strip()
    descripcion = request.POST.get("descripcion", "").strip()

    controles = [
        (id_incidencia, "Identificador", "No se especificó la incidencia a modificar."),
        (tipo, "Tipo de incidencia", "Por favor, seleccione un tipo de incidencia."),
        (titulo, "Título de incidencia", "Por favor, ingrese el título de la incidencia."),
        (descripcion, "Descripción", "Por favor, ingrese la descripción de la incidencia.")
    ]

    for valor, titulo_err, mensaje in controles:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": titulo_err,
                "descripcion": mensaje,
                "icon": "warning"
            })

    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al usuario.",
            "icon": "warning"
        })

    try:
        id_incidencia = int(id_incidencia)
        tipo = int(tipo)

        if id_incidencia <= 0 or tipo <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos inválidos",
            "descripcion": (
                "El identificador de la incidencia o el tipo "
                "seleccionado no es válido."
            ),
            "icon": "warning"
        })

    try:
        with transaction.atomic():
            supervisor = (
                supervisores_encargados.objects
                .select_related("id_usuario", "id_turno")
                .get(
                    id_usuario__cedula_identidad=cedula,
                    vigencia=True
                )
            )

            incidencia_modificar = (
                incidencia.objects
                .select_for_update()
                .select_related(
                    "id_tipo",
                    "id_turno",
                    "id_supervisor"
                )
                .get(
                    pk=id_incidencia,
                    id_turno_id=supervisor.id_turno_id
                )
            )

            tipo_obj = tipo_incidencia.objects.get(pk=tipo)

            incidencia_modificar.id_tipo = tipo_obj
            incidencia_modificar.titulo = titulo
            incidencia_modificar.descripcion = descripcion

            incidencia_modificar.save(
                update_fields=[
                    "id_tipo",
                    "titulo",
                    "descripcion"
                ]
            )

            bitacora.objects.create(
                id_usuario=supervisor.id_usuario,
                accion=(
                    f"Modificó la incidencia "
                    f"'{incidencia_modificar.titulo}' - "
                    f"Tipo: {tipo_obj.nombre}"
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Actualización exitosa",
            "descripcion": (
                "Los datos de la incidencia fueron "
                "modificados exitosamente."
            ),
            "icon": "success"
        })

    except supervisores_encargados.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": (
                "No existe un supervisor encargado vigente "
                "asociado a la sesión."
            ),
            "icon": "warning"
        })

    except incidencia.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Incidencia no encontrada",
            "descripcion": (
                "La incidencia no existe o no pertenece "
                "al turno del supervisor autenticado."
            ),
            "icon": "warning"
        })

    except tipo_incidencia.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo de incidencia no encontrado",
            "descripcion": (
                "No se encuentra registrado el tipo de "
                "incidencia seleccionado."
            ),
            "icon": "error"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error imprevisto",
            "descripcion": (
                "Ocurrió un error al intentar actualizar "
                "la incidencia. Inténtelo nuevamente."
            ),
            "icon": "error"
        })

# ACEPTAR, EN PROCESO O RESUELTO ADMINISTRADOR(A)

def gestion_incidencia_administrativo(request):
    return render(request, "Encargado_Administrativo/visualizar_incidencias.html")

def incidencias_recibidos_vigilantes(request):
    tipo_incidencia = request.POST.get("tipo_incidencia", "").strip()
    turno_laboral = request.POST.get("turno_laboral", "").strip()

    incidencias = incidencia.objects.select_related(
        "id_tipo",
        "id_turno",
        "id_supervisor__id_usuario"
    )

    if tipo_incidencia:
        if not tipo_incidencia.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Tipo de incidencia inválido",
                "descripcion": (
                    "El tipo de incidencia seleccionado "
                    "no es válido."
                ),
                "icon": "warning"
            })

        incidencias = incidencias.filter(
            id_tipo_id=int(tipo_incidencia)
        )

    if turno_laboral:
        if not turno_laboral.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Turno inválido",
                "descripcion": (
                    "El turno laboral seleccionado "
                    "no es válido."
                ),
                "icon": "warning"
            })

        incidencias = incidencias.filter(
            id_turno_id=int(turno_laboral)
        )

    incidencias = incidencias.order_by("-fecha_hora")

    datos = []
    for item in incidencias:
        supervisor = item.id_supervisor
        usuario = supervisor.id_usuario if supervisor else None

        nombre_usuario = (
            f"{usuario.nombres} {usuario.apellidos}"
            if usuario
            else "No disponible"
        )

        turno = (
            item.id_turno.nombre
            if item.id_turno
            else "No disponible"
        )

        fecha_hora = (
            timezone.localtime(
                item.fecha_hora
            ).strftime("%d/%m/%Y %H:%M")
            if item.fecha_hora
            else "No registrada"
        )

        datos.append({
            "id": item.id_incidencia,
            "usuario": nombre_usuario,
            "turno": turno,
            "tipo": item.id_tipo.nombre,
            "fecha_hora": fecha_hora,
            "titulo": item.titulo,
            "descripcion": item.descripcion or "Sin descripción"
        })

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin incidencias",
            "descripcion": (
                "No existen incidencias que coincidan "
                "con los filtros seleccionados."
            ),
            "icon": "warning",
            "incidencias": []
        })

    return JsonResponse({
        "estado": "exito",
        "incidencias": datos
    })

def buscar_incidencia(request):
    if request.method == "POST":
        id_incidencia = request.POST.get("id_incidencia", "").strip()

        if not id_incidencia:
            return JsonResponse({
                "estado": "fallo",
                "title": "Incidencia no especificada",
                "descripcion": (
                    "No se recibió el identificador de la incidencia."
                ),
                "icon": "warning"
            })

        try:
            registro = (
                incidencia.objects
                .select_related(
                    "id_tipo",
                    "id_turno",
                    "id_supervisor__id_usuario"
                )
                .get(id_incidencia=id_incidencia)
            )

            supervisor = registro.id_supervisor
            usuario = (
                supervisor.id_usuario
                if supervisor
                else None
            )

            datos = {
                "id_incidencia": registro.id_incidencia,

                "usuario": (
                    f"{usuario.nombres} {usuario.apellidos}"
                    if usuario
                    else "No asignado"
                ),

                "ci_usuario": (
                    usuario.cedula_identidad
                    if usuario
                    else ""
                ),

                "turno": (
                    registro.id_turno.nombre
                    if registro.id_turno
                    else "No asignado"
                ),

                "id_tipo": registro.id_tipo.id_tipo,
                "tipo": registro.id_tipo.nombre,

                "fecha_hora": (
                    timezone.localtime(
                        registro.fecha_hora
                    ).strftime("%Y-%m-%d %H:%M")
                    if registro.fecha_hora
                    else ""
                ),

                "titulo": registro.titulo,

                "descripcion": (
                    registro.descripcion
                    if registro.descripcion
                    else "Sin descripción registrada."
                )
            }

            return JsonResponse({
                "estado": "exito",
                "incidencia": datos
            })

        except incidencia.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Incidencia no encontrada",
                "descripcion": (
                    "La incidencia solicitada no existe."
                ),
                "icon": "warning"
            })

        except (ValueError, TypeError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Identificador inválido",
                "descripcion": (
                    "El identificador de la incidencia no es válido."
                ),
                "icon": "warning"
            })
    
# REPORTE DE LAS LITAS INCIDENCIAS REGISTRADAS POR EL VIGILANTE

def lista_incidencias_pdf(request):
    if request.method == "POST":
        fecha = request.POST.get("fecha_incidencia", "").strip()
        tipo = request.POST.get("tipo_incidencia", "").strip()

        cedula = request.session.get("cedula_identidad")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "title": "Sesión no válida",
                "descripcion": "No se pudo identificar al usuario.",
                "icon": "warning"
            })

        try:
            supervisor = supervisores_encargados.objects.select_related(
                "id_usuario",
                "id_turno"
            ).get(
                id_usuario__cedula_identidad=cedula,
                vigencia=True
            )

        except supervisores_encargados.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Supervisor no encontrado",
                "descripcion": (
                    "No existe un supervisor encargado vigente "
                    "asociado a la sesión."
                ),
                "icon": "warning"
            })

        registros = (
            incidencia.objects
            .filter(
                id_turno_id=supervisor.id_turno_id
            )
            .select_related(
                "id_tipo",
                "id_turno",
                "id_supervisor",
                "id_supervisor__id_usuario"
            )
            .prefetch_related(
                "vigilantes_asignados__id_vigilante__id_usuario"
            )
            .order_by("-fecha_hora")
            .distinct()
        )

        if fecha:
            registros = registros.filter(
                fecha_hora__date=fecha
            )

        if tipo:
            registros = registros.filter(
                id_tipo_id=tipo
            )

        if not registros.exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Sin incidencias",
                "descripcion": (
                    "No existen incidencias que coincidan "
                    "con los filtros seleccionados."
                ),
                "icon": "warning"
            })

        response = HttpResponse(
            content_type="application/pdf"
        )

        response["Content-Disposition"] = (
            'inline; filename="lista_incidencias.pdf"'
        )

        documento = SimpleDocTemplate(
            response,
            pagesize=landscape(legal),
            rightMargin=30,
            leftMargin=30,
            topMargin=160,
            bottomMargin=35
        )

        estilos = getSampleStyleSheet()

        estilo_titulo = ParagraphStyle(
            "TituloIncidencias",
            parent=estilos["Heading2"],
            fontName="Times-Bold",
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=colors.white
        )

        estilo_encabezado = ParagraphStyle(
            "EncabezadoIncidencias",
            parent=estilos["Normal"],
            fontName="Times-Bold",
            fontSize=12,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.white
        )

        estilo_celda = ParagraphStyle(
            "CeldaIncidencias",
            parent=estilos["Normal"],
            fontName="Times-Roman",
            fontSize=12,
            leading=13,
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
                Paragraph(
                    "LISTA DE INCIDENCIAS",
                    estilo_titulo
                ),
                "",
                "",
                "",
                "",
                ""
            ],
            [
                Paragraph("N.º", estilo_encabezado),
                Paragraph("TÍTULO", estilo_encabezado),
                Paragraph("TIPO DE INCIDENCIA", estilo_encabezado),
                Paragraph("DESCRIPCIÓN", estilo_encabezado),
                Paragraph("FECHA Y HORA", estilo_encabezado),
                Paragraph("VIGILANTE", estilo_encabezado)
            ]
        ]

        for numero, registro in enumerate(registros, start=1):
            descripcion = (
                registro.descripcion
                if registro.descripcion
                else "Sin descripción"
            )

            fecha_hora = (
                timezone.localtime(
                    registro.fecha_hora
                ).strftime("%d/%m/%Y %H:%M:%S")
                if registro.fecha_hora
                else "No registrada"
            )

            nombres_vigilantes = [
                (
                    f"{asignacion.id_vigilante.id_usuario.nombres} "
                    f"{asignacion.id_vigilante.id_usuario.apellidos}"
                )
                for asignacion in registro.vigilantes_asignados.all()
            ]
            vigilante = ", ".join(nombres_vigilantes) or "No asignado"

            datos_tabla.append([
                Paragraph(str(numero), estilo_celda),
                Paragraph(
                    str(registro.titulo),
                    estilo_celda
                ),
                Paragraph(
                    str(registro.id_tipo.nombre),
                    estilo_celda
                ),
                Paragraph(
                    str(descripcion),
                    estilo_celda
                ),
                Paragraph(
                    fecha_hora,
                    estilo_celda
                ),
                Paragraph(
                    str(vigilante),
                    estilo_celda
                )
            ])

        tabla = Table(
            datos_tabla,
            colWidths=[
                35,
                170,
                130,
                280,
                120,
                150
            ],
            repeatRows=2,
            hAlign="CENTER"
        )

        tabla.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#58A5C4")),

            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
            ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
            ("ALIGN", (0, 1), (-1, 1), "CENTER"),
            ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

            ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
            ("ALIGN", (0, 2), (-1, -1), "CENTER"),
            ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
            ("INNERGRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7)
        ]))

        elementos = [
            Spacer(1, 15),
            tabla
        ]

        documento.build(
            elementos,
            onFirstPage=lambda canvas, documento:
                encabezado_incidencia_pdf(
                    canvas,
                    documento,
                    ruta_logo
                ),
            onLaterPages=lambda canvas, documento:
                encabezado_incidencia_pdf(
                    canvas,
                    documento,
                    ruta_logo
                )
        )

        return response

def encabezado_incidencia_pdf(canvas, documento, ruta_logo):
    canvas.saveState()
        
    ancho_pagina, alto_pagina = landscape(letter)

    # LOGO (Dimensiones y posición original)
    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            60,
            alto_pagina - 210,
            width=250,
            height=250,
            preserveAspectRatio=True,
            mask="auto"
        )

    # TITULO EMPRESA (Dimensiones y posición original)
    canvas.setFont(
        "Times-Bold",
        25
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        335,
        alto_pagina - 110,
        "EMPRESA HIELO CAIPE C.A"
    )

    # FECHA (Dimensiones y posición original)
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

    canvas.setFont(
        "Times-Bold",
        14
    )

    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        390,
        alto_pagina - 170,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

def lista_incidencias_admin_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": (
                "Esta operación requiere una solicitud POST."
            ),
            "icon": "warning"
        }, status=405)

    tipo_incidencia = request.POST.get("tipo_incidencia", "").strip()
    turno_laboral = request.POST.get("turno_laboral", "").strip()

    if tipo_incidencia and not tipo_incidencia.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo de incidencia inválido",
            "descripcion": (
                "El tipo de incidencia seleccionado no es válido."
            ),
            "icon": "warning"
        })

    if turno_laboral and not turno_laboral.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Turno inválido",
            "descripcion": (
                "El turno laboral seleccionado no es válido."
            ),
            "icon": "warning"
        })

    registros = (
        incidencia.objects
        .select_related(
            "id_tipo",
            "id_turno",
            "id_supervisor__id_usuario"
        )
        .prefetch_related(
            "varios_vigilantes__id_usuario"
        )
    )

    if tipo_incidencia:
        registros = registros.filter(
            id_tipo_id=int(tipo_incidencia)
        )

    if turno_laboral:
        registros = registros.filter(
            id_turno_id=int(turno_laboral)
        )

    registros = registros.order_by("-fecha_hora")

    if not registros.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin incidencias",
            "descripcion": (
                "No existen incidencias que coincidan "
                "con los filtros seleccionados."
            ),
            "icon": "warning"
        })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        'inline; filename="lista_incidencias.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(legal),
        rightMargin=30,
        leftMargin=30,
        topMargin=160,
        bottomMargin=35
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloIncidencias",
        parent=estilos["Heading2"],
        fontName="Times-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoIncidencias",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaIncidencias",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
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
            Paragraph("LISTA DE INCIDENCIAS", estilo_titulo),
            "", "", "", "", ""
        ],
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("TÍTULO", estilo_encabezado),
            Paragraph("TIPO DE INCIDENCIA", estilo_encabezado),
            Paragraph("DESCRIPCIÓN", estilo_encabezado),
            Paragraph("FECHA Y HORA", estilo_encabezado),
            Paragraph("VIGILANTES ASIGNADOS", estilo_encabezado)
        ]
    ]

    for numero, registro in enumerate(registros, start=1):
        descripcion = (
            registro.descripcion or "Sin descripción"
        )

        fecha_hora = (
            timezone.localtime(
                registro.fecha_hora
            ).strftime("%d/%m/%Y %H:%M:%S")
            if registro.fecha_hora
            else "No registrada"
        )

        vigilantes = registro.varios_vigilantes.all()

        nombres_vigilantes = [
            f"{vigilante.id_usuario.nombres} "
            f"{vigilante.id_usuario.apellidos}"
            for vigilante in vigilantes
            if vigilante.id_usuario
        ]

        texto_vigilantes = (
            ", ".join(nombres_vigilantes)
            if nombres_vigilantes
            else "Sin vigilantes asignados"
        )

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(str(registro.titulo), estilo_celda),
            Paragraph(str(registro.id_tipo.nombre), estilo_celda),
            Paragraph(str(descripcion), estilo_celda),
            Paragraph(fecha_hora, estilo_celda),
            Paragraph(str(texto_vigilantes), estilo_celda)
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[35, 150, 125, 260, 125, 190],
        repeatRows=2,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#58A5C4")),

        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7)
    ]))

    elementos = [
        Spacer(1, 15),
        tabla
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_incidencia_admin_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_incidencia_admin_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response
    
def encabezado_incidencia_admin_pdf(canvas, documento, ruta_logo):
    canvas.saveState()
    
    ancho_pagina, alto_pagina = landscape(letter)

    # LOGO (Dimensiones y posición original)
    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            60,
            alto_pagina - 210,
            width=250,
            height=250,
            preserveAspectRatio=True,
            mask="auto"
        )

    # TITULO EMPRESA (Dimensiones y posición original)
    canvas.setFont(
        "Times-Bold",
        25
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        335,
        alto_pagina - 110,
        "EMPRESA HIELO CAIPE C.A"
    )

    # FECHA (Dimensiones y posición original)
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

    canvas.setFont(
        "Times-Bold",
        14
    )

    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        390,
        alto_pagina - 170,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()