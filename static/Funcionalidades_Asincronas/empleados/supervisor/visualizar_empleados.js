document.addEventListener("DOMContentLoaded", async () => {

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

    const btn_ret = document.querySelector(".botones_navegacion .btn_ret");
    const btn_av = document.querySelector(".botones_navegacion .btn_av");

    let empleados_registrados = [];
    let pagina_actual = 0;

    const filas_por_pagina = 10;

    let nacionalidad = "", cedula = "", cedulaUsuario = "", perfil = "";

    configurarCedula(input_cedula_identidad, select_nacionalidad)

    function perfiles_registrados() {
        const perfiles = [
            "Personal de Limpieza",
            "Despachador",
            "Vigilante"
        ];

        select_perfiles_registrados.innerHTML = "<option value='' selected>Todos los Perfiles</option>";

        perfiles.forEach(perfil => {
            const option = document.createElement("option");
            option.value = perfil;
            option.textContent = perfil;
            select_perfiles_registrados.append(option);
        });
    }
    perfiles_registrados();

    document.addEventListener("DOMContentLoaded", async () => {
        await usuarios_registrados();
    });

    select_nacionalidad.addEventListener("change", async () => {
        await usuarios_registrados();
    });

    input_cedula_identidad.addEventListener("input", async () => {
        await usuarios_registrados();
    });

    select_perfiles_registrados.addEventListener("input", async () => {
        await usuarios_registrados();
    });

    async function usuarios_registrados() {
        try {
            const formulario = new FormData();

            nacionalidad = select_nacionalidad.value;
            cedula = input_cedula_identidad.value.trim();
            perfil = select_perfiles_registrados.value;

            formulario.append("nacionalidad", nacionalidad);
            formulario.append("cedula", cedula);
            formulario.append("perfil", perfil);

            const respuesta = await fetch("/visualizar_empleado_supervisor/", {
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

            if (resultado.estado === "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });

                return;
            }

            empleados_registrados = resultado.empleados || [];
            pagina_actual = 0;

            mostrar_empleados();

        } catch (error) {
            console.error(error);
        }
    }

    /* MOSTRAR EMPLEADOS POR PÁGINA */

    function mostrar_empleados() {
        contenedor_empleados.innerHTML = "";

        const inicio = pagina_actual * filas_por_pagina;
        const fin = inicio + filas_por_pagina;

        const empleados_pagina = empleados_registrados.slice(inicio, fin);

        if (empleados_pagina.length === 0) {
            contenedor_empleados.innerHTML = `
            <tr>
                <td colspan="6" class="texto_sin_registros">
                    No se encuentra empleado registrado.
                </td>
            </tr>
        `;
        } else {
            empleados_pagina.forEach((usuario, index) => {
                const fila = document.createElement("tr");
                fila.dataset.cedula = usuario.cedula;

                const valores = [
                    inicio + index + 1,
                    usuario.nombres,
                    usuario.apellidos,
                    usuario.cedula,
                    usuario.perfil
                ];

                valores.forEach(valor => {
                    const celda = document.createElement("td");
                    celda.textContent = valor ?? "";
                    fila.appendChild(celda);
                });

                contenedor_empleados.appendChild(fila);
            });
        }

        actualizar_botones();
    }

    /* ACTUALIZAR ESTADO DE LOS BOTONES */
    function actualizar_botones() {
        const total_paginas = Math.ceil(
            empleados_registrados.length / filas_por_pagina
        );

        btn_ret.disabled = pagina_actual === 0;

        btn_av.disabled = pagina_actual >= total_paginas - 1;
    }

    /* RETROCEDER */
    btn_ret.addEventListener("click", function (e) {
        e.preventDefault();

        if (pagina_actual > 0) {
            pagina_actual--;
            mostrar_empleados();
        }
    });

    /* AVANZAR */
    btn_av.addEventListener("click", function (e) {
        e.preventDefault();

        const total_paginas = Math.ceil(
            empleados_registrados.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas - 1) {
            pagina_actual++;
            mostrar_empleados();
        }
    });

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

        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_empleado.close();
    });

});