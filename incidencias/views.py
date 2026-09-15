from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime

from incidencias.models import tipo_incidencia, incidencia, solucion_incidencia
from inicio_sesion.models import perfil_usuario, usuarios, bitacora, perfiles

import os
from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    KeepTogether
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
        usuario = usuarios.objects.get(
            cedula_identidad=cedula
        )

        fechas = (
            incidencia.objects
            .filter(
                id_perfil_usuario__id_usuario=usuario
            )
            .values_list("fecha_hora", flat=True)
            .order_by("-fecha_hora")
        )

        fechas_unicas = sorted(
            {
                timezone.localtime(fecha).date()
                for fecha in fechas
                if fecha
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

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario no encontrado",
            "descripcion": "No se encontró el usuario asociado a la sesión.",
            "icon": "error"
        })

# REGISTRAR Y GESTIONAR INCIDENCIA VIGILANTE

def registrar_incidencias(request):
    if request.method == "POST":
        fecha_hora_incidencia = request.POST.get("fecha_hora_incidencia")
        tipo_incidencias = request.POST.get("tipos_incidencias")
        titulo_incidencia = request.POST.get("titulo_incidencia")
        descripcion_incidencia = request.POST.get("descripcion_incidencia")

        controles = [
            (fecha_hora_incidencia, "Fecha y Hora de la Incidencia", "Por favor, ingrese la fecha y hora de la incidencia."),
            (tipo_incidencias, "Tipo de Incidencia", "Por favor, seleccione uno de los tipos de incidencia."),
            (titulo_incidencia, "Titulo de Incidencia", "Por favor, ingrese el titulo de incidencia."),
            (descripcion_incidencia, "Descripción de la Incidencia", "Por favor, ingrese la descripción de la incidencia."),
        ]

        for valor, titulo, mensaje in controles:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": titulo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        try:
            tipo_obj = tipo_incidencia.objects.get(id_tipo=tipo_incidencias)
        except tipo_incidencia.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "No se encuentra registrado el tipo de incidencia seleccionado.",
                "icon": "error"
            })   

        try:
            with transaction.atomic():
                usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))
                
                perfi_vigilante = perfiles.objects.get(pk=5)
        
                empleado = perfil_usuario.objects.get(id_usuario=usuario, id_perfil=perfi_vigilante)

                incidencia.objects.create(
                    id_tipo=tipo_obj,
                    id_perfil_usuario=empleado,
                    fecha_hora=fecha_hora_incidencia,
                    titulo=titulo_incidencia,
                    descripcion=descripcion_incidencia,
                )
    
                accion = (
                    f"Registró una nueva incidencia: "
                    f"'{titulo_incidencia}' - "
                    f"Tipo: {tipo_obj.nombre}"
                )
    
                bitacora.objects.create(
                    id_usuario=usuario,
                    accion=accion
                )
    
                return JsonResponse({
                    "estado": "exito",
                    "title": "Éxito",
                    "descripcion": "Se registraron los datos de la incidencia exitosamente.",
                    "icon": "success"
                })
        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": f"Ocurrio un error: {e}.",
                "icon": "error"
            })

    return render(request, "Vigilante/registrar_incidencias.html")

def gestionar_incidencias(request):
    return render(request, "Vigilante/gestion_incidencia.html")

def incidencias_vigilante(request):
    tipo = request.POST.get("tipo_incidencia", "").strip()
    fecha = request.POST.get("fecha_incidencia", "").strip()

    try:
        usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))

        incidencias = (
            incidencia.objects
            .filter(
                id_perfil_usuario__id_usuario=usuario
            )
            .select_related("id_tipo")
        )

        if tipo:
            incidencias = incidencias.filter(id_tipo_id=tipo)

        if fecha:
            incidencias = incidencias.filter(fecha_hora__date=fecha)

        incidencias = incidencias.order_by("-fecha_hora")

        datos = [
            {
                "id_incidencia": registro.id_incidencia,
                "tipo": registro.id_tipo.nombre,
                "fecha_hora": (
                    timezone.localtime(registro.fecha_hora).strftime("%Y-%m-%d %H:%M")
                    if registro.fecha_hora
                    else ""
                ),
                "titulo": registro.titulo,
                "descripcion": registro.descripcion or "",
                "estado": registro.estado,
                "solucion": registro.solucion or "",
                "fecha_resolucion": (
                    timezone.localtime(
                        registro.fecha_resolucion
                    ).strftime("%Y-%m-%d %H:%M")
                    if registro.fecha_resolucion
                    else ""
                )
            }
            for registro in incidencias
        ]

        return JsonResponse({
            "estado": "exito",
            "incidencias": datos
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario no encontrado",
            "descripcion": "No se encontró el usuario asociado a la sesión.",
            "icon": "error"
        })

