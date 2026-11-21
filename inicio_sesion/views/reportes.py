from django.shortcuts import render
from django.http import JsonResponse, HttpResponse

from inicio_sesion.models import (
    usuarios,
    credenciales,
    nacimiento,
    residencia,
    turnos_laborales,
    bitacora,
    intentos_inicio_sesion,
    sesiones_usuario,
    gasto,
    categoria_gasto,
    cliente,
    personal_limpieza,
    supervisores_encargados,
    despachadores,
    vigilantes,
    contacto,
    propietarios,
    atencion_cliente,
    encargados_administrativos
)

from incidencias.models import incidencia, tipo_incidencia, vigilante_incidencia
from asignaciones.models import equipos, entrega_equipos, asignacion_equipo


import os
import qrcode

from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.core import signing
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, legal
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    KeepTogether
)

from datetime import datetime
from decimal import Decimal
from urllib.parse import urlencode

TIPOS_REPORTE_VERIFICABLES = {
    "gastos": "Reporte de gastos",
    "encargado_administrativo": "Reporte del encargado administrativo",
    "clientes": "Reporte de clientes",
    "bitacora": "Reporte de bitácora",
    "inicios_sesion": "Reporte de inicios de sesión",
    "intentos_sesion": "Reporte de intentos de sesión",
    "lista_empleados": "Listado de empleados",
    "datos_empleado": "Datos del empleado",
    "incidencias": "Reporte de incidencias",
    "equipos": "Reporte de equipos",
    "entrega_equipos": "Reporte de entrega de equipos",
    "asignaciones_equipos": "Reporte de asignaciones de equipos"
}

def _crear_qr_verificacion(request, tipo_reporte, fecha_generacion, datos):
    token = signing.dumps(
        {
            "tipo": tipo_reporte,
            "fecha_generacion": fecha_generacion.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
            "datos": datos
        },
        salt="reporte-verificacion",
        compress=True
    )

    url_verificacion = request.build_absolute_uri(
        f"{reverse('verificar_reporte_qr')}?"
        f"{urlencode({'token': token})}"
    )

    codigo_qr = qrcode.make(url_verificacion)
    buffer_qr = BytesIO()
    codigo_qr.save(buffer_qr, format="PNG")
    buffer_qr.seek(0)
    return buffer_qr, url_verificacion

def _dibujar_qr_y_enlace(
    canvas,
    buffer_qr,
    url_verificacion,
    ancho_pagina,
    alto_pagina
):
    tamano_qr = 60
    x_qr = ancho_pagina - tamano_qr - 30
    y_qr = alto_pagina - 125

    canvas.drawImage(
        ImageReader(buffer_qr),
        x_qr,
        y_qr,
        width=tamano_qr,
        height=tamano_qr,
        preserveAspectRatio=True,
        mask="auto"
    )
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.HexColor("#00445F"))
    canvas.drawRightString(x_qr - 8, y_qr + 20, "Verificar QR")
    canvas.linkURL(
        url_verificacion,
        (x_qr - 68, y_qr + 16, x_qr - 5, y_qr + 30),
        relative=0,
        thickness=0
    )

@require_GET
def verificar_reporte_qr(request):
    token = request.GET.get("token", "").strip()
    reporte = None

    if token and len(token) <= 2048:
        try:
            contenido = signing.loads(
                token,
                salt="reporte-verificacion"
            )
        except signing.BadSignature:
            contenido = None

        if isinstance(contenido, dict):
            tipo = contenido.get("tipo")
            fecha_generacion = contenido.get("fecha_generacion")
            datos = contenido.get("datos")
            datos_validos = (
                isinstance(datos, list)
                and all(
                    isinstance(item, dict)
                    and isinstance(item.get("etiqueta"), str)
                    and isinstance(item.get("valor"), str)
                    for item in datos
                )
            )

            if (
                isinstance(tipo, str)
                and tipo in TIPOS_REPORTE_VERIFICABLES
                and isinstance(fecha_generacion, str)
                and datos_validos
            ):
                reporte = {
                    "tipo": TIPOS_REPORTE_VERIFICABLES[tipo],
                    "fecha_generacion": fecha_generacion,
                    "datos": datos
                }

    return render(
        request,
        "Modulos/Reportes/verificar_reporte.html",
        {"reporte": reporte}
    )

# Reporte para Encargado Administrativo y Propietario

def reporte_sistema_administrador(request):
    return render(request, "Modulos/Reportes/gestionar_reportes_administrador.html")

# Bitacora de Acción

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

    if not registros.exists():
        return JsonResponse({
            "estado": "error",
            "title": "Sin registros",
            "icon": "warning",
            "descripcion": (
                "No hay registros en la bitácora para generar el reporte PDF."
            )
        })

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="lista_bitacora.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(legal),
        rightMargin=30,
        leftMargin=30,
        topMargin=175,
        bottomMargin=35
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
        fontSize=9,
        leading=11,
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

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "bitacora",
        fecha_generacion,
        [{
            "etiqueta": "Registros en el reporte",
            "valor": str(registros.count())
        }]
    )

    datos_tabla = [
        [
            Paragraph("BITÁCORA DE ACCIÓN", estilo_titulo),
            "",
            "",
            "",
            "",
            "",
            ""
        ],
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("Usuario", estilo_encabezado),
            Paragraph("C.I", estilo_encabezado),
            Paragraph("Cargo del usuario", estilo_encabezado),
            Paragraph("Módulo", estilo_encabezado),
            Paragraph("Fecha", estilo_encabezado),
            Paragraph("Acción", estilo_encabezado),
        ]
    ]

    for numero, registro in enumerate(registros, start=1):

        usuario = (
            f"{registro.id_usuario.nombres} "
            f"{registro.id_usuario.apellidos}"
        )

        cedula_usuario = (
            registro.id_usuario.cedula_identidad
            or "No especificada"
        )

        fecha = registro.fecha_hora.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        cargo = registro.cargo_usuario or "No especificado"
        modulo = registro.nombre_modulo or "No especificado"
        accion = registro.accion or "No especificada"

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(escape(str(usuario)), estilo_celda),
            Paragraph(escape(str(cedula_usuario)), estilo_celda),
            Paragraph(escape(str(cargo)), estilo_celda),
            Paragraph(escape(str(modulo)), estilo_celda),
            Paragraph(str(fecha), estilo_celda),
            Paragraph(escape(str(accion)), estilo_celda),
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[35, 125, 75, 115, 125, 95, 320],
        repeatRows=2,
        hAlign="CENTER",
        splitByRow=1
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

    elementos = [
        Spacer(1, 10),
        tabla
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, doc:
            encabezado_bitacora_pdf(
                canvas,
                doc,
                ruta_logo,
                buffer_qr,
                url_verificacion
            ),
        onLaterPages=lambda canvas, doc:
            encabezado_bitacora_pdf(
                canvas,
                doc,
                ruta_logo,
                buffer_qr,
                url_verificacion
            )
    )

    return response

def encabezado_bitacora_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(legal)

    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            50,
            alto_pagina - 135,
            width=165,
            height=165,
            preserveAspectRatio=True,
            mask="auto"
        )

    canvas.setFont("Times-Bold", 17)
    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        270,
        alto_pagina - 65,
        "EMPRESA HIELO CAIPE C.A"
    )

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

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        280,
        alto_pagina - 95,
        f"Fecha de generación: {fecha_actual}"
    )

    canvas.setStrokeColor(
        colors.HexColor("#00445F")
    )
    canvas.setLineWidth(1)

    canvas.line(
        30,
        alto_pagina - 150,
        ancho_pagina - 30,
        alto_pagina - 150
    )

    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()

# Inicios de Sesión

