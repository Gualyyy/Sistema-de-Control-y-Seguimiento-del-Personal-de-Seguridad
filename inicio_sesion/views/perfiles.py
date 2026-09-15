from django.db import transaction
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse

from inicio_sesion.models import usuarios, historial_perfiles_usuario, turnos_laborales, perfiles, perfil_usuario, bitacora

from datetime import datetime

import os
from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    KeepTogether
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# PERFILES REGISTRADOS

def perfiles_registrados(request):
    perfiles_registrados = perfiles.objects.exclude(
        perfil="Administrador(a)"
    ).values(
        "id_perfil",
        "perfil"
    )

    return JsonResponse(list(perfiles_registrados), safe=False)

def perfiles_disponibles(request):
    if request.method == "POST":
        turno_seleccionado = request.POST.get("turno")

        # TODOS LOS PERFILES DISPONIBLES
        perfiles_lista = perfiles.objects.exclude(perfil="Administrador(a)")

        # SUPERVISOR ENCARGADO
        supervisor = perfiles.objects.filter(perfil="Supervisor Encargado").first()

        if supervisor and turno_seleccionado:
            try:
                turno_id = int(turno_seleccionado)
            except (TypeError, ValueError):
                turno_id = None

            if turno_id:
                supervisor_ocupado = perfil_usuario.objects.filter(
                    id_perfil=supervisor,
                    id_turno_id=turno_id,
                    vigencia=True
                ).exists()

                if supervisor_ocupado:
                    perfiles_lista = perfiles_lista.exclude(id_perfil=supervisor.id_perfil)

        # PERFILES DISPONIBLES
        datos = [
            {
                "id_perfil": perfil.id_perfil,
                "perfil": perfil.perfil
            }
            for perfil in perfiles_lista
        ]

        return JsonResponse({
            "perfiles": datos
        })

    return JsonResponse({ "perfiles": [] }, status=405)

def turnos_registrados(request):
    turnos_lista = turnos_laborales.objects.exclude(nombre="Sin Turno")

    datos = [
        {
            "id_turno": turno.id_turno,
            "nombre": turno.nombre
        }
        for turno in turnos_lista
    ]
    
    return JsonResponse(datos, safe=False)

# BUSCAR DATOS PERFILES 

