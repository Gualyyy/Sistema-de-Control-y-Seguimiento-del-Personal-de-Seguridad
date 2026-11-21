from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
from math import ceil

import re
import unicodedata

from inicio_sesion.models import usuarios, contacto, atencion_cliente, propietarios, encargados_administrativos, supervisores_encargados, credenciales, nacimiento, sesiones_usuario, intentos_inicio_sesion, bloqueo_inicio_sesion, cliente

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

def obtener_rol(usuario):

    if propietarios.objects.filter(
        id_usuario=usuario
    ).exists():
        return {
            "rol": "Propietario"
        }

    if encargados_administrativos.objects.filter(
        id_usuario=usuario,
        vigencia=True
    ).exists():
        return {
            "rol": "Encargado Administrativo"
        }

    if atencion_cliente.objects.filter(
        id_usuario=usuario,
        vigencia=True
    ).exists():
        return {
            "rol": "Atención al Cliente"
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

    if cliente.objects.filter(
        id_usuario=usuario
    ).exists():
        return {
            "rol": "Cliente"
        }

    return None

def inicio_sesion(request):
    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario", "").strip()
        contrasenia = request.POST.get("contrasenia", "")
        tab_id = request.POST.get("tab_id", "").strip()

        direccion_ip = request.META.get("REMOTE_ADDR")

        if not nombre_usuario:
            return JsonResponse({
                "estado": "fallo",
                "title": "Campo vacío",
                "descripcion": "Por favor, ingrese su nombre de usuario.",
                "icon": "warning"
            })

        if not contrasenia:
            return JsonResponse({
                "estado": "fallo",
                "title": "Campo vacío",
                "descripcion": "Por favor, ingrese su contraseña.",
                "icon": "warning"
            })

        if not tab_id:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error de sesión",
                "descripcion": (
                    "No se pudo identificar la pestaña actual. "
                    "Recargue la página e intente nuevamente."
                ),
                "icon": "warning"
            })

        try:
            credencial = credenciales.objects.select_related(
                "id_usuario"
            ).get(nombre_usuario=nombre_usuario)

            usuario = credencial.id_usuario

        except credenciales.DoesNotExist:
            intentos_inicio_sesion.objects.create(
                usuario=None,
                nombre_usuario=nombre_usuario,
                direccion_ip=direccion_ip,
                exitoso=False,
            )

            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario no encontrado",
                "descripcion": "El usuario no se encuentra registrado.",
                "icon": "error"
            })

        bloqueo, creado = bloqueo_inicio_sesion.objects.get_or_create(
            usuario=usuario
        )

        ahora = timezone.now()

        if bloqueo.bloqueado and bloqueo.bloqueado_hasta:
            if bloqueo.bloqueado_hasta > ahora:
                tiempo_restante = bloqueo.bloqueado_hasta - ahora
                minutos = ceil(tiempo_restante.total_seconds() / 60)

                return JsonResponse({
                    "estado": "bloqueado",
                    "title": "Cuenta bloqueada",
                    "descripcion": (
                        "Se ha superado el número máximo de intentos para esta cuenta. "
                        f"Debe esperar {minutos} minuto(s) para volver a intentarlo."
                    ),
                    "icon": "warning"
                })

            bloqueo.bloqueado = False
            bloqueo.intentos = 0
            bloqueo.bloqueado_hasta = None
            bloqueo.save(update_fields=[
                "bloqueado",
                "intentos",
                "bloqueado_hasta",
                "ultimo_intento",
            ])

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
                    "La cuenta ingresada se encuentra bloqueada. "
                    "Comuníquese con el administrador."
                ),
                "icon": "warning"
            })

        resultado = check_password(
            contrasenia,
            credencial.clave
        )

        if not resultado:
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
                bloqueo.bloqueado_hasta = (
                    timezone.now() + timedelta(minutes=5)
                )

            bloqueo.save()

            intentos_restantes = max(
                0,
                LIMITE_INTENTOS - bloqueo.intentos
            )

            if bloqueo.bloqueado:
                descripcion = (
                    "Ha superado el número máximo de intentos para esta cuenta. "
                    "El acceso ha sido bloqueado durante 5 minutos."
                )
            else:
                descripcion = (
                    "La contraseña es incorrecta. "
                    f"Le quedan {intentos_restantes} intento(s)."
                )

            return JsonResponse({
                "estado": "bloqueado" if bloqueo.bloqueado else "fallo",
                "title": "Error de autenticación",
                "descripcion": descripcion,
                "icon": "warning" if bloqueo.bloqueado else "error"
            })

        # Verificar que el usuario tenga un perfil vigente
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
                "descripcion": (
                    "El usuario no tiene un perfil vigente "
                    "para acceder al sistema."
                ),
                "icon": "warning"
            })

        # Verificar sesiones activas
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

        sesiones_expiradas.update(
            activa=False,
            fecha_fin=ahora
        )

        if sesiones_vigentes.exists():
            intentos_inicio_sesion.objects.create(
                usuario=usuario,
                nombre_usuario=nombre_usuario,
                direccion_ip=direccion_ip,
                exitoso=False,
            )

            return JsonResponse({
                "estado": "sesion_activa",
                "title": "Sesión ya iniciada",
                "descripcion": (
                    "Este usuario ya tiene una sesión activa en otro "
                    "navegador o pestaña. Cierre sesión desde allí o, "
                    "si ya cerró el navegador con Alt+F4, espere "
                    "hasta 2 minutos para volver a intentarlo."
                ),
                "icon": "warning"
            })

        # Registrar inicio de sesión exitoso
        intentos_inicio_sesion.objects.create(
            usuario=usuario,
            nombre_usuario=nombre_usuario,
            direccion_ip=direccion_ip,
            exitoso=True,
        )

        # Restablecer los intentos de la IP al iniciar sesión correctamente
        bloqueo.intentos = 0
        bloqueo.bloqueado = False
        bloqueo.bloqueado_hasta = None
        bloqueo.ultima_direccion_ip = direccion_ip
        bloqueo.save()

        # Variables de sesión
        request.session["usuario"] = (
            f"{usuario.nombres} {usuario.apellidos}"
        )

        request.session["perfil"] = perfil["rol"]
        request.session["turno"] = perfil.get("turno")

        request.session["panel_token"] = TimestampSigner(
            salt="panel-route"
        ).sign("panel")

        request.session["cedula_identidad"] = (
            usuario.cedula_identidad
        )

        # Validar si debe completar el registro
        if perfil["rol"] == "Cliente":
            completar_registro = True
        else:
            registro_nacimiento = nacimiento.objects.filter(
                id_usuario=usuario
            ).first()

            completar_registro = (
                registro_nacimiento is not None
                and all(
                    valor is not None
                    and str(valor).strip().upper() != "N/A"
                    for campo, valor in registro_nacimiento.__dict__.items()
                    if campo not in (
                        "_state",
                        "id",
                        "id_nacimiento",
                        "id_usuario_id"
                    )
                )
            )

        request.session["completar_registro"] = completar_registro

        request.session.save()

        # Registrar sesión del usuario
        sesiones_usuario.objects.update_or_create(
            session_key=request.session.session_key,
            defaults={
                "usuario": usuario,
                "tab_id": tab_id,
                "activa": True,
                "fecha_fin": None,
                "info_general": request.META.get(
                    "HTTP_USER_AGENT",
                    ""
                ),
                "direccion_ip": direccion_ip,
            },
        )

        if not completar_registro:
            return JsonResponse({
                "estado": "incompleto",
                "url": reverse("completar_registro")
            })

        return JsonResponse({
            "estado": "exito",
            "url": reverse("panel_usuario")
        })

    if request.session.get("usuario"):
        return redirect("panel_usuario")

    return render(request, "inicio_sesion/autenticacion.html")

