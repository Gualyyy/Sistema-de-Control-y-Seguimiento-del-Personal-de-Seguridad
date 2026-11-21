document.addEventListener("DOMContentLoaded", () => {
    const formulario_validar = document.getElementById("formulario_validar");
    const btn_reenviar = document.getElementById("btn_reenviar");
    const btn_validar = document.getElementById("btn_validar");
    const contador_codigo = document.getElementById("vigencia_codigo");

    const dialogo_correos_usuario = document.getElementById("correos_usuario");
    const formulario_seleccion = document.getElementById("formulario_seleccion");

    const input_radius_correo_principal = document.getElementById("correo_principal");
    const label_nombre_principal = document.getElementById("nombre_principal");

    const input_radius_correo_secundario = document.getElementById("correo_secundario");
    const label_nombre_secundario = document.getElementById("nombre_secundario");

    let intervalo_vigencia_codigo = null;
    let consulta_vigencia_en_curso = false;
    let reenvio_en_curso = false;
    let usuario_bloqueado = false;
    let bloqueo_temporal_codigo = false;

    function formatear_tiempo(segundos) {
        const minutos = Math.floor(segundos / 60);
        const segundos_restantes = segundos % 60;

        return `${String(minutos).padStart(2, "0")}:${String(segundos_restantes).padStart(2, "0")}`;
    }

    function detener_contador() {
        if (intervalo_vigencia_codigo !== null) {
            clearInterval(intervalo_vigencia_codigo);
            intervalo_vigencia_codigo = null;
        }
    }

    function bloquear_contador() {
        usuario_bloqueado = true;
        bloqueo_temporal_codigo = false;

        detener_contador();

        if (contador_codigo) {
            contador_codigo.hidden = false;
            contador_codigo.textContent = "Cuenta inhabilitada. No es posible continuar.";
        }

        if (btn_reenviar) {
            btn_reenviar.disabled = true;
        }

        if (btn_validar) {
            btn_validar.disabled = true;
        }
    }


    function iniciar_contador(segundos, bloqueado = false) {
        detener_contador();

        if (usuario_bloqueado) {
            bloquear_contador();
            return;
        }

        let restantes = Math.max(0, Math.floor(segundos));
        bloqueo_temporal_codigo = bloqueado;

        if (contador_codigo) {
            contador_codigo.hidden = false;
        }

        if (restantes <= 0) {
            if (contador_codigo) {
                contador_codigo.textContent = bloqueado
                    ? "El bloqueo ha finalizado. Puede solicitar un nuevo código."
                    : "Código expirado. Solicite uno nuevo.";
            }

            if (btn_reenviar) {
                btn_reenviar.disabled = usuario_bloqueado;
            }

            if (btn_validar) {
                btn_validar.disabled = true;
            }

            bloqueo_temporal_codigo = false;
            return;
        }

        if (btn_reenviar) {
            btn_reenviar.disabled = true;
        }

        if (btn_validar) {
            btn_validar.disabled = bloqueado;
        }

        if (contador_codigo) {
            contador_codigo.textContent = bloqueado
                ? `Código bloqueado. Debe esperar ${formatear_tiempo(restantes)} para solicitar otro.`
                : `Código vigente: ${formatear_tiempo(restantes)}`;
        }

        intervalo_vigencia_codigo = setInterval(() => {
            if (usuario_bloqueado) {
                bloquear_contador();
                return;
            }

            restantes--;

            if (restantes <= 0) {
                detener_contador();

                if (contador_codigo) {
                    contador_codigo.textContent = bloqueo_temporal_codigo
                        ? "El bloqueo ha finalizado. Puede solicitar un nuevo código."
                        : "Código expirado. Solicite uno nuevo.";
                }

                if (btn_reenviar) {
                    btn_reenviar.disabled = false;
                }

                if (btn_validar) {
                    btn_validar.disabled = true;
                }

                bloqueo_temporal_codigo = false;
                return;
            }

            if (contador_codigo) {
                contador_codigo.textContent = bloqueo_temporal_codigo
                    ? `Código bloqueado. Debe esperar ${formatear_tiempo(restantes)} para solicitar otro.`
                    : `Código vigente: ${formatear_tiempo(restantes)}`;
            }
        }, 1000);
    }


    async function vigencia_codigo() {
        if (consulta_vigencia_en_curso) {
            return;
        }

        consulta_vigencia_en_curso = true;

        try {
            const respuesta = await fetch("/vigencia_codigo/", {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                },
                cache: "no-store"
            });

            const resultado = await respuesta.json();

            if (resultado.bloqueado === true) {
                if (resultado.bloqueo_permanente === true) {
                    bloquear_contador();
                } else {
                    iniciar_contador(
                        Number(resultado.segundos_restantes),
                        true
                    );
                }
                return;
            }

            if (usuario_bloqueado) {
                bloquear_contador();
                return;
            }

            if (contador_codigo) {
                contador_codigo.hidden = false;
            }

            if (!respuesta.ok || resultado.estado !== "exito") {
                detener_contador();
                bloqueo_temporal_codigo = false;

                if (contador_codigo) {
                    const codigo_expirado =
                        Number(resultado.segundos_restantes) === 0;
                    contador_codigo.textContent = codigo_expirado
                        ? "Código expirado. Solicite uno nuevo."
                        : resultado.descripcion || "No se pudo verificar la vigencia.";
                }

                if (btn_reenviar) {
                    btn_reenviar.disabled = false;
                }

                if (btn_validar) {
                    btn_validar.disabled =
                        Number(resultado.segundos_restantes) === 0;
                }

                return;
            }

            const segundos = Number(resultado.segundos_restantes);

            if (!Number.isFinite(segundos) || segundos <= 0) {
                detener_contador();

                if (contador_codigo) {
                    contador_codigo.textContent = "Código expirado";
                }

                if (btn_reenviar) {
                    btn_reenviar.disabled = false;
                }

                if (btn_validar) {
                    btn_validar.disabled = true;
                }

                return;
            }

            iniciar_contador(segundos);

        } catch (error) {
            console.error(error);

            if (usuario_bloqueado) {
                bloquear_contador();
                return;
            }

            if (contador_codigo && intervalo_vigencia_codigo === null) {
                contador_codigo.hidden = false;
                contador_codigo.textContent =
                    "No se pudo verificar la vigencia.";
            }

            if (btn_reenviar && intervalo_vigencia_codigo === null) {
                btn_reenviar.disabled = false;
            }

        } finally {
            consulta_vigencia_en_curso = false;
        }
    }

    if (btn_reenviar) {
        btn_reenviar.disabled = usuario_bloqueado;
    }

    async function correos_usuario() {
        try {
            const respuesta = await fetch("/correos_usuario/", {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                },
                cache: "no-store"
            });

            const resultado = await respuesta.json();

            if (!respuesta.ok || resultado.estado !== "exito") {
                mostrar_mensaje_dialogo(
                    "contenedor_mensajes_seleccion",
                    resultado.notificacion || "No se pudieron consultar los correos.",
                    resultado.tipo || "error"
                );

                return false;
            }

            if (input_radius_correo_principal) {
                input_radius_correo_principal.value =
                    resultado.correo_principal || "";

                input_radius_correo_principal.checked = false;
                input_radius_correo_principal.disabled =
                    !resultado.correo_principal;
            }

            if (label_nombre_principal) {
                label_nombre_principal.textContent =
                    resultado.correo_principal || "Correo principal no disponible";
            }

            if (input_radius_correo_secundario) {
                input_radius_correo_secundario.disabled = true;
                input_radius_correo_secundario.checked = false;
                input_radius_correo_secundario.value = "";
            }

            if (label_nombre_secundario) {
                label_nombre_secundario.textContent =
                    "Correo secundario no disponible";
            }

            const correo_secundario = resultado.correo_secundario?.trim();

            if (correo_secundario && correo_secundario !== "N/A") {
                if (input_radius_correo_secundario) {
                    input_radius_correo_secundario.value = correo_secundario;
                    input_radius_correo_secundario.disabled = false;
                }

                if (label_nombre_secundario) {
                    label_nombre_secundario.textContent = correo_secundario;
                }
            }

            ocultar_mensaje_dialogo("contenedor_mensajes_seleccion");

            return true;

        } catch (error) {
            console.error(error);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_seleccion",
                "Ocurrió un error al consultar los correos electrónicos.",
                "error"
            );

            return false;
        }
    }

    if (btn_reenviar) {
        btn_reenviar.disabled = true;

        btn_reenviar.addEventListener("click", () => {
            if (
                !dialogo_correos_usuario ||
                !dialogo_correos_usuario.showModal
            ) {
                return;
            }

            if (!dialogo_correos_usuario.open) {
                dialogo_correos_usuario.showModal();
            }
        });
    }

    if (contador_codigo) {
        vigencia_codigo();
    }

    correos_usuario();

    if (formulario_seleccion) {
        formulario_seleccion.addEventListener("submit", async (e) => {
            e.preventDefault();

            if (reenvio_en_curso) {
                return;
            }

            reenvio_en_curso = true;

            const boton_submit = formulario_seleccion.querySelector(
                '[type="submit"]'
            );

            try {
                mostrar_mensaje_dialogo(
                    "contenedor_mensajes_seleccion",
                    "Reenviando código de verificación...",
                    "cargando"
                );

                const formulario = new FormData(formulario_seleccion);

                const token = formulario_seleccion.querySelector(
                    '[name="csrfmiddlewaretoken"]'
                )?.value;

                const respuesta = await fetch("/reenviar_codigo/", {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        ...(token ? { "X-CSRFToken": token } : {})
                    },
                    body: formulario
                });

                const resultado = await respuesta.json();

                if (!respuesta.ok || resultado.estado !== "exito") {
                    mostrar_mensaje_dialogo(
                        "contenedor_mensajes_seleccion",
                        resultado.notificacion || "No fue posible reenviar el código.",
                        resultado.tipo || "error"
                    );

                    return;
                }

                if (
                    dialogo_correos_usuario &&
                    dialogo_correos_usuario.open
                ) {
                    await mostrar_mensaje_temporal(
                        "contenedor_mensajes_seleccion",
                        resultado.notificacion || "El código se ha reenviado correctamente.",
                        resultado.tipo || "exito",
                        3
                    );

                    dialogo_correos_usuario.close();
                }

                detener_contador();

                if (contador_codigo) {
                    contador_codigo.textContent = "Actualizando vigencia...";
                }

                await vigencia_codigo();

            } catch (error) {
                console.error(error);

                mostrar_mensaje_dialogo(
                    "contenedor_mensajes_seleccion",
                    "No fue posible reenviar el código. Inténtelo nuevamente.",
                    "error"
                );

            } finally {
                reenvio_en_curso = false;

                if (boton_submit) {
                    boton_submit.disabled = false;
                }
            }
        });
    }

    if (formulario_validar) {
        formulario_validar.addEventListener("submit", async (e) => {
            e.preventDefault();

            if (usuario_bloqueado || bloqueo_temporal_codigo) {
                return;
            }

            const boton_submit = document.getElementById("btn_validar");

            if (boton_submit) {
                boton_submit.disabled = true;
            }

            try {
                const formulario = new FormData(formulario_validar);

                const respuesta = await fetch("/verificar_codigo/", {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: formulario
                });

                let resultado;

                try {
                    resultado = await respuesta.json();
                } catch {
                    throw new Error("El servidor no devolvió una respuesta JSON válida.");
                }

                if (resultado.bloqueado === true) {
                    if (resultado.bloqueo_permanente === true) {
                        bloquear_contador();
                    } else {
                        iniciar_contador(
                            Number(resultado.segundos_restantes) || 300,
                            true
                        );
                    }
                }

                await Swal.fire({
                    title: resultado.title || "Verificación de código",
                    text: resultado.descripcion || "No se pudo completar la solicitud.",
                    icon: resultado.icon || "warning"
                });

                if (resultado.estado === "exito" && resultado.url) {
                    window.vigilanciaReemplazar(resultado.url);
                    return;
                }

                if (resultado.bloqueado !== true) {
                    formulario_validar.reset();
                }

            } catch (error) {
                console.error("Error al verificar el código:", error);

                await Swal.fire({
                    title: "Error de conexión",
                    text: "No fue posible procesar la respuesta del servidor. Intente nuevamente.",
                    icon: "error"
                });

            } finally {
                if (boton_submit) {
                    boton_submit.disabled =
                        usuario_bloqueado || bloqueo_temporal_codigo;
                }
            }
        });
    }
    // FUNCIONES NOTIFICACIONES

    function mostrar_mensaje_dialogo(id_contenedor, mensaje, tipo = "informacion") {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.className = `contenedor_mensajes ${tipo}`;
        contenedor.replaceChildren();

        const reloj = document.createElement("i");
        reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
        reloj.setAttribute("aria-hidden", "true");

        const texto = document.createElement("span");
        texto.textContent = mensaje;

        contenedor.append(reloj, texto);
        contenedor.hidden = false;
    }

    function mostrar_mensaje_temporal(id_contenedor, mensaje, tipo = "exito", segundos = 4) {
        return new Promise((resolve) => {
            const contenedor = document.getElementById(id_contenedor);

            if (!contenedor) {
                resolve();
                return;
            }

            contenedor.className = `contenedor_mensajes ${tipo}`;
            contenedor.replaceChildren();

            const reloj = document.createElement("i");
            reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
            reloj.setAttribute("aria-hidden", "true");

            const texto = document.createElement("span");
            texto.textContent = mensaje;

            const contador = document.createElement("span");
            contador.className = "contador_notificacion";
            contador.setAttribute("aria-live", "off");

            contenedor.append(reloj, texto, contador);
            contenedor.hidden = false;

            let restante = segundos;
            contador.textContent = ` ${restante} s`;

            const intervalo = setInterval(() => {
                restante--;

                if (restante <= 0) {
                    clearInterval(intervalo);
                    ocultar_mensaje_dialogo(id_contenedor);
                    resolve();
                    return;
                }

                contador.textContent = ` ${restante} s`;
            }, 1000);
        });
    }

    function ocultar_mensaje_dialogo(id_contenedor) {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.hidden = true;
        contenedor.replaceChildren();
    }
});