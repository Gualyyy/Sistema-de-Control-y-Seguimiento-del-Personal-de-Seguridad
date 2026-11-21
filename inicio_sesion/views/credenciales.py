from django.shortcuts import render, redirect
from django.urls import reverse
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from datetime import timedelta
import secrets

from inicio_sesion.models import (
    autenticar_codigo,
    cliente,
    contacto,
    credenciales,
    usuarios,
)
from inicio_sesion.models import propietarios, atencion_cliente, encargados_administrativos, supervisores_encargados

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

import logging

logger = logging.getLogger(__name__)

# MODULO PARA RECUPERAR CREDENCIALES

# GESTIÓN DE EMAIL CÓDGIO

def enviar_codigo(request):
    correo_seleccionado = request.POST.get("correo_seleccionado", "").strip().lower()
    print(correo_seleccionado)

    cedula_identidad = request.session.get("usuario_credenciales")
    print(cedula_identidad)

    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": (
                "No se encontró la cédula de identidad en la sesión."
            )
        })

    if not correo_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Correo electrónico",
            "descripcion": "Debe seleccionar un correo electrónico."
        })

    # Verificar que el correo seleccionado esté registrado
    # para el usuario identificado.
    usuario = usuarios.objects.filter(
        cedula_identidad=cedula_identidad
    ).first()

    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Usuario no encontrado",
            "descripcion": "No se encontró el usuario solicitado."
        })

    contacto_usuario = contacto.objects.filter(
        id_usuario=usuario
    ).first()

    if not contacto_usuario:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Contacto no registrado",
            "descripcion": (
                "El usuario no tiene información de contacto registrada."
            )
        })

    correos_registrados = {
        correo.strip().lower()
        for correo in (
            contacto_usuario.correo_principal,
            contacto_usuario.correo_secundario
        )
        if correo and correo.strip()
    }

    if correo_seleccionado not in correos_registrados:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Correo no válido",
            "descripcion": (
                "El correo seleccionado no coincide con los "
                "datos de contacto registrados."
            )
        })

    request.session["correo_usuario"] = correo_seleccionado

    try:
        ahora = timezone.now()

        # Comprobar si ya existe un código vigente.
        codigo_existente = autenticar_codigo.objects.filter(
            cedula_identidad=cedula_identidad,
            activo=True,
            fecha_expiracion__gt=ahora
        ).exists()

        if codigo_existente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Código ya generado",
                "descripcion": (
                    "Ya existe un código de seguridad vigente."
                )
            })

        # Generar código y token seguros.
        codigo = f"{secrets.randbelow(1_000_000):06d}"
        token = secrets.token_urlsafe(32)

        # Preparar el contenido HTML y texto plano.
        contexto = {
            "codigo_verificacion": codigo
        }

        contenido_html = render_to_string(
            "Email/codigo_verificacion.html",
            contexto
        )

        contenido_texto = (
            "Empresa Hielo Caipe C.A.\n\n"
            "Código de seguridad para verificar tu identidad: "
            f"{codigo}\n\n"
            "Este código vence en 5 minutos. "
            "No lo compartas con otras personas."
        )

        correo = EmailMultiAlternatives(
            subject="Código de seguridad - Hielo Caipe",
            body=contenido_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[correo_seleccionado]
        )

        correo.attach_alternative(contenido_html, "text/html")

        # Guardar el código y enviar el correo.
        # Si falla el envío, se desactiva el código creado.
        with transaction.atomic():
            autenticar_codigo.objects.filter(
                cedula_identidad=cedula_identidad,
                activo=True
            ).update(activo=False)

            registro_codigo = autenticar_codigo.objects.create(
                cedula_identidad=cedula_identidad,
                token=token,
                codigo=codigo,
                intentos=0,
                numero_reenvios=0,
                bloqueado_hasta=None,
                activo=True,
                descripcion="Código de seguridad para autenticación",
                fecha_expiracion=ahora + timedelta(minutes=5)
            )

            try:
                correo.send(fail_silently=False)
            except Exception:
                registro_codigo.activo = False
                registro_codigo.save(update_fields=["activo"])
                raise

        request.session["recuperacion_codigo_enviado"] = True

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Código enviado",
            "descripcion": (
                "El código de seguridad fue enviado al correo "
                "electrónico seleccionado. Tiene una vigencia de 5 minutos."
            ),
            "url": reverse("verificar_codigo")
        })

    except Exception:
        # Registrar el error en el servidor sin exponer detalles
        # de conexión, credenciales SMTP ni información sensible.
        logging.getLogger(__name__).exception(
            "Error al generar o enviar el código de seguridad."
        )

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error al enviar el código",
            "descripcion": (
                "No fue posible enviar el código de seguridad. "
                "Inténtelo nuevamente más tarde."
            )
        })