# MODULOS PARA REGISTRAR LAS CREDENCIALES

# BUSCAR LOS EMPLEADO QUE NO TIENE CREDENCIALES REGISTRADO

def empleado_sin_credenciales(request):
    nacionalidad = request.POST.get("nacionalidad", "").strip().upper()
    num_cedula = request.POST.get("num_cedula", "").strip()

    if not nacionalidad:
        return JsonResponse({
            "title": "Campo vacío",
            "descripcion": "Por favor, debe seleccionar la nacionalidad.",
            "icon": "warning"
        })

    if not num_cedula:
        return JsonResponse({
            "title": "Campo vacío",
            "descripcion": "Por favor, debe ingresar los números de la cédula de identidad.",
            "icon": "warning"
        })

    cedula_identidad = f"{nacionalidad}-{num_cedula}"

    try:
        empleado = usuarios.objects.get(cedula_identidad=cedula_identidad)
    except usuarios.DoesNotExist:
        return JsonResponse({
            "title": "Empleado no encontrado",
            "descripcion": "El empleado no se encuentra registrado.",
            "icon": "error"
        })

    perfiles = (
        encargados_administrativos.objects.filter(
            id_usuario=empleado,
            vigencia=True
        ).exists()
        or propietarios.objects.filter(
            id_usuario=empleado
        ).exists()
        or atencion_cliente.objects.filter(
            id_usuario=empleado,
            vigencia=True
        ).exists()
        or supervisores_encargados.objects.filter(
            id_usuario=empleado,
            vigencia=True
        ).exists()
    )

    if not perfiles:
        return JsonResponse({
            "title": "Perfil no autorizado",
            "descripcion": "El empleado no posee un perfil autorizado para registrar credenciales.",
            "icon": "warning"
        })

    if credenciales.objects.filter(id_usuario=empleado).exists():
        return JsonResponse({
            "title": "Credenciales existentes",
            "descripcion": "Este empleado ya tiene credenciales registradas.",
            "icon": "warning"
        })

    return JsonResponse({
        "title": "Empleado encontrado",
        "descripcion": (
            "El empleado está registrado, posee un perfil autorizado "
            "y no tiene credenciales. Puede continuar con el registro."
        ),
        "icon": "success",
        "estado": True,
        "id_usuario": empleado.id_usuario
    })

