from unittest.mock import patch

from django.test import RequestFactory, TestCase
from reportlab.platypus import Paragraph

from incidencias.models import incidencia, tipo_incidencia, vigilante_incidencia
from incidencias.views import lista_incidencias_pdf
from inicio_sesion.models import (
    supervisores_encargados,
    turnos_laborales,
    usuarios,
    vigilantes,
)


class ListaIncidenciasPdfTest(TestCase):
    def setUp(self):
        turno, _ = turnos_laborales.objects.get_or_create(nombre="Diurno")
        usuario_supervisor = usuarios.objects.create(
            nombres="Ana",
            apellidos="Supervisora",
            cedula_identidad="10000000001",
            genero="Femenino",
            estado_civil="Soltera",
        )
        supervisor = supervisores_encargados.objects.create(
            id_usuario=usuario_supervisor,
            id_turno=turno,
        )
        tipo, _ = tipo_incidencia.objects.get_or_create(nombre="Seguridad")
        registro = incidencia.objects.create(
            id_supervisor=supervisor,
            id_turno=turno,
            id_tipo=tipo,
            titulo="Incidencia de prueba",
            descripcion="Descripción de prueba",
        )

        for numero, nombres, apellidos in (
            (2, "Luis", "Vigilante"),
            (3, "Marta", "Vigilante"),
        ):
            usuario = usuarios.objects.create(
                nombres=nombres,
                apellidos=apellidos,
                cedula_identidad=f"1000000000{numero}",
                genero="Masculino",
                estado_civil="Soltero",
            )
            vigilante = vigilantes.objects.create(
                id_usuario=usuario,
                id_turno=turno,
            )
            vigilante_incidencia.objects.create(
                id_incidencia=registro,
                id_vigilante=vigilante,
            )

        self.cedula_supervisor = usuario_supervisor.cedula_identidad

    def test_reporte_incluye_vigilantes_asignados_a_la_incidencia(self):
        request = RequestFactory().post(
            "/incidencias/lista_incidencias_pdf/"
        )
        request.session = {
            "cedula_identidad": self.cedula_supervisor,
        }

        with patch(
            "incidencias.views.Paragraph",
            wraps=Paragraph,
        ) as paragraph:
            response = lista_incidencias_pdf(request)

        textos = [call.args[0] for call in paragraph.call_args_list]

        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn("Luis Vigilante, Marta Vigilante", textos)
