"""
Video tutorial: "Villa navideña animada" — paso a paso, con luces y pista que gira.

Cada escena es una animación HTML + GSAP (escenas/), renderizada cuadro a cuadro
con Chromium. La narración se genera con la voz neuronal Kokoro (sin internet) y
la música de fondo ("Noche de paz", dominio público) se sintetiza aquí mismo.

Uso:
    pip install kokoro-onnx soundfile playwright numpy
    python render.py                 # tutorial.mp4 + subtitulos.srt + guion.md
    python render.py --preview       # capturas de cada escena en video/preview/
    python render.py --preview --solo portada,planta
    python render.py --imagenes      # imágenes de la guía escrita (../imagenes/)

Requiere ffmpeg, Chromium y los archivos del modelo Kokoro en video/modelos/ (ver README).
"""
import base64
import hashlib
import json
import multiprocessing as mp
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
ESCENA_HTML = AQUI / "escenas" / "escena.html"
PARTES = AQUI / "_partes"
W, H, FPS = 1920, 1080, 30
CRF = 24

# ============================================================== VOZ Y MÚSICA
VOZ = "em_alex"        # voces en español de Kokoro: em_alex, ef_dora, em_santa
VELOCIDAD = 1.0
PAUSA = 0.5            # silencio después de cada frase
ENTRADA = 0.7          # segundos antes de la primera frase de cada escena
COLA = 0.9             # segundos después de la última frase
MUSICA = True          # "Noche de paz" en caja musical, muy suave debajo de la voz
CHROMIUM = "/opt/pw-browsers/chromium" if Path("/opt/pw-browsers/chromium").exists() else None

