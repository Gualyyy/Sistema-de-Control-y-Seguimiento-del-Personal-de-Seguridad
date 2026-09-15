from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from inicio_sesion.models import bitacora, sesiones_usuario, intentos_inicio_sesion
from datetime import datetime
from django.db.models.functions import TruncDate

import os
from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, legal

# BITACORA DE ACCIÓN

def visualizar_bitacora(request):
    return render(request, "Modulos/visualizar_bitacora.html")

def bitacora_registradas(request):
    cedula = request.POST.get("cedula", "").strip()
    nacionalidad = request.POST.get("nacionalidad", "").strip()

    if cedula in ("undefined", "null"):
        cedula = ""

    if nacionalidad in ("undefined", "null"):
        nacionalidad = ""

    registros = (
        bitacora.objects
        .select_related("id_usuario")
        .order_by("-fecha_hora")
    )

    # FILTRAR POR CÉDULA
    if cedula and nacionalidad:
        cedula_identidad = f"{nacionalidad}-{cedula}"

        registros = registros.filter(id_usuario__cedula_identidad=cedula_identidad)

    datos = []
    for registro in registros:
        datos.append({
            "id": registro.id_bitacora,
            "usuario": (
                f"{registro.id_usuario.nombres} "
                f"{registro.id_usuario.apellidos}"
            ),
            "cedula": registro.id_usuario.cedula_identidad,
            "fecha": registro.fecha_hora.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
            "accion": registro.accion,
        })

    return JsonResponse(datos, safe=False)
    
def lista_bitacora_pdf(request):

    cedula = request.POST.get("cedula", "").strip()
    nacionalidad = request.POST.get("nacionalidad", "").strip()

    registros = (
        bitacora.objects
        .select_related("id_usuario")
        .order_by("-fecha_hora")
    )

    if cedula and nacionalidad:
        cedula_identidad = f"{nacionalidad}-{cedula}"

        registros = registros.filter(
            id_usuario__cedula_identidad=cedula_identidad
        )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="lista_bitacora.pdf"'
    )

    # topMargin ajustado a 160 para respetar las dimensiones originales del encabezado
    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=140,
        bottomMargin=30
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloBitacora",
        parent=estilos["Heading2"],
        fontName="Times-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoBitacora",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=11,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaBitacora",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=12,
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
            Paragraph("BITÁCORA DE ACCIÓN", estilo_titulo),
            "",
            "",
            "",
            ""
        ],
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("Usuario", estilo_encabezado),
            Paragraph("C.I", estilo_encabezado),
            Paragraph("Fecha", estilo_encabezado),
            Paragraph("Acción", estilo_encabezado),
        ]
    ]

    for numero, registro in enumerate(registros, start=1):

        usuario = (
            f"{registro.id_usuario.nombres} "
            f"{registro.id_usuario.apellidos}"
        )

        cedula = (
            registro.id_usuario.cedula_identidad
            or "No especificada"
        )

        fecha = registro.fecha_hora.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        accion = registro.accion or "No especificada"

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(str(usuario), estilo_celda),
            Paragraph(str(cedula), estilo_celda),
            Paragraph(str(fecha), estilo_celda),
            Paragraph(str(accion), estilo_celda),
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[
            35,   # N.º
            150,  # Usuario
            90,   # Cédula
            100,  # Fecha
            357   # Acción / Observación
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

        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),

        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),

        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),

        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    elementos = [tabla]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, doc:
            encabezado_bitacora_pdf(
                canvas,
                doc,
                ruta_logo
            ),
        onLaterPages=lambda canvas, doc:
            encabezado_bitacora_pdf(
                canvas,
                doc,
                ruta_logo
            )
    )
    return response

def encabezado_bitacora_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(letter)

    # LOGO (Dimensiones y posición original)
    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            50,
            alto_pagina - 170,
            width=200,
            height=200,
            preserveAspectRatio=True,
            mask="auto"
        )

    # TITULO EMPRESA (Dimensiones y posición original)
    canvas.setFont(
        "Times-Bold",
        18
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        250,
        alto_pagina - 100,
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
        11
    )

    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        273,
        alto_pagina - 130,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

#  INICIOS DE SESIÓN Y REPORTE

def visualizar_inicio_sesion(request):
    return render(request, "Modulos/visualizar_inicios_sesiones.html")

def fechas_inicios_sesiones(request):
    registros = (
        sesiones_usuario.objects
        .values_list("fecha_inicio", flat=True)
        .order_by("-fecha_inicio")
    )

    fechas = []

    for fecha in registros:
        fecha = fecha.date()

        if fecha not in fechas:
            fechas.append(fecha)

    return JsonResponse({
        "estado": "exito",
        "fechas": [
            fecha.strftime("%Y-%m-%d")
            for fecha in fechas
        ]
    })