def reenviar_codigo(request):
    cedula_identidad = request.session.get("usuario_credenciales")

    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": "No se encontró la cédula de identidad en la sesión."
        }, status=401)

    cedula_identidad = str(cedula_identidad).strip()

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Solicitud no válida",
            "descripcion": "El método de solicitud no está permitido."
        }, status=405)

    correo_seleccionado = request.POST.get(
        "correo_seleccionado", ""
    ).strip().lower()

    if not correo_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Correo electrónico",
            "descripcion": "Debe seleccionar un correo electrónico."
        }, status=400)

    try:
        usuario = usuarios.objects.filter(
            cedula_identidad=cedula_identidad
        ).first()

        if not usuario:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Usuario no encontrado",
                "descripcion": "No se encontró el usuario solicitado."
            }, status=404)

        if usuario.credenciales.bloqueado:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Usuario bloqueado",
                "descripcion": "No puede solicitar códigos mientras sus credenciales estén bloqueadas."
            }, status=403)

        contacto_usuario = contacto.objects.filter(
            id_usuario=usuario
        ).first()

        if not contacto_usuario:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Contacto no registrado",
                "descripcion": "El usuario no tiene información de contacto registrada."
            }, status=400)

        correos_registrados = {
            correo.strip().lower()
            for correo in (
                contacto_usuario.correo_principal,
                contacto_usuario.correo_secundario
            )
            if correo and correo.strip()
        }

        if correo_seleccionado not in correos_registrados:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Correo no válido",
                "descripcion": "El correo seleccionado no coincide con los datos de contacto registrados."
            }, status=400)

        ahora = timezone.now()

        with transaction.atomic():
            codigo_existente = (
                autenticar_codigo.objects
                .select_for_update()
                .filter(
                    cedula_identidad=cedula_identidad,
                    activo=True
                )
                .order_by("-creado")
                .first()
            )

            if not codigo_existente:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Código no disponible",
                    "descripcion": "No existe un registro de código activo para reenviar. Solicite un código nuevo."
                }, status=404)

            if (
                codigo_existente.bloqueado_hasta
                and codigo_existente.bloqueado_hasta > ahora
            ):
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Solicitud bloqueada",
                    "descripcion": "Debe esperar antes de solicitar otro código."
                }, status=429)

            if codigo_existente.numero_reenvios >= 3:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Límite alcanzado",
                    "descripcion": "Ha alcanzado el límite de reenvíos permitidos."
                }, status=429)

            nuevo_codigo = f"{secrets.randbelow(1_000_000):06d}"
            nuevo_token = secrets.token_urlsafe(32)
            nueva_expiracion = ahora + timedelta(minutes=5)

            contenido_html = render_to_string(
                "Email/reenviar_codigo.html",
                {
                    "codigo_verificacion": nuevo_codigo
                }
            )

            contenido_texto = (
                "Empresa Hielo Caipe C.A.\n\n"
                "Ha solicitado el reenvío de su código de seguridad.\n\n"
                f"Su nuevo código de verificación es: {nuevo_codigo}\n\n"
                "El código tiene una vigencia de 5 minutos. "
                "No lo comparta con otras personas.\n\n"
                "Si usted no realizó esta solicitud, ignore este mensaje."
            )

            correo = EmailMultiAlternatives(
                subject="Reenvío de código de seguridad - Hielo Caipe",
                body=contenido_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[correo_seleccionado]
            )

            correo.attach_alternative(
                contenido_html,
                "text/html"
            )

            correo_enviado = correo.send(fail_silently=False)

            if correo_enviado != 1:
                raise RuntimeError(
                    "No se pudo confirmar el envío del correo."
                )

            codigo_existente.codigo = nuevo_codigo
            codigo_existente.token = nuevo_token
            codigo_existente.creado = ahora
            codigo_existente.fecha_expiracion = nueva_expiracion
            codigo_existente.numero_reenvios += 1
            codigo_existente.intentos = 0
            codigo_existente.bloqueado_hasta = None

            codigo_existente.save(update_fields=[
                "codigo",
                "token",
                "creado",
                "fecha_expiracion",
                "numero_reenvios",
                "intentos",
                "bloqueado_hasta"
            ])

        request.session["correo_usuario"] = correo_seleccionado
        request.session["recuperacion_codigo_enviado"] = True

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Código reenviado",
            "descripcion": "Se envió un nuevo código de seguridad al correo seleccionado. Tiene una vigencia de 5 minutos.",
            "segundos_restantes": 300,
            "url": reverse("verificar_codigo")
        })

    except Exception:
        logger.exception(
            "Error al reenviar el código de seguridad."
        )

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error al reenviar",
            "descripcion": "No fue posible reenviar el código de seguridad. Inténtelo nuevamente más tarde."
        }, status=500)
    