def buscar_datos_incidencia(request):
    if request.method == "POST":
        id_incidencia = request.POST.get("id_incidencia", "").strip()

        if not id_incidencia:
            return JsonResponse({
                "estado": "fallo",
                "title": "Incidencia no especificada",
                "descripcion": "No se recibió el identificador de la incidencia.",
                "icon": "warning"
            })

        try:
            usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))

            registro = (
                incidencia.objects
                .select_related(
                    "id_tipo",
                    "id_perfil_usuario",
                    "id_perfil_usuario__id_usuario",
                    "id_perfil_usuario__id_perfil"
                )
                .get(
                    id_incidencia=id_incidencia,
                    id_perfil_usuario__id_usuario=usuario
                )
            )

            datos = {
                "id_incidencia": registro.id_incidencia,
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
                "descripcion": registro.descripcion,
                "estado": registro.estado,
                "solucion": registro.solucion or "La incidencia aún no ha sido revisada ni atendida.",
                "fecha_resolucion": (
                    timezone.localtime(
                        registro.fecha_resolucion
                    ).strftime("%Y-%m-%d %H:%M")
                    if registro.fecha_resolucion
                    else ""
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
                "descripcion": "La incidencia no existe o no está asociada al usuario.",
                "icon": "warning"
            })

        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario no encontrado",
                "descripcion": "No se encontró el usuario asociado a la sesión.",
                "icon": "error"
            })

def modificar_datos_incidencia(request):
    if request.method == "POST":
        id_incidencia = request.POST.get("id")
        tipo = request.POST.get("tipos")
        fecha_hora_str = request.POST.get("fecha_hora")
        titulo = request.POST.get("titulo_m")
        descripcion = request.POST.get("descripcion")

        # 1. Validaciones iniciales
        controles = [
            (id_incidencia, "ID Inválido", "No se especificó la incidencia a modificar."),
            (tipo, "Tipo de Incidencia", "Por favor, seleccione uno de los tipos de incidencia."),
            (fecha_hora_str, "Fecha y Hora de la Incidencia", "Por favor, ingrese la fecha y hora de la incidencia."),
            (titulo, "Título de Incidencia", "Por favor, ingrese el título de la incidencia."),
            (descripcion, "Descripción de la Incidencia", "Por favor, ingrese la descripción de la incidencia."),
        ]

        for valor, titulo_err, mensaje in controles:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": titulo_err,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        try:
            with transaction.atomic():
                # Obtener tipo de incidencia
                tipo_obj = tipo_incidencia.objects.get(id_tipo=tipo)

                # Procesar fecha y zona horaria
                fecha_hora = datetime.fromisoformat(fecha_hora_str)
                if timezone.is_naive(fecha_hora):
                    fecha_hora = timezone.make_aware(
                        fecha_hora,
                        timezone.get_current_timezone()
                    )

                # Obtener usuario de la sesión para la bitácora
                usuario = usuarios.objects.get(
                    cedula_identidad=request.session.get("cedula_identidad")
                )

                # 2. Búsqueda por la clave primaria obtenida del formulario
                incidencia_modificar = incidencia.objects.get(pk=id_incidencia)

                # 3. Asignación y guardado
                incidencia_modificar.id_tipo = tipo_obj
                incidencia_modificar.fecha_hora = fecha_hora
                incidencia_modificar.titulo = titulo
                incidencia_modificar.descripcion = descripcion
                incidencia_modificar.estado = "Modificada"

                incidencia_modificar.save()

                # Registro en la bitácora
                bitacora.objects.create(
                    id_usuario=usuario,
                    accion=(
                        f"Modificó la incidencia "
                        f"'{incidencia_modificar.titulo}' - "
                        f"Tipo: {tipo_obj.nombre}"
                    )
                )

                return JsonResponse({
                    "estado": "exito",
                    "title": "Éxito",
                    "descripcion": "Los datos de la incidencia fueron modificados exitosamente.",
                    "icon": "success"
                })

        except tipo_incidencia.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "No se encuentra registrado el tipo de incidencia seleccionado.",
                "icon": "error"
            })

        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario no encontrado",
                "descripcion": "No se encontró el usuario asociado a la sesión actual.",
                "icon": "error"
            })

        except incidencia.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Incidencia no encontrada",
                "descripcion": "La incidencia especificada no existe en la base de datos.",
                "icon": "warning"
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error imprevisto",
                "descripcion": f"Ocurrió un error al intentar actualizar: {str(e)}",
                "icon": "error"
            })