def lista_inicios_sesiones_pdf(request):
    fecha = request.POST.get("fechas", "").strip()

    registros = (
        sesiones_usuario.objects
        .select_related("usuario")
        .order_by("-fecha_inicio")
    )

    if fecha and parse_date(fecha) is None:
        return JsonResponse({
            "estado": "error",
            "title": "Fecha no válida",
            "icon": "error",
            "descripcion": "La fecha seleccionada no es válida."
        }, status=400)

    if fecha:
        registros = registros.filter(fecha_inicio__date=fecha)

    if not registros.exists():
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin registros",
            "icon": "warning",
            "descripcion": (
                "No existen inicios de sesión que coincidan "
                "con los filtros seleccionados."
            )
        })

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = ('inline; filename="lista_inicios_sesiones.pdf"')

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(legal),
        rightMargin=30,
        leftMargin=30,
        topMargin=190,
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

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "inicios_sesion",
        fecha_generacion,
        [{
            "etiqueta": "Registros en el reporte",
            "valor": str(registros.count())
        }]
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
            Paragraph(escape(str(usuario)), estilo_celda),
            Paragraph(escape(str(cedula)), estilo_celda),
            Paragraph(str(fecha_inicio), estilo_celda),
            Paragraph(str(fecha_fin), estilo_celda),
            Paragraph(str(activo), estilo_celda),
            Paragraph(str(navegador), estilo_celda),
            Paragraph(escape(str(direccion_ip)), estilo_celda),
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

    elementos = [
        Spacer(1, 10),
        tabla
    ]

    documento.build(
        elementos,

        onFirstPage=lambda canvas, documento:
            encabezado_inicios_sesiones_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            ),

        onLaterPages=lambda canvas, documento:
            encabezado_inicios_sesiones_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            )
    )

    return response

def encabezado_inicios_sesiones_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(legal)

    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            80,
            alto_pagina - 190,
            width=210,
            height=210,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto"
        )

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))

    canvas.drawCentredString(
        ancho_pagina / 2,
        alto_pagina - 75,
        "EMPRESA HIELO CAIPE C.A"
    )

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

    canvas.setFont("Times-Bold", 12)
    canvas.setFillColor(colors.HexColor("#072F3F"))

    canvas.drawCentredString(
        ancho_pagina / 2,
        alto_pagina - 105,
        f"Fecha de generación: {fecha_actual}"
    )

    canvas.setStrokeColor(colors.HexColor("#58A5C4"))
    canvas.setLineWidth(1)

    canvas.line(
        30,
        alto_pagina - 165,
        ancho_pagina - 30,
        alto_pagina - 165
    )

    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()

# Intentos de Inicios de Sesión

def lista_intentos_sesion_pdf(request):
    fecha = request.POST.get("fecha", "").strip()

    if fecha and parse_date(fecha) is None:
        return JsonResponse({
            "estado": "error",
            "title": "Fecha no válida",
            "icon": "error",
            "descripcion": "La fecha seleccionada no es válida."
        }, status=400)

    registros = (
        intentos_inicio_sesion.objects
        .select_related("usuario")
        .order_by("-fecha_hora")
    )

    if fecha:
        registros = registros.filter(
            fecha_hora__date=fecha
        )

    if not registros.exists():
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin registros",
            "icon": "warning",
            "descripcion": (
                "No existen intentos de inicio de sesión "
                "para generar el reporte con los filtros seleccionados."
            )
        })

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
        topMargin=190,
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
        fontSize=9,
        leading=11,
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

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "intentos_sesion",
        fecha_generacion,
        [{
            "etiqueta": "Registros en el reporte",
            "valor": str(registros.count())
        }]
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
                escape(str(usuario)),
                estilo_celda
            ),
            Paragraph(
                escape(str(nombre_usuario)),
                estilo_celda
            ),
            Paragraph(
                escape(str(direccion_ip)),
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

    elementos = [
        Spacer(1, 10),
        tabla
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_intentos_sesion_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_intentos_sesion_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            )
    )

    return response

def encabezado_intentos_sesion_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
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

    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()

# Gastos

def lista_gastos_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "error",
            "title": "Solicitud no válida",
            "icon": "error",
            "descripcion": "No se pudo procesar la solicitud."
        }, status=405)

    categoria_id = request.POST.get("categoria", "").strip()

    if not categoria_id:
        return JsonResponse({
            "estado": "vacio",
            "title": "Categoría no seleccionada",
            "icon": "warning",
            "descripcion": (
                "Debe seleccionar una categoría de gastos "
                "para generar el reporte PDF."
            )
        }, status=400)

    try:
        categoria_id = int(categoria_id)
    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "error",
            "title": "Categoría no válida",
            "icon": "error",
            "descripcion": "La categoría seleccionada no es válida."
        }, status=400)

    try:
        categoria = categoria_gasto.objects.get(
            id_categoria_gasto=categoria_id,
            activo=True
        )
    except categoria_gasto.DoesNotExist:
        return JsonResponse({
            "estado": "error",
            "title": "Categoría no encontrada",
            "icon": "error",
            "descripcion": (
                "La categoría seleccionada no existe "
                "o se encuentra inhabilitada."
            )
        }, status=404)

    gastos = (
        gasto.objects
        .select_related("id_categoria_gasto")
        .filter(
            id_categoria_gasto=categoria,
            estado=gasto.Estado.REGISTRADO
        )
        .order_by("-fecha_gasto", "-id_gasto")
    )

    if not gastos.exists():
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin registros",
            "icon": "warning",
            "descripcion": (
                f"No existen gastos registrados en la categoría "
                f"{categoria.nombre} para generar el reporte PDF."
            )
        }, status=404)

    registros = list(gastos)

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="lista_gastos.pdf"'
    )

    response["Cache-Control"] = "no-store"

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=190,
        bottomMargin=90
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloGastos",
        parent=estilos["Heading2"],
        fontName="Times-Bold",
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoGastos",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaGastos",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        leading=11,
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

    total_gastos = sum(
        (registro.monto for registro in registros),
        Decimal("0.00")
    )

    fecha_generacion = timezone.localtime()

    buffer_qr, _ = _crear_qr_verificacion(
        request,
        "gastos",
        fecha_generacion,
        [
            {"etiqueta": "Categoría", "valor": str(categoria.nombre)},
            {
                "etiqueta": "Cantidad de registros",
                "valor": str(len(registros))
            },
            {
                "etiqueta": "Total de gastos",
                "valor": f"${total_gastos:,.2f}"
            }
        ]
    )

    datos_tabla = [
        [
            Paragraph(
                "REPORTE GENERAL DE GASTOS",
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
            Paragraph("FECHA", estilo_encabezado),
            Paragraph("CATEGORÍA", estilo_encabezado),
            Paragraph("DESCRIPCIÓN", estilo_encabezado),
            Paragraph("MONTO", estilo_encabezado),
            Paragraph("ESTADO", estilo_encabezado)
        ]
    ]

    for numero, registro in enumerate(registros, start=1):

        fecha_gasto = registro.fecha_gasto.strftime(
            "%d/%m/%Y"
        )

        nombre_categoria = escape(
            registro.id_categoria_gasto.nombre
        )

        descripcion = escape(
            registro.descripcion or "Sin descripción"
        )

        monto = f"${registro.monto:,.2f}"

        estado = escape(registro.get_estado_display())

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(fecha_gasto, estilo_celda),
            Paragraph(nombre_categoria, estilo_celda),
            Paragraph(descripcion, estilo_celda),
            Paragraph(monto, estilo_celda),
            Paragraph(estado, estilo_celda)
        ])

    ultima_fila = len(datos_tabla)

    datos_tabla.append([
        Paragraph(
            "TOTAL DE GASTOS REGISTRADOS",
            estilo_encabezado
        ),
        "",
        "",
        "",
        Paragraph(
            f"${total_gastos:,.2f}",
            estilo_encabezado
        ),
        ""
    ])

    tabla = Table(
        datos_tabla,
        colWidths=[
            45,
            85,
            130,
            260,
            115,
            97
        ],
        repeatRows=2,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([

        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),

        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        ("BACKGROUND", (0, 1), (-1, 1),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),

        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),

        ("ALIGN", (0, 1), (-1, 1), "CENTER"),

        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        ("FONTNAME", (0, 2), (-1, -2), "Times-Roman"),

        ("ALIGN", (0, 2), (-1, -2), "CENTER"),

        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        ("BACKGROUND", (0, ultima_fila), (-1, ultima_fila),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, ultima_fila), (-1, ultima_fila),
         colors.white),

        ("FONTNAME", (0, ultima_fila), (-1, ultima_fila),
         "Times-Bold"),

        ("ALIGN", (0, ultima_fila), (-1, ultima_fila),
         "CENTER"),

        ("VALIGN", (0, ultima_fila), (-1, ultima_fila),
         "MIDDLE"),

        ("SPAN", (0, ultima_fila), (3, ultima_fila)),

        ("BOX", (0, 0), (-1, -1),
         1, colors.HexColor("#00445F")),

        ("INNERGRID", (0, 1), (-1, -2),
         0.4, colors.HexColor("#58A5C4")),

        ("ROWBACKGROUNDS", (0, 2), (-1, -2), [
            colors.white,
            colors.HexColor("#F1F6F8")
        ]),

        ("TOPPADDING", (0, 0), (-1, -1), 9),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),

        ("LEFTPADDING", (0, 0), (-1, -1), 7),

        ("RIGHTPADDING", (0, 0), (-1, -1), 7)

    ]))

    elementos = [
        Spacer(1, 10),
        tabla
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_gastos_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_gastos_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr
            )
    )

    return response

def encabezado_gastos_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr
):

    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(letter)

    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            30,
            alto_pagina - 175,
            width=150,
            height=150,
            preserveAspectRatio=True,
            mask="auto"
        )

    canvas.setFont(
        "Times-Bold",
        22
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        220,
        alto_pagina - 85,
        "EMPRESA HIELO CAIPE C.A."
    )

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

    fecha = timezone.localtime()

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
        220,
        alto_pagina - 120,
        f"Fecha de generación: {fecha_actual}"
    )

    canvas.setFont(
        "Times-Roman",
        11
    )

    canvas.drawString(
        220,
        alto_pagina - 145,
        "Barinas, Venezuela"
    )

    canvas.drawString(
        220,
        alto_pagina - 162,
        "RIF: J-0012902-5"
    )

    canvas.setStrokeColor(
        colors.HexColor("#00779E")
    )

    canvas.setLineWidth(1)

    canvas.line(
        30,
        410,
        ancho_pagina - 30,
        410
    )

    canvas.drawImage(
        ImageReader(buffer_qr),
        ancho_pagina - 95,
        20,
        width=60,
        height=60,
        preserveAspectRatio=True,
        mask="auto"
    )

    canvas.setFont(
        "Times-Roman",
        9
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        30,
        55,
        "EMPRESA HIELO CAIPE C.A."
    )

    canvas.drawString(
        30,
        40,
        "Reporte administrativo de gastos"
    )

    canvas.setFont(
        "Times-Roman",
        9
    )

    canvas.drawRightString(
        ancho_pagina - 110,
        40,
        f"Página {documento.page}"
    )

    canvas.restoreState()

# Encargado Administrativo

def datos_encargado_administrativo_pdf(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "error",
            "title": "Solicitud no válida",
            "icon": "error",
            "descripcion": "No se pudo procesar la solicitud."
        }, status=405)

    # BUSCAR ENCARGADO ADMINISTRATIVO VIGENTE
    encargado = (
        encargados_administrativos.objects
        .select_related(
            "id_usuario",
            "id_usuario__contacto",
            "id_usuario__nacimiento",
            "id_usuario__residencia"
        )
        .filter(vigencia=True)
        .order_by("-id_encargado")
        .first()
    )

    if not encargado:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin encargado administrativo",
            "icon": "warning",
            "descripcion": (
                "No existe un encargado administrativo vigente "
                "para generar el reporte PDF."
            )
        }, status=404)

    # INFORMACIÓN DEL USUARIO
    usuario = encargado.id_usuario

    # INFORMACIÓN DE CONTACTO
    contacto_usuario = getattr(usuario, "contacto", None)

    # INFORMACIÓN DE NACIMIENTO
    nacimiento_usuario = getattr(usuario, "nacimiento", None)

    # INFORMACIÓN DE RESIDENCIA
    residencia_usuario = getattr(usuario, "residencia", None)

    # NOMBRE COMPLETO
    nombre_completo = (
        f"{usuario.nombres} {usuario.apellidos}"
    ).strip()

    # FUNCIÓN PARA OBTENER VALORES
    def obtener_valor(objeto, campo, predeterminado="No registrado"):

        if objeto is None:
            return predeterminado

        valor = getattr(objeto, campo, None)

        if valor is None or not str(valor).strip():
            return predeterminado

        return str(valor)

    # ESTADO DE VIGENCIA
    vigencia = (
        "Vigente"
        if encargado.vigencia
        else "No vigente"
    )

    # RESPUESTA PDF
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="datos_encargado_administrativo.pdf"'
    )

    response["Cache-Control"] = "no-store"

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=190,
        bottomMargin=100
    )

    # ESTILOS
    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloEncargado",
        parent=estilos["Heading2"],
        fontName="Times-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoEncargado",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_etiqueta = ParagraphStyle(
        "EtiquetaEncargado",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#00445F"),
        wordWrap="CJK"
    )

    estilo_celda = ParagraphStyle(
        "CeldaEncargado",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.black,
        wordWrap="CJK"
    )

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    # FECHA DE GENERACIÓN
    fecha_generacion = timezone.localtime()

    # CÓDIGO QR
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "encargado_administrativo",
        fecha_generacion,
        [
            {
                "etiqueta": "Empleado",
                "valor": nombre_completo
            },
            {
                "etiqueta": "Cédula",
                "valor": str(usuario.cedula_identidad)
            },
            {
                "etiqueta": "Cargo",
                "valor": "Encargado Administrativo"
            },
            {
                "etiqueta": "Vigencia",
                "valor": vigencia
            }
        ]
    )

    # FUNCIÓN PARA CREAR CELDAS
    def crear_celda(valor, estilo):

        return Paragraph(
            escape(str(valor)),
            estilo
        )

    # FUNCIÓN PARA AGREGAR SECCIONES
    datos_tabla = [
        [
            crear_celda(
                "DATOS DEL ENCARGADO ADMINISTRATIVO",
                estilo_titulo
            ),
            ""
        ]
    ]

    filas_secciones = []

    def agregar_seccion(titulo, campos):

        filas_secciones.append(len(datos_tabla))

        datos_tabla.append([
            crear_celda(
                titulo,
                estilo_encabezado
            ),
            ""
        ])

        for etiqueta, valor in campos:

            datos_tabla.append([
                crear_celda(
                    etiqueta,
                    estilo_etiqueta
                ),
                crear_celda(
                    valor,
                    estilo_celda
                )
            ])

    # ==================================================
    # 1. INFORMACIÓN PERSONAL
    # ==================================================

    agregar_seccion(
        "INFORMACIÓN PERSONAL",
        [
            (
                "Tipo de usuario",
                obtener_valor(
                    usuario,
                    "tipo_usuario"
                )
            ),
            (
                "Nombre o razón social",
                obtener_valor(
                    usuario,
                    "nombre_razon_social"
                )
            ),
            (
                "Nombres",
                obtener_valor(
                    usuario,
                    "nombres"
                )
            ),
            (
                "Apellidos",
                obtener_valor(
                    usuario,
                    "apellidos"
                )
            ),
            (
                "Cédula de identidad",
                obtener_valor(
                    usuario,
                    "cedula_identidad"
                )
            ),
            (
                "Género",
                obtener_valor(
                    usuario,
                    "genero"
                )
            ),
            (
                "Estado civil",
                obtener_valor(
                    usuario,
                    "estado_civil"
                )
            )
        ]
    )

    # ==================================================
    # 2. INFORMACIÓN DE CONTACTO
    # ==================================================

    agregar_seccion(
        "INFORMACIÓN DE CONTACTO",
        [
            (
                "Teléfono principal",
                obtener_valor(
                    contacto_usuario,
                    "telefono_principal"
                )
            ),
            (
                "Teléfono secundario",
                obtener_valor(
                    contacto_usuario,
                    "telefono_secundario"
                )
            ),
            (
                "Correo principal",
                obtener_valor(
                    contacto_usuario,
                    "correo_principal"
                )
            ),
            (
                "Correo secundario",
                obtener_valor(
                    contacto_usuario,
                    "correo_secundario"
                )
            )
        ]
    )

    # ==================================================
    # 3. INFORMACIÓN DE NACIMIENTO
    # ==================================================

    agregar_seccion(
        "INFORMACIÓN DE NACIMIENTO",
        [
            (
                "País de nacimiento",
                obtener_valor(
                    nacimiento_usuario,
                    "pais"
                )
            ),
            (
                "Estado de nacimiento",
                obtener_valor(
                    nacimiento_usuario,
                    "estado"
                )
            ),
            (
                "Municipio de nacimiento",
                obtener_valor(
                    nacimiento_usuario,
                    "municipio"
                )
            ),
            (
                "Parroquia de nacimiento",
                obtener_valor(
                    nacimiento_usuario,
                    "parroquia"
                )
            ),
            (
                "Dirección de nacimiento",
                obtener_valor(
                    nacimiento_usuario,
                    "direccion"
                )
            ),
            (
                "Fecha de nacimiento",
                obtener_valor(
                    nacimiento_usuario,
                    "fecha_nacimiento"
                )
            )
        ]
    )

    # ==================================================
    # 4. INFORMACIÓN DE RESIDENCIA
    # ==================================================

    agregar_seccion(
        "INFORMACIÓN DE RESIDENCIA",
        [
            (
                "Condición de residencia",
                obtener_valor(
                    residencia_usuario,
                    "condicion_residencia"
                )
            ),
            (
                "Municipio de residencia",
                obtener_valor(
                    residencia_usuario,
                    "municipio"
                )
            ),
            (
                "Parroquia de residencia",
                obtener_valor(
                    residencia_usuario,
                    "parroquia"
                )
            ),
            (
                "Dirección de residencia",
                obtener_valor(
                    residencia_usuario,
                    "direccion"
                )
            )
        ]
    )

    # ==================================================
    # 5. INFORMACIÓN DEL CARGO
    # ==================================================

    agregar_seccion(
        "INFORMACIÓN DEL CARGO",
        [
            (
                "Perfil asignado",
                "Encargado Administrativo"
            ),
            (
                "Vigencia del cargo",
                vigencia
            )
        ]
    )

    # ==================================================
    # TABLA GENERAL
    # ==================================================

    tabla = Table(
        datos_tabla,
        colWidths=[
            190,
            322
        ],
        repeatRows=1,
        splitByRow=1,
        hAlign="CENTER"
    )

    estilos_tabla = [

        # TÍTULO PRINCIPAL
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, 0), (-1, 0),
         colors.white),

        ("ALIGN", (0, 0), (-1, 0),
         "CENTER"),

        ("VALIGN", (0, 0), (-1, -1),
         "MIDDLE"),

        # CAMPOS
        ("BACKGROUND", (0, 1), (0, -1),
         colors.HexColor("#EAF2F5")),

        ("BACKGROUND", (1, 1), (1, -1),
         colors.white),

        # BORDES
        ("BOX", (0, 0), (-1, -1),
         1, colors.HexColor("#00445F")),

        ("INNERGRID", (0, 1), (-1, -1),
         0.4, colors.HexColor("#58A5C4")),

        # ESPACIADO
        ("TOPPADDING", (0, 0), (-1, -1), 8),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

        ("LEFTPADDING", (0, 0), (-1, -1), 9),

        ("RIGHTPADDING", (0, 0), (-1, -1), 9)
    ]

    # ENCABEZADOS DE SECCIONES
    for fila in filas_secciones:

        estilos_tabla.extend([

            ("SPAN", (0, fila), (-1, fila)),

            ("BACKGROUND", (0, fila), (-1, fila),
             colors.HexColor("#00445F")),

            ("TEXTCOLOR", (0, fila), (-1, fila),
             colors.white),

            ("ALIGN", (0, fila), (-1, fila),
             "CENTER"),

            ("VALIGN", (0, fila), (-1, fila),
             "MIDDLE")
        ])

    tabla.setStyle(
        TableStyle(estilos_tabla)
    )

    # ELEMENTOS DEL PDF
    elementos = [
        Spacer(1, 10),
        tabla
    ]

    # GENERAR DOCUMENTO
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_encargado_administrativo_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_encargado_administrativo_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr
            )
    )

    return response