# ============================================================== GUION
# (id de la escena en escenas.js, capítulo, frases). Cada frase es un subtítulo y
# una marca de tiempo: las animaciones de la escena aparecen al empezar cada frase.
GUION = [
    ("portada", "Introducción", [
        "Hola. En este tutorial vamos a construir, paso a paso, una villa navideña animada igual a la que viste en la tienda.",
        "Tiene una iglesia con torre, una casa con tienda, una panadería, un río con luz azul y un árbol de Navidad con luces de colores.",
        "Y lo mejor: una pista de patinaje que gira sola.",
        "Te voy a explicar todo: los materiales, las herramientas, las medidas, la pintura, cómo se conectan las luces y cómo se arma el motor.",
        "Y al final, cómo hace la fábrica para sacar copias exactas en polirresina.",
    ]),
    ("original", "Cómo está hecha la original", [
        "Primero, veamos cómo está hecha la villa de la tienda.",
        "Es de polirresina: una mezcla de resina poliéster con polvo de piedra, llamado carbonato de calcio.",
        "La fábrica vacía esa mezcla en moldes de silicona, y por eso las casas salen huecas por dentro.",
        "Dentro de las casas van luces LED, y debajo de la base hay un motor pequeño con engranajes que hace girar la pista.",
        "Funciona con un cable USB de 5 V, o con 3 pilas AA.",
        "La pintura es a mano, y la nieve es pintura blanca con escarcha encima.",
    ]),
    ("plan", "Cómo está hecha la original", [
        "Nosotros lo vamos a hacer en dos etapas.",
        "En la etapa A construyes la pieza a mano, con foam, cartón pluma y masilla epóxica.",
        "Esa ya es tu villa terminada, con luces y movimiento.",
        "La etapa B es opcional: a esa pieza le sacas moldes de silicona y vacías copias en polirresina, igual que la fábrica.",
        "Si solo quieres una villa, te basta con la etapa A. Si quieres hacer varias, o venderlas, sigue también la etapa B.",
        "Calcula unos 3 o 4 fines de semana, porque hay que esperar varios secados.",
    ]),
    ("seguridad", "Seguridad", [
        "Antes de empezar, un minuto de seguridad.",
        "El cúter debe tener la hoja nueva. Corta siempre sobre una base de corte, y con la otra mano lejos del filo.",
        "El cautín pasa de 300 grados: úsalo con su soporte y nunca lo dejes encendido solo.",
        "La pistola de silicona también quema. Ten un vaso con agua fría cerca, por si te cae una gota.",
        "Todo este proyecto funciona con 5 V. Nunca conectes nada directo al enchufe de 220 V.",
        "Y en la etapa B, la resina suelta vapores tóxicos: necesitas respirador con filtros, guantes, lentes y mucha ventilación.",
    ]),
    ("herramientas", "Herramientas y materiales", [
        "Estas son las herramientas.",
        "Para cortar y medir: un cúter grande, un cúter de precisión, una regla metálica, una escuadra, un compás y una base de corte.",
        "Para pegar: una pistola de silicona, de preferencia de baja temperatura, porque la de alta temperatura derrite el foam.",
        "Para la electrónica: un cautín de 30 a 40 W con estaño, un multímetro, un pelacables, un alicate de corte y tubo termocontraíble.",
        "Para perforar: un minitaladro con brocas de 3 y 5 mm.",
        "Para pintar: pinceles planos y redondos, uno viejo para pincel seco, una espátula pequeña, una esponja y lija al agua.",
        "Y una secadora de pelo, que te va a ahorrar mucho tiempo de espera.",
    ]),
    ("mat_estructura", "Herramientas y materiales", [
        "Ahora los materiales, empezando por la estructura.",
        "Una plancha de MDF de 5 mm para la base, cortada de 32 por 24 cm.",
        "Foam de poliestireno extruido, el que venden como aislante térmico: una plancha de 5 cm y otra de 2.5 cm de grosor.",
        "Si no lo consigues, usa tecnopor de alta densidad, aunque el detalle sale menos fino.",
        "Cartón pluma, también llamado foam board, de 5 mm, para las paredes de las casas.",
        "Cartulina gruesa o cartón gris de 2 mm, para los techos, las agujas y los marcos.",
        "Masilla epóxica de dos componentes, tipo Poxilina, para las figuras y los adornos.",
        "Y además: conos de tecnopor, palitos de brocheta, mondadientes, alambre delgado y una lámina de PVC espumado de 3 mm.",
    ]),
    ("mat_acabado", "Herramientas y materiales", [
        "Para el acabado:",
        "Masilla lista para drywall, que también se vende como pasta muro, y cola sintética, la goma blanca.",
        "Mica transparente, papel celofán amarillo y papel albanene, para las ventanas.",
        "Imprimante acrílico blanco, y pinturas acrílicas en estos colores.",
        "Barniz acrílico brillante, para el hielo y el río.",
        "Para la nieve: bicarbonato de sodio, cola y pintura blanca. Y escarcha iridiscente fina, que es el brillo que tiene la original.",
        "Y barras de silicona transparentes, que sirven para los carámbanos y el agua del río.",
    ]),
    ("mat_electronica", "Herramientas y materiales", [
        "Y la electrónica. Esta es la lista exacta.",
        "16 LEDs blanco cálido: 8 de 5 mm difusos, para dentro de las casas, y 8 de 3 mm transparentes, que se ven como foquitos en las fachadas.",
        "6 LEDs RGB de cambio lento, de dos patas: son los que cambian de color solos, como los del árbol de la original.",
        "1 LED azul de 5 mm para el río.",
        "Resistencias de un cuarto de watt: 20 de 220 ohmios y 10 de 100 ohmios.",
        "Un cable USB, un interruptor pequeño, una placa perforada, cable delgado rojo y negro, termocontraíble y estaño.",
        "Para el movimiento: un motorreductor N20 de 6 V y 10 RPM, con su soporte y una rueda para eje de 3 mm.",
        "Y para alimentar todo, un cargador de celular de 5 V y 1 A.",
    ]),
    ("planta", "Medidas y plano", [
        "Ahora, las medidas. La villa mide 32 cm de ancho, 24 de fondo, y unos 28 de alto hasta la punta de la torre.",
        "Un truco muy útil: imprime la foto de la villa a 32 cm de ancho. Así mides cada casa directamente con la regla.",
        "Mira la planta desde arriba. Atrás, en un nivel más alto de 9 cm de fondo, van la casa tudor, la iglesia y la casa del arco.",
        "Adelante a la izquierda va la pista de patinaje: un círculo de 10 cm de diámetro.",
        "En el centro baja el río, desde un puente de piedra hasta el borde.",
        "Y adelante a la derecha va la panadería, con el árbol de Navidad a su lado y el muñeco de nieve en la esquina.",
    ]),
    ("alzado", "Medidas y plano", [
        "Y de frente, estas son las alturas.",
        "La base, con el MDF y el foam, mide 5.5 cm adelante. El nivel de atrás sube 2.5 cm más.",
        "Sobre su nivel, la casa tudor mide 11 cm hasta la punta del techo, la iglesia 12, y la torre 20.",
        "La panadería mide 10 cm, el árbol de Navidad 9, y los pinos entre 6 y 12.",
        "Las figuras miden 3.5 cm, y el muñeco de nieve 4.5.",
    ]),
    ("paso1", "Paso 1 · Base", [
        "Paso 1: la base.",
        "Corta el MDF de 32 por 24 cm y lija los bordes.",
        "Corta el foam de 5 cm del mismo tamaño. El cúter se pasa varias veces, sin forzar, y con la hoja siempre nueva.",
        "De la plancha de 2.5 cm corta una franja de 32 por 9 cm. Ese es el nivel de atrás.",
        "Todavía no pegues nada. Primero vamos a tallar.",
    ]),
    ("paso2", "Paso 2 · Tallar el terreno", [
        "Paso 2: tallar el terreno. Dibuja la planta con plumón sobre el foam.",
        "Para la pista, marca con el compás un círculo de 10 cm y córtalo atravesando todo el foam. Debajo de ese hueco irá el motor.",
        "El río es una canaleta de 2.5 cm de ancho y 8 mm de profundidad, que baja desde el nivel de atrás hasta el borde.",
        "El borde delantero se talla como roca: corta pedazos irregulares, y luego presiona papel aluminio arrugado contra el foam para darle textura.",
        "Ahora voltea el foam. Por debajo, haz canales de 1 cm para los cables, y que todos lleguen al hueco de la pista.",
        "Atrás, abre una ranura para el interruptor y un agujero para el cable USB.",
        "Ahora sí: pega el foam al MDF y el nivel de atrás encima, con cola sintética y mondadientes como clavos. Pon peso encima y deja secar una noche.",
    ]),
    ("paso3", "Paso 3 · Casas", [
        "Paso 3: las casas. Se hacen con cartón pluma de 5 mm.",
        "Cada casa son cuatro paredes: dos frentes con forma de pentágono, que llevan la punta del techo, y dos laterales rectangulares.",
        "Para la casa tudor: dos frentes de 8 cm de ancho, con 7 cm de pared y 11 hasta la punta; y dos laterales de 4 por 7 cm.",
        "Los laterales miden 1 cm menos que el fondo, porque van entre los frentes: es el grosor de los dos cartones.",
        "Dibuja las ventanas y las puertas, y córtalas antes de armar, con el cúter de precisión, de esquina a esquina.",
        "Arma las paredes con silicona y alfileres, y revisa con la escuadra que queden a 90 grados.",
        "Deja las casas abiertas por abajo: por ahí van a entrar las luces. La iglesia, la casa del arco y la panadería se hacen igual, con las medidas de la tabla.",
    ]),
    ("paso4", "Paso 4 · Techos y torres", [
        "Paso 4: techos y torres.",
        "Los techos son dos rectángulos de cartulina gruesa, que sobresalen medio centímetro por cada lado para formar el alero.",
        "La torre grande es una caja de cartón pluma de 3.5 por 3.5 cm y 14 cm de alto.",
        "Su aguja es una pirámide de cartulina: cuatro triángulos de 3.8 cm de base y 6.3 cm de alto.",
        "Únelos con cinta por dentro, y en la punta pon un poco de masilla epóxica para afinarla.",
        "La torre pequeña es igual, pero de 2.5 cm, con una aguja de 3 cm. Las chimeneas son cubitos de foam de 1 cm.",
    ]),
    ("paso5", "Paso 5 · Texturas", [
        "Paso 5: las texturas. Esto es lo que hace que se vea como la de fábrica.",
        "Ladrillos: moja un poco el papel del cartón pluma, despégalo, y raya el foam con un lapicero sin tinta: filas de 4 mm, con cortes cada 8 mm, alternados.",
        "Casa tudor: pega tiras de cartulina de 2 mm de ancho, como vigas de madera, en cruz y en diagonal.",
        "Tejas: tiras de cartulina de 1 cm, con cortes cada 7 mm. Se pegan de abajo hacia arriba, y cada fila tapa la mitad de la anterior.",
        "Los marcos de las ventanas son tiras finas de cartulina, y las barritas de la ventana son tiras de 1 mm.",
        "Los toldos de la panadería son cartulina doblada en ondas, y el letrero es un rectángulo de 4 por 1 cm.",
    ]),
    ("paso6", "Paso 6 · Árboles", [
        "Paso 6: los árboles.",
        "Los pinos se hacen con conos de tecnopor de 6, 9 y 12 cm, de los que venden en librerías.",
        "Clava un palito de brocheta abajo, como tronco, y deja 1 cm afuera para clavarlo en el terreno.",
        "Las ramas se forman con masilla espesa: ponla con la espátula de abajo hacia arriba, jalando hacia abajo, en capas, como faldas.",
        "El árbol de Navidad es un cono de 9 cm. Antes de la masilla, hazle 4 agujeros de 5 mm para los LEDs de colores.",
        "Por el centro del cono, de la punta a la base, abre un túnel con la brocheta: por ahí bajarán los cables.",
        "La estrella se hace con silicona transparente sobre papel encerado, de 2 cm, y se pega sobre el LED de la punta.",
    ]),
    ("paso7", "Paso 7 · Figuras", [
        "Paso 7: las figuras. Puedes comprarlas hechas, en tiendas de nacimientos, o modelarlas con masilla epóxica.",
        "La masilla son dos barras: mezcla partes iguales y amasa hasta que tenga un solo color. Tienes unos 15 minutos para trabajarla.",
        "Para cada patinador, dobla un alambre como un muñequito de palitos de 3.5 cm, y cúbrelo de masilla: el cuerpo, la cabeza, el gorro y la bufanda.",
        "En los pies pega dos trocitos de clip, que son las cuchillas de los patines.",
        "El muñeco de nieve son tres bolitas de 22, 16 y 11 mm, con sombrero de copa, bufanda roja y nariz de zanahoria.",
        "Deja endurecer las figuras una noche antes de pintarlas.",
    ]),
    ("paso8", "Paso 8 · Sellar", [
        "Paso 8: sellar. El foam no se pinta directo, y no acepta pintura en spray: el spray lo derrite.",
        "Mezcla 3 partes de masilla con 1 de cola sintética, y pásala con brocha por todo el terreno y las rocas. Así la superficie queda dura.",
        "En las uniones de las casas, pasa la masilla con el dedo húmedo, para que no se noten.",
        "Cuando seque, lija suave y da una mano de imprimante blanco a todo: casas, techos, árboles y figuras.",
        "Si vas a sacar moldes en la etapa B, este es el momento: antes de pintar.",
    ]),
    ("paso9", "Paso 9 · Pintura", [
        "Paso 9: la pintura. Se usan tres técnicas, siempre en este orden.",
        "Uno, la capa base: el color principal, en dos manos finas.",
        "Dos, la aguada: pintura oscura muy diluida, 1 parte de pintura por 5 de agua, con una gota de lavavajilla. Se mete en las ranuras y marca las sombras.",
        "Tres, el pincel seco: carga el pincel viejo con un color claro, quita casi toda la pintura en un papel, y pásalo rápido por encima. Solo pinta los relieves.",
        "Con estas tres técnicas, los ladrillos, las tejas y las rocas se ven igual que en la pieza de fábrica.",
    ]),
    ("colores", "Paso 9 · Pintura", [
        "Y estos son los colores de cada parte, mirando la original.",
        "Tejas: siena tostada con rojo óxido, y pincel seco terracota.",
        "Iglesia: ladrillo rojo óxido, aguada marrón oscuro, y marcos blancos.",
        "Casa tudor: paredes crema, vigas marrón muy oscuro, y la vitrina con marco rojo.",
        "Panadería: amarillo crema, toldos a rayas rojas y blancas, y el letrero blanco con letras rojas.",
        "Rocas: gris oscuro, con pincel seco gris claro. Puertas: verde oscuro.",
        "Pinos: verde oscuro, con pincel seco verde hoja. Y el árbol de Navidad, verde con escarcha verde y bolitas rojas.",
        "Para las rayas de los toldos, usa cinta de pintor cortada en tiras de 4 mm.",
    ]),
    ("paso10", "Paso 10 · Mecanismo de la pista", [
        "Paso 10: el mecanismo de la pista que gira.",
        "Por dentro va así: abajo el MDF, un taco de madera pegado al MDF, el motor sujeto al costado del taco con su soporte, la rueda en el eje, y encima el disco de la pista.",
        "El disco es de PVC espumado de 3 mm y mide 9.5 cm: medio centímetro menos que el hueco, para que no roce.",
        "Marca el centro exacto del hueco con el compás: ahí debe quedar el eje del motor, apuntando hacia arriba.",
        "A la rueda quítale la llanta de goma, y pega el disco encima con pegamento epóxico, bien centrado.",
        "El disco debe quedar 8 mm por debajo del borde de la pista: antes de apretar los tornillos del soporte, sube o baja el motor hasta lograrlo.",
        "La rueda entra a presión en el eje: así puedes sacar la pista cuando quieras para revisar el motor.",
        "A 5 V, este motor da unas 8 vueltas por minuto. Si lo quieres más lento, ponle en serie una resistencia de 22 a 47 ohmios.",
    ]),
    ("pista", "Paso 10 · Mecanismo de la pista", [
        "Pinta el disco de celeste muy claro, con algunas curvas blancas, como marcas de patines.",
        "Dale 3 manos de barniz brillante, dejando secar cada una. Así parece hielo de verdad.",
        "Pega los patinadores a 3 cm del centro, mirando hacia donde gira el disco.",
        "Alrededor del hueco, haz un murito de masilla de 1 cm de alto, píntalo como piedra y ponle nieve encima.",
    ]),
    ("circuito", "Paso 11 · Electrónica", [
        "Paso 11: la electrónica. Primero entendamos el circuito, que es muy simple.",
        "El cable USB trae dos hilos: el rojo es el positivo, de 5 V, y el negro es el negativo.",
        "El positivo pasa por el interruptor y llega a la placa de distribución, que tiene dos líneas: una positiva y una negativa.",
        "De esas dos líneas salen todas las ramas: cada LED con su resistencia, y el motor.",
        "Todas van en paralelo: por eso, si un LED falla, los demás siguen prendidos.",
        "Es lo mismo que tiene la villa de fábrica; ellos solo usan una placa impresa.",
    ]),
    ("leds", "Paso 11 · Electrónica", [
        "Cada LED necesita una resistencia, o se quema en segundos.",
        "La fórmula es: voltaje de la fuente, menos voltaje del LED, dividido entre la corriente.",
        "Para un LED blanco: 5 menos 3, entre 9 miliamperios, da unos 220 ohmios. Lo mismo para el azul.",
        "Para los RGB de cambio lento, usa 100 ohmios, una por cada LED: si dos comparten la misma resistencia, parpadean mal.",
        "La resistencia de 220 tiene los colores rojo, rojo, marrón. La de 100: marrón, negro, marrón.",
        "Y fíjate en las patas del LED: la larga es la positiva, y el lado plano de la cabeza es el negativo.",
        "Si usas 3 pilas AA en vez de USB, cambia las de 220 por 150 ohmios, y las de 100 por 68.",
    ]),
    ("soldar", "Paso 11 · Electrónica", [
        "Ahora a soldar. Calienta el cautín y limpia la punta en la esponja húmeda.",
        "Corta la pata positiva del LED a 1 cm, tuércela con una pata de la resistencia, y suelda.",
        "Para soldar: apoya el cautín en la unión 2 segundos, acerca el estaño a la unión, no a la punta, y retira. Debe quedar brillante, como una gota.",
        "Al otro extremo de la resistencia suelda un cable rojo, y a la pata negativa un cable negro.",
        "Cubre cada unión con termocontraíble y caliéntalo con la secadora o con el costado del cautín, sin tocarlo.",
        "Cada LED queda con una cola de cables de 30 cm. Haz los 23 y márcalos con cinta de papel: tudor 1, iglesia 2, y así.",
    ]),
    ("probar", "Paso 11 · Electrónica", [
        "Antes de instalar nada, prueba cada LED.",
        "Conecta el cable USB al cargador, y toca los cables del LED: rojo con rojo y negro con negro. Debe prender.",
        "Si no prende, está al revés o la soldadura está mal. Con el multímetro en modo diodo también ves la polaridad.",
        "Prueba también el motor: debe girar suave, sin ruidos raros.",
    ]),
    ("placa", "Paso 11 · Electrónica", [
        "Ahora arma la placa de distribución. Corta la placa perforada a 2.5 por 6 cm, rayándola varias veces con el cúter y quebrándola.",
        "Suelda dos alambres de punta a punta: uno será la línea positiva y el otro la negativa.",
        "Suelda el cable USB: el negro directo a la línea negativa, y el rojo primero al interruptor, y del interruptor a la línea positiva.",
        "Antes de conectar, pon el multímetro en continuidad y toca las dos líneas: no debe sonar. Si suena, hay un cortocircuito.",
        "Opcional: entre el USB y el interruptor, pon un fusible reseteable de 500 miliamperios como protección.",
        "Y haz un nudo en el cable USB por dentro de la base: así, si alguien lo jala, no se arrancan las soldaduras.",
    ]),
    ("paso12", "Paso 12 · Instalar las luces", [
        "Paso 12: instalar las luces. Primero coloca las ventanas por dentro de cada casa, en tres capas.",
        "Mica transparente, que hace de vidrio; celofán amarillo, que da el tono cálido; y albanene, que esparce la luz para que no se vea el puntito del LED.",
        "Pinta el interior de la casa de blanco, para que la luz rebote. Los LEDs de 5 mm van adentro, a 1 cm de las ventanas.",
        "Para los foquitos de la fachada, haz agujeros de 3 mm y mete los LEDs desde adentro, con la cabeza asomando.",
        "En el piso de cada casa, perfora el foam hasta el canal de abajo, pasa los cables, y pega la casa con silicona en su lugar.",
        "El LED azul va escondido bajo el puente, apuntando al río, y los RGB entran en los agujeros del árbol, con los cables por el túnel.",
        "Todos los cables llegan por los canales al hueco de la pista. En la placa, suelda cada rojo a la línea positiva y cada negro a la negativa.",
        "Prende el interruptor y revisa que todo funcione. Luego pega la placa parada contra la pared del hueco, lejos del motor.",
    ]),
    ("paso13", "Paso 13 · Nieve", [
        "Paso 13: la nieve.",
        "La receta: 2 cucharadas de bicarbonato, 1 de cola sintética y 1 cucharadita de pintura blanca. Debe quedar como pasta dental espesa.",
        "Ponla con la espátula en los techos, el suelo y las rocas, con bordes redondeados, como nieve acumulada.",
        "En los aleros, deja que cuelgue un poco: eso hace los bordes chorreados que tiene la original.",
        "El borde de la base lleva la nieve más gruesa: masilla con cola, 3 a 1. Pon una franja de 1 cm y jala con el dedo hacia abajo cada 2 o 3 cm, para formar las gotas.",
        "Mientras todo está húmedo, espolvorea la escarcha iridiscente, y deja secar 24 horas.",
        "Para carámbanos transparentes, deja caer gotas de silicona desde los aleros, jalando la pistola hacia abajo.",
    ]),
    ("paso14", "Paso 14 · Río y hielo", [
        "Paso 14: el agua del río.",
        "Pinta la canaleta de azul oscuro en los bordes y azul claro al centro, con unas líneas blancas, como espuma.",
        "Encima, pon tiras de silicona transparente siguiendo la corriente, y caliéntalas con la secadora para que parezca agua que corre.",
        "Termina con 2 manos de barniz brillante. Con el LED azul debajo del puente, el río brilla igual que en la original.",
    ]),
    ("paso15", "Paso 15 · Montaje final", [
        "Paso 15: el montaje final.",
        "Clava los pinos con su palito y una gota de silicona: los grandes atrás y los pequeños adelante.",
        "Pega el árbol de Navidad, el muñeco de nieve en la esquina de la panadería, y el niño en el nivel de atrás.",
        "Pon la pista: presiona la rueda en el eje hasta el fondo, y gírala con la mano para ver que no roce.",
        "Debajo de la base pega una lámina de fieltro y cuatro patitas de goma.",
        "Y al final, retoca con nieve y escarcha cualquier unión o cable que se vea.",
    ]),
    ("problemas", "Paso 16 · Pruebas", [
        "Paso 16: pruebas. Conecta el cargador, prende el interruptor y deja la villa funcionando una hora.",
        "Si un solo LED no prende, revisa su polaridad y su soldadura.",
        "Si no prende ninguno, mide con el multímetro si llegan 5 V a la placa: puede ser el interruptor o el cable.",
        "Si en una ventana se ve el puntito de luz, agrega otra capa de albanene o aleja el LED.",
        "Si la pista se traba o hace ruido, está rozando: centra el disco o lija el borde del hueco.",
        "Y si el cargador se calienta, desconéctalo: hay un corto. Revisa todo con el multímetro.",
    ]),
    ("etapa_b", "Etapa B · Copias en polirresina", [
        "Etapa B: copias en polirresina, como la fábrica. Esta parte es opcional.",
        "La idea: tu pieza sellada es el modelo original. Le haces un molde de silicona, y en ese molde vacías polirresina todas las veces que quieras.",
        "La fábrica no moldea todo de una vez: hace moldes por partes. La base, cada bloque de casas, los árboles y las figuras van por separado.",
        "Y las piezas con salientes, como los toldos, también se cuelan aparte y se pegan después.",
    ]),
    ("molde", "Etapa B · Copias en polirresina", [
        "Para el molde necesitas caucho de silicona para moldes con su catalizador, una balanza, vasos, palitos y plastilina.",
        "Pega la pieza sobre una tabla con plastilina, sellando todo el borde, y arma alrededor una caja de cartón pluma, con 1 cm de espacio.",
        "Pesa la silicona y agrega el catalizador que indica el envase, normalmente entre 2 y 5 por ciento. Mezcla 2 minutos, raspando el vaso.",
        "Primero pasa una capa fina con pincel sobre la pieza, para que no queden burbujas en los detalles.",
        "Luego vierte el resto en un hilo delgado, desde unos 30 cm de alto, en una esquina de la caja. Así salen las burbujas.",
        "Deja curar 24 horas, desarma la caja y saca la pieza con cuidado. Ese molde sirve para muchas copias.",
    ]),
    ("colado", "Etapa B · Copias en polirresina", [
        "Ahora la polirresina: resina poliéster preacelerada, carbonato de calcio, y el catalizador, que se llama MEKP.",
        "Pesa la resina y agrega el mismo peso de carbonato de calcio. Mezcla hasta que no quede ningún grumo.",
        "Agrega el catalizador: entre 1 y 2 por ciento del peso de la resina, más o menos 1 ml por cada 100 gramos. Mezcla 1 minuto.",
        "Tienes unos 10 a 15 minutos antes de que endurezca, y menos si hace calor.",
        "Las casas deben salir huecas: llena un tercio del molde y gíralo despacio en todas direcciones para cubrir las paredes.",
        "Bota el sobrante y repite 2 o 3 veces, hasta tener 3 a 4 mm de grosor. Los árboles y las figuras se llenan completos.",
        "Desmolda en 1 o 2 horas, cuando esté dura y fría. Lija los bordes, abre las ventanas con el minitaladro, y desde ahí se pinta y se ilumina igual que en la etapa A.",
    ]),
    ("seguridad_resina", "Etapa B · Copias en polirresina", [
        "Muy importante con la resina.",
        "Sus vapores son tóxicos: trabaja al aire libre o con mucha ventilación, y con respirador de filtros para vapores orgánicos.",
        "El catalizador es corrosivo, sobre todo para los ojos: usa siempre lentes y guantes de nitrilo.",
        "Nunca mezcles el catalizador directamente con acelerador de cobalto, porque reaccionan con violencia. Por eso conviene comprar la resina ya preacelerada.",
        "Y no botes resina líquida: deja que endurezca en el vaso y después tírala a la basura.",
    ]),
    ("final", "Final", [
        "Y eso es todo. Repasemos: base y terreno, casas con texturas, árboles y figuras, sellado, pintura, motor, luces, nieve y montaje.",
        "La lista de materiales, las medidas y el circuito están en la guía escrita, en el mismo repositorio que este video.",
        "Si haces tu villa, me encantaría verla. ¡Feliz Navidad!",
    ]),
]