def vigencia_codigo(request):
    cedula_identidad = request.session.get("usuario_credenciales")

    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "bloqueado": False,
            "descripcion": "No se encontró la cédula de identidad en la sesión."
        }, status=401)

    cedula_identidad = str(cedula_identidad).strip()

    usuario = usuarios.objects.filter(
        cedula_identidad=cedula_identidad
    ).first()

    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "bloqueado": False,
            "descripcion": "No se encontró el usuario registrado."
        })

    if usuario.credenciales.bloqueado:
        return JsonResponse({
            "estado": "fallo",
            "bloqueado": True,
            "bloqueo_permanente": True,
            "descripcion": "Las credenciales del usuario están bloqueadas."
        })

    codigo_existente = autenticar_codigo.objects.filter(
        cedula_identidad=cedula_identidad,
        activo=True
    ).order_by("-creado").first()

    if not codigo_existente:
        return JsonResponse({
            "estado": "fallo",
            "bloqueado": False,
            "descripcion": "No existe un código de seguridad activo."
        }, status=404)

    ahora = timezone.now()
    fecha_desbloqueo = codigo_existente.bloqueado_hasta

    if fecha_desbloqueo and fecha_desbloqueo > ahora:
        segundos_restantes = max(
            1,
            int((fecha_desbloqueo - ahora).total_seconds() + 0.999)
        )

        return JsonResponse({
            "estado": "fallo",
            "bloqueado": True,
            "bloqueo_permanente": False,
            "segundos_restantes": segundos_restantes,
            "descripcion": "El código está inhabilitado. Espere a que finalice el tiempo de bloqueo."
        }, status=429)

    fecha_expiracion = codigo_existente.fecha_expiracion

    if not fecha_expiracion or fecha_expiracion <= ahora:
        return JsonResponse({
            "estado": "fallo",
            "bloqueado": False,
            "descripcion": "El código de seguridad ha expirado. Solicite uno nuevo.",
            "segundos_restantes": 0
        })

    segundos_restantes = max(
        0,
        int((fecha_expiracion - ahora).total_seconds())
    )

    return JsonResponse({
        "estado": "exito",
        "bloqueado": False,
        "segundos_restantes": segundos_restantes,
        "descripcion": "El código de seguridad continúa vigente."
    })

