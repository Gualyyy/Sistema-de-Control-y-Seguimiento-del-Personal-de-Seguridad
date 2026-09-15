document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");
    const select_empleados = document.getElementById("empleados_registrados");
    const select_perfiles = document.getElementById("perfiles_asignados");
    const select_equipos = document.getElementById("equipos_registrados");

    const input_cantidad_entrega = document.getElementById("cantida_entrega");
    const input_cantidad_actual = document.getElementById("cantida_actual");
    const contenedor_msg_cantidad = document.getElementById("contenedor_msg_cantidad");

    const contador_observacion = document.getElementById("contador_observacion");
    const textarea_observacion_entrega = document.getElementById("observacion_entrega");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let equipo = "", usuario = "", perfil = "";

    async function empleados_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/empleados_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_perfiles.innerHTML = "<option value='' selected>Debe seleccionar un Empleado</option>";

            select_empleados.innerHTML = "<option value='' selected>Seleccione el Empleado</option>";

            resultado.forEach(usuario => {
                const option = document.createElement("option");
                option.value = usuario.id_usuario;
                option.textContent = usuario.nombres + " " + usuario.apellidos;
                select_empleados.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    empleados_registrados();

    select_empleados.addEventListener("change", async () => {
        usuario = select_empleados.value;

        await perfiles_asignados();

        await datos_equipo_seleccionado();
    });

    async function perfiles_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("id_usuario", usuario)

            const respuesta = await fetch("/asignaciones/perfiles_asignados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_perfiles.innerHTML = "<option value='' selected>Selecciona el perfil</option>";

            resultado.forEach(perfil => {
                const option = document.createElement("option");
                option.value = perfil.id_perfil;
                option.textContent = perfil.perfil;
                select_perfiles.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_perfiles.addEventListener("change", async () => {
        perfil = select_perfiles.value;

        await datos_equipo_seleccionado();
    });

    async function equipos_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/equipos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_equipos.innerHTML = "<option value='' selected>Seleccione el Equipo</option>";

            resultado.forEach(equipo => {
                const option_equipo = document.createElement("option");
                option_equipo.value = equipo.id_equipo;
                option_equipo.textContent = equipo.nombre + " - " + equipo.categoria;
                select_equipos.append(option_equipo);
            });
        } catch (error) {
            console.error(error);
        }
    }
    equipos_registrados();

    input_cantidad_entrega.addEventListener("input", () => {
        input_cantidad_entrega.value = input_cantidad_entrega.value.replace(/\D/g, "");

        if (input_cantidad_entrega.value === "") {
            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";
            input_cantidad_entrega.classList.remove("is-invalid");
            return;
        }

        if (input_cantidad_entrega.value.startsWith("0")) {
            contenedor_msg_cantidad.textContent = "La cantidad debe ser un número entero mayor a 0 y no puede comenzar con 0.";
            contenedor_msg_cantidad.className = "mensaje-feedback error";

            input_cantidad_entrega.classList.add("is-invalid");
            input_cantidad_entrega.value = "";
            return;
        }

        if (input_cantidad_entrega.value.length > 3) {
            input_cantidad_entrega.value = input_cantidad_entrega.value.slice(0, 3);
        }

        const cantidad_ingresada = parseInt(input_cantidad_entrega.value, 10);
        const cantidad_actual = parseInt(input_cantidad_actual.value, 10);

        if (cantidad_ingresada > cantidad_actual) {
            contenedor_msg_cantidad.textContent = `No se permite entregar una cantidad mayor a la actual (${cantidad_actual}).`;
            contenedor_msg_cantidad.className = "mensaje-feedback error";

            input_cantidad_entrega.classList.add("is-invalid");
            return;
        }

        contenedor_msg_cantidad.textContent = "";
        contenedor_msg_cantidad.className = "mensaje-feedback";

        input_cantidad_entrega.classList.remove("is-invalid");
    });

    select_equipos.addEventListener("change", async (e) => {
        equipo = select_equipos.value;

        await datos_equipo_seleccionado();
    });

    async function datos_equipo_seleccionado() {
        try {
            if (!equipo) return;

            const formulario = new FormData();
            formulario.append("id_equipo", equipo);
            formulario.append("id_usuario", usuario);
            formulario.append("id_perfil", perfil);

            const respuesta = await fetch("/asignaciones/datos_equipo_seleccionado/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            // DATOS DE LA ASIGNACIÓN
            textarea_observacion_entrega.value = resultado.asignacion.observacion || "";

            actualizarContador(textarea_observacion_entrega, contador_observacion);

            // DATOS DEL EQUIPO
            const cantidadDisponible = parseInt(resultado.equipo.cantidad_disponible) || 0;

            input_cantidad_actual.value = "Cuenta con " + cantidadDisponible + " unidades disponibles para asignar";

            input_cantidad_entrega.max = cantidadDisponible;
            input_cantidad_entrega.min = 1;
            input_cantidad_entrega.value = "";

            // VALIDAR CANTIDAD
            input_cantidad_entrega.oninput = () => {
                input_cantidad_entrega.value = input_cantidad_entrega.value.replace(/[^0-9]/g, "");

                const cantidadMaxima = parseInt(input_cantidad_entrega.max) || 0;
                const cantidadIngresada = parseInt(input_cantidad_entrega.value) || 0;

                if (cantidadIngresada > cantidadMaxima) {
                    input_cantidad_entrega.value = cantidadMaxima;
                }
            };
        } catch (error) {
            console.error(error);
        }
    }

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

            if (resultado.estado == "fallo") {
                return;
            }

            select_perfiles.innerHTML = "<option value='' selected>Debe seleccionar un Empleado</option>";
            formulario_registrar.reset();
        } catch (error) {
            console.error(error);
        }
    });

});