# Imágenes para la guía escrita: escena -> archivo (se capturan con --imagenes)
IMAGENES = {
    "portada": "villa", "planta": "plano-planta", "alzado": "plano-alzado", "paso3": "plantilla-casa",
    "paso4": "techos-torres", "paso10": "mecanismo-pista", "circuito": "circuito", "leds": "led-resistencia",
    "placa": "placa-distribucion", "paso12": "instalacion-luces", "paso13": "nieve", "colores": "colores",
    "molde": "molde-silicona", "colado": "colado-polirresina",
}

# ============================================================== PRONUNCIACIÓN
# Cómo debe sonar cada símbolo o sigla. Solo afecta al audio: los subtítulos
# muestran el texto original. Se aplica en orden.
PRONUNCIACION = [
    (r"(\d+)\.(\d+)", r"\1 punto \2"),
    (r"\b1 A\b", "1 amperio"),
    (r"\b3 pilas AA\b", "3 pilas doble A"),
    (r"\bpilas AA\b", "pilas doble A"),
    (r"(\d) V\b", r"\1 voltios"),
    (r"(\d) W\b", r"\1 uats"),
    (r"(\d) mm\b", r"\1 milímetros"),
    (r"(\d) cm\b", r"\1 centímetros"),
    (r"(\d) ml\b", r"\1 mililitros"),
    (r"\bLEDs\b", "leds"),
    (r"\bLED\b", "led"),
    (r"\bUSB\b", "u ese be"),
    (r"\bRGB\b", "erre ge be"),
    (r"\bMDF\b", "eme de efe"),
    (r"\bPVC\b", "pe ve ce"),
    (r"\bMEKP\b", "eme e ka pe"),
    (r"\bN20\b", "ene veinte"),
    (r"\bRPM\b", "erre pe eme"),
    (r"\bfoam board\b", "fóum bord"),
    (r"\bfoam\b", "fóum"),
    (r"\bdrywall\b", "dráiguol"),
    (r"\btudor\b", "túdor"),
    (r"\bPoxilina\b", "póxilina"),
    (r"\bml\b", "mililitros"),
]