def encabezado_encargado_administrativo_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr
):

    canvas.saveState()

    ancho_pagina, alto_pagina = letter

    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            35,
            alto_pagina - 175,
            width=80,
            height=80,
            preserveAspectRatio=True,
            mask="auto"
        )

    canvas.setFont(
        "Times-Bold",
        21
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        195,
        alto_pagina - 85,
        "EMPRESA HIELO CAIPE C.A."
    )

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

    fecha = timezone.localtime()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    canvas.setFont(
        "Times-Bold",
        13
    )

    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        195,
        alto_pagina - 120,
        f"Fecha de generación: {fecha_actual}"
    )

    canvas.setFont(
        "Times-Roman",
        11
    )

    canvas.drawString(
        195,
        alto_pagina - 145,
        "Barinas, Venezuela"
    )

    canvas.drawString(
        195,
        alto_pagina - 162,
        "RIF: J-0012902-5"
    )

    canvas.setStrokeColor(
        colors.HexColor("#00779E")
    )

    canvas.setLineWidth(1)

    canvas.line(
        40,
        alto_pagina - 190,
        ancho_pagina - 40,
        alto_pagina - 190
    )

    canvas.drawImage(
        ImageReader(buffer_qr),
        ancho_pagina - 105,
        25,
        width=65,
        height=65,
        preserveAspectRatio=True,
        mask="auto"
    )

    canvas.setFont(
        "Times-Roman",
        9
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        40,
        65,
        "EMPRESA HIELO CAIPE C.A."
    )

    canvas.drawString(
        40,
        50,
        "Reporte administrativo del personal"
    )

    canvas.drawRightString(
        ancho_pagina - 120,
        40,
        f"Página {documento.page}"
    )

    canvas.restoreState()

# Cliente

def lista_clientes_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "error",
            "title": "Solicitud no válida",
            "icon": "error",
            "descripcion": "No se pudo procesar la solicitud."
        }, status=405)

    tipo_cliente = request.POST.get("tipo_cliente", "").strip().upper()

    if tipo_cliente not in ["TODOS", "NATURAL", "EMPRESA"]:
        return JsonResponse({
            "estado": "error",
            "title": "Filtro no válido",
            "icon": "warning",
            "descripcion": (
                "Debe seleccionar un tipo de cliente válido "
                "para generar el reporte PDF."
            )
        }, status=400)

    clientes = (
        cliente.objects
        .select_related(
            "id_usuario",
            "id_usuario__contacto"
        )
        .order_by(
            "id_usuario__tipo_usuario",
            "id_usuario__nombre_razon_social"
        )
    )

    if tipo_cliente != "TODOS":
        clientes = clientes.filter(
            id_usuario__tipo_usuario=tipo_cliente
        )

    if not clientes.exists():
        descripcion = (
            "No existen clientes registrados "
            "para el tipo de cliente seleccionado."
        )

        return JsonResponse({
            "estado": "vacio",
            "title": "Sin registros",
            "icon": "warning",
            "descripcion": descripcion
        }, status=404)

    registros = list(clientes)

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="lista_clientes.pdf"'
    )

    response["Cache-Control"] = "no-store"

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=165,
        bottomMargin=90
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloClientes",
        parent=estilos["Heading2"],
        fontName="Times-Bold",
        fontSize=14,
        leading=17,
        alignment=1,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoClientes",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=9,
        leading=11,
        alignment=1,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaClientes",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        leading=11,
        alignment=1,
        textColor=colors.black,
        wordWrap="CJK"
    )

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    fecha_generacion = timezone.localtime()

    cantidad_naturales = sum(
        1 for registro in registros
        if registro.id_usuario.tipo_usuario == "NATURAL"
    )

    cantidad_empresas = sum(
        1 for registro in registros
        if registro.id_usuario.tipo_usuario == "EMPRESA"
    )

    nombre_filtro = {
        "TODOS": "Todos los clientes",
        "NATURAL": "Personas naturales",
        "EMPRESA": "Empresas"
    }

    buffer_qr, _ = _crear_qr_verificacion(
        request,
        "clientes",
        fecha_generacion,
        [
            {"etiqueta": "Filtro", "valor": nombre_filtro[tipo_cliente]},
            {
                "etiqueta": "Total de clientes",
                "valor": str(len(registros))
            },
            {
                "etiqueta": "Personas naturales",
                "valor": str(cantidad_naturales)
            },
            {"etiqueta": "Empresas", "valor": str(cantidad_empresas)}
        ]
    )

    datos_tabla = [
        [
            Paragraph(
                "LISTADO DE CLIENTES REGISTRADOS",
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
            Paragraph("CLIENTE / RAZÓN SOCIAL", estilo_encabezado),
            Paragraph("TIPO", estilo_encabezado),
            Paragraph("CÉDULA / RIF", estilo_encabezado),
            Paragraph("TELÉFONO PRINCIPAL", estilo_encabezado),
            Paragraph("CORREO ELECTRÓNICO", estilo_encabezado)
        ]
    ]

    for numero, registro in enumerate(registros, start=1):

        usuario = registro.id_usuario

        nombre_cliente = (
            f"{usuario.nombres} {usuario.apellidos}"
            if usuario.tipo_usuario == "NATURAL"
            else usuario.nombre_razon_social
        )

        tipo = usuario.get_tipo_usuario_display()

        cedula = usuario.cedula_identidad or "No registrado"

        contacto_usuario = getattr(
            usuario,
            "contacto",
            None
        )

        telefono = (
            contacto_usuario.telefono_principal
            if contacto_usuario and contacto_usuario.telefono_principal
            else "No registrado"
        )

        correo = (
            contacto_usuario.correo_principal
            if contacto_usuario and contacto_usuario.correo_principal
            else "No registrado"
        )

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(escape(nombre_cliente), estilo_celda),
            Paragraph(escape(tipo), estilo_celda),
            Paragraph(escape(cedula), estilo_celda),
            Paragraph(escape(telefono), estilo_celda),
            Paragraph(escape(correo), estilo_celda)
        ])

    ultima_fila = len(datos_tabla)

    datos_tabla.append([
        Paragraph(
            "TOTAL DE CLIENTES REGISTRADOS",
            estilo_encabezado
        ),
        "",
        "",
        Paragraph(
            str(len(registros)),
            estilo_encabezado
        ),
        "",
        ""
    ])

    tabla = Table(
        datos_tabla,
        colWidths=[
            35,
            200,
            90,
            105,
            130,
            172
        ],
        repeatRows=2,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([

        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),

        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        ("BACKGROUND", (0, 1), (-1, 1),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),

        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),

        ("ALIGN", (0, 1), (-1, 1), "CENTER"),

        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        ("FONTNAME", (0, 2), (-1, -2), "Times-Roman"),

        ("ALIGN", (0, 2), (-1, -1), "CENTER"),

        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        ("BACKGROUND", (0, ultima_fila), (-1, ultima_fila),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, ultima_fila), (-1, ultima_fila),
         colors.white),

        ("FONTNAME", (0, ultima_fila), (-1, ultima_fila),
         "Times-Bold"),

        ("SPAN", (0, ultima_fila), (2, ultima_fila)),

        ("BOX", (0, 0), (-1, -1),
         1, colors.HexColor("#00445F")),

        ("INNERGRID", (0, 1), (-1, -2),
         0.4, colors.HexColor("#58A5C4")),

        ("ROWBACKGROUNDS", (0, 2), (-1, -2), [
            colors.white,
            colors.HexColor("#F1F6F8")
        ]),

        ("TOPPADDING", (0, 0), (-1, -1), 9),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),

        ("LEFTPADDING", (0, 0), (-1, -1), 7),

        ("RIGHTPADDING", (0, 0), (-1, -1), 7)

    ]))

    elementos = [
        Spacer(1, 10),
        tabla
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_clientes_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                tipo_cliente
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_clientes_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                tipo_cliente
            )
    )

    return response

