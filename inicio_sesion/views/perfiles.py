from django.db import transaction
from django.shortcuts import render
from django.http import JsonResponse

from inicio_sesion.models import usuarios, turnos_laborales, bitacora, supervisores_encargados, personal_limpieza, despachadores, vigilantes

# PERFILES REGISTRADOS

def perfiles_disponibles(request):

    if request.method != "POST":
        return JsonResponse({
            "perfiles": []
        }, status=405)

    turno_seleccionado = request.POST.get("turno")

    datos = [
        {
            "id_perfil": "SUPERVISOR_ENCARGADO",
            "perfil": "Supervisor Encargado"
        },
        {
            "id_perfil": "PERSONAL_LIMPIEZA",
            "perfil": "Personal de Limpieza"
        },
        {
            "id_perfil": "DESPACHADOR",
            "perfil": "Despachador"
        },
        {
            "id_perfil": "VIGILANTE",
            "perfil": "Vigilante"
        }
    ]

    if turno_seleccionado:

        try:
            turno_id = int(turno_seleccionado)
        except (TypeError, ValueError):
            turno_id = None

        if turno_id:

            supervisor_ocupado = (
                supervisores_encargados.objects
                .filter(
                    id_turno_id=turno_id,
                    vigencia=True
                )
                .exists()
            )

            if supervisor_ocupado:
                datos = [
                    perfil
                    for perfil in datos
                    if perfil["id_perfil"] != "SUPERVISOR_ENCARGADO"
                ]

    return JsonResponse({"perfiles": datos})

# BUSCAR DATOS PERFILES 