def inicios_sesiones_registradas(request):
    fecha = request.POST.get("fecha", "").strip()

    registros = (
        sesiones_usuario.objects
        .select_related("usuario")
        .order_by("-fecha_inicio")
    )

    if fecha:
        registros = registros.filter(fecha_inicio__date=fecha)

    datos = []
    for registro in registros:
        user_agent = registro.info_general or ""

        if "OPR/" in user_agent:
            navegador = "Opera"
        elif "Edg/" in user_agent:
            navegador = "Microsoft Edge"
        elif "Chrome/" in user_agent:
            navegador = "Google Chrome"
        elif "Firefox/" in user_agent:
            navegador = "Mozilla Firefox"
        elif "Safari/" in user_agent:
            navegador = "Safari"
        else:
            navegador = "Desconocido"

        datos.append({
            "id": registro.id_sesion,
            "usuario": (
                registro.usuario.nombres + " " +
                registro.usuario.apellidos
            ),
            "cedula_identidad": registro.usuario.cedula_identidad,
            "fecha_inicio": registro.fecha_inicio.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
            "fecha_fin": (
                registro.fecha_fin.strftime("%d/%m/%Y %H:%M:%S")
                if registro.fecha_fin
                else "Sesión activa"
            ),
            "activa": registro.activa,
            "navegador": navegador,
            "direccion_ip": registro.direccion_ip,
        })

    return JsonResponse(datos, safe=False)