def enviar_usuario(request):
    cedula_identidad = request.session.get("usuario_credenciales")

    correo_seleccionado = request.session.get("correo_usuario", "").strip().lower()

    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": (
                "No se encontró la cédula de identidad en la sesión."
            )
        })

    if not correo_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Correo electrónico no disponible",
            "descripcion": (
                "No se encontró un correo electrónico seleccionado "
                "en la sesión. Vuelva a seleccionar un correo."
            )
        })

    try:
        usuario = usuarios.objects.filter(
            cedula_identidad=cedula_identidad
        ).first()

        if not usuario:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Usuario no encontrado",
                "descripcion": "No se encontró el usuario solicitado."
            })

        contacto_usuario = contacto.objects.filter(
            id_usuario=usuario
        ).first()

        if not contacto_usuario:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Contacto no registrado",
                "descripcion": (
                    "El usuario no tiene información de contacto registrada."
                )
            })

        # Verificar que el correo guardado en la sesión
        # pertenezca al usuario identificado.
        correos_registrados = {
            correo.strip().lower()
            for correo in (
                contacto_usuario.correo_principal,
                contacto_usuario.correo_secundario
            )
            if correo and correo.strip()
        }

        if correo_seleccionado not in correos_registrados:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Correo no válido",
                "descripcion": (
                    "El correo guardado en la sesión no coincide "
                    "con los datos de contacto registrados."
                )
            })

        credencial = credenciales.objects.filter(
            id_usuario=usuario
        ).first()

        if not credencial:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Credenciales no encontradas",
                "descripcion": (
                    "El usuario no tiene credenciales registradas."
                )
            })

        contexto = {
            "nombre_usuario": credencial.nombre_usuario
        }

        contenido_html = render_to_string(
            "Email/recuperar_usuario.html",
            contexto
        )

        contenido_texto = (
            "Empresa Hielo Caipe C.A.\n\n"
            "Ha solicitado recuperar su nombre de usuario.\n\n"
            f"Su nombre de usuario es: {credencial.nombre_usuario}\n\n"
            "Si usted no realizó esta solicitud, ignore este mensaje."
        )

        correo = EmailMultiAlternatives(
            subject="",
            body=contenido_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[correo_seleccionado]
        )

        correo.attach_alternative(
            contenido_html,
            "text/html"
        )

        enviados = correo.send(fail_silently=False)

        if enviados != 1:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Correo no enviado",
                "descripcion": (
                    "No fue posible confirmar el envío del nombre de usuario."
                )
            })
        
        del request.session["usuario_credenciales"]
        del request.session["tipo_usuario_credenciales"]
        del request.session["recuperacion_codigo_verificado"]

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Correo enviado",
            "descripcion": (
                "Se envió el nombre de usuario al correo seleccionado."
            ),
            "url": reverse("recuperar_nombre_usuario")
        })

    except Exception as e:
        logger.exception(
            "Error al enviar el nombre de usuario por correo."
        )

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error al enviar",
            "descripcion": (
                "No fue posible enviar el correo. "
                "Inténtelo nuevamente más tarde. "
                f"Error: {e}"
            )
        })

# MODULO Y VERIFICACIÓN DE CÓDIGO

def buscar_usuario(request):
    if request.method != "POST":
        return render(request, "Credenciales/buscar_usuario.html")

    # Limpiar los datos anteriores de recuperación.
    request.session.pop("usuario_credenciales", None)
    request.session.pop("tipo_usuario_credenciales", None)
    request.session.pop("recuperacion_codigo_verificado", None)
    request.session.pop("recuperacion_codigo_enviado", None)
    request.session.pop("recuperacion_destino", None)

    nacionalidad = request.POST.get("nacionalidad", "").strip().upper()
    num_cedula = request.POST.get("num_cedula", "").strip()

    if not nacionalidad:
        return JsonResponse({
            "estado": "error",
            "title": "Campo vacío",
            "descripcion": "Por favor, debe seleccionar la nacionalidad.",
            "icon": "warning"
        })

    if not num_cedula:
        return JsonResponse({
            "estado": "error",
            "title": "Campo vacío",
            "descripcion": "Por favor, debe ingresar el número de la cédula de identidad.",
            "icon": "warning"
        })

    # Validar el identificador y su longitud.
    longitudes = {
        "V": (7, 8),
        "E": (8, 10),
        "J": (9, 9),
        "G": (9, 9)
    }

    rango = longitudes.get(nacionalidad)

    if rango is None:
        return JsonResponse({
            "estado": "error",
            "title": "Identificador inválido",
            "descripcion": "El tipo de identificación seleccionado no es válido.",
            "icon": "warning"
        })

    if (
        not num_cedula.isdigit()
        or not (rango[0] <= len(num_cedula) <= rango[1])
    ):
        return JsonResponse({
            "estado": "error",
            "title": "Identificador inválido",
            "descripcion": "El número ingresado no cumple con la longitud permitida.",
            "icon": "warning"
        })

    cedula_identidad = f"{nacionalidad}-{num_cedula}"

    # Buscar al usuario por su cédula.
    usuario = usuarios.objects.filter(
        cedula_identidad=cedula_identidad
    ).first()

    if usuario:
        perfil = None

        # Propietario: no posee campo de vigencia.
        if propietarios.objects.filter(
            id_usuario=usuario
        ).exists():
            perfil = "Propietario"

        # Encargado administrativo.
        elif encargados_administrativos.objects.filter(
            id_usuario=usuario,
            vigencia=True
        ).exists():
            perfil = "Encargado Administrativo"

        # Atención al cliente.
        elif atencion_cliente.objects.filter(
            id_usuario=usuario,
            vigencia=True
        ).exists():
            perfil = "Atención al Cliente"

        # Supervisor encargado.
        elif supervisores_encargados.objects.filter(
            id_usuario=usuario,
            vigencia=True
        ).exists():
            perfil = "Supervisor Encargado"

        if perfil:
            # Verificar que el usuario tenga datos de contacto registrados.
            tiene_contacto = contacto.objects.filter(
                id_usuario=usuario
            ).exists()

            if not tiene_contacto:
                return JsonResponse({
                    "estado": "error",
                    "title": "Registro incompleto",
                    "descripcion": (
                        "El usuario está registrado como "
                        f"{perfil}, pero no tiene un registro de contacto. "
                        "Debe completar sus datos de contacto antes "
                        "de recuperar sus credenciales."
                    ),
                    "icon": "warning"
                })

            # Guardar los datos únicamente si cumple las condiciones.
            request.session["usuario_credenciales"] = (
                usuario.cedula_identidad
            )
            request.session["tipo_usuario_credenciales"] = "empleado"

            return JsonResponse({
                "estado": "exito",
                "title": "Usuario encontrado",
                "descripcion": (
                    f"El usuario está registrado como {perfil} "
                    "y cuenta con datos de contacto."
                ),
                "icon": "success"
            })

    # Los clientes también usan las credenciales y el contacto del usuario.
    if usuario and cliente.objects.filter(id_usuario=usuario).exists():
        request.session["usuario_credenciales"] = (
            usuario.cedula_identidad
        )
        request.session["tipo_usuario_credenciales"] = "cliente"

        return JsonResponse({
            "estado": "exito",
            "title": "Cliente encontrado",
            "descripcion": "El cliente se encuentra registrado en el sistema.",
            "icon": "success"
        })

    return JsonResponse({
        "estado": "error",
        "title": "Usuario no encontrado",
        "descripcion": (
            "No se encontró un empleado con un perfil válido "
            "ni un cliente activo con ese identificador."
        ),
        "icon": "error"
    })

