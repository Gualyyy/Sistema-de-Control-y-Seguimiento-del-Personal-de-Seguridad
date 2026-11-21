from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse

from inicio_sesion.models import usuarios, credenciales, contacto, nacimiento, residencia, bitacora, credenciales
from inicio_sesion.models import encargados_administrativos

# GESTIÓN DE ENCARGADO ADMINISTRATIVO POR PARTE DEL PROPIETARIO

def existe_administrador(request):
    existe = encargados_administrativos.objects.filter(vigencia=True).exists()

    return JsonResponse({
        "existe": existe
    })

def registrar_administrador(request):
    if request.method != "POST":
        return render(request, "Modulos/Empleados/Propietario/registrar_administrador.html")

    nombres = request.POST.get("nombres")
    apellidos = request.POST.get("apellidos")
    nacionalidad = request.POST.get("nacionalidad")
    num_cedula = request.POST.get("cedula_identidad")
    
    prefijo_principal = request.POST.get("prefijo_principal")
    numero_principal = request.POST.get("numero_principal")

    prefijo_secundaria = request.POST.get("prefijo_secundaria", "").strip()
    numero_secundaria = request.POST.get("numero_secundaria", "").strip()
    
    correo_principal = request.POST.get("correo_principal", "").strip()
    dominio_principal = request.POST.get("dominio_principal", "").strip()
    
    correo_secundaria = request.POST.get("correo_secundaria", "").strip()
    dominio_secundaria = request.POST.get("dominio_secundaria", "").strip()

    campos = [
        (nombres, "Nombres", "Por favor, debe de ingresar el/los nombre(s)."),
        (apellidos, "Apellidos", "Por favor, debe de ingresar el/los nombre(s)."),
        (nacionalidad, "Nacionalidad", "Por favor, debe seleccionar la nacionalidad."),
        (num_cedula, "Número de la Cedula de Identidad", "Por favor, debe ingresar los número de la cedula de identidad."),
        
        (prefijo_principal, "Prefijo Telefonico (Principal)", "Por favor, debe seleccionar el prefijo telefonico."),
        (numero_principal, "Número Telefonico (Principal)", "Por favor,  debe ingresar los números telefonicos."),
        
        (correo_principal, "Nombre del Correo (Principal)", "Por favor, debe ingresar el nombre o identificador del correo electrónico."),
        (dominio_principal, "Dominio del Correo (Principal)", "Por favor, debe seleccionar el dominio del correo electrónico."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if request.POST.get("genero"):
        genero = request.POST.get("genero")
    else:
        genero = "N/A"

    if request.POST.get("estado_civil"):
        estado_civil = request.POST.get("estado_civil")
    else:
        estado_civil = "N/A"

    nombre_razon_social = nombres + " " + apellidos
    tipo_usuario = "NATURAL"

    # TELÉFONO SECUNDARIO
    if not numero_secundaria:
        telefono_secundario = "N/A"

    elif not prefijo_secundaria:
        return JsonResponse({
            "title": "Prefijo vacío",
            "descripcion": "Por favor, selecciona el prefijo telefónico.",
            "icon": "warning"
        })

    else:
        telefono_secundario = prefijo_secundaria + "-" + numero_secundaria

    # CORREO ELECTRONICO (ALTERNATIVO)
    if not correo_secundaria:
        correo_secundario = "N/A"

    elif not dominio_secundaria:
        return JsonResponse({
            "title": "Prefijo vacío",
            "descripcion": "Por favor, selecciona el dominio del Correo Electronico.",
            "icon": "warning"
        })

    else:
        correo_secundario = correo_secundaria + dominio_secundaria

    cedula_identidad = nacionalidad + "-" + num_cedula
    telefono_principal = prefijo_principal + "-" + numero_principal
    correo_electronico = correo_principal + dominio_principal

    if telefono_secundario != "N/A":
        if telefono_secundario.casefold() == telefono_principal.casefold():
            return JsonResponse({
                "estado": "fallo",
                "title": "Teléfonos iguales",
                "descripcion": "El teléfono principal y secundario no pueden ser iguales.",
                "icon": "warning"
            })

        if contacto.objects.filter(
            Q(telefono_principal__iexact=telefono_secundario) |
            Q(telefono_secundario__iexact=telefono_secundario)
        ).exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Teléfono registrado",
                "descripcion": "Ya existe un usuario con este número telefónico.",
                "icon": "warning"
            })

    if correo_secundario != "N/A":
        if correo_secundario.casefold() == correo_electronico.casefold():
            return JsonResponse({
                "estado": "fallo",
                "title": "Correos iguales",
                "descripcion": "El correo principal y secundario no pueden ser iguales.",
                "icon": "warning"
            })

        if contacto.objects.filter(
            Q(correo_principal__iexact=correo_secundario) |
            Q(correo_secundario__iexact=correo_secundario)
        ).exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Correo registrado",
                "descripcion": "Ya existe un usuario con este correo electrónico.",
                "icon": "warning"
            })

    pais_nacimiento = "N/A"
    estado_nacimiento = "N/A"
    municipio_nacimiento = "N/A"
    parroquia_nacimiento = "N/A"
    direccion_nacimiento = "N/A"
    fecha_nacimiento = "N/A"

    condicion_residencia = "N/A"
    municipio_residencia = "N/A"
    parroquia_residencia = "N/A"
    direccion_residencia = "N/A"

    try:
        with transaction.atomic():
            if usuarios.objects.filter(cedula_identidad=cedula_identidad).exists():
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Cédula registrada",
                    "descripcion": "Ya existe un usuario con esa cédula de identidad.",
                    "icon": "warning"
                })

            # Crear usuario.
            usuario = usuarios.objects.create(
                nombre_razon_social=nombre_razon_social,
                tipo_usuario=tipo_usuario,
                nombres=nombres,
                apellidos=apellidos,
                cedula_identidad=cedula_identidad,
                genero=genero,
                estado_civil=estado_civil
            )

            contacto.objects.create(
                telefono_principal=telefono_principal,
                telefono_secundario=telefono_secundario,
                correo_principal=correo_electronico,
                correo_secundario=correo_secundario,
                id_usuario=usuario
            )

            nacimiento.objects.create(
                pais=pais_nacimiento,
                estado=estado_nacimiento,
                municipio=municipio_nacimiento,
                parroquia=parroquia_nacimiento,
                direccion=direccion_nacimiento,
                fecha_nacimiento=fecha_nacimiento,
                id_usuario=usuario
            )

            residencia.objects.create(
                condicion_residencia=condicion_residencia,
                municipio=municipio_residencia,
                parroquia=parroquia_residencia,
                direccion=direccion_residencia,
                id_usuario=usuario 
            )

            encargados_administrativos.objects.create(
                id_usuario=usuario
            )

            # Registrar en bitácora dentro de la transacción.
            cedula_sesion = request.session.get("cedula_identidad")

            if not cedula_sesion:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Error de Sesión",
                    "descripcion": "Debe iniciar sesión.",
                    "icon": "error"
                })

            info_usuario = usuarios.objects.get(
                cedula_identidad=cedula_sesion
            )

            accion = (
                f"Registró un nuevo Encargado Administrativo: "
                f"{nombres} {apellidos}, "
                f"cédula de identidad {cedula_identidad}. "
                f"Perfil asignado: Encargado Administrativo. "
                f"Turno: Turno Completo."
            )

            bitacora.objects.create(
                id_usuario=info_usuario,
                nombre_modulo="Registro de encargados administrativos",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=accion
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Éxito",
            "descripcion": (
                "Se registraron los datos del empleado "
                "y se asignó su perfil correctamente."
            ),
            "icon": "success"
        })
    
    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": (
                "Ocurrió un error al registrar el usuario. "
                "Verifique los datos e intente nuevamente."
                f"{e}"
            ),
            "icon": "error"
        })

