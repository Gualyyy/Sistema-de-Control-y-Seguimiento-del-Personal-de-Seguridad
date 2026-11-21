import json

from django.test import RequestFactory, TestCase

from inicio_sesion.models import bitacora, usuarios
from inicio_sesion.views.seguridad import bitacora_registradas


class BitacoraRegistradaTest(TestCase):
    def test_lista_incluye_modulo_y_cargo_del_usuario(self):
        usuario = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="Ana Pérez",
            nombres="Ana",
            apellidos="Pérez",
            cedula_identidad="V-12345678",
        )
        bitacora.objects.create(
            id_usuario=usuario,
            nombre_modulo="Gestión de productos",
            cargo_usuario="Encargado Administrativo",
            accion="Actualizó un producto",
        )

        request = RequestFactory().post(
            "/bitacora_registradas/",
            {"cedula": "", "nacionalidad": ""},
        )
        response = bitacora_registradas(request)
        registro = json.loads(response.content)[0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(registro["nombre_modulo"], "Gestión de productos")
        self.assertEqual(
            registro["cargo_usuario"],
            "Encargado Administrativo",
        )
