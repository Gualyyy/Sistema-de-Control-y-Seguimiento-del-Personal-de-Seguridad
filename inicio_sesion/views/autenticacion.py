from functools import wraps
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.sessions.models import Session
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from datetime import timedelta
from math import ceil
from django.db import IntegrityError

from inicio_sesion.models import usuarios, credenciales, nacimiento, perfil_usuario, sesiones_usuario, intentos_inicio_sesion, bloqueo_inicio_sesion

def autenticado_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view

def registrar_intento(usuario, nombre_usuario, ip, exitoso):
    intentos_inicio_sesion.objects.create(usuario=usuario, nombre_usuario=nombre_usuario, direccion_ip=ip, exitoso=exitoso)

def invalidar_sesiones_anteriores(usuario, session_key_actual):
    sesiones_anteriores = sesiones_usuario.objects.filter(
        usuario=usuario,
        activa=True,
    ).exclude(session_key=session_key_actual)
    claves_sesion = list(sesiones_anteriores.values_list("session_key", flat=True))

    sesiones_anteriores.update(
        activa=False,
        fecha_fin=timezone.now(),
    )
    Session.objects.filter(session_key__in=claves_sesion).delete()

def registrar_sesion_usuario(request, usuario, direccion_ip, tab_id):
    session_key = request.session.session_key

    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    return sesiones_usuario.objects.create(
        usuario=usuario,
        session_key=session_key,
        tab_id=tab_id,
        activa=True,
        info_general=request.META.get(
            "HTTP_USER_AGENT",
            ""
        ),
        direccion_ip=direccion_ip
    )

def crear_token_panel():
    signer = TimestampSigner(salt="panel-route")
    return signer.sign("panel")

def validar_token_panel(token):
    signer = TimestampSigner(salt="panel-route")

    try:
        return signer.unsign(token, max_age=24 * 60 * 60) == "panel"
    except (BadSignature, SignatureExpired):
        return False

