
document.addEventListener("DOMContentLoaded", () => {

    const areaMensajes = document.getElementById("area_mensajes");
    const mensajeChat = document.getElementById("mensaje_chat");
    const btnEnviar = document.getElementById("btn_enviar_mensaje");
    const btnEmojis = document.getElementById("btn_emojis");
    const contenedorEmojis = document.getElementById("contenedor_emojis");
    const contenedorChat = document.getElementById("contenedor_chat");

    if (
        !areaMensajes ||
        !mensajeChat ||
        !btnEnviar ||
        !btnEmojis ||
        !contenedorEmojis ||
        !contenedorChat
    ) {
        return;
    }

    const idConversacion = contenedorChat.dataset.id_conversacion;
    const idUsuario = Number(contenedorChat.dataset.id_usuario);
    const urlMensajes = contenedorChat.dataset.urlMensajes;

    if (
        !/^\d+$/.test(idConversacion || "") ||
        !Number.isSafeInteger(idUsuario) ||
        idUsuario <= 0 ||
        !urlMensajes
    ) {
        console.error("Faltan datos válidos para iniciar el chat.");
        return;
    }



    const selectorEmojis = contenedorEmojis.querySelector("emoji-picker");

    let socket = null;
    let temporizadorReconectar = null;
    let temporizadorEscritura = null;
    let escrituraActiva = false;
    let reconexionManual = false;

    const mensajesDOM = new Map();

    // --------------------------------------------------
    // HORA
    // --------------------------------------------------

    function obtenerHora(fecha) {

        return new Intl.DateTimeFormat("es-VE", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: true
        }).format(new Date(fecha));

    }

    // --------------------------------------------------
    // DESPLAZAMIENTO
    // --------------------------------------------------

    function desplazarAlFinal() {

        areaMensajes.scrollTop = areaMensajes.scrollHeight;

    }

    // --------------------------------------------------
    // AJUSTAR TEXTAREA
    // --------------------------------------------------

    function ajustarTextarea() {

        mensajeChat.style.height = "auto";

        mensajeChat.style.height =
            Math.min(mensajeChat.scrollHeight, 110) + "px";

    }

    // --------------------------------------------------
    // CONEXIÓN WEBSOCKET
    // --------------------------------------------------

    function conectarWebSocket() {

        const protocolo = location.protocol === "https:" ? "wss:" : "ws:";

        socket = new WebSocket(
            `${protocolo}//${location.host}/ws/chat/${idConversacion}/`
        );

        socket.addEventListener("open", () => {

            console.log("WebSocket conectado.");

            if (!document.hidden) {
                marcarMensajesLeidos();
            }

        });

        socket.addEventListener("message", (evento) => {

            const data = JSON.parse(evento.data);

            switch (data.evento) {

                case "conexion_establecida":

                    console.log("Conexión establecida con el chat.");

                    break;

                case "nuevo_mensaje":

                    mostrarMensaje(data.mensaje);

                    if (
                        data.mensaje.id_remitente !== idUsuario &&
                        !document.hidden
                    ) {
                        marcarMensajesLeidos();
                    }

                    break;

                case "actualizar_estado":

                    actualizarEstadoMensajes(data);

                    break;

                case "escribiendo":

                    mostrarEscritura(
                        data.id_usuario,
                        data.escribiendo
                    );

                    break;

                case "error":

                    console.error(data.descripcion);

                    break;

            }

        });

        socket.addEventListener("close", (evento) => {

            console.warn("WebSocket desconectado:", evento.code);

            if (evento.code === 4401 || evento.code === 4403) {
                reconexionManual = true;
                console.error("No tienes autorización para acceder al chat.");
                return;
            }

            programarReconectar();

        });

        socket.addEventListener("error", (error) => {

            console.error("Error en WebSocket:", error);

        });

    }

    function programarReconectar() {

        if (reconexionManual || temporizadorReconectar) {
            return;
        }

        temporizadorReconectar = setTimeout(() => {

            temporizadorReconectar = null;

            conectarWebSocket();

        }, 3000);

    }

    // --------------------------------------------------
    // ENVIAR MENSAJE
    // --------------------------------------------------

    function enviarMensaje() {

        const contenido = mensajeChat.value.trim();

        if (!contenido) {
            mensajeChat.focus();
            return;
        }

        if (!socket || socket.readyState !== WebSocket.OPEN) {
            console.warn("No hay conexión con el servidor.");
            return;
        }

        socket.send(JSON.stringify({
            accion: "enviar_mensaje",
            contenido: contenido
        }));

        mensajeChat.value = "";

        ajustarTextarea();

        mensajeChat.focus();

        detenerEscritura();

    }

    btnEnviar.addEventListener("click", enviarMensaje);

    mensajeChat.addEventListener("keydown", (evento) => {

        if (
            evento.key === "Enter" &&
            !evento.shiftKey &&
            !evento.isComposing
        ) {
            evento.preventDefault();
            enviarMensaje();
        }

    });

    // --------------------------------------------------
    // CREAR MENSAJE
    // --------------------------------------------------

    function crearMensaje(data) {

        const mensaje = document.createElement("div");

        const propio = data.id_remitente === idUsuario;

        mensaje.classList.add(
            "mensaje",
            propio ? "mensaje_enviado" : "mensaje_recibido"
        );

        mensaje.dataset.idMensaje = data.id_mensaje;

        const texto = document.createElement("div");

        texto.classList.add("contenido_mensaje");

        texto.textContent = data.eliminado
            ? "Este mensaje fue eliminado."
            : data.contenido;

        const hora = document.createElement("span");

        hora.classList.add("hora_mensaje");

        hora.appendChild(
            document.createTextNode(
                obtenerHora(data.fecha_envio) + " "
            )
        );

        if (propio) {

            const estado = document.createElement("i");

            estado.className = "fa-solid fa-check";

            estado.dataset.estadoMensaje = data.id_mensaje;

            estado.title = "Enviado";

            hora.appendChild(estado);

        }

        mensaje.appendChild(texto);
        mensaje.appendChild(hora);

        return mensaje;

    }

    // --------------------------------------------------
    // MOSTRAR MENSAJE
    // --------------------------------------------------

    function mostrarMensaje(data) {

        if (mensajesDOM.has(data.id_mensaje)) {
            return;
        }

        const mensaje = crearMensaje(data);

        areaMensajes.appendChild(mensaje);

        mensajesDOM.set(data.id_mensaje, mensaje);

        if (data.es_propio || data.id_remitente === idUsuario) {

            actualizarEstadoMensajes({
                accion: data.estado || "ENVIADO",
                mensajes: [data.id_mensaje]
            });

        }

        desplazarAlFinal();

    }

    // --------------------------------------------------
    // ACTUALIZAR ESTADO
    // --------------------------------------------------

    function actualizarEstadoMensajes(data) {

        data.mensajes.forEach(idMensaje => {

            const mensaje = mensajesDOM.get(idMensaje);

            if (!mensaje) {
                return;
            }

            const icono = mensaje.querySelector(
                "[data-estado-mensaje]"
            );

            if (!icono) {
                return;
            }

            const estado = String(data.accion).toUpperCase();

            if (estado === "ENTREGADO") {

                icono.className = "fa-solid fa-check-double";

                icono.style.color = "";

                icono.title = "Entregado";

            } else if (estado === "LEIDO") {

                icono.className = "fa-solid fa-check-double";

                icono.style.color = "#1689d4";

                icono.title = "Leído";

            } else if (estado === "ENVIADO") {

                icono.className = "fa-solid fa-check";

                icono.style.color = "";

                icono.title = "Enviado";

            }

        });

    }

    // --------------------------------------------------
    // CARGAR HISTORIAL
    // --------------------------------------------------

    async function cargarMensajes() {

        try {

            const respuesta = await fetch(
                `${urlMensajes}?id_conversacion=${encodeURIComponent(idConversacion)}`,
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    }
                }
            );

            if (!respuesta.ok) {
                throw new Error("No fue posible obtener los mensajes.");
            }

            const data = await respuesta.json();

            if (data.estado !== "exito") {
                console.error(data.descripcion);
                return;
            }

            areaMensajes.innerHTML = "";

            mensajesDOM.clear();

            data.mensajes.forEach(mensaje => {

                mostrarMensaje(mensaje);

                if (mensaje.es_propio) {

                    actualizarEstadoMensajes({
                        accion: mensaje.estado,
                        mensajes: [mensaje.id_mensaje]
                    });

                }

            });

            desplazarAlFinal();

        } catch (error) {

            console.error("Error al cargar el historial:", error);

        }

    }

    // --------------------------------------------------
    // MARCAR MENSAJES COMO LEÍDOS
    // --------------------------------------------------

    function marcarMensajesLeidos() {

        if (
            document.hidden ||
            !socket ||
            socket.readyState !== WebSocket.OPEN
        ) {
            return;
        }

        socket.send(JSON.stringify({
            accion: "marcar_leidos"
        }));

    }

    document.addEventListener("visibilitychange", () => {

        if (!document.hidden) {
            marcarMensajesLeidos();
        }

    });

    areaMensajes.addEventListener("scroll", () => {

        if (!document.hidden) {
            marcarMensajesLeidos();
        }

    });

    // --------------------------------------------------
    // INDICADOR DE ESCRITURA
    // --------------------------------------------------

    function notificarEscritura() {

        if (
            !socket ||
            socket.readyState !== WebSocket.OPEN
        ) {
            return;
        }

        if (!escrituraActiva) {

            escrituraActiva = true;

            socket.send(JSON.stringify({
                accion: "escribiendo"
            }));

        }

        clearTimeout(temporizadorEscritura);

        temporizadorEscritura = setTimeout(() => {

            detenerEscritura();

        }, 1500);

    }

    function detenerEscritura() {

        clearTimeout(temporizadorEscritura);

        if (
            escrituraActiva &&
            socket &&
            socket.readyState === WebSocket.OPEN
        ) {

            socket.send(JSON.stringify({
                accion: "detener_escritura"
            }));

        }

        escrituraActiva = false;

    }

    function mostrarEscritura(idRemitente, escribiendo) {

        if (idRemitente === idUsuario) {
            return;
        }

        const indicador = document.getElementById("indicador_escritura");

        if (indicador) {

            indicador.hidden = !escribiendo;

            indicador.textContent = escribiendo
                ? "Escribiendo..."
                : "";

        }

    }

    mensajeChat.addEventListener("input", () => {

        ajustarTextarea();

        notificarEscritura();

    });

    // --------------------------------------------------
    // SELECTOR DE EMOJIS
    // --------------------------------------------------

    btnEmojis.addEventListener("click", (evento) => {

        evento.stopPropagation();

        contenedorEmojis.hidden = !contenedorEmojis.hidden;

    });

    selectorEmojis?.addEventListener("emoji-click", (evento) => {

        const emoji = evento.detail.unicode;

        const inicio = mensajeChat.selectionStart;
        const final = mensajeChat.selectionEnd;

        mensajeChat.value =
            mensajeChat.value.substring(0, inicio) +
            emoji +
            mensajeChat.value.substring(final);

        const nuevaPosicion = inicio + emoji.length;

        mensajeChat.focus();

        mensajeChat.setSelectionRange(
            nuevaPosicion,
            nuevaPosicion
        );

        ajustarTextarea();

        notificarEscritura();

    });

    document.addEventListener("click", (evento) => {

        if (
            !contenedorEmojis.contains(evento.target) &&
            !btnEmojis.contains(evento.target)
        ) {

            contenedorEmojis.hidden = true;

        }

    });

    contenedorEmojis.addEventListener("click", (evento) => {

        evento.stopPropagation();

    });

    // --------------------------------------------------
    // INICIALIZAR
    // --------------------------------------------------

    async function inicializarChat() {

        await cargarMensajes();

        conectarWebSocket();

    }

    inicializarChat();

    // --------------------------------------------------
    // LIMPIEZA
    // --------------------------------------------------

    window.addEventListener("beforeunload", () => {

        detenerEscritura();

        if (socket) {
            socket.close();
        }

        clearTimeout(temporizadorReconectar);

    });

});
