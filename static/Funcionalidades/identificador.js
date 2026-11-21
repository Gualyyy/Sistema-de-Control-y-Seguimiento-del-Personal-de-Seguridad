function configurarIdentificador(campoCedula, selectNacionalidad, tipo_cliente) {

    const opcionesIdentificador = {
        V: "V",
        E: "E",
        J: "J",
        G: "G"
    };

    function actualizarOpciones() {
        const tipo = tipo_cliente.value;
        const valorAnterior = selectNacionalidad.value;

        selectNacionalidad.replaceChildren();

        const opcionesPermitidas = tipo === "PERSONAL" || tipo === "NATURAL"
            ? ["V", "E"]
            : tipo === "EMPRESA"
                ? ["J", "G"]
                : [];

        opcionesPermitidas.forEach(valor => {
            const opcion = document.createElement("option");

            opcion.value = valor;
            opcion.textContent = opcionesIdentificador[valor];

            selectNacionalidad.appendChild(opcion);
        });

        selectNacionalidad.value = opcionesPermitidas.includes(valorAnterior)
            ? valorAnterior
            : opcionesPermitidas[0] || "";

        longitudIdentidad();
    }

    function longitudIdentidad() {
        const nacionalidad = selectNacionalidad.value;

        campoCedula.value = "";

        if (!nacionalidad) {
            campoCedula.disabled = true;
            campoCedula.required = false;
            campoCedula.placeholder = "Ingrese el identificador";
            campoCedula.removeAttribute("minlength");
            campoCedula.removeAttribute("maxlength");
            return;
        }

        campoCedula.disabled = false;
        campoCedula.required = true;
        campoCedula.removeAttribute("minlength");
        campoCedula.removeAttribute("maxlength");

        switch (nacionalidad) {
            case "V":
                campoCedula.maxLength = 8;
                campoCedula.minLength = 7;
                campoCedula.placeholder = "Cédula (7-8 números)";
                break;

            case "E":
                campoCedula.maxLength = 10;
                campoCedula.minLength = 8;
                campoCedula.placeholder = "Documento extranjero (8-10 números)";
                break;

            case "J":
                campoCedula.maxLength = 9;
                campoCedula.minLength = 9;
                campoCedula.placeholder = "RIF jurídico (9 números)";
                break;

            case "G":
                campoCedula.maxLength = 9;
                campoCedula.minLength = 9;
                campoCedula.placeholder = "RIF gubernamental (9 números)";
                break;
        }
    }

    campoCedula.addEventListener("input", function () {
        this.value = this.value.replace(/\D/g, "");
    });

    selectNacionalidad.addEventListener("change", longitudIdentidad);
    tipo_cliente.addEventListener("change", actualizarOpciones);

    actualizarOpciones();
}