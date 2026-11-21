from django.shortcuts import render
from django.http import JsonResponse, HttpResponse

from inicio_sesion.models import usuarios
from inicio_sesion.models import personal_limpieza, supervisores_encargados, despachadores, vigilantes, propietarios, encargados_administrativos, atencion_cliente
from asignaciones.models import entrega_equipos

import os
from django.conf import settings
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader

# VISUALIZACIÓN Y REPORTE SUPERVISOR ENCARGADO

def visualizar_empleado_supervisor(request):
    if request.method != "POST":
        return render(
            request,
            "Modulos/Empleados/Supervisor/visualizar_empleados.html"
        )

    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al usuario.",
            "icon": "warning"
        })

    nacionalidad = request.POST.get("nacionalidad", "").strip()
    cedula = request.POST.get("cedula", "").strip()
    perfil = request.POST.get("perfil", "").strip()

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
            "descripcion": (
                "No existe un Supervisor Encargado activo "
                "asociado a la sesión."
            ),
            "icon": "warning"
        })

    turno_id = supervisor.id_turno_id

    perfiles_validos = (
        "Personal de Limpieza",
        "Despachador",
        "Vigilante"
    )

    if perfil and perfil not in perfiles_validos:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil inválido",
            "descripcion": "El perfil seleccionado no es válido.",
            "icon": "warning"
        })

    datos = []

    def coincide_cedula(usuario):
        if nacionalidad and cedula:
            return usuario.cedula_identidad == f"{nacionalidad}-{cedula}"
        return True

    # PERSONAL DE LIMPIEZA
    if not perfil or perfil == "Personal de Limpieza":
        empleados = (
            personal_limpieza.objects
            .select_related("id_usuario", "id_turno")
            .filter(
                vigencia=True,
                id_turno_id=turno_id
            )
        )

        for empleado in empleados:
            usuario = empleado.id_usuario

            if not coincide_cedula(usuario):
                continue

            datos.append({
                "id": usuario.id_usuario,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula": usuario.cedula_identidad,
                "perfil": "Personal de Limpieza",
                "turno": empleado.id_turno.nombre
            })

    # DESPACHADORES
    if not perfil or perfil == "Despachador":
        empleados = (
            despachadores.objects
            .select_related("id_usuario", "id_turno")
            .filter(
                vigencia=True,
                id_turno_id=turno_id
            )
        )

        for empleado in empleados:
            usuario = empleado.id_usuario

            if not coincide_cedula(usuario):
                continue

            datos.append({
                "id": usuario.id_usuario,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula": usuario.cedula_identidad,
                "perfil": "Despachador",
                "turno": empleado.id_turno.nombre
            })

    # VIGILANTES
    if not perfil or perfil == "Vigilante":
        empleados = (
            vigilantes.objects
            .select_related("id_usuario", "id_turno")
            .filter(
                vigencia=True,
                id_turno_id=turno_id
            )
        )

        for empleado in empleados:
            usuario = empleado.id_usuario

            if not coincide_cedula(usuario):
                continue

            datos.append({
                "id": usuario.id_usuario,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula": usuario.cedula_identidad,
                "perfil": "Vigilante",
                "turno": empleado.id_turno.nombre
            })

    datos.sort(
        key=lambda empleado: (
            empleado["apellidos"].lower(),
            empleado["nombres"].lower()
        )
    )

    return JsonResponse({
        "estado": "exito",
        "empleados": datos,
        "total": len(datos)
    })
def lista_empleado_supervisor_pdf(request):
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al usuario.",
            "icon": "warning"
        })

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).select_related("id_usuario", "id_turno").first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "No existe un Supervisor Encargado activo asociado a la sesión.",
            "icon": "warning"
        })

    turno_id = supervisor.id_turno_id
    perfil_empleado = request.POST.get("perfil", "").strip()

    modelos_perfiles = (
        ("Personal de Limpieza", personal_limpieza),
        ("Despachador", despachadores),
        ("Vigilante", vigilantes),
    )

    datos = []

    for nombre_perfil, modelo_perfil in modelos_perfiles:
        if perfil_empleado and perfil_empleado != nombre_perfil:
            continue

        empleados = (
            modelo_perfil.objects
            .filter(
                id_turno_id=turno_id,
                vigencia=True
            )
            .select_related("id_usuario", "id_turno")
            .order_by("id_usuario__apellidos", "id_usuario__nombres")
        )

        for empleado in empleados:
            usuario = empleado.id_usuario

            datos.append({
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula": usuario.cedula_identidad,
                "perfil": nombre_perfil,
                "turno": empleado.id_turno.nombre
            })

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin empleados registrados",
            "icon": "warning",
            "descripcion": "No hay empleados registrados para el turno laboral del supervisor encargado."
        })
    
    datos.sort(
        key=lambda empleado: (
            empleado["apellidos"].lower(),
            empleado["nombres"].lower()
        )
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        'inline; filename="lista_empleados_turno.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=130,
        bottomMargin=30
    )

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    datos_tabla = [
        ["LISTA DE EMPLEADOS", "", "", "", "", ""],
        ["N.º", "Nombres", "Apellidos", "C.I", "Perfil", "Turno Laboral"],
    ]

    if datos:
        for numero, dato in enumerate(datos, start=1):
            datos_tabla.append([
                numero,
                dato["nombres"],
                dato["apellidos"],
                dato["cedula"],
                dato["perfil"],
                dato["turno"]
            ])
    else:
        datos_tabla.append([
            "No hay empleados registrados para este turno.",
            "",
            "",
            "",
            "",
            ""
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[35, 85, 85, 70, 125, 120],
        repeatRows=2
    )

    estilo_tabla = [
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
        ("FONTSIZE", (0, 1), (-1, 1), 10),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 10),
        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]

    if not datos:
        estilo_tabla.extend([
            ("SPAN", (0, 2), (-1, 2)),
            ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#00445F")),
            ("FONTNAME", (0, 2), (-1, 2), "Times-Bold"),
        ])

    tabla.setStyle(TableStyle(estilo_tabla))

    documento.build(
        [tabla],
        onFirstPage=lambda canvas, documento:
            encabezado_lista_supervisor_pdf(canvas, documento, ruta_logo),
        onLaterPages=lambda canvas, documento:
            encabezado_lista_supervisor_pdf(canvas, documento, ruta_logo)
    )

    return response

def encabezado_lista_supervisor_pdf(canvas, documento, ruta_logo):
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
