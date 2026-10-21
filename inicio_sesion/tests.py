from django.contrib.auth.hashers import make_password
from django.contrib.sessions.backends.db import SessionStore
from django.core.signing import TimestampSigner
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from django.conf import settings
from inicio_sesion.models import (
    bloqueo_inicio_sesion,
    credenciales,
    directiva_nacional,
    sesiones_usuario,
    usuarios,
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

    def test_paginas_del_foro_siguen_publicas(self):
        for nombre_url in ("foro", "historia", "quienes_somos", "contactanos"):
            with self.subTest(nombre_url=nombre_url):
                response = self.client.get(
                    reverse(nombre_url),
                    {"tab_id": f"tab-publica-{nombre_url}"},
                )
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
        directiva_nacional.objects.create(id_usuario=usuario)

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
        directiva_nacional.objects.create(id_usuario=usuario)

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
        directiva_nacional.objects.create(id_usuario=usuario)

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
        directiva_nacional.objects.create(id_usuario=usuario)

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
        directiva_nacional.objects.create(id_usuario=usuario)

        response = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "cmendoza",
            "contrasenia": "123456",
            "tab_id": "tab-1",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "incompleto")

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
        directiva_nacional.objects.create(id_usuario=usuario)

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