# INDICADORES DE CONTRASEÑA PARA ASEGURAR QUE NO SEA DEBIL

def normalizar_texto(valor):
    valor = unicodedata.normalize("NFD", str(valor or "").lower())
    valor = "".join(
        caracter for caracter in valor
        if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"[^a-z0-9]", "", valor)

def obtener_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))

def contiene_dato_personal(clave, dato, longitud_minima=3):
    dato_normalizado = normalizar_texto(dato)
    clave_normalizada = normalizar_texto(clave)

    return (
        len(dato_normalizado) >= longitud_minima
        and dato_normalizado in clave_normalizada
    )

def contiene_numero_personal(clave, dato, longitud_minima=6):
    clave_digitos = obtener_digitos(clave)
    dato_digitos = obtener_digitos(dato)

    return (
        len(dato_digitos) >= longitud_minima
        and dato_digitos in clave_digitos
    )

def contiene_fecha_nacimiento(clave, fecha):
    clave_digitos = obtener_digitos(clave)
    fecha_digitos = obtener_digitos(fecha)

    if len(fecha_digitos) < 6:
        return False

    variantes = {fecha_digitos}

    # Para fechas de ocho dígitos, considera también
    # partes habituales de la fecha.
    if len(fecha_digitos) == 8:
        variantes.update({
            fecha_digitos[:4],
            fecha_digitos[4:],
            fecha_digitos[2:]
        })

    return any(
        len(variante) >= 6 and variante in clave_digitos
        for variante in variantes
    )