def correos_usuario(request):
    cedula_identidad = request.session.get("usuario_credenciales")

    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "notificacion": "No se encontró la cédula de identidad en la sesión.",
            "tipo": "advertencia"
        })

    try:
        usuario = usuarios.objects.get(
            cedula_identidad=cedula_identidad
        )

        datos_contacto = contacto.objects.filter(
            id_usuario=usuario
        ).first()

        if not datos_contacto:
            return JsonResponse({
                "estado": "fallo",
                "notificacion": "El usuario no tiene información de contacto registrada.",
                "tipo": "advertencia"
            })

        return JsonResponse({
            "estado": "exito",
            "notificacion": "Se obtuvieron los correos del usuario correctamente.",
            "tipo": "exito",
            "correo_principal": datos_contacto.correo_principal,
            "correo_secundario": datos_contacto.correo_secundario or ""
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "notificacion": "No existe un usuario registrado con esa cédula.",
            "tipo": "advertencia"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "notificacion": "Ocurrió un error al consultar los correos del usuario.",
            "tipo": "error"
        })

def verificar_codigo(request):
    if request.method != "POST":
        return render(request, "Credenciales/verificar_codigo.html")

    cedula_identidad = request.session.get("usuario_credenciales")
    codigo_ingresado = request.POST.get("codigo_recibido", "").strip()

    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": "No se encontró la cédula de identidad en la sesión."
        }, status=401)

    if not codigo_ingresado:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Campo obligatorio",
            "descripcion": "Debe ingresar el código de seguridad."
        }, status=400)

    try:
        codigo_obj = autenticar_codigo.objects.filter(
            cedula_identidad=str(cedula_identidad).strip(),
            activo=True
        ).order_by("-creado").first()

        if not codigo_obj:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Código no disponible",
                "descripcion": "No existe un código de seguridad activo."
            }, status=404)

        ahora = timezone.now()

        if codigo_obj.bloqueado_hasta and codigo_obj.bloqueado_hasta > ahora:
            segundos_restantes = max(
                1,
                int((codigo_obj.bloqueado_hasta - ahora).total_seconds() + 0.999)
            )

            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Código bloqueado",
                "descripcion": (
                    "Ha alcanzado los 3 intentos fallidos. "
                    "Debe esperar 5 minutos antes de solicitar otro código."
                ),
                "bloqueado": True,
                "bloqueo_permanente": False,
                "segundos_restantes": segundos_restantes
            }, status=429)

        if codigo_obj.bloqueado_hasta:
            codigo_obj.intentos = 0
            codigo_obj.bloqueado_hasta = None
            codigo_obj.save(update_fields=[
                "intentos",
                "bloqueado_hasta"
            ])

        if (
            not codigo_obj.fecha_expiracion
            or codigo_obj.fecha_expiracion <= ahora
        ):
            codigo_obj.activo = False
            codigo_obj.save(update_fields=["activo"])

            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Código expirado",
                "descripcion": "El código de seguridad ha expirado. Solicite uno nuevo."
            }, status=400)

        if codigo_ingresado != codigo_obj.codigo:
            codigo_obj.intentos += 1

            if codigo_obj.intentos >= 3:
                codigo_obj.bloqueado_hasta = ahora + timedelta(minutes=5)

            codigo_obj.save(update_fields=[
                "intentos",
                "bloqueado_hasta"
            ])

            if codigo_obj.intentos >= 3:
                segundos_restantes = max(
                    1,
                    int((codigo_obj.bloqueado_hasta - ahora).total_seconds() + 0.999)
                )

                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Código bloqueado",
                    "descripcion": (
                        "Ha alcanzado los 3 intentos fallidos. "
                        "Su código está bloqueado durante 5 minutos. "
                        "Espere a que finalice el tiempo para solicitar otro."
                    ),
                    "bloqueado": True,
                    "bloqueo_permanente": False,
                    "segundos_restantes": segundos_restantes
                }, status=429)

            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Código incorrecto",
                "descripcion": (
                    f"El código ingresado es incorrecto. "
                    f"Intentos restantes: {3 - codigo_obj.intentos}."
                ),
                "intentos_restantes": 3 - codigo_obj.intentos
            }, status=400)

        codigo_obj.activo = False
        codigo_obj.save(update_fields=["activo"])

        request.session["recuperacion_codigo_verificado"] = True

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Código verificado",
            "descripcion": "El código de seguridad se verificó correctamente.",
            "url": reverse("menu_recuperar_credenciales")
        })

    except Exception:
        logger.exception("Error al verificar el código de seguridad.")

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": "No fue posible verificar el código de seguridad."
        }, status=500)

