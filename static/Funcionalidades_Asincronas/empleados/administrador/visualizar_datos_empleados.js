document.addEventListener("DOMContentLoaded", () => {

    const dialogo_empleado = document.getElementById("dialogo_empleado");
    const btn_cerrar = document.getElementById("btn_cerrar");
    const contenedor_empleados = document.getElementById("contenedor_empleados");

    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const select_perfiles_registrados = document.getElementById("perfiles_registrados");

    const id_empleado = document.getElementById("id_empleado");

    const nombres_usuario = document.getElementById("nombre_usuario");
    const apellido_usuario = document.getElementById("apellido_usuario");
    const cedula_usuario = document.getElementById("cedula_usuario");
    const genero_usuario = document.getElementById("genero_usuario");
    const estado_civil_usuario = document.getElementById("estado_civil_usuario");

    const telefono_principal_usuario = document.getElementById("telefono_principal_usuario");
    const telefono_secundaria_usuario = document.getElementById("telefono_secundaria_usuario");
    const correo_principal_usuario = document.getElementById("correo_principal_usuario");
    const correo_secundario_usuario = document.getElementById("correo_secundario_usuario");

    const pais_nacimiento_usuario = document.getElementById("pais_nacimiento_usuario");
    const estado_nacimiento_usuario = document.getElementById("estado_nacimiento_usuario");
    const municipio_nacimiento_usuario = document.getElementById("municipio_nacimiento_usuario");
    const parroquia_nacimiento_usuario = document.getElementById("parroquia_nacimiento_usuario");
    const direccion_nacimiento_usuario = document.getElementById("direccion_nacimiento_usuario");
    const fecha_nacimiento_usuario = document.getElementById("fecha_nacimiento_usuario");

    const condicion_residencia_usuario = document.getElementById("condicion_residencia_usuario");
    const municipio_residencia = document.getElementById("municipio_residencia");
    const parroquia_residencia = document.getElementById("parroquia_residencia");
    const direccion_domicilio = document.getElementById("direccion_domicilio");

    const contenedor_perfiles_asignados = document.getElementById("contenedor_perfiles_asignados");

    const btn_ret = document.querySelector(".botones_navegacion .btn_ret");
    const btn_av = document.querySelector(".botones_navegacion .btn_av");

    const lista_empleados_pdf = document.getElementById("lista_empleados_pdf");
    const datos_empleado_pdf = document.getElementById("datos_empleado_pdf");

    let nacionalidad = "", cedula = "", cedulaUsuario = "", perfil = "";

    let empleados_recibidos = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    configurarPasos(".contenedor_datos_contenido");
    configurarCedula(input_cedula_identidad, select_nacionalidad);

    function perfiles_registrados() {
        const perfiles = [
            "Supervisor Encargado",
            "Personal de Limpieza",
            "Despachador",
            "Vigilante"
        ];

        select_perfiles_registrados.innerHTML = "<option value='' selected>Selecciona un Perfil</option>";

        perfiles.forEach(perfil => {
            const option = document.createElement("option");
            option.value = perfil;
            option.textContent = perfil;
            select_perfiles_registrados.append(option);
        });
    }
    perfiles_registrados();

    select_perfiles_registrados.addEventListener("change", async () => {
        perfil = select_perfiles_registrados.value;

        await usuarios_registrados();
    });

    select_nacionalidad.addEventListener("change", async () => {
        nacionalidad = select_nacionalidad.value;

        await usuarios_registrados();
    });

    input_cedula_identidad.addEventListener("input", async () => {
        cedula = input_cedula_identidad.value;

        await usuarios_registrados();
    });

    function mostrarEmpleados() {
        contenedor_empleados.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const empleados_pagina = empleados_recibidos.slice(inicio, final);

        if (empleados_pagina.length === 0) {
            contenedor_empleados.innerHTML = `
                <tr>
                    <td colspan="6" class="texto_sin_registros">
                        No hay empleados registrados.
                    </td>
                </tr>
            `;

            actualizarBotones();
            return;
        }

        empleados_pagina.forEach((usuario, index) => {
            const fila = document.createElement("tr");
            fila.dataset.cedula = usuario.cedula;

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td>${usuario.nombres}</td>
                <td>${usuario.apellidos}</td>
                <td>${usuario.cedula}</td>
                <td>${usuario.perfil}</td>
                <td>${usuario.turno}</td>
            `;

            contenedor_empleados.appendChild(fila);
        });

        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(empleados_recibidos.length / filas_por_pagina);

        btn_ret.disabled = pagina_actual === 1;

        btn_av.disabled = pagina_actual >= total_paginas;
    }

    btn_ret.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarEmpleados();
        }
    });

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            empleados_recibidos.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarEmpleados();
        }
    });

    async function usuarios_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("nacionalidad", nacionalidad);
            formulario.append("cedula", cedula);
            formulario.append("perfil", perfil);

            const respuesta = await fetch("/visualizacion_datos_usuarios/", {
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

            empleados_recibidos = Array.isArray(resultado) ? resultado : [];
            pagina_actual = 1;
            mostrarEmpleados();
        } catch (error) {
            console.error(error);
        }
    }
    usuarios_registrados();

    contenedor_empleados.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (!fila) return;

        cedulaUsuario = fila.dataset.cedula;
        [nacionalidad, cedula] = cedulaUsuario.split("-");

        try {
            const formulario = new FormData();
            formulario.append("nacionalidad", nacionalidad)
            formulario.append("cedula", cedula)

            const respuesta = await fetch("/buscar_datos_usuario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
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

            dialogo_empleado.showModal();

            id_empleado.value = resultado.usuario.id;

            nombres_usuario.value = resultado.usuario.nombres;
            apellido_usuario.value = resultado.usuario.apellidos;
            cedula_usuario.value = resultado.usuario.cedula_identidad;
            genero_usuario.value = resultado.usuario.genero;
            estado_civil_usuario.value = resultado.usuario.estado_civil;

            telefono_principal_usuario.value = resultado.contacto.telefono_principal;
            telefono_secundaria_usuario.value = resultado.contacto.telefono_secundario;
            correo_principal_usuario.value = resultado.contacto.correo_principal;
            correo_secundario_usuario.value = resultado.contacto.correo_secundario;

            pais_nacimiento_usuario.value = resultado.nacimiento.pais;
            estado_nacimiento_usuario.value = resultado.nacimiento.estado;
            municipio_nacimiento_usuario.value = resultado.nacimiento.municipio;
            parroquia_nacimiento_usuario.value = resultado.nacimiento.parroquia;
            direccion_nacimiento_usuario.value = resultado.nacimiento.direccion;
            fecha_nacimiento_usuario.value = resultado.nacimiento.fecha_nacimiento;

            condicion_residencia_usuario.value = resultado.residencia.condicion_residencia;
            municipio_residencia.value = resultado.residencia.municipio;
            parroquia_residencia.value = resultado.residencia.parroquia;
            direccion_domicilio.value = resultado.residencia.direccion;

            contenedor_perfiles_asignados.innerHTML = "";

            if (resultado.laboral.perfil === "N/A") {
                contenedor_perfiles_asignados.innerHTML = `
                    <p>No tiene un perfil laboral asignado.</p>
                `;
            } else {
                const grupoPerfil = document.createElement("div");
                grupoPerfil.classList.add("grupo_perfil");

                grupoPerfil.innerHTML = `
                    <label for="perfil_asignado">Perfil Laboral:</label>
                    <input type="text" id="perfil_asignado" value="${resultado.laboral.perfil}" readonly>

                    <label for="turno_asignado">Turno Laboral:</label>
                    <input type="text" id="turno_asignado" value="${resultado.laboral.turno}" readonly>
                `;

                contenedor_perfiles_asignados.appendChild(grupoPerfil);
            }
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_empleado.close();
    });

    lista_empleados_pdf.addEventListener("click", () => {
        const formulario = document.createElement("form");

        formulario.method = "POST";
        formulario.action = "/lista_empleados_pdf/";
        formulario.target = "_blank";
        const tabId = document.body.dataset.tabId;

        formulario.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" 
                value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">

            <input type="hidden" name="tab_id" value="${tabId}">

            <input type="hidden" name="perfil"
                value="${select_perfiles_registrados.value}">
        `;

        document.body.appendChild(formulario);
        formulario.submit();
        formulario.remove();
    });

    datos_empleado_pdf.addEventListener("click", () => {
        const formulario = document.createElement("form");
        formulario.method = "POST";
        formulario.action = "/datos_empleados_pdf/";
        formulario.target = "_blank";

        const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const idUsuario = document.querySelector("#id_empleado").value;
        const tabId = document.body.dataset.tabId;

        formulario.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
            
            <input type="hidden" name="tab_id" value="${tabId}">

            <input type="hidden" name="id_usuario" value="${idUsuario}">
        `;

        document.body.appendChild(formulario);
        formulario.submit();
        formulario.remove();
    });
});