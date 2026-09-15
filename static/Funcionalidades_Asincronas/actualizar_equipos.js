document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const input_id_equipo = document.getElementById("id_equipo");
    const input_nombre_equipo = document.getElementById("nombre_equipo");
    const textarea_observacion_equipo = document.getElementById("observacion_equipo");
    const input_cantidad_total = document.getElementById("cantidad_total");
    const select_categoria_equipo = document.getElementById("categoria_equipo");

    const contador_observacion = document.getElementById("contador_observacion");

    const contenedor_msg_cantidad = document.getElementById("contenedor_msg_cantidad");

    const btn_actualizar = document.getElementById("btn_actualizar");

    textarea_observacion_equipo.addEventListener("input", () => {
        textarea_observacion_equipo.value = textarea_observacion_equipo.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-*]/g, "");

        actualizarContador(textarea_observacion_equipo, contador_observacion);
    });

    function actualizarContador(textarea, contador) {
        contador.textContent = textarea.value.length;
    }

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_nombre_equipo.addEventListener("input", () => {
        soloTexto(input_nombre_equipo);
    });

    const controles_actualizacion = [
        input_id_equipo,
        input_nombre_equipo,
        textarea_observacion_equipo,
        input_cantidad_total,
        select_categoria_equipo,
        btn_actualizar,
    ];

    function bloquearFormularioActualizar(bloquear = true) {
        controles_actualizacion.forEach(control => {
            if (control) {
                control.disabled = bloquear;
            }
        });
    }
    bloquearFormularioActualizar(true);

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/buscar_equipos/", {
                method: "POST",
                body: formulario
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            await Swal.fire({
                title: "Datos encontrados",
                text: "Los datos del equipo fueron encontrados correctamente.",
                icon: "success"
            });

            formulario_busqueda.reset();

            bloquearFormularioActualizar(false);

            input_id_equipo.value = resultado.equipo.id_equipo;
            input_nombre_equipo.value = resultado.equipo.nombre;
            textarea_observacion_equipo.value = resultado.equipo.observacion;

            actualizarContador(textarea_observacion_equipo, contador_observacion);

            input_cantidad_total.value = resultado.equipo.cantidad_total;
            input_cantidad_total.dataset.actual = resultado.equipo.cantidad_total;
            input_cantidad_total.dataset.asignada = resultado.equipo.cantidad_asignada;

            const option_categoria = document.createElement("option");
            option_categoria.value = resultado.equipo.id_categoria;
            option_categoria.textContent = resultado.equipo.categoria;
            option_categoria.selected = true;
            option_categoria.hidden = true;
            select_categoria_equipo.append(option_categoria);
        } catch (error) {
            console.error(error);
        }
    });

    input_cantidad_total.addEventListener("input", () => {
        // Solo números
        input_cantidad_total.value = input_cantidad_total.value.replace(/[^0-9]/g, "");

        // Máximo 3 dígitos
        if (input_cantidad_total.value.length > 3) {
            input_cantidad_total.value = input_cantidad_total.value.slice(0, 3);
        }

        // Limpiar estados anteriores
        contenedor_msg_cantidad.classList.remove("error", "exito");
        input_cantidad_total.classList.remove("is-invalid", "is-valid");

        // No permitir ceros al inicio
        if (input_cantidad_total.value.length > 0 && input_cantidad_total.value.startsWith("0")) {
            contenedor_msg_cantidad.textContent = "La cantidad debe ser un número entero mayor a 0 y no puede comenzar con 0.";

            contenedor_msg_cantidad.classList.add("error");
            input_cantidad_total.classList.add("is-invalid");

            btn_actualizar.disabled = true;
            return;
        }

        const cantidadNueva = parseInt(input_cantidad_total.value) || 0;

        // Campo vacío
        if (cantidadNueva === 0) {
            contenedor_msg_cantidad.textContent = "";
            btn_actualizar.disabled = true;
            return;
        }

        const cantidadAsignada = parseInt(input_cantidad_total.dataset.asignada) || 0;

        if (cantidadNueva < cantidadAsignada) {
            contenedor_msg_cantidad.textContent =
                `La cantidad no puede ser menor a ${cantidadAsignada} ${cantidadAsignada === 1 ? "unidad" : "unidades"
                } actualmente asignadas.`;

            contenedor_msg_cantidad.classList.add("error");
            input_cantidad_total.classList.add("is-invalid");

            btn_actualizar.disabled = true;
            return;
        }

        // Cantidad válida
        contenedor_msg_cantidad.textContent = "";
        input_cantidad_total.classList.add("is-valid");
        btn_actualizar.disabled = false;
    });

    async function categoria_equipo_registrados() {
        try {
            const respuesta = await fetch("/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipo.innerHTML = "";
            resultado.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categoria_equipo.append(option_categoria);
            });

        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipo_registrados();

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/actualizacion_equipos/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            formulario_actualizar.reset();

            contador_observacion.innerHTML = "0";

            bloquearFormularioActualizar(true);
        } catch (error) {
            console.error(error);
        }
    });
});