def buscar_datos_asignacion(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad", "").strip()
        cedula = request.POST.get("cedula", "").strip()

        if not nacionalidad or not cedula:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": "Debe ingresar la nacionalidad y la cédula.",
                "icon": "warning"
            })

        cedula_completa = f"{nacionalidad}-{cedula}"

        try:
            usuario = usuarios.objects.get(cedula_identidad=cedula_completa)
        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "No se encontró ningún empleado con esa cédula.",
                "icon": "warning"
            })

        perfiles_asignados = perfil_usuario.objects.filter(
            id_usuario=usuario
        ).select_related(
            "id_perfil",
            "id_turno"
        )

        if perfiles_asignados.filter(
            id_perfil__perfil__iexact="Administrador(a)"
        ).exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Acceso no permitido",
                "descripcion": "Datos no permitidos.",
                "icon": "error"
            })

        turnos = list(turnos_laborales.objects.all())

        supervisor = perfiles.objects.filter(
            perfil="Supervisor Encargado"
        ).first()

        perfiles_datos = []

        for perfil_usuario_obj in perfiles_asignados:
            opciones_turnos = []

            if (
                supervisor
                and perfil_usuario_obj.id_perfil_id == supervisor.id_perfil
            ):
                if not perfil_usuario_obj.vigencia:
                    opciones_turnos = [
                        {
                            "id_turno": turno.id_turno,
                            "nombre": turno.nombre
                        }
                        for turno in turnos
                    ]

                else:
                    for turno in turnos:

                        if turno.id_turno == perfil_usuario_obj.id_turno_id:
                            opciones_turnos.append({
                                "id_turno": turno.id_turno,
                                "nombre": turno.nombre
                            })
                            continue

                        supervisor_ocupado = perfil_usuario.objects.filter(
                            id_perfil=supervisor,
                            id_turno=turno,
                            vigencia=True
                        ).exclude(
                            id_perfil_usuario=perfil_usuario_obj.id_perfil_usuario
                        ).exists()

                        if not supervisor_ocupado:
                            opciones_turnos.append({
                                "id_turno": turno.id_turno,
                                "nombre": turno.nombre
                            })

            else:
                opciones_turnos = [
                    {
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    }
                    for turno in turnos
                ]

            perfiles_datos.append({
                "id_perfil_usuario": perfil_usuario_obj.id_perfil_usuario,
                "id_perfil": perfil_usuario_obj.id_perfil.id_perfil,
                "perfil": perfil_usuario_obj.id_perfil.perfil,
                "id_turno": perfil_usuario_obj.id_turno.id_turno,
                "turno": perfil_usuario_obj.id_turno.nombre,
                "vigencia": perfil_usuario_obj.vigencia,
                "turnos": opciones_turnos
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

        perfiles_asignados = perfil_usuario.objects.filter(
            id_usuario_id=id_empleado,
            vigencia=True
        ).values_list(
            "id_perfil_id",
            flat=True
        )

        perfiles_lista = perfiles.objects.exclude(
            perfil="Administrador(a)"
        ).exclude(
            id_perfil__in=perfiles_asignados
        )

        supervisor = perfiles.objects.filter(perfil="Supervisor Encargado").first()
        if supervisor:
            supervisor_usuario = perfil_usuario.objects.filter(
                id_usuario_id=id_empleado,
                id_perfil=supervisor,
                vigencia=True
            ).exists()
            if supervisor_usuario:
                perfiles_lista = perfiles_lista.exclude(id_perfil=supervisor.id_perfil)

            elif turno_seleccionado:
                try:
                    turno_id = int(turno_seleccionado)
                except (TypeError, ValueError):
                    turno_id = None

                if turno_id:
                    supervisor_ocupado = (
                        perfil_usuario.objects.filter(
                            id_perfil=supervisor,
                            id_turno_id=turno_id,
                            vigencia=True
                        ).exists()
                    )

                    if supervisor_ocupado:
                        perfiles_lista = (
                            perfiles_lista.exclude(
                                id_perfil=supervisor.id_perfil
                            )
                        )

        datos = [
            {
                "id_perfil": perfil.id_perfil,
                "perfil": perfil.perfil
            }
            for perfil in perfiles_lista
        ]

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
        ids_perfiles = request.POST.getlist("perfiles")

        if not id_turno:
            return JsonResponse({
                "estado": "error",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Por favor, debes seleccionar el turno laboral."
                )
            })

        if not ids_perfiles:
            return JsonResponse({
                "estado": "error",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Por favor, debes seleccionar al menos un perfil laboral."
                )
            })

        # BUSCAR EMPLEADO Y TURNO
        try:
            usuario = usuarios.objects.get(id_usuario=id_empleado)
        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "error",
                "icon": "error",
                "title": "Usuario no encontrado",
                "descripcion": "El usuario seleccionado no existe."
            })

        try:
            turno = turnos_laborales.objects.get(id_turno=id_turno)
        except turnos_laborales.DoesNotExist:
            return JsonResponse({
                "estado": "error",
                "icon": "error",
                "title": "Turno no encontrado",
                "descripcion": "El turno seleccionado no existe."
            })

        # BUSCAR PERFILES
        perfiles_seleccionados = perfiles.objects.filter(
            id_perfil__in=ids_perfiles
        ).exclude(
            perfil="Administrador(a)"
        )

        if perfiles_seleccionados.count() != len(set(ids_perfiles)):
            return JsonResponse({
                "estado": "error",
                "icon": "error",
                "title": "Perfil no encontrado",
                "descripcion": (
                    "Uno o más de los perfiles seleccionados "
                    "no son válidos."
                )
            })

        # VALIDAR ASIGNACIONES EXISTENTES
        asignaciones_existentes = perfil_usuario.objects.filter(
            id_usuario=usuario,
            id_perfil__in=ids_perfiles,
            vigencia=True
        ).select_related("id_perfil", "id_turno")

        if asignaciones_existentes.exists():

            perfiles_existentes = ", ".join(
                asignacion.id_perfil.perfil
                for asignacion in asignaciones_existentes
            )

            return JsonResponse({
                "estado": "error",
                "icon": "warning",
                "title": "Perfil ya asignado",
                "descripcion": (
                    f"El empleado ya tiene asignado el perfil: "
                    f"{perfiles_existentes}."
                )
            })

        # REGISTRAR ASIGNACIONES
        try:
            with transaction.atomic():

                usuario_accion = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )

                nombres_perfiles = []

                for perfil in perfiles_seleccionados:

                    perfil_usuario.objects.create(
                        id_perfil=perfil,
                        id_usuario=usuario,
                        id_turno=turno,
                        vigencia=True
                    )

                    historial_perfiles_usuario.objects.create(
                        id_usuario=usuario,
                        id_perfil=perfil,
                        id_turno=turno,
                        accion="ASIGNACION"
                    )

                    nombres_perfiles.append(perfil.perfil)

                # BITÁCORA
                perfiles_texto = ", ".join(nombres_perfiles)

                bitacora.objects.create(
                    id_usuario=usuario_accion,
                    accion=(
                        f"Se asignaron los perfiles {perfiles_texto} "
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
                    "Se registraron los perfiles "
                    "exitosamente."
                )
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": f"Ocurrió un error: {e}."
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

    # CANTIDAD TOTAL DE PERFILES ASIGNABLES
    cantidad_perfiles = perfiles.objects.exclude(perfil="Administrador(a)").count()

    # CANTIDAD DE PERFILES ASIGNADOS AL EMPLEADO
    cantidad_asignados = perfil_usuario.objects.filter(
        id_usuario_id=id_empleado,
        vigencia=True
    ).values(
        "id_perfil"
    ).distinct().count()

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

    # Todavía puede asignarse otro perfil
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

    perfiles_asignados = perfil_usuario.objects.filter(
        id_usuario_id=id_empleado
    ).select_related(
        "id_perfil",
        "id_turno"
    )

    turnos = list(turnos_laborales.objects.all())

    supervisor = perfiles.objects.filter(perfil="Supervisor Encargado").first()

    datos = []
    for asignacion in perfiles_asignados:
        opciones_turnos = []

        if (supervisor and asignacion.id_perfil_id == supervisor.id_perfil):
            if not asignacion.vigencia:

                opciones_turnos = [
                    {
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    }
                    for turno in turnos
                ]

            else:
                for turno in turnos:
                    if (turno.id_turno == asignacion.id_turno_id):

                        opciones_turnos.append({
                            "id_turno": turno.id_turno,
                            "nombre": turno.nombre
                        })

                        continue

                    supervisor_ocupado = (
                        perfil_usuario.objects.filter(
                            id_perfil=supervisor,
                            id_turno=turno,
                            vigencia=True
                        )
                        .exclude(
                            id_perfil_usuario=
                            asignacion.id_perfil_usuario
                        )
                        .exists()
                    )
                    
                    if not supervisor_ocupado:
                        opciones_turnos.append({
                            "id_turno": turno.id_turno,
                            "nombre": turno.nombre
                        })

        else:
            opciones_turnos = [
                {
                    "id_turno": turno.id_turno,
                    "nombre": turno.nombre
                }
                for turno in turnos
            ]

        datos.append({
            "id_perfil_usuario":
                asignacion.id_perfil_usuario,
            "id_perfil":
                asignacion.id_perfil.id_perfil,
            "perfil":
                asignacion.id_perfil.perfil,
            "id_turno": (
                asignacion.id_turno.id_turno
                if asignacion.id_turno
                else None
            ),
            "turno": (
                asignacion.id_turno.nombre
                if asignacion.id_turno
                else "Sin turno asignado"
            ),
            "vigencia":
                asignacion.vigencia,

            "turnos":
                opciones_turnos
        })


    return JsonResponse({
        "estado": "exito",
        "perfiles": datos
    })

#  DETALLES PERFILES ASIGNADO

def buscar_datos_perfil(request):
    if request.method == "POST":
        id_perfil_usuario = request.POST.get("id_perfil_usuario")

        if not id_perfil_usuario:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Dato faltante",
                "descripcion": "No se recibió el perfil seleccionado."
            })

        try:
            info_perfil = perfil_usuario.objects.select_related(
                "id_usuario",
                "id_perfil",
                "id_turno"
            ).get(
                id_perfil_usuario=id_perfil_usuario
            )

            return JsonResponse({
                "estado": "exito",
                "id_perfil_usuario": info_perfil.id_perfil_usuario,
                "id_turno":  info_perfil.id_turno.id_turno,
                "turno":  info_perfil.id_turno.nombre,
                "vigencia": info_perfil.vigencia
            })

        except perfil_usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no disponible",
                "descripcion": "El perfil seleccionado no existe."
            })