def buscar_datos_asignacion(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad", "").strip()
        cedula = request.POST.get("cedula", "").strip()

        if not nacionalidad or not cedula:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Debe ingresar la nacionalidad y la cédula."
                ),
                "icon": "warning"
            })

        cedula_completa = f"{nacionalidad}-{cedula}"

        try:
            usuario = usuarios.objects.get(cedula_identidad=cedula_completa)
        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "no_existe",
                "title": "Error",
                "descripcion": (
                    "No se encontró ningún empleado "
                    "con esa cédula."
                ),
                "icon": "warning"
            })

        turnos = list(turnos_laborales.objects.all())

        perfiles_datos = []

        # SUPERVISOR ENCARGADO
        supervisor = (
            supervisores_encargados.objects
            .filter(
                id_usuario=usuario
            )
            .select_related("id_turno")
            .first()
        )

        if supervisor:
            opciones_turnos = []

            if not supervisor.vigencia:
                opciones_turnos = [
                    {
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    }
                    for turno in turnos
                ]

            else:
                for turno in turnos:
                    if turno.id_turno == supervisor.id_turno_id:

                        opciones_turnos.append({
                            "id_turno": turno.id_turno,
                            "nombre": turno.nombre
                        })

                        continue

                    supervisor_ocupado = (
                        supervisores_encargados.objects
                        .filter(
                            id_turno=turno,
                            vigencia=True
                        )
                        .exclude(
                            id_supervisor=supervisor.id_supervisor
                        )
                        .exists()
                    )

                    if not supervisor_ocupado:

                        opciones_turnos.append({
                            "id_turno": turno.id_turno,
                            "nombre": turno.nombre
                        })

            perfiles_datos.append({
                "id_perfil_usuario": supervisor.id_supervisor,
                "id_perfil": "SUPERVISOR_ENCARGADO",
                "perfil": "Supervisor Encargado",
                "id_turno": supervisor.id_turno_id,
                "turno": supervisor.id_turno.nombre,
                "vigencia": supervisor.vigencia,
                "turnos": opciones_turnos
            })

        # PERSONAL DE LIMPIEZA
        limpieza = (
            personal_limpieza.objects
            .filter(
                id_usuario=usuario
            )
            .select_related("id_turno")
            .first()
        )

        if limpieza:
            opciones_turnos = [
                {
                    "id_turno": turno.id_turno,
                    "nombre": turno.nombre
                }
                for turno in turnos
            ]

            perfiles_datos.append({
                "id_perfil_usuario": limpieza.id_personal,
                "id_perfil": "PERSONAL_LIMPIEZA",
                "perfil": "Personal de Limpieza",
                "id_turno": limpieza.id_turno_id,
                "turno": limpieza.id_turno.nombre,
                "vigencia": limpieza.vigencia,
                "turnos": opciones_turnos
            })

        # DESPACHADOR
        despachador = (
            despachadores.objects
            .filter(
                id_usuario=usuario
            )
            .select_related("id_turno")
            .first()
        )

        if despachador:
            opciones_turnos = [
                {
                    "id_turno": turno.id_turno,
                    "nombre": turno.nombre
                }
                for turno in turnos
            ]

            perfiles_datos.append({
                "id_perfil_usuario": despachador.id_despachador,
                "id_perfil": "DESPACHADOR",
                "perfil": "Despachador",
                "id_turno": despachador.id_turno_id,
                "turno": despachador.id_turno.nombre,
                "vigencia": despachador.vigencia,
                "turnos": opciones_turnos
            })

        # VIGILANTE
        vigilante = (
            vigilantes.objects
            .filter(
                id_usuario=usuario
            )
            .select_related("id_turno")
            .first()
        )

        if vigilante:
            opciones_turnos = [
                {
                    "id_turno": turno.id_turno,
                    "nombre": turno.nombre
                }
                for turno in turnos
            ]

            perfiles_datos.append({
                "id_perfil_usuario": vigilante.id_vigilante,
                "id_perfil": "VIGILANTE",
                "perfil": "Vigilante",
                "id_turno": vigilante.id_turno_id,
                "turno": vigilante.id_turno.nombre,
                "vigencia": vigilante.vigencia,
                "turnos": opciones_turnos
            })

        if not perfiles_datos:
            request.session["id_empleado"] = usuario.id_usuario

            return JsonResponse({
                "estado": "exito",
                "success": True,
                "codigo": "SIN_PERFIL",
                "usuario": {
                    "id_usuario": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula_identidad": usuario.cedula_identidad,
                    "genero": usuario.genero,
                    "estado_civil": usuario.estado_civil
                },
                "perfiles": []
            })

        request.session["id_empleado"] = usuario.id_usuario

        return JsonResponse({
            "estado": "exito",
            "success": True,
            "usuario": {
                "id_usuario": usuario.id_usuario,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula_identidad": usuario.cedula_identidad,
                "genero": usuario.genero,
                "estado_civil": usuario.estado_civil
            },
            "perfiles": perfiles_datos
        })
            
# PERFILES NO ASIGNADOS

def perfiles_usuario_no_registrados(request):
    if request.method == "POST":
        turno_seleccionado = request.POST.get("turno")
        
        id_empleado = request.session.get("id_empleado")
        if not id_empleado:
            return JsonResponse({
                "estado": "fallo",
                "mensaje": "No se ha seleccionado ningún empleado.",
                "perfiles": []
            })

        datos = []

        # SUPERVISOR ENCARGADO
        supervisor_usuario = (
            supervisores_encargados.objects
            .filter(
                id_usuario_id=id_empleado
            )
            .first()
        )

        if not supervisor_usuario:
            supervisor_disponible = True
            
            if turno_seleccionado:
                try:
                    turno_id = int(turno_seleccionado)
                except (TypeError, ValueError):
                    turno_id = None

                if turno_id:
                    supervisor_ocupado = (
                        supervisores_encargados.objects
                        .filter(
                            id_turno_id=turno_id,
                            vigencia=True
                        )
                        .exists()
                    )

                    if supervisor_ocupado:
                        supervisor_disponible = False

            if supervisor_disponible:
                datos.append({
                    "id_perfil": "SUPERVISOR_ENCARGADO",
                    "perfil": "Supervisor Encargado"
                })

        # PERSONAL DE LIMPIEZA
        limpieza_usuario = (
            personal_limpieza.objects
            .filter(
                id_usuario_id=id_empleado
            )
            .exists()
        )

        if not limpieza_usuario:
            datos.append({
                "id_perfil": "PERSONAL_LIMPIEZA",
                "perfil": "Personal de Limpieza"
            })

        # DESPACHADOR
        despachador_usuario = (
            despachadores.objects
            .filter(
                id_usuario_id=id_empleado
            )
            .exists()
        )

        if not despachador_usuario:
            datos.append({
                "id_perfil": "DESPACHADOR",
                "perfil": "Despachador"
            })

        # VIGILANTE
        vigilante_usuario = (
            vigilantes.objects
            .filter(
                id_usuario_id=id_empleado
            )
            .exists()
        )

        if not vigilante_usuario:
            datos.append({
                "id_perfil": "VIGILANTE",
                "perfil": "Vigilante"
            })

        return JsonResponse({
            "estado": "exito",
            "perfiles": datos
        })

