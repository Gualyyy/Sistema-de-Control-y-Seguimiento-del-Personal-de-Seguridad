from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.utils.text import get_valid_filename

from ventas.models import categoria_producto, unidad_medida, producto, existencia_inventario, tipo_movimiento, movimiento_inventario, venta, detalle_venta, metodo_pago, pago, categoria_gasto, gasto  
from inicio_sesion.models import bitacora, usuarios

import os
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Image
)

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from xml.sax.saxutils import escape

# Create your views here.

def registrar_pago_productos(request):
    return render(request, "Ventas/registrar_venta.html")

