from django.db import transaction
from django.shortcuts import render
from django.http import JsonResponse

from inicio_sesion.models import usuarios, credenciales, contacto, informacion_contacto, residencia, bitacora

import logging
import os
import uuid

from django.core.files.images import get_image_dimensions
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

# CONFIGURACIÓN DEL SISTEMA Y ACTUALIZAR DATOS USUARIO

# VISUALIZAR DATOS USUARIO DEL SISTEMA

def datos_usuario_sistema(request):
    cedula = request.session.get("cedula_identidad")
    perfil = request.session.get("perfil", "").strip().upper()

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "No se encontró la identificación del usuario en la sesión."
        }, status=401)

    try:
        usuario = usuarios.objects.select_related(
            "contacto",
            "residencia",
            "credenciales",
            "cliente"
        ).get(cedula_identidad=cedula)

        try:
            datos_contacto = usuario.contacto

            contacto_data = {
                "telefono_principal": datos_contacto.telefono_principal,
                "telefono_secundario": datos_contacto.telefono_secundario,
                "correo_principal": datos_contacto.correo_principal,
                "correo_secundario": datos_contacto.correo_secundario
            }

        except Exception:
            contacto_data = None

        try:
            datos_residencia = usuario.residencia

            residencia_data = {
                "condicion_residencia": datos_residencia.condicion_residencia,
                "municipio": datos_residencia.municipio,
                "parroquia": datos_residencia.parroquia,
                "direccion": datos_residencia.direccion
            }

        except Exception:
            residencia_data = None

        foto_perfil = None

        try:
            credencial = usuario.credenciales

            if credencial.foto_perfil:
                foto_perfil = credencial.foto_perfil.url.rstrip("/")

        except credenciales.DoesNotExist:
            pass

        es_cliente = hasattr(usuario, "cliente")

        return JsonResponse({
            "estado": "exito",
            "title": "Datos obtenidos",
            "icon": "success",

            "perfil": perfil,
            "es_cliente": es_cliente,

            "usuario": {
                "id_usuario": usuario.id_usuario,
                "tipo_usuario": usuario.tipo_usuario,
                "razon_social": usuario.nombre_razon_social,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula_identidad": usuario.cedula_identidad,
                "genero": usuario.genero,
                "estado_civil": usuario.estado_civil,
                "foto_perfil": foto_perfil
            },

            "contacto": contacto_data,
            "residencia": residencia_data
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario no encontrado",
            "icon": "error",
            "descripcion": "No se encontró un usuario asociado a la cédula de la sesión."
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del servidor",
            "icon": "error",
            "descripcion": "Ocurrió un error al consultar los datos del usuario."
        }, status=500)

# ACTUALIZAR DATOS DE PERFIL 

def actualizar_datos_sistema(request):
    if request.method != "POST":
        return render(request, "Modulos/Configuracion/perfil_usuario.html")

    genero = request.POST.get("genero", "").strip() or "N/A"
    estado_civil = request.POST.get("estado_civil", "").strip() or "N/A"
    
    prefijo_principal = request.POST.get("prefijo_principal", "").strip()
    numero_principal = request.POST.get("numero_principal", "").strip()

    prefijo_secundaria = request.POST.get("prefijo_secundaria", "").strip()
    numero_secundaria = request.POST.get("numero_secundaria", "").strip()

    correo_principal = request.POST.get("correo_principal", "").strip()
    dominio_principal = request.POST.get("dominio_principal", "").strip()

    correo_secundaria = request.POST.get("correo_secundaria", "").strip()
    dominio_secundaria = request.POST.get("dominio_secundaria", "").strip()

    condicion_residencia = request.POST.get("condicion_residencia", "").strip()
    municipio_residencia = request.POST.get("municipio_residencia", "").strip()
    parroquia_residencia = request.POST.get("parroquia_residencia", "").strip()
    direccion_residencia = request.POST.get("direccion_residencia", "").strip()

    campos = [
        (prefijo_principal, "Prefijo principal", "Por favor, seleccione un prefijo telefónico."),
        (numero_principal, "Número principal", "Por favor, ingrese el número telefónico principal."),
        (correo_principal, "Correo principal", "Por favor, ingrese el correo electrónico principal."),
        (dominio_principal, "Dominio principal", "Por favor, seleccione el dominio del correo electrónico principal."),
        (condicion_residencia, "Condición de residencia", "Por favor, seleccione la condición de residencia."),
        (municipio_residencia, "Municipio de residencia", "Por favor, seleccione el municipio de residencia."),
        (parroquia_residencia, "Parroquia de residencia", "Por favor, seleccione la parroquia de residencia."),
        (direccion_residencia, "Dirección de residencia", "Por favor, ingrese la dirección de residencia.")
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    # CORREO SECUNDARIO OPCIONAL
    if not correo_secundaria:
        email_secundario = "N/A"
    else:
        if not dominio_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Dominio vacío",
                "descripcion": "Por favor, selecciona el dominio del correo electrónico secundario.",
                "icon": "warning"
            })

    # TELÉFONO SECUNDARIO
    if not numero_secundaria:
        tlf_secundaria = "N/A"
    else:
        if not prefijo_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Prefijo vacío",
                "descripcion": "Por favor, selecciona el prefijo telefónico secundario.",
                "icon": "warning"
            })

    tlf_principal = prefijo_principal + "-" + numero_principal
    email_principal = correo_principal + dominio_principal

    try:
        with transaction.atomic():
            usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))
            usuario.estado_civil = estado_civil
            usuario.genero = genero
            usuario.save()

            info_contacto = contacto.objects.get(id_usuario=usuario)
            info_contacto.telefono_principal = tlf_principal
            info_contacto.telefono_secundario = tlf_secundaria
            info_contacto.correo_principal = email_principal
            info_contacto.correo_secundario = email_secundario
            info_contacto.save()

            info_residencia = residencia.objects.get(
                id_usuario=usuario
            )

            info_residencia.condicion_residencia = condicion_residencia
            info_residencia.municipio = municipio_residencia
            info_residencia.parroquia = parroquia_residencia
            info_residencia.direccion = direccion_residencia
            info_residencia.save()

            return JsonResponse({
                "estado": "exito",
                "title": "Éxito",
                "descripcion": "Los datos se actualizaron correctamente.",
                "icon": "success"
            })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": f"Ocurrió un error en el servidor: {e}",
            "icon": "error"
        })

# ACTUALIZAR MI IMAGEN DE PERFIL

def actualizar_img_perfil(request):

    foto_perfil = request.FILES.get("foto_perfil")

    if not foto_perfil:
        return JsonResponse({
            "estado": "fallo",
            "title": "Fotografía requerida",
            "descripcion": "Seleccione una fotografía de perfil.",
            "icon": "warning"
        })

    extension = os.path.splitext(foto_perfil.name)[1].lower()

    if extension not in [".png", ".jpg", ".jpeg"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Formato no permitido",
            "descripcion": "Solo se permiten imágenes PNG y JPG.",
            "icon": "warning"
        })

    if foto_perfil.size > 5 * 1024 * 1024:
        return JsonResponse({
            "estado": "fallo",
            "title": "Imagen demasiado grande",
            "descripcion": "La fotografía no debe superar los 5 MB.",
            "icon": "warning"
        })

    try:
        from PIL import Image, UnidentifiedImageError

        imagen = Image.open(foto_perfil)

        formato_real = imagen.format

        formatos_permitidos = {
            ".png": "PNG",
            ".jpg": "JPEG",
            ".jpeg": "JPEG"
        }

        if formato_real != formatos_permitidos.get(extension):
            raise ValueError("El contenido no coincide con la extensión.")

        imagen.verify()

        foto_perfil.seek(0)

        ancho, alto = get_image_dimensions(foto_perfil)

        if not ancho or not alto:
            raise ValueError("Dimensiones inválidas.")

        foto_perfil.seek(0)

    except (ValueError, OSError, UnidentifiedImageError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Imagen no válida",
            "descripcion": "El archivo seleccionado no es una imagen válida.",
            "icon": "warning"
        })

    # ------------------------------------------
    # OBTENER USUARIO Y CREDENCIALES
    # ------------------------------------------

    try:

        usuario = usuarios.objects.get(
            cedula_identidad=request.session.get("cedula_identidad")
        )

        info_credencial = credenciales.objects.get(
            id_usuario=usuario
        )

    except (usuarios.DoesNotExist, credenciales.DoesNotExist):

        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario no encontrado",
            "descripcion": "No se encontró la información del usuario.",
            "icon": "warning"
        })

    # ------------------------------------------
    # REGISTRAR O ACTUALIZAR FOTOGRAFÍA
    # ------------------------------------------

    nueva_ruta = None

    try:

        with transaction.atomic():

            info_credencial = credenciales.objects.select_for_update().get(
                id_usuario=usuario
            )

            foto_actual = info_credencial.foto_perfil

            ruta_anterior = (
                foto_actual.name
                if foto_actual and foto_actual.name
                else None
            )

            nombre_archivo = (
                f"{usuario.cedula_identidad}_"
                f"{uuid.uuid4().hex}{extension}"
            )

            info_credencial.foto_perfil.save(
                nombre_archivo,
                foto_perfil,
                save=False
            )

            nueva_ruta = info_credencial.foto_perfil.name

            info_credencial.save(
                update_fields=["foto_perfil"]
            )

            if ruta_anterior and ruta_anterior != nueva_ruta:

                transaction.on_commit(
                    lambda ruta=ruta_anterior: default_storage.delete(ruta)
                )

            url_foto = info_credencial.foto_perfil.url

        return JsonResponse({
            "estado": "exito",
            "title": "Fotografía actualizada",
            "descripcion": "La fotografía de perfil fue registrada correctamente.",
            "icon": "success",
            "foto_perfil": url_foto
        })

    except Exception:

        logger.exception(
            "Error al registrar la fotografía de perfil."
        )

        if nueva_ruta:
            try:
                default_storage.delete(nueva_ruta)

            except Exception:
                logger.exception(
                    "No fue posible eliminar la fotografía nueva."
                )

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al registrar",
            "descripcion": "Ocurrió un error al guardar la fotografía. Inténtelo nuevamente.",
            "icon": "error"
        })

