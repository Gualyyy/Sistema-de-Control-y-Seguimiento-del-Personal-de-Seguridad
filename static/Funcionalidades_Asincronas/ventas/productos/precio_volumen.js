document.addEventListener("DOMContentLoaded", () => {

    const formulario_registro = document.getElementById("formulario_registro");

    const input_id_producto = document.getElementById("id_producto");

    const select_productos_registrados = document.getElementById("productos_registrados");

    const input_cantidad_minima = document.getElementById("cantidad_minima");
    const contenedor_msg_minimo = document.getElementById("contenedor_msg_minimo");

    const input_cantidad_maxima = document.getElementById("cantidad_maxima");
    const contenedor_msg_maximo = document.getElementById("contenedor_msg_maximo");

    const input_precio_unitario = document.getElementById("precio_unitario");
    const contenedor_msg_precio = document.getElementById("contenedor_msg_precio");

    const contenedor_precio_volumen = document.getElementById("contenedor_precio_volumen");

    const btn_registrar = document.getElementById("btn_registrar");

    let id_producto = "";

    const controles_actualizacion = [
        input_cantidad_minima,
        contenedor_msg_minimo,
        input_cantidad_maxima,
        contenedor_msg_maximo,
        input_precio_unitario,
        contenedor_msg_precio,
        btn_registrar
    ]

    function bloquearFormularioActualizar(bloquear = true) {
        controles_actualizacion.forEach(control => {
            if (control) {
                control.disabled = bloquear;
            }
        });
    }
    bloquearFormularioActualizar(true);

    async function productos_registrados() {
        try {
            const respuesta = await fetch("/ventas/productos_registrados_venta/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_productos_registrados.innerHTML = "<option value='' selected>Selecciona un Producto</option>";

            resultado.productos.forEach(producto => {
                const option_producto = document.createElement("option");
                option_producto.value = producto.id_producto;
                option_producto.textContent = producto.nombre;
                select_productos_registrados.append(option_producto);
            });
        } catch (error) {
            console.log(error);
        }
    }
    productos_registrados();

    select_productos_registrados.addEventListener("change", async () => {
        id_producto = select_productos_registrados.value;

        input_id_producto.value = id_producto;

        bloquearFormularioActualizar(false);

        await precios_producto_registrado();
    });

    async function precios_producto_registrado() {
        try {
            const formulario = new FormData();
            formulario.append("id_producto", id_producto);

            const respuesta = await fetch("/ventas/precios_volumna_producto/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            contenedor_precio_volumen.innerHTML = "";

            if (resultado.estado !== "ok" || !resultado.precios.length) {
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
                <td>${precio.precio_unitario}</td>
            `;

                contenedor_precio_volumen.appendChild(fila);
            });
        } catch (error) {
            console.error(error);
        }
    }

    async function validar_limite_volumen(
        input,
        contenedor,
        campo,
        mensaje,
        condicion = "mayor"
    ) {
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

            if (resultado.estado === "vacio") {
                contenedor.textContent = "";
                contenedor.className = "mensaje-feedback";
                input.classList.remove("is-invalid");
                actualizar_estado_boton();
                return;
            }

            if (
                resultado.estado !== "ok" ||
                !resultado.precios ||
                Array.isArray(resultado.precios)
            ) {
                throw new Error("No se pudo obtener el último registro.");
            }

            const texto = input.value.trim();
            const dato_ultimo = resultado.precios[campo];

            if (texto === "" || dato_ultimo == null || dato_ultimo === "") {
                contenedor.textContent = texto === ""
                    ? "Este campo es obligatorio."
                    : "No se pudo obtener el límite almacenado.";

                contenedor.className = "mensaje-feedback error";
                input.classList.add("is-invalid");
                actualizar_estado_boton();
                return;
            }

            const valor = Number(texto);
            const ultimo = Number(dato_ultimo);

            if (!Number.isFinite(valor) || !Number.isFinite(ultimo)) {
                contenedor.textContent = "Ingrese un valor numérico válido.";
                contenedor.className = "mensaje-feedback error";
                input.classList.add("is-invalid");
                actualizar_estado_boton();
                return;
            }

            const invalido = condicion === "menor"
                ? valor >= ultimo
                : valor <= ultimo;

            if (invalido) {
                contenedor.textContent = `${mensaje} ${ultimo}.`;
                contenedor.className = "mensaje-feedback error";
                input.classList.add("is-invalid");
                actualizar_estado_boton();
                return;
            }

            contenedor.textContent = "";
            contenedor.className = "mensaje-feedback";
            input.classList.remove("is-invalid");

            actualizar_estado_boton();

        } catch (error) {
            console.error("Error al validar el límite:", error);

            contenedor.textContent = "No fue posible validar el valor.";
            contenedor.className = "mensaje-feedback error";
            input.classList.add("is-invalid");

            actualizar_estado_boton();
        }
    }

    input_cantidad_minima.addEventListener("input", () => {
        validar_limite_volumen(
            input_cantidad_minima,
            contenedor_msg_minimo,
            "cantidad_minima",
            "La cantidad mínima debe ser mayor a"
        );
    });

    input_cantidad_maxima.addEventListener("input", () => {
        validar_limite_volumen(
            input_cantidad_maxima,
            contenedor_msg_maximo,
            "cantidad_maxima",
            "La cantidad máxima debe ser mayor a"
        );
    });

    input_precio_unitario.addEventListener("input", () => {
        validar_limite_volumen(
            input_precio_unitario,
            contenedor_msg_precio,
            "precio_unitario",
            "El precio unitario debe ser menor a",
            "menor"
        );
    });

    function actualizar_estado_boton() {
        const campos = [
            input_cantidad_minima,
            input_cantidad_maxima,
            input_precio_unitario
        ];

        btn_registrar.disabled = campos.some(campo =>
            campo.value.trim() === "" ||
            campo.classList.contains("is-invalid")
        );
    }

    function validarNumeroEntero(input) {
        input.addEventListener("input", function () {
            this.value = this.value.replace(/[^0-9]/g, "");
        });
    }

    validarNumeroEntero(input_cantidad_minima);
    validarNumeroEntero(input_cantidad_maxima);

    formulario_registro.addEventListener("submit", async (e) => {
        e.preventDefault();
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
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            contenedor_precio_volumen.innerHTML = "";
            bloquearFormularioActualizar(true);
            formulario_registro.reset();
        } catch (error) {
            console.error(error);
        }
    })

});