def visualizar_administrador(request):
    return render(request, "Modulos/Empleados/Propietario/visualizar_administrador.html")

def administrador_registrado(request):
    NO_REGISTRADO = "No registrado"

    def obtener_valor(instancia, campo):
        if instancia is None:
            return NO_REGISTRADO

        valor = getattr(instancia, campo, None)

        if valor is None:
            return NO_REGISTRADO

        if isinstance(valor, str):
            valor = valor.strip()

            if not valor or valor.casefold() == "n/a":
                return NO_REGISTRADO

        return valor

    try:
        administrador = encargados_administrativos.objects.select_related(
            "id_usuario"
        ).first()

        if administrador is None:
            return JsonResponse({
                "estado": "fallo",
                "existe": False,
                "title": "No registrado o sin perfil vigente",
                "descripcion": (
                    "No se encuentra registrado ningún encargado administrativo "
                    "con un perfil vigente en el sistema."
                ),
                "icon": "info"
            })

        usuario = administrador.id_usuario

        # DATOS DE NACIMIENTO
        try:
            info_nacimiento = nacimiento.objects.get(
                id_usuario=usuario
            )
        except nacimiento.DoesNotExist:
            info_nacimiento = None

        # DATOS DE CONTACTO
        try:
            info_contacto = contacto.objects.get(
                id_usuario=usuario
            )
        except contacto.DoesNotExist:
            info_contacto = None

        # DATOS DE RESIDENCIA
        try:
            info_residencia = residencia.objects.get(
                id_usuario=usuario
            )
        except residencia.DoesNotExist:
            info_residencia = None

        
        # CREDENCIALES E IMAGEN DE PERFIL
        try:
            datos_credenciales = usuario.credenciales
        except credenciales.DoesNotExist:
            datos_credenciales = None

        tiene_credenciales = datos_credenciales is not None

        foto_perfil = (
            datos_credenciales.foto_perfil.url
            if datos_credenciales and datos_credenciales.foto_perfil
            else None
        )

        # RESPUESTA CON LOS DATOS DEL ADMINISTRADOR
        return JsonResponse({
            "estado": "exito",
            "existe": True,
            "tiene_credenciales": tiene_credenciales,
            "foto_perfil": foto_perfil,

            # DATOS PERSONALES
            "usuario": {
                "id": usuario.id_usuario,
                "nombres": obtener_valor(usuario, "nombres"),
                "apellidos": obtener_valor(usuario, "apellidos"),
                "cedula_identidad": obtener_valor(
                    usuario, "cedula_identidad"
                ),
                "genero": obtener_valor(usuario, "genero"),
                "estado_civil": obtener_valor(
                    usuario, "estado_civil"
                )
            },

            # DATOS LABORALES
            "laboral": {
                "perfil": "Encargado Administrativo",
                "turno": "Turno Completo",
                "vigencia": administrador.vigencia,
                "bloqueado": (
                    datos_credenciales.bloqueado
                    if datos_credenciales
                    else False
                )
            },

            # DATOS DE CONTACTO
            "contacto": {
                "telefono_principal": obtener_valor(
                    info_contacto, "telefono_principal"
                ),
                "telefono_secundario": obtener_valor(
                    info_contacto, "telefono_secundario"
                ),
                "correo_principal": obtener_valor(
                    info_contacto, "correo_principal"
                ),
                "correo_secundario": obtener_valor(
                    info_contacto, "correo_secundario"
                )
            },

            # DATOS DE NACIMIENTO
            "nacimiento": {
                "pais": obtener_valor(
                    info_nacimiento, "pais"
                ),
                "estado": obtener_valor(
                    info_nacimiento, "estado"
                ),
                "municipio": obtener_valor(
                    info_nacimiento, "municipio"
                ),
                "parroquia": obtener_valor(
                    info_nacimiento, "parroquia"
                ),
                "direccion": obtener_valor(
                    info_nacimiento, "direccion"
                ),
                "fecha_nacimiento": obtener_valor(
                    info_nacimiento, "fecha_nacimiento"
                )
            },

            # DATOS DE RESIDENCIA
            "residencia": {
                "condicion_residencia": obtener_valor(
                    info_residencia, "condicion_residencia"
                ),
                "municipio": obtener_valor(
                    info_residencia, "municipio"
                ),
                "parroquia": obtener_valor(
                    info_residencia, "parroquia"
                ),
                "direccion": obtener_valor(
                    info_residencia, "direccion"
                )
            }
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": (
                "Ocurrió un error al consultar los datos del "
                "encargado administrativo"
                f" Error: {e}"
            ),
            "icon": "error"
        })

