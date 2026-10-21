from importlib import import_module
from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from inicio_sesion.models import sesiones_usuario

class RequerirSesionMiddleware:
    rutas_publicas = (
        "/",
        "/inicio_sesion/",
        "/modo_incognito/",
        "/historia/",
        "/quienes_somos/",
        "/contactanos/",
        "/cerrar_sesion/",
    )
    prefijos_publicos = ("/admin/", "/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

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

        if usa_sesion_pestana:
            session_store_class = import_module(settings.SESSION_ENGINE).SessionStore
            sesion_guardada = sesiones_usuario.objects.filter(
                tab_id=tab_id,
                activa=True,
            ).only("session_key").first() if tab_id else None
            request.session = session_store_class(
                session_key=sesion_guardada.session_key if sesion_guardada else None
            )

        try:
            if ruta_publica or request.session.get("usuario"):
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

            if (
                usa_sesion_pestana
                and tab_id
                and request.session.session_key
                and (settings.SESSION_SAVE_EVERY_REQUEST or request.session.modified)
            ):
                request.session.save()

            if not request.path.startswith(("/static/", "/media/")):
                response["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response["Pragma"] = "no-cache"
                response["Expires"] = "0"

            return self._agregar_tab_id_a_redireccion(response, tab_id)
        finally:
            request.session = session_original