# ACEPTAR, EN PROCESO O RESUELTO ADMINISTRADOR(A)

def gestion_incidencia_admin(request):
    return render(request, "Administrador/gestionar_incidencia.html")

def incidencias_recibidos_vigilantes(request):
    tipo_incidencia = request.POST.get("tipo_incidencia", "").strip()
    turno_laboral = request.POST.get("turno_laboral", "").strip()

    incidencias = incidencia.objects.all()

    if tipo_incidencia:
        incidencias = incidencias.filter(id_tipo_id=tipo_incidencia)

    if turno_laboral:
        incidencias = incidencias.filter(id_perfil_usuario__id_turno_id=turno_laboral)

    incidencias = incidencias.select_related(
        "id_perfil_usuario__id_usuario",
        "id_perfil_usuario__id_perfil",
        "id_perfil_usuario__id_turno",
        "id_tipo"
    ).order_by("-fecha_hora")

    datos = []

    for item in incidencias:
        datos.append({
            "id": item.id_incidencia,
            "usuario": (
                f"{item.id_perfil_usuario.id_usuario.nombres} "
                f"{item.id_perfil_usuario.id_usuario.apellidos}"
            ),
            "perfil": item.id_perfil_usuario.id_perfil.perfil,
            "turno": (
                item.id_perfil_usuario.id_turno.nombre
                if item.id_perfil_usuario.id_turno
                else None
            ),
            "tipo": item.id_tipo.nombre,
            "fecha_hora": (
                item.fecha_hora.strftime("%d/%m/%Y %H:%M")
                if item.fecha_hora
                else None
            ),
            "titulo": item.titulo,
            "descripcion": item.descripcion,
            "estado": item.estado,
        })

    return JsonResponse({
        "estado": True,
        "incidencias": datos
    })

def buscar_incidencia(request):
    if request.method == "POST":
        id_incidencia = request.POST.get("id_incidencia", "").strip()

        if not id_incidencia:
            return JsonResponse({
                "estado": "fallo",
                "title": "Incidencia no especificada",
                "descripcion": "No se recibió el identificador de la incidencia.",
                "icon": "warning"
            })

        try:
            registro = (
                incidencia.objects
                .select_related(
                    "id_tipo",
                    "id_perfil_usuario__id_usuario",
                    "id_perfil_usuario__id_perfil",
                    "id_perfil_usuario__id_turno",
                    "id_usuario_acepta__id_usuario",
                    "id_usuario_acepta__id_perfil",
                    "id_usuario_acepta__id_turno"
                )
                .get(id_incidencia=id_incidencia)
            )

            datos = {
                "id_incidencia": registro.id_incidencia,

                "usuario": (
                    f"{registro.id_perfil_usuario.id_usuario.nombres} "
                    f"{registro.id_perfil_usuario.id_usuario.apellidos}"
                ),

                "perfil": registro.id_perfil_usuario.id_perfil.perfil,

                "turno": (
                    registro.id_perfil_usuario.id_turno.nombre
                    if registro.id_perfil_usuario.id_turno
                    else ""
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
                "descripcion": registro.descripcion,
                "estado": registro.estado,
                "solucion": (
                    registro.solucion
                    if registro.solucion
                    else "La incidencia aún no tiene una solución registrada."
                ),
                "fecha_resolucion": (
                    timezone.localtime(
                        registro.fecha_resolucion
                    ).strftime("%Y-%m-%d %H:%M")
                    if registro.fecha_resolucion
                    else "La incidencia aún no ha sido resuelta."
                ),
                "usuario_acepta": (
                    f"{registro.id_usuario_acepta.id_usuario.nombres} "
                    f"{registro.id_usuario_acepta.id_usuario.apellidos}"
                    if registro.id_usuario_acepta
                    else "La incidencia aún no ha sido aceptada."
                ),
                "perfil_acepta": (
                    registro.id_usuario_acepta.id_perfil.perfil
                    if registro.id_usuario_acepta
                    else "Sin responsable asignado."
                ),
                "turno_acepta": (
                    registro.id_usuario_acepta.id_turno.nombre
                    if registro.id_usuario_acepta
                    and registro.id_usuario_acepta.id_turno
                    else "Sin turno asignado."
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
                "descripcion": "La incidencia no existe.",
                "icon": "warning"
            })

def registrar_solucion(request):
    if request.method == "POST":
        id_incidencia = request.POST.get("id_incidencia", "").strip()
        estado_incidencia = request.POST.get("estado_incidencia", "").strip()
        descripcion_solucion = request.POST.get(
            "solucion_incidencia", ""
        ).strip()

        if not id_incidencia:
            return JsonResponse({
                "estado": "fallo",
                "title": "Incidencia no especificada",
                "descripcion": "No se recibió el identificador de la incidencia.",
                "icon": "warning"
            })

        if not estado_incidencia:
            return JsonResponse({
                "estado": "fallo",
                "title": "Estado no especificado",
                "descripcion": "Debe seleccionar un estado para la incidencia.",
                "icon": "warning"
            })

        if not descripcion_solucion:
            return JsonResponse({
                "estado": "fallo",
                "title": "Solución no especificada",
                "descripcion": "Debe ingresar la solución o acción realizada.",
                "icon": "warning"
            })

        try:
            registro = incidencia.objects.get(
                id_incidencia=id_incidencia
            )

            perfil_usuario_actual = perfil_usuario.objects.get(
                id_usuario__cedula_identidad=request.session.get(
                    "cedula_identidad"
                ),
                vigencia=True
            )

            registro.estado = estado_incidencia
            registro.solucion = descripcion_solucion

            if estado_incidencia == "Aceptada":
                registro.id_usuario_acepta = perfil_usuario_actual

            if estado_incidencia == "Resuelta":
                registro.fecha_resolucion = timezone.now()

            registro.save()

            solucion_incidencia.objects.create(
                id_incidencia=registro,
                id_perfil_usuario=perfil_usuario_actual,
                estado=estado_incidencia,
                descripcion=descripcion_solucion
            )

            return JsonResponse({
                "estado": "exito",
                "title": "Incidencia actualizada",
                "descripcion": (
                    "La incidencia fue actualizada y la acción "
                    "fue registrada en el historial."
                ),
                "icon": "success"
            })

        except incidencia.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Incidencia no encontrada",
                "descripcion": "La incidencia no existe.",
                "icon": "warning"
            })

        except perfil_usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No se encontró el usuario asociado a la sesión."
                ),
                "icon": "error"
            })


