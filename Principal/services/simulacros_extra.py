"""Preguntas complementarias originales para la modalidad integral ampliada.

Se conservan las dos preguntas básicas por área para no romper las prácticas
que ya usa el proyecto. El banco adicional tiene ocho preguntas por área.
"""
BANCO_EXTRA = {
    "Matemáticas": [
        ("Un artículo cuesta $80.000 y tiene 25 % de descuento. ¿Cuánto se paga?", {"A": "$20.000", "B": "$60.000", "C": "$70.000", "D": "$100.000"}, "B", "Porcentajes", "El descuento es 20.000; 80.000 - 20.000 = 60.000."),
        ("Una receta requiere 2 tazas de harina para 5 porciones. ¿Cuántas tazas se necesitan para 15 porciones?", {"A": "3", "B": "5", "C": "6", "D": "10"}, "C", "Proporcionalidad", "Se triplican las porciones, por lo tanto 2 × 3 = 6 tazas."),
        ("En el conjunto 2, 4, 4, 6, 9, ¿cuál es la mediana?", {"A": "4", "B": "5", "C": "6", "D": "9"}, "A", "Estadística", "El valor central de los cinco datos ordenados es 4."),
        ("Un rectángulo tiene base 9 cm y altura 4 cm. ¿Cuál es su área?", {"A": "13 cm²", "B": "26 cm²", "C": "36 cm²", "D": "72 cm²"}, "C", "Geometría", "Área = 9 × 4 = 36 centímetros cuadrados."),
        ("Si un dado justo se lanza una vez, ¿cuál es la probabilidad de obtener un número par?", {"A": "1/6", "B": "1/3", "C": "1/2", "D": "2/3"}, "C", "Probabilidad", "Los resultados favorables son 2, 4 y 6: tres de seis posibles."),
        ("¿Cuál es la pendiente de la recta que pasa por (0,2) y (2,6)?", {"A": "1", "B": "2", "C": "3", "D": "4"}, "B", "Funciones", "La pendiente es (6-2)/(2-0) = 2."),
        ("¿Cuál es el siguiente término en 3, 6, 12, 24, ...?", {"A": "30", "B": "36", "C": "42", "D": "48"}, "D", "Patrones", "Cada término es el doble del anterior."),
        ("Una urna contiene 3 fichas rojas y 2 azules. ¿Qué fracción representa las fichas azules?", {"A": "2/3", "B": "2/5", "C": "3/5", "D": "1/2"}, "B", "Fracciones", "Hay 2 azules entre 5 fichas en total."),
    ],
    "Lectura Crítica": [
        ("Texto: «El parque recibe más visitantes desde que instalaron iluminación». ¿Qué hecho cambió?", {"A": "El clima", "B": "La iluminación", "C": "Los árboles", "D": "La ubicación"}, "B", "Comprensión literal", "La oración atribuye el aumento de visitantes a la iluminación."),
        ("Texto: «No todos los libros digitales son gratuitos». ¿Qué afirmación es compatible?", {"A": "Todos son gratuitos", "B": "Ninguno es gratuito", "C": "Algunos podrían tener costo", "D": "Todos tienen costo"}, "C", "Inferencia", "Negar que todos sean gratuitos permite que al menos algunos no lo sean."),
        ("Texto: «Se recomienda caminar diariamente porque favorece la salud». ¿Cuál es la intención?", {"A": "Narrar un viaje", "B": "Persuadir sobre un hábito", "C": "Dar una fecha", "D": "Presentar un diálogo"}, "B", "Intención comunicativa", "El enunciado da una recomendación y la fundamenta."),
        ("¿Cuál conector expresa consecuencia?", {"A": "Sin embargo", "B": "Aunque", "C": "Por lo tanto", "D": "Mientras"}, "C", "Conectores", "Por lo tanto introduce una conclusión o consecuencia."),
        ("Texto: «La ciudad creció, pero la oferta de transporte no aumentó». ¿Qué contraste establece?", {"A": "Crecimiento frente a transporte insuficiente", "B": "Menos habitantes y más buses", "C": "Menos tráfico", "D": "Igual crecimiento de ambos"}, "A", "Relación de ideas", "Se contrasta el crecimiento urbano con la falta de aumento del transporte."),
        ("Texto: «El experimento se repitió tres veces para verificar el resultado». ¿Por qué se repitió?", {"A": "Para cambiar la hipótesis", "B": "Para confirmar consistencia", "C": "Para reducir las muestras", "D": "Para evitar registrar datos"}, "B", "Comprensión literal", "La finalidad indicada es verificar el resultado."),
        ("Texto: «Tal vez llueva mañana». ¿Qué indica «tal vez»?", {"A": "Certeza", "B": "Negación", "C": "Posibilidad", "D": "Orden"}, "C", "Modalidad", "Tal vez expresa incertidumbre o posibilidad."),
        ("Texto: «Muchos creen que estudiar de noche es mejor, pero no hay datos suficientes». ¿Qué postura asume el autor?", {"A": "Afirma que es mejor", "B": "Advierte falta de evidencia", "C": "Prohíbe estudiar de noche", "D": "Sostiene que de día es peor"}, "B", "Evaluación de argumentos", "El autor señala que no existen datos suficientes para sostener la afirmación."),
    ],
    "Sociales y Ciudadanas": [
        ("¿Qué entidad colombiana vigila la conducta oficial de servidores públicos desde su función disciplinaria?", {"A": "Procuraduría General", "B": "Banco de la República", "C": "Registraduría", "D": "ICBF"}, "A", "Instituciones", "La Procuraduría tiene funciones de vigilancia de la conducta oficial y control disciplinario."),
        ("En una votación escolar, ¿qué práctica fortalece la democracia?", {"A": "Impedir candidatos", "B": "Permitir participación informada", "C": "Ocultar propuestas", "D": "Modificar votos"}, "B", "Participación", "La inclusión y la información facilitan decisiones democráticas."),
        ("Una comunidad quiere proteger un río. ¿Qué acción ciudadana es más pertinente?", {"A": "Verter residuos", "B": "Organizar limpieza y veeduría", "C": "Cerrar información", "D": "Retirar señales"}, "B", "Ciudadanía ambiental", "La participación y vigilancia ayudan a proteger un bien común."),
        ("¿Cuál de los siguientes es un derecho fundamental reconocido en Colombia?", {"A": "Vida", "B": "Cobrar peajes", "C": "Evitar impuestos", "D": "Conducir sin licencia"}, "A", "Derechos", "La protección a la vida está reconocida como derecho fundamental."),
        ("¿Qué busca la separación de poderes en un Estado democrático?", {"A": "Acumular decisiones", "B": "Evitar concentración del poder", "C": "Eliminar controles", "D": "Sustituir elecciones"}, "B", "Organización del Estado", "La división de funciones permite controles y equilibrios."),
        ("En una discusión comunitaria, ¿cuál actitud contribuye a resolver un conflicto?", {"A": "Escuchar argumentos", "B": "Interrumpir siempre", "C": "Difundir insultos", "D": "Ignorar acuerdos"}, "A", "Convivencia", "Escuchar y reconocer perspectivas facilita la resolución pacífica."),
        ("¿Qué significa que una norma se aplique a todas las personas por igual?", {"A": "Privilegio", "B": "Igualdad ante la ley", "C": "Arbitrariedad", "D": "Censura"}, "B", "Estado de derecho", "La igualdad ante la ley exige reglas comunes sin discriminación arbitraria."),
        ("Cuando una institución pública publica su presupuesto, ¿qué principio fortalece?", {"A": "Opacidad", "B": "Transparencia", "C": "Secreto absoluto", "D": "Exclusión"}, "B", "Control ciudadano", "La información pública permite seguimiento y rendición de cuentas."),
    ],
    "Ciencias Naturales": [
        ("¿Qué gas captan las plantas para realizar la fotosíntesis?", {"A": "Dióxido de carbono", "B": "Oxígeno", "C": "Helio", "D": "Neón"}, "A", "Biología", "Las plantas incorporan dióxido de carbono para producir compuestos orgánicos."),
        ("¿Qué propiedad se conserva en una reacción química balanceada?", {"A": "La masa total", "B": "La temperatura", "C": "El color", "D": "La forma"}, "A", "Química", "La ley de conservación de la masa establece que la masa se conserva."),
        ("¿Qué instrumento permite medir la temperatura?", {"A": "Balanza", "B": "Termómetro", "C": "Cronómetro", "D": "Regla"}, "B", "Medición", "El termómetro mide la temperatura."),
        ("¿Cuál es un ejemplo de cambio físico?", {"A": "Quemar papel", "B": "Oxidar hierro", "C": "Derretir hielo", "D": "Cocinar un huevo"}, "C", "Estados de la materia", "Derretir hielo cambia de estado sin formar una sustancia distinta."),
        ("En una cadena alimentaria, ¿qué organismos suelen ser productores?", {"A": "Hongos", "B": "Plantas", "C": "Leones", "D": "Bacterias descomponedoras"}, "B", "Ecología", "Las plantas transforman energía solar en materia orgánica."),
        ("Si una fuerza neta actúa sobre un cuerpo, ¿qué puede cambiar?", {"A": "Su movimiento", "B": "Su identidad química necesariamente", "C": "Su número de átomos necesariamente", "D": "La gravedad universal"}, "A", "Mecánica", "Según la segunda ley de Newton, la fuerza neta produce aceleración."),
        ("¿Qué parte de la célula contiene el material genético en células eucariotas?", {"A": "Núcleo", "B": "Pared celular", "C": "Citoplasma exclusivamente", "D": "Membrana"}, "A", "Biología celular", "El núcleo alberga la mayor parte del ADN en células eucariotas."),
        ("Un experimento cambia solo la cantidad de luz recibida por plantas. ¿Qué es la cantidad de luz?", {"A": "Variable dependiente", "B": "Variable independiente", "C": "Constante obligatoria", "D": "Resultado"}, "B", "Método científico", "La luz es la variable manipulada en el experimento."),
    ],
}
