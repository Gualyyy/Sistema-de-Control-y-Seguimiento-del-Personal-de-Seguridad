document.addEventListener("DOMContentLoaded", () => {

    const comprobante_venta = document.getElementById("comprobante_venta");
    const fecha_registro_compra = document.getElementById("fecha_registro_compra");
    const nombre_cliente = document.getElementById("nombre_cliente");
    const identificacion_cliente = document.getElementById("identificacion_cliente");
    const correo_cliente = document.getElementById("correo_cliente");
    const estado_factura = document.getElementById("estado_factura");

    const detalle_productos = document.getElementById("detalle_productos");

    const subtotal = document.getElementById("subtotal");
    const descuento_compra = document.getElementById("descuento_compra");
    const iva_compra = document.getElementById("iva_compra");
    const total_compra = document.getElementById("total_compra");
    const tasa_cambio_compra = document.getElementById("tasa_cambio_compra");
    const total_usd_compra = document.getElementById("total_usd_compra");

    const metodo_pago = document.getElementById("metodo_pago");
    const referencia_pago = document.getElementById("referencia_pago");
    const monto_pago = document.getElementById("monto_pago");
    const estado_pago = document.getElementById("estado_pago");
    const banco_pago = document.getElementById("banco_pago");
    const documento_pago = document.getElementById("documento_pago");
    const numero_movil_pago = document.getElementById("numero_movil_pago");
    const tipo_cuenta_pago = document.getElementById("tipo_cuenta_pago");

    const select_fecha_compra = document.getElementById("fecha_compra");
    const select_estado_compra = document.getElementById("estado_compra");

    const contenedor_compras = document.getElementById("contenedor_compras");


    function mostrarCompras() {
        contenedor_compras.innerHTML = "";

        if (compras_recibidas.length === 0) {

            contenedor_compras.innerHTML = `
            <div class="texto_sin_registros">
                No hay compras registradas.
            </div>
        `;

            return;
        }

        compras_recibidas.forEach(compra => {
            const productos = compra.productos.map(producto => `
            <li>
                ${producto.nombre} (${producto.cantidad} ${producto.unidad})
            </li>
        `).join("");

            const estados = {
                CONFIRMADA: "confirmada",
                PENDIENTE_CONFIRMACION: "pendiente",
                RECHAZADA: "rechazada",
                ANULADA: "anulada"
            };

            const tarjeta = document.createElement("div");
            tarjeta.classList.add("tarjeta_compra");

            tarjeta.innerHTML = `
            <div class="compra_identificacion">

                <div class="numero_comprobante">
                    <i class="fa-solid fa-file-lines"></i>
                    <strong>N.º ${compra.comprobante}</strong>
                </div>

                <div>
                    <i class="fa-regular fa-calendar"></i>
                    <span>${compra.fecha}</span>
                </div>

                <div>
                    <i class="fa-regular fa-clock"></i>
                    <span>${compra.hora}</span>
                </div>

            </div>

            <div class="compra_estado_total">

                <span class="estado_compra ${estados[compra.estado] || ""}">
                    ${compra.estado_display}
                </span>

                <strong class="total_compra">
                    $ ${Number(compra.total).toFixed(2)}
                </strong>

                <span class="moneda_compra">(USD)</span>

            </div>

            <div class="compra_productos">

                <strong>Productos:</strong>

                <ul>
                    ${productos}
                </ul>

            </div>

            <div class="compra_acciones">

                <button
                    type="button"
                    class="btn_detalle_compra"
                    data-id="${compra.id_venta}">

                    <i class="fa-solid fa-eye"></i>
                    Ver Detalle

                </button>

            </div>
        `;

            contenedor_compras.appendChild(tarjeta);
        });
    }

    async function historial_compras() {
        try {
            const formulario = new FormData();
            formulario.append("accion", "historial");
            formulario.append("fecha_compra", select_fecha_compra.value);
            formulario.append("estado", select_estado_compra.value);

            const respuesta = await fetch("/ventas/historial_compra_cliente/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                compras_recibidas = [];
                mostrarCompras();
                return;
            }

            compras_recibidas = resultado.compras;

            mostrarCompras();
        } catch (error) {
            console.error(error);
        }
    }

    async function fechas_registradas() {
        try {
            const respuesta = await fetch("/ventas/fechas_compras_cliente/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_fecha_compra.innerHTML = `
                <option value="" selected>Todas las fechas</option>
            `;

            resultado.fechas.forEach(fecha => {
                const option = document.createElement("option");
                option.value = fecha;
                option.textContent = fecha;
                select_fecha_compra.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    fechas_registradas();

    async function estados_compras() {
        try {
            const respuesta = await fetch("/ventas/estado_compra_cliente/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_estado_compra.innerHTML = `
                <option value="" selected>Todas las fechas</option>
            `;

            resultado.estados.forEach(estado => {
                const option = document.createElement("option");
                option.value = estado.valor;
                option.textContent = estado.nombre;
                select_estado_compra.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    estados_compras();

    select_fecha_compra.addEventListener("change", () => {
        historial_compras();
    });

    select_estado_compra.addEventListener("change", () => {
        historial_compras();
    });
    historial_compras();

    let id_venta = "";

    contenedor_compras.addEventListener("click", async (e) => {

        const boton = e.target.closest(".btn_detalle_compra");

        if (!boton) return;

        id_venta = boton.dataset.id;

        await datos_factura();
    });

    // FORMATEAR MONEDA
    function formatoMoneda(valor, moneda = "VES") {
        return new Intl.NumberFormat("es-VE", {
            style: "currency",
            currency: moneda,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(Number(valor) || 0);
    }

    // FORMATEAR FECHA
    function formatoFecha(fecha, hora) {
        return hora ? `${fecha} - ${hora}` : fecha;
    }

    // MOSTRAR ESTADO
    function obtenerEstado(estado) {
        const estados = {
            BORRADOR: "Borrador",
            PENDIENTE_CONFIRMACION: "Pendiente de confirmación",
            CONFIRMADA: "Confirmada",
            RECHAZADA: "Rechazada",
            ANULADA: "Anulada",
            REGISTRADO: "Registrado",
            ANULADO: "Anulado"
        };

        return estados[estado] || estado || "No disponible";
    }

    // CONSULTAR Y MOSTRAR FACTURA
    async function datos_factura() {
        try {
            const formulario = new FormData();
            formulario.append("id_venta", id_venta);

            const csrf = document.querySelector("[name=csrfmiddlewaretoken]");

            const respuesta = await fetch("/ventas/datos_factura_cliente/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf.value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (!respuesta.ok || resultado.estado !== "exito") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const factura = resultado.factura;
            const cliente = factura.cliente;
            const resumen = factura.resumen;

            // DATOS GENERALES
            comprobante_venta.textContent = factura.comprobante || "No disponible";

            fecha_registro_compra.textContent = formatoFecha(
                factura.fecha,
                factura.hora
            );

            nombre_cliente.textContent = (
                `${cliente.nombre || ""} ${cliente.apellido || ""}`.trim()
            );

            identificacion_cliente.textContent = cliente.cedula || "No disponible";
            correo_cliente.textContent = cliente.correo || "No disponible";

            estado_factura.textContent = factura.estado_display || obtenerEstado(
                factura.estado
            );

            // DETALLE DE PRODUCTOS
            detalle_productos.replaceChildren();

            if (factura.productos.length === 0) {
                const fila = document.createElement("tr");
                const celda = document.createElement("td");

                celda.colSpan = 8;
                celda.textContent = "No hay productos registrados en esta compra.";

                fila.appendChild(celda);
                detalle_productos.appendChild(fila);

            } else {

                factura.productos.forEach((articulo, indice) => {

                    const fila = document.createElement("tr");

                    const valores = [
                        indice + 1,
                        articulo.nombre,
                        articulo.codigo,
                        articulo.cantidad,
                        articulo.unidad,
                        formatoMoneda(articulo.precio_unitario),
                        formatoMoneda(articulo.descuento),
                        formatoMoneda(articulo.subtotal)
                    ];

                    valores.forEach(valor => {
                        const celda = document.createElement("td");
                        celda.textContent = valor ?? "No disponible";
                        fila.appendChild(celda);
                    });

                    detalle_productos.appendChild(fila);
                });
            }

            // RESUMEN ECONÓMICO
            subtotal.textContent = formatoMoneda(resumen.subtotal);

            descuento_compra.textContent = formatoMoneda(
                resumen.descuento
            );

            iva_compra.textContent = formatoMoneda(resumen.impuesto);

            total_compra.textContent = formatoMoneda(
                resumen.total
            );

            tasa_cambio_compra.textContent = formatoMoneda(
                resumen.tasa_cambio
            );

            total_usd_compra.textContent = formatoMoneda(
                resumen.total_usd,
                "USD"
            );

            // INFORMACIÓN DEL PAGO
            const pago_actual = factura.pagos?.[0];

            if (pago_actual) {

                metodo_pago.textContent = pago_actual.metodo_pago || "No disponible";

                referencia_pago.textContent = pago_actual.referencia || "No disponible";

                monto_pago.textContent = formatoMoneda(
                    pago_actual.monto
                );

                estado_pago.textContent = obtenerEstado(
                    pago_actual.estado
                );

                banco_pago.textContent = (
                    pago_actual.banco_origen || "No disponible"
                );

                documento_pago.textContent = (
                    pago_actual.cuenta_destino?.documento || "No disponible"
                );

                numero_movil_pago.textContent = (
                    pago_actual.cuenta_destino?.telefono || "No disponible"
                );

                tipo_cuenta_pago.textContent = (
                    pago_actual.cuenta_destino?.tipo_cuenta || "No disponible"
                );

            } else {

                [
                    metodo_pago,
                    referencia_pago,
                    monto_pago,
                    estado_pago,
                    banco_pago,
                    documento_pago,
                    numero_movil_pago,
                    tipo_cuenta_pago
                ].forEach(elemento => {
                    elemento.textContent = "No disponible";
                });
            }

            // MOTIVO DE RECHAZO U OBSERVACIÓN
            const motivo = document.getElementById("motivo_rechazo");
            const observacion = document.getElementById("observacion_factura");

            if (motivo) {
                motivo.textContent = factura.motivo_rechazo || "No aplica";
            }

            if (observacion) {
                observacion.textContent = factura.observacion || "Sin observaciones";
            }

            console.log("Factura cargada:", factura);
        } catch (error) {
            console.error("Error al consultar la factura:", error);
        }
    }
});