def menu_recuperar_credenciales(request):
    if not request.session.get("recuperacion_codigo_verificado"):
        return redirect("verificar_codigo")

    return render(request, "Credenciales/menu_recuperar_credenciales.html")

def cambiar_contrasenia(request):
    if not request.session.get("recuperacion_codigo_verificado"):
        if request.method == "POST":
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Verificación requerida",
                "descripcion": (
                    "Debe verificar el código de seguridad antes de "
                    "cambiar la contraseña."
                )
            })
        return redirect("verificar_codigo")

    if request.method != "POST":
        return render(request, "Credenciales/cambiar_contrasenia.html")

    contrasenia = request.POST.get("contrasenia")
    cedula_identidad = request.session.get("usuario_credenciales")
    contrasenia_confirmar = request.POST.get("contrasenia_confirmar")

    if contrasenia != contrasenia_confirmar:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Contraseñas diferentes",
            "descripcion": "Las contraseñas ingresadas no coinciden."
        })

    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": (
                "No se encontró la cédula de identidad en la sesión. "
                "Vuelva a iniciar el proceso de recuperación."
            )
        })

    if not contrasenia:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Contraseña",
            "descripcion": (
                "El campo está vacío. Por favor, ingrese una contraseña."
            )
        })

    if not contrasenia or any(caracter.isspace() for caracter in contrasenia):
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Contraseña no válida",
            "descripcion": "La contraseña no puede contener espacios en blanco."
        })

    try:
        with transaction.atomic():
            usuario = usuarios.objects.get(
                cedula_identidad=cedula_identidad
            )

            credencial = credenciales.objects.get(
                id_usuario=usuario
            )

            credencial.clave = make_password(contrasenia)
            credencial.save(update_fields=["clave"])

        del request.session["usuario_credenciales"]
        del request.session["tipo_usuario_credenciales"]
        del request.session["recuperacion_codigo_verificado"]

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Éxito",
            "descripcion": "Contraseña actualizada exitosamente.",
            "url": reverse("inicio_sesion")
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Usuario no encontrado",
            "descripcion": (
                "No se encontró un usuario asociado a la solicitud."
            )
        })

    except credenciales.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Credenciales no encontradas",
            "descripcion": (
                "El usuario no tiene credenciales registradas."
            )
        })
    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error del servidor",
            "descripcion": (
                "Ocurrió un error al actualizar la contraseña. "
                "Inténtelo nuevamente."
            )
        })

def recuperar_nombre_usuario(request):       
    return render(request, "Credenciales/recuperar_usuario.html")