def texto_hablado(texto):
    t = texto
    for patron, dicho in PRONUNCIACION:
        t = re.sub(patron, dicho, t)
    return t.replace("¡", "").replace("\"", "")


# ============================================================== VOZ
def rutas_modelo():
    carpeta = AQUI / "modelos"
    modelo = next((carpeta / n for n in ["kokoro-v1.0.onnx", "kokoro-v1.0.int8.onnx"] if (carpeta / n).exists()), None)
    voces = next((carpeta / n for n in ["voices-v1.0.bin"] if (carpeta / n).exists()), None)
    return modelo, voces


_kokoro = None


def _sintetizar(args):
    global _kokoro
    texto, destino = args
    import soundfile as sf
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        modelo, voces = rutas_modelo()
        _kokoro = Kokoro(str(modelo), str(voces))
    audio, sr = _kokoro.create(texto_hablado(texto), voice=VOZ, speed=VELOCIDAD, lang="es")
    sf.write(str(destino), audio, sr)
    return texto


def preparar_voz():
    """Genera (o reutiliza de la caché) el audio de cada frase. Devuelve {frase: (wav, duración)}."""
    import soundfile as sf
    cache = AQUI / "_voz"
    cache.mkdir(exist_ok=True)
    archivos, pendientes = {}, []
    for _, _, frases in GUION:
        for f in frases:
            clave = hashlib.sha1(f"{VOZ}|{VELOCIDAD}|{texto_hablado(f)}".encode()).hexdigest()[:16]
            ruta = cache / f"{clave}.wav"
            archivos[f] = ruta
            if not ruta.exists() and (f, ruta) not in pendientes:
                pendientes.append((f, ruta))
    if pendientes:
        modelo, voces = rutas_modelo()
        if not modelo or not voces:
            raise SystemExit("Faltan los archivos del modelo Kokoro en video/modelos/ (ver README).")
        print(f"Generando voz para {len(pendientes)} frases...", flush=True)
        with mp.get_context("fork").Pool(max(1, mp.cpu_count())) as pool:
            for i, _ in enumerate(pool.imap_unordered(_sintetizar, pendientes), 1):
                if i % 20 == 0 or i == len(pendientes):
                    print(f"  {i}/{len(pendientes)}", flush=True)
    return {f: (r, sf.info(str(r)).duration) for f, r in archivos.items()}


