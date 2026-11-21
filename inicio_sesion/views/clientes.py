from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.contrib.auth.hashers import make_password

from inicio_sesion.models import bitacora, usuarios, contacto, cliente, credenciales, residencia, nacimiento

import os
from django.conf import settings
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from xml.sax.saxutils import escape

# Create your views here.

# VALIDACIONES

def validar_identificador(request):
    tipo_identificador = request.POST.get("tipo_identificador", "").strip().upper()
    identificador = request.POST.get("identificador", "").strip()
    id_usuario = request.POST.get("id_usuario", "").strip()

    if not tipo_identificador or not identificador:
        return JsonResponse({
            "existe": False
        })

    identificador_usuario = f"{tipo_identificador}-{identificador}"

    consulta = usuarios.objects.filter(
        Q(cedula_identidad__iexact=identificador_usuario) | 
        Q(cedula_identidad__iexact=identificador)
    )

    if id_usuario:
        consulta = consulta.exclude(
            id_usuario=id_usuario
        )

    existe = consulta.exists()

    return JsonResponse({
        "existe": existe
    })

# REGISTRAR CLIENTE

def registrar_clientes_foro(request):
    if request.method != "POST":
        return render(request, "inicio_sesion/registrar_clientes.html")

    tipo_cliente = request.POST.get("tipo_cliente", "").strip().upper()
    nombre_cliente = request.POST.get("nombre_cliente", "").strip()
    apellido_cliente = request.POST.get("apellido_cliente", "").strip()
    nombre_empresa = request.POST.get("nombre_empresa", "").strip()

    tipo_identificador = request.POST.get("tipo_identificador", "").strip().upper()
    identificador = request.POST.get("identificador", "").strip()
    
    prefijo = request.POST.get("prefijo", "").strip()
    num_telefono = request.POST.get("num_telefono", "").strip()

    correo = request.POST.get("correo", "").strip()
    dominio = request.POST.get("dominio", "").strip()

    nombre_usuario = request.POST.get("nombre_usuario", "").strip()
    contrasenia = request.POST.get("contrasenia", "")

    condicion_residencia = request.POST.get("condicion_residencia", "").strip()
    municipio_residencia = request.POST.get("municipio_residencia", "").strip()
    parroquia_residencia = request.POST.get("parroquia_residencia", "").strip()
    direccion_residencia = request.POST.get("direccion_residencia", "").strip()

    if tipo_cliente not in ("NATURAL", "EMPRESA"):
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo de Cliente",
            "descripcion": "El tipo de cliente seleccionado no es válido.",
            "icon": "warning"
        })

    campos = [
        (tipo_identificador, "Tipo de Identificador", "Por favor, seleccione el tipo de identificador."),
        (identificador, "Identificador", "Por favor, ingrese el identificador."),
        (tipo_cliente, "Tipo de Cliente", "Por favor, seleccione el tipo de cliente."),
        
        (prefijo, "Prefijo Telefónico", "Por favor, seleccione el prefijo telefónico del cliente."),
        (num_telefono, "Número Telefónico", "Por favor, ingrese el número telefónico del cliente."),
        (correo, "Correo", "Por favor, ingrese el nombre del correo electrónico del cliente."),
        (dominio, "Dominio", "Por favor, seleccione el dominio del correo electrónico del cliente."),
        
        (nombre_usuario, "Nombre de Usuario", "Por favor, ingrese el nombre de usuario."),
        (contrasenia, "Contraseña", "Por favor, ingrese la contraseña del usuario."),
        
        (condicion_residencia, "Condición de Residencia", "Por favor, debe ingresar la condición de residencia."),
        (municipio_residencia, "Municipio de Residencia", "Por favor, debe seleccionar el municipio de residencia."),
        (parroquia_residencia, "Prroquia de Residencia", "Por favor, debe seleccionar la parroquia de residencia."),
        (direccion_residencia, "Dirección de Residencia", "Por favor, debe ingresar la dirección de residencia."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if tipo_cliente == "NATURAL":

        if not nombre_cliente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Nombres del Cliente",
                "descripcion": "Por favor, ingrese los nombres del cliente.",
                "icon": "warning"
            })

        if not apellido_cliente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Apellidos del Cliente",
                "descripcion": "Por favor, ingrese los apellidos del cliente.",
                "icon": "warning"
            })

        nombre_razon_social = (
            f"{nombre_cliente} {apellido_cliente}"
        )

        nombre_empresa = "N/A"

    elif tipo_cliente == "EMPRESA":

        if not nombre_empresa:
            return JsonResponse({
                "estado": "fallo",
                "title": "Nombre de la Empresa",
                "descripcion": "Por favor, ingrese el nombre de la empresa.",
                "icon": "warning"
            })

        nombre_razon_social = nombre_empresa
        nombre_cliente = "N/A"
        apellido_cliente = "N/A"

    identificador_cliente = (
        f"{tipo_identificador}-{identificador}"
    )

    correo_electronico = correo + dominio
    telefono = f"{prefijo}-{num_telefono}"

    genero = "N/A"
    estado_civil = "N/A"

    telefono_secundario = "N/A"
    correo_secundario = "N/A"

    # DATOS QUE NO VAN HACER ALMACENADO
    pais_nacimiento = "N/A"
    estado_nacimiento = "N/A"
    municipio_nacimiento = "N/A"
    parroquia_nacimiento = "N/A"
    direccion_nacimiento = "N/A"
    fecha_nacimiento = "N/A"

    try:
        with transaction.atomic():
            usuario = usuarios.objects.create(
                tipo_usuario=tipo_cliente,
                nombre_razon_social=nombre_razon_social,
                nombres=nombre_cliente,
                apellidos=apellido_cliente,
                cedula_identidad=identificador_cliente,
                genero=genero,
                estado_civil=estado_civil
            )

            contacto.objects.create(
                telefono_principal=telefono,
                telefono_secundario=telefono_secundario,
                correo_principal=correo_electronico,
                correo_secundario=correo_secundario,
                id_usuario=usuario
            )

            residencia.objects.create(
                condicion_residencia=condicion_residencia,
                municipio=municipio_residencia,
                parroquia=parroquia_residencia,
                direccion=direccion_residencia,
                id_usuario=usuario
            )

            # DATOS NO RELEVANTES
            nacimiento.objects.create(
                pais=pais_nacimiento,
                estado=estado_nacimiento,
                municipio=municipio_nacimiento,
                parroquia=parroquia_nacimiento,
                direccion=direccion_nacimiento,
                fecha_nacimiento=fecha_nacimiento,
                id_usuario=usuario
            )

            credenciales.objects.create(
                nombre_usuario=nombre_usuario,
                clave=make_password(contrasenia),
                id_usuario=usuario
            )
            
            cliente.objects.create(
                id_usuario=usuario,
            )

            bitacora.objects.create(
                id_usuario=usuario,
                nombre_modulo="Registro de clientes",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=(
                    f"Registró al cliente "
                    f"{usuario.nombre_razon_social}, "
                    f"identificado como "
                    f"{usuario.cedula_identidad}."
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
            "title": "Registro duplicado",
            "descripcion": (
                "Ya existe un cliente registrado con "
                "ese identificador o con alguno de sus datos únicos."
            ),
            "icon": "warning"
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del Servidor",
            "descripcion": (
                "Ocurrió un error inesperado al registrar "
                "el cliente. Inténtelo nuevamente "
                f"Error {e}"
            ),
            "icon": "error"
        })

