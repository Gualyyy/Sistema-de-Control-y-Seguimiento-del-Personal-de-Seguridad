from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction, IntegrityError
from django.utils import timezone

from ventas.models import cliente, contacto_cliente
from inicio_sesion.models import bitacora, usuarios

import os
from django.conf import settings
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Spacer,
    KeepTogether,
    Paragraph
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from xml.sax.saxutils import escape

# Create your views here.

def validar_identificador(request):
    if request.method == "POST":
        tipo_identificador = request.POST.get("tipo_identificador", "").strip()
        identificador = request.POST.get("identificador", "").strip()
        id_cliente = request.POST.get("id_cliente", "").strip()

        idenficador_cliente = f"{tipo_identificador}-{identificador}"

        consulta = cliente.objects.filter(
            identificador=idenficador_cliente
        )

        # Solo excluir al usuario cuando se está actualizando
        if id_cliente:
            consulta = consulta.exclude(
                id_cliente=id_cliente
            )

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })

def validar_telefono_cliente(request):
    if request.method == "POST":
        prefijo = request.POST.get("prefijo", "").strip()
        numeros = request.POST.get("numeros", "").strip()
        id_cliente = request.POST.get("id_cliente", "").strip()

        telefono = f"{prefijo}-{numeros}"

        consulta = contacto_cliente.objects.filter(
            telefono=telefono
        )

        if id_cliente:
            contacto_usuario = contacto_cliente.objects.filter(
                id_cliente=id_cliente
            ).first()

            if contacto_usuario and contacto_usuario.telefono == telefono:
                return JsonResponse({
                    "existe": True
                })

            consulta = consulta.exclude(
                id_cliente=id_cliente
            )

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })

def validar_correo_cliente(request):
    if request.method == "POST":
        correo = request.POST.get("correo", "").strip().lower()
        dominio = request.POST.get("dominio", "").strip().lower()
        id_cliente = request.POST.get("id_cliente", "").strip()

        email = f"{correo}{dominio}"

        consulta = contacto_cliente.objects.filter(
            correo__iexact=email
        )

        if id_cliente:
            contacto_usuario = contacto_cliente.objects.filter(
                id_cliente=id_cliente
            ).first()

            if contacto_usuario and contacto_usuario.correo.lower() == email:
                return JsonResponse({
                    "existe": True
                })

            consulta = consulta.exclude(
                id_cliente=id_cliente
            )

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })

def registrar_clientes_ventas(request):
    if request.method != "POST":
        return render(request, "Clientes/registrar_clientes.html")

    nombre_cliente = request.POST.get("nombre_cliente", "").strip()
    apellido_cliente = request.POST.get("apellido_cliente", "").strip()
    nombre_empresa = request.POST.get("nombre_empresa", "").strip()
    tipo_identificador = request.POST.get("tipo_identificador")
    identificador = request.POST.get("identificador")
    tipo_cliente = request.POST.get("tipo_cliente")

    num_telefono = request.POST.get("num_telefono")
    prefijo = request.POST.get("prefijo")

    correo = request.POST.get("correo")
    dominio = request.POST.get("dominio")

    campos = [
        (tipo_identificador, "Tipo de Identificador", "Por favor, seleccione el tipo de identificador."),
        (identificador, "Identificador", "Por favor, ingrese el idenficador."),
        (tipo_cliente, "Tipo de Cliente", "Por favor, seleccione el tipo de cliente."),
        (num_telefono, "Número Telefonico", "Por favor, ingrese el número telefonico del cliente."),
        (prefijo, "Prefijo Telefonico", "Por favor, seleccione el prefijo telefonico del cliente."),
        (correo, "Correo", "Por favor, ingresa el nombre del correo eletronico del cliente."),
        (dominio, "Dominio", "Por favor, selecciona el dominio del correo eletronico del cliente."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if tipo_cliente == "EMPRESA":
        if not nombre_empresa:
            return JsonResponse({
                "title": "Nombre de la Empresa",
                "descripcion": "Por favor, ingrese el nombre de la empresa.",
                "icon": "warning"
            }) 

        nombre_razon_social = nombre_empresa
        nombre_cliente = ""
        apellido_cliente = ""
    else:
        if not nombre_cliente:
            return JsonResponse({
                "title": "Nombre del Cliente",
                "descripcion": "Por favor, ingrese el nombre del cliente.",
                "icon": "warning"
            }) 

        if not apellido_cliente:
            return JsonResponse({
                "title": "Apellido del Cliente",
                "descripcion": "Por favor, ingrese el apellido del cliente.",
                "icon": "warning"
            }) 

        nombre_razon_social = nombre_cliente + " " + apellido_cliente

    idenficador_cliente = tipo_identificador + "-" + identificador
    correo_electronico = correo + dominio
    telefono = prefijo + "-" + num_telefono

    try:
        with transaction.atomic():
            obj_usuario = usuarios.objects.get(
                cedula_identidad=request.session.get("cedula_identidad")
            )

            obj_cliente = cliente.objects.create(
                nombre_razon_social=nombre_razon_social,
                nombre_cliente=nombre_cliente,
                apellido_cliente=apellido_cliente,
                identificador=idenficador_cliente,
                tipo_cliente=tipo_cliente
            )

            contacto_cliente.objects.create(
                telefono=telefono,
                correo=correo_electronico,
                id_cliente=obj_cliente
            )

            bitacora.objects.create(
                id_usuario=obj_usuario,
                accion=(
                    f"Registró al cliente "
                    f"{obj_cliente.nombre_razon_social}, "
                    f"identificado como "
                    f"{obj_cliente.identificador}."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Cliente Registrado",
            "descripcion": (
                "El cliente y sus datos de contacto "
                "se registraron correctamente."
            ),
            "icon": "success"
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario no encontrado",
            "descripcion": (
                "No se encontró el usuario responsable "
                "del registro. Inicie sesión nuevamente."
            ),
            "icon": "error"
        })

    except IntegrityError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador Duplicado",
            "descripcion": (
                "Ya existe un cliente registrado con "
                "ese identificador."
            ),
            "icon": "warning"
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del Servidor",
            "descripcion": (
                "Ocurrió un error al registrar el cliente. "
                f"Inténtelo nuevamente {e}."
            ),
            "icon": "error"
        })
    