# ============================================================== LÍNEA DE TIEMPO
def linea_de_tiempo(voz):
    """Duración de cada escena, inicio de cada frase y subtítulos."""
    escenas, t0 = [], 0.0
    pasos = [c for c in dict.fromkeys(c for _, c, _ in GUION)]
    for i, (id_, cap, frases) in enumerate(GUION):
        t, marcas, subs = ENTRADA, [], []
        for f in frases:
            d = voz[f][1] if f in voz else max(2.4, len(f) / 14)
            marcas.append(round(t, 3))
            subs.append([round(t, 3), round(t + d + PAUSA * 0.6, 3), f])
            t += d + PAUSA
        t += COLA
        cuadros = round(t * FPS)
        escenas.append({"i": i, "id": id_, "cap": cap, "frases": frases, "t0": t0, "cuadros": cuadros,
                        "cfg": {"dur": cuadros / FPS, "marcas": marcas, "subs": subs, "cap": cap,
                                "n": pasos.index(cap) + 1, "caps": len(pasos), "t0": t0}})
        t0 += cuadros / FPS
    for e in escenas:
        e["cfg"]["total"] = t0
    return escenas, t0


# ============================================================== RENDER DE ESCENAS
def huella_escenas():
    h = hashlib.sha1()
    for p in sorted((AQUI / "escenas").rglob("*")):
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()[:10]


