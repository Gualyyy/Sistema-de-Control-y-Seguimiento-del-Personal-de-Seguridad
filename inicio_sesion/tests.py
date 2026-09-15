from datetime import date

from django.contrib.auth.hashers import make_password
from django.core.signing import TimestampSigner
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inicio_sesion.models import (
    bloqueo_inicio_sesion,
    credenciales,
    perfiles,
    perfil_usuario,
    sesiones_usuario,
    usuarios,
)


class ProteccionDeVistasTest(TestCase):
    def test_panel_usuario_redirige_si_no_hay_sesion(self):
        response = self.client.get(reverse("panel_usuario"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("inicio_sesion"))

    def test_panel_usuario_permite_acceso_si_hay_sesion(self):
        session = self.client.session
        session["usuario"] = "Usuario de prueba"
        session["panel_token"] = TimestampSigner(salt="panel-route").sign("panel")
        session.save()

        response = self.client.get(reverse("panel_usuario"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("panel_usuario_token", kwargs={"token": session["panel_token"]}))

    def test_panel_usuario_no_se_cachea(self):
        session = self.client.session
        session["usuario"] = "Usuario de prueba"
        session["panel_token"] = TimestampSigner(salt="panel-route").sign("panel")
        session.save()

        response = self.client.get(reverse("panel_usuario"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("no-store", response.get("Cache-Control", ""))

    def test_panel_usuario_redirige_a_una_ruta_obfusca(self):
        signer = TimestampSigner(salt="panel-route")
        session = self.client.session
        session["usuario"] = "Usuario de prueba"
        session["panel_token"] = signer.sign("panel")
        session.save()

        response = self.client.get(reverse("panel_usuario"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("panel_usuario_token", kwargs={"token": session["panel_token"]}))

    def test_registro_usuarios_redirige_si_no_hay_sesion(self):
        response = self.client.get(reverse("registro_usuarios"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("inicio_sesion"))

    def test_completar_registro_rechaza_menores_de_18_años(self):
        usuarios.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            cedula_identidad="12345678",
            genero="Masculino",
            estado_civil="Soltero",
            nombre_usuario="juanprueba",
            clave="123456"
        )

        session = self.client.session
        session["usuario"] = "Juan Pérez"
        session["panel_token"] = TimestampSigner(salt="panel-route").sign("panel")
        session["cedula_identidad"] = "12345678"
        session.save()

        response = self.client.post(reverse("completar_registro"), {
            "prefijo_principal": "+58",
            "numero_principal": "1234567",
            "correo_principal": "usuario",
            "dominio_principal": "@gmail.com",
            "prefijo_secundaria": "+58",
            "numero_secundaria": "7654321",
            "correo_secundaria": "usuario2",
            "dominio_secundaria": "@gmail.com",
            "pais_nacimiento": "Venezuela",
            "estado_nacimiento": "Caracas",
            "municipio_nacimiento": "Libertador",
            "parroquia_nacimiento": "Catia",
            "direccion_nacimiento": "Calle prueba",
            "fecha_nacimiento": (date.today().replace(year=date.today().year - 17)).strftime("%Y-%m-%d"),
            "condicion_residencia": "Residente",
            "municipio_residencia": "Libertador",
            "parroquia_residencia": "Catia",
            "direccion_residencia": "Calle residencia"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("menor de 18 años", response.json()["descripcion"].lower())

    def test_inicio_sesion_actualiza_sesion_existente_sin_error(self):
        usuario = usuarios.objects.create(
            nombres="Ana",
            apellidos="García",
            cedula_identidad="87654321",
            genero="Femenino",
            estado_civil="Soltera",
            nombre_usuario="anagarcia",
            clave=make_password("123456")
        )
        perfil = perfiles.objects.create(perfil="Empleado")
        perfil_usuario.objects.create(id_perfil=perfil, id_usuario=usuario)

        session_key = self.client.session.session_key
        sesiones_usuario.objects.create(
            usuario=usuario,
            session_key=session_key,
            activa=True,
            info_general="test-agent",
            direccion_ip="127.0.0.1"
        )

        response = self.client.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia",
            "contrasenia": "123456"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "incompleto")

    def test_inicio_sesion_invalida_la_sesion_anterior_del_usuario(self):
        usuario = usuarios.objects.create(
            nombres="Ana",
            apellidos="García",
            cedula_identidad="87654321",
            genero="Femenino",
            estado_civil="Soltera",
            nombre_usuario="anagarcia",
            clave=make_password("123456")
        )
        perfil = perfiles.objects.create(perfil="Empleado")
        perfil_usuario.objects.create(id_perfil=perfil, id_usuario=usuario)

        cliente_anterior = self.client
        respuesta_anterior = cliente_anterior.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia",
            "contrasenia": "123456"
        })
        clave_anterior = cliente_anterior.session.session_key

        cliente_nuevo = self.client_class()
        respuesta_nueva = cliente_nuevo.post(reverse("inicio_sesion"), {
            "nombre_usuario": "anagarcia",
            "contrasenia": "123456"
        })

        self.assertEqual(respuesta_anterior.status_code, 200)
        self.assertEqual(respuesta_nueva.status_code, 200)
        self.assertEqual(
            sesiones_usuario.objects.filter(usuario=usuario, activa=True).count(),
            1,
        )
        self.assertFalse(
            sesiones_usuario.objects.filter(
                usuario=usuario,
                session_key=clave_anterior,
                activa=True,
            ).exists()
        )
        respuesta_sesion_anterior = cliente_anterior.get(reverse("panel_usuario"))
        self.assertEqual(respuesta_sesion_anterior.status_code, 302)
        self.assertEqual(respuesta_sesion_anterior.url, reverse("inicio_sesion"))

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
        perfil = perfiles.objects.create(perfil="Empleado")
        perfil_usuario.objects.create(id_perfil=perfil, id_usuario=usuario)

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
        perfil = perfiles.objects.create(perfil="Empleado")
        perfil_usuario.objects.create(id_perfil=perfil, id_usuario=usuario)

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
