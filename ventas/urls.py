from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Clientes
    path('validar_identificador/', views.validar_identificador, name='validar_identificador'),
    path('validar_telefono_cliente/', views.validar_telefono_cliente, name='validar_telefono_cliente'),
    path('validar_correo_cliente/', views.validar_correo_cliente, name='validar_correo_cliente'),
    path('registrar_clientes_ventas/', views.registrar_clientes_ventas, name='registrar_clientes_ventas'),
    path('buscar_datos_cliente/', views.buscar_datos_cliente, name='buscar_datos_cliente'),
    path('actualizar_clientes_ventas/', views.actualizar_clientes_ventas, name='actualizar_clientes_ventas'),
    path('visualizar_clientes_ventas/', views.visualizar_clientes_ventas, name='visualizar_clientes_ventas'),
    path('clientes_registrados_ventas/', views.clientes_registrados_ventas, name='clientes_registrados_ventas'),
    path('detalle_registro_cliente/', views.detalle_registro_cliente, name='detalle_registro_cliente'),
    path('clientes_registrados_pdf/', views.clientes_registrados_pdf, name='clientes_registrados_pdf'),
    path('detalle_cliente_pdf/', views.detalle_cliente_pdf, name='detalle_cliente_pdf'),

    # Productos
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
    
    path('actualizar_existencia/', views.actualizar_existencia, name='actualizar_existencia'),
    path('productos_registrados_venta/', views.productos_registrados_venta, name='productos_registrados_venta'),
    path('datos_producto_existencia/', views.datos_producto_existencia, name='datos_producto_existencia'),
    
    path('registrar_precio_volumen/', views.registrar_precio_volumen, name='registrar_precio_volumen'),
    path('precios_volumna_producto/', views.precios_volumna_producto, name='precios_volumna_producto'),
    path('ultimo_registro_volumen_producto/', views.ultimo_registro_volumen_producto, name='ultimo_registro_volumen_producto'),

    # Ventas
    path('registrar_pago_productos/', views.registrar_pago_productos, name='registrar_pago_productos'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )