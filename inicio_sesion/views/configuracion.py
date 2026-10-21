from django.db.models import Q
from django.db import transaction
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

from inicio_sesion.models import usuarios, credenciales, contacto, nacimiento, residencia, turnos_laborales, bitacora

import os
from django.core.files.images import get_image_dimensions
from django.utils.text import slugify

# CONFIGURACIÓN DEL SISTEMA Y ACTUALIZAR DATOS USUARIO

# VISUALIZAR DATOS USUARIO DEL SISTEMA

def datos_usuario_sistema(request):
    cedula = request.session.get("cedula_identidad")

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
            "credenciales"
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

        return JsonResponse({
            "estado": "exito",
            "title": "Datos obtenidos",
            "icon": "success",
            "usuario": {
                "id_usuario": usuario.id_usuario,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula_identidad": usuario.cedula_identidad,
                "genero": usuario.genero,
                "estado_civil": usuario.estado_civil,
                "foto_perfil": foto_perfil,
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
        }, status=404)

def actualizar_datos_sistema(request):
    if request.method != "POST":
        return render(request, "Modulos/Configuracion/perfil_usuario.html")

    foto_perfil = request.FILES.get("foto_perfil")
    
    prefijo_principal = request.POST.get("prefijo_principal")
    numero_principal = request.POST.get("numero_principal")
    
    prefijo_secundaria = request.POST.get("prefijo_secundaria")
    numero_secundaria = request.POST.get("numero_secundaria")
    
    correo_principal = request.POST.get("correo_principal")
    dominio_principal = request.POST.get("dominio_principal")
    
    correo_secundaria = request.POST.get("correo_secundaria")
    dominio_secundaria = request.POST.get("dominio_secundaria")
    
    condicion_residencia = request.POST.get("condicion_residencia")
    municipio_residencia = request.POST.get("municipio_residencia")
    parroquia_residencia = request.POST.get("parroquia_residencia")
    direccion_residencia = request.POST.get("direccion_residencia")

    cedula_usuario = request.session.get("cedula_identidad")

    campos = [
        # TELÉFONO PRINCIPAL
        (prefijo_principal, "prefijo principal", "Por favor, seleccione un prefijo telefónico."),
        (numero_principal, "número principal", "Por favor, ingrese el número telefónico principal."),

        # CORREO PRINCIPAL
        (correo_principal, "correo principal", "Por favor, ingrese el correo electrónico principal."),
        (dominio_principal, "dominio principal", "Por favor, seleccione el dominio del correo electrónico principal."),

        # RESIDENCIA
        (condicion_residencia, "condición de residencia", "Por favor, seleccione la condición de residencia."),
        (municipio_residencia, "municipio de residencia", "Por favor, seleccione el municipio de residencia."),
        (parroquia_residencia, "parroquia de residencia", "Por favor, selecciona la parroquia de residencia."),
        (direccion_residencia, "dirección de residencia", "Por favor, ingrese la dirección de residencia."),
    ]

    if foto_perfil:
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
            ancho, alto = get_image_dimensions(foto_perfil)

            if not ancho or not alto:
                raise ValueError("Imagen inválida")

        except (ValueError, OSError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Imagen no válida",
                "descripcion": "El archivo seleccionado no es una imagen válida.",
                "icon": "warning"
            })

        nombre_usuario = request.session.get("usuario")
        nombre_usuario = slugify(nombre_usuario)

        nombre_imagen = f"foto_perfil_{nombre_usuario}{extension}"
        foto_perfil.name = nombre_imagen
        
    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if not dominio_secundaria and not correo_secundaria:
        email_secundario = "N/A"

    elif not dominio_secundaria:
        return JsonResponse({
            "title": "Prefijo vacío",
            "descripcion": "Por favor, selecciona el dominio del Correo Electronico.",
            "icon": "warning"
        })

    elif not correo_secundaria:
        return JsonResponse({
            "title": "Número vacío",
            "descripcion": "Por favor, ingresa el nombre del Correo Electronico.",
            "icon": "warning"
        })
    else:
        email_secundario = correo_secundaria + dominio_secundaria 

    if not prefijo_secundaria and not numero_secundaria:
        tlf_secundaria = "N/A"

    elif not prefijo_secundaria:
        return JsonResponse({
            "estado": "fallo",
            "title": "Prefijo vacío",
            "descripcion": "Por favor, selecciona el prefijo telefónico.",
            "icon": "warning"
        })
    elif not numero_secundaria:
        return JsonResponse({
            "estado": "fallo",
            "title": "Número vacío",
            "descripcion": "Por favor, ingresa el número telefónico.",
            "icon": "warning"
        })
    else:
        tlf_secundaria = prefijo_secundaria + "-" + numero_secundaria

    tlf_principal = prefijo_principal + "-" + numero_principal
    
    email_principal = correo_principal + dominio_principal

    try:
        with transaction.atomic():
            usuario = usuarios.objects.get(cedula_identidad=cedula_usuario)

            info_credencial = credenciales.objects.get(id_usuario=usuario)
            if foto_perfil:
                info_credencial.foto_perfil = foto_perfil
                info_credencial.save(update_fields=["foto_perfil"])

            info_contacto = contacto.objects.get(id_usuario=usuario)
            info_contacto.telefono_principal = tlf_principal
            info_contacto.telefono_secundario = tlf_secundaria
            info_contacto.correo_principal = email_principal
            info_contacto.correo_secundario = email_secundario
            info_contacto.save()

            info_residencia = residencia.objects.get(id_usuario=usuario)
            info_residencia.condicion_residencia = condicion_residencia
            info_residencia.municipio = municipio_residencia
            info_residencia.parroquia = parroquia_residencia
            info_residencia.direccion = direccion_residencia
            info_residencia.save()

            return JsonResponse({
                "estado": "exito",
                "title": "Exito",
                "descripcion": "Exito en actualizar los datos",
                "icon": "success"
            })
    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": f"Ocurrio un error en el servidor {e}",
            "icon": "error"
        })    