def validar_patron_contrasenia(request):
    clave = request.POST.get("clave", "")

    if not clave:
        return JsonResponse({
            "estado": "fallo",
            "title": "Campo vacío",
            "descripcion": "Debe ingresar una contraseña.",
            "icon": "warning"
        }, status=400)

    # Nombres y apellidos de todos los usuarios.
    usuarios_registrados = usuarios.objects.values_list(
        "nombres", "apellidos"
    )

    nombres = []
    apellidos = []

    for nombre, apellido in usuarios_registrados:
        nombres.extend((nombre or "").split())
        apellidos.extend((apellido or "").split())

    # Cédulas de todos los usuarios.
    cedulas = usuarios.objects.values_list(
        "cedula_identidad", flat=True
    )

    # Teléfonos principales y secundarios de todos los contactos.
    telefonos = contacto.objects.values_list(
        "telefono_principal", "telefono_secundario"
    )

    lista_telefonos = []

    for principal, secundario in telefonos:
        if principal:
            lista_telefonos.append(principal)

        if secundario:
            lista_telefonos.append(secundario)

    # Fechas de nacimiento de todos los usuarios que tengan registro.
    fechas_nacimiento = nacimiento.objects.values_list(
        "fecha_nacimiento", flat=True
    )

    reglas = {
        "longitud": 8 <= len(clave) <= 15,

        "alfabetico": bool(
            re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", clave)
        ),

        "especial": bool(
            re.search(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s]", clave)
        ),

        "numero": bool(re.search(r"\d", clave)),

        "repetidos": not bool(re.search(r"(.)\1\1", clave)),

        "nombre": not any(
            contiene_dato_personal(clave, nombre)
            for nombre in nombres
        ),

        "apellido": not any(
            contiene_dato_personal(clave, apellido)
            for apellido in apellidos
        ),

        "cedula": not any(
            contiene_numero_personal(clave, cedula)
            for cedula in cedulas
        ),

        "telefono": not any(
            contiene_numero_personal(clave, telefono)
            for telefono in lista_telefonos
        ),

        "nacimiento": not any(
            contiene_fecha_nacimiento(clave, fecha)
            for fecha in fechas_nacimiento
        )
    }

    return JsonResponse({
        "estado": "exito",
        "validaciones": reglas,
        "valida": all(reglas.values())
    })

# REGISTRAR LAS CREDENCIALES EN LA BASE DE DATOS

def registrar_credenciales(request):
    if request.method != "POST":
        return render(request, "inicio_sesion/registrar_credenciales.html")

    id_usuario = request.POST.get("id_usuario", "").strip()
    nombre_usuario = request.POST.get("nombre_usuario", "")
    contrasenia = request.POST.get("contrasenia", "")

    # Validar nombre de usuario vacío
    nombre_usuario = nombre_usuario.strip()

    if not nombre_usuario:
        return JsonResponse({
            "estado": "vacio",
            "title": "Nombre de usuario vacío",
            "descripcion": "Por favor, ingrese el nombre de usuario.",
            "icon": "warning"
        })

    # Impedir espacios dentro del nombre de usuario
    if any(caracter.isspace() for caracter in nombre_usuario):
        return JsonResponse({
            "estado": "error",
            "title": "Nombre de usuario inválido",
            "descripcion": "El nombre de usuario no debe contener espacios en blanco.",
            "icon": "warning"
        })

    # Validar contraseña vacía
    if not contrasenia.strip():
        return JsonResponse({
            "estado": "vacio",
            "title": "Contraseña vacía",
            "descripcion": "Por favor, ingrese la contraseña.",
            "icon": "warning"
        })

    try:
        with transaction.atomic():
            usuario = usuarios.objects.get(id_usuario=id_usuario)

            # Evitar nombres de usuario duplicados
            if credenciales.objects.filter(
                nombre_usuario__iexact=nombre_usuario
            ).exists():
                return JsonResponse({
                    "estado": "error",
                    "title": "Nombre de usuario registrado",
                    "descripcion": "Este nombre de usuario ya está registrado. Ingrese otro.",
                    "icon": "warning"
                })

            credenciales.objects.create(
                nombre_usuario=nombre_usuario,
                clave=make_password(contrasenia),
                id_usuario=usuario
            )

            return JsonResponse({
                "estado": "exito",
                "title": "Registro exitoso",
                "descripcion": "Se registraron exitosamente las credenciales.",
                "icon": "success"
            })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "error",
            "title": "Empleado no encontrado",
            "descripcion": "No se encuentra registrado el empleado.",
            "icon": "error"
        })

    except Exception:
        return JsonResponse({
            "estado": "error",
            "title": "Error del servidor",
            "descripcion": "Ocurrió un error al registrar las credenciales. Intente nuevamente.",
            "icon": "error"
        })

def menu_acceso(request):
    return render(request, "inicio_sesion/menu_acceso.html")