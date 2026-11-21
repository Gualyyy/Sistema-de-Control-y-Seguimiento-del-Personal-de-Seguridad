import json
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.sessions.backends.db import SessionStore
from django.core.signing import TimestampSigner
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from inicio_sesion.models import (
    autenticar_codigo,
    atencion_cliente,
    bitacora,
    bloqueo_inicio_sesion,
    cliente,
    contacto,
    credenciales,
    despachadores,
    encargados_administrativos,
    intentos_inicio_sesion,
    nacimiento,
    personal_limpieza,
    propietarios,
    residencia,
    sesiones_recuperacion,
    sesiones_usuario,
    supervisores_encargados,
    turnos_laborales,
    usuarios,
    vigilantes,
)
from inicio_sesion.views.autenticacion import obtener_rol
from inicio_sesion.views.encargado_administrativo import (
    actualizar_administrador,
    registrar_administrador,
)
from inicio_sesion.views.empleados import actualizacion_datos_usuarios
from inicio_sesion.views.perfiles import (
    cantidad_perfiles_asignado,
    perfiles_usuario_no_registrados,
    registrar_nueva_asignacion,
)


class ProteccionDeVistasTest(TestCase):
    def crear_sesion_pestana(self, usuario, tab_id, datos):
        session = SessionStore()
        session.update(datos)
        session["tab_id"] = tab_id
        session.save()

        sesiones_usuario.objects.create(
            usuario=usuario,
            session_key=session.session_key,
            tab_id=tab_id,
            activa=True,
            info_general="test-agent",
            direccion_ip="127.0.0.1",
        )
        return session.session_key

    def test_modulos_requieren_sesion(self):
        response = self.client.get(reverse("registros_equipos"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("inicio_sesion"))

    def test_fetch_sin_sesion_recibe_401_json(self):
        response = self.client.get(
            reverse("tipos_incidencias"),
            HTTP_SEC_FETCH_MODE="cors",
            HTTP_SEC_FETCH_DEST="empty",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["estado"], "fallo")
        self.assertEqual(response.json()["title"], "Sesión requerida")

    def test_endpoint_mantener_sesion_eliminado(self):
        response = self.client.post("/mantener_sesion/")

        self.assertEqual(response.status_code, 404)

    def test_inicio_sesion_sigue_publico(self):
        response = self.client.get(reverse("inicio_sesion"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="mensaje_autenticacion"')
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertEqual(response["Pragma"], "no-cache")
        self.assertEqual(response["Expires"], "0")

    def test_menu_acceso_sigue_publico(self):
        with patch(
            "inicio_sesion.views.autenticacion.render",
            return_value=HttpResponse("ok"),
        ):
            response = self.client.get(reverse("menu_acceso"))

        self.assertEqual(response.status_code, 200)

    def test_buscar_usuario_sigue_publico(self):
        response = self.client.get(reverse("buscar_usuario"))

        self.assertEqual(response.status_code, 200)

    def test_buscar_usuario_guarda_la_cedula_en_sesion_por_pestana(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Recuperación",
            cedula_identidad="V-1234567",
            genero="Masculino",
            estado_civil="Soltero",
        )
        propietarios.objects.create(id_usuario=usuario)
        credenciales.objects.create(
            id_usuario=usuario,
            nombre_usuario="usuario_recuperacion",
            clave=make_password("clave-original"),
        )
        contacto.objects.create(
            telefono_principal="04121234567",
            correo_principal="usuario@example.com",
            id_usuario=usuario,
        )

        tab_id = "tab-recuperacion"
        response_busqueda = self.client.post(
            reverse("buscar_usuario"),
            {"nacionalidad": "V", "num_cedula": "1234567"},
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response_busqueda.status_code, 200)
        self.assertEqual(response_busqueda.json()["estado"], "exito")
        self.assertTrue(
            sesiones_recuperacion.objects.filter(tab_id=tab_id).exists()
        )

        response_cambio_sin_verificar = self.client.post(
            reverse("cambiar_contrasenia"),
            {
                "contrasenia": "clave-nueva",
                "contrasenia_confirmar": "clave-nueva",
            },
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response_cambio_sin_verificar.status_code, 200)
        self.assertEqual(
            response_cambio_sin_verificar.json()["title"],
            "Verificación requerida",
        )

        response_correos = self.client.get(
            reverse("correos_usuario"),
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response_correos.status_code, 200)
        self.assertEqual(response_correos.json()["estado"], "exito")
        self.assertEqual(
            response_correos.json()["correo_principal"],
            "usuario@example.com",
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_cliente_puede_recuperar_su_contrasenia(self):
        usuario = usuarios.objects.create(
            nombres="Cliente",
            apellidos="Recuperación",
            cedula_identidad="V-7654321",
            genero="Masculino",
            estado_civil="Soltero",
        )
        cliente.objects.create(id_usuario=usuario)
        credenciales.objects.create(
            id_usuario=usuario,
            nombre_usuario="cliente_recuperacion",
            clave=make_password("clave-original"),
        )
        contacto.objects.create(
            telefono_principal="04121234567",
            correo_principal="cliente@example.com",
            id_usuario=usuario,
        )

        tab_id = "tab-recuperacion-cliente"
        response_busqueda = self.client.post(
            reverse("buscar_usuario"),
            {"nacionalidad": "V", "num_cedula": "7654321"},
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response_busqueda.status_code, 200)
        self.assertEqual(response_busqueda.json()["estado"], "exito")

        response_correos = self.client.get(
            reverse("correos_usuario"),
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response_correos.status_code, 200)
        self.assertEqual(response_correos.json()["estado"], "exito")
        self.assertEqual(
            response_correos.json()["correo_principal"],
            "cliente@example.com",
        )

        response_codigo = self.client.post(
            reverse("enviar_codigo"),
            {"correo_seleccionado": "cliente@example.com"},
            HTTP_X_TAB_ID=tab_id,
        )
        self.assertEqual(response_codigo.json()["estado"], "exito")

        codigo = autenticar_codigo.objects.get(
            cedula_identidad=usuario.cedula_identidad,
            activo=True,
        )
        response_verificacion = self.client.post(
            reverse("verificar_codigo"),
            {"codigo_recibido": codigo.codigo},
            HTTP_X_TAB_ID=tab_id,
        )
        self.assertEqual(response_verificacion.json()["estado"], "exito")

        response_cambio = self.client.post(
            reverse("cambiar_contrasenia"),
            {
                "contrasenia": "ClaveNueva#2026",
                "contrasenia_confirmar": "ClaveNueva#2026",
            },
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response_cambio.json()["estado"], "exito")
        usuario.credenciales.refresh_from_db()
        self.assertTrue(
            check_password(
                "ClaveNueva#2026",
                usuario.credenciales.clave,
            )
        )

    def test_verificar_codigo_sigue_publico(self):
        response = self.client.get(reverse("verificar_codigo"))

        self.assertEqual(response.status_code, 200)

    def test_encabezado_muestra_marca_sin_navegacion_durante_recuperacion(self):
        for indice, nombre_url in enumerate((
            "verificar_codigo",
            "menu_recuperar_credenciales",
            "cambiar_contrasenia",
            "recuperar_nombre_usuario",
        )):
            with self.subTest(nombre_url=nombre_url):
                session = SessionStore()
                session["usuario_credenciales"] = "V-1234567"
                if nombre_url == "verificar_codigo":
                    session["recuperacion_codigo_enviado"] = True
                else:
                    session["recuperacion_codigo_verificado"] = True
                session.save()
                tab_id = f"tab-encabezado-recuperacion-{indice}"
                sesiones_recuperacion.objects.create(
                    tab_id=tab_id,
                    session_key=session.session_key,
                )

                response = self.client.get(
                    reverse(nombre_url),
                    HTTP_X_TAB_ID=tab_id,
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'data-recovery-active="true"')
                self.assertContains(
                    response,
                    '<header class="header-logueado">',
                )
                self.assertNotContains(response, 'class="nav-foro"')
                if nombre_url == "verificar_codigo":
                    self.assertContains(
                        response,
                        'data-recovery-step="verificacion"',
                    )

                if nombre_url == "recuperar_nombre_usuario":
                    session = SessionStore(
                        session_key=session.session_key
                    )
                    del session["usuario_credenciales"]
                    session.save()

                    response = self.client.get(
                        reverse("recuperar_nombre_usuario"),
                        HTTP_X_TAB_ID=tab_id,
                    )

                    self.assertContains(
                        response,
                        '<header class="header-logueado">',
                    )
                    self.assertContains(response, 'class="nav-foro"')
                    self.assertContains(
                        response,
                        'data-recovery-active="false"',
                    )

    def test_middleware_limita_la_navegacion_a_la_etapa_de_recuperacion(self):
        session = SessionStore()
        session["usuario_credenciales"] = "V-1234567"
        session["recuperacion_codigo_enviado"] = True
        session.save()
        tab_id = "tab-etapa-verificacion"
        sesiones_recuperacion.objects.create(
            tab_id=tab_id,
            session_key=session.session_key,
        )

        response = self.client.get(
            reverse("buscar_usuario"),
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("verificar_codigo")))
        self.assertIn("no-store", response["Cache-Control"])

        response_post = self.client.post(
            reverse("buscar_usuario"),
            {"nacionalidad": "V", "num_cedula": "1234567"},
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(
            response_post.url.startswith(reverse("verificar_codigo"))
        )

        session = SessionStore(session_key=session.session_key)
        self.assertEqual(
            session.get("usuario_credenciales"),
            "V-1234567",
        )
        self.assertTrue(session.get("recuperacion_codigo_enviado"))

        response_url_incompleta = self.client.get(
            f"/verificar_cod/?tab_id={tab_id}",
        )
        self.assertEqual(response_url_incompleta.status_code, 302)
        self.assertTrue(
            response_url_incompleta.url.startswith(
                reverse("verificar_codigo")
            )
        )

        response = self.client.get(
            reverse("verificar_codigo"),
            HTTP_X_TAB_ID=tab_id,
        )
        self.assertEqual(response.status_code, 200)

        session = SessionStore(session_key=session.session_key)
        session["recuperacion_codigo_verificado"] = True
        session.save()

        response = self.client.get(
            reverse("verificar_codigo"),
            HTTP_X_TAB_ID=tab_id,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("menu_recuperar_credenciales"))
        )

        for indice, (ruta_elegida, ruta_alternativa) in enumerate((
            ("cambiar_contrasenia", "recuperar_nombre_usuario"),
            ("recuperar_nombre_usuario", "cambiar_contrasenia"),
        )):
            with self.subTest(ruta_elegida=ruta_elegida):
                session = SessionStore()
                session["usuario_credenciales"] = "V-1234567"
                session["recuperacion_codigo_verificado"] = True
                session.save()
                tab_id = f"tab-rama-recuperacion-{indice}"
                sesiones_recuperacion.objects.create(
                    tab_id=tab_id,
                    session_key=session.session_key,
                )

                response = self.client.get(
                    reverse(ruta_elegida),
                    HTTP_X_TAB_ID=tab_id,
                )
                self.assertEqual(response.status_code, 200)

                for ruta_bloqueada in (
                    "menu_recuperar_credenciales",
                    ruta_alternativa,
                    "inicio_sesion",
                ):
                    response = self.client.get(
                        reverse(ruta_bloqueada),
                        HTTP_X_TAB_ID=tab_id,
                    )
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(
                        response.url.startswith(reverse(ruta_elegida))
                    )

    def test_enviar_usuario_desde_menu_selecciona_rama_y_devuelve_json(self):
        session = SessionStore()
        session["usuario_credenciales"] = "V-1234567"
        session["recuperacion_codigo_verificado"] = True
        session.save()
        tab_id = "tab-enviar-usuario-desde-menu"
        sesiones_recuperacion.objects.create(
            tab_id=tab_id,
            session_key=session.session_key,
        )

        response = self.client.post(
            reverse("enviar_usuario"),
            HTTP_X_TAB_ID=tab_id,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json()["title"],
            "Correo electrónico no disponible",
        )

        session = SessionStore(session_key=session.session_key)
        self.assertEqual(session.get("recuperacion_destino"), "usuario")

    def test_validar_patron_contrasenia_sigue_publico(self):
        response = self.client.post(reverse("validar_patron_contrasenia"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["estado"], "fallo")
        self.assertEqual(response.json()["title"], "Datos incompletos")

    def test_validaciones_de_registro_son_publicas(self):
        for nombre_url in (
            "validar_identificador",
            "validar_email",
            "validar_nombre_usuario",
            "validar_contrasenia",
            "validar_telefono",
        ):
            with self.subTest(nombre_url=nombre_url):
                response = self.client.post(reverse(nombre_url))
                self.assertEqual(response.status_code, 200)

    def test_paginas_del_foro_siguen_publicas(self):
        for nombre_url in ("foro", "historia", "quienes_somos", "contactanos"):
            with self.subTest(nombre_url=nombre_url):
                response = self.client.get(
                    reverse(nombre_url),
                    {"tab_id": f"tab-publica-{nombre_url}"},
                )
                self.assertEqual(response.status_code, 200)

    def test_datos_contacto_foro_sigue_publico(self):
        response = self.client.get(reverse("datos_contacto_foro"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["estado"], ("exito", "fallo"))

    def test_registrar_clientes_foro_sigue_publico(self):
        response = self.client.get(reverse("registrar_clientes_foro"))

        self.assertEqual(response.status_code, 200)

    def test_inicio_sesion_redirige_al_panel_con_sesion_activa(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Prueba",
            cedula_identidad="10000002",
            genero="Masculino",
            estado_civil="Soltero",
        )
        self.crear_sesion_pestana(usuario, "tab-login-activa", {
            "usuario": "Usuario Prueba",
        })

        response = self.client.get(
            reverse("inicio_sesion"),
            HTTP_X_TAB_ID="tab-login-activa",
            HTTP_REFERER="http://testserver/?tab_id=tab-login-activa",
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("panel_usuario")))
        self.assertIn("no-store", response["Cache-Control"])

    def test_tab_id_sin_registro_no_reutiliza_sesion_cookie(self):
        session = self.client.session
        session["usuario"] = "Usuario de prueba"
        session.save()

        response = self.client.get(reverse("inicio_sesion"), {
            "tab_id": "pestana-nueva",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="formulario_autenticacion"')
        self.assertContains(response, "Sistema de Control y Seguimiento")
        self.assertContains(response, "Todos los derechos reservados 2026")
        self.assertNotContains(response, "Gestión de Empleados")

    def test_post_publico_no_falla_si_la_sesion_de_la_pestana_expira(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Prueba",
            cedula_identidad="10000011",
            genero="Masculino",
            estado_civil="Soltero",
        )
        tab_id = "tab-sesion-expirada"
        session_key = self.crear_sesion_pestana(usuario, tab_id, {})
        SessionStore(session_key=session_key).delete(session_key)

        response = self.client.post(
            reverse("empleado_sin_credenciales"),
            {},
            HTTP_X_TAB_ID=tab_id,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Campo vacío")
        self.assertFalse(
            sesiones_usuario.objects.get(tab_id=tab_id).activa
        )

    def test_cookie_de_otra_pestana_no_permite_acceder_al_panel(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Protegido",
            cedula_identidad="10000010",
            genero="Masculino",
            estado_civil="Soltero",
        )
        tab_id_autorizado = "tab-autorizado"
        token = TimestampSigner(salt="panel-route").sign("panel")
        session_key = self.crear_sesion_pestana(
            usuario,
            tab_id_autorizado,
            {
                "usuario": "Usuario Protegido",
                "panel_token": token,
            },
        )
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session_key

        response = self.client.get(
            reverse("panel_usuario_token", kwargs={"token": token}),
            HTTP_X_TAB_ID="tab-no-autorizado",
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("inicio_sesion")))
        self.assertIn("no-store", response["Cache-Control"])
        self.assertTrue(
            sesiones_usuario.objects.filter(
                session_key=session_key,
                tab_id=tab_id_autorizado,
                activa=True,
            ).exists()
        )

    def test_ruta_inexistente_muestra_404_sin_sesion(self):
        response = self.client.get("/ruta-inexistente/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "404", status_code=404)

    def test_ruta_inexistente_sin_barra_redirige_a_la_ruta_con_barra(self):
        response = self.client.get("/ruta-inexistente")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/ruta-inexistente/")

    def test_panel_usuario_redirige_si_no_hay_sesion(self):
        response = self.client.get(reverse("panel_usuario"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("inicio_sesion"))

    def test_panel_usuario_permite_acceso_si_hay_sesion(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Prueba",
            cedula_identidad="10000001",
            genero="Masculino",
            estado_civil="Soltero",
        )
        tab_id = "tab-panel"
        session_key = self.crear_sesion_pestana(usuario, tab_id, {
            "usuario": "Usuario Prueba",
            "panel_token": TimestampSigner(salt="panel-route").sign("panel"),
        })

        response = self.client.get(
            reverse("panel_usuario"),
            HTTP_X_TAB_ID=tab_id,
            HTTP_REFERER=f"http://testserver/?tab_id={tab_id}",
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/panel/"))
        self.assertIn(f"tab_id={tab_id}", response.url)
        self.assertTrue(sesiones_usuario.objects.filter(session_key=session_key, activa=True).exists())

    def test_generar_pdf_usa_sesion_de_referer_del_mismo_host(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Reporte",
            cedula_identidad="10000008",
            genero="Masculino",
            estado_civil="Soltero",
        )
        tab_id = "tab-reporte-pdf"
        session_key = self.crear_sesion_pestana(
            usuario,
            tab_id,
            {"usuario": "Usuario Reporte"},
        )

        response = self.client.post(
            reverse("lista_equipos_pdf"),
            {"categoria": ""},
            HTTP_REFERER=f"http://testserver/visualizacion_equipos/?tab_id={tab_id}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(
            sesiones_usuario.objects.filter(
                session_key=session_key,
                activa=True,
            ).exists()
        )

    def test_recarga_sin_referer_ni_cache_control_conserva_la_sesion(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Recarga",
            cedula_identidad="10000005",
            genero="Masculino",
            estado_civil="Soltero",
        )
        tab_id = "tab-recarga-sin-referer"
        self.crear_sesion_pestana(usuario, tab_id, {
            "usuario": "Usuario Recarga",
            "panel_token": TimestampSigner(salt="panel-route").sign("panel"),
        })

        response = self.client.get(
            f"{reverse('panel_usuario')}?tab_id={tab_id}",
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/panel/"))
        self.assertIn(f"tab_id={tab_id}", response.url)

    def test_recarga_sin_referer_conserva_la_sesion_de_la_pestana(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Recarga",
            cedula_identidad="10000007",
            genero="Masculino",
            estado_civil="Soltero",
        )
        tab_id = "tab-recarga"
        session_key = self.crear_sesion_pestana(usuario, tab_id, {
            "usuario": "Usuario Recarga",
            "panel_token": TimestampSigner(salt="panel-route").sign("panel"),
        })

        for _ in range(3):
            response = self.client.get(
                f"{reverse('panel_usuario')}?tab_id={tab_id}",
                HTTP_CACHE_CONTROL="no-cache",
            )

            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("/panel/"))
            self.assertIn(f"tab_id={tab_id}", response.url)
            self.assertTrue(
                sesiones_usuario.objects.filter(
                    session_key=session_key,
                    activa=True,
                ).exists()
            )

    def test_panel_usuario_no_se_cachea(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Prueba",
            cedula_identidad="10000003",
            genero="Masculino",
            estado_civil="Soltero",
        )
        self.crear_sesion_pestana(usuario, "tab-cache", {
            "usuario": "Usuario Prueba",
            "panel_token": TimestampSigner(salt="panel-route").sign("panel"),
        })

        response = self.client.get(
            reverse("panel_usuario"),
            HTTP_X_TAB_ID="tab-cache",
            HTTP_REFERER="http://testserver/?tab_id=tab-cache",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("no-store", response.get("Cache-Control", ""))

    def test_completar_registro_redirige_si_no_hay_sesion_y_no_se_cachea(self):
        response = self.client.get(reverse("completar_registro"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("inicio_sesion"))
        self.assertIn("no-store", response.get("Cache-Control", ""))

    def test_completar_registro_rechaza_post_si_no_hay_sesion(self):
        response = self.client.post(
            reverse("completar_registro"),
            HTTP_SEC_FETCH_MODE="cors",
            HTTP_SEC_FETCH_DEST="empty",
        )

        self.assertEqual(response.status_code, 401)

    def test_panel_usuario_redirige_a_una_ruta_obfusca(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Prueba",
            cedula_identidad="10000004",
            genero="Masculino",
            estado_civil="Soltero",
        )
        token = TimestampSigner(salt="panel-route").sign("panel")
        self.crear_sesion_pestana(usuario, "tab-token", {
            "usuario": "Usuario Prueba",
            "panel_token": token,
        })

        response = self.client.get(
            reverse("panel_usuario"),
            HTTP_X_TAB_ID="tab-token",
            HTTP_REFERER="http://testserver/?tab_id=tab-token",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("panel_usuario_token", kwargs={"token": token}),
            response.url,
        )
        self.assertIn("tab_id=tab-token", response.url)

    def test_panel_usuario_token_renderiza_el_panel_del_perfil(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Supervisor",
            cedula_identidad="10000009",
            genero="Masculino",
            estado_civil="Soltero",
        )
        token = TimestampSigner(salt="panel-route").sign("panel")
        self.crear_sesion_pestana(usuario, "tab-panel-perfil", {
            "usuario": "Usuario Supervisor",
            "perfil": "Supervisor Encargado",
            "panel_token": token,
        })

        response = self.client.get(
            reverse("panel_usuario_token", kwargs={"token": token}),
            HTTP_X_TAB_ID="tab-panel-perfil",
            HTTP_REFERER="http://testserver/?tab_id=tab-panel-perfil",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Panel/panel_usuario.html")
        self.assertTemplateUsed(
            response,
            "Usuarios/panel_supervisor_encargado.html",
        )
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertEqual(response["Pragma"], "no-cache")
        self.assertEqual(response["Expires"], "0")

        ruta_panel = reverse(
            "panel_usuario_token",
            kwargs={"token": token},
        )
        headers_pestana = {
            "HTTP_X_TAB_ID": "tab-panel-perfil",
            "HTTP_REFERER": "http://testserver/?tab_id=tab-panel-perfil",
        }
        respuesta_cierre = self.client.get(
            reverse("cerrar_sesion"),
            **headers_pestana,
        )
        respuesta_volver = self.client.get(ruta_panel, **headers_pestana)

        self.assertEqual(respuesta_cierre.status_code, 302)
        self.assertEqual(respuesta_volver.status_code, 302)
        self.assertTrue(
            respuesta_volver.url.startswith(reverse("inicio_sesion"))
        )

    def test_registro_usuarios_redirige_si_no_hay_sesion(self):
        response = self.client.get(reverse("registro_usuarios"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("inicio_sesion"))

    def test_registro_usuarios_no_se_cachea_y_se_bloquea_tras_cerrar_sesion(self):
        usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Prueba",
            cedula_identidad="10000006",
            genero="Masculino",
            estado_civil="Soltero",
        )
        tab_id = "tab-registro-cache"
        session_key = self.crear_sesion_pestana(usuario, tab_id, {
            "usuario": "Usuario Prueba",
        })
        ruta_registro = reverse("registro_usuarios")
        headers_pestana = {
            "HTTP_X_TAB_ID": tab_id,
            "HTTP_REFERER": f"http://testserver/?tab_id={tab_id}",
        }

        respuesta_registro = self.client.get(ruta_registro, **headers_pestana)

        self.assertEqual(respuesta_registro.status_code, 200)
        self.assertIn("no-store", respuesta_registro["Cache-Control"])

        respuesta_cierre = self.client.get(
            reverse("cerrar_sesion"),
            **headers_pestana,
        )
        respuesta_registro_tras_cierre = self.client.get(
            ruta_registro,
            **headers_pestana,
        )

        self.assertEqual(respuesta_cierre.status_code, 302)
        self.assertFalse(
            sesiones_usuario.objects.filter(
                session_key=session_key,
                activa=True,
            ).exists()
        )
        self.assertEqual(respuesta_registro_tras_cierre.status_code, 302)
        self.assertTrue(
            respuesta_registro_tras_cierre.url.startswith(
                reverse("inicio_sesion")
            )
        )

    def test_inicio_sesion_actualiza_sesion_de_la_pestana_sin_error(self):
        usuario = usuarios.objects.create(
            nombres="Ana",
            apellidos="García",
            cedula_identidad="87654321",
            genero="Femenino",
            estado_civil="Soltera",
        )
        credenciales.objects.create(
            id_usuario=usuario,
            nombre_usuario="anagarcia",
            clave=make_password("123456"),
        )
        propietarios.objects.create(id_usuario=usuario)

        tab_id = "tab-existente"
        session_key = self.crear_sesion_pestana(usuario, tab_id, {})

        response = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia",
            "contrasenia": "123456",
            "tab_id": tab_id,
        },
            HTTP_X_TAB_ID=tab_id,
            HTTP_REFERER=f"http://testserver/?tab_id={tab_id}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "incompleto")
        self.assertEqual(
            sesiones_usuario.objects.filter(session_key=session_key, activa=True).count(),
            1,
        )

    def test_inicio_sesion_con_registro_completo_permite_abrir_el_panel(self):
        usuario = usuarios.objects.create(
            nombres="Ana",
            apellidos="García",
            cedula_identidad="87654325",
            genero="Femenino",
            estado_civil="Soltera",
        )
        credenciales.objects.create(
            id_usuario=usuario,
            nombre_usuario="ana_panel",
            clave=make_password("123456"),
        )
        propietarios.objects.create(id_usuario=usuario)
        nacimiento.objects.create(
            id_usuario=usuario,
            pais="Venezuela",
            estado="Miranda",
            municipio="Sucre",
            parroquia="Petare",
            direccion="Dirección de prueba",
            fecha_nacimiento="1990-01-01",
        )
        tab_id = "tab-login-panel"
        headers = {
            "HTTP_X_TAB_ID": tab_id,
            "HTTP_REFERER": f"http://testserver/?tab_id={tab_id}",
        }

        respuesta_login = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "ana_panel",
            "contrasenia": "123456",
            "tab_id": tab_id,
        }, **headers)

        self.assertEqual(respuesta_login.status_code, 200)
        self.assertEqual(respuesta_login.json()["estado"], "exito")

        respuesta_panel = self.client.get(
            respuesta_login.json()["url"],
            **headers,
        )
        self.assertEqual(respuesta_panel.status_code, 302)
        self.assertIn("/panel/", respuesta_panel.url)

        respuesta_panel_token = self.client.get(
            respuesta_panel.url,
            **headers,
        )
        self.assertEqual(respuesta_panel_token.status_code, 200)
        self.assertTemplateUsed(
            respuesta_panel_token,
            "Panel/panel_usuario.html",
        )
        self.assertContains(respuesta_panel_token, 'id="btnMenuLateral"')
        self.assertContains(respuesta_panel_token, 'id="asideMenu"')

    def test_inicio_sesion_asigna_rol_atencion_al_cliente(self):
        usuario = usuarios.objects.create(
            nombres="Ana",
            apellidos="García",
            cedula_identidad="87654324",
            genero="Femenino",
            estado_civil="Soltera",
        )
        credenciales.objects.create(
            id_usuario=usuario,
            nombre_usuario="anagarcia_atencion",
            clave=make_password("123456"),
        )
        atencion_cliente.objects.create(id_usuario=usuario)

        self.assertEqual(
            obtener_rol(usuario),
            {"rol": "Atención al Cliente"},
        )

        response = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia_atencion",
            "contrasenia": "123456",
            "tab_id": "tab-atencion",
        }, HTTP_X_TAB_ID="tab-atencion")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "incompleto")
        self.assertEqual(response.json()["estado"], "incompleto")

    def test_impide_dos_sesiones_activas_del_mismo_usuario(self):
        usuario = usuarios.objects.create(
            nombres="Ana",
            apellidos="García",
            cedula_identidad="87654321",
            genero="Femenino",
            estado_civil="Soltera",
        )
        credenciales.objects.create(
            id_usuario=usuario,
            nombre_usuario="anagarcia",
            clave=make_password("123456"),
        )
        propietarios.objects.create(id_usuario=usuario)

        respuesta_anterior = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia",
            "contrasenia": "123456",
            "tab_id": "tab-uno",
        }, HTTP_X_TAB_ID="tab-uno")

        respuesta_nueva = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia",
            "contrasenia": "123456",
            "tab_id": "tab-dos",
        }, HTTP_X_TAB_ID="tab-dos")

        sesion_uno = sesiones_usuario.objects.get(usuario=usuario, tab_id="tab-uno", activa=True)

        self.assertEqual(respuesta_anterior.status_code, 200)
        self.assertEqual(respuesta_nueva.status_code, 200)
        self.assertEqual(respuesta_nueva.json()["estado"], "sesion_activa")
        self.assertIn("ya tiene una sesión activa", respuesta_nueva.json()["descripcion"])
        self.assertEqual(
            sesiones_usuario.objects.filter(usuario=usuario, activa=True).count(),
            1,
        )

        respuesta_panel_uno = self.client.get(
            reverse("panel_usuario"),
            HTTP_X_TAB_ID="tab-uno",
            HTTP_REFERER="http://testserver/?tab_id=tab-uno",
        )
        respuesta_panel_dos = self.client.get(
            reverse("panel_usuario"),
            HTTP_X_TAB_ID="tab-dos",
            HTTP_REFERER="http://testserver/?tab_id=tab-dos",
        )
        self.assertEqual(respuesta_panel_uno.status_code, 302)
        self.assertEqual(respuesta_panel_dos.status_code, 302)
        self.assertIn("tab_id=tab-uno", respuesta_panel_uno.url)
        self.assertEqual(respuesta_panel_dos.url, reverse("inicio_sesion") + "?tab_id=tab-dos")

        respuesta_cierre_uno = self.client.get(
            reverse("cerrar_sesion"),
            HTTP_X_TAB_ID="tab-uno",
            HTTP_REFERER="http://testserver/?tab_id=tab-uno",
        )
        self.assertEqual(respuesta_cierre_uno.status_code, 302)
        self.assertFalse(
            sesiones_usuario.objects.filter(
                session_key=sesion_uno.session_key,
                activa=True,
            ).exists()
        )

    def test_mismo_usuario_activo_es_rechazado_en_otro_navegador(self):
        usuario = usuarios.objects.create(
            nombres="Ana",
            apellidos="García",
            cedula_identidad="87654322",
            genero="Femenino",
            estado_civil="Soltera",
        )
        credenciales.objects.create(
            id_usuario=usuario,
            nombre_usuario="anagarcia2",
            clave=make_password("123456"),
        )
        propietarios.objects.create(id_usuario=usuario)

        navegador_uno = self.client
        navegador_dos = self.client_class()

        respuesta_uno = navegador_uno.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia2",
            "contrasenia": "123456",
            "tab_id": "browser-one-tab",
        }, HTTP_X_TAB_ID="browser-one-tab")
        respuesta_dos = navegador_dos.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia2",
            "contrasenia": "123456",
            "tab_id": "browser-two-tab",
        }, HTTP_X_TAB_ID="browser-two-tab")

        sesiones = sesiones_usuario.objects.filter(usuario=usuario, activa=True)

        self.assertEqual(respuesta_uno.status_code, 200)
        self.assertEqual(respuesta_dos.status_code, 200)
        self.assertEqual(respuesta_dos.json()["estado"], "sesion_activa")
        self.assertIn("ya tiene una sesión activa", respuesta_dos.json()["descripcion"])
        self.assertIn("espere hasta 2 minutos", respuesta_dos.json()["descripcion"])
        self.assertEqual(sesiones.count(), 1)
        self.assertTrue(sesiones.filter(tab_id="browser-one-tab").exists())
        self.assertFalse(sesiones.filter(tab_id="browser-two-tab").exists())

    def test_sesion_sin_senal_reciente_se_libera_al_iniciar_sesion(self):
        usuario = usuarios.objects.create(
            nombres="Ana",
            apellidos="García",
            cedula_identidad="87654323",
            genero="Femenino",
            estado_civil="Soltera",
        )
        credenciales.objects.create(
            id_usuario=usuario,
            nombre_usuario="anagarcia3",
            clave=make_password("123456"),
        )
        propietarios.objects.create(id_usuario=usuario)

        session_key = self.crear_sesion_pestana(usuario, "tab-antigua", {
            "usuario": "Ana García",
        })
        sesiones_usuario.objects.filter(session_key=session_key).update(
            ultima_actividad=timezone.now() - timedelta(minutes=3),
        )

        response = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia3",
            "contrasenia": "123456",
            "tab_id": "tab-nueva",
        }, HTTP_X_TAB_ID="tab-nueva")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "incompleto")
        self.assertFalse(
            sesiones_usuario.objects.get(session_key=session_key).activa
        )

    def test_credenciales_nuevas_no_quedan_bloqueadas_por_defecto(self):
        usuario = usuarios.objects.create(
            nombres="Carlos",
            apellidos="Mendoza",
            cedula_identidad="99887766",
            genero="Masculino",
            estado_civil="Soltero",
        )
        credenciales.objects.create(
            nombre_usuario="cmendoza",
            clave=make_password("123456"),
            id_usuario=usuario,
        )
        propietarios.objects.create(id_usuario=usuario)

        response = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "cmendoza",
            "contrasenia": "123456",
            "tab_id": "tab-1",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "incompleto")

    def test_usuario_inexistente_no_genera_error_al_iniciar_sesion(self):
        response = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "usuario_inexistente",
            "contrasenia": "clave-incorrecta",
            "tab_id": "tab-usuario-inexistente",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "fallo")
        self.assertEqual(response.json()["title"], "Usuario no encontrado")
        self.assertFalse(bloqueo_inicio_sesion.objects.exists())
        self.assertTrue(
            intentos_inicio_sesion.objects.filter(
                nombre_usuario="usuario_inexistente",
                usuario__isnull=True,
                exitoso=False,
            ).exists()
        )

    def test_tres_intentos_fallidos_bloquean_temporalmente(self):
        usuario = usuarios.objects.create(
            nombres="María",
            apellidos="López",
            cedula_identidad="11223344",
            genero="Femenino",
            estado_civil="Soltera",
        )
        credenciales.objects.create(
            nombre_usuario="mlopez",
            clave=make_password("123456"),
            id_usuario=usuario,
        )
        propietarios.objects.create(id_usuario=usuario)

        for _ in range(3):
            response = self.client.post(reverse("inicio_sesion"), {
                "nombre_usuario": "mlopez",
                "contrasenia": "clave-incorrecta",
                "tab_id": "tab-2",
            })

        bloqueo = bloqueo_inicio_sesion.objects.get(usuario=usuario)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "bloqueado")
        self.assertTrue(bloqueo.bloqueado)
        self.assertIsNotNone(bloqueo.bloqueado_hasta)
        self.assertGreater(bloqueo.bloqueado_hasta, timezone.now())


