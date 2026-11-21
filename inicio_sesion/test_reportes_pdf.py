import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase, TestCase

from asignaciones.models import (
    asignacion_equipo,
    categoria_equipo,
    entrega_equipos,
    equipos,
)
from inicio_sesion.models import (
    supervisores_encargados,
    turnos_laborales,
    usuarios,
)

from inicio_sesion.views import reportes


class ReportesPdfTest(SimpleTestCase):
    def test_lista_empleados_no_genera_pdf_sin_registros(self):
        request = RequestFactory().post(
            "/lista_empleados_pdf/",
            {"perfil": "Vigilante"}
        )
        consulta_empleados = MagicMock()
        consulta_empleados.select_related.return_value = consulta_empleados
        consulta_empleados.__iter__.return_value = iter(())

        with (
            patch(
                "inicio_sesion.views.reportes.vigilantes.objects.filter",
                return_value=consulta_empleados
            ),
            patch(
                "inicio_sesion.views.reportes._crear_qr_verificacion"
            ) as crear_qr
        ):
            response = reportes.lista_empleados_pdf(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(json.loads(response.content)["estado"], "vacio")
        crear_qr.assert_not_called()


class ReportesEquiposSinFiltrosTest(TestCase):
    def setUp(self):
        usuario = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="Usuario de prueba",
            nombres="Usuario",
            apellidos="Prueba",
            cedula_identidad="V-9876543",
        )
        turno = turnos_laborales.objects.create(nombre="T_REPORTE")
        supervisor = supervisores_encargados.objects.create(
            id_usuario=usuario,
            id_turno=turno,
        )
        categoria = categoria_equipo.objects.create(
            nombre="Categoría de reporte"
        )
        equipo = equipos.objects.create(
            nombre="Equipo de reporte",
            codigo="REPORTE-001",
            observacion="",
            id_categoria=categoria,
        )
        self.entregas = [
            entrega_equipos.objects.create(
                supervisor_encargado=supervisor,
                id_equipo=equipo,
                estado=estado,
                motivo_incidencia=motivo,
            )
            for estado, motivo in (
                ("ASIGNADO", "NINGUNA"),
                ("RETIRADO", "ERROR_HUMANO"),
                ("DAÑADO", "NINGUNA"),
            )
        ]

    def generar_reporte_sin_filtros(self, vista, ruta):
        request = RequestFactory().post(ruta, {})

        with (
            patch(
                "inicio_sesion.views.reportes._crear_qr_verificacion",
                return_value=(BytesIO(), "https://example.com/qr")
            ) as crear_qr,
            patch("inicio_sesion.views.reportes.SimpleDocTemplate.build")
        ):
            response = vista(request)

        self.assertEqual(response.status_code, 200)
        datos_qr = crear_qr.call_args.args[3]
        self.assertEqual(datos_qr[0]["valor"], str(len(self.entregas)))

    def test_entregas_sin_filtros_incluyen_todos_los_registros(self):
        self.generar_reporte_sin_filtros(
            reportes.lista_entrega_equipos_pdf,
            "/lista_entrega_equipos_pdf/"
        )

    def test_asignaciones_sin_filtros_incluyen_las_finalizadas(self):
        for estado in ("ASIGNADO", "PARCIAL", "FINALIZADO"):
            asignacion_equipo.objects.create(
                id_entrega=self.entregas[0],
                id_usuario=self.entregas[0].supervisor_encargado.id_usuario,
                estado=estado,
            )

        self.generar_reporte_sin_filtros(
            reportes.lista_asignaciones_pdf_admin,
            "/lista_asignaciones_pdf_admin/"
        )