# REGISTRAR NUEVAS PERFILES ASIGNADOS

def registrar_nueva_asignacion(request):
    if request.method == "POST":
        id_empleado = request.session.get("id_empleado")

        if not id_empleado:
            return JsonResponse({
                "estado": "error",
                "icon": "warning",
                "title": "Empleado no seleccionado",
                "descripcion": "No se ha seleccionado ningún empleado."
            })

        id_turno = request.POST.get("turnos_registro")
        id_perfil = request.POST.get("perfil")

        if not id_turno or not id_perfil:
            return JsonResponse({
                "estado": "error",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Debe seleccionar el turno laboral y el perfil."
                )
            })

        perfiles_validos = {
            "SUPERVISOR_ENCARGADO": "Supervisor Encargado",
            "PERSONAL_LIMPIEZA": "Personal de Limpieza",
            "DESPACHADOR": "Despachador",
            "VIGILANTE": "Vigilante"
        }

        if id_perfil not in perfiles_validos:
            return JsonResponse({
                "estado": "error",
                "icon": "error",
                "title": "Perfil no válido",
                "descripcion": "El perfil seleccionado no es válido."
            })

        try:
            usuario = usuarios.objects.get(
                id_usuario=id_empleado
            )
        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "error",
                "icon": "error",
                "title": "Usuario no encontrado",
                "descripcion": "El usuario seleccionado no existe."
            })

        try:
            turno = turnos_laborales.objects.get(
                id_turno=id_turno
            )
        except turnos_laborales.DoesNotExist:
            return JsonResponse({
                "estado": "error",
                "icon": "error",
                "title": "Turno no encontrado",
                "descripcion": "El turno seleccionado no existe."
            })

        # VALIDAR SI EL EMPLEADO YA TIENE OTRO PERFIL ACTIVO
        supervisor_activo = supervisores_encargados.objects.filter(
            id_usuario=usuario,
            vigencia=True
        ).exists()

        limpieza_activa = personal_limpieza.objects.filter(
            id_usuario=usuario,
            vigencia=True
        ).exists()

        despachador_activo = despachadores.objects.filter(
            id_usuario=usuario,
            vigencia=True
        ).exists()

        vigilante_activo = vigilantes.objects.filter(
            id_usuario=usuario,
            vigencia=True
        ).exists()

        tiene_perfil_activo = (
            supervisor_activo
            or limpieza_activa
            or despachador_activo
            or vigilante_activo
        )

        if tiene_perfil_activo:
            return JsonResponse({
                "estado": "error",
                "icon": "warning",
                "title": "Perfil activo",
                "descripcion": (
                    "El empleado ya tiene un perfil laboral activo. "
                    "Debe inhabilitar el perfil actual antes de "
                    "asignar uno nuevo."
                )
            })

        try:
            with transaction.atomic():
                usuario_accion = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )

                nombre_perfil = perfiles_validos[id_perfil]

                # SUPERVISOR ENCARGADO
                if id_perfil == "SUPERVISOR_ENCARGADO":

                    supervisor_existente = (
                        supervisores_encargados.objects
                        .filter(
                            id_usuario=usuario
                        )
                        .first()
                    )

                    if supervisor_existente:
                        if supervisor_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Supervisor Encargado."
                                )
                            })

                        supervisor_ocupado = (
                            supervisores_encargados.objects
                            .filter(
                                id_turno=turno,
                                vigencia=True
                            )
                            .exclude(
                                id_supervisor=(
                                    supervisor_existente.id_supervisor
                                )
                            )
                            .exists()
                        )

                        if supervisor_ocupado:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Turno ocupado",
                                "descripcion": (
                                    "El turno seleccionado ya tiene "
                                    "un Supervisor Encargado activo."
                                )
                            })

                        supervisor_existente.id_turno = turno
                        supervisor_existente.vigencia = True

                        supervisor_existente.save(
                            update_fields=[
                                "id_turno",
                                "vigencia"
                            ]
                        )

                    else:
                        supervisor_ocupado = (
                            supervisores_encargados.objects
                            .filter(
                                id_turno=turno,
                                vigencia=True
                            )
                            .exists()
                        )

                        if supervisor_ocupado:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Turno ocupado",
                                "descripcion": (
                                    "El turno seleccionado ya tiene "
                                    "un Supervisor Encargado activo."
                                )
                            })

                        supervisores_encargados.objects.create(
                            id_usuario=usuario,
                            id_turno=turno,
                            vigencia=True
                        )

                # PERSONAL DE LIMPIEZA
                elif id_perfil == "PERSONAL_LIMPIEZA":

                    limpieza_existente = (
                        personal_limpieza.objects
                        .filter(
                            id_usuario=usuario
                        )
                        .first()
                    )

                    if limpieza_existente:

                        if limpieza_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Personal de Limpieza."
                                )
                            })

                        limpieza_existente.id_turno = turno
                        limpieza_existente.vigencia = True

                        limpieza_existente.save(
                            update_fields=[
                                "id_turno",
                                "vigencia"
                            ]
                        )

                    else:
                        personal_limpieza.objects.create(
                            id_usuario=usuario,
                            id_turno=turno,
                            vigencia=True
                        )

                # DESPACHADOR
                elif id_perfil == "DESPACHADOR":

                    despachador_existente = (
                        despachadores.objects
                        .filter(
                            id_usuario=usuario
                        )
                        .first()
                    )

                    if despachador_existente:

                        if despachador_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Despachador."
                                )
                            })

                        despachador_existente.id_turno = turno
                        despachador_existente.vigencia = True

                        despachador_existente.save(
                            update_fields=[
                                "id_turno",
                                "vigencia"
                            ]
                        )

                    else:
                        despachadores.objects.create(
                            id_usuario=usuario,
                            id_turno=turno,
                            vigencia=True
                        )

                # VIGILANTE
                elif id_perfil == "VIGILANTE":

                    vigilante_existente = (
                        vigilantes.objects
                        .filter(
                            id_usuario=usuario
                        )
                        .first()
                    )

                    if vigilante_existente:

                        if vigilante_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Vigilante."
                                )
                            })

                        vigilante_existente.id_turno = turno
                        vigilante_existente.vigencia = True

                        vigilante_existente.save(
                            update_fields=[
                                "id_turno",
                                "vigencia"
                            ]
                        )

                    else:
                        vigilantes.objects.create(
                            id_usuario=usuario,
                            id_turno=turno,
                            vigencia=True
                        )

                bitacora.objects.create(
                    id_usuario=usuario_accion,
                    accion=(
                        f"Se asignó el perfil {nombre_perfil} "
                        f"al empleado {usuario.nombres} "
                        f"{usuario.apellidos} "
                        f"en el turno {turno.nombre}."
                    )
                )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": (
                    f"El perfil {nombre_perfil} "
                    "se registró exitosamente."
                )
            })

        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No se encontró el usuario que registra "
                    "la asignación."
                )
            })

        except Exception as e:
            print(e)

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "Ocurrió un error al registrar "
                    "la asignación."
                )
            })

