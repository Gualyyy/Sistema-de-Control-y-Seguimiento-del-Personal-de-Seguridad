document.addEventListener("DOMContentLoaded", () => {

    const control_imagen_producto = document.getElementById("imagen_producto");

    const select_producto_existencia = document.getElementById("producto_existencia");

    const input_nombre_producto = document.getElementById("nombre_producto");
    const input_codigo_producto = document.getElementById("codigo_producto");
    const input_categoria_producto = document.getElementById("categoria_producto");
    const input_unidad_producto = document.getElementById("unidad_producto");
    const input_precio_base = document.getElementById("precio_base");
    const input_costo_base = document.getElementById("costo_base");

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const textarea_motivo_existencia = document.getElementById("motivo_existencia");
    const id_producto_existencia = document.getElementById("id_producto_existencia");
    const input_cantidad_actual = document.getElementById("cantidad_actual");
    const input_nueva_cantidad = document.getElementById("nueva_cantidad");
    const contenedor_msg_cantidad = document.getElementById("contenedor_msg_cantidad");

    const contador_motivo = document.getElementById("contador_motivo");

    const btn_actualizar = document.getElementById("btn_actualizar");

    let codigo = "";

    async function productos_registrados() {
        try {
            const respuesta = await fetch("/ventas/productos_registrados_venta/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_producto_existencia.innerHTML = "<option value='' selected>Selecciona un Producto</option>";

            resultado.productos.forEach(producto => {
                const option_producto = document.createElement("option");
                option_producto.value = producto.codigo;
                option_producto.textContent = producto.nombre;
                select_producto_existencia.append(option_producto);
            });
        } catch (error) {
            console.log(error);
        }
    }
    productos_registrados();

    select_producto_existencia.addEventListener("change", async () => {
        codigo = select_producto_existencia.value;

        if (!codigo) {
            limpiar_datos_producto();
            return;
        }

        await datos_producto_registrado();
    });

    function limpiar_datos_producto() {
        input_nombre_producto.textContent = "Nombre del producto";
        input_codigo_producto.value = "";
        input_categoria_producto.value = "";
        input_unidad_producto.value = "";
        input_precio_base.value = "";
        input_costo_base.value = "";
        input_cantidad_actual.value = "";
        input_nueva_cantidad.value = "";
        control_imagen_producto.src = control_imagen_producto.dataset.default;
        contador_motivo.value = "0";
    }

    const controles_actualizacion = [
        input_nueva_cantidad,
        textarea_motivo_existencia,
        btn_actualizar
    ]

    function bloquearFormularioActualizar(bloquear = true) {
        controles_actualizacion.forEach(control => {
            if (control) {
                control.disabled = bloquear;
            }
        });
    }
    bloquearFormularioActualizar(true);

    async function datos_producto_registrado() {
        try {
            const formulario = new FormData();
            formulario.append("codigo_producto", codigo);

            const respuesta = await fetch("/ventas/datos_producto_existencia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario,
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (!resultado.producto) {
                limpiar_datos_producto();
                return;
            }

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            bloquearFormularioActualizar(false);

            control_imagen_producto.src = resultado.producto.imagen;

            id_producto_existencia.value = resultado.producto.id_producto;

            input_nombre_producto.textContent = resultado.producto.nombre;
            input_codigo_producto.value = resultado.producto.codigo;
            input_categoria_producto.value = resultado.producto.categoria;
            input_precio_base.value = resultado.producto.precio_base + "$";
            input_costo_base.value = resultado.producto.costo_base + "$";
            input_cantidad_actual.value = `La cantidad actual del producot es ${resultado.producto.cantidad_actual} unidad(es).`
            input_unidad_producto.value = resultado.producto.unidad + " | " + resultado.producto.abreviatura;
        } catch (error) {
            console.error(error);
        }
    }

    input_nueva_cantidad.addEventListener("input", () => {
        input_nueva_cantidad.value = input_nueva_cantidad.value.replace(/\D/g, "");

        const cantidadTexto = input_nueva_cantidad.value;

        const mostrarError = (mensaje) => {
            contenedor_msg_cantidad.textContent = mensaje;
            contenedor_msg_cantidad.className = "mensaje-feedback error";
            input_nueva_cantidad.classList.add("is-invalid");
            btn_actualizar.disabled = true;
        };

        if (cantidadTexto === "") {
            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";
            input_nueva_cantidad.classList.remove("is-invalid");
            btn_actualizar.disabled = true;
            return;
        }

        if (cantidadTexto.startsWith("0")) {
            mostrarError(
                "La cantidad debe ser un entero mayor que cero y no puede comenzar con 0."
            );
            return;
        }

        const cantidadIngresada = Number(cantidadTexto);

        if (!Number.isSafeInteger(cantidadIngresada) || cantidadIngresada <= 0) {
            mostrarError("Ingrese una cantidad entera válida mayor que cero.");
            return;
        }

        contenedor_msg_cantidad.textContent = "";
        contenedor_msg_cantidad.className = "mensaje-feedback";
        input_nueva_cantidad.classList.remove("is-invalid");
        btn_actualizar.disabled = false;
    });

    textarea_motivo_existencia.addEventListener("input", () => {
        textarea_motivo_existencia.value = textarea_motivo_existencia.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_motivo.textContent = textarea_motivo_existencia.value.length;
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/ventas/actualizar_existencia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario,
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            formulario_actualizar.reset();
            limpiar_datos_producto();
        } catch (error) {
            console.error(error);
        }
    });

});