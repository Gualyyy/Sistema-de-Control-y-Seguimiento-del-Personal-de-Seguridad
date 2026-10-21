document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");

    const select_supervisores_encargados = document.getElementById("supervisores_encargados");
    const select_categoria_equipos = document.getElementById("categoria_equipos");
    const select_equipos_entregar = document.getElementById("equipos_entregar");

    const input_cantidad_equipo = document.getElementById("cantidad_equipo");
    const input_cantidad_disponible = document.getElementById("cantidad_disponible");

    const contenedor_msg_cantidad = document.getElementById("contenedor_msg_cantidad");
    const textarea_observacion_entrega = document.getElementById("observacion_entrega");
    const contador_observacion = document.getElementById("contador_observacion");

    const btn_registrar = document.getElementById("btn_registrar");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let categoria = "";

    textarea_observacion_entrega.addEventListener("input", () => {
        textarea_observacion_entrega.value = textarea_observacion_entrega.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_observacion.textContent = textarea_observacion_entrega.value.length;
    });

    async function supervisores_registrados() {
        try {
            const respuesta = await fetch("/supervisores_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_supervisores_encargados.innerHTML = "<option value=''>Selecciona un Supervisor</option>"

            resultado.supervisores.forEach(supervisor => {
                const option_supervisor = document.createElement("option");
                option_supervisor.value = supervisor.id_supervisor;
                option_supervisor.textContent = supervisor.nombres + " " + supervisor.apellidos + " | " + supervisor.turno;
                select_supervisores_encargados.append(option_supervisor);
            });
        } catch (error) {
            console.error(error);
        }
    }
    supervisores_registrados();

    async function categoria_equipos() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipos.innerHTML = "<option value=''>Selecciona la Categoria</option>"

            select_equipos_entregar.innerHTML = "<option value=''>Debe seleccionar la Categoria primero</option>"

            resultado.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categoria_equipos.append(option_categoria);
            });
        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipos();

    select_categoria_equipos.addEventListener("change", async () => {
        categoria = select_categoria_equipos.value;

        await equipos_entregar();
    });


    async function equipos_entregar() {
        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);

            const respuesta = await fetch("/asignaciones/equipos_registrados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();

            select_equipos_entregar.innerHTML = "<option value=''>Selecciona el equipo</option>";

            if (!respuesta.ok || resultado.estado !== "exito") {
                input_cantidad_disponible.value = "";

                contenedor_msg_cantidad.textContent = resultado.descripcion || "No se pudieron cargar los equipos.";

                contenedor_msg_cantidad.className = "mensaje-feedback error";
                return;
            }

            resultado.equipos.forEach(equipo => {
                const option = document.createElement("option");

                option.value = equipo.id_equipo;
                option.textContent = `${equipo.nombre} | ${equipo.categoria} `;
                option.dataset.cantidadDisponible = equipo.cantidad_disponible;

                select_equipos_entregar.appendChild(option);
            });

        } catch (error) {
            console.error(error);
        }
    }

    function validar_cantidad_entrega() {
        const opcion = select_equipos_entregar.options[
            select_equipos_entregar.selectedIndex
        ];

        const cantidad_texto = input_cantidad_equipo.value;
        const cantidad_disponible = opcion?.value
            ? Number(opcion.dataset.cantidadDisponible)
            : 0;

        input_cantidad_equipo.max = cantidad_disponible || "";
        input_cantidad_equipo.setAttribute("min", "1");

        if (!opcion?.value) {
            input_cantidad_disponible.value = "";
            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";
            input_cantidad_equipo.classList.remove("is-invalid");
            btn_registrar.disabled = true;
            return;
        }

        input_cantidad_disponible.value =
            `Cantidad disponible para entregar: ${cantidad_disponible} `;

        if (cantidad_texto === "") {
            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";
            input_cantidad_equipo.classList.remove("is-invalid");
            btn_registrar.disabled = true;
            return;
        }

        const cantidad = Number(cantidad_texto);

        if (!Number.isInteger(cantidad) || cantidad <= 0) {
            contenedor_msg_cantidad.textContent =
                "La cantidad debe ser un número entero mayor que cero.";
        } else if (cantidad > cantidad_disponible) {
            contenedor_msg_cantidad.textContent = `No puedes entregar más de ${cantidad_disponible} unidad(es).`;
        } else {
            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";
            input_cantidad_equipo.classList.remove("is-invalid");
            btn_registrar.disabled = false;
            return;
        }

        contenedor_msg_cantidad.className = "mensaje-feedback error";
        input_cantidad_equipo.classList.add("is-invalid");
        btn_registrar.disabled = true;
    }

    select_equipos_entregar.addEventListener("change", () => {
        input_cantidad_equipo.value = "";
        validar_cantidad_entrega();
    });

    input_cantidad_equipo.addEventListener("input", () => {
        input_cantidad_equipo.value =
            input_cantidad_equipo.value.replace(/\D/g, "");

        validar_cantidad_entrega();
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/asignaciones/registrar_entrega_equipos/", {
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

            if (resultado.estado === "exito") {
                formulario_registrar.reset();

                contador_observacion.value = "0";

                contenedor_msg_cantidad.textContent = "";
                contenedor_msg_cantidad.className = "mensaje-feedback";

                input_cantidad_equipo.classList.remove("is-invalid");
                input_cantidad_equipo.setCustomValidity("");
                input_cantidad_equipo.removeAttribute("max");
            }

        } catch (error) {
            console.error(error);
        }
    });

});