# CONOCER LA CANTIDAD DE PERFILES ASIGNADO AL EMEPLEADO

def cantidad_perfiles_asignado(request):
    id_empleado = request.session.get("id_empleado")

    if not id_empleado:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": "No se ha seleccionado ningún empleado."
        })

    # TOTAL DE PERFILES LABORALES DISPONIBLES
    cantidad_perfiles = 4

    # CANTIDAD DE PERFILES VIGENTES DEL EMPLEADO
    cantidad_asignados = 0

    if supervisores_encargados.objects.filter(
        id_usuario_id=id_empleado,
        vigencia=True
    ).exists():
        cantidad_asignados += 1

    if personal_limpieza.objects.filter(
        id_usuario_id=id_empleado,
        vigencia=True
    ).exists():
        cantidad_asignados += 1

    if despachadores.objects.filter(
        id_usuario_id=id_empleado,
        vigencia=True
    ).exists():
        cantidad_asignados += 1

    if vigilantes.objects.filter(
        id_usuario_id=id_empleado,
        vigencia=True
    ).exists():
        cantidad_asignados += 1

    # VERIFICAR SI TIENE TODOS LOS PERFILES
    if cantidad_asignados >= cantidad_perfiles:
        return JsonResponse({
            "estado": "fallo",
            "todos_asignados": True,
            "icon": "error",
            "title": "Perfiles completos",
            "descripcion": (
                "El empleado ya tiene todos los perfiles laborales "
                "asignados."
            )
        })

    # TODAVÍA PUEDE ASIGNARSE OTRO PERFIL
    return JsonResponse({
        "estado": "exito",
        "todos_asignados": False
    })