class AtencionClienteUnicaActivaTest(TestCase):
    def setUp(self):
        self.empleado_activo = usuarios.objects.create(
            nombres="Empleado",
            apellidos="Activo",
            cedula_identidad="90000001",
        )
        self.empleado_nuevo = usuarios.objects.create(
            nombres="Empleado",
            apellidos="Nuevo",
            cedula_identidad="90000002",
        )
        self.usuario_accion = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Administrador",
            cedula_identidad="90000003",
        )
        atencion_cliente.objects.create(id_usuario=self.empleado_activo)

    def test_informa_si_otro_empleado_tiene_atencion_activa(self):
        request = RequestFactory().post("/perfiles_usuario_no_registrados/")
        request.session = {"id_empleado": self.empleado_nuevo.id_usuario}

        response = perfiles_usuario_no_registrados(request)
        resultado = json.loads(response.content)
        perfil_atencion = next(
            perfil
            for perfil in resultado["perfiles"]
            if perfil["id_perfil"] == "ATENCION_CLIENTE"
        )

        self.assertTrue(perfil_atencion["ocupado"])

    def test_rechaza_asignar_atencion_si_otro_empleado_esta_activo(self):
        request = RequestFactory().post(
            "/registrar_nueva_asignacion/",
            {"perfil": "ATENCION_CLIENTE"},
        )
        request.session = {
            "id_empleado": self.empleado_nuevo.id_usuario,
            "cedula_identidad": self.usuario_accion.cedula_identidad,
        }

        response = registrar_nueva_asignacion(request)

        resultado = json.loads(response.content)
        self.assertEqual(resultado["estado"], "error")
        self.assertEqual(resultado["title"], "Perfil ocupado")
        self.assertFalse(
            atencion_cliente.objects.filter(
                id_usuario=self.empleado_nuevo
            ).exists()
        )

    def test_rechaza_reasignar_atencion_inactiva_ya_registrada(self):
        atencion_cliente.objects.create(
            id_usuario=self.empleado_nuevo,
            vigencia=False,
        )
        request = RequestFactory().post(
            "/registrar_nueva_asignacion/",
            {"perfil": "ATENCION_CLIENTE"},
        )
        request.session = {
            "id_empleado": self.empleado_nuevo.id_usuario,
            "cedula_identidad": self.usuario_accion.cedula_identidad,
        }

        response = registrar_nueva_asignacion(request)

        resultado = json.loads(response.content)
        self.assertEqual(resultado["estado"], "error")
        self.assertEqual(resultado["title"], "Perfil ya registrado")
        self.assertFalse(
            atencion_cliente.objects.get(
                id_usuario=self.empleado_nuevo
            ).vigencia
        )

    def test_bloquea_si_solo_falta_atencion_ocupada_y_permite_si_libre(self):
        turno = turnos_laborales.objects.create(nombre="Turno prueba")
        supervisores_encargados.objects.create(
            id_usuario=self.empleado_nuevo,
            id_turno=turno,
            vigencia=False,
        )
        personal_limpieza.objects.create(
            id_usuario=self.empleado_nuevo,
            id_turno=turno,
            vigencia=False,
        )
        despachadores.objects.create(
            id_usuario=self.empleado_nuevo,
            id_turno=turno,
            vigencia=False,
        )
        vigilantes.objects.create(
            id_usuario=self.empleado_nuevo,
            id_turno=turno,
            vigencia=False,
        )

        request = RequestFactory().get("/cantidad_perfiles_asignado/")
        request.session = {"id_empleado": self.empleado_nuevo.id_usuario}

        response = cantidad_perfiles_asignado(request)

        resultado = json.loads(response.content)
        self.assertEqual(resultado["estado"], "fallo")
        self.assertFalse(resultado["todos_asignados"])
        self.assertTrue(resultado["atencion_ocupada"])

        atencion_cliente.objects.filter(
            id_usuario=self.empleado_activo
        ).update(vigencia=False)
        response = cantidad_perfiles_asignado(request)

        resultado = json.loads(response.content)
        self.assertEqual(resultado["estado"], "exito")
        self.assertFalse(resultado["todos_asignados"])
        self.assertFalse(resultado["atencion_ocupada"])

        atencion_cliente.objects.create(
            id_usuario=self.empleado_nuevo,
            vigencia=False,
        )
        response = cantidad_perfiles_asignado(request)

        resultado = json.loads(response.content)
        self.assertEqual(resultado["estado"], "fallo")
        self.assertTrue(resultado["todos_asignados"])


