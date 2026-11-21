from django.test import RequestFactory, SimpleTestCase
from django.template.loader import render_to_string


class PanelSidebarTest(SimpleTestCase):
    def test_admin_report_link_resolves(self):
        request = RequestFactory().get("/panel/token/")
        request.session = {
            "usuario": "Empleado",
            "completar_registro": True,
            "perfil": "Encargado Administrativo"
        }

        html = render_to_string(
            "Estructura/Barra_Lateral.html",
            request=request
        )

        self.assertIn('href="/reporte_sistema_administrador/"', html)

    def test_cliente_ve_opciones_de_perfil_y_cerrar_sesion(self):
        request = RequestFactory().get("/panel/token/")
        request.session = {
            "usuario": "Cliente",
            "completar_registro": True,
            "perfil": "Cliente"
        }

        html = render_to_string(
            "Usuarios/panel_cliente.html",
            request=request
        )

        self.assertIn('id="asideMenu"', html)
        self.assertIn('href="/actualizar_datos_sistema/"', html)
        self.assertIn('href="/cerrar_sesion/"', html)
        self.assertIn("Mi perfil", html)
        self.assertIn("Cerrar sesión", html)
