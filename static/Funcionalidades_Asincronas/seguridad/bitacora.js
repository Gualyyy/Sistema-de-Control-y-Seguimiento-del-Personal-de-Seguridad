document.addEventListener("DOMContentLoaded", () => {

    const contenedor_bitacora = document.getElementById("contenedor_bitacora");
    const bitacora_pdf = document.getElementById("bitacora_pdf");
    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const select_nacionalidad = document.getElementById("nacionalidad");

    const btn_avanzar = document.querySelector(".btn_avanzar");
    const btn_retroceder = document.querySelector(".btn_retroceder");

    configurarCedula(input_cedula_identidad, select_nacionalidad);

    const FILAS_POR_PAGINA = 10;

    let cedula = "", nacionalidad = "";
    let registros_bitacora = [];
    let pagina_actual = 1;

    input_cedula_identidad.addEventListener("input", () => {
        cedula = input_cedula_identidad.value.trim();

        bitacora_registrados();
    });

    select_nacionalidad.addEventListener("change", () => {
        nacionalidad = select_nacionalidad.value;

        bitacora_registrados();
    });

    function mostrar_bitacora() {
        contenedor_bitacora.innerHTML = "";

        const inicio = (pagina_actual - 1) * FILAS_POR_PAGINA;
        const fin = inicio + FILAS_POR_PAGINA;

        const registros = registros_bitacora.slice(inicio, fin);


        registros.forEach((registro, indice) => {
            const fila = document.createElement("tr");

            fila.innerHTML = `
                <td>${inicio + indice + 1}</td>
                <td>${registro.usuario}</td>
                <td>${registro.cedula}</td>
                <td>${registro.fecha}</td>
                <td>${registro.accion}</td>
            `;
            contenedor_bitacora.appendChild(fila);
        });

        const total_paginas = Math.ceil(registros_bitacora.length / FILAS_POR_PAGINA);

        btn_retroceder.disabled = pagina_actual <= 1;
        btn_avanzar.disabled = pagina_actual >= total_paginas;
    }


    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(registros_bitacora.length / FILAS_POR_PAGINA);

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_bitacora();
        }
    });

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_bitacora();
        }
    });

    async function bitacora_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("cedula", cedula);
            formulario.append("nacionalidad", nacionalidad);

            const respuesta = await fetch("/bitacora_registradas/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            registros_bitacora = resultado;
            pagina_actual = 1;
            mostrar_bitacora();
        } catch (error) {
            console.error(error);
        }
    }
    bitacora_registrados();

    bitacora_pdf.addEventListener("click", async () => {
        const nacionalidad = select_nacionalidad.value;
        const cedula = input_cedula_identidad.value.trim();

        if (nacionalidad === "" && cedula !== "") {
            Swal.fire({
                icon: "warning",
                title: "Nacionalidad requerida",
                text: "Debe seleccionar una nacionalidad."
            });
            return;
        }

        if (cedula === "" && nacionalidad !== "") {
            Swal.fire({
                icon: "warning",
                title: "Cédula requerida",
                text: "Debe ingresar una cédula."
            });
            return;
        }

        if ((nacionalidad === "V" && (cedula.length < 7 || cedula.length > 8)) ||
            (nacionalidad === "E" && (cedula.length < 8 || cedula.length > 10))) {
            Swal.fire({
                icon: "warning",
                title: "Longitud no válida",
                text: nacionalidad === "V"
                    ? "La cédula debe tener entre 7 y 8 números."
                    : "El documento debe tener entre 8 y 10 números."
            });
            return;
        }

        try {
            const formulario = new FormData();

            formulario.append("nacionalidad", nacionalidad);
            formulario.append("cedula", cedula);

            const csrf = document.querySelector(
                "[name=csrfmiddlewaretoken]"
            ).value;

            const respuesta = await fetch("/lista_bitacora_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf
                },
                body: formulario
            });

            const tipoContenido = respuesta.headers.get("content-type") || "";

            if (tipoContenido.includes("application/json")) {
                const resultado = await respuesta.json();

                await Swal.fire({
                    icon: resultado.icon || "warning",
                    title: resultado.title || "Sin registros",
                    text: resultado.descripcion ||
                        "No hay registros para generar el reporte.",
                    confirmButtonText: "Entendido",
                    confirmButtonColor: "#00445F"
                });

                return;
            }

            if (!respuesta.ok) {
                throw new Error("No se pudo generar el reporte PDF.");
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);

            const ventana = window.open(url, "_blank");

            if (!ventana) {
                URL.revokeObjectURL(url);

                await Swal.fire({
                    icon: "warning",
                    title: "Ventana bloqueada",
                    text: "Permita las ventanas emergentes para visualizar el reporte PDF."
                });
                return;
            }

            ventana.addEventListener("beforeunload", () => {
                URL.revokeObjectURL(url);
            }, { once: true });

        } catch (error) {
            console.error(error);

        }
    });
});