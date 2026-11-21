from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Productos
    path('buscar_categoria/', views.buscar_categoria, name='buscar_categoria'),
    path('estado_categoria/', views.estado_categoria, name='estado_categoria'),
    path('actualizar_categoria/', views.actualizar_categoria, name='actualizar_categoria'),
    path('registrar_categorias/', views.registrar_categorias, name='registrar_categorias'),
    path('gestionar_categorias/', views.gestionar_categorias, name='gestionar_categorias'),
    path('categorias_productos/', views.categorias_productos, name='categorias_productos'),
   
    path('unidades_medida/', views.unidades_medida, name='unidades_medida'),
    path('registrar_productos/', views.registrar_productos, name='registrar_productos'),
    path('visualizar_productos/', views.visualizar_productos, name='visualizar_productos'),
    path('productos_registrados/', views.productos_registrados, name='productos_registrados'),
    path('detalle_producto_registrado/', views.detalle_producto_registrado, name='detalle_producto_registrado'),
    path('lista_productos_pdf/', views.lista_productos_pdf, name='lista_productos_pdf'),
    path('lista_detalle_producto_pdf/', views.lista_detalle_producto_pdf, name='lista_detalle_producto_pdf'),
    path('actualizar_producto/', views.actualizar_producto, name='actualizar_producto'),
    path('buscar_datos_producto/', views.buscar_datos_producto, name='buscar_datos_producto'),
    
    path('estado_producto/', views.estado_producto, name='estado_producto'),
    
    path('actualizar_existencia/', views.actualizar_existencia, name='actualizar_existencia'),
    path('productos_registrados_venta/', views.productos_registrados_venta, name='productos_registrados_venta'),
    path('datos_producto_existencia/', views.datos_producto_existencia, name='datos_producto_existencia'),
    
    path('registrar_precio_volumen/', views.registrar_precio_volumen, name='registrar_precio_volumen'),
    path('precios_volumna_producto/', views.precios_volumna_producto, name='precios_volumna_producto'),
    path('ultimo_registro_volumen_producto/', views.ultimo_registro_volumen_producto, name='ultimo_registro_volumen_producto'),
    
    path('movimiento_producto/', views.movimiento_producto, name='movimiento_producto'),
    path('lista_inventario_pdf/', views.lista_inventario_pdf, name='lista_inventario_pdf'),
    
    path('productos_exhibicion/', views.productos_exhibicion, name='productos_exhibicion'),

    # Cuentas Bancarias
    path('validar_numero_cuenta/', views.validar_numero_cuenta, name='validar_numero_cuenta'),
    path('registrar_cuentas/', views.registrar_cuentas, name='registrar_cuentas'),
    path('gestionar_cuentas/', views.gestionar_cuentas, name='gestionar_cuentas'),
    path('visualizar_cuentas/', views.visualizar_cuentas, name='visualizar_cuentas'),
    path('actualizar_cuentas/', views.actualizar_cuentas, name='actualizar_cuentas'),
    path('buscar_cuentas/', views.buscar_cuentas, name='buscar_cuentas'),
    path('estado_cuenta/', views.estado_cuenta, name='estado_cuenta'),
    path('metodos_registrados/', views.metodos_registrados, name='metodos_registrados'),

    # Compra/Ventas de los productos
    path('productos_disponible_venta/', views.productos_disponible_venta, name='productos_disponible_venta'),
    path('registrar_compra_cliente/', views.registrar_compra_cliente, name='registrar_compra_cliente'),
    path('precio_volumen_producto/', views.precio_volumen_producto, name='precio_volumen_producto'),
    
    path('fechas_compras_cliente/', views.fechas_compras_cliente, name='fechas_compras_cliente'),
    path('estado_compra_cliente/', views.estado_compra_cliente, name='estado_compra_cliente'),
    path('historial_compra_cliente/', views.historial_compra_cliente, name='historial_compra_cliente'),
    path('datos_factura_cliente/', views.datos_factura_cliente, name='datos_factura_cliente'),
    
    path('verificar_compras_clientes/', views.verificar_compras_clientes, name='verificar_compras_clientes'),
    path('obtener_venta_verificar/', views.obtener_venta_verificar, name='obtener_venta_verificar'),
    path('detalle_venta_verificar/', views.detalle_venta_verificar, name='detalle_venta_verificar'),
    
    path('estado_compra_venta/', views.estado_compra_venta, name='estado_compra_venta'),
    path('aceptar_venta/', views.aceptar_venta, name='aceptar_venta'),
    path('rechazar_venta/', views.rechazar_venta, name='rechazar_venta'),

    # Estadisticas ganancias y gastos de la empresa
    path('ganancias_ventas/', views.ganancias_ventas, name='ganancias_ventas'),
    path('visualizar_ganancias/', views.visualizar_ganancias, name='visualizar_ganancias'),
    path('ganancia_producto/', views.ganancia_producto, name='ganancia_producto'),
    path('estadisticas/ganancia_periodo/', views.ganancia_periodo, name='ganancia_periodo'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )