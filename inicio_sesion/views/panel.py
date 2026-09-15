from django.shortcuts import redirect, render
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.views.decorators.cache import never_cache

from inicio_sesion.models import perfil_usuario, sesiones_usuario, contacto, turnos_laborales, usuarios, perfiles

from inicio_sesion.views.autenticacion import validar_token_panel, crear_token_panel

import os
from django.conf import settings
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# USUARIOS PANEL

def pagina_error_404(request, exception):
    return render(
        request,
        "inicio_sesion/404.html",
        {"pagina_404": True},
        status=404
    )

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
        "inicio_sesion/panel_usuario.html"
    )

    response["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response


def empleados_registrados(request):

    nombres_perfiles = [
        "Vigilante",
        "Despachador",
        "Personal de Limpieza",
        "Supervisor Encargado"
    ]

    # OBTENER LOS PERFILES
    perfiles_registrados = perfiles.objects.filter(
        perfil__in=nombres_perfiles
    )

    # CONTAR EMPLEADOS POR PERFIL
    conteo_perfiles = (
        perfil_usuario.objects
        .filter(
            id_perfil__perfil__in=nombres_perfiles,
            vigencia=True
        )
        .values("id_perfil")
        .annotate(
            cantidad=Count("id_perfil_usuario")
        )
    )

    # CREAR DICCIONARIO DE CANTIDADES
    conteo = {
        item["id_perfil"]: item["cantidad"]
        for item in conteo_perfiles
    }

    # RESPUESTA
    datos = []

    for perfil in perfiles_registrados:

        datos.append({
            "id_perfil": perfil.id_perfil,
            "perfil": perfil.perfil,
            "cantidad": conteo.get(
                perfil.id_perfil,
                0
            )
        })

    return JsonResponse(datos, safe=False)

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

def empleado_perfil(request):
    if request.method == "POST":
        id_perfil = request.POST.get("id_perfil", "").strip()

        # Validar ID vacío, null o undefined
        if id_perfil in ("", "null", "undefined"):
            return JsonResponse({
                "estado": True,
                "empleados": []
            })
    
        # Buscar las asignaciones del perfil
        asignaciones = perfil_usuario.objects.filter(
            id_perfil_id=id_perfil,
            vigencia=True
        )

        datos_empleados = []
        for asignacion in asignaciones:
            id_usuario = asignacion.id_usuario_id

            # Datos del usuario
            try:
                usuario = usuarios.objects.get(id_usuario=id_usuario)
            except usuarios.DoesNotExist:
                continue

            # Datos de contacto
            try:
                datos_contacto = contacto.objects.get(id_usuario_id=id_usuario)
            except contacto.DoesNotExist:
                datos_contacto = None

            # Datos del turno
            turno = None
            if asignacion.id_turno_id:
                try:
                    datos_turno = turnos_laborales.objects.get(id_turno=asignacion.id_turno_id)

                    turno = datos_turno.nombre
                except turnos_laborales.DoesNotExist:
                    turno = "No asignado"
            else:
                turno = "No asignado"

            # Construir datos
            datos_empleados.append({
                "id": usuario.id_usuario,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula": usuario.cedula_identidad,
                "telefono": (
                    datos_contacto.telefono_principal
                    if datos_contacto
                    else "No registrado"
                ),
                "correo": (
                    datos_contacto.correo_principal
                    if datos_contacto
                    else "No registrado"
                ),
                "turno": turno
            })

        return JsonResponse({
            "estado": True,
            "empleados": datos_empleados
        })


def empleado_perfil_pdf(request):
    if request.method == "POST":
        id_perfil = request.POST.get("id_perfil").strip()

        if not id_perfil or id_perfil in ("null", "undefined"):
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil no seleccionado",
                "descripcion": "No se recibió un perfil válido para generar el PDF.",
                "icon": "warning"
            })

        try:
            id_perfil = int(id_perfil)
        except (ValueError, TypeError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil no válido",
                "descripcion": "El ID del perfil recibido no es válido.",
                "icon": "error"
            })

        # BUSCAR ASIGNACIONES DEL PERFIL
        asignaciones = (
            perfil_usuario.objects
            .filter(
                id_perfil_id=id_perfil,
                vigencia=True
            )
            .select_related(
                "id_perfil",
                "id_turno"
            )
        )

        datos = []

        for asignacion in asignaciones:

            id_usuario = asignacion.id_usuario_id

            # BUSCAR USUARIO
            try:
                usuario = usuarios.objects.get(id_usuario=id_usuario)
            except usuarios.DoesNotExist:
                continue

            # BUSCAR CONTACTO
            try:
                datos_contacto = contacto.objects.get(id_usuario_id=id_usuario)

            except contacto.DoesNotExist:
                datos_contacto = None

            # TURNO
            if asignacion.id_turno_id:

                try:
                    datos_turno = turnos_laborales.objects.get(id_turno=asignacion.id_turno_id)

                    turno = datos_turno.nombre

                except turnos_laborales.DoesNotExist:
                    turno = "No asignado"

            else:
                turno = "No asignado"

            datos.append({
                "id": usuario.id_usuario,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula": usuario.cedula_identidad,
                "telefono": (
                    datos_contacto.telefono_principal
                    if datos_contacto
                    else "No registrado"
                ),
                "correo": (
                    datos_contacto.correo_principal
                    if datos_contacto
                    else "No registrado"
                ),
                "turno": turno
            })

        # VALIDAR SI LA TABLA ESTÁ VACÍA
        if not datos:
            return JsonResponse({
                "estado": "fallo",
                "title": "Sin empleados registrados",
                "descripcion": "No existen empleados registrados para el perfil seleccionado.",
                "icon": "warning"
            })

        # CONTINUAR CON LA GENERACIÓN DEL PDF
        response = HttpResponse(
            content_type="application/pdf"
        )


        response["Content-Disposition"] = (
            'inline; filename="empleados_perfil.pdf"'
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

        # DATOS DE LA TABLA
        datos_tabla = [

            # ENCABEZADO PRINCIPAL
            [
                "LISTA DE EMPLEADOS",
                "",
                "",
                "",
                "",
                "",
                ""
            ],

            # ENCABEZADO DE COLUMNAS
            [
                "ID",
                "Nombres",
                "Apellidos",
                "C.I",
                "Teléfono",
                "Correo Electrónico",
                "Turno Laboral"
            ]
        ]

        # REGISTROS
        for numero, dato in enumerate(datos, start=1):
            datos_tabla.append([
                numero,
                dato["nombres"],
                dato["apellidos"],
                dato["cedula"],
                dato["telefono"],
                dato["correo"],
                dato["turno"]
            ])

        # TABLA
        tabla = Table(
            datos_tabla,
            colWidths=[
                35,   # ID
                85,   # Nombres
                85,   # Apellidos
                70,   # C.I
                75,   # Teléfono
                130,  # Correo
                85    # Turno
            ],
            repeatRows=2
        )

        tabla.setStyle(TableStyle([
            # ENCABEZADO PRINCIPAL
            ("SPAN",       (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Times-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 14),
            ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
            ("VALIGN",     (0, 0), (-1, 0), "MIDDLE"),

            # ENCABEZADO DE COLUMNAS
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
            ("TEXTCOLOR",  (0, 1), (-1, 1), colors.white),
            ("FONTNAME",   (0, 1), (-1, 1), "Times-Bold"),
            ("FONTSIZE",   (0, 1), (-1, 1), 9),
            ("ALIGN",      (0, 1), (-1, 1), "CENTER"),
            ("VALIGN",     (0, 1), (-1, 1), "MIDDLE"),

            # CONTENIDO
            ("FONTNAME",   (0, 2), (-1, -1), "Times-Roman"),
            ("FONTSIZE",   (0, 2), (-1, -1), 8),
            ("TEXTCOLOR",  (0, 2), (-1, -1), colors.black),
            ("ALIGN",      (0, 2), (-1, -1), "CENTER"),
            ("VALIGN",     (0, 2), (-1, -1), "MIDDLE"),

            # BORDES
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.grey),

            # ESPACIADO
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
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