def buscar_datos_cliente(request):
    if request.method == "POST":
        tipo_cliente = request.POST.get("tipo_cliente_b", "").strip()
        tipo_identificador_b = request.POST.get("tipo_identificador_b", "").strip()
        identificador_b = request.POST.get("identificador_b", "").strip()

        campos = [
            (tipo_cliente, "Tipo de Cliente", "Por favor, debe seleccionar una opción."),
            (tipo_identificador_b, "Tipo de Identificador", "Por favor, debe seleccionar el tipo de identificación."),
            (identificador_b, "Identificador", "Por favor, debe ingresar la identificación del cliente.")
        ]

        for valor, campo, mensaje in campos:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        if tipo_cliente not in {"NATURAL", "EMPRESA"}:
            return JsonResponse({
                "estado": "fallo",
                "title": "Tipo de cliente inválido",
                "descripcion": "Seleccione un tipo de cliente válido.",
                "icon": "warning"
            })

        if tipo_identificador_b not in {"V", "E", "J", "G"} or not identificador_b.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Identificación inválida",
                "descripcion": "Verifique el tipo y número de identificación.",
                "icon": "warning"
            })

        identificacion_cliente = f"{tipo_identificador_b}-{identificador_b}"

        cliente_obj = (
            cliente.objects
            .select_related("contacto")
            .filter(
                identificador=identificacion_cliente,
                tipo_cliente=tipo_cliente
            )
            .first()
        )

        if not cliente_obj:
            return JsonResponse({
                "estado": "fallo",
                "title": "Cliente no encontrado",
                "descripcion": "No se encontró un cliente con los datos proporcionados.",
                "icon": "warning"
            })

        contacto = cliente_obj.contacto

        return JsonResponse({
            "estado": "exito",
            "title": "Cliente encontrado",
            "descripcion": "Los datos del cliente se obtuvieron correctamente.",
            "icon": "success",
            "cliente": {
                "id_cliente": cliente_obj.id_cliente,
                "nombre_razon_social": cliente_obj.nombre_razon_social,
                "nombres_cliente": cliente_obj.nombre_cliente,
                "apellidos_cliente": cliente_obj.apellido_cliente,
                "identificador": cliente_obj.identificador,
                "tipo_cliente": cliente_obj.tipo_cliente,
                "activo": cliente_obj.activo,
                "fecha_registro": cliente_obj.fecha_registro.strftime("%d/%m/%Y %H:%M:%S"),
                "contacto": {
                    "id_contacto": contacto.id_contacto,
                    "telefono": contacto.telefono,
                    "correo": contacto.correo
                }
            }
        })
        