def encabezado_clientes_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    tipo_cliente
):

    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(letter)

    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            30,
            alto_pagina - 155,
            width=135,
            height=135,
            preserveAspectRatio=True,
            mask="auto"
        )

    canvas.setFont(
        "Times-Bold",
        22
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        190,
        alto_pagina - 75,
        "EMPRESA HIELO CAIPE C.A."
    )

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

    fecha = timezone.localtime()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    canvas.setFont(
        "Times-Bold",
        13
    )

    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        190,
        alto_pagina - 108,
        f"Fecha de generación: {fecha_actual}"
    )

    canvas.setFont(
        "Times-Roman",
        11
    )

    canvas.drawString(
        190,
        alto_pagina - 132,
        "Barinas, Venezuela"
    )

    canvas.drawString(
        190,
        alto_pagina - 149,
        "RIF: J-0012902-5"
    )

    filtros = {
        "TODOS": "Todos los clientes",
        "NATURAL": "Personas naturales",
        "EMPRESA": "Empresas"
    }

    canvas.setFont(
        "Times-Bold",
        11
    )

    canvas.drawString(
        190,
        alto_pagina - 170,
        f"Filtro aplicado: {filtros[tipo_cliente]}"
    )

    canvas.setStrokeColor(
        colors.HexColor("#00779E")
    )

    canvas.setLineWidth(1)

    canvas.line(
        30,
        alto_pagina - 185,
        ancho_pagina - 30,
        alto_pagina - 185
    )

    canvas.drawImage(
        ImageReader(buffer_qr),
        ancho_pagina - 95,
        20,
        width=60,
        height=60,
        preserveAspectRatio=True,
        mask="auto"
    )

    canvas.setFont(
        "Times-Roman",
        9
    )

    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        30,
        55,
        "EMPRESA HIELO CAIPE C.A."
    )

    canvas.drawString(
        30,
        40,
        "Reporte administrativo de clientes"
    )

    canvas.drawRightString(
        ancho_pagina - 110,
        40,
        f"Página {documento.page}"
    )

    canvas.restoreState()

# Empleados

def lista_empleados_pdf(request):
    perfil_empleado = request.POST.get("perfil", "").strip()
    confirmar = request.POST.get("confirmar", "false") == "true"

    datos = []

    modelos_perfiles = (
        ("Propietario", propietarios),
        ("Encargado Administrativo", encargados_administrativos),
        ("Atención al Cliente", atencion_cliente),
        ("Supervisor Encargado", supervisores_encargados),
        ("Personal de Limpieza", personal_limpieza),
        ("Despachador", despachadores),
        ("Vigilante", vigilantes),
    )

    for nombre_perfil, modelo_perfil in modelos_perfiles:

        if perfil_empleado and perfil_empleado != nombre_perfil:
            continue

        empleados = modelo_perfil.objects.filter(
            **(
                {"vigencia": True}
                if any(
                    campo.name == "vigencia"
                    for campo in modelo_perfil._meta.fields
                )
                else {}
            )
        ).select_related("id_usuario")

        if any(
            campo.name == "id_turno"
            for campo in modelo_perfil._meta.fields
        ):
            empleados = empleados.select_related("id_turno")

        for empleado in empleados:

            usuario = empleado.id_usuario

            turno = getattr(empleado, "id_turno", None)

            nombre_turno = (
                turno.nombre
                if turno and turno.nombre
                else "Turno Completo"
            )

            datos.append({
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula": usuario.cedula_identidad,
                "perfil": nombre_perfil,
                "turno": nombre_turno
            })

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin registros",
            "descripcion": (
                "No existen empleados que coincidan con los filtros "
                "seleccionados para generar el reporte PDF."
            ),
            "icon": "warning"
        }, status=404)

    # ADVERTENCIA ANTES DE GENERAR EL PDF
    if not confirmar:
        return JsonResponse({
            "estado": "confirmacion",
            "title": "¿Desea generar el reporte?",
            "descripcion": (
                f"Se encontraron {len(datos)} empleados que cumplen "
                "con los filtros seleccionados. "
                "¿Está seguro de que desea generar el archivo PDF?"
            ),
            "icon": "warning",
            "cantidad": len(datos)
        })

    # A PARTIR DE AQUÍ CONSERVA TODO TU CÓDIGO ACTUAL
    # DE GENERACIÓN DEL DOCUMENTO PDF.

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="lista_empleados.pdf"'
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
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

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "lista_empleados",
        fecha_generacion,
        [{
            "etiqueta": "Empleados en el reporte",
            "valor": str(len(datos))
        }]
    )

    # DATOS TABLA
    datos_tabla = [
        ["LISTA DE EMPLEADOS", "", "", "", "", ""],
        ["N.º", "Nombres", "Apellidos", "C.I", "Perfil", "Turno Laboral"],
    ]

    # REGISTROS
    for numero, dato in enumerate(datos, start=1):

        datos_tabla.append([
            numero,
            dato["nombres"],
            dato["apellidos"],
            dato["cedula"],
            dato["perfil"],
            dato["turno"]
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[35, 85, 85, 70, 125, 120],
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
    ]))

    elementos = [tabla]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_lista_empleados_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_lista_empleados_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            )
    )

    return response

def encabezado_lista_empleados_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
    canvas.saveState()

    ancho_pagina, alto_pagina = letter

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

    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()

# Datos del Empleado