def historial_soluciones_admin(request):
    return render(request, "Administrador/historial_soluciones.html")

def historial_soluciones(request):
    historial = (
        solucion_incidencia.objects
        .select_related(
            "id_incidencia__id_tipo",
            "id_perfil_usuario__id_usuario",
            "id_perfil_usuario__id_perfil",
            "id_perfil_usuario__id_turno"
        )
        .order_by("-fecha_hora")
    )

    datos = []

    for item in historial:
        datos.append({
            "id_solucion": item.id_solucion,
            "id_incidencia": item.id_incidencia.id_incidencia,
            "usuario": (
                f"{item.id_perfil_usuario.id_usuario.nombres} "
                f"{item.id_perfil_usuario.id_usuario.apellidos}"
            ),
            "perfil": item.id_perfil_usuario.id_perfil.perfil,
            "turno": (
                item.id_perfil_usuario.id_turno.nombre
                if item.id_perfil_usuario.id_turno
                else ""
            ),
            "tipo": item.id_incidencia.id_tipo.nombre,
            "titulo": item.id_incidencia.titulo,
            "estado": item.estado,
            "descripcion": item.descripcion,
            "fecha_hora": (
                timezone.localtime(
                    item.fecha_hora
                ).strftime("%d/%m/%Y %H:%M")
                if item.fecha_hora
                else ""
            )
        })

    return JsonResponse({
        "estado": "exito",
        "historial": datos
    })

# ACEPTAR, EN PROCESO O RESUELTO SUPËRVISORA ENCARGADA

# REPORTE DE LAS LITAS INCIDENCIAS REGISTRADAS POR EL VIGILANTE

