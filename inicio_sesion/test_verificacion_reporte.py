from io import BytesIO
from datetime import datetime
from urllib.parse import parse_qs, urlsplit
from unittest.mock import Mock, patch

from django.core import signing
from django.test import RequestFactory, TestCase
from django.urls import reverse

from inicio_sesion.views.reportes import (
    _crear_qr_verificacion,
    _dibujar_qr_y_enlace
)


class VerificacionReporteQrTest(TestCase):
    def crear_token(self, **cambios):
        contenido = {
            "tipo": "clientes",
            "fecha_generacion": "12/11/2026 22:00:00",
            "datos": [
                {"etiqueta": "Total de clientes", "valor": "8"}
            ]
        }
        contenido.update(cambios)
        return signing.dumps(
            contenido,
            salt="reporte-verificacion",
            compress=True
        )

    def test_qr_contiene_url_con_token_firmado(self):
        request = RequestFactory().post("/", HTTP_HOST="testserver")
        imagen_qr = Mock()
        imagen_qr.save.side_effect = (
            lambda buffer, format: buffer.write(b"png")
        )

        with patch(
            "inicio_sesion.views.reportes.qrcode.make",
            return_value=imagen_qr
        ) as crear_imagen:
            _crear_qr_verificacion(
                request,
                "clientes",
                datetime(2026, 11, 12, 22, 0),
                [{"etiqueta": "Total de clientes", "valor": "8"}]
            )

        url = crear_imagen.call_args.args[0]
        self.assertEqual(urlsplit(url).path, reverse("verificar_reporte_qr"))
        token = parse_qs(urlsplit(url).query)["token"][0]
        self.assertEqual(
            signing.loads(token, salt="reporte-verificacion")["tipo"],
            "clientes"
        )

    def test_enlace_corto_del_qr_es_clicable_en_el_pdf(self):
        canvas = Mock()
        url = "https://example.com/validar_reporte_qr/?token=firmado"

        with patch(
            "inicio_sesion.views.reportes.ImageReader",
            return_value="imagen-qr"
        ):
            _dibujar_qr_y_enlace(
                canvas,
                BytesIO(),
                url,
                612,
                792
            )

        canvas.drawRightString.assert_called_once_with(
            514,
            687,
            "Verificar QR"
        )
        canvas.linkURL.assert_called_once()
        self.assertEqual(canvas.linkURL.call_args.args[0], url)

    def test_cabeceras_de_reportes_muestran_qr_y_enlace_clicable(self):
        from inicio_sesion.views import reportes

        cabeceras = (
            reportes.encabezado_bitacora_pdf,
            reportes.encabezado_inicios_sesiones_pdf,
            reportes.encabezado_intentos_sesion_pdf,
            reportes.encabezado_lista_empleados_pdf,
            reportes.encabezado_datos_pdf,
            reportes.encabezado_incidencia_pdf,
            reportes.encabezado_lista_equipos_pdf,
            reportes.encabezado_lista_entrega_equipos_pdf,
            reportes.encabezado_lista_admin_pdf,
        )
        url = "https://example.com/validar_reporte_qr/?token=firmado"

        for cabecera in cabeceras:
            with self.subTest(cabecera=cabecera.__name__):
                canvas = Mock()
                with patch(
                    "inicio_sesion.views.reportes.ImageReader",
                    return_value="imagen-qr"
                ):
                    cabecera(
                        canvas,
                        Mock(page=1, pagesize=(792, 612)),
                        "logo-inexistente.png",
                        BytesIO(),
                        url
                    )

                canvas.linkURL.assert_called_once()
                enlace = canvas.linkURL.call_args
                self.assertEqual(enlace.args[0], url)
                x_derecha, y_texto, _ = (
                    canvas.drawRightString.call_args.args
                )
                self.assertEqual(
                    enlace.args[1],
                    (
                        x_derecha - 60,
                        y_texto - 4,
                        x_derecha + 3,
                        y_texto + 10
                    )
                )
                self.assertEqual(
                    enlace.kwargs,
                    {"relative": 0, "thickness": 0}
                )

    def test_tipos_de_reportes_de_equipos_aceptan_qr_firmado(self):
        for tipo in ("entrega_equipos", "asignaciones_equipos"):
            with self.subTest(tipo=tipo):
                response = self.client.get(
                    reverse("verificar_reporte_qr"),
                    {"token": self.crear_token(tipo=tipo)}
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Reporte auténtico")

    def test_muestra_datos_cuando_la_firma_es_valida(self):
        response = self.client.get(
            reverse("verificar_reporte_qr"),
            {"token": self.crear_token()}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reporte auténtico")
        self.assertContains(response, "Total de clientes")
        self.assertContains(response, "12/11/2026 22:00:00")

    def test_muestra_error_si_el_token_fue_alterado(self):
        token = self.crear_token()
        token_alterado = token[:-1] + ("A" if token[-1] != "A" else "B")

        response = self.client.get(
            reverse("verificar_reporte_qr"),
            {"token": token_alterado}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Firma no válida")
        self.assertNotContains(response, "Total de clientes")