def abrir(pw, e):
    b = pw.chromium.launch(executable_path=CHROMIUM)
    page = b.new_page(viewport={"width": W, "height": H})
    page.add_init_script(f"window.__CFG = {json.dumps(e['cfg'], ensure_ascii=False)};")
    page.goto(f"file://{ESCENA_HTML}?id={e['id']}")
    page.wait_for_function("window.__listo === true", polling=50, timeout=60000)
    return b, page


def render_escena(args):
    e, destino = args
    from playwright.sync_api import sync_playwright
    tmp = destino.with_suffix(".tmp.mp4")
    with sync_playwright() as pw:
        b, page = abrir(pw, e)
        cdp = page.context.new_cdp_session(page)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                               "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(CRF),
                               "-pix_fmt", "yuv420p", "-r", str(FPS), str(tmp)], stdin=subprocess.PIPE)
        for k in range(e["cuadros"]):
            page.evaluate(f"seek({k / FPS:.4f})")
            datos = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 92, "optimizeForSpeed": True})["data"]
            ff.stdin.write(base64.b64decode(datos))
        ff.stdin.close()
        ff.wait()
        b.close()
    tmp.rename(destino)
    return e["id"]


def capturas(escenas, carpeta, momentos):
    """Guarda PNGs de cada escena en los momentos indicados: momentos(e) -> [(nombre, t)]."""
    from playwright.sync_api import sync_playwright
    carpeta.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        for e in escenas:
            b, page = abrir(pw, e)
            for nombre, t in momentos(e):
                page.evaluate(f"seek({t:.3f})")
                page.screenshot(path=str(carpeta / f"{nombre}.png"))
            b.close()
            print("  ", e["id"], flush=True)


