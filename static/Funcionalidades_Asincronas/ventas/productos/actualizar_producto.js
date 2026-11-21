document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const input_codigo_producto = document.getElementById("codigo_producto");

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const input_id_codigo = document.getElementById("id_codigo");
    const input_nombre_producto = document.getElementById("nombre_producto");

    const input_precio_base = document.getElementById("precio_base");
    const contenedor_mensaje_precio_base = document.getElementById("contenedor_mensaje_precio_base");

    const input_costo_base = document.getElementById("costo_base");
    const contenedor_mensaje_costo_base = document.getElementById("contenedor_mensaje_costo_base");

    const input_imagen_producto = document.getElementById("imagen_producto");
    const select_categoria_producto = document.getElementById("categoria_producto");
    const select_unidad_producto = document.getElementById("unidad_producto");
    const btn_actualizar = document.getElementById("btn_actualizar");

    const controles_actualizacion = [
        input_id_codigo,
        input_nombre_producto,
        input_precio_base,
        input_costo_base,
        input_imagen_producto,
        select_categoria_producto,
        select_unidad_producto,
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

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_nombre_producto.addEventListener("input", (e) => {
        soloTexto(e.target);
    });

    function limpiar_mensaje(input, contenedor) {
        input.setCustomValidity("");
        input.classList.remove("is-valid", "is-invalid");
        contenedor.classList.remove("exito", "error");
        contenedor.textContent = "";
    }

    function mostrar_error(input, contenedor, mensaje) {
        input.setCustomValidity(mensaje);
        input.classList.add("is-invalid");
        contenedor.textContent = mensaje;
        contenedor.classList.add("error");
    }

    function mostrar_exito(input, contenedor, mensaje) {
        input.classList.add("is-valid");
        contenedor.textContent = mensaje;
        contenedor.classList.add("exito");
    }

    function limitar_decimal(input) {
        let valor = input.value.replace(/[^0-9.]/g, "");
        const partes = valor.split(".");

        const enteros = partes[0].slice(0, 3);
        const decimales = partes.slice(1).join("").slice(0, 2);

        if (partes.length > 1 && enteros !== "") {
            valor = `${enteros}.${decimales}`;
        } else {
            valor = enteros;
        }

        input.value = valor;
    }

    function validar_precio_base() {
        limpiar_mensaje(input_precio_base, contenedor_mensaje_precio_base);

        const precio = input_precio_base.value.trim();

        if (precio === "") {
            btn_actualizar.disabled = true;
            return false;
        }

        const precio_base = Number(precio);

        if (!Number.isFinite(precio_base)) {
            mostrar_error(
                input_precio_base,
                contenedor_mensaje_precio_base,
                "Ingrese un precio base válido."
            );
            btn_actualizar.disabled = true;
            return false;
        }

        if (precio_base <= 0) {
            mostrar_error(
                input_precio_base,
                contenedor_mensaje_precio_base,
                "El precio base debe ser mayor que cero."
            );
            btn_actualizar.disabled = true;
            return false;
        }

        mostrar_exito(
            input_precio_base,
            contenedor_mensaje_precio_base,
            "El precio base es válido."
        );

        return true;
    }

    function validar_costo_base() {
        limpiar_mensaje(input_costo_base, contenedor_mensaje_costo_base);

        const costo = input_costo_base.value.trim();

        if (costo === "") {
            btn_actualizar.disabled = true;
            return false;
        }

        const costo_base = Number(costo);

        if (!Number.isFinite(costo_base)) {
            mostrar_error(
                input_costo_base,
                contenedor_mensaje_costo_base,
                "Ingrese un costo base válido."
            );
            btn_actualizar.disabled = true;
            return false;
        }

        if (costo_base <= 0) {
            mostrar_error(
                input_costo_base,
                contenedor_mensaje_costo_base,
                "El costo base debe ser mayor que cero."
            );
            btn_actualizar.disabled = true;
            return false;
        }

        const precio_base = Number(input_precio_base.value.trim());

        if (Number.isFinite(precio_base) && costo_base >= precio_base) {
            mostrar_error(
                input_costo_base,
                contenedor_mensaje_costo_base,
                costo_base === precio_base
                    ? "El costo base no puede ser igual al precio base."
                    : "El costo base no puede ser mayor al precio base."
            );
            btn_actualizar.disabled = true;
            return false;
        }

        mostrar_exito(
            input_costo_base,
            contenedor_mensaje_costo_base,
            "El costo base es válido."
        );

        return true;
    }

    function validar_campos() {
        const precio_incompleto = tiene_decimal_incompleto(input_precio_base);
        const costo_incompleto = tiene_decimal_incompleto(input_costo_base);

        const precio_valido = validar_precio_base() && !precio_incompleto;
        const costo_valido = validar_costo_base() && !costo_incompleto;

        btn_actualizar.disabled = !(precio_valido && costo_valido);

        return precio_valido && costo_valido;
    }

    function tiene_decimal_incompleto(input) {
        return input.value.trim().endsWith(".");
    }

    input_precio_base.addEventListener("input", function () {
        limitar_decimal(this);
        validar_campos();
    });

    input_costo_base.addEventListener("input", function () {
        limitar_decimal(this);
        validar_campos();
    });

    validar_campos();

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/ventas/buscar_datos_producto/", {
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

            if (resultado.estado != "exito") return;

            bloquearFormularioActualizar(false);

            input_id_codigo.value = resultado.producto.codigo;
            input_nombre_producto.value = resultado.producto.nombre;
            input_codigo_producto.value = resultado.producto.codigo;
            input_precio_base.value = resultado.producto.precio_base;
            input_costo_base.value = resultado.producto.costo_base;
            validar_campos();

            const opcion_categoria = document.createElement("option");
            opcion_categoria.value = resultado.producto.id_categoria;
            opcion_categoria.textContent = resultado.producto.categoria;
            opcion_categoria.hidden = true;
            opcion_categoria.selected = true;
            select_categoria_producto.append(opcion_categoria);

            const opcion_unidad = document.createElement("option");
            opcion_unidad.value = resultado.producto.id_unidad;
            opcion_unidad.textContent = resultado.producto.unidad + " | " + resultado.producto.abreviatura;
            opcion_unidad.hidden = true;
            opcion_unidad.selected = true;
            select_unidad_producto.append(opcion_unidad);

            formulario_busqueda.reset();
        } catch (error) {
            console.error(error);
        }
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/ventas/actualizar_producto/", {
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

            bloquearFormularioActualizar(true);
            formulario_actualizar.reset();
            contenedor_mensaje_costo_base.innerHTML = "";
            contenedor_mensaje_precio_base.innerHTML = "";
        } catch (error) {
            console.error(error);
        }
    });
});