class VigenciaCodigoTest(TestCase):
    def setUp(self):
        self.usuario = usuarios.objects.create(
            nombres="Usuario",
            apellidos="Prueba",
            cedula_identidad="V-1234567",
        )
        credenciales.objects.create(
            id_usuario=self.usuario,
            nombre_usuario="usuario.prueba",
            clave=make_password("clave-prueba"),
        )
        session = self.client.session
        session["usuario_credenciales"] = self.usuario.cedula_identidad
        session.save()
        self.tab_id = "tab-recuperar-codigo"
        sesiones_recuperacion.objects.create(
            tab_id=self.tab_id,
            session_key=session.session_key,
        )

    def test_vigencia_informa_tiempo_restante_de_bloqueo_temporal(self):
        ahora = timezone.now()
        autenticar_codigo.objects.create(
            cedula_identidad=self.usuario.cedula_identidad,
            codigo="123456",
            descripcion="Código de prueba",
            activo=True,
            bloqueado_hasta=ahora + timedelta(minutes=3),
            fecha_expiracion=ahora + timedelta(minutes=5),
        )

        response = self.client.get(
            reverse("vigencia_codigo"),
            HTTP_X_TAB_ID=self.tab_id,
        )
        resultado = response.json()

        self.assertEqual(response.status_code, 429)
        self.assertTrue(resultado["bloqueado"])
        self.assertFalse(resultado["bloqueo_permanente"])
        self.assertGreater(resultado["segundos_restantes"], 0)
        self.assertIn("inhabilitado", resultado["descripcion"])

    def test_vigencia_informa_cuenta_bloqueada_permanentemente(self):
        self.usuario.credenciales.bloqueado = True
        self.usuario.credenciales.save(update_fields=["bloqueado"])

        response = self.client.get(
            reverse("vigencia_codigo"),
            HTTP_X_TAB_ID=self.tab_id,
        )
        resultado = response.json()

        self.assertTrue(resultado["bloqueado"])
        self.assertTrue(resultado["bloqueo_permanente"])

    def test_intentos_se_reinician_cuando_termina_bloqueo_temporal(self):
        autenticar_codigo.objects.create(
            cedula_identidad=self.usuario.cedula_identidad,
            codigo="123456",
            descripcion="Código de prueba",
            intentos=5,
            bloqueado_hasta=timezone.now() - timedelta(seconds=1),
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
        )

        response = self.client.post(reverse("verificar_codigo"), {
            "codigo_recibido": "000000",
        }, HTTP_X_TAB_ID=self.tab_id)
        codigo = autenticar_codigo.objects.get(
            cedula_identidad=self.usuario.cedula_identidad
        )

        self.assertEqual(response.json()["estado"], "fallo")
        self.assertEqual(codigo.intentos, 1)
        self.assertIsNone(codigo.bloqueado_hasta)


