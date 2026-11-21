import json
from datetime import timedelta

from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone

from inicio_sesion.views.gastos import actualizar_datos_gasto


class ActualizarGastoValidationsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def enviar_actualizacion(self, **cambios):
        datos = {
            "id_gasto": "1",
            "categoria_gastos": "1",
            "descripcion": "Pago de servicio",
            "monto_gasto": "25.50",
            "fecha_gasto": timezone.localdate().isoformat(),
            "es_recurrente": "false",
            "frecuencia": "",
            "referencia": "",
            "observacion": "",
        }
        datos.update(cambios)

        request = self.factory.post("/actualizar_datos_gasto/", data=datos)
        request.session = {}
        response = actualizar_datos_gasto(request)
        return json.loads(response.content)

    def test_rechaza_fecha_futura(self):
        fecha_futura = timezone.localdate() + timedelta(days=1)

        respuesta = self.enviar_actualizacion(
            fecha_gasto=fecha_futura.isoformat()
        )

        self.assertEqual(respuesta["estado"], "fallo")
        self.assertEqual(respuesta["title"], "Fecha del Gasto")

    def test_rechaza_observaciones_mayores_a_250_caracteres(self):
        respuesta = self.enviar_actualizacion(observacion="x" * 251)

        self.assertEqual(respuesta["estado"], "fallo")
        self.assertEqual(respuesta["title"], "Observaciones")

    def test_rechaza_monto_con_tres_decimales(self):
        respuesta = self.enviar_actualizacion(monto_gasto="10.001")

        self.assertEqual(respuesta["estado"], "fallo")
        self.assertEqual(respuesta["title"], "Monto del Gasto")

    def test_rechaza_monto_mayor_a_999_99(self):
        respuesta = self.enviar_actualizacion(monto_gasto="1000")

        self.assertEqual(respuesta["estado"], "fallo")
        self.assertEqual(respuesta["title"], "Monto del Gasto")