def datos_empleados_pdf(request):

    # OBTENER CÉDULA DE IDENTIDAD
    cedula_identidad = request.POST.get(
        "cedula_identidad", ""
    ).strip()

    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "No se especificó la cédula de identidad del empleado.",
            "icon": "error"
        })

    # BUSCAR USUARIO
    try:
        usuario = usuarios.objects.get(
            cedula_identidad=cedula_identidad
        )
    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "No existe ningún empleado registrado con esa cédula de identidad.",
            "icon": "error"
        })

    # IDENTIFICAR PERFIL Y TURNO LABORAL
    perfiles_empleado = (
        ("Propietario", propietarios),
        ("Encargado Administrativo", encargados_administrativos),
        ("Atención al Cliente", atencion_cliente),
        ("Supervisor Encargado", supervisores_encargados),
        ("Personal de Limpieza", personal_limpieza),
        ("Despachador", despachadores),
        ("Vigilante", vigilantes),
    )

    perfil = "No asignado"
    turno_laboral = "Turno Completo"

    for nombre_perfil, modelo_perfil in perfiles_empleado:

        # VERIFICAR SI EL MODELO TIENE CAMPO DE TURNO
        tiene_turno = any(
            campo.name == "id_turno"
            for campo in modelo_perfil._meta.fields
        )

        relaciones = ["id_turno"] if tiene_turno else []

        try:
            empleado = modelo_perfil.objects.select_related(
                *relaciones
            ).get(id_usuario=usuario)

            perfil = nombre_perfil

            # DETERMINAR TURNO LABORAL
            turno = getattr(empleado, "id_turno", None)

            turno_laboral = (
                turno.nombre
                if turno and turno.nombre
                else "Turno Completo"
            )

            break

        except modelo_perfil.DoesNotExist:
            continue

    # INFORMACIÓN DE CONTACTO
    try:
        info_contacto = contacto.objects.get(
            id_usuario=usuario
        )
    except contacto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "El empleado no tiene información de contacto registrada.",
            "icon": "error"
        })

    # INFORMACIÓN DE NACIMIENTO
    try:
        info_nacimiento = nacimiento.objects.get(
            id_usuario=usuario
        )
    except nacimiento.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "El empleado no tiene información de nacimiento registrada.",
            "icon": "error"
        })

    # INFORMACIÓN DE RESIDENCIA
    try:
        info_residencia = residencia.objects.get(
            id_usuario=usuario
        )
    except residencia.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "El empleado no tiene información de residencia registrada.",
            "icon": "error"
        })

    # RESPUESTA PDF
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'inline; filename="empleado_{usuario.cedula_identidad}.pdf"'
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=130,
        bottomMargin=30
    )

    # ESTILOS
    estilos = getSampleStyleSheet()

    estilo_titulo = estilos["Heading2"]
    estilo_titulo.fontName = "Times-Bold"
    estilo_titulo.fontSize = 14
    estilo_titulo.alignment = TA_CENTER
    estilo_titulo.textColor = colors.black
    estilo_titulo.leading = 18

    # FUNCIÓN PARA CREAR TABLAS
    def crear_tabla(titulo, datos):

        datos_tabla = [
            [titulo, ""]
        ]

        datos_tabla.extend(datos)

        tabla = Table(
            datos_tabla,
            colWidths=[110, 380],
            splitByRow=1
        )

        tabla.setStyle(TableStyle([

            # ENCABEZADO
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 13),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

            # UNIR LAS DOS COLUMNAS DEL ENCABEZADO
            ("SPAN", (0, 0), (-1, 0)),

            # CAMPOS
            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#00445F")),
            ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
            ("FONTNAME", (0, 1), (0, -1), "Times-Bold"),
            ("FONTSIZE", (0, 1), (0, -1), 10),

            # VALORES
            ("FONTNAME", (1, 1), (1, -1), "Times-Roman"),
            ("TEXTCOLOR", (1, 1), (1, -1), colors.black),
            ("FONTSIZE", (1, 1), (1, -1), 11),

            # GENERAL
            ("ALIGN", (0, 1), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        return tabla

    # DATOS BÁSICOS
    datos_basicos = [
        ["Nombres:", usuario.nombres or "No registrado"],
        ["Apellidos:", usuario.apellidos or "No registrado"],
        ["Cédula de Identidad:", usuario.cedula_identidad or "No registrado"],
        ["Género:", usuario.genero or "No registrado"],
        ["Estado civil:", usuario.estado_civil or "No registrado"],
        ["Perfil:", perfil],
        ["Turno Laboral:", turno_laboral],
    ]

    # CONTACTO
    datos_contacto = [
        ["Teléfono Principal:", info_contacto.telefono_principal or "No registrado"],
        ["Teléfono Secundario:", info_contacto.telefono_secundario or "No registrado"],
        ["Correo Principal:", info_contacto.correo_principal or "No registrado"],
        ["Correo Secundario:", info_contacto.correo_secundario or "No registrado"],
    ]

    # NACIMIENTO
    datos_nacimiento = [
        ["País:", info_nacimiento.pais or "No registrado"],
        ["Estado:", info_nacimiento.estado or "No registrado"],
        ["Municipio:", info_nacimiento.municipio or "No registrado"],
        ["Parroquia:", info_nacimiento.parroquia or "No registrado"],
        ["Dirección:", info_nacimiento.direccion or "No registrado"],
        ["Fecha:", info_nacimiento.fecha_nacimiento or "No registrado"],
    ]

    # RESIDENCIA
    datos_residencia = [
        ["Condición:", info_residencia.condicion_residencia or "No registrado"],
        ["Municipio:", info_residencia.municipio or "No registrado"],
        ["Parroquia:", info_residencia.parroquia or "No registrado"],
        ["Dirección:", info_residencia.direccion or "No registrado"],
    ]

    # CREAR TABLAS
    tabla_basicos = crear_tabla(
        "DATOS BÁSICOS",
        datos_basicos
    )

    tabla_contacto = crear_tabla(
        "CONTACTO",
        datos_contacto
    )

    tabla_nacimiento = crear_tabla(
        "DATOS DE NACIMIENTO",
        datos_nacimiento
    )

    tabla_residencia = crear_tabla(
        "DATOS DE RESIDENCIA",
        datos_residencia
    )

    # ELEMENTOS DEL PDF
    elementos = [

        KeepTogether([
            tabla_basicos,
            Spacer(1, 15)
        ]),

        KeepTogether([
            tabla_contacto,
            Spacer(1, 15)
        ]),

        KeepTogether([
            tabla_nacimiento,
            Spacer(1, 15)
        ]),

        KeepTogether([
            tabla_residencia
        ])
    ]

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "datos_empleado",
        fecha_generacion,
        []
    )

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_datos_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_datos_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            )
    )

    return response

def encabezado_datos_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
    canvas.saveState()

    ancho_pagina, alto_pagina = letter

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

    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()

# Incidencias

def lista_incidencias_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "error",
            "title": "Solicitud no válida",
            "descripcion": "Método de solicitud no permitido.",
            "icon": "warning"
        }, status=405)

    fecha = request.POST.get("fecha_incidencia", "").strip()
    tipo = request.POST.get("tipo_incidencia", "").strip()

    if fecha and parse_date(fecha) is None:
        return JsonResponse({
            "estado": "error",
            "title": "Fecha no válida",
            "descripcion": "La fecha seleccionada no es válida.",
            "icon": "warning"
        }, status=400)

    if tipo and not tipo.isdigit():
        return JsonResponse({
            "estado": "error",
            "title": "Tipo no válido",
            "descripcion": "El tipo de incidencia seleccionado no es válido.",
            "icon": "warning"
        }, status=400)

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
            id_tipo_id=int(tipo)
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

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "incidencias",
        fecha_generacion,
        [{
            "etiqueta": "Incidencias en el reporte",
            "valor": str(registros.count())
        }]
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
                escape(str(registro.titulo)),
                estilo_celda
            ),
            Paragraph(
                escape(str(registro.id_tipo.nombre)),
                estilo_celda
            ),
            Paragraph(
                escape(str(descripcion)),
                estilo_celda
            ),
            Paragraph(
                fecha_hora,
                estilo_celda
            ),
            Paragraph(
                escape(str(vigilante)),
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
                ruta_logo,
                buffer_qr,
                url_verificacion
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_incidencia_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            )
    )

    return response

def encabezado_incidencia_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(legal)

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

    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()

# Equipos