class ActualizacionDatosEmpleadoTest(TestCase):
    def test_campos_principales_vacios_son_requeridos(self):
        campos_requeridos = {
            "nombre_usuario": "Nombre",
            "apellido_usuario": "Apellido",
            "nacionalidad_usuario": "Nacionalidad",
            "cedula_usuario": "Cédula",
            "genero_usuario": "Género",
            "estado_civil_usuario": "Estado Civil",
            "prefijo_principal": "Prefijo Principal",
            "numero_principal": "Teléfono Principal",
            "email_principal": "Correo Principal",
            "dominio_principal": "Dominio Principal",
        }
        datos = {
            "nombre_usuario": "Empleado",
            "apellido_usuario": "Prueba",
            "nacionalidad_usuario": "V",
            "cedula_usuario": "1234567",
            "genero_usuario": "Masculino",
            "estado_civil_usuario": "Soltero",
            "prefijo_principal": "0412",
            "numero_principal": "1234567",
            "email_principal": "empleado",
            "dominio_principal": "@example.com",
        }

        for campo, titulo in campos_requeridos.items():
            with self.subTest(campo=campo):
                datos_prueba = {**datos, campo: ""}
                request = RequestFactory().post(
                    "/actualizacion_datos_usuarios/",
                    datos_prueba,
                )

                response = actualizacion_datos_usuarios(request)
                resultado = json.loads(response.content)

                self.assertEqual(resultado["estado"], "fallo")
                self.assertEqual(resultado["title"], titulo)

    def test_secundarios_vacios_y_registros_incompletos_no_bloquean(self):
        actor = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="",
            nombres="Administrador",
            apellidos="Prueba",
            cedula_identidad="V-7654321",
        )
        empleado = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="",
            nombres="Empleado",
            apellidos="Prueba",
            cedula_identidad="V-1234567",
            genero="Masculino",
            estado_civil="Soltero",
        )
        contacto.objects.create(
            id_usuario=empleado,
            telefono_principal="0412-1234567",
            telefono_secundario="N/A",
            correo_principal="empleado@example.com",
            correo_secundario="N/A",
        )
        nacimiento.objects.create(
            id_usuario=empleado,
            pais="",
            estado="",
            municipio="",
            parroquia="",
            direccion="",
            fecha_nacimiento="",
        )
        residencia.objects.create(
            id_usuario=empleado,
            condicion_residencia="",
            municipio="",
            parroquia="",
            direccion="",
        )
        request = RequestFactory().post(
            "/actualizacion_datos_usuarios/",
            {
                "usuario_id": str(empleado.id_usuario),
                "nombre_usuario": "Empleado",
                "apellido_usuario": "Prueba",
                "nacionalidad_usuario": "V",
                "cedula_usuario": "1234567",
                "genero_usuario": "Masculino",
                "estado_civil_usuario": "Soltero",
                "prefijo_principal": "0412",
                "numero_principal": "1234567",
                "email_principal": "empleado",
                "dominio_principal": "@example.com",
            },
        )
        request.session = {"cedula_identidad": actor.cedula_identidad}

        response = actualizacion_datos_usuarios(request)
        resultado = json.loads(response.content)
        contacto_actualizado = contacto.objects.get(id_usuario=empleado)

        self.assertEqual(resultado["estado"], "exito")
        self.assertEqual(contacto_actualizado.telefono_secundario, "N/A")
        self.assertEqual(contacto_actualizado.correo_secundario, "N/A")
        self.assertEqual(bitacora.objects.count(), 1)
        self.assertEqual(nacimiento.objects.get(id_usuario=empleado).pais, "")
        self.assertEqual(
            residencia.objects.get(id_usuario=empleado).condicion_residencia,
            "",
        )