def actualizar_clientes_ventas(request):
    if request.method != "POST":
        return render(request, "Clientes/actualizar_clientes.html")

    id_cliente = request.POST.get("id_cliente")
    tipo_cliente = request.POST.get("tipo_cliente")
    nombre_cliente = request.POST.get("nombre_cliente", "").strip()
    apellido_cliente = request.POST.get("apellido_cliente", "").strip()
    nombre_empresa = request.POST.get("nombre_empresa", "").strip()
    tipo_identificador = request.POST.get("tipo_identificador")
    identificador = request.POST.get("identificador")

    prefijo = request.POST.get("prefijo")
    num_telefono = request.POST.get("num_telefono")

    correo = request.POST.get("correo")
    dominio = request.POST.get("dominio")

    campos = [
        (id_cliente, "Cliente", "No se ha especificado el cliente que desea actualizar."),
        (tipo_identificador, "Tipo de Identificador", "Por favor, seleccione el tipo de identificador."),
        (identificador, "Identificador", "Por favor, ingrese el identificador."),
        (tipo_cliente, "Tipo de Cliente", "Por favor, seleccione el tipo de cliente."),
        (num_telefono, "Número Telefónico", "Por favor, ingrese el número telefónico del cliente."),
        (prefijo, "Prefijo Telefónico", "Por favor, seleccione el prefijo telefónico del cliente."),
        (correo, "Correo Electrónico", "Por favor, ingrese el nombre del correo electrónico del cliente."),
        (dominio, "Dominio", "Por favor, seleccione el dominio del correo electrónico del cliente."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if tipo_cliente == "EMPRESA":
        if not nombre_empresa:
            return JsonResponse({
                "estado": "fallo",
                "title": "Nombre de la Empresa",
                "descripcion": "Por favor, ingrese el nombre de la empresa.",
                "icon": "warning"
            })

        nombre_razon_social_actualizado = nombre_empresa
        nombre_cliente_actualizado = ""
        apellido_cliente_actualizado = ""

    elif tipo_cliente == "NATURAL":
        if not nombre_cliente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Nombre del Cliente",
                "descripcion": "Por favor, ingrese el nombre del cliente.",
                "icon": "warning"
            })

        if not apellido_cliente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Apellido del Cliente",
                "descripcion": "Por favor, ingrese el apellido del cliente.",
                "icon": "warning"
            })

        nombre_razon_social_actualizado = f"{nombre_cliente} {apellido_cliente}".strip()
        nombre_cliente_actualizado = nombre_cliente
        apellido_cliente_actualizado = apellido_cliente

    else:
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo de Cliente Inválido",
            "descripcion": "Seleccione un tipo de cliente válido.",
            "icon": "warning"
        })

    identificador_actualizado = f"{tipo_identificador}-{identificador}"
    telefono_actualizado = f"{prefijo}-{num_telefono}"
    correo_actualizado = f"{correo}{dominio}"

    try:
        with transaction.atomic():
            cliente_obj = cliente.objects.get(id_cliente=id_cliente)

            cliente_obj.nombre_razon_social = nombre_razon_social_actualizado
            cliente_obj.nombre_cliente = nombre_cliente_actualizado
            cliente_obj.apellido_cliente = apellido_cliente_actualizado
            cliente_obj.identificador = identificador_actualizado
            cliente_obj.tipo_cliente = tipo_cliente
            cliente_obj.save()

            contacto_obj, creado = contacto_cliente.objects.get_or_create(
                id_cliente=cliente_obj,
                defaults={
                    "telefono": telefono_actualizado,
                    "correo": correo_actualizado
                }
            )

            if not creado:
                contacto_obj.telefono = telefono_actualizado
                contacto_obj.correo = correo_actualizado
                contacto_obj.save()

            obj_usuario = usuarios.objects.get(
                cedula_identidad=request.session.get("cedula_identidad")
            )

            bitacora.objects.create(
                id_usuario=obj_usuario,
                accion=(
                    f"Actualizó los datos del cliente "
                    f"{cliente_obj.nombre_razon_social}, "
                    f"identificado como {cliente_obj.identificador}."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Cliente Actualizado",
            "descripcion": (
                "Los datos del cliente y su información de contacto "
                "se actualizaron correctamente."
            ),
            "icon": "success"
        })

    except cliente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente No Encontrado",
            "descripcion": "El cliente que intenta actualizar no existe.",
            "icon": "warning"
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario No Encontrado",
            "descripcion": "No se encontró el usuario responsable. Inicie sesión nuevamente.",
            "icon": "error"
        })

    except IntegrityError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos Duplicados",
            "descripcion": (
                "El identificador, teléfono o correo electrónico "
                "puede estar registrado en otro cliente."
            ),
            "icon": "warning"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del Servidor",
            "descripcion": (
                "Ocurrió un error al actualizar el cliente. "
                "Inténtelo nuevamente."
            ),
            "icon": "error"
        })