def lista_inicios_sesiones_pdf(request):
    fecha = request.POST.get("fechas", "").strip()

    registros = (
        sesiones_usuario.objects
        .select_related("usuario")
        .order_by("-fecha_inicio")
    )

    if fecha:
        registros = registros.filter(fecha_inicio__date=fecha)

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = ('inline; filename="lista_inicios_sesiones.pdf"')

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
        "TituloSesiones",
        parent=estilos["Heading2"],
        fontName="Times-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoSesiones",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=14,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaSesiones",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=16,
        leading=14,
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
                "INICIOS DE SESIONES",
                estilo_titulo
            ),
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ],
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("EMPLEADO", estilo_encabezado),
            Paragraph("C.I", estilo_encabezado),
            Paragraph("FECHA INICIO", estilo_encabezado),
            Paragraph("FECHA FINALIZADA", estilo_encabezado),
            Paragraph("ACTIVO", estilo_encabezado),
            Paragraph("NAVEGADOR", estilo_encabezado),
            Paragraph("DIRECCIÓN IP", estilo_encabezado),
        ]
    ]

    for numero, registro in enumerate(registros, start=1):

        usuario = (
            f"{registro.usuario.nombres} "
            f"{registro.usuario.apellidos}"
        )

        cedula = (
            registro.usuario.cedula_identidad
            or "No especificada"
        )

        fecha_inicio = registro.fecha_inicio.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        fecha_fin = (
            registro.fecha_fin.strftime(
                "%d/%m/%Y %H:%M:%S"
            )
            if registro.fecha_fin
            else "Sesión activa"
        )

        activo = "Sí" if registro.activa else "No"

        user_agent = registro.info_general or ""

        if "OPR/" in user_agent:
            navegador = "Opera"
        elif "Edg/" in user_agent:
            navegador = "Microsoft Edge"
        elif "Chrome/" in user_agent:
            navegador = "Google Chrome"
        elif "Firefox/" in user_agent:
            navegador = "Mozilla Firefox"
        elif "Safari/" in user_agent:
            navegador = "Safari"
        else:
            navegador = "Desconocido"

        direccion_ip = registro.direccion_ip

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(str(usuario), estilo_celda),
            Paragraph(str(cedula), estilo_celda),
            Paragraph(str(fecha_inicio), estilo_celda),
            Paragraph(str(fecha_fin), estilo_celda),
            Paragraph(str(activo), estilo_celda),
            Paragraph(str(navegador), estilo_celda),
            Paragraph(str(direccion_ip), estilo_celda),
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[
            40,   # N.º
            170,  # Empleado
            90,   # C.I
            115,  # Fecha inicio
            130,  # Fecha finalizada
            55,   # Activo
            110,  # Navegador
            110   # Dirección IP
        ],
        repeatRows=2,
        hAlign="CENTER"
    )
    tabla.setStyle(TableStyle([

        # TÍTULO
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        # ENCABEZADO
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        # CONTENIDO
        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        # BORDES
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

        # ESPACIADO
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos = []

    elementos.append(Spacer(1, 15))
    elementos.append(tabla)

    documento.build(
        elementos,

        onFirstPage=lambda canvas, documento:
            encabezado_inicios_sesiones_pdf(
                canvas,
                documento,
                ruta_logo
            ),

        onLaterPages=lambda canvas, documento:
            encabezado_inicios_sesiones_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_inicios_sesiones_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(legal)

    # LOGO
    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            70,
            alto_pagina - 180,
            width=200,
            height=200,
            preserveAspectRatio=True,
            mask="auto"
        )

    # TITULO EMPRESA
    canvas.setFont(
        "Times-Bold",
        18
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        370,
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
        14
    )

    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        365,
        alto_pagina - 140,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()
    
# INTENTO INICIÓN DE SESIÓN

def visualizar_intentos_sesion(request):
    return render(request, "Modulos/visualizar_intentos_sesion.html")

def fechas_intentos_registrados(request):
    fechas = (
        intentos_inicio_sesion.objects
        .annotate(fecha=TruncDate("fecha_hora"))
        .values_list("fecha", flat=True)
        .distinct()
        .order_by("-fecha")
    )

    return JsonResponse({
        "estado": "exito",
        "fechas": list(fechas)
    })

def intentos_registrados(request):
    fecha = request.POST.get("fecha")

    intentos = intentos_inicio_sesion.objects.select_related("usuario").order_by("-fecha_hora")

    if fecha:
        intentos = intentos.filter(fecha_hora__date=fecha)

    datos = []
    for intento in intentos:
        datos.append({
                "id_intento": intento.id_intento,
                "usuario": (
                    f"{intento.usuario.nombres} "
                    f"{intento.usuario.apellidos}"
                    if intento.usuario
                    else "Usuario no registrado"
                ),
                "nombre_usuario": (
                    intento.nombre_usuario
                    if intento.nombre_usuario
                    else "Usuario no registrado"
                ),
                "direccion_ip": intento.direccion_ip,
                "exitoso": intento.exitoso,
                "fecha_hora": intento.fecha_hora.strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
            })

    return JsonResponse({
        "estado": "exito",
        "intentos": datos
    })

def lista_intentos_sesion_pdf(request):

    fecha = request.POST.get("fecha", "").strip()

    registros = (
        intentos_inicio_sesion.objects
        .select_related("usuario")
        .order_by("-fecha_hora")
    )

    if fecha:
        registros = registros.filter(
            fecha_hora__date=fecha
        )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="lista_intentos_inicio_sesion.pdf"'
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
        "TituloIntentos",
        parent=estilos["Heading2"],
        fontName="Times-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoIntentos",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaIntentos",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=11,
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
                "INTENTOS DE INICIO DE SESIÓN",
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
            Paragraph("EMPLEADO", estilo_encabezado),
            Paragraph("NOMBRE DE USUARIO", estilo_encabezado),
            Paragraph("DIRECCIÓN IP", estilo_encabezado),
            Paragraph("INICIO DE SESIÓN", estilo_encabezado),
            Paragraph("FECHA Y HORA", estilo_encabezado),
        ]
    ]

    for numero, intento in enumerate(registros, start=1):

        usuario = (
            f"{intento.usuario.nombres} "
            f"{intento.usuario.apellidos}"
            if intento.usuario
            else "Usuario no registrado"
        )

        nombre_usuario = (
            intento.nombre_usuario
            if intento.nombre_usuario
            else "Usuario no registrado"
        )

        direccion_ip = (
            intento.direccion_ip
            if intento.direccion_ip
            else "No disponible"
        )

        inicio_sesion = (
            "Exitoso"
            if intento.exitoso
            else "Fallido"
        )

        fecha_hora = intento.fecha_hora.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        datos_tabla.append([
            Paragraph(
                str(numero),
                estilo_celda
            ),
            Paragraph(
                str(usuario),
                estilo_celda
            ),
            Paragraph(
                str(nombre_usuario),
                estilo_celda
            ),
            Paragraph(
                str(direccion_ip),
                estilo_celda
            ),
            Paragraph(
                inicio_sesion,
                estilo_celda
            ),
            Paragraph(
                fecha_hora,
                estilo_celda
            ),
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[
            35,   # N.º
            210,  # Empleado
            145,  # Nombre de usuario
            105,  # Dirección IP
            105,  # Inicio de sesión
            130   # Fecha y hora
        ],
        repeatRows=2,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([
        # TÍTULO
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        # ENCABEZADO
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        # CONTENIDO
        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        # BORDES
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),

        ("INNERGRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

        # ESPACIADO
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos = []

    elementos.append(
        Spacer(1, 15)
    )

    elementos.append(tabla)

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
            alto_pagina - 180,
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
        345,
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
        alto_pagina - 140,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

