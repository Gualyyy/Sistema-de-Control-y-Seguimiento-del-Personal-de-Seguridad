document.addEventListener("DOMContentLoaded", () => {

    const select_metodos_pagos = document.getElementById("metodos_pagos");
    const contenedor_compras = document.getElementById("contenedor_compras");

    const btn_rechazar_venta = document.getElementById("btn_rechazar_venta");
    const btn_aceptar_venta = document.getElementById("btn_aceptar_venta");

    const dialogo_rechazado = document.getElementById("dialogo_rechazado");
    const btn_cerrar_rechazado = document.getElementById("btn_cerrar_rechazado");

    const formulario_rechazar = document.getElementById("formulario_rechazar");

    // INFORMACIÓN GENERAL DE LA VENTA
    const input_id_venta = document.getElementById("id_venta");

    const input_comprobante = document.getElementById("comprobante");
    const input_fecha_venta = document.getElementById("fecha_venta");
    const input_estado_venta = document.getElementById("estado_venta");
    const textarea_observacion_venta = document.getElementById("observacion_venta");

    // INFORMACIÓN DEL CLIENTE
    const input_razon_social = document.getElementById("razon_social");
    const input_documento_identidad = document.getElementById("documento_identidad");
    const input_telefono = document.getElementById("telefono");
    const input_correo_electronico = document.getElementById("correo_electronico");

    // PRODUCTOS DE LA VENTA
    const contenedor_detalles_venta = document.getElementById("contenedor_detalles_venta");

    // PAGOS DE LA VENTA
    const input_metodo_pago = document.getElementById("metodo_pago");
    const input_monto = document.getElementById("monto");
    const input_referencia = document.getElementById("referencia");
    const input_banco_origen = document.getElementById("banco_origen");
    const input_telefono_origen = document.getElementById("telefono_origen");
    const input_fecha_pago_origen = document.getElementById("fecha_pago_origen");
    const enlace_capture_pago = document.getElementById("capture_pago_enlace");
    const capture_pago_no_disponible = document.getElementById("capture_pago_no_disponible");

    // INFORMACIÓN DEL RECEPTOR
    const input_banco_receptor = document.getElementById("banco_receptor");
    const input_documento_titular = document.getElementById("documento_titular");
    const input_numero_cuenta = document.getElementById("numero_cuenta");
    const input_tipo_cuenta_receptor = document.getElementById("tipo_cuenta_receptor");
    const input_telefono_receptor = document.getElementById("telefono_receptor");

    // RESUMEN FINANCIERO
    const input_subtotal_venta = document.getElementById("subtotal_venta");
    const input_descuento_venta = document.getElementById("descuento_venta");
    const input_impuesto_venta = document.getElementById("impuesto_venta");
    const input_total_venta = document.getElementById("total_venta");

    let metodo_pago = "", id_venta = "";

    const formato_monto = new Intl.NumberFormat("es-VE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    function mostrar_monto(monto_ves, monto_usd) {
        if (monto_ves !== null && monto_ves !== undefined) {
            return `${formato_monto.format(Number(monto_ves))} Bs.`;
        }

        return `${formato_monto.format(Number(monto_usd))} $`;
    }

    function actualizar_botones_accion(puede_procesar) {
        btn_aceptar_venta.disabled = !puede_procesar;
        btn_rechazar_venta.disabled = !puede_procesar;

        if (puede_procesar) {
            delete btn_aceptar_venta.dataset.inhabilitado;
            delete btn_rechazar_venta.dataset.inhabilitado;
        } else {
            btn_aceptar_venta.dataset.inhabilitado = "true";
            btn_rechazar_venta.dataset.inhabilitado = "true";
        }
    }

    actualizar_botones_accion(false);

    async function metodos_registrados() {
        try {
            const respuesta = await fetch("/ventas/metodos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_metodos_pagos.innerHTML = "<option value='' selected>Todos los Métodos de Pago</option>";

            resultado.metodos.forEach(metodo => {
                const option = document.createElement("option");
                option.value = metodo.id_metodo;
                option.textContent = metodo.nombre;
                select_metodos_pagos.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    metodos_registrados();

    select_metodos_pagos.addEventListener("change", async () => {
        metodo_pago = select_metodos_pagos.value;

        await ventas_verificar()
    });

    async function ventas_verificar() {
        try {
            const formulario = new FormData();
            formulario.append("metodo_pago", metodo_pago);

            const respuesta = await fetch("/ventas/obtener_venta_verificar/", {
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

            if (!respuesta.ok || resultado.estado !== "exito") {

                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });

                ventas_recibidas = [];

                contenedor_compras.innerHTML = `
                    <div class="texto_sin_registros">
                        <i class="fa-solid fa-receipt"></i>
                        <p>No hay ventas registradas.</p>
                    </div>
                `;

                return;
            }

            ventas_recibidas = resultado.ventas || [];

            contenedor_compras.innerHTML = "";

            if (ventas_recibidas.length === 0) {
                contenedor_compras.innerHTML = `
                    <div class="texto_sin_registros">
                        <i class="fa-solid fa-receipt"></i>
                        <p>No hay ventas registradas.</p>
                    </div>
                `;

                return;
            }

            ventas_recibidas.forEach((venta, index) => {

                const contenedor_venta = document.createElement("div");

                contenedor_venta.classList.add("contenedor_venta");

                contenedor_venta.dataset.id = venta.id_venta;

                const estado_clase = String(venta.estado)
                    .toLowerCase()
                    .replace(/[^a-z0-9_-]/g, "");

                contenedor_venta.innerHTML = `
                    <div class="encabezado_contenedor_venta">
                        <h4>Venta ${index + 1}</h4>

                        <span class="estado_venta estado_${estado_clase}">
                            ${venta.estado_display}
                        </span>
                    </div>

                    <div class="datos_contenedor_venta">
                        <div class="dato_venta">
                            <span>Comprobante:</span>
                            <strong>${venta.comprobante}</strong>
                        </div>
                        <div class="dato_venta">
                            <span>Fecha de venta:</span>
                            <strong>${venta.fecha_venta}</strong>
                        </div>
                    </div>

                    <div class="acciones_contenedor_venta">
                        <button type="button" class="btn_detalle_venta" data-id="${venta.id_venta}">
                            <i class="fa-solid fa-eye"></i>
                            Ver detalle
                        </button>
                    </div>
                `;

                contenedor_compras.appendChild(contenedor_venta);
            });

        } catch (error) {
            console.error(error);

            ventas_recibidas = [];

            contenedor_compras.innerHTML = `
                <div class="texto_sin_registros">
                    <i class="fa-solid fa-circle-exclamation"></i>
                    <p>No se pudieron cargar las ventas.</p>
                </div>
            `;

        }
    }
    ventas_verificar();

    contenedor_compras.addEventListener("click", async (e) => {
        const btn_detalle = e.target.closest(".btn_detalle_venta");

        if (!btn_detalle) return;

        id_venta = btn_detalle.dataset.id;
        actualizar_botones_accion(false);

        await buscar_venta();
    });

    async function buscar_venta() {
        try {
            const formulario = new FormData();
            formulario.append("id_venta", id_venta);

            const respuesta = await fetch("/ventas/detalle_venta_verificar/", {
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
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            // INFORMACIÓN GENERAL DE LA VENTA
            input_id_venta.value = resultado.venta.id_venta;

            input_comprobante.value = resultado.venta.comprobante;
            input_fecha_venta.value = resultado.venta.fecha_venta;
            input_estado_venta.value = resultado.venta.estado_display;
            textarea_observacion_venta.value = resultado.venta.observacion;
            actualizar_botones_accion(
                resultado.venta.estado === "PENDIENTE_CONFIRMACION"
            );

            // INFORMACIÓN DEL CLIENTE
            input_razon_social.value = resultado.cliente.nombre;
            input_documento_identidad.value = resultado.cliente.documento;
            input_telefono.value = resultado.cliente.telefono;
            input_correo_electronico.value = resultado.cliente.correo;

            // PRODUCTOS DE LA VENTA
            contenedor_detalles_venta.innerHTML = "";

            resultado.productos.forEach((producto, index) => {
                const fila = document.createElement("tr");

                fila.dataset.id_detalle = producto.id_detalle;

                fila.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${producto.producto}</td>
                    <td>${producto.cantidad}</td>
                    <td>${producto.unidad_medida}</td>
                    <td>${mostrar_monto(producto.precio_unidad_ves, producto.precio_unidad)}</td>
                    <td>${mostrar_monto(producto.descuento_ves, producto.descuento)}</td>
                    <td>${mostrar_monto(producto.subtotal_ves, producto.subtotal)}</td>
                `;

                contenedor_detalles_venta.appendChild(fila);
            });

            // PAGOS DE LA VENTA
            input_metodo_pago.value = resultado.pago.metodo_pago;
            input_monto.value = mostrar_monto(
                resultado.pago.monto_ves,
                resultado.pago.monto
            );
            input_referencia.value = resultado.pago.referencia;
            input_banco_origen.value = resultado.pago.banco_origen;
            input_telefono_origen.value = resultado.pago.telefono_origen;
            input_fecha_pago_origen.value = resultado.pago.fecha_pago_bancario;
            enlace_capture_pago.hidden = !resultado.pago.capture_pago;
            enlace_capture_pago.href = resultado.pago.capture_pago || "#";
            capture_pago_no_disponible.hidden = Boolean(
                resultado.pago.capture_pago
            );

            // INFORMACIÓN DE LA CUENTA DESTINO
            input_banco_receptor.value = resultado.cuenta_destino.banco;
            input_documento_titular.value = resultado.cuenta_destino.documento;
            input_telefono_receptor.value = resultado.cuenta_destino.telefono;
            input_tipo_cuenta_receptor.value = resultado.cuenta_destino.tipo_cuenta_display;
            input_numero_cuenta.value = resultado.cuenta_destino.numero_cuenta;

            // RESUMEN FINANCIERO
            input_subtotal_venta.value = mostrar_monto(
                resultado.resumen.subtotal_ves,
                resultado.resumen.subtotal
            );
            input_descuento_venta.value = mostrar_monto(
                resultado.resumen.descuento_ves,
                resultado.resumen.descuento
            );
            input_impuesto_venta.value = mostrar_monto(
                resultado.resumen.impuesto_ves,
                resultado.resumen.impuesto
            );
            input_total_venta.value = mostrar_monto(
                resultado.resumen.total_ves,
                resultado.resumen.total
            );

        } catch (error) {
            console.error("Error al consultar la venta:", error);
        }
    }

    // CONFIRMAR VENTA

    btn_aceptar_venta.addEventListener("click", async () => {
        try {
            btn_aceptar_venta.disabled = true;
            btn_rechazar_venta.disabled = true;

            const formulario = new FormData();
            formulario.append("id_venta", input_id_venta.value);

            const respuesta = await fetch("/ventas/aceptar_venta/", {
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

            if (resultado.inhabilitar_botones || (resultado.estado_venta && resultado.estado_venta !== "PENDIENTE_CONFIRMACION")) {
                actualizar_botones_accion(false);
            }

            if (resultado.estado_venta && resultado.estado_venta !== "PENDIENTE_CONFIRMACION") {
                await buscar_venta();
            }

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            await ventas_verificar();
        } catch (error) {
            console.error("Error al confirmar la venta:", error);

            await Swal.fire({
                title: "Error al confirmar la venta",
                text: "Ocurrió un error inesperado al confirmar la venta. Intente nuevamente.",
                icon: "error"
            });

        } finally {
            if (btn_aceptar_venta.dataset.inhabilitado !== "true" &&
                btn_rechazar_venta.dataset.inhabilitado !== "true") {
                btn_aceptar_venta.disabled = false;
                btn_rechazar_venta.disabled = false;
            }
        }
    });

    // RECHAZAR VENTA

    btn_rechazar_venta.addEventListener("click", () => {
        dialogo_rechazado.showModal();
    });

    let temporizador_mensaje_rechazado = null;

    formulario_rechazar.addEventListener("submit", async (e) => {
        e.preventDefault();

        const boton_registrar = formulario_rechazar.querySelector(
            'button[type="submit"]'
        );

        try {
            boton_registrar.disabled = true;
            btn_aceptar_venta.disabled = true;
            btn_rechazar_venta.disabled = true;

            if (temporizador_mensaje_rechazado) {
                clearInterval(temporizador_mensaje_rechazado);
                temporizador_mensaje_rechazado = null;
            }

            mostrar_mensaje_temporal(
                "contenedor_mensajes_rechazado",
                "Procesando el rechazo de la venta...",
                "procesando",
                10
            );

            const formulario = new FormData(formulario_rechazar);
            formulario.append("id_venta", input_id_venta.value);

            const respuesta = await fetch("/ventas/rechazar_venta/", {
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

            if (
                resultado.inhabilitar_botones ||
                (
                    resultado.estado_venta &&
                    resultado.estado_venta !== "PENDIENTE_CONFIRMACION"
                )
            ) {
                actualizar_botones_accion(false);
            }

            if (
                resultado.estado_venta &&
                resultado.estado_venta !== "PENDIENTE_CONFIRMACION"
            ) {
                await buscar_venta();
            }

            if (!respuesta.ok || resultado.estado !== "exito") {
                mostrar_mensaje_temporal(
                    "contenedor_mensajes_rechazado",
                    `${resultado.title}: ${resultado.descripcion}`,
                    resultado.icon === "warning" ? "advertencia" : "fallo",
                    20
                );

                return;
            }

            mostrar_mensaje_temporal(
                "contenedor_mensajes_rechazado",
                `${resultado.title}: ${resultado.descripcion}`,
                resultado.icon === "warning" ? "advertencia" : "exito",
                10
            );

            dialogo_rechazado.close();
            await ventas_verificar();

        } catch (error) {
            console.error("Error al rechazar la venta:", error);

            mostrar_mensaje_temporal(
                "contenedor_mensajes_rechazado",
                "Ocurrió un error inesperado al rechazar la venta. Intente nuevamente.",
                "fallo",
                20
            );

        } finally {
            boton_registrar.disabled = false;

            if (
                btn_aceptar_venta.dataset.inhabilitado !== "true" &&
                btn_rechazar_venta.dataset.inhabilitado !== "true"
            ) {
                btn_aceptar_venta.disabled = false;
                btn_rechazar_venta.disabled = false;
            }
        }
    });

    btn_cerrar_rechazado.addEventListener("click", () => {
        dialogo_rechazado.close();
    });

    // MENSAJES TEMPORALES DIALOGO

    function mostrar_mensaje_temporal(id_contenedor, mensaje, tipo = "exito", segundos = 4) {
        return new Promise((resolve) => {
            const contenedor = document.getElementById(id_contenedor);

            if (!contenedor) {
                resolve();
                return;
            }

            let temporizador = null;

            if (id_contenedor === "contenedor_mensajes_rechazado") {
                if (temporizador_mensaje_rechazado) {
                    clearInterval(temporizador_mensaje_rechazado);
                    temporizador_mensaje_rechazado = null;
                }
            }

            contenedor.className = `contenedor_mensajes ${tipo}`;
            contenedor.replaceChildren();

            const reloj = document.createElement("i");
            reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
            reloj.setAttribute("aria-hidden", "true");

            const texto = document.createElement("span");
            texto.textContent = mensaje;

            const contador = document.createElement("span");
            contador.className = "contador_notificacion";
            contador.setAttribute("aria-live", "off");

            contenedor.append(reloj, texto, contador);

            contenedor.hidden = false;

            let restante = segundos;

            contador.textContent = ` ${restante} s`;

            temporizador = setInterval(() => {
                restante--;

                if (restante <= 0) {
                    clearInterval(temporizador);

                    if (id_contenedor === "contenedor_mensajes_rechazado") {
                        temporizador_mensaje_rechazado = null;
                    }

                    ocultar_mensaje_dialogo(id_contenedor);
                    resolve();

                    return;
                }

                contador.textContent = ` ${restante} s`;
            }, 1000);

            if (id_contenedor === "contenedor_mensajes_rechazado") {
                temporizador_mensaje_rechazado = temporizador;
            }
        });
    }

    function ocultar_mensaje_dialogo(id_contenedor) {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.hidden = true;
        contenedor.replaceChildren();
    }

});