# ============================================================== MÚSICA ("Noche de paz", F. X. Gruber, 1818)
MELODIA = [  # (nota MIDI, corcheas) en 6/8
    (67, 3), (69, 1), (67, 2), (64, 6), (67, 3), (69, 1), (67, 2), (64, 6),
    (74, 4), (74, 2), (71, 6), (72, 4), (72, 2), (67, 6),
    (69, 4), (69, 2), (72, 3), (71, 1), (69, 2), (67, 3), (69, 1), (67, 2), (64, 6),
    (69, 4), (69, 2), (72, 3), (71, 1), (69, 2), (67, 3), (69, 1), (67, 2), (64, 6),
    (74, 4), (74, 2), (77, 3), (74, 1), (71, 2), (72, 6), (76, 6),
    (72, 3), (67, 1), (64, 2), (67, 3), (65, 1), (62, 2), (60, 12),
]
ACORDES = [48, 48, 48, 48, 43, 43, 48, 48, 41, 48, 41, 48, 41, 48, 41, 48, 43, 43, 48, 48, 48, 43, 48, 48]


def caja_musical(segundos, sr=24000):
    import numpy as np
    corchea = 0.36
    vuelta = sum(c for _, c in MELODIA) * corchea
    out = np.zeros(int((segundos + 4) * sr), dtype=np.float32)

    def nota(t, midi, dur, vol, brillo):
        f = 440 * 2 ** ((midi - 69) / 12)
        n = int(min(dur + 1.6, 3.0) * sr)
        x = np.arange(n) / sr
        env = np.exp(-x * (2.6 if brillo else 1.4)) * np.minimum(1, x / 0.004)
        onda = np.sin(2 * np.pi * f * x) + brillo * (0.3 * np.sin(2 * np.pi * 2 * f * x) + 0.12 * np.sin(2 * np.pi * 4.2 * f * x) * np.exp(-x * 6))
        a = int(t * sr)
        b = min(len(out), a + n)
        if a < len(out):
            out[a:b] += (vol * env * onda)[: b - a]

    inicio = 0.0
    while inicio < segundos:
        t = inicio
        for midi, c in MELODIA:
            nota(t, midi + 12, c * corchea, 0.22, 1.0)
            t += c * corchea
        for k, raiz in enumerate(ACORDES):
            nota(inicio + k * 6 * corchea, raiz, 3 * corchea, 0.16, 0.0)
            nota(inicio + (k * 6 + 3) * corchea, raiz + 7, 3 * corchea, 0.09, 0.0)
        inicio += vuelta + 2 * corchea
    # un poco de eco para que suene como una caja musical en una sala
    eco = out.copy()
    for retardo, g in [(0.11, 0.35), (0.23, 0.22), (0.37, 0.12)]:
        d = int(retardo * sr)
        eco[d:] += g * out[:-d]
    return eco[: int(segundos * sr)]


