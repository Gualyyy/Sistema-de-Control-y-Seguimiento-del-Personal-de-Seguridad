document.addEventListener("DOMContentLoaded", () => {

    const select_tipos_incidencias = document.getElementById("tipos_incidencias");
    const select_turno_laboral = document.getElementById("turno_laboral");

    const contenedor_incidencias = document.getElementById("contenedor_incidencias");

    const btn_retroceder = document.querySelector(".btn_retroceder");
    const btn_avanzar = document.querySelector(".btn_avanzar");

    const dialogo_incidencia = document.getElementById("dialogo_incidencia");
    const btn_cerrar_incidencia = document.getElementById("btn_cerrar_incidencia");

    const input_titulo_v = document.getElementById("titulo_incidencia_visualizar");
    const input_tipo_incidencia_v = document.getElementById("tipo_incidencia_v");
    const textarea_descripcion_incidencia_v = document.getElementById("descripcion_incidencia_v");
    const input_fecha_incidencia_v = document.getElementById("fecha_incidencia_v");
    const input_estado_v = document.getElementById("estado_v");
    const input_solucion_v = document.getElementById("solucion_v");
    const input_fecha_resolucion_v = document.getElementById("fecha_resolucion_v");

    const dialogo_solucion = document.getElementById("dialogo_solucion");
    const btn_cerrar_solucion = document.getElementById("btn_cerrar_solucion");

    const formulario_solucion = document.getElementById("formulario_solucion");
    const input_id_incidencia = document.getElementById("id_incidencia");
    const select_estado_incidencia = document.getElementById("estado_incidencia");
    const textarea_solucion_incidencia = document.getElementById("solucion_incidencia");
    const contador_solucion_incidencia = document.getElementById("contador_solucion_incidencia");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let tipo_incidencia = "", turno_laboral = "";

    let incidencias_recibidas = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    async function tipos_incidencias() {
        try {
            const respuesta = await fetch("/incidencias/tipos_incidencias/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_tipos_incidencias.innerHTML = "<option value='' selected>Selecciona el Tipo de Incidencia</option>";

            resultado.forEach(incidencia => {
                const option = document.createElement("option");
                option.value = incidencia.id_tipo;
                option.textContent = incidencia.nombre;
                select_tipos_incidencias.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    tipos_incidencias();

    async function turnos_registrados() {
        try {
            const respuesta = await fetch("/turnos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_turno_laboral.innerHTML = "<option value='' selected>Seleccione un Turno</option>";

            resultado.forEach(turno => {
                const option = document.createElement("option");
                option.value = turno.id_turno;
                option.textContent = turno.nombre;
                select_turno_laboral.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    turnos_registrados();

    select_tipos_incidencias.addEventListener("change", async () => {
        tipo_incidencia = select_tipos_incidencias.value;

        await incidencia_recibida();
    });

    select_turno_laboral.addEventListener("change", async () => {
        turno_laboral = select_turno_laboral.value;

        await incidencia_recibida();
    });

    function mostrarIncidencias() {
        contenedor_incidencias.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const incidencias_pagina =
            incidencias_recibidas.slice(inicio, final);

        if (incidencias_pagina.length === 0) {
            contenedor_incidencias.innerHTML = `
            <tr>
                <td colspan="5">
                    No hay incidencias recibidas.
                </td>
            </tr>
        `;

            actualizarBotones();
            return;
        }

        incidencias_pagina.forEach((incidencia, index) => {
            const fila = document.createElement("tr");

            fila.dataset.id_incidencia = incidencia.id;

            let accion = "";

            if (incidencia.estado !== "Resuelta") {
                accion = `
                    <button type="button" class="btn_solucionar btn_tabla" data-id="${incidencia.id}">
                        Solucionar
                    </button>
                `;
            } else {
                accion = `
                    <span>Resuelta</span>
                `;
            }

            fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${incidencia.usuario}</td>
                <td>${incidencia.tipo}</td>
                <td>${incidencia.estado}</td>
                <td>${accion}</td>
            `;

            contenedor_incidencias.appendChild(fila);
        });

        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(incidencias_recibidas.length / filas_por_pagina);

        btn_retroceder.disabled = pagina_actual === 1;

        btn_avanzar.disabled = pagina_actual >= total_paginas;
    }

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarIncidencias();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(incidencias_recibidas.length / filas_por_pagina);

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarIncidencias();
        }
    });

    async function incidencia_recibida() {
        try {
            const formulario = new FormData();
            formulario.append("tipo_incidencia", tipo_incidencia);
            formulario.append("turno_laboral", turno_laboral);

            const respuesta = await fetch("/incidencias/incidencias_recibidos_vigilantes/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            if (!resultado.estado) {
                return;
            }

            incidencias_recibidas = resultado.incidencias;

            pagina_actual = 1;
            mostrarIncidencias();
        } catch (error) {
            console.error(error);
        }
    }
    incidencia_recibida();

    contenedor_incidencias.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");

        const incidencia = fila.dataset.id_incidencia;

        try {
            const formulario = new FormData();
            formulario.append("id_incidencia", incidencia);

            const respuesta = await fetch("/incidencias/buscar_incidencia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            input_titulo_v.value = resultado.incidencia.titulo;
            input_tipo_incidencia_v.value = resultado.incidencia.tipo;
            textarea_descripcion_incidencia_v.value = resultado.incidencia.descripcion;
            input_fecha_incidencia_v.value = resultado.incidencia.fecha_hora;

            input_estado_v.value = resultado.incidencia.estado;
            input_solucion_v.value = resultado.incidencia.solucion;
            input_fecha_resolucion_v.value = resultado.incidencia.solucion;

            select_estado_incidencia.innerHTML = "";

            const estado_actual = resultado.incidencia.estado;

            const opciones_estado = {
                "Pendiente": ["Aceptada", "En proceso", "Resuelta"],
                "Modificada": ["Aceptada", "En proceso", "Resuelta"],
                "Aceptada": ["En proceso", "Resuelta"],
                "En proceso": ["Resuelta"],
                "Resuelta": []
            };

            select_estado_incidencia.innerHTML = "<option value=''>Selecciona un estado</option>";

            const estados_disponibles = opciones_estado[estado_actual] || [];

            estados_disponibles.forEach((estado) => {
                const option_estado = document.createElement("option");
                option_estado.value = estado;
                option_estado.textContent = estado;
                select_estado_incidencia.append(option_estado);
            });

            input_id_incidencia.value = resultado.incidencia.id_incidencia;

            if (e.target.closest(".btn_solucionar")) {
                dialogo_solucion.showModal();
            } else {
                dialogo_incidencia.showModal();
            }
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar_solucion.addEventListener("click", () => {
        dialogo_solucion.close();
    });

    btn_cerrar_incidencia.addEventListener("click", () => {
        dialogo_incidencia.close();
    });

    formulario_solucion.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_solucion);

            const respuesta = await fetch("/incidencias/registrar_solucion/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_solucion.close();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (resultado.estado == "exito") {
                contador_solucion_incidencia.textContent = "0";
                formulario_solucion.reset();
                await incidencia_recibida();
            }
        } catch (error) {
            console.error(error);
        }
    });

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    textarea_solucion_incidencia.addEventListener("input", () => {
        soloTexto(textarea_solucion_incidencia);

        textarea_solucion_incidencia.value = textarea_solucion_incidencia.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g, "");

        contador_solucion_incidencia.textContent = textarea_solucion_incidencia.value.length;
    });
});