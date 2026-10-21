function configurarContrasenia(contenedor) {
    const inputClave = contenedor.querySelector('input[name="contrasenia"]');
    const inputCheckbox = contenedor.querySelector(".checkbox_ojo");
    const labelOjo = contenedor.querySelector(".icono_ojo");

    if (!inputClave || !inputCheckbox || !labelOjo) {
        throw new Error(
            "El campo de contraseña debe incluir su input, checkbox y label del ojo."
        );
    }

    if (contenedor.dataset.contraseniaConfigurada === "true") {
        return;
    }

    inputCheckbox.id = `checkbox_ojo_${crypto.randomUUID()}`;
    labelOjo.htmlFor = inputCheckbox.id;

    const actualizarVisibilidad = () => {
        inputClave.type = inputCheckbox.checked ? "text" : "password";
    };

    inputCheckbox.addEventListener("change", actualizarVisibilidad);
    actualizarVisibilidad();
    contenedor.dataset.contraseniaConfigurada = "true";
}