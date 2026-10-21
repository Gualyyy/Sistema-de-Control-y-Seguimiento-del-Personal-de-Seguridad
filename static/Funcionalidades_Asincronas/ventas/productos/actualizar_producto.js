document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const input_codigo_producto = document.getElementById("codigo_producto");

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const input_id_codigo = document.getElementById("id_codigo");
    const input_nombre_producto = document.getElementById("nombre_producto");
    const input_precio_base = document.getElementById("precio_base");
    const input_costo_base = document.getElementById("costo_base");
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

    [input_precio_base, input_costo_base].forEach(input => {
        input.addEventListener("input", function () {
            let valor = this.value.replace(/[^0-9.]/g, "");
            const partes = valor.split(".");

            let enteros = partes[0].slice(0, 3);
            let decimales = partes.slice(1).join("").slice(0, 2);

            if (partes.length > 1 && enteros !== "") {
                valor = `${enteros}.${decimales}`;
            } else {
                valor = enteros;
            }

            this.value = valor;
        });
    });

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
        } catch (error) {
            console.error(error);
        }
    });
});