# IMAGEN DE PERFIL ALMACENADA DEL USUARIO

def img_perfil_almacenado(request):

    try:
        usuario = usuarios.objects.get(
            cedula_identidad=request.session.get("cedula_identidad")
        )

        info_credencial = credenciales.objects.get(
            id_usuario=usuario
        )

        foto_perfil = info_credencial.foto_perfil

        if foto_perfil and foto_perfil.name:
            return JsonResponse({
                "estado": "exito",
                "foto_perfil": foto_perfil.url
            })

        return JsonResponse({
            "estado": "exito",
            "foto_perfil": None
        })

    except (usuarios.DoesNotExist, credenciales.DoesNotExist):
        return JsonResponse({
            "estado": "fallo",
            "foto_perfil": None
        })

# VISUALIZAR SON LOS DATOS DE CONTACTO ALMACENADO

def datos_contacto_foro(request):
    try:
        contacto = informacion_contacto.objects.first()

        return JsonResponse({
            "estado": "exito",
            "contacto": {
                "direccion": contacto.direccion or "" if contacto else "",
                "telefono": contacto.telefono or "" if contacto else "",
                "correo_electronico": contacto.correo_electronico or "" if contacto else ""
            }
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "Ocurrió un error al consultar la información de contacto.",
            "icon": "error"
        })
    
# REGISTRAR O REEMPLEZAR LOS DATOS DE CONTACTO ALMACENADO

def reemplazar_contactos_foro(request):
    if request.method != "POST":
        return render(request, "Modulos/Configuracion/contacto_empresa.html")

    prefijo = request.POST.get("prefijo")
    num_tlf = request.POST.get("num_telefono")
    correo = request.POST.get("correo")
    dominio = request.POST.get("dominio")
    direccion = request.POST.get("direccion")

    campos = [
        (prefijo, "Prefijo Telefonico", "Por favor, debe seleccionar el prefijo del teléfono."),
        (num_tlf, "Números Teléfonicos", "Por favor, debe ingresar los números telefonico."),
        (correo, "Correo Electrónico", "Por favor, debe ingresar el correo electrónico."),
        (dominio, "Dominio", "Por favor, debe seleccione el dominio del correo electrónico."),
        (direccion, "Dirección", "Por favor, debe ingresar la dirección de domicilio de la empresa."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    telefono = f"{prefijo} - {num_tlf}"
    correo_electronico = f"{correo}{dominio}"

    try:
        contacto = informacion_contacto.objects.first()

        if contacto:
            contacto.telefono = telefono
            contacto.correo_electronico = correo_electronico
            contacto.direccion = direccion
            contacto.save()

            return JsonResponse({
                "estado": "exito",
                "title": "Información actualizada",
                "descripcion": "Los datos de contacto de la empresa se actualizaron correctamente.",
                "icon": "success"
            })

        informacion_contacto.objects.create(
            telefono=telefono,
            correo_electronico=correo_electronico,
            direccion=direccion
        )

        return JsonResponse({
            "estado": "exito",
            "title": "Información registrada",
            "descripcion": "Los datos de contacto de la empresa se registraron correctamente.",
            "icon": "success"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "Ocurrió un error al guardar los datos de contacto.",
            "icon": "error"
        })

# IMAGENES FORO CARRUSEL Y PÚBLICIDAD