# CARGA LOS PERFILES ASIGNADOS O MODIFICADOS

def cargar_perfiles_asignados(request):
    id_empleado = request.session.get("id_empleado")

    if not id_empleado:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Empleado no seleccionado",
            "descripcion": "No se ha seleccionado ningún empleado.",
            "perfiles": []
        })

    turnos = list(turnos_laborales.objects.all())

    datos = []

    # SUPERVISOR ENCARGADO
    supervisor = supervisores_encargados.objects.filter(
        id_usuario_id=id_empleado
    ).select_related(
        "id_turno"
    ).first()

    if supervisor:
        opciones_turnos = []

        if not supervisor.vigencia:
            opciones_turnos = [
                {
                    "id_turno": turno.id_turno,
                    "nombre": turno.nombre
                }
                for turno in turnos
            ]

        else:
            for turno in turnos:

                # El turno actual siempre puede mantenerse
                if (
                    supervisor.id_turno and
                    turno.id_turno == supervisor.id_turno_id
                ):
                    opciones_turnos.append({
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    })
                    continue

                # Verificar si otro supervisor ya ocupa el turno
                supervisor_ocupado = supervisores_encargados.objects.filter(
                    id_turno_id=turno.id_turno,
                    vigencia=True
                ).exclude(
                    id_supervisor=supervisor.id_supervisor
                ).exists()

                if not supervisor_ocupado:
                    opciones_turnos.append({
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    })

        datos.append({
            "id_registro": supervisor.id_supervisor,
            "id_perfil": "SUPERVISOR_ENCARGADO",
            "perfil": "Supervisor Encargado",
            "id_turno": (
                supervisor.id_turno.id_turno
                if supervisor.id_turno
                else None
            ),
            "turno": (
                supervisor.id_turno.nombre
                if supervisor.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": supervisor.vigencia,
            "turnos": opciones_turnos
        })

    # PERSONAL DE LIMPIEZA
    limpieza = personal_limpieza.objects.filter(
        id_usuario_id=id_empleado
    ).select_related(
        "id_turno"
    ).first()

    if limpieza:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        datos.append({
            "id_registro": limpieza.id_personal,
            "id_perfil": "PERSONAL_LIMPIEZA",
            "perfil": "Personal de Limpieza",
            "id_turno": (
                limpieza.id_turno.id_turno
                if limpieza.id_turno
                else None
            ),
            "turno": (
                limpieza.id_turno.nombre
                if limpieza.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": limpieza.vigencia,
            "turnos": opciones_turnos
        })

    # DESPACHADOR
    despachador = despachadores.objects.filter(
        id_usuario_id=id_empleado
    ).select_related(
        "id_turno"
    ).first()

    if despachador:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        datos.append({
            "id_registro": despachador.id_despachador,
            "id_perfil": "DESPACHADOR",
            "perfil": "Despachador",
            "id_turno": (
                despachador.id_turno.id_turno
                if despachador.id_turno
                else None
            ),
            "turno": (
                despachador.id_turno.nombre
                if despachador.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": despachador.vigencia,
            "turnos": opciones_turnos
        })

    # VIGILANTE
    vigilante = vigilantes.objects.filter(
        id_usuario_id=id_empleado
    ).select_related(
        "id_turno"
    ).first()

    if vigilante:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        datos.append({
            "id_registro": vigilante.id_vigilante,
            "id_perfil": "VIGILANTE",
            "perfil": "Vigilante",
            "id_turno": (
                vigilante.id_turno.id_turno
                if vigilante.id_turno
                else None
            ),
            "turno": (
                vigilante.id_turno.nombre
                if vigilante.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": vigilante.vigencia,
            "turnos": opciones_turnos
        })

    return JsonResponse({
        "estado": "exito",
        "perfiles": datos
    })

#  DETALLES PERFILES ASIGNADO

def buscar_datos_perfil(request):
    if request.method == "POST":
        id_perfil = request.POST.get("id_perfil")
        id_perfil_usuario = request.POST.get("id_perfil_usuario")
        
        print(id_perfil)

        if id_perfil == "SUPERVISOR_ENCARGADO":
            try:
                info_perfil = (
                    supervisores_encargados.objects
                    .select_related("id_usuario", "id_turno")
                    .get(id_supervisor=id_perfil_usuario)
                )

            except supervisores_encargados.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Perfil no disponible",
                    "descripcion": "El Supervisor Encargado seleccionado no existe."
                })

        elif id_perfil == "PERSONAL_LIMPIEZA":

            try:
                info_perfil = (
                    personal_limpieza.objects
                    .select_related("id_usuario", "id_turno")
                    .get(id_personal=id_perfil_usuario)
                )

            except personal_limpieza.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Perfil no disponible",
                    "descripcion": "El Personal de Limpieza seleccionado no existe."
                })

        elif id_perfil == "DESPACHADOR":

            try:
                info_perfil = (
                    despachadores.objects
                    .select_related("id_usuario", "id_turno")
                    .get(id_despachador=id_perfil_usuario)
                )

            except despachadores.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Perfil no disponible",
                    "descripcion": "El Despachador seleccionado no existe."
                })

        elif id_perfil == "VIGILANTE":

            try:
                info_perfil = (
                    vigilantes.objects
                    .select_related("id_usuario", "id_turno")
                    .get(id_vigilante=id_perfil_usuario)
                )

            except vigilantes.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Perfil no disponible",
                    "descripcion": "El Vigilante seleccionado no existe."
                })

        else:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil inválido",
                "descripcion": "El tipo de personal seleccionado no es válido."
            })

        return JsonResponse({
            "estado": "exito",
            "id_registro": id_perfil_usuario,
            "id_perfil": id_perfil,
            "id_turno": (
                info_perfil.id_turno.id_turno
                if info_perfil.id_turno
                else None
            ),
            "turno": (
                info_perfil.id_turno.nombre
                if info_perfil.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": info_perfil.vigencia
        })

# ACTUALIZAR PERFILES ASIGNADOS

def actualizar_vigencia_perfil(request):
    if request.method == "POST":
        id_registro = request.POST.get("id_perfil_asignado")
        id_perfil = request.POST.get("id_perfil")
        turno = request.POST.get("actualizar_turno")
        vigencia = request.POST.get("vigencia")

        if not id_registro or not id_perfil:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Dato faltante",
                "descripcion": "No se recibió el personal seleccionado."
            })

        if not turno:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Turno no seleccionado",
                "descripcion": "Debe seleccionar un turno."
            })

        if vigencia not in ["DESIGNACION", "REASIGNAR"]:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Acción no válida",
                "descripcion": "La acción solicitada no es válida."
            })

        try:
            id_registro = int(id_registro)
            id_turno = int(turno)
        except (TypeError, ValueError):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Datos inválidos",
                "descripcion": (
                    "El registro o turno seleccionado no es válido."
                )
            })

        try:
            with transaction.atomic():
                # OBTENER REGISTRO SEGÚN EL TIPO DE PERSONAL
                if id_perfil == "SUPERVISOR_ENCARGADO":
                    try:
                        info_perfil = (
                            supervisores_encargados.objects
                            .select_related("id_usuario", "id_turno")
                            .select_for_update()
                            .get(id_supervisor=id_registro)
                        )
                    except supervisores_encargados.DoesNotExist:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "warning",
                            "title": "Perfil no disponible",
                            "descripcion": (
                                "El Supervisor Encargado seleccionado "
                                "no existe."
                            )
                        })

                    modelo = "supervisor"

                elif id_perfil == "PERSONAL_LIMPIEZA":
                    try:
                        info_perfil = (
                            personal_limpieza.objects
                            .select_related("id_usuario", "id_turno")
                            .select_for_update()
                            .get(id_personal=id_registro)
                        )
                    except personal_limpieza.DoesNotExist:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "warning",
                            "title": "Perfil no disponible",
                            "descripcion": (
                                "El Personal de Limpieza seleccionado "
                                "no existe."
                            )
                        })

                    modelo = "limpieza"

                elif id_perfil == "DESPACHADOR":
                    try:
                        info_perfil = (
                            despachadores.objects
                            .select_related("id_usuario", "id_turno")
                            .select_for_update()
                            .get(id_despachador=id_registro)
                        )
                    except despachadores.DoesNotExist:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "warning",
                            "title": "Perfil no disponible",
                            "descripcion": (
                                "El Despachador seleccionado "
                                "no existe."
                            )
                        })

                    modelo = "despachador"

                elif id_perfil == "VIGILANTE":
                    try:
                        info_perfil = (
                            vigilantes.objects
                            .select_related("id_usuario", "id_turno")
                            .select_for_update()
                            .get(id_vigilante=id_registro)
                        )
                    except vigilantes.DoesNotExist:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "warning",
                            "title": "Perfil no disponible",
                            "descripcion": (
                                "El Vigilante seleccionado "
                                "no existe."
                            )
                        })

                    modelo = "vigilante"

                else:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Perfil inválido",
                        "descripcion": (
                            "El tipo de personal seleccionado "
                            "no es válido."
                        )
                    })

                # TURNO
                try:
                    turno_nuevo = turnos_laborales.objects.get(
                        id_turno=id_turno
                    )
                except turnos_laborales.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Turno no disponible",
                        "descripcion": (
                            "El turno seleccionado no existe."
                        )
                    })

                # USUARIO QUE REALIZA LA ACCIÓN
                try:
                    usuario_accion = usuarios.objects.get(
                        cedula_identidad=request.session.get(
                            "cedula_identidad"
                        )
                    )
                except usuarios.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Usuario no disponible",
                        "descripcion": (
                            "No se pudo identificar al usuario "
                            "que realiza la acción."
                        )
                    })

                usuario_afectado = info_perfil.id_usuario

                # NOMBRES DE LOS PERFILES
                nombres_perfiles = {
                    "SUPERVISOR_ENCARGADO": "Supervisor Encargado",
                    "PERSONAL_LIMPIEZA": "Personal de Limpieza",
                    "DESPACHADOR": "Despachador",
                    "VIGILANTE": "Vigilante"
                }

                nombre_perfil = nombres_perfiles[id_perfil]

                # VALIDAR QUE EL EMPLEADO NO TENGA OTRO PERFIL ACTIVO
                if vigencia == "REASIGNAR":

                    # Bloquear los perfiles activos del empleado
                    supervisores_activos = (
                        supervisores_encargados.objects
                        .select_for_update()
                        .filter(
                            id_usuario=usuario_afectado,
                            vigencia=True
                        )
                    )

                    limpiezas_activas = (
                        personal_limpieza.objects
                        .select_for_update()
                        .filter(
                            id_usuario=usuario_afectado,
                            vigencia=True
                        )
                    )

                    despachadores_activos = (
                        despachadores.objects
                        .select_for_update()
                        .filter(
                            id_usuario=usuario_afectado,
                            vigencia=True
                        )
                    )

                    vigilantes_activos = (
                        vigilantes.objects
                        .select_for_update()
                        .filter(
                            id_usuario=usuario_afectado,
                            vigencia=True
                        )
                    )

                    # Determinar cuál perfil activo tiene actualmente
                    perfil_activo = None

                    if supervisores_activos.exists():
                        perfil_activo = "Supervisor Encargado"

                    elif limpiezas_activas.exists():
                        perfil_activo = "Personal de Limpieza"

                    elif despachadores_activos.exists():
                        perfil_activo = "Despachador"

                    elif vigilantes_activos.exists():
                        perfil_activo = "Vigilante"

                    # Si existe cualquier perfil activo,
                    # NO se permite activar/reasignar otro.
                    if perfil_activo:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "warning",
                            "title": "Perfil activo",
                            "descripcion": (
                                f"El empleado ya tiene el perfil "
                                f"{perfil_activo} activo. "
                                "Debe deshabilitarlo antes de "
                                "activar otro perfil."
                            )
                        })

                # VALIDACIÓN ESPECIAL PARA SUPERVISOR
                if modelo == "supervisor" and vigencia == "REASIGNAR":
                    supervisor_ocupado = (
                        supervisores_encargados.objects
                        .select_for_update()
                        .filter(
                            id_turno=turno_nuevo,
                            vigencia=True
                        )
                        .exclude(
                            id_supervisor=info_perfil.id_supervisor
                        )
                        .exists()
                    )

                    if supervisor_ocupado:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "warning",
                            "title": "Turno ocupado",
                            "descripcion": (
                                "El turno seleccionado ya tiene un "
                                "Supervisor Encargado vigente."
                            )
                        })

                # ACTUALIZAR VIGENCIA Y TURNO
                nueva_vigencia = vigencia == "REASIGNAR"

                info_perfil.vigencia = nueva_vigencia
                info_perfil.id_turno = turno_nuevo

                info_perfil.save(
                    update_fields=[
                        "vigencia",
                        "id_turno"
                    ]
                )

                nombres_completos = (
                    f"{usuario_afectado.nombres} "
                    f"{usuario_afectado.apellidos}"
                )

                if nueva_vigencia:
                    descripcion = (
                        f"Se reasignó el perfil "
                        f"{nombre_perfil} al empleado "
                        f"{nombres_completos} "
                        f"en el turno {turno_nuevo.nombre}."
                    )
                else:
                    descripcion = (
                        f"Se deshabilitó el perfil "
                        f"{nombre_perfil} del empleado "
                        f"{nombres_completos}."
                    )

                # BITÁCORA
                bitacora.objects.create(
                    id_usuario=usuario_accion,
                    accion=descripcion
                )

                return JsonResponse({
                    "estado": "exito",
                    "icon": "success",
                    "title": "Éxito",
                    "descripcion": descripcion
                })

        except Exception as e:
            print(e)

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "Ocurrió un error al momento de actualizar "
                    "el perfil."
                )
            })
        
def gestionar_perfiles_empleado(request):
    return render(request, "Modulos/Perfiles/gestionar_perfiles_empleado.html")