class ActualizarAdministradorTest(TestCase):
    def test_marcadores_de_datos_incompletos_conservan_datos_opcionales(self):
        usuario = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="",
            nombres="Admin",
            apellidos="Prueba",
            cedula_identidad="V-1234567",
            genero="Masculino",
            estado_civil="Soltero/a",
        )
        encargados_administrativos.objects.create(id_usuario=usuario)
        contacto.objects.create(
            id_usuario=usuario,
            telefono_principal="0412-1234567",
            telefono_secundario="N/A",
            correo_principal="admin@example.com",
            correo_secundario="N/A",
        )

        request = RequestFactory().post(
            "/actualizar_administrador/",
            {
                "id_usuario": str(usuario.id_usuario),
                "nombres": "Admin",
                "apellidos": "Prueba",
                "nacionalidad": "V",
                "cedula_identidad": "1234567",
                "genero": "No registrado",
                "estado_civil": "No registrado",
                "prefijo_principal": "0412",
                "numero_principal": "1234567",
                "correo_principal": "admin",
                "dominio_principal": "@example.com",
            },
        )
        request.session = {"cedula_usuario": usuario.cedula_identidad}

        response = actualizar_administrador(request)
        usuario.refresh_from_db()

        self.assertEqual(json.loads(response.content)["estado"], "exito")
        self.assertEqual(usuario.genero, "Masculino")
        self.assertEqual(usuario.estado_civil, "Soltero/a")
        self.assertFalse(nacimiento.objects.filter(id_usuario=usuario).exists())
        self.assertFalse(residencia.objects.filter(id_usuario=usuario).exists())