# ACTUALIZAR DATOS DEL CLIENTE
  
def buscar_datos_cliente(request):
    tipo_cliente = request.POST.get("tipo_cliente_b", "").strip().upper()
    tipo_identificador_b = request.POST.get("tipo_identificador_b", "").strip().upper()
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

    if (
        tipo_identificador_b not in {"V", "E", "J", "G"}
        or not identificador_b.isdigit()
    ):
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificación inválida",
            "descripcion": "Verifique el tipo y número de identificación.",
            "icon": "warning"
        })

    identificacion_cliente = f"{tipo_identificador_b}-{identificador_b}"

    try:
        cliente_obj = cliente.objects.select_related(
            "id_usuario"
        ).filter(
            id_usuario__cedula_identidad=identificacion_cliente,
            id_usuario__tipo_usuario=tipo_cliente
        ).first()

        if not cliente_obj:
            return JsonResponse({
                "estado": "fallo",
                "title": "Cliente no encontrado",
                "descripcion": (
                    "No se encontró un cliente registrado con "
                    "los datos de identificación proporcionados."
                ),
                "icon": "warning"
            })

        usuario = cliente_obj.id_usuario

        contacto_obj = contacto.objects.get(
            id_usuario=usuario
        )

        residencia_obj = residencia.objects.get(
            id_usuario=usuario
        )

        return JsonResponse({
            "estado": "exito",
            "title": "Cliente encontrado",
            "descripcion": "Los datos del cliente se obtuvieron correctamente.",
            "icon": "success",
            "cliente": {
                "id_cliente": cliente_obj.id_cliente,
                "id_usuario": usuario.id_usuario,
                "nombre_razon_social": usuario.nombre_razon_social,
                "nombres_cliente": usuario.nombres,
                "apellidos_cliente": usuario.apellidos,
                "identificador": usuario.cedula_identidad,
                "tipo_cliente": usuario.tipo_usuario,

                "contacto": {
                    "id_contacto": (
                        contacto_obj.id_contacto
                        if contacto_obj else None
                    ),
                    "telefono": (
                        contacto_obj.telefono_principal
                        if contacto_obj else ""
                    ),
                    "correo": (
                        contacto_obj.correo_principal
                        if contacto_obj else ""
                    )
                },

                "residencia": {
                    "id_residencia": (
                        residencia_obj.id_residencia
                        if residencia_obj else None
                    ),
                    "condicion_residencia": (
                        residencia_obj.condicion_residencia
                        if residencia_obj else ""
                    ),
                    "municipio": (
                        residencia_obj.municipio
                        if residencia_obj else ""
                    ),
                    "parroquia": (
                        residencia_obj.parroquia
                        if residencia_obj else ""
                    ),
                    "direccion": (
                        residencia_obj.direccion
                        if residencia_obj else ""
                    )
                }
            }
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del servidor",
            "descripcion": (
                "Ocurrió un error al consultar los datos del cliente. "
                "Inténtelo nuevamente."
            ),
            "icon": "error"
        })
    
