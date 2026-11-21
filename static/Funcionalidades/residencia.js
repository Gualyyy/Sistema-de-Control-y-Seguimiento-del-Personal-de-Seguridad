document.addEventListener("DOMContentLoaded", function () {

    const municipioSelect = document.getElementById("municipio_residencia");
    const parroquiaSelect = document.getElementById("parroquia_residencia");
    const direccionTextarea = document.getElementById("direccion_domicilio");

    const municipios = ["Barinas", "Pedraza", "Antonio José de Sucre", "Ezequiel Zamora", "Bolívar", "Alberto Arvelo Torrealba", "Rojas", "Obispo", "Sosa", "Cruz Paredes", "Arismendi", "Andrés Eloy Blanco"];

    const parroquiasPorMunicipio = {
        "Barinas": ["Alfredo Arvelo Larriva", "San Silvestre", "Santa Inés", "Santa Lucía", "Torunos", "El Carmen", "Alto Barinas", "Rómulo Betancourt", "Corazón de Jesús", "Ramón Ignacio Méndez", "Manuel Palacio Fajardo", "Juan Antonio Rodríguez Domínguez", "Domingo Ortiz de Páez"],

        "Pedraza": ["Ciudad Bolivia", "Ignacio Briceño", "José Félix Ribas", "Páez"],

        "Antonio José de Sucre": ["Ticoporo", "Andrés Bello", "Nicolás Pulido"],

        "Ezequiel Zamora": ["Santa Bárbara", "José Ignacio del Pumar", "Pedro Briceño Méndez", "Ramón Ignacio Méndez"],

        "Bolívar": ["Barinitas", "Altamira de Cáceres", "Calderas"],

        "Alberto Arvelo Torrealba": ["Sabaneta", "El Real"],

        "Rojas": ["Libertad", "Dolores", "Palacios Fajardo", "Santa Rosa", "Simón Rodríguez"],

        "Obispo": ["Obispos", "El Real", "La Luz", "Los Guasimitos"],

        "Sosa": ["Ciudad de Nutrias", "El Regalo", "Puerto de Nutrias", "Santa Catalina", "Simón Bolívar"],

        "Cruz Paredes": ["Barrancas", "El Socorro", "Masparrito"],

        "Arismendi": ["Arismendi", "Guadarrama", "La Unión", "San Antonio"],

        "Andrés Eloy Blanco": ["El Cantón", "Santa Cruz de Guacas", "Puerto Vivas", "Dominga Ortiz de Páez"]
    };

    /******************** MUNICIPIO RESIDENCIA ***********************/

    function cargarMunicipios() {

        municipioSelect.innerHTML = "";

        municipios.forEach(municipio => {

            const option = document.createElement("option");

            option.value = municipio;
            option.textContent = municipio;

            municipioSelect.appendChild(option);
        });

        municipioSelect.disabled = false;
        municipioSelect.required = true;

        municipioSelect.value = "Barinas";

        parroquiaSelect.disabled = false;
        parroquiaSelect.required = true;

        direccionTextarea.disabled = false;
        direccionTextarea.required = true;
    }

    cargarMunicipios();


    /******************** PARROQUIA RESIDENCIA ***********************/

    function actualizarParroquias() {

        const municipio = municipioSelect.value;

        parroquiaSelect.innerHTML = "";

        if (!municipio || !(municipio in parroquiasPorMunicipio)) {

            parroquiaSelect.disabled = true;
            parroquiaSelect.required = false;

            return;
        }

        parroquiasPorMunicipio[municipio].forEach(parroquia => {

            const option = document.createElement("option");

            option.value = parroquia;
            option.textContent = parroquia;

            parroquiaSelect.appendChild(option);
        });

        parroquiaSelect.disabled = false;
        parroquiaSelect.required = true;

        parroquiaSelect.value =
            municipio === "Barinas" &&
                parroquiasPorMunicipio[municipio].includes("El Carmen")
                ? "El Carmen"
                : parroquiaSelect.options[0].value;

        direccionTextarea.disabled = false;
        direccionTextarea.required = true;
    }

    actualizarParroquias();

    municipioSelect.addEventListener("change", actualizarParroquias);

});
