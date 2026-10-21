document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");

    const select_empleados = document.getElementById("empleados_registrados");
    const select_equipos = document.getElementById("equipos_registrados");

    const input_cantidad_entrega = document.getElementById("cantidad_entrega");
    const input_cantidad_actual = document.getElementById("cantidad_actual");
    const contenedor_msg_cantidad = document.getElementById("contenedor_msg_cantidad");

    const contador_observacion = document.getElementById("contador_observacion");
    const textarea_observacion_entrega = document.getElementById("observacion_entrega");

    const btn_registro = document.getElementById("btn_registro");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let equipo = "", empleado = "";

    async function empleados_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/empleados_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_empleados.innerHTML = "<option value='' selected>Seleccione el Empleado</option>";

            if (resultado.estado == "fallo") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            resultado.forEach(usuario => {
                const option = document.createElement("option");
                option.value = usuario.id_usuario;
                option.textContent = usuario.nombres + " " + usuario.apellidos + " | " + usuario.perfil;
                select_empleados.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    empleados_registrados();

    select_empleados.addEventListener("change", async () => {
        empleado = select_empleados.value;

        await datos_equipo_seleccionado();
    });

    async function equipos_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/equipos_registrados_supervisor/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_equipos.innerHTML = "<option value='' selected>Seleccione el Equipo</option>";

            resultado.forEach(equipo => {
                const option_equipo = document.createElement("option");
                option_equipo.value = equipo.id_equipo;
                option_equipo.textContent = equipo.nombre + " | " + equipo.categoria;
                select_equipos.append(option_equipo);
            });
        } catch (error) {
            console.error(error);
        }
    }
    equipos_registrados();

    select_equipos.addEventListener("change", async (e) => {
        equipo = select_equipos.value;

        await datos_equipo_seleccionado();
    });

    let cantidadDisponibleEquipo = 0;
    let idEntregaSeleccionada = null;

    async function datos_equipo_seleccionado() {
        try {
            if (!equipo || !empleado) return;

            const formulario = new FormData();
            formulario.append("id_equipo", equipo);
            formulario.append("id_usuario", empleado);

            const respuesta = await fetch("/asignaciones/datos_equipo_seleccionado/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });

                cantidadDisponibleEquipo = 0;
                idEntregaSeleccionada = null;
                input_cantidad_actual.value = "";
                textarea_observacion_entrega.value = "";
                input_cantidad_entrega.value = "";

                btn_registro.disabled = true;
                return;
            }

            const datos = resultado.datos;

            idEntregaSeleccionada = datos.id_entrega;
            cantidadDisponibleEquipo = Number(datos.cantidad_disponible) || 0;

            textarea_observacion_entrega.value = datos.observacion || "";
            actualizarContador(
                textarea_observacion_entrega,
                contador_observacion
            );

            input_cantidad_actual.value = `Disponible para asignar: ${cantidadDisponibleEquipo}`;

            input_cantidad_entrega.removeAttribute("max");
            input_cantidad_entrega.min = 1;
            input_cantidad_entrega.value = "";

            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";
            input_cantidad_entrega.classList.remove("is-invalid");

            btn_registro.disabled = true;

            if (cantidadDisponibleEquipo <= 0) {
                contenedor_msg_cantidad.textContent = "Esta entrega no tiene unidades disponibles.";
                contenedor_msg_cantidad.className = "mensaje-feedback error";
            }

        } catch (error) {
            console.error("Error al consultar los datos del equipo:", error);

            cantidadDisponibleEquipo = 0;
            idEntregaSeleccionada = null;
            input_cantidad_actual.value = "";
            textarea_observacion_entrega.value = "";
            input_cantidad_entrega.value = "";

            btn_registro.disabled = true;
        }
    }

    input_cantidad_entrega.addEventListener("input", () => {
        input_cantidad_entrega.value =
            input_cantidad_entrega.value.replace(/\D/g, "");

        const cantidadTexto = input_cantidad_entrega.value;

        const mostrarError = (mensaje) => {
            contenedor_msg_cantidad.textContent = mensaje;
            contenedor_msg_cantidad.className = "mensaje-feedback error";
            input_cantidad_entrega.classList.add("is-invalid");
            btn_registro.disabled = true;
        };

        if (!idEntregaSeleccionada || cantidadDisponibleEquipo <= 0) {
            mostrarError("Seleccione una entrega con unidades disponibles.");
            return;
        }

        if (cantidadTexto === "") {
            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";
            input_cantidad_entrega.classList.remove("is-invalid");
            btn_registro.disabled = true;
            return;
        }

        if (cantidadTexto.startsWith("0")) {
            mostrarError(
                "La cantidad debe ser un entero mayor que cero y no puede comenzar con 0."
            );
            return;
        }

        if (cantidadTexto.length > 3) {
            input_cantidad_entrega.value = cantidadTexto.slice(0, 3);
        }

        const cantidadIngresada = Number(input_cantidad_entrega.value);

        if (!Number.isInteger(cantidadIngresada) || cantidadIngresada <= 0) {
            mostrarError("La cantidad debe ser un número entero mayor que cero.");
            return;
        }

        if (cantidadIngresada > cantidadDisponibleEquipo) {
            mostrarError(
                `No se permite asignar una cantidad mayor a la disponible (${cantidadDisponibleEquipo}).`
            );
            return;
        }

        contenedor_msg_cantidad.textContent = "";
        contenedor_msg_cantidad.className = "mensaje-feedback";
        input_cantidad_entrega.classList.remove("is-invalid");
        btn_registro.disabled = false;
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

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/asignaciones/asignar_equipo_usuario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            equipo = "";
            empleado = "";
            contador_observacion.value = 0;
            formulario_registrar.reset();
        } catch (error) {
            console.error(error);
        }
    });

});