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

        const opcionInicial = document.createElement("option");
        opcionInicial.value = "";
        opcionInicial.textContent = "I";
        selectNacionalidad.appendChild(opcionInicial);

        let opcionesPermitidas = [];

        if (tipo === "NATURAL") {
            opcionesPermitidas = ["V", "E"];
        } else if (tipo === "EMPRESA") {
            opcionesPermitidas = ["J", "G"];
        }

        opcionesPermitidas.forEach(valor => {
            const opcion = document.createElement("option");
            opcion.value = valor;
            opcion.textContent = opcionesIdentificador[valor];
            selectNacionalidad.appendChild(opcion);
        });

        selectNacionalidad.value =
            opcionesPermitidas.includes(valorAnterior)
                ? valorAnterior
                : "";

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

        switch (nacionalidad) {
            case "V":
                campoCedula.minLength = 7;
                campoCedula.maxLength = 8;
                campoCedula.placeholder = "Cédula (7-8 números)";
                break;

            case "E":
                campoCedula.minLength = 8;
                campoCedula.maxLength = 10;
                campoCedula.placeholder = "Documento extranjero (8-10 números)";
                break;

            case "J":
                campoCedula.minLength = 9;
                campoCedula.maxLength = 9;
                campoCedula.placeholder = "RIF jurídico (9 números)";
                break;

            case "G":
                campoCedula.minLength = 9;
                campoCedula.maxLength = 9;
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