# ACTUALIZAR PERFILES ASIGNADOS

def actualizar_vigencia_perfil(request):
    if request.method == "POST":
        id_perfil_asignado = request.POST.get("id_perfil_asignado")
        turno = request.POST.get("actualizar_turno")
        vigencia = request.POST.get("vigencia")

        if not id_perfil_asignado:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Dato faltante",
                "descripcion": "No se recibió el perfil seleccionado."
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
            with transaction.atomic():

                info_perfil = perfil_usuario.objects.select_related(
                    "id_usuario",
                    "id_perfil",
                    "id_turno"
                ).get(
                    id_perfil_usuario=id_perfil_asignado
                )

                turno_nuevo = turnos_laborales.objects.get(
                    id_turno=turno
                )

                usuario_accion = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )

                usuario_afectado = info_perfil.id_usuario

                # La acción determina la vigencia
                nueva_vigencia = vigencia == "REASIGNAR"

                info_perfil.vigencia = nueva_vigencia
                info_perfil.id_turno = turno_nuevo

                info_perfil.save(
                    update_fields=[
                        "vigencia",
                        "id_turno"
                    ]
                )

                if nueva_vigencia:
                    descripcion = (
                        f"Se reasignó el perfil "
                        f"{info_perfil.id_perfil.perfil} "
                        f"al empleado "
                        f"{usuario_afectado.nombres} "
                        f"{usuario_afectado.apellidos} "
                        f"en el turno {turno_nuevo.nombre}."
                    )
                else:
                    descripcion = (
                        f"Se deshabilitó el perfil "
                        f"{info_perfil.id_perfil.perfil} "
                        f"del empleado "
                        f"{usuario_afectado.nombres} "
                        f"{usuario_afectado.apellidos}."
                    )

                historial_perfiles_usuario.objects.create(
                    id_usuario=info_perfil.id_usuario,
                    id_perfil=info_perfil.id_perfil,
                    id_turno=turno_nuevo,
                    accion=vigencia
                )

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

        except perfil_usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no disponible",
                "descripcion": "El perfil seleccionado no existe."
            })

        except turnos_laborales.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Turno no disponible",
                "descripcion": "El turno seleccionado no existe."
            })

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
    return render(request, "Modulos/gestionar_perfiles_empleado.html")