def lista_incidencias_pdf(request):
    fecha = request.POST.get("fecha_incidencia", "").strip()
    tipo = request.POST.get("tipo_incidencia", "").strip()

    try:
        usuario = usuarios.objects.get(
            cedula_identidad=request.session.get("cedula_identidad")
        )

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario no encontrado",
            "descripcion": "No se encontró el usuario asociado a la sesión.",
            "icon": "error"
        })

    registros = (
        incidencia.objects
        .filter(
            id_perfil_usuario__id_usuario=usuario
        )
        .select_related(
            "id_tipo",
            "id_perfil_usuario__id_usuario"
        )
        .order_by("-fecha_hora")
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
        topMargin=140,
        bottomMargin=30
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
        textColor=colors.black
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
            Paragraph("ESTADO", estilo_encabezado),
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

        datos_tabla.append([
            Paragraph(
                str(numero),
                estilo_celda
            ),
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
                str(registro.estado),
                estilo_celda
            ),
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[
            35,
            170,
            130,
            280,
            120,
            100
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
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos = [
        Spacer(1, 15),
        tabla
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_intentos_sesion_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_intentos_sesion_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_intentos_sesion_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(legal)

    # LOGO
    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            100,
            alto_pagina - 190,
            width=220,
            height=220,
            preserveAspectRatio=True,
            mask="auto"
        )

    # TITULO EMPRESA
    canvas.setFont(
        "Times-Bold",
        22
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        340,
        alto_pagina - 100,
        "EMPRESA HIELO CAIPE C.A"
    )

    # FECHA
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
        16
    )

    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        350,
        alto_pagina - 150,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()


def detalle_incidencia_pdf(request):
    id_incidencia = request.POST.get("id_incidencia", "").strip()

    if not id_incidencia:
        return JsonResponse({
            "estado": "fallo",
            "title": "Incidencia no especificada",
            "descripcion": "No se recibió el identificador de la incidencia.",
            "icon": "warning"
        })

    try:

        registro = (
            incidencia.objects
            .select_related(
                "id_tipo",
                "id_perfil_usuario",
                "id_perfil_usuario__id_usuario",
                "id_perfil_usuario__id_perfil"
            )
            .get(
                id_incidencia=id_incidencia
            )
        )

    except incidencia.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Incidencia no encontrada",
            "descripcion": "No se encontró la incidencia solicitada.",
            "icon": "warning"
        })

    usuario = registro.id_perfil_usuario.id_usuario
    perfil = registro.id_perfil_usuario.id_perfil

    # INFORMACIÓN DEL EMPLEADO
    datos_empleado = [
        ["Nombres:", usuario.nombres],
        ["Apellidos:", usuario.apellidos],
        ["Cédula de Identidad:", usuario.cedula_identidad],
        ["Perfil:", perfil.perfil.strip()],
    ]

    # INFORMACIÓN DE LA INCIDENCIA
    datos_incidencia = [
        ["Tipo:", registro.id_tipo.nombre],
        ["Título:", registro.titulo],
        ["Fecha y hora:", (
            timezone.localtime(
                registro.fecha_hora
            ).strftime("%d/%m/%Y %H:%M")
            if registro.fecha_hora
            else ""
        )],
        ["Estado:", registro.estado],
        ["Descripción:", registro.descripcion],
        ["Solución:", (
            registro.solucion
            or "La incidencia aún no ha sido revisada ni atendida."
        )],
        ["Fecha de resolución:", (
            timezone.localtime(
                registro.fecha_resolucion
            ).strftime("%d/%m/%Y %H:%M")
            if registro.fecha_resolucion
            else "Pendiente"
        )],
    ]

    # RESPUESTA PDF
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="incidencia_{registro.id_incidencia}.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=130,
        bottomMargin=30
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = estilos["Heading2"]
    estilo_titulo.fontName = "Times-Bold"
    estilo_titulo.fontSize = 14
    estilo_titulo.alignment = TA_CENTER
    estilo_titulo.textColor = colors.white
    estilo_titulo.leading = 18

    def crear_tabla(titulo, datos):
        datos_tabla = [
            [titulo, ""]
        ]

        estilo_campo = ParagraphStyle(
            "Campo",
            fontName="Times-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.white,
        )

        estilo_valor = ParagraphStyle(
            "Valor",
            fontName="Times-Roman",
            fontSize=11,
            leading=14,
        )

        for campo, valor in datos:

            datos_tabla.append([
                Paragraph(
                    str(campo),
                    estilo_campo
                ),
                Paragraph(
                    str(valor or ""),
                    estilo_valor
                )
            ])

        tabla = Table(
            datos_tabla,
            colWidths=[120, 370],
            splitByRow=1
        )

        tabla.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 13),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                ("SPAN", (0, 0), (-1, 0)),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#00445F")),
            ])
        )

        return tabla

    tabla_empleado = crear_tabla(
        "DATOS DEL EMPLEADO",
        datos_empleado
    )

    tabla_incidencia = crear_tabla(
        "DATOS DE LA INCIDENCIA",
        datos_incidencia
    )

    elementos = [

        KeepTogether([
            tabla_empleado,
            Spacer(1, 15)
        ]),

        KeepTogether([
            tabla_incidencia
        ])
    ]

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

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
    y_logo = letter[1] - 160

    ancho_logo = 180
    alto_logo = 180

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
    