def actualizar_clientes_ventas(request):
    if request.method != "POST":
        return render(request, "Modulos/Clientes/actualizar_clientes.html")

    id_usuario = request.POST.get("id_usuario", "").strip()
    tipo_cliente = request.POST.get("tipo_cliente", "").strip().upper()
    nombre_cliente = request.POST.get("nombre_cliente", "").strip()
    apellido_cliente = request.POST.get("apellido_cliente", "").strip()
    nombre_empresa = request.POST.get("nombre_empresa", "").strip()
    tipo_identificador = request.POST.get("tipo_identificador", "").strip().upper()
    identificador = request.POST.get("identificador", "").strip()

    prefijo = request.POST.get("prefijo", "").strip()
    num_telefono = request.POST.get("num_telefono", "").strip()

    correo = request.POST.get("correo", "").strip()
    dominio = request.POST.get("dominio", "").strip()

    condicion_residencia = request.POST.get("condicion_residencia", "").strip()
    municipio_residencia = request.POST.get("municipio_residencia", "").strip()
    parroquia_residencia = request.POST.get("parroquia_residencia", "").strip()
    direccion_residencia = request.POST.get("direccion_residencia", "").strip()

    campos = [
        (id_usuario, "Usuario", "No se ha especificado el usuario que desea actualizar."),
        (tipo_identificador, "Tipo de Identificador", "Por favor, seleccione el tipo de identificador."),
        (identificador, "Identificador", "Por favor, ingrese el identificador."),
        (tipo_cliente, "Tipo de Cliente", "Por favor, seleccione el tipo de cliente."),
        
        (num_telefono, "Número Telefónico", "Por favor, ingrese el número telefónico del cliente."),
        (prefijo, "Prefijo Telefónico", "Por favor, seleccione el prefijo telefónico del cliente."),
        (correo, "Correo Electrónico", "Por favor, ingrese el nombre del correo electrónico del cliente."),
        (dominio, "Dominio", "Por favor, seleccione el dominio del correo electrónico del cliente."),
        
        (condicion_residencia, "Condición de Residencia", "Por favor, debe seleccionar la condición de residencia."),
        (municipio_residencia, "Municipio de Residencia", "Por favor, debe seleccionar el municipio donde reside."),
        (parroquia_residencia, "Parroquia de Residencia", "Por favor, debe seleccionar la parroquia donde reside."),
        (direccion_residencia, "Dirección de Residencia", "Por favor, debe ingresar la dirección de domicilio."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if not id_usuario.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario Inválido",
            "descripcion": "El identificador del usuario no es válido.",
            "icon": "warning"
        })

    if tipo_identificador not in ["V", "E", "J", "G"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo de Identificador Inválido",
            "descripcion": "Seleccione un tipo de identificador válido.",
            "icon": "warning"
        })

    if not identificador.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador Inválido",
            "descripcion": "El identificador debe contener únicamente números.",
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
        nombre_cliente_actualizado = "N/A"
        apellido_cliente_actualizado = "N/A"

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

        nombre_razon_social_actualizado = (
            f"{nombre_cliente} {apellido_cliente}".strip()
        )
        nombre_cliente_actualizado = nombre_cliente
        apellido_cliente_actualizado = apellido_cliente

    else:
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo de Cliente Inválido",
            "descripcion": "Seleccione un tipo de cliente válido.",
            "icon": "warning"
        })

    identificador_actualizado = (
        f"{tipo_identificador}-{identificador}"
    )
    telefono_actualizado = f"{prefijo}-{num_telefono}"
    correo_actualizado = f"{correo}{dominio}"

    try:
        with transaction.atomic():

            obj_usuario = usuarios.objects.get(
                cedula_identidad=request.session.get(
                    "cedula_identidad"
                )
            )

            usuario_cliente = usuarios.objects.get(id_usuario=id_usuario)
            usuario_cliente.tipo_usuario = tipo_cliente
            usuario_cliente.nombre_razon_social = nombre_razon_social_actualizado
            usuario_cliente.nombres = nombre_cliente_actualizado
            usuario_cliente.apellidos = apellido_cliente_actualizado
            usuario_cliente.cedula_identidad = identificador_actualizado
            usuario_cliente.save()

            contacto_obj = contacto.objects.get(id_usuario=usuario_cliente)
            contacto_obj.telefono_principal = telefono_actualizado
            contacto_obj.correo_principal = correo_actualizado
            contacto_obj.save(update_fields=[
                "telefono_principal",
                "correo_principal"
            ])

            residencia_obj = residencia.objects.get(id_usuario=usuario_cliente)
            residencia_obj.condicion_residencia = condicion_residencia
            residencia_obj.municipio = municipio_residencia
            residencia_obj.parroquia = parroquia_residencia
            residencia_obj.direccion = direccion_residencia
            residencia_obj.save()

            bitacora.objects.create(
                id_usuario=obj_usuario,
                nombre_modulo="Actualización de datos del cliente",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=(
                    f"Actualizó los datos del cliente "
                    f"{usuario_cliente.nombre_razon_social}, "
                    f"identificado como "
                    f"{usuario_cliente.cedula_identidad}."
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

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario No Encontrado",
            "descripcion": (
                "No se encontró el usuario que desea actualizar "
                "o el usuario responsable. Verifique la sesión."
            ),
            "icon": "warning"
        })

    except IntegrityError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos Duplicados",
            "descripcion": (
                "El identificador, teléfono o correo electrónico "
                "puede estar registrado en otro usuario."
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

# VISUALIZAR CLIENTES

def visualizar_clientes_ventas(request):
    return render(request, "Modulos/Clientes/visualizar_clientes.html")

def clientes_registrados_ventas(request):
    tipo_cliente = request.POST.get("tipo_cliente", "").strip().upper()
    tipo_identificador = request.POST.get("tipo_identificador", "").strip().upper()
    identificador = request.POST.get("identificador", "").strip()

    clientes = (
        cliente.objects
        .select_related(
            "id_usuario",
            "id_usuario__contacto",
            "id_usuario__credenciales"
        )
        .all()
    )

    if tipo_cliente:
        clientes = clientes.filter(
            id_usuario__tipo_usuario=tipo_cliente
        )

    if tipo_identificador and identificador:
        identificador_completo = (
            f"{tipo_identificador}-{identificador}"
        )

        clientes = clientes.filter(
            id_usuario__cedula_identidad__iexact=identificador_completo
        )

    elif tipo_identificador:
        clientes = clientes.filter(
            id_usuario__cedula_identidad__istartswith=(
                f"{tipo_identificador}-"
            )
        )

    elif identificador:
        clientes = clientes.filter(
            id_usuario__cedula_identidad__iendswith=(
                f"-{identificador}"
            )
        )

    clientes = clientes.order_by(
        "id_usuario__nombre_razon_social"
    )

    datos_clientes = []

    for registro in clientes:
        usuario = registro.id_usuario

        contacto_obj = getattr(
            usuario,
            "contacto",
            None
        )

        credenciales_obj = getattr(
            usuario,
            "credenciales",
            None
        )

        datos_clientes.append({
            "id_cliente": registro.id_cliente,
            "id_usuario": usuario.id_usuario,
            "nombre_razon_social": usuario.nombre_razon_social,
            "nombre_cliente": usuario.nombres,
            "apellido_cliente": usuario.apellidos,
            "identificador": usuario.cedula_identidad,
            "tipo_cliente": usuario.tipo_usuario,

            "telefono": (
                contacto_obj.telefono_principal
                if contacto_obj else ""
            ),

            "correo": (
                contacto_obj.correo_principal
                if contacto_obj else ""
            ),

            "nombre_usuario": (
                credenciales_obj.nombre_usuario
                if credenciales_obj else ""
            ),

            "bloqueado": (
                credenciales_obj.bloqueado
                if credenciales_obj else False
            ),

            "foto_perfil": (
                credenciales_obj.foto_perfil.url
                if (
                    credenciales_obj
                    and credenciales_obj.foto_perfil
                )
                else ""
            ),
        })

    return JsonResponse({
        "estado": "exito",
        "total": len(datos_clientes),
        "clientes": datos_clientes
    })

def detalle_registro_cliente(request):
    id_usuario = request.POST.get("id_usuario", "").strip()

    if not id_usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no seleccionado",
            "descripcion": "Debe seleccionar un cliente para consultar sus datos.",
            "icon": "warning"
        })

    if not id_usuario.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El ID del usuario proporcionado no es válido.",
            "icon": "warning"
        })

    try:
        cliente_obj = cliente.objects.select_related(
            "id_usuario"
        ).get(
            id_usuario__id_usuario=id_usuario
        )

        usuario = cliente_obj.id_usuario

        contacto_obj = contacto.objects.get(id_usuario=usuario)

        residencia_obj = residencia.objects.get(id_usuario=usuario)

        return JsonResponse({
            "estado": "exito",
            "cliente": {
                "id_cliente": cliente_obj.id_cliente,
                "id_usuario": usuario.id_usuario,
                "tipo_cliente": usuario.tipo_usuario,
                "nombre_razon_social": usuario.nombre_razon_social,
                "nombre_cliente": usuario.nombres,
                "apellido_cliente": usuario.apellidos,
                "identificador": usuario.cedula_identidad,

                "contacto": {
                    "id_contacto": (
                        contacto_obj.id_contacto
                        if contacto_obj else None
                    ),
                    "telefono": (
                        contacto_obj.telefono_principal
                        if contacto_obj else ""
                    ),
                    "correo": (
                        contacto_obj.correo_principal
                        if contacto_obj else ""
                    )
                },

                "residencia": {
                    "id_residencia": (
                        residencia_obj.id_residencia
                        if residencia_obj else None
                    ),
                    "condicion_residencia": (
                        residencia_obj.condicion_residencia
                        if residencia_obj else ""
                    ),
                    "municipio": (
                        residencia_obj.municipio
                        if residencia_obj else ""
                    ),
                    "parroquia": (
                        residencia_obj.parroquia
                        if residencia_obj else ""
                    ),
                    "direccion": (
                        residencia_obj.direccion
                        if residencia_obj else ""
                    )
                }
            }
        })

    except cliente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "descripcion": (
                "El cliente solicitado no existe, no está registrado "
                "o se encuentra inactivo."
            ),
            "icon": "warning"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar",
            "descripcion": (
                "Ocurrió un error al obtener los datos del cliente."
            ),
            "icon": "error"
        })

