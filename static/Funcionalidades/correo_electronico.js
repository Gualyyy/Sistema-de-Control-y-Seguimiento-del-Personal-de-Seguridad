function configurarCorreo(inputCorreo, selectDominio) {

    if (!inputCorreo || !selectDominio) {
        console.error("No existe el control del correo o dominio");
        return;
    }

    const dominios = [
        "@gmail.com",
        "@outlook.com",
        "@yahoo.com"
    ];

    const caracteresDenegados = [
        "@", " ", "(", ")", "[", "]", "{", "}", "<", ">", ",", ";", ":",
        "\\", "/", "'", "\"", "|", "°", "¬", "¿", "?", "¡", "!", "#",
        "$", "%", "^", "&", "*", "=", "+", "~", "`", "-", "´"
    ];

    function cargarDominios() {

        selectDominio.innerHTML = "";

        const correoOpcional = selectDominio.classList.contains(
            "campo_opcional"
        );
        if (correoOpcional) {
            const opcionVacia = document.createElement("option");
            opcionVacia.value = "";
            opcionVacia.textContent = "Seleccione un dominio";
            opcionVacia.selected = true;
            selectDominio.appendChild(opcionVacia);
        }

        dominios.forEach(dominio => {

            const option = document.createElement("option");

            option.value = dominio;
            option.textContent = dominio;

            selectDominio.appendChild(option);

        });

        selectDominio.value = correoOpcional ? "" : dominios[0];
    }

    inputCorreo.addEventListener("keydown", function (e) {

        const tecla = e.key;

        if (
            [
                "Backspace",
                "Delete",
                "Tab",
                "ArrowLeft",
                "ArrowRight",
                "Home",
                "End"
            ].includes(tecla)
        ) {
            return;
        }

        if (!/^[a-zA-Z0-9._]$/.test(tecla)) {
            e.preventDefault();
            return;
        }

        if (caracteresDenegados.includes(tecla)) {
            e.preventDefault();
            return;
        }

        if (tecla === "." && this.value.includes(".")) {
            e.preventDefault();
            return;
        }

        if (tecla === "." && this.value.length === 0) {
            e.preventDefault();
        }

    });

    inputCorreo.addEventListener("paste", function (e) {
        e.preventDefault();
    });

    cargarDominios();
}