def inicio_sesion(request):
    if request.method == "POST":
        if request.session.get("usuario"):
            return JsonResponse({
                "estado": "fallo",
                "title": "Sesión ya iniciada",
                "descripcion": "Este navegador ya tiene una sesión activa para un usuario.",
                "icon": "warning"
            })

        nombre_usuario = request.POST.get("nombre_usuario")
        contrasenia = request.POST.get("contrasenia")
        tab_id = request.POST.get("tab_id")
        direccion_ip = request.META.get("REMOTE_ADDR")

        # Validar campos vacíos
        if not nombre_usuario:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacio",
                "descripcion": "Por favor, ingrese su nombre de usuario.",
                "icon": "warning"
            })

        if not contrasenia:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacio",
                "descripcion": "Por favor, ingrese su contraseña.",
                "icon": "warning"
            })

        if not tab_id:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error de sesión",
                "descripcion": "No se pudo identificar la pestaña actual. Recargue la página e intente nuevamente.",
                "icon": "warning"
            })

        # Verificar que las credenciales existen
        try:
            credencial = credenciales.objects.select_related("id_usuario").get(nombre_usuario=nombre_usuario)

            usuario = credencial.id_usuario

            # Verificar bloqueo
            bloqueo, creado = bloqueo_inicio_sesion.objects.get_or_create(usuario=usuario)
        except credenciales.DoesNotExist:
            registrar_intento(None, nombre_usuario, direccion_ip, False)

            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "empleado no se encuentra registrado.",
                "icon": "error"
            })

        if not credencial.bloqueado:
            registrar_intento(usuario, nombre_usuario, direccion_ip, False)

            return JsonResponse({
                "estado": "bloqueado",
                "title": "Cuenta bloqueada",
                "descripcion": (
                    "Su cuenta se encuentra bloqueada. "
                    "Comuníquese con el administrador."
                ),
                "icon": "warning"
            })

        # Verificar que el usuario cuenta con al menos un perfil activo
        perfiles_usuario = perfil_usuario.objects.filter(
            id_usuario=usuario,
            vigencia=True
        ).select_related("id_perfil")
        if not perfiles_usuario.exists():
            registrar_intento(usuario, nombre_usuario, direccion_ip, False)

            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario inhabilitado",
                "descripcion": "El empleado no cuenta con un perfil vigente para iniciar sesión.",
                "icon": "warning"
            })

        # Verificar si está bloqueado
        if bloqueo.bloqueado and bloqueo.bloqueado_hasta > timezone.now():
            tiempo_restante = (bloqueo.bloqueado_hasta - timezone.now())
            minutos = ceil(tiempo_restante.total_seconds() / 60)

            return JsonResponse({
                "estado": "bloqueado",
                "title": "Cuenta bloqueada",
                "descripcion": (
                    f"Ha superado el número máximo de intentos. "
                    f"Debe esperar {minutos} minuto(s) para volver a intentarlo."
                ),
                "icon": "warning"
            })

        # Desbloquear si ya expiró el tiempo
        if bloqueo.bloqueado and bloqueo.bloqueado_hasta <= timezone.now():

            bloqueo.bloqueado = False
            bloqueo.intentos = 0
            bloqueo.bloqueado_hasta = None
            bloqueo.save()

        # Validar contraseña
        resultado = check_password(contrasenia, credencial.clave)

        if resultado:
            # Registrar inicio de sesión
            registrar_intento(usuario, nombre_usuario, direccion_ip, resultado)

            bloqueo.intentos = 0
            bloqueo.bloqueado = False
            bloqueo.bloqueado_hasta = None
            bloqueo.ultima_direccion_ip = direccion_ip
            bloqueo.save()

            invalidar_sesiones_anteriores(usuario, request.session.session_key)

            # Variables de sesión
            request.session["usuario"] = (f"{usuario.nombres} {usuario.apellidos}")

            request.session["panel_token"] = crear_token_panel()

            # Perfiles activos
            request.session["perfiles"] = list(
                perfiles_usuario.values_list(
                    "id_perfil__perfil",
                    flat=True
                )
            )

            request.session["id_perfiles_usuario"] = list(
                perfiles_usuario.values_list(
                    "id_perfil_usuario",
                    flat=True
                )
            )

            # Cédula
            request.session["cedula_identidad"] = (usuario.cedula_identidad)

            # Verificar registro de nacimiento
            resultado = nacimiento.objects.filter(id_usuario=usuario).exists()

            request.session["completar_registro"] = resultado

            request.session.save()

            # Registro incompleto
            if not resultado:
                registrar_sesion_usuario(
                    request,
                    usuario,
                    direccion_ip,
                    tab_id
                )

                return JsonResponse({
                    "estado": "incompleto",
                    "title": "Registro incompleto",
                    "descripcion": "Debe completar sus datos de nacimiento.",
                    "icon": "warning",
                    "url": reverse("completar_registro")
                })

            # Registrar sesión
            registrar_sesion_usuario(
                request,
                usuario,
                direccion_ip,
                tab_id
            )

            return JsonResponse({
                "estado": "exito",
                "url": reverse("panel_usuario")
            })
        else:
            registrar_intento(usuario, nombre_usuario, direccion_ip, resultado)

            LIMITE_INTENTOS = 3

            bloqueo.intentos += 1
            bloqueo.ultima_direccion_ip = direccion_ip

            if bloqueo.intentos >= LIMITE_INTENTOS:
                bloqueo.bloqueado = True
                bloqueo.bloqueado_hasta = (timezone.now() + timedelta(minutes=5))
            bloqueo.save()
            intentos_restantes = max(0, LIMITE_INTENTOS - bloqueo.intentos)

            if bloqueo.bloqueado:
                descripcion = (
                    "Ha superado el número máximo de intentos. "
                    "Su cuenta ha sido bloqueada durante 5 minutos."
                )
            else:
                descripcion = (
                    f"La contraseña es incorrecta. "
                    f"Le quedan {intentos_restantes} intento(s)."
                )

            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": descripcion,
                "icon": "error"
            })

    return render(request, "inicio_sesion/autenticacion.html")

def cerrar_sesion(request):
    session_key = request.session.session_key
    sesion = sesiones_usuario.objects.filter(session_key=session_key, activa=True).first()

    if sesion:
        sesion.fecha_fin = timezone.now()
        sesion.activa = False
        sesion.save()

    for key in list(request.session.keys()):
        del request.session[key]

    request.session.flush()
    return redirect("inicio_sesion")

