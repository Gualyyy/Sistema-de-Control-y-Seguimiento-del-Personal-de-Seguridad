document.addEventListener("DOMContentLoaded", function () {

    const pais_nacimiento = document.getElementById("pais_nacimiento");
    const estado_nacimiento = document.getElementById("estado_nacimiento");
    const municipio_nacimiento = document.getElementById("municipio_nacimiento");
    const parroquia_nacimiento = document.getElementById("parroquia_nacimiento");
    const direccion_nacimiento = document.getElementById("direccion_nacimiento");
    const fecha_nacimiento_usuario = document.getElementById("fecha_nacimiento_usuario");

    const estado_nacimiento_nvzla = document.getElementById("estado_novzla");
    const municipio_nacimiento_nvzla = document.getElementById("municipio_novzla");
    const parroquia_nacimiento_nvzla = document.getElementById("parroquia_novzla");

    const paises = [
        "Afganistán",
        "Albania",
        "Alemania",
        "Andorra",
        "Angola",
        "Antigua y Barbuda",
        "Arabia Saudita",
        "Argelia",
        "Argentina",
        "Armenia",
        "Australia",
        "Austria",
        "Azerbaiyán",
        "Bahamas",
        "Bangladés",
        "Barbados",
        "Baréin",
        "Bélgica",
        "Belice",
        "Benín",
        "Bielorrusia",
        "Birmania",
        "Bolivia",
        "Bosnia y Herzegovina",
        "Botsuana",
        "Brasil",
        "Brunéi",
        "Bulgaria",
        "Burkina Faso",
        "Burundi",
        "Bután",
        "Cabo Verde",
        "Camboya",
        "Camerún",
        "Canadá",
        "Catar",
        "Chad",
        "Chile",
        "China",
        "Chipre",
        "Ciudad del Vaticano",
        "Colombia",
        "Comoras",
        "Corea del Norte",
        "Corea del Sur",
        "Costa de Marfil",
        "Costa Rica",
        "Croacia",
        "Cuba",
        "Dinamarca",
        "Dominica",
        "Ecuador",
        "Egipto",
        "El Salvador",
        "Emiratos Árabes Unidos",
        "Eritrea",
        "Eslovaquia",
        "Eslovenia",
        "España",
        "Estados Unidos",
        "Estonia",
        "Etiopía",
        "Filipinas",
        "Finlandia",
        "Fiyi",
        "Francia",
        "Gabón",
        "Gambia",
        "Georgia",
        "Ghana",
        "Granada",
        "Grecia",
        "Guatemala",
        "Guyana",
        "Guinea",
        "Guinea ecuatorial",
        "Guinea-Bisáu",
        "Haití",
        "Honduras",
        "Hungría",
        "India",
        "Indonesia",
        "Irak",
        "Irán",
        "Irlanda",
        "Islandia",
        "Islas Marshall",
        "Islas Salomón",
        "Israel",
        "Italia",
        "Jamaica",
        "Japón",
        "Jordania",
        "Kazajistán",
        "Kenia",
        "Kirguistán",
        "Kiribati",
        "Kuwait",
        "Laos",
        "Lesoto",
        "Letonia",
        "Líbano",
        "Liberia",
        "Libia",
        "Liechtenstein",
        "Lituania",
        "Luxemburgo",
        "Madagascar",
        "Malasia",
        "Malaui",
        "Maldivas",
        "Malí",
        "Malta",
        "Marruecos",
        "Mauricio",
        "Mauritania",
        "México",
        "Micronesia",
        "Moldavia",
        "Mónaco",
        "Mongolia",
        "Montenegro",
        "Mozambique",
        "Namibia",
        "Nauru",
        "Nepal",
        "Nicaragua",
        "Níger",
        "Nigeria",
        "Noruega",
        "Nueva Zelanda",
        "Omán",
        "Países Bajos",
        "Pakistán",
        "Palaos",
        "Panamá",
        "Papúa Nueva Guinea",
        "Paraguay",
        "Perú",
        "Polonia",
        "Portugal",
        "Reino Unido",
        "República Centroafricana",
        "República Checa",
        "República de Macedonia",
        "República del Congo",
        "República Democrática del Congo",
        "República Dominicana",
        "República Sudafricana",
        "Ruanda",
        "Rumanía",
        "Rusia",
        "Samoa",
        "San Cristóbal y Nieves",
        "San Marino",
        "San Vicente y las Granadinas",
        "Santa Lucía",
        "Santo Tomé y Príncipe",
        "Senegal",
        "Serbia",
        "Seychelles",
        "Sierra Leona",
        "Singapur",
        "Siria",
        "Somalia",
        "Sri Lanka",
        "Suazilandia",
        "Sudán",
        "Sudán del Sur",
        "Suecia",
        "Suiza",
        "Surinam",
        "Tailandia",
        "Tanzania",
        "Tayikistán",
        "Timor Oriental",
        "Togo",
        "Tonga",
        "Trinidad y Tobago",
        "Túnez",
        "Turkmenistán",
        "Turquía",
        "Tuvalu",
        "Ucrania",
        "Uganda",
        "Uruguay",
        "Uzbekistán",
        "Vanuatu",
        "Venezuela",
        "Vietnam",
        "Yemen",
        "Yibuti",
        "Zambia",
        "Zimbabue"
    ];
    const Estado = [
        "Amazonas", "Anzoátegui", "Apure", "Aragua", "Barinas", "Bolívar", "Carabobo", "Cojedes",
        "Delta Amacuro", "Distrito Capital", "Falcón", "Guárico", "Lara", "Mérida", "Miranda", "Monagas",
        "Nueva Esparta", "Portuguesa", "Sucre", "Táchira", "Trujillo", "La Guaira", "Yaracuy", "Zulia", "Dependencias"
    ];
    const municipiosPorEstado = {
        "Amazonas": [
            "Alto Orinoco", "Atabapo", "Atures", "Autana",
            "Manapiare", "Maroa", "Río Negro"
        ],

        "Anzoátegui": [
            "Anaco", "Aragua", "Diego Bautista Urbaneja", "Fernando de Peñalver",
            "Francisco del Carmen Carvajal", "Francisco de Miranda", "Guanta",
            "Independencia", "José Gregorio Monagas", "Juan Antonio Sotillo",
            "Juan Manuel Cajigal", "Libertad", "Manuel Ezequiel Bruzual",
            "Pedro María Freites", "Píritu", "San Juan de Capistrano",
            "Santa Ana", "Simón Bolívar", "Simón Rodríguez"
        ],

        "Apure": [
            "Achaguas", "Biruaca", "Muñoz", "Páez",
            "Pedro Camejo", "Rómulo Gallegos", "San Fernando"
        ],

        "Aragua": [
            "Bolívar", "Camatagua", "Francisco Linares Alcántara",
            "Girardot", "José Ángel Lamas", "José Félix Ribas",
            "José Rafael Revenga", "Libertador", "Mario Briceño Iragorry",
            "Ocumare de la Costa de Oro", "San Casimiro",
            "San Sebastián", "Santiago Mariño", "Santos Michelena",
            "Sucre", "Tovar", "Urdaneta", "Zamora"
        ],

        "Barinas": [
            "Alberto Arvelo Torrealba", "Andrés Eloy Blanco",
            "Antonio José de Sucre", "Arismendi", "Barinas",
            "Bolívar", "Cruz Paredes", "Ezequiel Zamora",
            "Obispos", "Pedraza", "Rojas", "Sosa"
        ],

        "Bolívar": [
            "Angostura", "Caroní", "Cedeño", "El Callao",
            "Gran Sabana", "Heres", "Padre Pedro Chien",
            "Piar", "Roscio", "Sifontes", "Sucre"
        ],

        "Carabobo": [
            "Bejuma", "Carlos Arvelo", "Diego Ibarra",
            "Guacara", "Juan José Mora", "Libertador",
            "Los Guayos", "Miranda", "Montalbán",
            "Naguanagua", "Puerto Cabello", "San Diego",
            "San Joaquín", "Valencia"
        ],

        "Cojedes": [
            "Anzoátegui", "El Pao", "Girardot",
            "Lima Blanco", "Pao de San Juan Bautista",
            "Ricaurte", "Rómulo Gallegos",
            "San Carlos", "Tinaco"
        ],

        "Delta Amacuro": [
            "Antonio Díaz", "Casacoima",
            "Pedernales", "Tucupita"
        ],

        "Distrito Capital": [
            "Libertador"
        ],

        "Falcón": [
            "Acosta", "Bolívar", "Buchivacoa", "Cacique Manaure",
            "Carirubana", "Colina", "Dabajuro", "Democracia",
            "Falcón", "Federación", "Jacura", "Los Taques",
            "Mauroa", "Miranda", "Monseñor Iturriza",
            "Palmasola", "Petit", "Píritu",
            "San Francisco", "Silva", "Sucre",
            "Tocópero", "Unión", "Urumaco", "Zamora"
        ],

        "Guárico": [
            "Camaguán", "Chaguaramas", "El Socorro",
            "Francisco de Miranda", "José Félix Ribas",
            "José Tadeo Monagas", "Juan Germán Roscio",
            "Julián Mellado", "Las Mercedes",
            "Leonardo Infante", "Ortiz",
            "San Gerónimo de Guayabal",
            "San José de Guaribe",
            "Santa María de Ipire"
        ],

        "La Guaira": [
            "Vargas"
        ],

        "Lara": [
            "Andrés Eloy Blanco", "Crespo", "Iribarren",
            "Jiménez", "Morán", "Palavecino",
            "Simón Planas", "Torres", "Urdaneta"
        ],

        "Mérida": [
            "Alberto Adriani", "Andrés Bello",
            "Antonio Pinto Salinas", "Aricagua",
            "Arzobispo Chacón", "Campo Elías",
            "Caracciolo Parra Olmedo", "Cardenal Quintero",
            "Guaraque", "Julio César Salas",
            "Justo Briceño", "Libertador",
            "Miranda", "Obispo Ramos de Lora",
            "Padre Noguera", "Pueblo Llano",
            "Rangel", "Rivas Dávila",
            "Santos Marquina", "Sucre",
            "Tovar", "Tulio Febres Cordero",
            "Zea"
        ],

        "Miranda": [
            "Acevedo", "Andrés Bello", "Baruta",
            "Brión", "Buroz", "Carrizal",
            "Chacao", "Cristóbal Rojas",
            "El Hatillo", "Guaicaipuro",
            "Independencia", "Lander",
            "Los Salias", "Páez",
            "Paz Castillo", "Pedro Gual",
            "Plaza", "Simón Bolívar",
            "Sucre", "Urdaneta", "Zamora"
        ],

        "Monagas": [
            "Acosta", "Aguasay", "Bolívar",
            "Caripe", "Cedeño", "Ezequiel Zamora",
            "Libertador", "Maturín", "Piar",
            "Punceres", "Santa Bárbara",
            "Sotillo", "Uracoa"
        ],

        "Nueva Esparta": [
            "Antolín del Campo", "Arismendi",
            "Díaz", "García", "Gómez",
            "Maneiro", "Marcano", "Mariño",
            "Península de Macanao",
            "Tubores", "Villalba"
        ],

        "Portuguesa": [
            "Agua Blanca", "Araure", "Esteller",
            "Guanare", "Guanarito",
            "Monseñor José Vicente de Unda",
            "Ospino", "Páez", "Papelón",
            "San Genaro de Boconoíto",
            "San Rafael de Onoto",
            "Santa Rosalía", "Sucre", "Turén"
        ],

        "Sucre": [
            "Andrés Eloy Blanco", "Andrés Mata",
            "Arismendi", "Benítez", "Bermúdez",
            "Bolívar", "Cajigal",
            "Cruz Salmerón Acosta",
            "Libertador", "Mariño",
            "Mejía", "Montes",
            "Ribero", "Sucre", "Valdez"
        ],

        "Táchira": [
            "Andrés Bello", "Antonio Rómulo Costa",
            "Ayacucho", "Bolívar", "Cárdenas",
            "Córdoba", "Fernández Feo",
            "Francisco de Miranda",
            "García de Hevia", "Guásimos",
            "Independencia", "Jáuregui",
            "José María Vargas", "Junín",
            "Libertad", "Libertador",
            "Lobatera", "Michelena",
            "Panamericano", "Pedro María Ureña",
            "Rafael Urdaneta",
            "Samuel Darío Maldonado",
            "San Cristóbal", "Seboruco",
            "Simón Rodríguez", "Sucre",
            "Torbes", "Uribante"
        ],

        "Trujillo": [
            "Andrés Bello", "Boconó", "Bolívar",
            "Candelaria", "Carache", "Escuque",
            "José Felipe Márquez Cañizales",
            "Juan Vicente Campos Elías",
            "La Ceiba", "Miranda",
            "Monte Carmelo", "Motatán",
            "Pampán", "Pampanito",
            "Rafael Rangel",
            "San Rafael de Carvajal",
            "Sucre", "Trujillo",
            "Urdaneta", "Valera"
        ],

        "Yaracuy": [
            "Arístides Bastidas", "Bolívar",
            "Bruzual", "Cocorote",
            "Independencia", "José Antonio Páez",
            "La Trinidad", "Manuel Monge",
            "Nirgua", "Peña",
            "San Felipe", "Sucre",
            "Urachiche", "Veroes"
        ],

        "Zulia": [
            "Almirante Padilla", "Baralt",
            "Cabimas", "Catatumbo", "Colón",
            "Francisco Javier Pulgar",
            "Guajira", "Jesús Enrique Lossada",
            "Jesús María Semprún",
            "La Cañada de Urdaneta",
            "Lagunillas", "Machiques de Perijá",
            "Mara", "Maracaibo",
            "Miranda", "Rosario de Perijá",
            "San Francisco", "Santa Rita",
            "Simón Bolívar", "Sucre",
            "Valmore Rodríguez"
        ]
    };
    const parroquiasPorMunicipio = {
        "Amazonas": {
            "Alto Orinoco": [
                "La Esmeralda",
                "Huachamacare",
                "Marawaka",
                "Mavaca",
                "Sierra Parima"
            ],

            "Atabapo": [
                "San Fernando de Atabapo",
                "Ucata",
                "Yapacana"
            ],

            "Atures": [
                "Fernando Girón Tovar",
                "Luis Alberto Gómez",
                "Parhueña",
                "Platanillal"
            ],

            "Autana": [
                "Isla de Ratón",
                "Samariapo",
                "Sipapo",
                "Munduapo"
            ],

            "Maroa": [
                "Maroa",
                "Victorino"
            ],

            "Manapiare": [
                "San Juan de Manapiare",
                "Alto Ventuari",
                "Medio Ventuari",
                "Bajo Ventuari"
            ],

            "Río Negro": [
                "San Carlos de Río Negro",
                "Solano",
                "Casiquiare",
                "Cocuy"
            ]
        },
        "Anzoátegui": {
            "Anaco": ["Anaco", "San Joaquín"],
            "Aragua": ["Aragua de Barcelona", "Cachipo"],
            "Fernando de Peñalver": ["Puerto Píritu", "San Miguel", "Sucre"],
            "Francisco del Carmen Carvajal": ["Valle de Guanape", "Santa Bárbara"],
            "Francisco de Miranda": ["Pariaguán"],
            "Guanta": ["Guanta", "Chorrerón"],
            "Independencia": ["Soledad"],
            "José Gregorio Monagas": ["Mapire", "Piar", "Santa Clara", "San Diego de Cabrutica", "Uverito", "Zuata"],
            "Juan Antonio Sotillo": ["Puerto La Cruz"],
            "Juan Manuel Cajigal": ["Onoto", "San Pablo"],
            "Libertad": ["San Mateo", "El Carito", "Santa Inés"],
            "Manuel Ezequiel Bruzual": ["Clarines", "Guanape", "Sabana de Uchire"],
            "Pedro María Freites": ["Cantaura", "Libertador", "Santa Rosa", "Urica"],
            "Píritu": ["Píritu", "San Francisco"],
            "San José de Guanipa": ["San José de Guanipa"],
            "San Juan de Capistrano": ["Boca de Uchire", "Boca de Chávez"],
            "Santa Ana": ["Santa Ana", "Boca de Santa Ana"],
            "Simón Bolívar": ["Bergantín", "Caigua", "El Carmen", "El Pilar", "Naricual", "San Cristóbal"],
            "Simón Rodríguez": ["El Tigre"]
        },
        "Apure": {
            "Achaguas": ["Achaguas", "Apurito", "El Yagual", "Guachara", "Mucuritas", "Queseras del Medio"],
            "Biruaca": ["Biruaca"],
            "Muñoz": ["Bruzual", "Mantecal", "Quintero", "Rincón Hondo", "San Vicente"],
            "Páez": ["Guasdualito", "Aramendi", "El Amparo", "San Camilo", "Urdaneta"],
            "Pedro Camejo": ["San Juan de Payara", "Codazzi", "Cunaviche"],
            "Rómulo Gallegos": ["Elorza", "La Trinidad"],
            "San Fernando": ["San Fernando", "El Recreo", "Peñalver", "San Rafael de Atamaica"]
        },
        "Aragua": {
            "Bolívar": ["San Mateo"],
            "Camatagua": ["Camatagua", "Carmen de Cura"],
            "Francisco Linares Alcántara": ["Santa Rita", "Francisco de Miranda", "Monseñor Feliciano González"],
            "Girardot": ["Pedro José Ovalles", "Joaquín Crespo", "José Casanova Godoy", "Madre María de San José", "Andrés Eloy Blanco", "Los Tacarigua", "Las Delicias", "Choroní"],
            "José Ángel Lamas": ["Santa Cruz"],
            "José Félix Ribas": ["Victoria", "Zuata", "La Quebrada", "Pao de Zárate", "Castor Nieves Ríos"],
            "José Rafael Revenga": ["El Consejo"],
            "Libertador": ["Palo Negro", "San Martín de Porres"],
            "Mario Briceño Iragorry": ["El Limón", "Caña de Azúcar"],
            "Ocumare de la Costa de Oro": ["Ocumare de la Costa"],
            "San Casimiro": ["San Casimiro", "Güiripa", "Ollas de Caramacate", "Valle Morín"],
            "San Sebastián": ["San Sebastián"],
            "Santiago Mariño": ["Turmero", "Arévalo Aponte", "Chuao", "Samán de Güere", "Alfredo Pacheco Miranda"],
            "Santos Michelena": ["Las Tejerías", "Tiara"],
            "Sucre": ["Cagua", "Bella Vista"],
            "Tovar": ["Colonia Tovar"],
            "Urdaneta": ["Barbacoas", "Las Peñitas", "San Francisco de Cara", "Taguay"],
            "Zamora": ["Villa de Cura", "Magdaleno", "San Francisco de Asís", "Valles de Tucutunemo", "Augusto Mijares"]
        },
        "Trujillo": {
            "Andrés Bello": ["Santa Isabel", "Araguaney", "El Jaguito", "La Esperanza"],
            "Boconó": ["Boconó", "Ayacucho", "Burbusay", "El Carmen", "General Ribas", "Guaramacal", "Monseñor Jáuregui", "Mosquey", "Rafael Rangel", "San José", "San Miguel", "Vega de Guaramacal"],
            "Bolívar": ["Sabana Grande", "Cheregüé", "Granados"],
            "Candelaria": ["Chejendé", "Arnoldo Gabaldón", "Bolivia", "Carrillo", "Cegarra", "Manuel Salvador Ulloa", "San José"],
            "Carache": ["Carache", "Cuicas", "La Concepción", "Panamericana", "Santa Cruz"],
            "Escuque": ["Escuque", "La Unión", "Sabana Libre", "Santa Rita"],
            "José Felipe Márquez Cañizales": ["El Socorro", "Antonio José de Sucre", "Los Caprichos"],
            "Juan Vicente Campo Elías": ["Campo Elia", "La Placita", "Los Caprichos"],
            "La Ceiba": ["Santa Apolonia", "Zona Rica", "La Ceiba"],
            "Miranda": ["El Dividive", "Agua Santa", "Agua Caliente", "El Cenizo", "Valerita"],
            "Monte Carmelo": ["Monte Carmelo", "Buena Vista", "Casa de Tabla"],
            "Motatán": ["Motatán", "El Baño", "Jalisco"],
            "Pampán": ["Pampán", "Flor de Patria", "Monay", "Santa Ana"],
            "Pampanito": ["Pampanito", "La concepción", "Pampanito II"],
            "parroquias": ["Betijoque", "José Gregorio Hernández", "La Pueblita", "Los Cedros"],
            "San Rafael de Carvajal": ["Carvajal", "La Cejita", "Campo Alegre", "Las Mesetas"],
            "Sucre": ["Sabana de Mendoza", "El Paraiso", "Junín", "Valmore Rodríguez"],
            "Trujillo": ["Trujillo", "San Lázaro", "Chiquinquirá", "Santa Rosa", "La Plazuela", "San Jacinto", "Tres Esquinas"],
            "Urdaneta": ["Cabimbú", "Jajó", "La Mesa de Esnujaque", "Santiago", "Tuñame", "La Quebrada"],
            "Valera": ["Juan Ignacio Montilla", "La Beatriz", "La Puerta", "Mendoza", "Mercedes Díaz", "San Luis"]
        },
        "Barinas": {
            "Alberto Arvelo Torrealba": ["Sabaneta", "Rodríguez Domínguez"],
            "Andrés Eloy Blanco": ["El Cantón", "Santa Cruz de Guacas", "Puerto Vivas"],
            "Antonio José de Sucre": ["Socopó"],
            "Arismendi": ["Arismendi", "Guadarrama", "La Unión", "San Antonio"],
            "Barinas": ["Alto Barinas", "Alberto Arvelo Larriva", "San Silvestre", "Santa Inés", "Santa Lucía", "Torunos", "El Carmen", "Rómulo Betancourt", "Corazón de Jesús", "Ramón Ignacio Méndez", "Manuel Palacio Fajardo", "Juan Antonio Rodríguez Domínguez", "Domingo Ortiz de Páez"],
            "Bolívar": ["Barinitas", "Altamira de Cáceres", "Calderas"],
            "Cruz Paredes": ["Barrancas", "El Socorro", "Masparrito"],
            "Ezequiel Zamora": ["Santa Bárbara", "José Ignacio del Pumar", "Pedro Briceño Méndez", "Ramón Ignacio Méndez"],
            "Obispo": ["Obispos", "El Real", "La Luz", "Los Guasimitos"],
            "Pedraza": ["Ciudad Bolivia", "Ignacio Briceño", "José Félix Ribas", "Páez"],
            "Rojas": ["Libertad", "Dolores", "Palacios Fajardo", "Santa Rosa", "Simón Rodríguez"],
            "Sosa": ["Ciudad de Nutrias", "El Regalo", "Puerto de Nutrias", "Santa Catalina", "Simón Bolívar"]
        },
        "Bolívar": {
            "Caroní": ["Ciudad Guayana", "Parroquia Cachamay", "Parroquia Chirica", "Parroquia Dalla Costa", "Parroquia Simón Bolívar", "Parroquia Unare"],
            "Cedeño": ["Caicara del Orinoco", "Altagracia", "Ascensión Farreras", "Guaniamo", "La Urbana"],
            "Gran Sabana": ["Ikabarú", "Kavanayén", "Santa Elena de Uairén"],
            "Heres": ["Ciudad Bolívar", "Catedral", "Simón Bolívar", "Marhuanta"],
            "Piar": ["Aripao", "El Pao", "Upata", "San Félix", "El Manteco", "Tumeremo"],
            "Roscio": ["Guasipati", "El Callao"],
            "Sifontes": ["El Dorado", "Tumeremo", "San Isidro"],
            "Sucre": ["Maripa", "Barbacoa", "El Pao"]
        },
        "Carabobo": {
            "Bejuma": ["Bejuma", "Canoabo", "Simón Bolívar", "Fraternidad", "José Rafael Pulgar"],
            "Carlos Arvelo": ["Güigüe", "Tocuyito", "Unión", "Miranda", "Independencia", "Puerto Cabello"],
            "Juan José Mora": ["Morón", "Guacara", "Begoña", "Yagua", "Tacarigua"],
            "Libertador": ["Naguanagua", "San Joaquín", "Morón", "Valencia"],
            "Los Guayos": ["Los Guayos", "Catedral", "Guacara", "Tocuyito"],
            "Puerto Cabello": ["Puerto Cabello", "Bartolomé Salom", "Unión", "Borburata", "Juan José Flores"],
            "San Diego": ["San Diego", "Dallago", "Cascabel", "Vigirima"],
            "San Joaquín": ["San Joaquín", "El Pao", "Quirindai", "Nicolas Pulido"]
        },
        "Cojedes": {
            "Anzoátegui": ["Macapo", "El Baúl", "Puerto Colorado"],
            "Cojedes": ["San Carlos", "Juan de Mata Suárez", "Ramón Ignacio Méndez", "Libertad", "El Pao", "Evaristo Fernández"],
            "Ricaurte": ["Libertad", "El Amparo", "La Aguadita", "Monte Verde"],
            "Pao de San Juan Bautista": ["Pao", "El Baúl", "Las Vegas", "Santa Apolonia"],
            "Tinaco": ["Tinaco", "San Carlos", "Sucre", "Santa Inés"]
        },
        "Delta Amacuro": {
            "Antonio Díaz": ["Antonio Díaz", "Boca de Uracoa", "Boca de Tucupita"],
            "Casacoima": ["Casacoima", "Pedernales", "Tucupita", "El Triunfo"],
            "Tucupita": ["San José de Tucupita", "Boca de Manamo", "Curiapo", "Parguaza"]
        },
        "Falcón": {
            "Buchivacoa": ["Churuguara", "Las Calderas", "Caujaro", "Pueblo Nuevo"],
            "Carirubana": ["Punto Fijo", "Judibana", "Santa Ana"],
            "Colina": ["Chichiriviche", "La Vela de Coro", "Capanaparo", "Cumarebo"],
            "Dabajuro": ["Dabajuro", "Mene de Mauroa"],
            "Falcón": ["Coro", "Santa Ana", "Tocuyo de la Costa", "San Luis"],
            "José Laurencio Silva": ["Judibana", "Santa Ana", "Pueblo Nuevo"],
            "Los Taques": ["Los Taques", "Judibana", "Santa Cruz de Los Taques"],
            "Mauroa": ["Mauroa", "Mene de Mauroa"],
            "Miranda": ["Miranda", "Pueblo Nuevo", "La Vela de Coro"],
            "Monseñor Iturriza": ["Monseñor Iturriza", "Judibana", "Santa Ana"]
        },
        "Guárico": {
            "Camaguán": ["Camaguán", "Uverito", "Chaguaramas"],
            "Chaguaramas": ["Chaguaramas", "El Socorro", "Las Mercedes del Llano"],
            "El Socorro": ["El Socorro", "Las Mercedes del Llano", "San Juan de los Morros"],
            "José Félix Ribas": ["Ortiz", "Tucupido", "Altagracia de Orituco"],
            "Juan Germán Roscio": ["Calabozo", "Las Mercedes", "El Sombrero"],
            "Las Mercedes": ["Las Mercedes", "Ortiz", "Valle de la Pascua"],
            "Leonardo Infante": ["El Sombrero", "Ortiz"],
            "Pedro Zaraza": ["Zaraza", "San José de Unare", "Ortiz"],
            "San Gerónimo de Guayabal": ["San Gerónimo de Guayabal"],
            "Valle de la Pascua": ["Valle de la Pascua", "Calabozo", "San Juan de Los Morros"]
        },
        "Lara": {
            "Iribarren": ["Barquisimeto", "Juan de Villegas", "Santa Rosa", "Atarigua", "Guacara"],
            "Morán": ["El Tocuyo", "Cubiro", "Duaca", "La Aguadita"],
            "Palavecino": ["Cabudare", "Judibana", "Moroturo"],
            "Simón Planas": ["Sarare", "Buría", "Guanare"],
            "Torres": ["Carora", "Aguada Grande", "Bobare"]
        },
        "Mérida": {
            "Alberto Adriani": [
                "Presidente Betancourt",
                "Presidente Páez",
                "Presidente Rómulo Gallegos",
                "Gabriel Picón González",
                "Héctor Amable Mora"
            ],

            "Andrés Bello": [
                "La Azulita"
            ],

            "Antonio Pinto Salinas": [
                "Santa Cruz de Mora",
                "Mesa Bolívar",
                "Mesa de Las Palmas"
            ],

            "Aricagua": [
                "Aricagua",
                "San Antonio"
            ],

            "Arzobispo Chacón": [
                "Canaguá",
                "Capurí",
                "Chacantá",
                "El Molino",
                "Guaimaral"
            ],

            "Campo Elías": [
                "Fernández Peña",
                "Matriz",
                "Montalbán",
                "Acequias",
                "Jají",
                "La Mesa"
            ],

            "Caracciolo Parra Olmedo": [
                "Tucaní",
                "Florencio Ramírez"
            ],

            "Cardenal Quintero": [
                "Santo Domingo",
                "Las Piedras"
            ],

            "Guaraque": [
                "Guaraque",
                "Mesa de Quintero",
                "Río Negro"
            ],

            "Julio César Salas": [
                "Arapuey",
                "Palmira"
            ],

            "Justo Briceño": [
                "Torondoy",
                "San Cristóbal de Torondoy"
            ],

            "Libertador": [
                "El Llano",
                "Gonzalo Picón Febres",
                "Jacinto Plaza",
                "Juan Rodríguez Suárez",
                "Lasso de la Vega",
                "Mariano Picón Salas",
                "Milla",
                "Osuna Rodríguez",
                "Pedro María Morantes",
                "Presidente Páez",
                "Sagrario",
                "Spinetti Dini",
                "Arias"
            ],

            "Miranda": [
                "Timotes",
                "Andrés Eloy Blanco",
                "Nueva Bolivia",
                "La Venta"
            ],

            "Obispo Ramos de Lora": [
                "Santa Elena de Arenales",
                "San Rafael de Alcázar"
            ],

            "Padre Noguera": [
                "Santa María de Caparo"
            ],

            "Pueblo Llano": [
                "Pueblo Llano"
            ],

            "Rangel": [
                "Mucuchíes",
                "Cacute",
                "La Toma",
                "Mucurubá",
                "San Rafael"
            ],

            "Rivas Dávila": [
                "Bailadores",
                "Gerónimo Maldonado"
            ],

            "Santos Marquina": [
                "Tabay"
            ],

            "Sucre": [
                "Lagunillas",
                "Chiguará",
                "Estánquez",
                "San Juan",
                "Pueblo Nuevo del Sur"
            ],

            "Tovar": [
                "El Amparo",
                "El Llano",
                "San Francisco",
                "Tovar"
            ],

            "Tulio Febres Cordero": [
                "Nueva Bolivia",
                "Independencia",
                "Mariano Picón Salas"
            ],

            "Zea": [
                "Zea",
                "Caño El Tigre"
            ]
        },
        "Miranda": {
            "Acevedo": ["Petare", "Guarenas", "Guatire"],
            "Baruta": ["Baruta", "El Cafetal"],
            "Brión": ["Mamporal", "Curiepe"],
            "Carrizal": ["Carrizal", "Paracotos"],
            "Chacao": ["Chacao", "El Rosal"],
            "Cristóbal Rojas": ["Charallave", "Cúa"],
            "El Hatillo": ["El Hatillo", "La Lagunita"],
            "Los Salias": ["San Antonio de Los Altos", "Carrizal"],
            "Sucre": ["Petare", "Petare Central"],
            "Tomás Lander": ["Ocumare del Tuy", "Santa Teresa del Tuy"]
        },
        "Monagas": {
            "Acosta": ["San Antonio", "Quiriquire"],
            "Aguasay": ["Aguasay", "Jusepín"],
            "Ezequiel Zamora": ["Punta de Mata", "Temblador"],
            "Libertador": ["Temblador", "Temblador"],
            "Maturín": ["Maturín", "San Simón"],
            "Piar": ["Aragua de Maturín", "El Furrial"],
            "Santa Bárbara": ["Santa Bárbara", "Punta de Mata"],
            "Uracoa": ["Uracoa", "Barrancas"]
        },
        "Nueva Esparta": {
            "Antolín del Campo": ["La Plaza de Paraguachí", "Villa Rosa"],
            "Arismendi": ["La Asunción", "El Cercado"],
            "García": ["Porlamar", "Pampatar"],
            "Maneiro": ["Punta de Piedras", "El Valle del Espíritu Santo"],
            "Mariño": ["Porlamar", "Pampatar"]
        },
        "Portuguesa": {
            "Agua Blanca": ["Agua Blanca", "Los Cedros"],
            "Araure": ["Araure", "Ospino"],
            "Esteller": ["Biscucuy", "Guanare"],
            "Guanare": ["Guanare", "Biscucuy"],
            "Ospino": ["Ospino", "Píritu"],
            "Papelón": ["Papelón", "Mesa de Cavaca"],
            "San Genaro de Boconoíto": ["Boconoíto", "Mesa de Cavaca"],
            "Guanarito": ["Guanarito", "Trinidad de la Capilla", "Divina Pastora"]
        },
        "Sucre": {
            "Andrés Mata": ["Cumaná", "Guaraguao"],
            "Benítez": ["Carúpano", "El Pilar"],
            "Bermúdez": ["Cumanacoa", "Boca de Uchire"],
            "Bolívar": ["Santa Fe", "San Antonio"],
            "Cajigal": ["Río Caribe", "Catuaro"],
            "Libertador": ["Tunapuy", "Cariaco"],
            "Maturín": ["El Furrial", "San Antonio de Maturín"],
            "Ribero": ["Cariaco", "San José de Aerocuar"],
            "Valdez": ["Cumanacoa", "Marigüitar"]
        },
        "Distrito Capital": {
            "Libertador": [
                "23 de Enero", "Altagracia", "Catedral", "Coche", "El Paraíso",
                "El Recreo", "El Valle", "La Pastora", "La Vega", "Macarao",
                "San Agustín", "San Bernardino", "San José", "San Juan",
                "Santa Rosalía", "Santa Teresa"
            ]
        },
        "La Guaira": {
            "Vargas": [
                "Carayaca", "Caraballeda", "Catia La Mar", "El Junko",
                "La Guaira", "Macuto", "Naiguatá", "Caribe", "Maiquetía"
            ]
        },

        "Táchira": {
            "Andrés Bello": [
                "Cordero"
            ],

            "Antonio Rómulo Costa": [
                "Antonio Rómulo Costa"
            ],

            "Ayacucho": [
                "San Juan de Colón",
                "Rivas Berti",
                "San Pedro del Río"
            ],

            "Bolívar": [
                "Bolívar",
                "Palotal",
                "General Juan Vicente Gómez",
                "Isaías Medina Angarita"
            ],

            "Cárdenas": [
                "Táriba",
                "La Florida",
                "Amenodoro Rangel Lamus"
            ],

            "Córdoba": [
                "Santa Ana",
                "Alberto Adriani",
                "Palo Gordo"
            ],

            "Fernández Feo": [
                "Fernández Feo",
                "Alberto Adriani",
                "Santo Domingo"
            ],

            "Francisco de Miranda": [
                "San José de Bolívar"
            ],

            "García de Hevia": [
                "La Fría",
                "Boca de Grita",
                "José Antonio Páez"
            ],

            "Guásimos": [
                "Palmira"
            ],

            "Independencia": [
                "Capacho Nuevo",
                "Juan Germán Roscio"
            ],

            "Jáuregui": [
                "La Grita",
                "Emilio Constantino Guerrero",
                "Monseñor Miguel Antonio Salas"
            ],

            "José María Vargas": [
                "El Cobre"
            ],

            "Junín": [
                "Rubio",
                "Bramón",
                "La Petrólea",
                "Quinimarí"
            ],

            "Libertad": [
                "Capacho Viejo",
                "Cipriano Castro"
            ],

            "Libertador": [
                "Abejales",
                "Doradas",
                "Emeterio Ochoa"
            ],

            "Lobatera": [
                "Lobatera",
                "Constitución"
            ],

            "Michelena": [
                "Michelena"
            ],

            "Panamericano": [
                "Abejales",
                "La Palmita"
            ],

            "Pedro María Ureña": [
                "Pedro María Ureña",
                "Nueva Arcadia"
            ],

            "Rafael Urdaneta": [
                "Delicias",
                "San José de Bolívar"
            ],

            "Samuel Darío Maldonado": [
                "La Tendida",
                "Boconó"
            ],

            "San Cristóbal": [
                "Pedro María Morantes",
                "San Juan Bautista",
                "San Sebastián",
                "Dr. Francisco Romero Lobo",
                "La Concordia",
                "San Cristóbal"
            ],

            "Seboruco": [
                "Seboruco"
            ],

            "Simón Rodríguez": [
                "San Simón"
            ],

            "Sucre": [
                "Queniquea",
                "Eleazar López Contreras",
                "San Pablo"
            ],

            "Torbes": [
                "San Josecito"
            ],

            "Uribante": [
                "Cárdenas",
                "Juan Pablo Peñaloza",
                "Potosí",
                "Santa Ana"
            ]
        },
        "Zulia": {
            "Almirante Padilla": [
                "Isla de Toas", "Monagas"
            ],
            "Baralt": [
                "San Timoteo", "General Urdaneta", "Libertador",
                "Marcelino Briceño", "Pueblo Nuevo", "Manuel Guanipa Matos"
            ],
            "Cabimas": [
                "Ambrosio", "Arístides Calvani", "Carmen Herrera",
                "Germán Ríos Linares", "Jorge Hernández", "La Rosa",
                "Punta Gorda", "Rómulo Betancourt", "San Benito"
            ],
            "Catatumbo": [
                "Encontrados", "Udón Pérez"
            ],
            "Colón": [
                "San Carlos del Zulia", "Moralito", "Santa Bárbara",
                "Santa Cruz del Zulia", "Urribarrí"
            ],
            "Francisco Javier Pulgar": [
                "Simón Rodríguez", "Agustín Codazzi",
                "Carlos Quevedo", "Francisco Javier Pulgar"
            ],
            "Guajira": [
                "Sinamaica", "Alta Guajira",
                "Elías Sánchez Rubio", "Guajira"
            ],
            "Jesús Enrique Lossada": [
                "La Concepción", "San José",
                "Mariano Parra León", "José Ramón Yépez"
            ],
            "Jesús María Semprún": [
                "Jesús María Semprún", "Barí"
            ],
            "La Cañada de Urdaneta": [
                "Concepción", "Andrés Bello",
                "Chiquinquirá", "El Carmelo", "Potreritos"
            ],
            "Lagunillas": [
                "Libertad", "Alonso de Ojeda",
                "Venezuela", "Eleazar López Contreras", "Campo Lara"
            ],
            "Machiques de Perijá": [
                "Bartolomé de las Casas", "Libertad",
                "Río Negro", "San José de Perijá"
            ],
            "Mara": [
                "San Rafael", "La Sierrita", "Las Parcelas",
                "Luis de Vicente", "Monseñor Marcos Sergio Godoy",
                "Ricaurte", "Tamare"
            ],
            "Maracaibo": [
                "Antonio Borjas Romero", "Bolívar", "Cacique Mara",
                "Carracciolo Parra Pérez", "Cecilio Acosta", "Cristo de Aranza",
                "Coquivacoa", "Chiquinquirá", "Francisco Eugenio Bustamante",
                "Idelfonso Vásquez", "Juana de Ávila", "Luis Hurtado Higuera",
                "Manuel Dagnino", "Olegario Villalobos", "Raúl Leoni",
                "Santa Lucía", "San Isidro", "Venancio Pulgar"
            ],
            "Miranda": [
                "Altagracia", "Faría", "Ana María Campos",
                "San Antonio", "San José"
            ],
            "Rosario de Perijá": [
                "Donaldo García", "El Rosario", "Sixto Zambrano"
            ],
            "San Francisco": [
                "San Francisco", "El Bajo", "Domitila Flores",
                "Francisco Ochoa", "Los Cortijos", "Marcial Hernández",
                "José Domingo Rus"
            ],
            "Santa Rita": [
                "Santa Rita", "El Mene", "Pedro Lucas Urribarrí",
                "José Cenobio Urribarrí"
            ],
            "Simón Bolívar": [
                "Rafael María Baralt", "Manuel Manrique", "Rafael Urdaneta"
            ],
            "Sucre": [
                "Bobures", "Gibraltar", "Heras",
                "Monseñor Arturo Álvarez", "Rómulo Gallegos", "El Batey"
            ],
            "Valmore Rodríguez": [
                "Rafael Urdaneta", "La Victoria", "Raúl Cuenca"
            ]
        }
    };

    function cargarPaises() {
        pais_nacimiento.innerHTML = '<option value="" disabled selected hidden>Elija el País</option>';

        paises.forEach(pais => {
            const opcion = document.createElement("option");
            opcion.value = pais;
            opcion.textContent = pais;
            pais_nacimiento.appendChild(opcion);
        });
    }
    cargarPaises();

    pais_nacimiento.addEventListener("change", () => {
        const es_venezuela = pais_nacimiento.value === "Venezuela";

        const controles_venezuela = [
            estado_nacimiento,
            municipio_nacimiento,
            parroquia_nacimiento
        ];
        const controles_otro_pais = [
            estado_nacimiento_nvzla,
            municipio_nacimiento_nvzla,
            parroquia_nacimiento_nvzla
        ];

        controles_venezuela.forEach(control => {
            control.hidden = !es_venezuela;
            control.required = es_venezuela;
        });

        controles_otro_pais.forEach(control => {
            control.hidden = es_venezuela;
            control.required = !es_venezuela;
        });
    });

    // CARGAR ESTADOS DE VENEZUELA
    function cargarEstados() {
        estado_nacimiento.innerHTML = '<option value="" disabled selected hidden>Elija el Estado</option>';

        Estado.forEach(estado => {

            const opcion = document.createElement("option");

            opcion.value = estado;
            opcion.textContent = estado;

            estado_nacimiento.appendChild(opcion);
        });

    }
    cargarEstados();

    // ESTADO → MUNICIPIO
    function cargarMunicipios() {
        const estado = estado_nacimiento.value;

        // Reiniciar
        municipio_nacimiento.innerHTML = '<option value="" disabled selected hidden>Elija el Municipio</option>';
        parroquia_nacimiento.innerHTML = '<option value="" disabled selected hidden>Elija una Parroquia</option>';
        municipio_nacimiento.required = false;
        parroquia_nacimiento.required = false;

        if (estado && estado in municipiosPorEstado) {
            municipiosPorEstado[estado].forEach(municipio => {
                const option = document.createElement("option");
                option.value = municipio;
                option.textContent = municipio;
                municipio_nacimiento.appendChild(option);
            });

            municipio_nacimiento.required = true;
        }
    }

    estado_nacimiento.addEventListener("change", cargarMunicipios);

    // MUNICIPIO → PARROQUIA
    function cargarParroquias() {
        const estado = estado_nacimiento.value;
        const municipio = municipio_nacimiento.value;

        parroquia_nacimiento.innerHTML = '<option value="" disabled selected hidden>Elija una Parroquia</option>';
        parroquia_nacimiento.required = false;

        if (estado &&
            municipio &&
            parroquiasPorMunicipio[estado] &&
            parroquiasPorMunicipio[estado][municipio]) {

            parroquiasPorMunicipio[estado][municipio].forEach(parroquia => {
                const option = document.createElement("option");
                option.value = parroquia;
                option.textContent = parroquia;
                parroquia_nacimiento.appendChild(option);
            });

            parroquia_nacimiento.required = true;
        }
    }

    municipio_nacimiento.addEventListener("change", cargarParroquias);

    // PARROQUIA → DIRECCIÓN + FECHA
    parroquia_nacimiento.addEventListener("change", function () {
        const parroquia = parroquia_nacimiento.value;
        if (!parroquia) {
            return;
        }

        direccion_nacimiento.required = true;

        fecha_nacimiento_usuario.required = true;
    });

});