def gestionar_administrador(request):
    id_administrador = request.POST.get("id_administrador")
    accion = request.POST.get("accion")

    if not id_administrador:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato requerido",
            "descripcion": "No se recibió el identificador del administrador.",
            "icon": "warning"
        })

    if accion not in ["bloquear", "retirar_cargo", "asignar_cargo"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Acción inválida",
            "descripcion": "La acción solicitada no es válida.",
            "icon": "warning"
        })
    
    try:
        with transaction.atomic():
            administrador = encargados_administrativos.objects.select_related(
                "id_usuario"
            ).get(id_usuario=id_administrador)

            usuario = administrador.id_usuario

            if accion == "bloquear":
                credencial = usuario.credenciales
                credencial.bloqueado = True
                credencial.save(update_fields=["bloqueado"])

                return JsonResponse({
                    "estado": "exito",
                    "title": "Cuenta bloqueada",
                    "descripcion": (
                        "La cuenta del Encargado Administrativo "
                        "ha sido bloqueada correctamente."
                    ),
                    "icon": "success"
                })

            if accion in ["retirar_cargo", "asignar_cargo"]:
                administrador.vigencia = accion == "asignar_cargo"
                administrador.save(update_fields=["vigencia"])

                if administrador.vigencia:
                    return JsonResponse({
                        "estado": "exito",
                        "title": "Cargo asignado",
                        "descripcion": (
                            "Se ha asignado el cargo de Encargado Administrativo "
                            "correctamente."
                        ),
                        "icon": "success"
                    })

                return JsonResponse({
                    "estado": "exito",
                    "title": "Cargo retirado",
                    "descripcion": (
                        "Se ha retirado la designación del "
                        "Encargado Administrativo correctamente."
                    ),
                    "icon": "success"
                })
    except encargados_administrativos.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Administrador no encontrado",
            "descripcion": "No se encontró el administrador solicitado.",
            "icon": "error"
        })

    except credenciales.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Credenciales no encontradas",
            "descripcion": (
                "El administrador no tiene credenciales registradas."
            ),
            "icon": "error"
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del sistema",
            "descripcion": (
                "No fue posible completar la operación."
                f"Error: {e}"
            ),
            "icon": "error"
        })

