
document.addEventListener("DOMContentLoaded", () => {

    const formulario_registro = document.getElementById("formulario_registro");

    const input_id_producto = document.getElementById("id_producto");

    const select_productos_registrados = document.getElementById("productos_registrados");

    const input_precio_producto = document.getElementById("precio_producto");

    const input_cantidad_minima = document.getElementById("cantidad_minima");
    const contenedor_msg_minimo = document.getElementById("contenedor_msg_minimo");

    const input_cantidad_maxima = document.getElementById("cantidad_maxima");
    const contenedor_msg_maximo = document.getElementById("contenedor_msg_maximo");

    const input_porcentaje_descuento = document.getElementById("porcentaje_descuento");
    const contenedor_msg_descuento = document.getElementById("contenedor_msg_descuento");

    const contenedor_precio_volumen = document.getElementById("contenedor_precio_volumen");

    const btn_registrar = document.getElementById("btn_registrar");

    let ultimo_registro = null;

    const errores_limite = {};

    const controles_actualizacion = [
        input_cantidad_minima,
        input_cantidad_maxima,
        input_porcentaje_descuento,
        btn_registrar
    ];

    function bloquearFormularioActualizar(bloquear = true) {
        controles_actualizacion.forEach(control => {
            if (control) {
                control.disabled = bloquear;
            }
        });
    }

    function mostrar_mensaje(input, contenedor, mensaje) {
        contenedor.textContent = mensaje;

        contenedor.className = mensaje
            ? "mensaje-feedback error"
            : "mensaje-feedback";

        input.classList.toggle("is-invalid", Boolean(mensaje));
    }

    function limpiar_validaciones() {
        Object.keys(errores_limite).forEach(campo => {
            errores_limite[campo] = "";
        });

        mostrar_mensaje(
            input_cantidad_minima,
            contenedor_msg_minimo,
            ""
        );

        mostrar_mensaje(
            input_cantidad_maxima,
            contenedor_msg_maximo,
            ""
        );

        mostrar_mensaje(
            input_porcentaje_descuento,
            contenedor_msg_descuento,
            ""
        );
    }

    bloquearFormularioActualizar(true);

    async function productos_registrados() {
        try {
            const respuesta = await fetch("/ventas/productos_registrados_venta/");
            const resultado = await respuesta.json();

            select_productos_registrados.innerHTML = `
                <option value="" selected>Selecciona un Producto</option>
            `;

            resultado.productos.forEach(producto => {
                const option_producto = document.createElement("option");

                option_producto.value = producto.id_producto;
                option_producto.textContent = producto.nombre;
                option_producto.dataset.precioBase = producto.precio_base;

                select_productos_registrados.appendChild(option_producto);
            });

        } catch (error) {
            console.error(error);
        }
    }

    productos_registrados();

    select_productos_registrados.addEventListener("change", async () => {

        const opcion_seleccionada = select_productos_registrados.selectedOptions[0];

        const id_producto = select_productos_registrados.value;
        const precio_base = opcion_seleccionada?.dataset.precioBase;

        input_id_producto.value = id_producto;

        ultimo_registro = null;

        formulario_registro.reset();
        select_productos_registrados.value = id_producto;
        input_id_producto.value = id_producto;

        limpiar_validaciones();

        contenedor_precio_volumen.innerHTML = "";

        if (!id_producto || precio_base === undefined || precio_base === "") {
            input_precio_producto.value = "";
            bloquearFormularioActualizar(true);
            return;
        }

        const precio = Number(precio_base);

        if (!Number.isFinite(precio) || precio <= 0) {
            input_precio_producto.value = "";
            bloquearFormularioActualizar(true);
            return;
        }

        input_precio_producto.value = `${precio.toFixed(2)} $`;

        await precios_producto_registrado();
        await consultar_ultimo_registro();

    });

    async function precios_producto_registrado() {

        try {
            const formulario = new FormData();
            formulario.append("id_producto", input_id_producto.value);

            const respuesta = await fetch("/ventas/precios_volumna_producto/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            contenedor_precio_volumen.innerHTML = "";

            if (resultado.estado !== "ok" || !Array.isArray(resultado.precios) || !resultado.precios.length) {

                contenedor_precio_volumen.innerHTML = `
                    <tr>
                        <td colspan="5" class="texto_sin_registros">
                            No hay precios de volumen registrados.
                        </td>
                    </tr>
                `;

                return;
            }

            resultado.precios.forEach((precio, index) => {

                const fila = document.createElement("tr");

                fila.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${precio.producto}</td>
                    <td>${precio.cantidad_minima}</td>
                    <td>${precio.cantidad_maxima}</td>
                    <td>${precio.porcentaje_descuento}%</td>
                `;

                contenedor_precio_volumen.appendChild(fila);

            });

        } catch (error) {
            console.error(error);
        }
    }

    async function consultar_ultimo_registro() {

        bloquearFormularioActualizar(true);

        try {

            const formulario = new FormData();

            formulario.append("id_producto", input_id_producto.value);

            const respuesta = await fetch("/ventas/ultimo_registro_volumen_producto/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            if (resultado.estado === "ok") {

                ultimo_registro = resultado.precios;

            } else if (resultado.estado === "vacio") {

                ultimo_registro = null;

            } else {

                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });

                ultimo_registro = null;
                return;
            }

            bloquearFormularioActualizar(false);

            validar_rango_cantidades();
            validar_porcentaje_descuento();

        } catch (error) {

            console.error(error);

            ultimo_registro = null;

            bloquearFormularioActualizar(true);

        }
    }

    function validar_rango_cantidades() {

        const texto_minimo = input_cantidad_minima.value.trim();
        const texto_maximo = input_cantidad_maxima.value.trim();

        const minimo = Number(texto_minimo);
        const maximo = Number(texto_maximo);

        let error_minimo = "";
        let error_maximo = "";

        const minimo_valido =
            texto_minimo !== "" &&
            Number.isSafeInteger(minimo) &&
            minimo >= 1;

        const maximo_valido =
            texto_maximo !== "" &&
            Number.isSafeInteger(maximo) &&
            maximo >= 1;

        if (!minimo_valido) {

            error_minimo = texto_minimo === ""
                ? "Ingrese la cantidad mínima."
                : "La cantidad mínima debe ser un entero mayor que cero.";

        } else if (
            ultimo_registro &&
            minimo <= Number(ultimo_registro.cantidad_maxima)
        ) {

            error_minimo = `La cantidad mínima debe ser mayor que ${ultimo_registro.cantidad_maxima}.`;

        }

        if (!maximo_valido) {

            error_maximo = texto_maximo === ""
                ? "Ingrese la cantidad máxima."
                : "La cantidad máxima debe ser un entero mayor que cero.";

        }

        if (minimo_valido && maximo_valido) {

            if (minimo === maximo) {

                error_minimo = "La cantidad mínima no puede ser igual a la máxima.";
                error_maximo = "La cantidad máxima no puede ser igual a la mínima.";

            } else if (minimo > maximo) {

                error_minimo = "La cantidad mínima debe ser menor que la máxima.";
                error_maximo = "La cantidad máxima debe ser mayor que la mínima.";

            }

        }

        errores_limite.cantidad_minima = error_minimo;
        errores_limite.cantidad_maxima = error_maximo;

        mostrar_mensaje(
            input_cantidad_minima,
            contenedor_msg_minimo,
            error_minimo
        );

        mostrar_mensaje(
            input_cantidad_maxima,
            contenedor_msg_maximo,
            error_maximo
        );

        actualizar_estado_boton();
    }


    function validar_porcentaje_descuento() {

        const texto = input_porcentaje_descuento.value.trim();

        const porcentaje = Number(texto);

        let error = "";

        if (texto === "") {

            error = "Ingrese el porcentaje de descuento.";

        } else if (!Number.isFinite(porcentaje) || porcentaje <= 0 || porcentaje > 100) {

            error = "El descuento debe ser mayor que 0 y no superar el 100%.";

        } else if (ultimo_registro) {

            const ultimo_porcentaje = Number(ultimo_registro.porcentaje_descuento);

            if (!Number.isFinite(ultimo_porcentaje)) {

                error = "No fue posible validar el último descuento registrado.";

            } else if (porcentaje <= ultimo_porcentaje) {

                error = `El descuento debe ser mayor a ${ultimo_porcentaje.toFixed(2)}%.`;

            }

        }

        errores_limite.porcentaje_descuento = error;

        mostrar_mensaje(
            input_porcentaje_descuento,
            contenedor_msg_descuento,
            error
        );

        actualizar_estado_boton();
    }

    input_cantidad_minima.addEventListener("input", function () {

        this.value = this.value.replace(/[^0-9]/g, "");

        validar_rango_cantidades();

    });

    input_cantidad_maxima.addEventListener("input", function () {

        this.value = this.value.replace(/[^0-9]/g, "");

        validar_rango_cantidades();

    });

    input_porcentaje_descuento.addEventListener("input", function () {

        validar_porcentaje_descuento();

    });

    function actualizar_estado_boton() {

        const campos = [
            input_cantidad_minima,
            input_cantidad_maxima,
            input_porcentaje_descuento
        ];

        const campos_invalidos = campos.some(campo =>
            campo.value.trim() === "" ||
            campo.classList.contains("is-invalid")
        );

        const minimo = Number(input_cantidad_minima.value);
        const maximo = Number(input_cantidad_maxima.value);

        const rango_invalido =
            !Number.isSafeInteger(minimo) ||
            !Number.isSafeInteger(maximo) ||
            minimo < 1 ||
            maximo <= minimo ||
            (
                ultimo_registro &&
                minimo <= Number(ultimo_registro.cantidad_maxima)
            );

        btn_registrar.disabled =
            campos_invalidos ||
            rango_invalido ||
            !input_id_producto.value ||
            !select_productos_registrados.value;
    }

    formulario_registro.addEventListener("submit", async (e) => {

        e.preventDefault();

        validar_rango_cantidades();
        validar_porcentaje_descuento();

        if (btn_registrar.disabled) {
            return;
        }

        try {

            const formulario = new FormData(formulario_registro);

            const respuesta = await fetch("/ventas/registrar_precio_volumen/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (resultado.estado === "exito") {

                contenedor_precio_volumen.innerHTML = "";

                ultimo_registro = null;

                formulario_registro.reset();

                input_id_producto.value = "";

                input_precio_producto.value = "";

                select_productos_registrados.value = "";

                limpiar_validaciones();

                bloquearFormularioActualizar(true);

            }

        } catch (error) {

            console.error(error);

        }

    });

});
