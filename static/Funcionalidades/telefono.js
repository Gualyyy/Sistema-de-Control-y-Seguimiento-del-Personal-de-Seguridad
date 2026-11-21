function configurarTelefono(inputTelefono, selectPrefijo) {

    const prefijos = ["0414", "0424", "0416", "0426", "0412", "0422"];

    function cargarPrefijos() {

        selectPrefijo.innerHTML = "";

        inputTelefono.placeholder = "Número telefónico (7 dígitos)";

        const telefonoOpcional = selectPrefijo.classList.contains(
            "campo_opcional"
        );
        if (telefonoOpcional) {
            const opcionVacia = document.createElement("option");
            opcionVacia.value = "";
            opcionVacia.textContent = "Seleccione un prefijo";
            opcionVacia.selected = true;
            selectPrefijo.appendChild(opcionVacia);
        }

        prefijos.forEach(prefijo => {
            const option = document.createElement("option");
            option.value = prefijo;
            option.textContent = prefijo;

            selectPrefijo.appendChild(option);
        });

        selectPrefijo.value = telefonoOpcional ? "" : prefijos[0];
    }

    selectPrefijo.addEventListener("change", function () {
        inputTelefono.value = "";
        inputTelefono.focus();
    });

    inputTelefono.addEventListener("keydown", function (e) {
        const tecla = e.key;

        const teclasPermitidas = [
            "Backspace",
            "Delete",
            "ArrowLeft",
            "ArrowRight",
            "Tab",
            "Home",
            "End"
        ];

        if (teclasPermitidas.includes(tecla)) {
            return;
        }

        if (!/^\d$/.test(tecla)) {
            e.preventDefault();
            return;
        }

        if (this.value.length >= 7) {
            e.preventDefault();
        }
    });

    inputTelefono.addEventListener("paste", function (e) {
        e.preventDefault();
    });

    cargarPrefijos();
}