def lista_equipos_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "descripcion": "Método de solicitud no permitido.",
            "icon": "warning"
        }, status=405)

    categoria = (request.POST.get("categoria") or "").strip()

    if categoria and not categoria.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Categoría inválida",
            "descripcion": "La categoría seleccionada no es válida.",
            "icon": "warning"
        }, status=400)

    lista_equipos = equipos.objects.select_related(
        "id_categoria"
    ).order_by("nombre")

    if categoria.isdigit():
        lista_equipos = lista_equipos.filter(
            id_categoria__id_categoria=int(categoria)
        )

    # Verificar que existan equipos antes de generar el PDF.
    if not lista_equipos.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin equipos registrados",
            "descripcion": (
                "No existen equipos registrados para generar el reporte."
            ),
            "icon": "warning"
        })

    # RESPUESTA PDF
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="lista_equipos.pdf"'
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=135,
        bottomMargin=35
    )

    # ESTILOS
    estilos = getSampleStyleSheet()

    estilo_encabezado = ParagraphStyle(
        "EncabezadoEquipos",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaEquipos",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=12,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "equipos",
        fecha_generacion,
        [{
            "etiqueta": "Equipos en el reporte",
            "valor": str(lista_equipos.count())
        }]
    )

    # DATOS DE LA TABLA
    datos_tabla = [
        [
            Paragraph("Lista de Equipos", estilo_encabezado),
            "",
            "",
            "",
            "",
        ],
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("Nombre", estilo_encabezado),
            Paragraph("Código", estilo_encabezado),
            Paragraph("Categoría", estilo_encabezado),
            Paragraph("Disponible", estilo_encabezado),
        ]
    ]

    for numero, equipo in enumerate(lista_equipos, start=1):
        nombre = equipo.nombre or "No especificado"
        codigo = equipo.codigo or "No especificado"

        categoria_nombre = (
            equipo.id_categoria.nombre
            if equipo.id_categoria
            else "No especificada"
        )

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(escape(str(nombre)), estilo_celda),
            Paragraph(escape(str(codigo)), estilo_celda),
            Paragraph(escape(str(categoria_nombre)), estilo_celda),
            Paragraph(str(equipo.cantidad_disponible), estilo_celda),
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[
            40,
            140,
            100,
            160,
            95,
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
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    # ELEMENTOS
    elementos = [
        tabla,
    ]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_lista_equipos_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_lista_equipos_pdf(
                canvas,
                documento,
                ruta_logo,
                buffer_qr,
                url_verificacion
            )
    )

    return response

def encabezado_lista_equipos_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
    canvas.saveState()

    ancho_pagina, alto_pagina = letter

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

    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()

# Entrega de Equipos

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
        }, status=404)

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "entrega_equipos",
        fecha_generacion,
        [{
            "etiqueta": "Entregas de equipos",
            "valor": str(len(entregas))
        }]
    )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="entregas_equipos.pdf"'
    )

    response["Cache-Control"] = "no-store"

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=20,
        leftMargin=20,
        topMargin=155,
        bottomMargin=30
    )

    estilos = getSampleStyleSheet()

    estilo_encabezado = ParagraphStyle(
        "EncabezadoEntregas",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaEntregas",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=6.5,
        leading=8,
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

    def crear_celda(valor):
        return Paragraph(
            escape(str(valor if valor not in (None, "") else "No registrado")),
            estilo_celda
        )

    def obtener_estado(valor):
        return "Activo" if valor else "Inactivo"

    datos_tabla = [
        [
            Paragraph(
                "REPORTE DE ENTREGA DE EQUIPOS",
                estilo_encabezado
            )
        ] + [""] * 18,
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("Supervisor Encargado", estilo_encabezado),
            Paragraph("Cédula", estilo_encabezado),
            Paragraph("Turno", estilo_encabezado),
            Paragraph("Equipo", estilo_encabezado),
            Paragraph("Código", estilo_encabezado),
            Paragraph("Categoría", estilo_encabezado),
            Paragraph("Observación del Equipo", estilo_encabezado),
            Paragraph("Inventario Actual", estilo_encabezado),
            Paragraph("Fecha de Registro", estilo_encabezado),
            Paragraph("Estado del Equipo", estilo_encabezado),
            Paragraph("Cant. Entregada", estilo_encabezado),
            Paragraph("Cant. Disponible", estilo_encabezado),
            Paragraph("Fecha de Entrega", estilo_encabezado),
            Paragraph("Observación de Entrega", estilo_encabezado),
            Paragraph("Estado de Entrega", estilo_encabezado),
            Paragraph("Motivo de Incidencia", estilo_encabezado)
        ]
    ]

    for numero, entrega in enumerate(entregas, start=1):

        supervisor_obj = entrega.supervisor_encargado
        usuario_supervisor = supervisor_obj.id_usuario
        equipo = entrega.id_equipo

        turno = (
            supervisor_obj.id_turno.nombre
            if getattr(supervisor_obj, "id_turno", None)
            else "No registrado"
        )

        categoria_equipo = (
            equipo.id_categoria.nombre
            if equipo.id_categoria
            else "No registrada"
        )

        fecha_registro = (
            timezone.localtime(equipo.fecha_registro).strftime("%d/%m/%Y %H:%M")
            if equipo.fecha_registro
            else "No registrada"
        )

        fecha_entrega = (
            timezone.localtime(entrega.fecha_entrega).strftime("%d/%m/%Y %H:%M")
            if entrega.fecha_entrega
            else "No registrada"
        )

        datos_tabla.append([
            crear_celda(numero),

            crear_celda(
                f"{usuario_supervisor.nombres} "
                f"{usuario_supervisor.apellidos}"
            ),

            crear_celda(usuario_supervisor.cedula_identidad),

            crear_celda(turno),

            crear_celda(equipo.nombre),

            crear_celda(equipo.codigo),

            crear_celda(categoria_equipo),

            crear_celda(equipo.observacion),

            crear_celda(equipo.cantidad_disponible),

            crear_celda(fecha_registro),

            crear_celda(obtener_estado(equipo.activo)),

            crear_celda(entrega.cantidad_entregada),

            crear_celda(entrega.cantidad_disponible),

            crear_celda(fecha_entrega),

            crear_celda(entrega.observacion),

            crear_celda(entrega.get_estado_display()),

            crear_celda(entrega.get_motivo_incidencia_display())
        ])

    anchos_columnas = [
        22,   # N.º
        95,   # Supervisor
        58,   # Cédula
        48,   # Turno
        65,   # Equipo
        55,   # Código
        60,   # Categoría
        105,  # Observación equipo
        48,   # Inventario actual
        65,   # Fecha registro
        48,   # Estado equipo
        48,   # Cantidad entregada
        48,   # Cantidad disponible
        65,   # Fecha entrega
        105,  # Observación entrega
        48,   # Estado entrega
        65    # Motivo incidencia
    ]

    tabla = Table(
        datos_tabla,
        colWidths=anchos_columnas,
        repeatRows=2,
        hAlign="CENTER",
        splitByRow=1
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

        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),

        ("BACKGROUND", (0, 2), (-1, -1), colors.white)
    ]))

    elementos = [tabla]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, doc: encabezado_lista_entrega_equipos_pdf(
            canvas, doc, ruta_logo, buffer_qr, url_verificacion
        ),
        onLaterPages=lambda canvas, doc: encabezado_lista_entrega_equipos_pdf(
            canvas, doc, ruta_logo, buffer_qr, url_verificacion
        )
    )

    return response

def encabezado_lista_entrega_equipos_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
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

    ancho_pagina, alto_pagina = documento.pagesize
    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()