# HISTORIAL DE GESTIÓN DE PERFILES

def fechas_historial_asignaciones(request):
    fechas = (
        historial_perfiles_usuario.objects
        .values_list("fecha_accion__date", flat=True)
        .distinct()
        .order_by("-fecha_accion__date")
    )

    return JsonResponse({
        "estado": "exito",
        "fechas": [
            {
                "valor": fecha.strftime("%Y-%m-%d"),
                "texto": fecha.strftime("%d/%m/%Y")
            }
            for fecha in fechas
        ]
    })

def historial_perfiles(request):
    if request.method == "POST":
        fecha = request.POST.get("fecha")
        perfil = request.POST.get("perfil")

        historial = historial_perfiles_usuario.objects.select_related(
            "id_usuario",
            "id_perfil",
            "id_turno"
        ).order_by("-fecha_accion")

        if fecha:
            historial = historial.filter(
                fecha_accion__date=fecha
            )

        if perfil:
            historial = historial.filter(
                id_perfil=perfil
            )

        datos = [
            {
                "id_historial": registro.id_historial,
                "usuario": (
                    f"{registro.id_usuario.nombres} "
                    f"{registro.id_usuario.apellidos}"
                ),
                "perfil": registro.id_perfil.perfil,
                "turno": registro.id_turno.nombre,
                "accion": registro.get_accion_display(),
                "fecha_accion": registro.fecha_accion.strftime(
                    "%d/%m/%Y %H:%M:%S"
                ),
            }
            for registro in historial
        ]

        return JsonResponse({
            "estado": "exito",
            "historial": datos
        })

    return render(request, "Modulos/historial_gestiones_perfiles.html")

# REPORTE DE TODOS HISTORIAL DE ASIGNACIONES PERFILES

def lista_historial_perfiles_pdf(request):
    fecha = request.POST.get("fecha", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    historial = historial_perfiles_usuario.objects.select_related(
        "id_usuario",
        "id_perfil",
        "id_turno"
    ).order_by("-fecha_accion")

    if fecha:
        historial = historial.filter(
            fecha_accion__date=fecha
        )

    if perfil:
        historial = historial.filter(
            id_perfil=perfil
        )

    datos = [
        {
            "id_historial": registro.id_historial,
            "usuario": (
                f"{registro.id_usuario.nombres} "
                f"{registro.id_usuario.apellidos}"
            ),
            "perfil": registro.id_perfil.perfil,
            "turno": registro.id_turno.nombre,
            "accion": registro.get_accion_display(),
            "fecha_accion": registro.fecha_accion.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
        }
        for registro in historial
    ]

    # RESPUESTA PDF
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = ('inline; filename="historial_perfiles.pdf"')

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

    # DATOS DE LA TABLA
    datos_tabla = [
        # ENCABEZADO PRINCIPAL
        ["HISTORIAL DE GESTIONES DE PERFILES", "", "", "", "",],
        # ENCABEZADO DE COLUMNAS
        ["N.º", "Empleado", "Perfil", "Turno Laboral", "Estado", "Fecha",],
    ]

    # REGISTROS
    for numero, dato in enumerate(datos, start=1):
        datos_tabla.append([
            numero,
            dato["usuario"],
            dato["perfil"],
            dato["turno"],
            dato["accion"],
            dato["fecha_accion"],
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[
            30,
            140,
            80,
            70,
            60,
            100
        ],
        repeatRows=2
    )

    # ESTILOS DE TABLA
    tabla.setStyle(TableStyle([
        # ENCABEZADO PRINCIPAL
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        # ENCABEZADO DE COLUMNAS
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        # CONTENIDO
        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 9),
        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        # BORDES
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # ESPACIADO
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos = [
        tabla
    ]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_historial_perfiles_pdf(
                canvas,
                documento,
                ruta_logo
            ),

        onLaterPages=lambda canvas, documento:
            encabezado_historial_perfiles_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_historial_perfiles_pdf(canvas, documento, ruta_logo):
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
