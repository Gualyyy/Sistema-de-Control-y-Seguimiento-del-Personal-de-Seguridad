import json
from decimal import Decimal
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, modify_settings
from django.urls import reverse

from inicio_sesion.models import cliente as Cliente, contacto, usuarios
from ventas.models import (
    cuenta_destino_pago,
    detalle_venta,
    existencia_inventario,
    metodo_pago,
    movimiento_inventario,
    precio_volumen,
    producto,
    categoria_producto,
    tipo_movimiento,
    unidad_medida,
    venta,
)


class ProductosExhibicionPublicosTest(TestCase):
    def test_productos_exhibicion_es_publico(self):
        response = self.client.get(reverse("productos_exhibicion"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "exito")


@modify_settings(
    MIDDLEWARE={
        "remove": "inicio_sesion.middleware.RequerirSesionMiddleware"
    }
)
class RechazarVentaTest(TestCase):
    def setUp(self):
        usuario = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="",
            nombres="Cliente",
            apellidos="Prueba",
            cedula_identidad="87654321",
        )
        cliente_actual = Cliente.objects.create(id_usuario=usuario)
        self.venta_actual = venta.objects.create(
            comprobante="RECHAZO-001",
            id_cliente=cliente_actual,
            estado=venta.Estado.PENDIENTE_CONFIRMACION,
        )
        self.unidad = unidad_medida.objects.create(
            nombre="Unidad de rechazo",
            abreviatura="UND-R",
            permite_decimales=True,
        )
        categoria = categoria_producto.objects.create(
            nombre="Categoría de rechazo"
        )
        self.producto_actual = producto.objects.create(
            nombre="Producto de rechazo",
            codigo="RECHAZO-001",
            precio_base=Decimal("10.00"),
            costo_base=Decimal("5.00"),
            id_categoria=categoria,
            id_unidad=self.unidad,
        )
        self.existencia = existencia_inventario.objects.create(
            id_producto=self.producto_actual,
            cantidad_actual=7,
        )
        detalle_venta.objects.create(
            id_venta=self.venta_actual,
            id_producto=self.producto_actual,
            cantidad=Decimal("2.500"),
            precio_unidad=Decimal("10.00"),
            descuento=Decimal("0.00"),
            subtotal=Decimal("25.00"),
            costo_unitario=Decimal("5.00"),
            costo_total=Decimal("12.50"),
        )

    def test_rechazar_venta_guarda_estado_y_motivo(self):
        response = self.client.post(
            reverse("rechazar_venta"),
            {
                "id_venta": self.venta_actual.id_venta,
                "motivo_rechazo": venta.MotivoRechazo.COMPROBANTE_INVALIDO,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "exito")

        self.venta_actual.refresh_from_db()
        self.assertEqual(self.venta_actual.estado, venta.Estado.RECHAZADA)
        self.assertEqual(
            self.venta_actual.motivo_rechazo,
            venta.MotivoRechazo.COMPROBANTE_INVALIDO,
        )
        self.existencia.refresh_from_db()
        self.assertEqual(self.existencia.cantidad_actual, Decimal("7.000"))
        self.assertFalse(
            movimiento_inventario.objects.filter(
                id_venta=self.venta_actual,
            ).exists()
        )

    def test_rechazar_venta_devuelve_inventario_descontado_previamente(self):
        self.existencia.cantidad_actual = Decimal("4.000")
        self.existencia.save(update_fields=["cantidad_actual"])
        self.venta_actual.inventario_descontado = True
        self.venta_actual.save(update_fields=["inventario_descontado"])
        response = self.client.post(
            reverse("rechazar_venta"),
            {
                "id_venta": self.venta_actual.id_venta,
                "motivo_rechazo": venta.MotivoRechazo.COMPROBANTE_INVALIDO,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.venta_actual.refresh_from_db()
        self.assertFalse(self.venta_actual.inventario_descontado)
        self.existencia.refresh_from_db()
        self.assertEqual(self.existencia.cantidad_actual, Decimal("7.000"))
        movimiento = movimiento_inventario.objects.get(
            id_venta=self.venta_actual,
            id_producto=self.producto_actual,
        )
        self.assertEqual(movimiento.cantidad, Decimal("2.500"))
        self.assertEqual(
            movimiento.id_tipo_movimiento.nombre,
            "Devolución",
        )

    def test_rechazar_venta_requiere_motivo_valido(self):
        response = self.client.post(
            reverse("rechazar_venta"),
            {
                "id_venta": self.venta_actual.id_venta,
                "motivo_rechazo": "MOTIVO_DESCONOCIDO",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.venta_actual.refresh_from_db()
        self.assertEqual(
            self.venta_actual.estado,
            venta.Estado.PENDIENTE_CONFIRMACION,
        )

    def test_rechazar_venta_requiere_motivo(self):
        response = self.client.post(
            reverse("rechazar_venta"),
            {"id_venta": self.venta_actual.id_venta},
        )

        self.assertEqual(response.status_code, 400)
        self.venta_actual.refresh_from_db()
        self.assertEqual(
            self.venta_actual.estado,
            venta.Estado.PENDIENTE_CONFIRMACION,
        )

    def test_rechazar_venta_procesada_no_se_puede_rechazar(self):
        self.venta_actual.estado = venta.Estado.CONFIRMADA
        self.venta_actual.save(update_fields=["estado"])

        response = self.client.post(
            reverse("rechazar_venta"),
            {
                "id_venta": self.venta_actual.id_venta,
                "motivo_rechazo": venta.MotivoRechazo.COMPROBANTE_INVALIDO,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.venta_actual.refresh_from_db()
        self.assertEqual(self.venta_actual.estado, venta.Estado.CONFIRMADA)
        self.assertEqual(self.venta_actual.motivo_rechazo, "")


@modify_settings(
    MIDDLEWARE={
        "remove": "inicio_sesion.middleware.RequerirSesionMiddleware"
    }
)
class RegistrarCompraClienteTest(TransactionTestCase):
    def setUp(self):
        usuario = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="",
            nombres="Cliente",
            apellidos="Prueba",
            cedula_identidad="12345678",
        )
        Cliente.objects.create(id_usuario=usuario)
        contacto.objects.create(
            id_usuario=usuario,
            telefono_principal="04120000000",
            correo_principal="cliente@example.com",
        )

        session = self.client.session
        session["cedula_identidad"] = usuario.cedula_identidad
        session.save()

        self.metodo = metodo_pago.objects.create(nombre="Transferencia")
        self.cuenta = cuenta_destino_pago.objects.create(
            id_metodo_pago=self.metodo,
            banco="Banco de prueba",
            documento="12345678",
        )

        categoria, _ = categoria_producto.objects.get_or_create(
            nombre="Prueba"
        )
        unidad, _ = unidad_medida.objects.get_or_create(
            nombre="Unidad",
            defaults={"abreviatura": "UND"},
        )
        self.producto = producto.objects.create(
            nombre="Producto de prueba",
            codigo="PRUEBA-001",
            precio_base=Decimal("10.00"),
            costo_base=Decimal("5.00"),
            id_categoria=categoria,
            id_unidad=unidad,
        )
        existencia_inventario.objects.create(
            id_producto=self.producto,
            cantidad_actual=10,
        )
        precio_volumen.objects.create(
            id_producto=self.producto,
            cantidad_minima=5,
            porcentaje_descuento=Decimal("20.00"),
            activo=True,
        )

    def test_registra_descuento_por_volumen_como_porcentaje(self):
        producto_sin_descuentos = producto.objects.create(
            nombre="Producto descuento por volumen",
            codigo="PRUEBA-DESCUENTO",
            precio_base=Decimal("20.00"),
            costo_base=Decimal("10.00"),
            id_categoria=self.producto.id_categoria,
            id_unidad=self.producto.id_unidad,
        )

        response = self.client.post(
            reverse("registrar_precio_volumen"),
            {
                "producto_registrado": producto_sin_descuentos.id_producto,
                "cantidad_minima": "5",
                "cantidad_maxima": "10",
                "porcentaje_descuento": "12.50",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "exito")
        descuento = precio_volumen.objects.get(
            id_producto=producto_sin_descuentos
        )
        self.assertEqual(
            descuento.porcentaje_descuento,
            Decimal("12.50"),
        )

    def test_consulta_factura_cliente_devuelve_datos_de_usuario_y_descuento(self):
        venta_actual = venta.objects.create(
            comprobante="FACTURA-CLIENTE-001",
            id_cliente=Cliente.objects.get(
                id_usuario__cedula_identidad="12345678"
            ),
            subtotal=Decimal("50.00"),
            descuento=Decimal("10.00"),
            impuesto=Decimal("6.40"),
            total=Decimal("46.40"),
            tasa_cambio=Decimal("1.00"),
            estado=venta.Estado.PENDIENTE_CONFIRMACION,
        )
        detalle_venta.objects.create(
            id_venta=venta_actual,
            id_producto=self.producto,
            cantidad=Decimal("5.000"),
            precio_unidad=Decimal("10.00"),
            descuento=Decimal("10.00"),
            subtotal=Decimal("40.00"),
            costo_unitario=Decimal("5.00"),
            costo_total=Decimal("25.00"),
        )

        response = self.client.post(
            reverse("datos_factura_cliente"),
            {"id_venta": venta_actual.id_venta},
        )

        self.assertEqual(response.status_code, 200)
        factura = response.json()["factura"]
        self.assertEqual(factura["cliente"]["nombre"], "Cliente")
        self.assertEqual(factura["cliente"]["apellido"], "Prueba")
        self.assertEqual(
            factura["productos"][0]["descuento"],
            "10.00",
        )
        self.assertEqual(factura["resumen"]["descuento"], "10.00")

    @patch(
        "ventas.views.compras.enviar_correo_compra_con_factura",
        return_value=True,
    )
    def test_registra_compra_pendiente_sin_descontar_y_descuenta_al_confirmar(
        self, enviar_correo
    ):
        response = self.client.post(
            reverse("registrar_compra_cliente"),
            {
                "productos": json.dumps([
                    {"id_producto": self.producto.id_producto, "cantidad": 5}
                ]),
                "id_metodo": self.metodo.id_metodo_pago,
                "id_cuenta": self.cuenta.id_cuenta_destino,
                "referencia": "123456",
                "capture_pago": SimpleUploadedFile(
                    "capture.png",
                    b"contenido del capture",
                    content_type="image/png",
                ),
                "telefono_origen": "04120000000",
                "banco_origen": "Banco de prueba",
                "tasa_cambio": "400.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "exito")
        enviar_correo.assert_called_once()
        contexto_correo = enviar_correo.call_args.args[1]
        self.assertIsNotNone(contexto_correo["fecha_compra"])
        self.assertEqual(len(contexto_correo["articulos"]), 1)
        self.assertEqual(contexto_correo["subtotal_usd"], Decimal("50.00"))
        self.assertEqual(contexto_correo["descuento_usd"], Decimal("10.00"))
        self.assertEqual(contexto_correo["total_usd"], Decimal("46.40"))

        registro = venta.objects.get(comprobante=response.json()["comprobante"])
        self.assertEqual(registro.tasa_cambio, Decimal("400.00"))
        self.assertEqual(registro.motivo_rechazo, "")
        self.assertEqual(
            registro.estado,
            venta.Estado.PENDIENTE_CONFIRMACION,
        )
        self.assertFalse(registro.inventario_descontado)
        self.assertEqual(registro.subtotal, Decimal("20000.00"))
        self.assertEqual(registro.descuento, Decimal("4000.00"))
        self.assertEqual(registro.impuesto, Decimal("2560.00"))
        self.assertEqual(registro.total, Decimal("18560.00"))
        self.assertEqual(registro.pagos.get().monto, Decimal("18560.00"))

        historial_response = self.client.post(
            reverse("historial_compra_cliente"),
            {
                "accion": "historial",
                "fecha_compra": "",
                "estado": "",
            },
        )
        producto_historial = historial_response.json()["compras"][0]["productos"][0]
        self.assertEqual(producto_historial["descuento"], "4000.00")
        self.assertEqual(producto_historial["subtotal"], "16000.00")

        registro_pago = registro.pagos.get()
        self.assertTrue(
            registro_pago.capture_pago.name.startswith("captures_pago/capture")
        )
        self.assertTrue(registro_pago.capture_pago.name.endswith(".png"))
        self.addCleanup(registro_pago.capture_pago.delete, save=False)

        detalle = registro.detalles.get()
        self.assertEqual(detalle.precio_unidad, Decimal("4000.00"))
        self.assertEqual(detalle.descuento, Decimal("4000.00"))
        self.assertEqual(detalle.subtotal, Decimal("16000.00"))
        self.producto.existencia.refresh_from_db()
        self.assertEqual(
            self.producto.existencia.cantidad_actual,
            Decimal("10.000"),
        )
        self.assertFalse(
            movimiento_inventario.objects.filter(id_venta=registro).exists()
        )

        detalle_response = self.client.post(
            reverse("detalle_venta_verificar"),
            {"id_venta": registro.id_venta},
        )
        datos = detalle_response.json()
        self.assertEqual(datos["venta"]["tasa_cambio"], "400.00")
        self.assertEqual(datos["productos"][0]["precio_unidad"], "10.00")
        self.assertEqual(datos["productos"][0]["precio_unidad_ves"], "4000.00")
        self.assertEqual(datos["productos"][0]["descuento"], "10.00")
        self.assertEqual(datos["productos"][0]["descuento_ves"], "4000.00")
        self.assertEqual(datos["resumen"]["subtotal"], "50.00")
        self.assertEqual(datos["resumen"]["descuento"], "10.00")
        self.assertEqual(datos["resumen"]["total"], "46.40")
        self.assertEqual(datos["resumen"]["total_ves"], "18560.00")
        self.assertEqual(datos["pago"]["monto"], "46.40")
        self.assertEqual(datos["pago"]["monto_ves"], "18560.00")
        self.assertIn(
            "captures_pago/capture",
            datos["pago"]["capture_pago"]
        )

        with patch(
            "ventas.views.compras.enviar_correo_compra_confirmada_con_factura",
            return_value=True,
        ):
            confirmar_response = self.client.post(
                reverse("aceptar_venta"),
                {"id_venta": registro.id_venta},
            )

        self.assertEqual(confirmar_response.status_code, 200)
        self.assertEqual(confirmar_response.json()["estado"], "exito")
        registro.refresh_from_db()
        self.assertEqual(registro.estado, venta.Estado.CONFIRMADA)
        self.assertTrue(registro.inventario_descontado)
        self.producto.existencia.refresh_from_db()
        self.assertEqual(
            self.producto.existencia.cantidad_actual,
            Decimal("5.000"),
        )
        movimiento = movimiento_inventario.objects.get(id_venta=registro)
        self.assertEqual(movimiento.id_tipo_movimiento.nombre, "Venta")

    @patch(
        "ventas.views.compras.enviar_correo_compra",
        side_effect=OSError("Correo no disponible"),
    )
    def test_error_de_correo_no_revierte_compra(self, enviar_correo):
        response = self.client.post(
            reverse("registrar_compra_cliente"),
            {
                "productos": json.dumps([
                    {"id_producto": self.producto.id_producto, "cantidad": 1}
                ]),
                "id_metodo": self.metodo.id_metodo_pago,
                "id_cuenta": self.cuenta.id_cuenta_destino,
                "referencia": "654321",
                "capture_pago": SimpleUploadedFile(
                    "capture.png",
                    b"contenido del capture",
                    content_type="image/png",
                ),
                "telefono_origen": "04120000000",
                "banco_origen": "Banco de prueba",
                "tasa_cambio": "400.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "exito")
        self.assertIn("pendiente de revisión", response.json()["descripcion"])
        self.assertEqual(venta.objects.count(), 1)
        enviar_correo.assert_called_once()
        registro = venta.objects.get()
        self.assertEqual(registro.estado, venta.Estado.PENDIENTE_CONFIRMACION)
        self.assertEqual(registro.subtotal, Decimal("4000.00"))
        self.assertEqual(registro.descuento, Decimal("0.00"))
        self.assertEqual(registro.detalles.get().descuento, Decimal("0.00"))
        self.assertFalse(registro.inventario_descontado)
        self.producto.existencia.refresh_from_db()
        self.assertEqual(
            self.producto.existencia.cantidad_actual,
            Decimal("10.000"),
        )
