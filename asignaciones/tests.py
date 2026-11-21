import json

from django.test import RequestFactory, TestCase

from inicio_sesion.models import (
    encargados_administrativos,
    supervisores_encargados,
    turnos_laborales,
    usuarios,
)

from .models import (
    categoria_equipo,
    equipos,
    entrega_equipos,
    historial_inventario_equipo,
)
from .views.entrega_equipo import correccion_entrega_equipos


class CantidadDevueltaCorreccionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        usuario_admin = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="Administrador",
            nombres="Admin",
            apellidos="Prueba",
            cedula_identidad="V-100",
        )
        encargados_administrativos.objects.create(id_usuario=usuario_admin)

        usuario_supervisor = usuarios.objects.create(
            tipo_usuario="NATURAL",
            nombre_razon_social="Supervisor",
            nombres="Supervisor",
            apellidos="Prueba",
            cedula_identidad="V-200",
        )
        turno, _ = turnos_laborales.objects.get_or_create(
            nombre="T_CORRECCION"
        )
        self.supervisor = supervisores_encargados.objects.create(
            id_usuario=usuario_supervisor,
            id_turno=turno,
        )

        categoria = categoria_equipo.objects.create(
            nombre="Categoría de prueba para corrección"
        )
        self.equipo = equipos.objects.create(
            nombre="Equipo de prueba de devolución",
            codigo="TEST-RETURN-001",
            observacion="",
            cantidad_disponible=10,
            id_categoria=categoria,
        )
        self.entrega = entrega_equipos.objects.create(
            supervisor_encargado=self.supervisor,
            id_equipo=self.equipo,
            cantidad_entregada=5,
            cantidad_disponible=2,
            estado="ASIGNADO",
        )

    def corregir(self, tipo_correccion):
        request = self.factory.post(
            "/asignaciones/correccion_entrega_equipos/",
            {
                "supervisores_encargados": self.supervisor.pk,
                "categoria_equipos": self.equipo.id_categoria_id,
                "equipos_entregados": self.entrega.pk,
                "tipo_correccion": tipo_correccion,
                "cantidad_actualizar": self.entrega.cantidad_entregada,
                "observacion_entrega": "Corrección de prueba",
                "motivo_correccion": "Registro incorrecto",
            },
        )
        request.session = {"cedula_identidad": "V-100"}
        return correccion_entrega_equipos(request)

    def assert_devuelve_la_entrega_completa(self, tipo_correccion):
        response = self.corregir(tipo_correccion)

        self.assertEqual(json.loads(response.content)["estado"], "exito")

        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.cantidad_disponible, 15)

        movimiento = historial_inventario_equipo.objects.get(
            id_equipo=self.equipo,
            tipo_movimiento="CORRECCION",
        )
        self.assertEqual(movimiento.cantidad_movimiento, 5)

    def test_retirar_devuelve_todas_las_unidades_entregadas(self):
        self.assert_devuelve_la_entrega_completa("RETIRAR")

    def test_error_humano_devuelve_todas_las_unidades_entregadas(self):
        self.assert_devuelve_la_entrega_completa("ERROR_HUMANO")
