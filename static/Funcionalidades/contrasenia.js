
function configurarContrasenia(contenedor) {
    const inputClave = contenedor.querySelector(
        'input[name="contrasenia"], input[name="contrasenia_confirmar"]'
    );

    const inputCheckbox = contenedor.querySelector(
        ".checkbox_ojo, .checkbox_ojo_confirmar"
    );

    const labelOjo = contenedor.querySelector(
        ".icono_ojo, .icono_ojo_confirmar"
    );

    if (contenedor.dataset.contraseniaConfigurada === "true") {
        return;
    }

    // Asignar un ID único al checkbox y asociar su etiqueta.
    if (!inputCheckbox.id || document.querySelectorAll(
        `#${CSS.escape(inputCheckbox.id)}`
    ).length > 1) {
        inputCheckbox.id = `checkbox_ojo_${window.vigilanciaGenerarIdentificador()}`;
    }

    labelOjo.htmlFor = inputCheckbox.id;

    // Mostrar u ocultar solamente la contraseña correspondiente.
    const actualizarVisibilidad = () => {
        inputClave.type = inputCheckbox.checked ? "text" : "password";
    };

    inputCheckbox.addEventListener("change", actualizarVisibilidad);

    actualizarVisibilidad();

    contenedor.dataset.contraseniaConfigurada = "true";
}