def datos_administrador(request):
    try:
        # CONSULTAR DIRECTAMENTE AL ENCARGADO ADMINISTRATIVO VIGENTE
        administrador = encargados_administrativos.objects.select_related(
            "id_usuario",
            "id_usuario__contacto",
            "id_usuario__nacimiento",
            "id_usuario__residencia"
        ).filter(
            vigencia=True
        ).first()

        if administrador is None:
            return JsonResponse({
                "estado": "fallo",
                "title": "No registrado o sin perfil vigente",
                "descripcion": (
                    "No se encuentra registrado ningún encargado administrativo "
                    "con un perfil vigente en el sistema."
                ),
                "icon": "info"
            })

        usuario = administrador.id_usuario

        # OBTENER LOS REGISTROS RELACIONADOS
        info_contacto = getattr(usuario, "contacto", None)
        info_nacimiento = getattr(usuario, "nacimiento", None)
        info_residencia = getattr(usuario, "residencia", None)

        # VALIDAR QUE LOS CAMPOS TENGAN INFORMACIÓN
        def obtener_dato(instancia, campo):
            if instancia is None:
                return "No registrado"

            valor = getattr(instancia, campo, None)

            if valor is None:
                return "No registrado"

            if isinstance(valor, str):
                if not valor.strip() or valor.strip().casefold() == "n/a":
                    return "No registrado"

            return str(valor) if campo == "fecha_nacimiento" else valor

        return JsonResponse({
            "estado": "exito",

            "usuario": {
                "id": usuario.id_usuario,
                "tipo_usuario": usuario.tipo_usuario,
                "nombre_razon_social": usuario.nombre_razon_social,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula_identidad": usuario.cedula_identidad,
                "genero": obtener_dato(usuario, "genero"),
                "estado_civil": obtener_dato(usuario, "estado_civil"),
            },

            "laboral": {
                "perfil": "Encargado Administrativo",
                "turno": "Turno Completo",
            },

           "contacto": {
                "telefono_principal": (
                    info_contacto.telefono_principal if info_contacto else "No registrado"
                ),
                "telefono_secundario": (
                    info_contacto.telefono_secundario if info_contacto else "No registrado"
                ),
                "correo_principal": (
                    info_contacto.correo_principal if info_contacto else "No registrado"
                ),
                "correo_secundario": (
                    info_contacto.correo_secundario if info_contacto else "No registrado"
                ),
            },

            "nacimiento": {
                "pais": obtener_dato(info_nacimiento, "pais"),
                "estado": obtener_dato(info_nacimiento, "estado"),
                "municipio": obtener_dato(info_nacimiento, "municipio"),
                "parroquia": obtener_dato(info_nacimiento, "parroquia"),
                "direccion": obtener_dato(info_nacimiento, "direccion"),
                "fecha_nacimiento": (
                    str(info_nacimiento.fecha_nacimiento)
                    if info_nacimiento and info_nacimiento.fecha_nacimiento
                    else None
                ),
            },

            "residencia": {
                "condicion_residencia": obtener_dato(info_residencia, "condicion_residencia"),
                "municipio": obtener_dato(info_residencia, "municipio"),
                "parroquia": obtener_dato(info_residencia, "parroquia"),
                "direccion": obtener_dato(info_residencia, "direccion"),
            },
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "Ocurrió un error al consultar los datos del administrador.",
            "icon": "error"
        })

