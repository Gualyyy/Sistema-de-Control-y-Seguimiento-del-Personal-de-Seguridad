from importlib import import_module
from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.contrib.sessions.backends.base import UpdateError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve
from django.utils import timezone

from inicio_sesion.models import sesiones_recuperacion, sesiones_usuario


class RequerirSesionMiddleware:
    rutas_publicas = (
        "/",
        "/inicio_sesion/",
        "/menu_acceso/",
        "/buscar_usuario/",
        "/enviar_codigo/",
        "/reenviar_codigo/",
        "/vigencia_codigo/",
        "/correos_usuario/",
        "/verificar_codigo/",
        "/enviar_usuario/",
        "/menu_recuperar_credenciales/",
        "/cambiar_contrasenia/",
        "/recuperar_nombre_usuario/",
        "/registrar_credenciales/",
        "/empleado_sin_credenciales/",
        "/validar_patron_contrasenia/",
        "/validar_identificador/",
        "/validar_email/",
        "/validar_nombre_usuario/",
        "/validar_contrasenia/",
        "/validar_telefono/",
        "/historia/",
        "/quienes_somos/",
        "/contactanos/",
        "/control_asistencia/",
        "/datos_contacto_foro/",
        "/registrar_clientes_foro/",
        "/ventas/productos_exhibicion/",
        "/cerrar_sesion/",
        "/validar_reporte_qr/",
    )
    rutas_sesion_recuperacion = (
        "/buscar_usuario/",
        "/enviar_codigo/",
        "/reenviar_codigo/",
        "/vigencia_codigo/",
        "/correos_usuario/",
        "/verificar_codigo/",
        "/enviar_usuario/",
        "/menu_recuperar_credenciales/",
        "/cambiar_contrasenia/",
        "/recuperar_nombre_usuario/",
    )
    rutas_verificacion_recuperacion = frozenset({
        "/verificar_codigo/",
        "/vigencia_codigo/",
        "/reenviar_codigo/",
        "/correos_usuario/",
    })
    rutas_cambio_contrasenia = frozenset({
        "/cambiar_contrasenia/",
        "/validar_contrasenia/",
        "/validar_patron_contrasenia/",
    })
    rutas_recuperar_usuario = frozenset({
        "/recuperar_nombre_usuario/",
        "/enviar_usuario/",
    })
    prefijos_publicos = ("/admin/", "/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def _desactivar_sesion_expirada(self, sesion_guardada):
        if sesion_guardada:
            sesiones_usuario.objects.filter(
                pk=sesion_guardada.pk,
                activa=True,
            ).update(activa=False, fecha_fin=timezone.now())

    def _obtener_tab_id(self, request):
        tab_id = (
            request.headers.get("X-Tab-ID")
            or request.GET.get("tab_id")
        )

        if not tab_id and request.method == "POST":
            tab_id = request.POST.get("tab_id")

            if not tab_id:
                referer = request.headers.get("Referer")
                if referer:
                    partes = urlsplit(referer)
                    if partes.netloc.lower() == request.get_host().lower():
                        tab_id = parse_qs(partes.query).get("tab_id", [None])[0]

        if tab_id:
            return tab_id[:100]
        return None

    def _validar_etapa_recuperacion(self, request):
        session = request.session
        if not session.get("usuario_credenciales"):
            return None

        ruta = request.path
        destino = session.get("recuperacion_destino")

        if destino == "contrasenia":
            if ruta in self.rutas_cambio_contrasenia:
                return None
            return "/cambiar_contrasenia/"

        if destino == "usuario":
            if ruta in self.rutas_recuperar_usuario:
                return None
            return "/recuperar_nombre_usuario/"

        if session.get("recuperacion_codigo_verificado"):
            if ruta == "/cambiar_contrasenia/":
                session["recuperacion_destino"] = "contrasenia"
                return None

            if ruta == "/recuperar_nombre_usuario/" or (
                ruta == "/enviar_usuario/" and request.method == "POST"
            ):
                session["recuperacion_destino"] = "usuario"
                return None

            if ruta == "/menu_recuperar_credenciales/":
                return None

            return "/menu_recuperar_credenciales/"

        if session.get("recuperacion_codigo_enviado"):
            if ruta in self.rutas_verificacion_recuperacion:
                return None
            return "/verificar_codigo/"

        return None

    def _agregar_tab_id_a_redireccion(self, response, tab_id):
        if not tab_id or response.status_code not in (301, 302, 303, 307, 308):
            return response

        partes = urlsplit(response.get("Location", ""))
        if partes.scheme or partes.netloc or partes.path.startswith(self.prefijos_publicos):
            return response

        parametros = dict(parse_qsl(partes.query, keep_blank_values=True))
        parametros.setdefault("tab_id", tab_id)
        response["Location"] = urlunsplit((
            partes.scheme,
            partes.netloc,
            partes.path,
            urlencode(parametros),
            partes.fragment,
        ))
        return response

    def __call__(self, request):
        session_original = request.session
        ruta_publica = (
            request.path in self.rutas_publicas
            or request.path.startswith(self.prefijos_publicos)
        )

        usa_sesion_pestana = not request.path.startswith(self.prefijos_publicos)
        tab_id = self._obtener_tab_id(request) if usa_sesion_pestana else None
        request.tab_id = tab_id
        sesion_guardada = None
        sesion_recuperacion = None

        if usa_sesion_pestana:
            session_store_class = import_module(settings.SESSION_ENGINE).SessionStore
            sesion_guardada = sesiones_usuario.objects.filter(
                tab_id=tab_id,
                activa=True,
            ).only("session_key").first() if tab_id else None
            if tab_id and not sesion_guardada:
                sesion_recuperacion = sesiones_recuperacion.objects.filter(
                    tab_id=tab_id,
                ).only("session_key").first()

            session_key = None
            if sesion_guardada:
                session_key = sesion_guardada.session_key
            elif sesion_recuperacion:
                session_key = sesion_recuperacion.session_key

            request.session = session_store_class(
                session_key=session_key
            )

            if (
                sesion_guardada
                and not request.session.exists(sesion_guardada.session_key)
            ):
                self._desactivar_sesion_expirada(sesion_guardada)
                sesion_guardada = None
                request.session = session_store_class(session_key=None)

            if (
                sesion_recuperacion
                and not request.session.exists(sesion_recuperacion.session_key)
            ):
                sesion_recuperacion.delete()
                sesion_recuperacion = None
                request.session = session_store_class(session_key=None)

        try:
            ruta_recuperacion = (
                self._validar_etapa_recuperacion(request)
                if usa_sesion_pestana
                else None
            )
            if ruta_recuperacion:
                response = redirect(ruta_recuperacion)
            elif ruta_publica or request.session.get("usuario"):
                response = self.get_response(request)
            else:
                try:
                    ruta = resolve(request.path_info)
                except Resolver404:
                    response = self.get_response(request)
                    return self._agregar_tab_id_a_redireccion(response, tab_id)

                if ruta.url_name == "ruta_no_encontrada":
                    response = self.get_response(request)
                else:
                    modo_fetch = request.headers.get("Sec-Fetch-Mode")
                    es_peticion_ajax = (
                        request.headers.get("X-Requested-With") == "XMLHttpRequest"
                        or (modo_fetch and modo_fetch != "navigate")
                    )

                    if es_peticion_ajax:
                        response = JsonResponse({
                            "estado": "fallo",
                            "title": "Sesión requerida",
                            "descripcion": "Inicie sesión para acceder a este módulo.",
                            "icon": "warning",
                        }, status=401)
                    else:
                        response = redirect("inicio_sesion")
                    response["Cache-Control"] = "no-store"

            if sesion_recuperacion and not request.session.get(
                "usuario_credenciales"
            ):
                for clave in (
                    "recuperacion_codigo_enviado",
                    "recuperacion_codigo_verificado",
                    "recuperacion_destino",
                ):
                    request.session.pop(clave, None)

                sesiones_recuperacion.objects.filter(
                    tab_id=tab_id
                ).delete()

            if (
                usa_sesion_pestana
                and tab_id
                and (request.session.session_key or request.session.modified)
                and (settings.SESSION_SAVE_EVERY_REQUEST or request.session.modified)
            ):
                try:
                    request.session.save()
                except UpdateError:
                    session_key = request.session.session_key
                    if (
                        request.session.modified
                        or not session_key
                        or request.session.exists(session_key)
                    ):
                        raise
                    self._desactivar_sesion_expirada(sesion_guardada)

                if (
                    request.path in self.rutas_sesion_recuperacion
                    and not sesion_guardada
                    and request.session.get("usuario_credenciales")
                    and request.session.session_key
                ):
                    sesiones_recuperacion.objects.update_or_create(
                        tab_id=tab_id,
                        defaults={"session_key": request.session.session_key},
                    )

            if not request.path.startswith(("/static/", "/media/")):
                response["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response["Pragma"] = "no-cache"
                response["Expires"] = "0"

            return self._agregar_tab_id_a_redireccion(response, tab_id)
        finally:
            request.session = session_original