def bloqueo_cliente(request):
    id_usuario = request.POST.get("id_usuario", "").strip()

    if not id_usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no seleccionado",
            "descripcion": "Debe seleccionar un cliente para cambiar su estado de bloqueo.",
            "icon": "warning"
        })

    if not id_usuario.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El ID del usuario proporcionado no es válido.",
            "icon": "warning"
        })

    try:
        cliente_obj = cliente.objects.select_related(
            "id_usuario",
            "id_usuario__credenciales"
        ).get(
            id_usuario__id_usuario=id_usuario
        )

        credenciales_obj = cliente_obj.id_usuario.credenciales

        credenciales_obj.bloqueado = not credenciales_obj.bloqueado

        credenciales_obj.save(update_fields=["bloqueado"])

        bloqueado = credenciales_obj.bloqueado

        return JsonResponse({
            "estado": "exito",
            "title": "Cliente bloqueado" if bloqueado else "Cliente desbloqueado",
            "descripcion": (
                "El cliente ha sido bloqueado correctamente."
                if bloqueado
                else "El cliente ha sido desbloqueado correctamente."
            ),
            "icon": "success",
            "cliente": {
                "id_usuario": cliente_obj.id_usuario.id_usuario,
                "bloqueado": bloqueado
            }
        })

    except cliente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "descripcion": "No se encontró un cliente registrado con el ID proporcionado.",
            "icon": "warning"
        })

    except credenciales.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Credenciales no encontradas",
            "descripcion": "El cliente no tiene credenciales registradas.",
            "icon": "warning"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al actualizar",
            "descripcion": "Ocurrió un error al cambiar el estado de bloqueo del cliente.",
            "icon": "error"
        })

