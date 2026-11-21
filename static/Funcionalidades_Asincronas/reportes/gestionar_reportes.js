document.addEventListener("DOMContentLoaded", () => {

    const formularios = document.querySelectorAll("[data-reporte-form]");

    function inicializarFiltroCedula(idCampo, idSelect) {
        const campo = document.getElementById(idCampo);
        const selectNacionalidad = document.getElementById(idSelect);

        if (!campo || !selectNacionalidad) {
            return;
        }

        configurarCedula(campo, selectNacionalidad);
        selectNacionalidad.value = "";
        selectNacionalidad.dispatchEvent(
            new Event("change", { bubbles: true })
        );
    }

    inicializarFiltroCedula("bitacora_cedula", "bitacora_nacionalidad");
    inicializarFiltroCedula(
        "reporte_cedula_asignaciones",
        "reporte_nacionalidad_asignaciones"
    );


    // MOSTRAR RESPUESTAS DE ERROR
    async function mostrarRespuestaError(respuesta, tituloPorDefecto) {

        let resultado;

        try {
            resultado = await respuesta.json();

        } catch (error) {

            throw new Error(
                "El servidor devolvió una respuesta no válida."
            );
        }

        await Swal.fire({
            title: resultado.title || tituloPorDefecto,
            text: resultado.descripcion || (
                "No fue posible procesar el reporte."
            ),
            icon: resultado.icon || "error",
            confirmButtonColor: "#00445F"
        });
    }


    // CARGAR OPCIONES DE LOS FILTROS
    async function cargarOpciones(select) {

        const opcionInicial = document.createElement("option");

        opcionInicial.value = "";

        opcionInicial.textContent =
            select.dataset.placeholder || "Selecciona una opción";

        select.append(opcionInicial);

        try {

            const respuesta = await fetch(select.dataset.optionsUrl);

            if (!respuesta.ok) {
                throw new Error(`Error HTTP ${respuesta.status}`);
            }

            const resultado = await respuesta.json();

            if (resultado.estado === "fallo") {
                throw new Error(
                    resultado.descripcion || "No se pudieron cargar las opciones."
                );
            }

            const opciones = select.dataset.optionsKey
                ? resultado[select.dataset.optionsKey]
                : resultado;

            if (!Array.isArray(opciones)) {
                throw new Error("La respuesta de opciones no es válida.");
            }

            opciones
                .filter(opcion => (
                    select.dataset.activeOnly !== "true" || opcion.activo
                ))
                .forEach(opcion => {

                    const elemento = document.createElement("option");

                    elemento.value = opcion[select.dataset.optionValue];

                    elemento.textContent = opcion[select.dataset.optionLabel];

                    select.append(elemento);
                });

        } catch (error) {

            console.error(
                "No se pudieron cargar las opciones del reporte.",
                error
            );

            opcionInicial.textContent = "No se pudieron cargar las opciones";

            select.disabled = true;

            await Swal.fire({
                title: "Error al cargar filtros",
                text: "No se pudieron cargar las opciones de un reporte.",
                icon: "error",
                confirmButtonColor: "#00445F"
            });
        }
    }


    // INICIALIZAR FILTROS DINÁMICOS
    document
        .querySelectorAll("[data-options-url]")
        .forEach(select => cargarOpciones(select));


    // PROCESAR FORMULARIOS DE REPORTES
    formularios.forEach(formulario => {

        formulario.addEventListener("submit", async evento => {

            evento.preventDefault();


            // VALIDAR PAREJAS DE CAMPOS
            const parejaCampos = formulario.dataset.pairFields;

            if (parejaCampos) {

                const [primero, segundo] = parejaCampos.split(",");

                const valorPrimero = formulario.elements[primero].value.trim();

                const valorSegundo = formulario.elements[segundo].value.trim();

                if (Boolean(valorPrimero) !== Boolean(valorSegundo)) {

                    await Swal.fire({
                        title: "Filtro incompleto",
                        text: "Completa ambos campos del filtro o déjalos vacíos.",
                        icon: "warning",
                        confirmButtonColor: "#00445F"
                    });

                    return;
                }
            }


            // VALIDAR TOKEN CSRF
            const tokenCSRF = formulario.querySelector(
                "[name=csrfmiddlewaretoken]"
            )?.value;

            if (!tokenCSRF) {

                await Swal.fire({
                    title: "Solicitud no válida",
                    text: "No se encontró el token de seguridad del formulario.",
                    icon: "error",
                    confirmButtonColor: "#00445F"
                });

                return;
            }


            const boton = formulario.querySelector("[type=submit]");

            let pestana = null;

            if (boton) {
                boton.disabled = true;
            }


            // ENVIAR SOLICITUD
            const enviarSolicitud = confirmar => {

                const datos = new FormData(formulario);

                if (formulario.dataset.confirmable === "true") {

                    datos.set(
                        "confirmar",
                        confirmar ? "true" : "false"
                    );
                }

                return fetch(formulario.dataset.endpoint, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": tokenCSRF
                    },
                    body: datos
                });
            };


            try {

                // PRIMERA PETICIÓN
                const requiereConfirmacion =
                    formulario.dataset.confirmable === "true";

                let respuesta = await enviarSolicitud(false);


                // VALIDAR RESPUESTA DEL SERVIDOR
                if (!respuesta.ok) {

                    await mostrarRespuestaError(
                        respuesta,
                        "No se pudo generar el reporte"
                    );

                    return;
                }


                let tipoRespuesta = respuesta.headers.get(
                    "content-type"
                ) || "";


                // PROCESAR CONFIRMACIÓN
                if (!tipoRespuesta.includes("application/pdf")) {

                    let resultado;

                    try {

                        resultado = await respuesta.json();

                    } catch (error) {

                        throw new Error(
                            "El servidor devolvió una respuesta no válida."
                        );
                    }


                    // VALIDAR RESPUESTA DE CONFIRMACIÓN
                    if (
                        resultado.estado !== "confirmacion" ||
                        !requiereConfirmacion
                    ) {

                        await Swal.fire({
                            title: resultado.title || "Reporte no disponible",
                            text: resultado.descripcion || (
                                "El servidor no devolvió un documento PDF."
                            ),
                            icon: resultado.icon || "warning",
                            confirmButtonColor: "#00445F"
                        });

                        return;
                    }


                    // MOSTRAR ADVERTENCIA
                    const confirmacion = await Swal.fire({
                        title: resultado.title,
                        text: resultado.descripcion,
                        icon: "warning",
                        showCancelButton: true,
                        confirmButtonText: "Sí, generar PDF",
                        cancelButtonText: "Cancelar",
                        confirmButtonColor: "#00445F",
                        cancelButtonColor: "#6c757d",
                        reverseButtons: true
                    });


                    // CANCELAR GENERACIÓN
                    if (!confirmacion.isConfirmed) {
                        return;
                    }


                    // SEGUNDA PETICIÓN: GENERAR PDF
                    respuesta = await enviarSolicitud(true);


                    if (!respuesta.ok) {

                        await mostrarRespuestaError(
                            respuesta,
                            "No se pudo generar el reporte"
                        );

                        return;
                    }


                    tipoRespuesta = respuesta.headers.get(
                        "content-type"
                    ) || "";
                }


                // VALIDAR TIPO DE DOCUMENTO
                if (!tipoRespuesta.includes("application/pdf")) {

                    throw new Error(
                        "La respuesta no contiene un documento PDF."
                    );
                }


                // OBTENER ARCHIVO
                const archivo = await respuesta.blob();


                // IMPEDIR MOSTRAR PDF VACÍO
                if (!archivo.size) {

                    await Swal.fire({
                        title: "Reporte vacío",
                        text: "El documento PDF no contiene información para visualizar.",
                        icon: "warning",
                        confirmButtonColor: "#00445F"
                    });

                    return;
                }


                // VALIDAR QUE SEA UN PDF
                const primerosBytes = new Uint8Array(
                    await archivo.slice(0, 5).arrayBuffer()
                );

                const firmaPDF = String.fromCharCode(...primerosBytes);

                if (firmaPDF !== "%PDF-") {

                    throw new Error(
                        "El archivo recibido no es un documento PDF válido."
                    );
                }


                // CREAR URL DEL DOCUMENTO
                const url = URL.createObjectURL(archivo);


                // ABRIR PESTAÑA SOLAMENTE CON PDF VÁLIDO
                pestana = window.open("about:blank", "_blank");

                if (pestana) {

                    pestana.location.href = url;

                } else {

                    window.open(url, "_blank");
                }


                // LIBERAR RECURSOS
                setTimeout(() => {
                    URL.revokeObjectURL(url);
                }, 60000);


            } catch (error) {

                pestana?.close();

                console.error(
                    "Error al generar el reporte PDF.",
                    error
                );

                await Swal.fire({
                    title: "Error al generar reporte",
                    text: error.message || (
                        "No fue posible visualizar el documento PDF."
                    ),
                    icon: "error",
                    confirmButtonColor: "#00445F"
                });

            } finally {

                if (boton) {
                    boton.disabled = false;
                }
            }

        });

    });

});
