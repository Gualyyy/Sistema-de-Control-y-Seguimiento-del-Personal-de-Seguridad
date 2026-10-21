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

    const lista_empleados_pdf = document.getElementById("lista_empleados_pdf");
    const datos_empleado_pdf = document.getElementById("datos_empleado_pdf");

    let nacionalidad = "", cedula = "", cedulaUsuario = "", perfil = "";

    configurarPasos(".contenedor_datos_contenido");
    configurarCedula(input_cedula_identidad, select_nacionalidad);

    function perfiles_registrados() {
        const perfiles = [
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

    async function usuarios_registrados() {
        try {
            const formulario = new FormData();
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

            contenedor_empleados.innerHTML = "";

            resultado.empleados.forEach((usuario, index) => {
                contenedor_empleados.innerHTML += `
                <tr data-cedula="${usuario.cedula}">
                    <td>${index + 1}</td>
                    <td>${usuario.nombres}</td>
                    <td>${usuario.apellidos}</td>
                    <td>${usuario.cedula}</td>
                    <td>${usuario.perfil}</td>
                    <td>${usuario.turno}</td>
                </tr>
            `;
            });
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

        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_empleado.close();
    });

    lista_empleados_pdf.addEventListener("click", async () => {
        try {
            const formulario = new FormData();
            formulario.append("csrfmiddlewaretoken", document.querySelector('[name="csrfmiddlewaretoken"]').value);
            formulario.append("tab_id", document.body.dataset.tabId);
            formulario.append("perfil", select_perfiles_registrados.value);

            const respuesta = await fetch("/lista_empleado_supervisor_pdf/", {
                method: "POST",
                body: formulario
            });
            const tipoContenido = respuesta.headers.get("content-type");
            if (tipoContenido.includes("application/json")) {
                const resultado = await respuesta.json();
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);
            window.open(url, "_blank");

            setTimeout(() => URL.revokeObjectURL(url), 60000);

        } catch (error) {
            console.error(error);
        }
    });

    datos_empleado_pdf.addEventListener("click", async () => {
        const idUsuario = document.querySelector("#id_empleado").value;

        const formulario = new FormData();
        formulario.append("csrfmiddlewaretoken", document.querySelector('[name="csrfmiddlewaretoken"]').value);
        formulario.append("tab_id", document.body.dataset.tabId);
        formulario.append("id_usuario", idUsuario);

        try {
            const respuesta = await fetch("/datos_empleados_pdf/", {
                method: "POST",
                body: formulario
            });

            const tipoContenido = respuesta.headers.get("content-type") || "";
            if (tipoContenido.includes("application/json")) {
                const resultado = await respuesta.json();

                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);
            window.open(url, "_blank");

            setTimeout(() => URL.revokeObjectURL(url), 60000);

        } catch (error) {
            console.error(error);
        }
    });
});