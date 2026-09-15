document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const formulario_registrar = document.getElementById("formulario_registrar");
    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const contenedor_perfiles = document.getElementById("contenedor_perfiles_registrados");

    const input_nombres_empleado = document.getElementById("nombres_empleado");
    const input_apellidos_empleado = document.getElementById("apellidos_empleado");

    const select_turnos_registro = document.getElementById("turnos_registro");
    const input_usuario_registro = document.getElementById("usuario_registro");

    const select_turno_actualizar = document.getElementById("actualizar_turno");

    const input_perfil_asignado = document.getElementById("id_perfil_asignado");

    const btn_asignar_perfil = document.getElementById("asignar_perfil");
    const dialogo_asignacion = document.getElementById("dialogo_registro");
    const btn_cerrar_registro = document.getElementById("btn_cerrar_registro");

    const dialogo_gestion = document.getElementById("dialogo_gestion");
    const btn_cerrar_gestion = document.getElementById("btn_cerrar_gestion");
    const input_habilitar_perfil = document.getElementById("habilitar_perfil");
    const input_deshabilitar_perfil = document.getElementById("deshabilitar_perfil");

    const contenedor_asignacion_perfil = document.getElementById("contenedor_asignacion_perfil");

    const contenedor_mensaje_turno = document.getElementById("contenedor_mensaje_turno");
    const contenedor_texto_mensaje_turno = document.getElementById("contenedor_texto_mensaje_turno");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    configurarCedula(input_cedula_identidad, select_nacionalidad);

    let turno = "";

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/buscar_datos_asignacion/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            formulario_busqueda.reset();

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            await Swal.fire({
                title: "Éxito",
                text: "Datos del empleado encontrado exitosamente",
                icon: "success"
            });

            btn_asignar_perfil.disabled = false;

            input_usuario_registro.value = resultado.usuario.id_usuario;
            input_nombres_empleado.value = resultado.usuario.nombres;
            input_apellidos_empleado.value = resultado.usuario.apellidos;

            contenedor_perfiles.innerHTML = "";

            resultado.perfiles.forEach((perfil, index) => {
                const fila = document.createElement("tr");
                fila.dataset.idPerfilUsuario = perfil.id_perfil_usuario;
                fila.dataset.vigencia = perfil.vigencia;

                fila.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${perfil.perfil}</td>
                    <td>${perfil.turno}</td>
                    <td>${perfil.vigencia ? "Activo" : "Inactivo"}</td>
                `;

                contenedor_perfiles.appendChild(fila);
            });
        } catch (error) {
            console.error(error);
        }
    });

    async function perfiles_asignados() {
        try {
            const respuesta = await fetch("/cargar_perfiles_asignados/");
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
            contenedor_perfiles.innerHTML = "";

            resultado.perfiles.forEach((perfil, index) => {
                const fila = document.createElement("tr");
                fila.dataset.idPerfilUsuario = perfil.id_perfil_usuario;
                fila.dataset.vigencia = perfil.vigencia;

                fila.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${perfil.perfil}</td>
                    <td>${perfil.turno}</td>
                    <td>${perfil.vigencia ? "Activo" : "Inactivo"}</td>
                `;

                contenedor_perfiles.appendChild(fila);
            });
        } catch (error) {
            console.error(error);
        }
    }

    btn_asignar_perfil.addEventListener("click", async () => {
        try {
            const respuesta = await fetch("/cantidad_perfiles_asignado/");
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

            dialogo_asignacion.showModal();
        } catch (error) {
            console.log(error);
        }
    });

    async function turnos_registrados() {
        try {
            const respuesta = await fetch("/turnos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_turnos_registro.innerHTML = "<option value='' selected>Seleccione un Turno</option>";

            select_turno_actualizar.innerHTML = "";

            resultado.forEach(turno => {
                const option_registrar = document.createElement("option");
                option_registrar.value = turno.id_turno;
                option_registrar.textContent = turno.nombre;
                select_turnos_registro.append(option_registrar);

                const option_actualizar = document.createElement("option");
                option_actualizar.value = turno.id_turno;
                option_actualizar.textContent = turno.nombre;
                select_turno_actualizar.append(option_actualizar);
            });
        } catch (error) {
            console.error(error);
        }
    }
    turnos_registrados();

    select_turnos_registro.addEventListener("change", async () => {
        turno = select_turnos_registro.value;

        try {
            contenedor_asignacion_perfil.innerHTML = "";

            contenedor_mensaje_turno.style.display = "none";
            contenedor_texto_mensaje_turno.textContent = "";

            if (!turno) {
                contenedor_asignacion_perfil.innerHTML = `
                    <p class="contenedor_vacio">
                        Seleccione un turno para mostrar los perfiles disponibles.
                    </p>
                `;
                return;
            }

            const formulario = new FormData();
            formulario.append("turno", turno);

            const respuesta = await fetch("/perfiles_usuario_no_registrados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.mensaje) {
                contenedor_texto_mensaje_turno.textContent = resultado.mensaje;
                contenedor_mensaje_turno.style.display = "block";
            }

            if (!resultado.perfiles || resultado.perfiles.length === 0) {
                contenedor_asignacion_perfil.innerHTML = `
                    <p class="contenedor_vacio">
                        Seleccione un turno para mostrar los perfiles disponibles.
                    </p>
                `;
                return;
            }

            resultado.perfiles.forEach(perfil => {
                const div = document.createElement("div");
                div.classList.add("perfil-item");

                const input = document.createElement("input");

                if (perfil.perfil === "Supervisor Encargado") {
                    input.type = "radio";
                } else {
                    input.type = "checkbox";
                }

                input.name = "perfiles";
                input.value = perfil.id_perfil;
                input.id = `perfil_${perfil.id_perfil}`;

                const label = document.createElement("label");

                label.htmlFor = `perfil_${perfil.id_perfil}`;
                label.textContent = perfil.perfil;

                div.appendChild(input);
                div.appendChild(label);

                contenedor_asignacion_perfil.appendChild(div);
            });
        } catch (error) {
            console.error(error);

            contenedor_asignacion_perfil.innerHTML = `
                <p class="contenedor_vacio">
                    No se pudieron cargar los perfiles disponibles.
                </p>
            `;

            contenedor_mensaje_turno.style.display = "none";
            contenedor_texto_mensaje_turno.textContent = "";
        }
    });


    btn_cerrar_registro.addEventListener("click", () => {
        dialogo_asignacion.close();
    });

    btn_cerrar_gestion.addEventListener("click", () => {
        dialogo_gestion.close();
    });


    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/actualizar_vigencia_perfil/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_gestion.close();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            await perfiles_asignados();
            formulario_actualizar.reset();
        } catch (error) {
            console.error(error);
        }
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/registrar_nueva_asignacion/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_asignacion.close();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            await perfiles_asignados();
            formulario_busqueda.reset();
        } catch (error) {
            console.error(error);
        }
    });


    contenedor_perfiles.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (!fila) return;

        try {
            const formulario = new FormData();
            formulario.append("id_perfil_usuario", fila.dataset.idPerfilUsuario);

            const respuesta = await fetch("/buscar_datos_perfil/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
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

            input_perfil_asignado.value = resultado.id_perfil_usuario

            const option = document.createElement("option");
            option.value = resultado.id_turno;
            option.textContent = resultado.turno;
            option.selected = true;
            option.hidden = true;
            select_turno_actualizar.append(option);

            input_habilitar_perfil.checked = resultado.vigencia;
            input_deshabilitar_perfil.checked = !resultado.vigencia;

            dialogo_gestion.showModal();
        } catch (error) {
            console.error(error);
        }
    });
});