class RegistrarAdministradorTest(TestCase):
    def setUp(self):
        self.operador = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="Operador Prueba",
            nombres="Operador",
            apellidos="Prueba",
            cedula_identidad="V-7654321",
            genero="Masculino",
            estado_civil="Soltero/a",
        )

    def registrar(self, **campos_secundarios):
        datos = {
            "nombres": "Nuevo",
            "apellidos": "Administrador",
            "nacionalidad": "V",
            "cedula_identidad": "1234567",
            "prefijo_principal": "0412",
            "numero_principal": "1234567",
            "correo_principal": "nuevo",
            "dominio_principal": "@gmail.com",
            "prefijo_secundaria": "0414",
            "numero_secundaria": "",
            "correo_secundaria": "",
            "dominio_secundaria": "@gmail.com",
        }
        datos.update(campos_secundarios)
        request = RequestFactory().post("/registrar_administrador/", datos)
        request.session = {"cedula_identidad": self.operador.cedula_identidad}
        return registrar_administrador(request).json()

    def test_permite_omitir_telefono_y_correo_secundarios(self):
        respuesta = self.registrar()

        self.assertEqual(respuesta["estado"], "exito")
        contacto_registrado = contacto.objects.get(
            id_usuario__cedula_identidad="V-1234567"
        )
        self.assertEqual(contacto_registrado.telefono_secundario, "N/A")
        self.assertEqual(contacto_registrado.correo_secundario, "N/A")

    def test_rechaza_telefono_secundario_igual_al_principal(self):
        respuesta = self.registrar(
            prefijo_secundaria="0412",
            numero_secundaria="1234567",
        )

        self.assertEqual(respuesta["title"], "Teléfonos iguales")

    def test_rechaza_correo_secundario_igual_al_principal(self):
        respuesta = self.registrar(correo_secundaria="nuevo")

        self.assertEqual(respuesta["title"], "Correos iguales")

    def test_rechaza_telefono_secundario_existente_en_la_base_de_datos(self):
        usuario = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="Otro Usuario",
            nombres="Otro",
            apellidos="Usuario",
            cedula_identidad="V-2345678",
        )
        contacto.objects.create(
            id_usuario=usuario,
            telefono_principal="0414-7654321",
            correo_principal="otro@example.com",
        )

        respuesta = self.registrar(numero_secundaria="7654321")

        self.assertEqual(respuesta["title"], "Teléfono registrado")

    def test_rechaza_correo_secundario_existente_en_la_base_de_datos(self):
        usuario = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="Otro Usuario",
            nombres="Otro",
            apellidos="Usuario",
            cedula_identidad="V-2345678",
        )
        contacto.objects.create(
            id_usuario=usuario,
            telefono_principal="0414-7654321",
            correo_principal="otro@example.com",
        )

        respuesta = self.registrar(
            numero_secundaria="7654322",
            correo_secundaria="otro",
            dominio_secundaria="@example.com",
        )

        self.assertEqual(respuesta["title"], "Correo registrado")
