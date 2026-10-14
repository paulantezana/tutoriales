"""Video 1 · Qué vamos a construir: el resultado, la teoría, la arquitectura y el proyecto en el celular."""
from curso import VIDEOS_CURSO

NOMBRE = "01-que-vamos-a-construir"
ETAPA = 1


def guion(D, R):
    SlideHTML, CELESTE, VERDE, AMARILLO = R.SlideHTML, R.CELESTE, R.VERDE, R.AMARILLO
    D.set(mouse=(1500, 700))

    # ---------------------------------------------------------- PORTADA
    D.capitulo("Introducción")
    D.slide(SlideHTML("portada", {
        "num": 1, "total": 9, "titulo": "YARBYS: <span class='acento'>IA en tu celular</span>",
        "sub": "Qué vamos a construir y cómo preparar el proyecto",
        "puntos": [["play", "Ver el resultado final"], ["brain", "Entender cómo funciona por dentro"],
                   ["layers", "Conocer la arquitectura del código"], ["si_flutter", "Crear el proyecto y ejecutarlo en tu celular"]],
        "resultado": "La app corriendo en tu celular", "icono": "smartphone"}), frases=[
        "Hola, ¿qué tal? Bienvenidos a este curso. Vamos a crear YARBYS: nuestro propio asistente de inteligencia artificial, que vive cien por ciento dentro del celular.",
        "En este primer video vas a ver el resultado final, vas a entender cómo funciona por dentro, y vamos a preparar el proyecto en Flutter.",
        "Y al terminar este video ya vas a tener la app corriendo en tu celular. Así que, vamos.",
    ])

    # ---------------------------------------------------------- RESULTADO FINAL
    D.capitulo("El resultado final")
    D.celular("resultado", ("smartphone", "Resultado final", "YARBYS <span class='acento'>en acción</span>"), [
        ("decir", "Este es YARBYS en mi celular, así queda al final del curso. Y fíjate en algo: está en modo avión. No hay internet."),
        ("nota", "plane", "Modo avión: sin internet", VERDE),
        ("decir", "Le pregunto qué tengo el miércoles."),
        ("preguntar", "¿Qué tengo el miércoles?", R.R_MIERCOLES, ["agenda.txt"], {"habla": True}),
        ("nota", "file-text", "Respondió con mi agenda.txt", AMARILLO),
        ("decir", "Respondió con mi agenda, que le enseñé antes, y me dice de qué documento sacó la información. Ahora le hablo con el micrófono."),
        ("preguntar", "¿Y cómo se llama mi perro?", R.R_PERRO, ["perfil.txt"], {"voz": True, "habla": True}),
        ("nota", "mic", "Me entendió por voz", CELESTE),
        ("decir", "Me entendió por voz y me respondió hablando. Y todo esto ocurre dentro del teléfono: el modelo de inteligencia artificial, la base de datos y la memoria."),
        ("nota", "brain", "Gemma 4 corre dentro del celular", CELESTE),
    ], inicial=[("tema", "final"), ("etapa", 8), ("debug", False), ("avion", True), ("pantalla", "chat")])

    # ---------------------------------------------------------- TEMARIO
    D.capitulo("El plan del curso")
    D.slide(SlideHTML("temario", {"videos": [list(v) for v in VIDEOS_CURSO], "actual": 1}), frases=[
        "El curso tiene nueve videos, y vamos a avanzar poco a poco. En cada video agregamos una pieza, y siempre terminamos con algo funcionando.",
        "Primero haremos que Gemma responda en la consola, sin ninguna pantalla. Luego le hacemos un chat sencillo, le damos memoria, y le enseñamos a leer tus documentos.",
        "Después le agregamos la voz, la dejamos bonita con su núcleo animado, y al final generamos el APK para instalarlo en cualquier celular.",
    ])

    # ---------------------------------------------------------- TEORÍA
    D.capitulo("¿IA en el celular?")
    D.slide(SlideHTML("ia_celular"), frases=[
        "Antes de programar, un poco de teoría. Cuando usas ChatGPT, tu pregunta viaja por internet hasta un centro de datos lleno de computadoras gigantes. Allí se genera la respuesta, y vuelve a tu teléfono.",
        "En YARBYS es distinto. El modelo de inteligencia artificial es un archivo que descargamos una sola vez, y que vive dentro del celular. El procesador del teléfono hace todo el trabajo.",
        "Eso tiene grandes ventajas: tus datos nunca salen del teléfono, funciona sin internet, no pagas por cada pregunta y no esperas a ningún servidor.",
        "¿Las desventajas? El modelo es más pequeño que los de la nube, ocupa espacio, y usa la memoria RAM y la batería. Por eso elegiremos un modelo pensado para celulares.",
    ])
    D.capitulo("Las 5 piezas")
    D.slide(SlideHTML("piezas"), frases=[
        "Para construir a YARBYS necesitamos cinco piezas, y todas viven dentro del celular.",
        "Un cerebro, que es el modelo de lenguaje: Gemma 4. Y un traductor de textos a números: EmbeddingGemma.",
        "Un buscador de información, que es la base de datos vectorial Qdrant Edge. Y una memoria para las conversaciones: SQLite.",
        "Y la voz, para escuchar y hablar. Flutter será el cuerpo: la app que une todas las piezas. Cada pieza la vamos a explicar en detalle en su propio video.",
    ])
    D.capitulo("La arquitectura")
    D.slide(SlideHTML("mapa", {"explicar": True, "kicker": "La arquitectura", "titulo": "Tres capas, y cada una con <span class='acento'>una tarea</span>"}), frases=[
        "Ahora, ¿cómo vamos a ordenar el código? En tres capas. Arriba, las pantallas: lo que ve el usuario. Inicio, el chat y tus documentos.",
        "En el medio, la clase Yarbys: el asistente. Recibe tu pregunta y coordina a todos los demás para responderla.",
        "Y abajo, los servicios. Cada uno hace una sola cosa: modelos descarga la inteligencia artificial, cerebro habla con Gemma, memoria guarda las conversaciones, conocimiento busca en tus documentos, y voz escucha y habla.",
        "Y hay una regla importante: las pantallas solo hablan con Yarbys, nunca directamente con Gemma o con la base de datos. Gracias a eso, cada pieza la podemos probar primero en la consola, y después conectarla a la pantalla.",
    ])
    D.capitulo("Flutter")
    D.slide(SlideHTML("flutter"), frases=[
        "Y el cuerpo de YARBYS es Flutter, el framework de Google para crear apps. Con un solo código, en lenguaje Dart, tienes tu app para Android y para iPhone.",
        "En Flutter todo es un widget: un texto, un botón, una lista. Y los combinamos como bloques de Lego para armar cada pantalla.",
        "Las piezas de inteligencia artificial las agregamos con paquetes de pub.dev, la tienda de librerías de Flutter. Las iremos instalando a medida que las necesitemos.",
    ])
    D.capitulo("Instalación")
    D.slide(SlideHTML("instalacion"), frases=[
        "Pasemos a la instalación en Windows. Primero, Flutter: lo descargas desde flutter.dev, lo descomprimes, por ejemplo, en C:\\flutter, y agregas la carpeta bin al PATH.",
        "Segundo, Android Studio. Trae el Android SDK, que es lo que necesitamos para compilar apps de Android.",
        "Tercero, Visual Studio Code con la extensión de Flutter. Y cuarto, tu celular Android con la depuración USB activada.",
        "Para activarla: en Ajustes, Acerca del teléfono, toca siete veces Número de compilación. Luego, en Opciones de desarrollador, activa Depuración USB, y conecta el celular a la computadora con el cable.",
    ])

    # ---------------------------------------------------------- CREAR EL PROYECTO
    D.s = R.Estado()
    D.set(mouse=(1200, 640), raiz="PROYECTOS")
    D.capitulo("Crear el proyecto")
    D.say("Con todo instalado, abrimos Visual Studio Code. Yo abrí la carpeta C:\\proyectos con File, Open Folder. Y abrimos la terminal con Control + comilla invertida.")
    D.wait(2.5)
    D.abrir_terminal()
    D.hold()
    D.say("Primero revisamos que todo esté bien instalado con flutter doctor.")
    D.comando("flutter doctor")
    D.salida("Doctor summary (to see all details, run flutter doctor -v):", R.BLANCO, 0.6)
    for item in ["Flutter (Channel stable, 3.47.7, on Microsoft Windows, locale es-PE)",
                 "Windows Version (Windows 11 or higher)",
                 "Android toolchain - develop for Android devices (Android SDK version 36.1.0)",
                 "Chrome - develop for the web", "Android Studio (version 2025.2)", "VS Code (version 1.105)",
                 "Connected device (3 available)", "Network resources"]:
        D.salida_segs([("[√] ", R.G), (item, R.BLANCO)], 0.35)
    D.salida("", R.BLANCO, 0.1)
    D.salida_segs([("• No issues found!", R.G)], 0.3)
    D.fin_comando()
    D.hold()
    D.say("Si todo sale con un check verde, estamos listos. Fíjate en Connected device: ahí aparece el celular conectado por USB.", esperar=True)
    D.say("Ahora creamos el proyecto con flutter create. Con --org ponemos el identificador de nuestra empresa, y con --platforms indicamos que la app será para Android y para iPhone.")
    D.comando("flutter create --org com.paulantezana --platforms android,ios yarbys")
    for linea, p in [("Creating project yarbys...", 0.8), ("Resolving dependencies in `yarbys`...", 0.9),
                     ("Downloading packages...", 1.0), ("Got dependencies in `yarbys`.", 0.3), ("Wrote 75 files.", 0.3),
                     ("", 0.1), ("All done!", 0.2), ("In order to run your application, type:", 0.1), ("", 0.05),
                     ("  $ cd yarbys", 0.05), ("  $ flutter run", 0.05), ("", 0.05),
                     ("Your application code is in yarbys\\lib\\main.dart.", 0.2)]:
        D.salida(linea, R.BLANCO, p)
    D.set(carpetas={"yarbys"})
    D.fin_comando()
    D.hold()
    D.say("Listo. Ahora abrimos la carpeta yarbys con File, Open Folder.", esperar=True)
    D.abrir_proyecto(0)
    D.set(abiertas=frozenset({"lib", "test"}))
    D.abrir_terminal()
    D.say("Este es un proyecto de Flutter. Las carpetas android e ios tienen la configuración de cada sistema. En lib va nuestro código en Dart, y pubspec.yaml es como la lista de compras del proyecto: ahí van los paquetes que usamos.", esperar=True)

    # ---------------------------------------------------------- LA APP DE EJEMPLO
    D.capitulo("La app de ejemplo")
    D.say("flutter create nos dejó una app de ejemplo en lib, main.dart. Vamos a leerla juntos, porque así se arma cualquier app de Flutter.")
    D.abrir_desde_explorador("lib/main.dart")
    D.hold()
    D.resaltar("void main() {", "}", titulo="main()", nota="Lo primero que se ejecuta\nrunApp: muestra el widget en la pantalla",
               frases=["Todo empieza en la función main: es lo primero que se ejecuta. Y runApp toma un widget, MyApp, y lo muestra en la pantalla."])
    D.resaltar("class MyApp extends StatelessWidget", "home: const MyHomePage", titulo="MyApp",
               nota="StatelessWidget: no cambia\nMaterialApp: título, colores y primera pantalla",
               frases=["MyApp es un StatelessWidget: un widget que no cambia. Su método build devuelve un MaterialApp, que define el título de la app, los colores, y en home, la primera pantalla."])
    D.resaltar("class MyHomePage extends StatefulWidget", "createState()", titulo="MyHomePage",
               nota="StatefulWidget: tiene datos que cambian\nsu estado vive en _MyHomePageState",
               frases=["MyHomePage, en cambio, es un StatefulWidget: tiene datos que cambian con el tiempo. Esos datos viven en otra clase, su estado: _MyHomePageState."])
    D.resaltar("int _counter = 0;", "_counter++;", titulo="setState", nota="Cambia el dato y le avisa a Flutter\nque vuelva a dibujar la pantalla",
               frases=["El estado guarda un contador. Y fíjate en setState: cambia el dato y le avisa a Flutter que vuelva a dibujar la pantalla. Esta idea la vamos a usar muchísimo."])
    D.resaltar("return Scaffold(", "title: Text(widget.title),", titulo="Scaffold",
               frases=["Y build arma la pantalla con bloques: un Scaffold, que es la página, con una AppBar arriba, que muestra el título."])
    D.resaltar("body: Center(", "child: const Icon(Icons.add),", titulo="Bloques de Lego",
               nota="Center › Column › Text\nFloatingActionButton: el botón +",
               frases=["En el cuerpo, un Center con una columna de textos, y el botón flotante con el signo más, que al tocarlo llama a _incrementCounter."])

    # ---------------------------------------------------------- ANDROID
    D.capitulo("Configurar Android")
    D.say("Antes de ejecutarla, dos ajustes de Android. Abrimos android, app, build.gradle.kts.")
    D.abrir_desde_explorador("android/app/build.gradle.kts")
    D.hold()
    c = D.codigo("android/app/build.gradle.kts", ETAPA)
    D.cambiar(c, c.viejas_rango("minSdk = flutter.minSdkVersion"), c.rango("// Gemma 4 necesita", "minSdk = 30"),
              "Gemma necesita Android 11 o superior, que es la versión 30 de la API. Así que cambiamos minSdk por 30, con un comentario que explica por qué.",
              titulo="minSdk = 30", nota="La versión mínima de Android: 11")
    D.guardar()
    D.terminar(c)
    D.say("Y en android, app, src, main, abrimos AndroidManifest.xml.")
    D.abrir_desde_explorador("android/app/src/main/AndroidManifest.xml")
    D.hold()
    c = D.codigo("android/app/src/main/AndroidManifest.xml", ETAPA)
    D.cambiar(c, c.viejas_rango('android:label="yarbys"'), c.rango('android:label="YARBYS"'),
              "Aquí cambiamos el nombre que se ve debajo del ícono: YARBYS, en mayúsculas.",
              titulo="android:label", nota="El nombre debajo del ícono")
    D.guardar()
    D.terminar(c)

    # ---------------------------------------------------------- EJECUTAR
    D.capitulo("Ejecutar en el celular")
    D.say("Ahora sí, a ejecutarla. Con el celular conectado, abrimos main.dart y presionamos F5. Abajo a la derecha, en la barra de estado, se ve el dispositivo elegido: mi Pixel 8.")
    D.abrir_desde_explorador("lib/main.dart")
    D.hold()
    D.depurar()
    D.say("La primera vez tarda un poco: Flutter compila la app, la instala en el celular, y conecta el depurador. Todo lo que pase se ve aquí abajo, en la Debug Console.", esperar=True)
    D.celular("contador", ("smartphone", "Paso 1 · Probar", "La app de ejemplo <span class='acento'>en el celular</span>"), [
        ("decir", "Y ahí está, en mi celular. Esta es la app de ejemplo de Flutter. Si toco el botón más, el contador sube."),
        ("toque", "fab"), ("ev", "contador", 1), ("esperar", 0.5), ("toque", "fab"), ("ev", "contador", 2),
        ("esperar", 0.5), ("toque", "fab"), ("ev", "contador", 3),
        ("nota", "mouse-pointer-click", "setState redibuja el número", CELESTE),
        ("decir", "Cada toque llama a setState, y Flutter vuelve a dibujar el número. Fíjate también en la cinta que dice DEBUG: estamos en modo depuración."),
    ], inicial=[("tema", "contador"), ("pantalla", "contador"), ("debug", True)])

    D.capitulo("Hot reload")
    D.say("Ahora, la magia de Flutter: el hot reload. Con la app corriendo, cambio el título de la pantalla.")
    c = D.codigo("lib/main.dart", ETAPA)
    D.cambiar(c, c.viejas_rango("home: const MyHomePage(title: 'Flutter Demo Home Page'),"),
              c.rango("home: const MyHomePage(title: 'Hola, soy YARBYS'),"),
              "En lugar de Flutter Demo Home Page, escribo: Hola, soy YARBYS.", titulo="El título")
    D.say("Y guardo con Control + S.")
    D.guardar()
    D.recargar()
    D.terminar(c)
    D.hold()
    D.celular("hola", ("zap", "Hot reload", "El cambio aparece <span class='acento'>al instante</span>"), [
        ("decir", "Y el cambio aparece en el celular al instante, sin volver a compilar, y sin perder el contador, que sigue en tres."),
        ("nota", "zap", "Hot reload: el cambio en menos de un segundo", AMARILLO),
        ("decir", "Así vamos a trabajar todo el curso: escribimos, guardamos, y vemos el resultado de inmediato."),
    ], inicial=[("tema", "contador"), ("pantalla", "contador"), ("debug", True), ("contador", 3),
                ("contador_titulo", "Hola, soy YARBYS")])
    D.detener()

    # ---------------------------------------------------------- CIERRE
    D.capitulo("Lo que sigue")
    D.slide(SlideHTML("siguiente", {
        "num": 1, "logros": ["Viste el resultado final y cómo funciona por dentro", "Conoces la arquitectura en tres capas",
                             "Creaste el proyecto y lo configuraste para Android", "La app corre en tu celular, con hot reload"],
        "sig": {"num": 2, "titulo": "Gemma responde, en la consola", "sub": "Descargamos Gemma 4 y le hacemos su primera pregunta, sin ninguna pantalla todavía."}}), frases=[
        "Y listo. En este video viste el resultado final, entendiste cómo funciona, y ya tienes el proyecto corriendo en tu celular.",
        "En el próximo video empieza lo bueno: descargamos Gemma 4, escribimos su cerebro, y le hacemos su primera pregunta, todavía sin pantalla, mirando la respuesta en la consola. ¡Nos vemos en el siguiente video!",
    ])
