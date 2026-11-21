from django.test import SimpleTestCase
from django.urls import resolve, reverse
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory


class ReportesUrlsTest(SimpleTestCase):
    def test_vistas_de_reportes_se_resuelven_en_inicio_sesion(self):
        nombres = (
            "verificar_reporte_qr",
            "reporte_sistema_administrador",
            "lista_bitacora_pdf",
            "lista_inicios_sesiones_pdf",
            "lista_intentos_sesion_pdf",
            "lista_gastos_pdf",
            "datos_encargado_administrativo_pdf",
            "lista_clientes_pdf",
            "lista_empleados_pdf",
            "datos_empleados_pdf",
            "lista_incidencias_pdf",
            "lista_equipos_pdf",
            "lista_entrega_equipos_pdf",
            "lista_asignaciones_pdf_admin",
        )

        for nombre in nombres:
            with self.subTest(nombre=nombre):
                ruta = reverse(nombre)
                self.assertTrue(ruta.startswith("/"))
                self.assertEqual(
                    resolve(ruta).func.__module__,
                    "inicio_sesion.views.reportes"
                )

    def test_pantalla_administrativa_incluye_reportes_de_equipos(self):
        request = RequestFactory().get("/")
        request.session = {"perfil": "Encargado Administrativo"}
        request.user = AnonymousUser()

        html = render_to_string(
            "Modulos/Reportes/gestionar_reportes_administrador.html",
            request=request
        )

        self.assertIn(reverse("lista_entrega_equipos_pdf"), html)
        self.assertIn(reverse("lista_asignaciones_pdf_admin"), html)
        self.assertIn('data-options-key="supervisores"', html)
        self.assertIn('name="categoria"', html)
        self.assertIn('name="supervisor"', html)
        self.assertIn('name="nacionalidad"', html)
        self.assertIn('name="cedula_identidad"', html)
        self.assertIn('name="categorias_registradas"', html)
