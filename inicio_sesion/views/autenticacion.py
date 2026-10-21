from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
from math import ceil

from inicio_sesion.models import directiva_nacional, encargados_administrativos, supervisores_encargados, credenciales, nacimiento, sesiones_usuario, intentos_inicio_sesion, bloqueo_inicio_sesion

DURACION_SENAL_SESION = timedelta(minutes=2)

def crear_token_panel():
    signer = TimestampSigner(salt="panel-route")
    return signer.sign("panel")

def validar_token_panel(token):
    signer = TimestampSigner(salt="panel-route")

    try:
        return signer.unsign(token, max_age=24 * 60 * 60) == "panel"
    except (BadSignature, SignatureExpired):
        return False

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

def modo_incognito(request):
    return render(request, "inicio_sesion/incognito.html")

def obtener_rol(usuario):

    if directiva_nacional.objects.filter(
        id_usuario=usuario
    ).exists():
        return {
            "rol": "Directiva Nacional"
        }

    if encargados_administrativos.objects.filter(
        id_usuario=usuario,
        vigencia=True
    ).exists():
        return {
            "rol": "Encargado Administrativo"
        }

    supervisor = supervisores_encargados.objects.filter(
        id_usuario=usuario,
        vigencia=True
    ).select_related("id_turno").first()

    if supervisor:
        return {
            "rol": "Supervisor Encargado",
            "turno": supervisor.id_turno.nombre
        }

    return None

def inicio_sesion(request):
    if request.method == "POST":
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
            intentos_inicio_sesion.objects.create(
                usuario=None,
                nombre_usuario=nombre_usuario,
                direccion_ip=direccion_ip,
                exitoso=False,
            )

            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "empleado no se encuentra registrado.",
                "icon": "error"
            })

        if credencial.bloqueado:
            intentos_inicio_sesion.objects.create(
                usuario=usuario,
                nombre_usuario=nombre_usuario,
                direccion_ip=direccion_ip,
                exitoso=False,
            )

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
        perfil = obtener_rol(usuario)

        if not perfil:
            intentos_inicio_sesion.objects.create(
                usuario=usuario,
                nombre_usuario=nombre_usuario,
                direccion_ip=direccion_ip,
                exitoso=False,
            )

            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario sin perfil",
                "descripcion": "El usuario no tiene un perfil vigente para acceder al sistema.",
                "icon": "warning"
            })
        
        request.session["perfil"] = perfil["rol"]
        request.session["turno"] = perfil.get("turno")
        
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
            ahora = timezone.now()
            sesiones_vigentes = sesiones_usuario.objects.filter(
                usuario=usuario,
                activa=True,
                ultima_actividad__gte=ahora - DURACION_SENAL_SESION,
                session_key__in=Session.objects.filter(
                    expire_date__gt=ahora
                ).values("session_key"),
            )
            if request.session.session_key:
                sesiones_vigentes = sesiones_vigentes.exclude(
                    session_key=request.session.session_key
                )
            sesiones_expiradas = sesiones_usuario.objects.filter(
                usuario=usuario,
                activa=True,
            ).exclude(
                session_key__in=sesiones_vigentes.values("session_key")
            )
            sesiones_expiradas.update(activa=False, fecha_fin=ahora)

            if sesiones_vigentes.exists():
                return JsonResponse({
                    "estado": "sesion_activa",
                    "title": "Sesión ya iniciada",
                    "descripcion": (
                        "Este usuario ya tiene una sesión activa en otro navegador "
                        "o pestaña. Cierre sesión desde allí o, si ya cerró el "
                        "navegador con Alt+F4, espere hasta 2 minutos para "
                        "volver a intentarlo."
                    ),
                    "icon": "warning",
                })

            # Registrar inicio de sesión
            intentos_inicio_sesion.objects.create(
                usuario=usuario,
                nombre_usuario=nombre_usuario,
                direccion_ip=direccion_ip,
                exitoso=True,
            )

            bloqueo.intentos = 0
            bloqueo.bloqueado = False
            bloqueo.bloqueado_hasta = None
            bloqueo.ultima_direccion_ip = direccion_ip
            bloqueo.save()

            # Variables de sesión
            request.session["usuario"] = (f"{usuario.nombres} {usuario.apellidos}")

            request.session["panel_token"] = TimestampSigner(
                salt="panel-route"
            ).sign("panel")

            # Cédula
            request.session["cedula_identidad"] = (usuario.cedula_identidad)

            # Verificar registro de nacimiento
            resultado = nacimiento.objects.filter(id_usuario=usuario).exists()

            request.session["completar_registro"] = resultado

            request.session.save()
            sesiones_usuario.objects.update_or_create(
                session_key=request.session.session_key,
                defaults={
                    "usuario": usuario,
                    "tab_id": tab_id,
                    "activa": True,
                    "fecha_fin": None,
                    "info_general": request.META.get("HTTP_USER_AGENT", ""),
                    "direccion_ip": direccion_ip,
                },
            )

            # Registro incompleto
            if not resultado:
                return JsonResponse({
                    "estado": "incompleto",
                    "title": "Registro incompleto",
                    "descripcion": "Debe completar sus datos de nacimiento.",
                    "icon": "warning",
                    "url": reverse("completar_registro")
                })

            return JsonResponse({
                "estado": "exito",
                "url": reverse("panel_usuario")
            })
        else:
            intentos_inicio_sesion.objects.create(
                usuario=usuario,
                nombre_usuario=nombre_usuario,
                direccion_ip=direccion_ip,
                exitoso=False,
            )

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

    if request.session.get("usuario"):
        return redirect("panel_usuario")

    return render(request, "inicio_sesion/autenticacion.html")