def visualizar_clientes_ventas(request):
    return render(request, "Clientes/visualizar_clientes.html")

def clientes_registrados_ventas(request):
    tipo_cliente = request.POST.get("tipo_cliente", "").strip()
    tipo_identificador = request.POST.get("tipo_identificador", "").strip()
    identificador = request.POST.get("identificador", "").strip()

    clientes = cliente.objects.select_related("contacto").all()

    if tipo_cliente:
        clientes = clientes.filter(tipo_cliente=tipo_cliente)

    if tipo_identificador and identificador:
        identificador_completo = f"{tipo_identificador}-{identificador}"
        clientes = clientes.filter(identificador=identificador_completo)
    elif tipo_identificador:
        clientes = clientes.filter(
            identificador__startswith=f"{tipo_identificador}-"
        )
    elif identificador:
        clientes = clientes.filter(
            identificador__endswith=f"-{identificador}"
        )

    clientes = clientes.order_by("nombre_razon_social")

    datos_clientes = []

    for registro in clientes:
        datos_clientes.append({
            "id_cliente": registro.id_cliente,
            "nombre_razon_social": registro.nombre_razon_social,
            "nombre_cliente": registro.nombre_cliente,
            "apellido_cliente": registro.apellido_cliente,
            "identificador": registro.identificador,
            "tipo_cliente": registro.tipo_cliente,
            "activo": registro.activo,
            "fecha_registro": registro.fecha_registro.strftime("%d/%m/%Y %H:%M:%S"),
            "telefono": registro.contacto.telefono,
            "correo": registro.contacto.correo
        })

    return JsonResponse({
        "estado": "exito",
        "clientes": datos_clientes
    })

def detalle_registro_cliente(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "Esta operación requiere una solicitud POST.",
            "icon": "warning"
        }, status=405)

    id_cliente = request.POST.get("id_cliente", "").strip()

    if not id_cliente:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no seleccionado",
            "descripcion": "Debe seleccionar un cliente para consultar sus datos.",
            "icon": "warning"
        }, status=400)

    try:
        registro = cliente.objects.select_related("contacto").get(
            id_cliente=id_cliente
        )

        try:
            contacto = registro.contacto
            telefono = contacto.telefono
            correo = contacto.correo
        except contacto_cliente.DoesNotExist:
            telefono = ""
            correo = ""

        return JsonResponse({
            "estado": "exito",
            "cliente": {
                "id_cliente": registro.id_cliente,
                "tipo_cliente": registro.tipo_cliente,
                "nombre_razon_social": registro.nombre_razon_social,
                "nombre_cliente": registro.nombre_cliente,
                "apellido_cliente": registro.apellido_cliente,
                "identificador": registro.identificador,
                "telefono": telefono,
                "correo": correo,
                "activo": registro.activo,
                "fecha_registro": (
                    timezone.localtime(registro.fecha_registro).strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )
                    if registro.fecha_registro
                    else "No registrada"
                )
            }
        })

    except cliente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "descripcion": "El cliente solicitado no existe o no está registrado.",
            "icon": "warning"
        }, status=404)

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El ID del cliente proporcionado no es válido.",
            "icon": "warning"
        }, status=400)

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar",
            "descripcion": "Ocurrió un error al obtener los datos del cliente.",
            "icon": "error"
        }, status=500)