def promedio_movil(x, n):
    """Promedio móvil centrado de n muestras (rápido, con suma acumulada)."""
    import numpy as np
    c = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)])
    a = np.clip(np.arange(len(x)) - n // 2, 0, len(x))
    b = np.clip(np.arange(len(x)) + n // 2, 0, len(x))
    return ((c[b] - c[a]) / np.maximum(1, b - a)).astype(np.float32)


def mezclar_audio(escenas, voz, total, destino):
    import numpy as np
    import soundfile as sf
    sr = 24000
    n = int(total * sr) + sr
    narr = np.zeros(n, dtype=np.float32)
    for e in escenas:
        for f, ini in zip(e["frases"], e["cfg"]["marcas"]):
            audio, _ = sf.read(str(voz[f][0]), dtype="float32")
            a = int((e["t0"] + ini) * sr)
            narr[a:a + len(audio)] += audio[: max(0, n - a)]
    pista = narr.copy()
    if MUSICA:
        musica = caja_musical(n / sr, sr)
        # la música baja cuando habla el narrador y sube en los silencios
        hay_voz = promedio_movil((np.abs(narr) > 0.01).astype(np.float32), int(0.6 * sr))
        ganancia = promedio_movil(np.where(hay_voz > 0.02, 0.10, 0.30).astype(np.float32), int(0.4 * sr))
        fundido = np.minimum(1, np.minimum(np.arange(n) / (2 * sr), (n - np.arange(n)) / (3 * sr)))
        pista += musica[:n] * ganancia * fundido
    pico = float(np.abs(pista).max()) or 1.0
    pista *= min(1.0, 0.92 / pico)
    sf.write(str(destino), pista, sr)


# ============================================================== TEXTOS
def fmt_srt(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def fmt_min(s):
    s = int(s)
    return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def escribir_textos(escenas, total):
    srt, n = [], 1
    for e in escenas:
        for ini, fin, texto in e["cfg"]["subs"]:
            srt.append(f"{n}\n{fmt_srt(e['t0'] + ini)} --> {fmt_srt(e['t0'] + fin)}\n{texto}\n")
            n += 1
    (AQUI / "subtitulos.srt").write_text("\n".join(srt), encoding="utf-8")
    md = ["# Guion del video: Villa navideña animada", "", f"Duración: {fmt_min(total)}", "",
          "## Capítulos (para la descripción de YouTube)", ""]
    vistos = []
    for e in escenas:
        if e["cap"] not in vistos:
            vistos.append(e["cap"])
            md.append(f"{fmt_min(e['t0'])} {e['cap']}")
    md += ["", "## Narración", ""]
    cap = None
    for e in escenas:
        if e["cap"] != cap:
            cap = e["cap"]
            md += ["", f"### {cap}", ""]
        for f, ini in zip(e["frases"], e["cfg"]["marcas"]):
            md.append(f"- `{fmt_min(e['t0'] + ini)}` {f}")
    (AQUI / "guion.md").write_text("\n".join(md) + "\n", encoding="utf-8")


# ============================================================== PRINCIPAL
def main():
    args = sys.argv[1:]
    solo = None
    if "--solo" in args:
        solo = set(args[args.index("--solo") + 1].split(","))
    voz = preparar_voz()
    escenas, total = linea_de_tiempo(voz)
    elegidas = [e for e in escenas if not solo or e["id"] in solo]
    print(f"Duración total: {fmt_min(total)} · {len(escenas)} escenas", flush=True)

    if "--preview" in args:
        def momentos(e):
            ms = e["cfg"]["marcas"]
            ts = [m + 1.8 for m in ms] + [e["cfg"]["dur"] - COLA - 0.1]
            return [(f"{e['i']:02d}_{e['id']}_{k}", min(t, e["cfg"]["dur"] - 0.6)) for k, t in enumerate(ts)]
        capturas(elegidas, AQUI / "preview", momentos)
        return

    if "--imagenes" in args:
        capturas([e for e in elegidas if e["id"] in IMAGENES], AQUI.parent / "imagenes",
                 lambda e: [(IMAGENES[e["id"]], e["cfg"]["dur"] - COLA - 0.1)])
        return

    PARTES.mkdir(exist_ok=True)
    huella = huella_escenas()
    trabajos = []
    for e in escenas:
        clave = hashlib.sha1((huella + json.dumps(e["cfg"], sort_keys=True)).encode()).hexdigest()[:12]
        e["parte"] = PARTES / f"{e['i']:02d}_{e['id']}_{clave}.mp4"
        if not e["parte"].exists():
            trabajos.append((e, e["parte"]))
    trabajos.sort(key=lambda x: -x[0]["cuadros"])
    if trabajos:
        print(f"Renderizando {len(trabajos)} escenas...", flush=True)
        with mp.get_context("spawn").Pool(max(1, mp.cpu_count())) as pool:
            for i, id_ in enumerate(pool.imap_unordered(render_escena, trabajos), 1):
                print(f"  {i}/{len(trabajos)} {id_}", flush=True)

    lista = PARTES / "lista.txt"
    lista.write_text("".join(f"file '{e['parte'].name}'\n" for e in escenas))
    video = PARTES / "video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-c", "copy", str(video)], check=True)
    wav = AQUI / "narracion.wav"
    mezclar_audio(escenas, voz, total, wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav), "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                    str(AQUI / "tutorial.mp4")], check=True)
    escribir_textos(escenas, total)
    print("Listo: tutorial.mp4, subtitulos.srt y guion.md", flush=True)


if __name__ == "__main__":
    main()