# 

def clientes_registrados_pdf(request):
    tipo_cliente = request.POST.get(
        "tipo_cliente", ""
    ).strip().upper()

    clientes = (
        cliente.objects
        .select_related("id_usuario")
        .all()
    )

    if tipo_cliente in ["NATURAL", "EMPRESA"]:
        clientes = clientes.filter(
            id_usuario__tipo_usuario=tipo_cliente
        )

    clientes = clientes.order_by(
        "id_usuario__nombre_razon_social"
    )

    if not clientes.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Clientes no registrados",
            "descripcion": (
                "No hay clientes registrados para generar "
                "el reporte PDF con los filtros seleccionados."
            ),
            "icon": "warning"
        })

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="lista_clientes.pdf"'
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

    if tipo_cliente == "NATURAL":
        titulo = "LISTA DE CLIENTES - PERSONAS NATURALES"

    elif tipo_cliente == "EMPRESA":
        titulo = "LISTA DE CLIENTES - EMPRESAS"

    else:
        titulo = "LISTA DE CLIENTES"

    datos_tabla = [
        [titulo, "", "", ""],
        [
            "N.º",
            "Cliente",
            "Identificador",
            "Tipo de cliente"
        ],
    ]

    for numero, registro in enumerate(clientes, start=1):
        usuario = registro.id_usuario

        datos_tabla.append([
            numero,
            usuario.nombre_razon_social or "No registrado",
            usuario.cedula_identidad or "No registrado",
            usuario.get_tipo_usuario_display()
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[45, 205, 125, 140],
        repeatRows=2
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),

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

# 

def detalle_cliente_pdf(request):
    tipo_cliente = request.POST.get(
        "tipo_cliente", ""
    ).strip().upper()

    clientes = (
        cliente.objects
        .select_related("id_usuario")
        .all()
    )

    if tipo_cliente in ["NATURAL", "EMPRESA"]:
        clientes = clientes.filter(
            id_usuario__tipo_usuario=tipo_cliente
        )

    clientes = clientes.order_by(
        "id_usuario__nombre_razon_social"
    )

    if not clientes.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Clientes no registrados",
            "descripcion": (
                "No hay clientes registrados para generar "
                "el reporte PDF con los filtros seleccionados."
            ),
            "icon": "warning"
        })

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="lista_clientes.pdf"'
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

    if tipo_cliente == "NATURAL":
        titulo = "LISTA DE CLIENTES - PERSONAS NATURALES"

    elif tipo_cliente == "EMPRESA":
        titulo = "LISTA DE CLIENTES - EMPRESAS"

    else:
        titulo = "LISTA DE CLIENTES"

    datos_tabla = [
        [titulo, "", "", ""],
        [
            "N.º",
            "Cliente",
            "Identificador",
            "Tipo de cliente"
        ],
    ]

    for numero, registro in enumerate(clientes, start=1):
        usuario = registro.id_usuario

        datos_tabla.append([
            numero,
            usuario.nombre_razon_social or "No registrado",
            usuario.cedula_identidad or "No registrado",
            usuario.get_tipo_usuario_display()
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[45, 205, 125, 140],
        repeatRows=2
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),

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