def clientes_registrados_pdf(request):
    tipo_cliente = request.POST.get("tipo_cliente", "").strip()

    clientes = cliente.objects.filter(activo=True)

    if tipo_cliente in [
        cliente.TipoCliente.NATURAL,
        cliente.TipoCliente.EMPRESA
    ]:
        clientes = clientes.filter(
            tipo_cliente=tipo_cliente
        )

    clientes = clientes.order_by("id_cliente")

    # VALIDAR CLIENTES REGISTRADOS
    if not clientes.exists():
        return JsonResponse({
            "title": "Clientes no registrados",
            "descripcion": (
                "No hay clientes registrados para generar "
                "el reporte PDF con los filtros seleccionados."
            ),
            "icon": "warning"
        })

    # RESPUESTA PDF
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="lista_clientes.pdf"'
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

    # TIPO DE CLIENTE PARA EL TÍTULO
    if tipo_cliente == cliente.TipoCliente.NATURAL:
        titulo = "LISTA DE CLIENTES - PERSONAS NATURALES"
    elif tipo_cliente == cliente.TipoCliente.EMPRESA:
        titulo = "LISTA DE CLIENTES - EMPRESAS"
    else:
        titulo = "LISTA DE CLIENTES"

    # DATOS TABLA
    datos_tabla = [
        # ENCABEZADO PRINCIPAL
        [titulo, "", "", ""],

        # ENCABEZADO DE COLUMNAS
        [
            "ID",
            "Cliente",
            "Identificador",
            "Tipo de cliente"
        ],
    ]

    # REGISTROS     
    for numero, registro in enumerate(clientes, start=1):
        datos_tabla.append([
            numero,
            registro.nombre_razon_social or "No registrado",
            registro.identificador or "No registrado",
            registro.get_tipo_cliente_display()
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[45, 205, 125, 140],
        repeatRows=2
    )

    tabla.setStyle(TableStyle([
        # ENCABEZADO PRINCIPAL
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        # ENCABEZADO DE COLUMNAS
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 10),

        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        # CONTENIDO
        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 10),
        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),

        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        # BORDES
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # ESPACIADO
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    # ELEMENTOS
    elementos = [tabla]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_clientes_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_clientes_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_clientes_pdf(canvas, documento, ruta_logo):
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

def detalle_cliente_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "title": "Método no permitido",
            "descripcion": "Esta operación requiere una solicitud POST.",
            "icon": "warning"
        }, status=405)

    id_cliente = request.POST.get("id_cliente", "").strip()

    if not id_cliente:
        return JsonResponse({
            "title": "Cliente no seleccionado",
            "descripcion": "Debe seleccionar un cliente para generar el reporte PDF.",
            "icon": "warning"
        }, status=400)

    try:
        registro = (
            cliente.objects
            .select_related("contacto")
            .get(id_cliente=id_cliente)
        )

    except (cliente.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "title": "Cliente no encontrado",
            "descripcion": "El cliente solicitado no existe o no está registrado.",
            "icon": "warning"
        }, status=404)

    # CONTACTO
    try:
        contacto = registro.contacto
        telefono = contacto.telefono
        correo = contacto.correo
    except contacto_cliente.DoesNotExist:
        telefono = "No registrado"
        correo = "No registrado"

    # FECHA DE REGISTRO
    fecha_registro = (
        timezone.localtime(
            registro.fecha_registro
        ).strftime("%d/%m/%Y %H:%M:%S")
        if registro.fecha_registro
        else "No registrada"
    )

    # TIPO DE CLIENTE
    tipo = registro.get_tipo_cliente_display()

    # NOMBRE DEL CLIENTE
    nombre = registro.nombre_razon_social or "No registrado"


    # RESPUESTA PDF
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="detalle_cliente_{registro.id_cliente}.pdf"'
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=130,
        bottomMargin=40
    )

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    # ESTILOS
    estilo_etiqueta = ParagraphStyle(
        "EtiquetaCliente",
        fontName="Times-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#00445F")
    )

    estilo_valor = ParagraphStyle(
        "ValorCliente",
        fontName="Times-Roman",
        fontSize=10,
        leading=14,
        textColor=colors.black,
        wordWrap="CJK"
    )

    estilo_titulo = ParagraphStyle(
        "TituloCliente",
        fontName="Times-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    # DATOS DEL CLIENTE
    datos_tabla = [
        [
            Paragraph(
                "DETALLE DEL CLIENTE",
                estilo_titulo
            ),
            ""
        ],
        [
            Paragraph("Cliente Registrado:", estilo_etiqueta),
            Paragraph(escape(str(nombre)), estilo_valor)
        ],
        [
            Paragraph("Identificador:", estilo_etiqueta),
            Paragraph(
                escape(str(registro.identificador or "No registrado")),
                estilo_valor
            )
        ],
        [
            Paragraph("Tipo de Identificador:", estilo_etiqueta),
            Paragraph(escape(str(tipo)), estilo_valor)
        ],
        [
            Paragraph("Teléfono:", estilo_etiqueta),
            Paragraph(escape(str(telefono)), estilo_valor)
        ],
        [
            Paragraph("Correo Electrónico:", estilo_etiqueta),
            Paragraph(escape(str(correo)), estilo_valor)
        ],
        [
            Paragraph("Fecha y Hora del Registro:", estilo_etiqueta),
            Paragraph(escape(str(fecha_registro)), estilo_valor)
        ],
    ]

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[190, 320],
        repeatRows=1
    )

    tabla.setStyle(TableStyle([
        # ENCABEZADO
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # CONTENIDO
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F0F5F7")),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),

        # BORDES
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # ESPACIADO
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    # ELEMENTOS
    elementos = [tabla]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_detalle_cliente_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_detalle_cliente_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_detalle_cliente_pdf(canvas, documento, ruta_logo):
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