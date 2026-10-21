document.addEventListener("DOMContentLoaded", () => {

    const formulario_correccion = document.getElementById("formulario_correccion");

    const select_supervisores_encargados = document.getElementById("supervisores_encargados");
    const select_categoria_equipos = document.getElementById("categoria_equipos");
    const select_equipos_entregados = document.getElementById("equipos_entregados");
    const select_tipo_correccion = document.getElementById("tipo_correccion");

    const input_cantidad_entregada = document.getElementById("cantidad_entregada");
    const input_cantidad_actualizar = document.getElementById("cantidad_actualizar");

    const contenedor_msg_cantidad = document.getElementById("contenedor_msg_cantidad");

    const textarea_observacion_entrega = document.getElementById("observacion_entrega");
    const textarea_motivo_correccion = document.getElementById("motivo_correccion");

    const contador_observacion = document.getElementById("contador_observacion");
    const contador_motivo = document.getElementById("contador_motivo");

    const btn_actualizar = document.getElementById("btn_actualizar");

    let supervisor = "", categoria = "";

    async function supervisores_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/supervisores_entregado_equipos/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_supervisores_encargados.innerHTML = "<option value=''>Selecciona un Supervisor</option>"

            select_categoria_equipos.innerHTML = "<option value=''>Debe seleccionar primero el Supervisor</option>";

            select_equipos_entregados.innerHTML = "<option value=''>Debe seleccionar primero el Supervisor</option>";

            resultado.supervisores.forEach(supervisor => {
                const option_supervisor = document.createElement("option");
                option_supervisor.value = supervisor.id_supervisor;
                option_supervisor.textContent = supervisor.nombre + " | " + supervisor.turno;
                select_supervisores_encargados.append(option_supervisor);
            });
        } catch (error) {
            console.error(error);
        }
    }
    supervisores_registrados();

    select_supervisores_encargados.addEventListener("change", async () => {
        supervisor = select_supervisores_encargados.value;

        await categoria_equipos_entregados();
    });

    async function categoria_equipos_entregados() {
        try {
            const formulario = new FormData();
            formulario.append("supervisores_encargados", supervisor);

            const respuesta = await fetch("/asignaciones/categorias_equipos_entregados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipos.innerHTML = "<option value=''>Selecciona la Categoria</option>";

            select_equipos_entregados.innerHTML = "<option value=''>Debe seleccionar primero la Categoria</option>";

            resultado.categorias.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categoria_equipos.append(option_categoria);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_categoria_equipos.addEventListener("change", async () => {
        categoria = select_categoria_equipos.value;

        await equipos_entregados();
    });

    async function equipos_entregados() {
        try {
            const formulario = new FormData();
            formulario.append("supervisor", supervisor);
            formulario.append("categoria", categoria);

            const respuesta = await fetch("/asignaciones/equipos_entregados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            select_equipos_entregados.innerHTML =
                "<option value=''>Selecciona el Equipo</option>";

            if (!respuesta.ok || resultado.estado !== "exito") {
                await Swal.fire({
                    title: resultado.title || "Error",
                    text: resultado.descripcion || "No fue posible consultar los equipos.",
                    icon: resultado.icon || "error"
                });
                return;
            }

            resultado.equipos.forEach(equipo => {
                const option = document.createElement("option");

                option.value = equipo.id_entrega;
                option.textContent = `${equipo.nombre} | ${equipo.categoria}`;

                option.dataset.id_equipo = equipo.id_equipo;
                option.dataset.cantidad_entregada = equipo.cantidad_entregada;
                option.dataset.cantidad_asignada = equipo.cantidad_asignada;
                option.dataset.cantidad_disponible = equipo.cantidad_disponible;
                option.dataset.observacion_entrega = equipo.observacion;

                select_equipos_entregados.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_equipos_entregados.addEventListener("change", () => {
        input_cantidad_entregada.value = "";
        input_cantidad_actualizar.value = "";

        input_cantidad_actualizar.removeAttribute("min");
        input_cantidad_actualizar.removeAttribute("max");
        input_cantidad_actualizar.classList.remove("is-invalid");

        contenedor_msg_cantidad.textContent = "";
        contenedor_msg_cantidad.className = "mensaje-feedback";

        btn_actualizar.disabled = true;

        const equipo = select_equipos_entregados.selectedOptions[0];

        if (!equipo || !equipo.value) {
            textarea_observacion_entrega.value = "";
            actualizarContador(
                textarea_observacion_entrega,
                contador_observacion
            );
            return;
        }

        const cantidad_entregada = Number(equipo.dataset.cantidad_entregada);
        const cantidad_asignada = Number(equipo.dataset.cantidad_asignada);
        const cantidad_disponible = Number(equipo.dataset.cantidad_disponible);

        if (!Number.isInteger(cantidad_entregada) ||
            !Number.isInteger(cantidad_asignada) ||
            !Number.isInteger(cantidad_disponible) ||
            cantidad_asignada < 0 ||
            cantidad_disponible < 0 ||
            cantidad_asignada + cantidad_disponible !== cantidad_entregada) {
            contenedor_msg_cantidad.textContent = "Las cantidades de la entrega no son consistentes. Consulte al administrador.";

            contenedor_msg_cantidad.className = "mensaje-feedback error";
            return;
        }

        input_cantidad_entregada.value =
            `Entregados: ${cantidad_entregada}. ` +
            `Asignados al personal: ${cantidad_asignada}. ` +
            `Disponibles para asignar: ${cantidad_disponible}.`;

        input_cantidad_actualizar.min = cantidad_asignada;
        input_cantidad_actualizar.max = cantidad_entregada;

        textarea_observacion_entrega.value = equipo.dataset.observacion_entrega || "";

        actualizarContador(
            textarea_observacion_entrega,
            contador_observacion
        );

        if (select_tipo_correccion.value === "ERROR_HUMANO") {
            input_cantidad_actualizar.value = cantidad_entregada;
            input_cantidad_actualizar.dispatchEvent(
                new Event("input", { bubbles: true })
            );
        }
    });


    input_cantidad_actualizar.addEventListener("input", () => {
        input_cantidad_actualizar.value =
            input_cantidad_actualizar.value.replace(/\D/g, "");

        const equipo = select_equipos_entregados.selectedOptions[0];

        const mostrarError = mensaje => {
            contenedor_msg_cantidad.textContent = mensaje;
            contenedor_msg_cantidad.className = "mensaje-feedback error";
            input_cantidad_actualizar.classList.add("is-invalid");
            btn_actualizar.disabled = true;
        };

        if (!input_cantidad_actualizar.value) {
            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";
            input_cantidad_actualizar.classList.remove("is-invalid");
            btn_actualizar.disabled = true;
            return;
        }

        if (!equipo || !equipo.value) {
            mostrarError("Debe seleccionar una entrega.");
            return;
        }

        if (input_cantidad_actualizar.value.length > 3) {
            input_cantidad_actualizar.value =
                input_cantidad_actualizar.value.slice(0, 3);
        }

        const cantidad_entregada = Number(equipo.dataset.cantidad_entregada);
        const cantidad_asignada = Number(equipo.dataset.cantidad_asignada);
        const cantidad_ingresada = Number(input_cantidad_actualizar.value);

        if (
            !Number.isInteger(cantidad_entregada) ||
            !Number.isInteger(cantidad_asignada) ||
            !Number.isInteger(cantidad_ingresada)
        ) {
            mostrarError("No se pudieron validar las cantidades de la entrega.");
            return;
        }

        if (cantidad_ingresada <= 0) {
            mostrarError("La cantidad debe ser un número entero mayor que 0.");
            return;
        }

        if (cantidad_ingresada < cantidad_asignada) {
            mostrarError(
                `La cantidad no puede ser inferior a las ${cantidad_asignada} unidades que siguen asignadas al personal.`
            );
            return;
        }

        if (cantidad_ingresada > cantidad_entregada) {
            mostrarError(
                `La cantidad no puede superar las ${cantidad_entregada} unidades originalmente entregadas.`
            );
            return;
        }

        contenedor_msg_cantidad.textContent = "";
        contenedor_msg_cantidad.className = "mensaje-feedback";
        input_cantidad_actualizar.classList.remove("is-invalid");
        btn_actualizar.disabled = false;
    });

    textarea_motivo_correccion.addEventListener("input", () => {
        textarea_motivo_correccion.value = textarea_motivo_correccion.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_motivo.textContent = textarea_motivo_correccion.value.length;
    });

    textarea_observacion_entrega.addEventListener("input", () => {
        textarea_observacion_entrega.value = textarea_observacion_entrega.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-*]/g,
            ""
        );

        actualizarContador(textarea_observacion_entrega, contador_observacion);
    });

    function actualizarContador(textarea, contador) {
        contador.textContent = textarea.value.length;
    }

    select_tipo_correccion.addEventListener("change", () => {
        const tipo_correccion = select_tipo_correccion.value;
        const equipo = select_equipos_entregados.options[
            select_equipos_entregados.selectedIndex
        ];

        input_cantidad_actualizar.value = "";
        textarea_motivo_correccion.value = "";

        textarea_motivo_correccion.readOnly = false;
        textarea_motivo_correccion.required = Boolean(tipo_correccion);

        if (tipo_correccion === "ERROR_HUMANO") {
            input_cantidad_actualizar.readOnly = true;
            textarea_observacion_entrega.readOnly = true;

            input_cantidad_actualizar.required = false;
            textarea_observacion_entrega.required = false;

            if (equipo && equipo.value) {
                const cantidad = equipo.dataset.cantidad_entregada;

                input_cantidad_actualizar.value = cantidad;

                btn_actualizar.disabled = false;
            } else {
                btn_actualizar.disabled = true;
            }

        } else if (tipo_correccion === "ACTUALIZAR") {
            input_cantidad_actualizar.readOnly = false;
            textarea_observacion_entrega.readOnly = false;

            input_cantidad_actualizar.required = true;
            textarea_observacion_entrega.required = true;

            btn_actualizar.disabled = true;

        } else {
            input_cantidad_actualizar.readOnly = true;
            textarea_observacion_entrega.readOnly = true;

            input_cantidad_actualizar.required = false;
            textarea_observacion_entrega.required = false;

            btn_actualizar.disabled = true;
        }

        actualizarContador(
            textarea_observacion_entrega,
            contador_observacion
        );
    });

    formulario_correccion.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_correccion);

            const respuesta = await fetch("/asignaciones/correccion_entrega_equipos/", {
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

            supervisor = "";
            categoria = "";
            formulario_correccion.reset();
        } catch (error) {
            console.error(error);
        }
    });

});