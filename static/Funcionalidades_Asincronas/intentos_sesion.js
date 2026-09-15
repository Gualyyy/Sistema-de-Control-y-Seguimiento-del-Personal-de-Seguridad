document.addEventListener("DOMContentLoaded", () => {

    const select_fechas = document.getElementById("fechas_registradas");
    const btn_intentos_sesion_pdf = document.getElementById("intentos_sesion_pdf");
    const contenedor_intentos_sesion = document.getElementById("contenedor_intentos_sesion");

    const btn_avanzar_intentos = document.querySelector(".btn_avanzar");
    const btn_retroceder_intentos = document.querySelector(".btn_retroceder");

    let fecha = "";

    const FILAS_POR_PAGINA_INTENTOS = 10;

    let registros_intentos = [];
    let pagina_actual_intentos = 1;

    async function fechas_registradas() {
        try {
            const respuesta = await fetch("/fechas_intentos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_fechas.innerHTML = "<option value='' selected>Seleccione la fecha</option>";

            resultado.fechas.forEach(fecha => {
                const option = document.createElement("option");
                option.value = fecha;
                option.textContent = fecha;
                select_fechas.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    fechas_registradas();

    select_fechas.addEventListener("change", async () => {
        fecha = select_fechas.value;

        await intentos_registrados();
    });

    function mostrar_intentos() {
        contenedor_intentos_sesion.innerHTML = "";

        const inicio = (pagina_actual_intentos - 1) * FILAS_POR_PAGINA_INTENTOS;

        const fin = inicio + FILAS_POR_PAGINA_INTENTOS;

        const registros = registros_intentos.slice(inicio, fin);

        registros.forEach((intento, indice) => {
            const fila = document.createElement("tr");
            fila.innerHTML = `
                <td>${inicio + indice + 1}</td>
                <td>${intento.usuario}</td>
                <td>${intento.nombre_usuario}</td>
                <td>${intento.direccion_ip}</td>
                <td>${intento.exitoso ? "Exitoso" : "Fallido"}</td>
                <td>${intento.fecha_hora}</td>
            `;

            contenedor_intentos_sesion.appendChild(fila);
        });

        const total_paginas = Math.ceil(registros_intentos.length / FILAS_POR_PAGINA_INTENTOS);

        btn_retroceder_intentos.disabled = pagina_actual_intentos <= 1;
        btn_avanzar_intentos.disabled = pagina_actual_intentos >= total_paginas;
    }

    btn_avanzar_intentos.addEventListener("click", () => {
        const total_paginas = Math.ceil(registros_intentos.length / FILAS_POR_PAGINA_INTENTOS);

        if (pagina_actual_intentos < total_paginas) {
            pagina_actual_intentos++;
            mostrar_intentos();
        }
    });

    btn_retroceder_intentos.addEventListener("click", () => {
        if (pagina_actual_intentos > 1) {
            pagina_actual_intentos--;
            mostrar_intentos();
        }
    });

    async function intentos_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("fecha", fecha);

            const respuesta = await fetch("/intentos_registrados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            registros_intentos = resultado.intentos;
            pagina_actual_intentos = 1;
            mostrar_intentos();
        } catch (error) {
            console.error(error);
        }
    }
    intentos_registrados();

    btn_intentos_sesion_pdf.addEventListener("click", () => {
        const formulario = document.createElement("form");

        formulario.method = "POST";
        formulario.action = "/lista_intentos_sesion_pdf/";
        formulario.target = "_blank";

        const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const fechas = document.querySelector("#fechas_registradas").value;

        formulario.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">

            <input type="hidden" name="fechas" value="${fechas}">
        `;

        document.body.appendChild(formulario);
        formulario.submit();
        formulario.remove();
    });
});