def actualizar_administrador(request):
    if request.method != "POST":
        return render(request, "Modulos/Empleados/Propietario/actualizar_administrador.html")

    usuario_id = request.POST.get("id_usuario", "").strip()

    if not usuario_id:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario no identificado",
            "descripcion": "No se pudo identificar al Encargado Administrativo que desea actualizar.",
            "icon": "warning"
        })

    try:
        administrador = encargados_administrativos.objects.select_related(
            "id_usuario"
        ).get(
            id_usuario__id_usuario=usuario_id
        )

        usuario = administrador.id_usuario

    except encargados_administrativos.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Administrador no encontrado",
            "descripcion": "No existe un Encargado Administrativo asociado al usuario seleccionado.",
            "icon": "error"
        })

    except ValueError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El identificador del usuario no es válido.",
            "icon": "warning"
        })

    # DATOS PERSONALES
    nombre_usuario = request.POST.get("nombres", "").strip()
    apellido_usuario = request.POST.get("apellidos", "").strip()
    nacionalidad_usuario = request.POST.get("nacionalidad", "").strip()
    cedula_usuario = request.POST.get("cedula_identidad", "").strip()
    genero_usuario = request.POST.get("genero", "").strip()
    estado_civil_usuario = request.POST.get("estado_civil", "").strip()

    # TELÉFONO PRINCIPAL
    prefijo_principal = request.POST.get("prefijo_principal", "").strip()
    numero_principal = request.POST.get("numero_principal", "").strip()

    # TELÉFONO SECUNDARIO
    prefijo_secundaria = request.POST.get("prefijo_secundaria", "").strip()
    numero_secundaria = request.POST.get("numero_secundaria", "").strip()

    # CORREO PRINCIPAL
    correo_principal_usuario = request.POST.get("correo_principal", "").strip()
    dominio_principal = request.POST.get("dominio_principal", "").strip()

    # CORREO SECUNDARIO
    correo_secundario_usuario = request.POST.get("correo_secundaria", "").strip()
    dominio_secundario = request.POST.get("dominio_secundaria", "").strip()

    # DATOS DE NACIMIENTO
    pais = request.POST.get("actualizar_pais_nacimiento", "").strip()

    if pais == "Venezuela":
        estado = request.POST.get("actualizar_estado_nacimiento", "").strip()
        municipio = request.POST.get("actualizar_municipio_nacimiento", "").strip()
        parroquia = request.POST.get("actualizar_parroquia_nacimiento", "").strip()
    else:
        estado = request.POST.get("actualizar_estado_nacimiento_nvzla", "").strip()
        municipio = request.POST.get("actualizar_municipio_nacimiento_nvzla", "").strip()
        parroquia = request.POST.get("actualizar_parroquia_nacimiento_nvzla", "").strip()

    direccion_nacimiento = request.POST.get("actualizar_direccion_nacimiento", "").strip()
    fecha_nacimiento = request.POST.get("actualizar_fecha_nacimiento", "").strip()

    # DATOS DE RESIDENCIA
    condicion_residencia = request.POST.get("actualizar_condicion_residencia", "").strip()
    municipio_residencia = request.POST.get("actualizar_municipio_residencia", "").strip()
    parroquia_residencia = request.POST.get("actualizar_parroquia_residencia", "").strip()
    direccion_residencia = request.POST.get("actualizar_direccion_residencia", "").strip()

    # VALIDAR CAMPOS PERSONALES Y DE CONTACTO
    campos_obligatorios = [
        (nombre_usuario, "Nombre", "Por favor, ingrese los nombres del administrador."),
        (apellido_usuario, "Apellido", "Por favor, ingrese los apellidos del administrador."),
        (nacionalidad_usuario, "Nacionalidad", "Por favor, seleccione la nacionalidad."),
        (cedula_usuario, "Cédula", "Por favor, ingrese el número de cédula."),
        (prefijo_principal, "Prefijo principal", "Por favor, seleccione el prefijo telefónico principal."),
        (numero_principal, "Teléfono principal", "Por favor, ingrese el número telefónico principal."),
        (correo_principal_usuario, "Correo principal", "Por favor, ingrese el correo principal."),
        (dominio_principal, "Dominio principal", "Por favor, seleccione el dominio del correo principal."),
    ]

    for valor, campo, mensaje in campos_obligatorios:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    # VALIDAR TELÉFONO SECUNDARIO
    if numero_secundaria:
        if not prefijo_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Prefijo secundario",
                "descripcion": "Debe seleccionar el prefijo telefónico secundario.",
                "icon": "warning"
            })

        telefono_secundario = f"{prefijo_secundaria}-{numero_secundaria}"
    else:
        telefono_secundario = "N/A"

    # VALIDAR CORREO SECUNDARIO
    if correo_secundario_usuario:
        if not dominio_secundario:
            return JsonResponse({
                "estado": "fallo",
                "title": "Dominio secundario",
                "descripcion": "Por favor, seleccione el dominio del correo secundario.",
                "icon": "warning"
            })

        correo_secundario = correo_secundario_usuario + dominio_secundario
    else:
        correo_secundario = "N/A"

    # CONSTRUIR DATOS DE CONTACTO
    razon_social = f"{nombre_usuario} {apellido_usuario}"
    cedula_identidad = f"{nacionalidad_usuario}-{cedula_usuario}"
    telefono_principal = f"{prefijo_principal}-{numero_principal}"
    correo_principal = correo_principal_usuario + dominio_principal

    def datos_completos(instancia, campos):
        if instancia is None:
            return False

        for campo in campos:
            valor = getattr(instancia, campo, None)

            if valor is None:
                return False

            if isinstance(valor, str):
                if not valor.strip() or valor.strip().casefold() in ("n/a", "no registrado"):
                    return False

        return True
 
    # DATOS DE NACIMIENTO
    try:
        info_nacimiento = nacimiento.objects.get(id_usuario=usuario)
    except nacimiento.DoesNotExist:
        info_nacimiento = None

    campos_nacimiento = [
        "pais",
        "estado",
        "municipio",
        "parroquia",
        "direccion",
        "fecha_nacimiento"
    ]

    nacimiento_registrado = datos_completos(
        info_nacimiento,
        campos_nacimiento
    )

    if nacimiento_registrado:

        campos_obligatorios = [
            (pais, "País de nacimiento", "Por favor, seleccione el país de nacimiento."),
            (estado, "Estado de nacimiento", "Por favor, complete el estado de nacimiento."),
            (municipio, "Municipio de nacimiento", "Por favor, complete el municipio de nacimiento."),
            (parroquia, "Parroquia de nacimiento", "Por favor, complete la parroquia de nacimiento."),
            (direccion_nacimiento, "Dirección de nacimiento", "Por favor, ingrese la dirección de nacimiento."),
            (fecha_nacimiento, "Fecha de nacimiento", "Por favor, seleccione la fecha de nacimiento."),
        ]

        for valor, campo, mensaje in campos_obligatorios:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

    # DATOS DE RESIDENCIA
    try:
        info_residencia = residencia.objects.get(id_usuario=usuario)
    except residencia.DoesNotExist:
        info_residencia = None

    campos_residencia = [
        "condicion_residencia",
        "municipio",
        "parroquia",
        "direccion"
    ]

    residencia_registrada = datos_completos(
        info_residencia,
        campos_residencia
    )

    # Los datos opcionales no se modifican cuando el formulario muestra el marcador.
    if not genero_usuario or genero_usuario.casefold() == "no registrado":
        genero_usuario = usuario.genero

    if not estado_civil_usuario or estado_civil_usuario.casefold() == "no registrado":
        estado_civil_usuario = usuario.estado_civil

    if residencia_registrada:

        campos_obligatorios = [
            (condicion_residencia, "Condición de residencia", "Por favor, seleccione la condición de residencia."),
            (municipio_residencia, "Municipio de residencia", "Por favor, seleccione el municipio de residencia."),
            (parroquia_residencia, "Parroquia de residencia", "Por favor, seleccione la parroquia de residencia."),
            (direccion_residencia, "Dirección de residencia", "Por favor, ingrese la dirección de residencia."),
        ]

        for valor, campo, mensaje in campos_obligatorios:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        # CONSERVAR TELÉFONO Y CORREO SECUNDARIOS ANTERIORES
        contacto_anterior = contacto.objects.filter(
            id_usuario=usuario
        ).first()

        if contacto_anterior:
            if not telefono_secundario or telefono_secundario.casefold() == "no registrado":
                telefono_secundario = contacto_anterior.telefono_secundario

            if not correo_secundario or correo_secundario.casefold() == "no registrado":
                correo_secundario = contacto_anterior.correo_secundario

    # REALIZAR ACTUALIZACIÓN
    try:
        with transaction.atomic():

            # VALIDAR CÉDULA ÚNICA
            if usuarios.objects.filter(
                cedula_identidad=cedula_identidad
            ).exclude(
                id_usuario=usuario.id_usuario
            ).exists():

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Cédula existente",
                    "descripcion": "Ya existe otro usuario con esa cédula.",
                    "icon": "warning"
                })

            # VALIDAR TELÉFONO PRINCIPAL ÚNICO
            if contacto.objects.filter(
                telefono_principal=telefono_principal
            ).exclude(
                id_usuario=usuario
            ).exists():

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Teléfono existente",
                    "descripcion": "Ya existe otro usuario con ese número telefónico.",
                    "icon": "warning"
                })

            # VALIDAR CORREO PRINCIPAL ÚNICO
            if contacto.objects.filter(
                correo_principal=correo_principal
            ).exclude(
                id_usuario=usuario
            ).exists():

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Correo existente",
                    "descripcion": "Ya existe otro usuario con ese correo.",
                    "icon": "warning"
                })

            # VALIDAR CORREO SECUNDARIO ÚNICO
            if correo_secundario != "N/A" and contacto.objects.filter(
                correo_secundario=correo_secundario
            ).exclude(
                id_usuario=usuario
            ).exists():

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Correo existente",
                    "descripcion": "Ya existe otro usuario con ese correo.",
                    "icon": "warning"
                })

            # ACTUALIZAR DATOS PERSONALES
            usuario.nombre_razon_social = razon_social
            usuario.nombres = nombre_usuario
            usuario.apellidos = apellido_usuario
            usuario.cedula_identidad = cedula_identidad
            usuario.genero = genero_usuario
            usuario.estado_civil = estado_civil_usuario
            usuario.save()

            # ACTUALIZAR O CREAR CONTACTO
            contacto.objects.update_or_create(
                id_usuario=usuario,
                defaults={
                    "telefono_principal": telefono_principal,
                    "telefono_secundario": telefono_secundario,
                    "correo_principal": correo_principal,
                    "correo_secundario": correo_secundario,
                }
            )

            # ACTUALIZAR NACIMIENTO SI ESTÁ COMPLETO
            if nacimiento_registrado:
                info_nacimiento.pais = pais
                info_nacimiento.estado = estado
                info_nacimiento.municipio = municipio
                info_nacimiento.parroquia = parroquia
                info_nacimiento.direccion = direccion_nacimiento
                info_nacimiento.fecha_nacimiento = fecha_nacimiento
                info_nacimiento.save()

            # ACTUALIZAR RESIDENCIA SI ESTÁ COMPLETA
            if residencia_registrada:
                info_residencia.condicion_residencia = condicion_residencia
                info_residencia.municipio = municipio_residencia
                info_residencia.parroquia = parroquia_residencia
                info_residencia.direccion = direccion_residencia
                info_residencia.save()

            info_usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))

            # REGISTRAR ACCIÓN EN BITÁCORA
            bitacora.objects.create(
                id_usuario=info_usuario,
                nombre_modulo="Actualización de encargados administrativos",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=(
                    f"Actualización de datos del Encargado Administrativo "
                    f"{nombre_usuario} {apellido_usuario} {cedula_identidad}"
                )
            )

            return JsonResponse({
                "estado": "exito",
                "title": "Actualización exitosa",
                "descripcion": "Los datos del Encargado Administrativo se actualizaron correctamente.",
                "icon": "success"
            })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": f"Ocurrió un error al actualizar los datos del administrador. Error: {str(e)}",
            "icon": "error"
        })
    