# Asignación de Equipos

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
            "id_usuario__contacto",
            "id_usuario__nacimiento",
            "id_usuario__residencia",
            "id_entrega",
            "id_entrega__id_equipo",
            "id_entrega__id_equipo__id_categoria",
            "id_entrega__supervisor_encargado",
            "id_entrega__supervisor_encargado__id_usuario",
            "id_entrega__supervisor_encargado__id_turno"
        )
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
            }, status=400)

        asignaciones = asignaciones.filter(
            id_entrega__id_equipo__id_categoria_id=int(categoria)
        )

    asignaciones = list(asignaciones)

    if not asignaciones:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin asignaciones",
            "descripcion": (
                "No existen asignaciones de equipos "
                "que coincidan con los filtros seleccionados."
            ),
            "icon": "warning"
        }, status=404)

    fecha_generacion = timezone.localtime()
    buffer_qr, url_verificacion = _crear_qr_verificacion(
        request,
        "asignaciones_equipos",
        fecha_generacion,
        [{
            "etiqueta": "Asignaciones de equipos",
            "valor": str(len(asignaciones))
        }]
    )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="reporte_general_asignaciones.pdf"'
    )

    response["Cache-Control"] = "no-store"

    estilo_titulo = ParagraphStyle(
        "estilo_titulo_asignaciones",
        fontName="Times-Bold",
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "estilo_encabezado_asignaciones",
        fontName="Times-Bold",
        fontSize=6,
        leading=7,
        alignment=TA_CENTER,
        textColor=colors.white,
        wordWrap="CJK"
    )

    estilo_celda = ParagraphStyle(
        "estilo_celda_asignaciones",
        fontName="Times-Roman",
        fontSize=6,
        leading=7,
        alignment=TA_CENTER,
        textColor=colors.black,
        wordWrap="CJK"
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=18,
        leftMargin=18,
        topMargin=155,
        bottomMargin=30
    )

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    def obtener_valor(objeto, campo, predeterminado="No registrado"):
        if objeto is None:
            return predeterminado

        valor = getattr(objeto, campo, None)

        if valor in (None, ""):
            return predeterminado

        return valor

    def crear_celda(valor):
        return Paragraph(
            escape(str(
                valor if valor not in (None, "") else "No registrado"
            )),
            estilo_celda
        )

    datos_tabla = [
        [
            Paragraph(
                "REPORTE GENERAL DE ASIGNACIONES DE EQUIPOS",
                estilo_titulo
            )
        ] + [""] * 22,
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("EMPLEADO", estilo_encabezado),
            Paragraph("TIPO DE USUARIO", estilo_encabezado),
            Paragraph("CÉDULA", estilo_encabezado),
            Paragraph("GÉNERO", estilo_encabezado),
            Paragraph("ESTADO CIVIL", estilo_encabezado),
            Paragraph("TELÉFONO PRINCIPAL", estilo_encabezado),
            Paragraph("CORREO PRINCIPAL", estilo_encabezado),
            Paragraph("SUPERVISOR", estilo_encabezado),
            Paragraph("CÉDULA SUPERVISOR", estilo_encabezado),
            Paragraph("TURNO", estilo_encabezado),
            Paragraph("EQUIPO", estilo_encabezado),
            Paragraph("CÓDIGO", estilo_encabezado),
            Paragraph("CATEGORÍA", estilo_encabezado),
            Paragraph("OBSERVACIÓN DEL EQUIPO", estilo_encabezado),
            Paragraph("INVENTARIO ACTUAL", estilo_encabezado),
            Paragraph("CANTIDAD ASIGNADA", estilo_encabezado),
            Paragraph("CANTIDAD DEVUELTA", estilo_encabezado),
            Paragraph("EN POSESIÓN", estilo_encabezado),
            Paragraph("OBSERVACIÓN DE ENTREGA", estilo_encabezado),
            Paragraph("ESTADO DE ASIGNACIÓN", estilo_encabezado),
            Paragraph("ESTADO DE ENTREGA", estilo_encabezado),
            Paragraph("FECHA DE ENTREGA", estilo_encabezado)
        ]
    ]

    for numero, asignacion in enumerate(asignaciones, start=1):

        usuario = asignacion.id_usuario
        entrega = asignacion.id_entrega
        equipo = entrega.id_equipo

        supervisor = entrega.supervisor_encargado

        usuario_supervisor = (
            supervisor.id_usuario
            if supervisor and supervisor.id_usuario
            else None
        )

        contacto = getattr(usuario, "contacto", None)

        nombre_empleado = (
            f"{obtener_valor(usuario, 'nombres')} "
            f"{obtener_valor(usuario, 'apellidos')}"
        )

        nombre_supervisor = (
            f"{obtener_valor(usuario_supervisor, 'nombres')} "
            f"{obtener_valor(usuario_supervisor, 'apellidos')}"
            if usuario_supervisor
            else "No registrado"
        )

        cedula_supervisor = (
            f"{obtener_valor(usuario_supervisor, 'nacionalidad', '')}"
            f"{obtener_valor(usuario_supervisor, 'cedula_identidad')}"
            if usuario_supervisor
            else "No registrado"
        )

        turno = (
            obtener_valor(supervisor.id_turno, "nombre")
            if supervisor and getattr(supervisor, "id_turno", None)
            else "No registrado"
        )

        categoria_equipo = (
            obtener_valor(equipo.id_categoria, "nombre")
            if equipo.id_categoria
            else "No registrada"
        )

        fecha_entrega = (
            timezone.localtime(
                asignacion.fecha_entrega
            ).strftime("%d/%m/%Y %H:%M")
            if asignacion.fecha_entrega
            else "No registrada"
        )

        cantidad_asignada = asignacion.cantidad_asignada or 0
        cantidad_devuelta = asignacion.cantidad_devuelta or 0

        cantidad_posesion = (
            cantidad_asignada - cantidad_devuelta
        )

        datos_tabla.append([
            crear_celda(numero),

            crear_celda(nombre_empleado),

            crear_celda(
                usuario.get_tipo_usuario_display()
                if hasattr(usuario, "get_tipo_usuario_display")
                else obtener_valor(usuario, "tipo_usuario")
            ),

            crear_celda(
                f"{obtener_valor(usuario, 'nacionalidad', '')}"
                f"{obtener_valor(usuario, 'cedula_identidad')}"
            ),

            crear_celda(
                usuario.get_genero_display()
                if hasattr(usuario, "get_genero_display")
                else obtener_valor(usuario, "genero")
            ),

            crear_celda(
                usuario.get_estado_civil_display()
                if hasattr(usuario, "get_estado_civil_display")
                else obtener_valor(usuario, "estado_civil")
            ),

            crear_celda(
                obtener_valor(contacto, "telefono_principal")
            ),

            crear_celda(
                obtener_valor(contacto, "correo_principal")
            ),

            crear_celda(nombre_supervisor),

            crear_celda(cedula_supervisor),

            crear_celda(turno),

            crear_celda(equipo.nombre),

            crear_celda(equipo.codigo),

            crear_celda(categoria_equipo),

            crear_celda(equipo.observacion),

            crear_celda(equipo.cantidad_disponible),

            crear_celda(cantidad_asignada),

            crear_celda(cantidad_devuelta),

            crear_celda(cantidad_posesion),

            crear_celda(entrega.observacion),

            crear_celda(asignacion.get_estado_display()),

            crear_celda(entrega.get_estado_display()),

            crear_celda(fecha_entrega)
        ])

    anchos_columnas = [
        20,  # N.º
        78,  # Empleado
        55,  # Tipo de usuario
        55,  # Cédula
        42,  # Género
        48,  # Estado civil
        65,  # Teléfono
        85,  # Correo
        78,  # Supervisor
        58,  # Cédula supervisor
        42,  # Turno
        55,  # Equipo
        48,  # Código
        55,  # Categoría
        90,  # Observación equipo
        45,  # Inventario
        45,  # Asignada
        45,  # Devuelta
        45,  # Posesión
        90,  # Observación entrega
        55,  # Estado asignación
        50,  # Estado entrega
        65   # Fecha entrega
    ]

    tabla = Table(
        datos_tabla,
        colWidths=anchos_columnas,
        repeatRows=2,
        hAlign="CENTER",
        splitByRow=1
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 1),
         colors.HexColor("#00445F")),

        ("TEXTCOLOR", (0, 0), (-1, 1), colors.white),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("BOX", (0, 0), (-1, -1), 0.8,
         colors.HexColor("#00445F")),

        ("INNERGRID", (0, 0), (-1, -1), 0.4,
         colors.HexColor("#58A5C4")),

        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2)
    ]))

    elementos = [tabla]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, doc:
            encabezado_lista_admin_pdf(
                canvas,
                doc,
                ruta_logo,
                buffer_qr,
                url_verificacion
            ),
        onLaterPages=lambda canvas, doc:
            encabezado_lista_admin_pdf(
                canvas,
                doc,
                ruta_logo,
                buffer_qr,
                url_verificacion
            )
    )

    return response

def encabezado_lista_admin_pdf(
    canvas,
    documento,
    ruta_logo,
    buffer_qr,
    url_verificacion
):
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

    _dibujar_qr_y_enlace(
        canvas,
        buffer_qr,
        url_verificacion,
        ancho_pagina,
        alto_pagina
    )

    canvas.restoreState()
