"""Video 2 · Gemma responde, en la consola: modelos.dart, cerebro.dart y la primera respuesta en la Debug Console."""
NOMBRE = "02-gemma-en-consola"
ETAPA = 2

R_QUIEN = ("Soy YARBYS, un asistente que vive dentro de tu celular. "
           "Puedo responder tus preguntas sin necesidad de internet.")


def guion(D, R):
    SlideHTML, CELESTE, VERDE, AMARILLO = R.SlideHTML, R.CELESTE, R.VERDE, R.AMARILLO
    D.set(mouse=(1500, 700))

    # ---------------------------------------------------------- PORTADA Y DÓNDE ESTAMOS
    D.capitulo("Introducción")
    D.slide(SlideHTML("portada", {
        "num": 2, "total": 9, "titulo": "Gemma responde, <span class='acento'>en la consola</span>",
        "sub": "El cerebro de YARBYS, todavía sin pantalla",
        "puntos": [["download", "Descargar Gemma 4 desde Hugging Face"], ["brain", "Escribir el cerebro: cerebro.dart"],
                   ["bug", "Probarlo en la consola y con el depurador"]],
        "resultado": "La respuesta de Gemma en la Debug Console, sin internet", "icono": "terminal"}), frases=[
        "Hola, ¿qué tal? Bienvenidos al video dos del curso de YARBYS.",
        "Hoy vamos a descargar Gemma 4, vamos a escribir el cerebro de YARBYS, y lo vamos a probar en la consola y con el depurador.",
        "Al final de este video, Gemma va a responder su primera pregunta dentro del celular, y sin internet.",
    ])
    D.slide(SlideHTML("mapa", {"hechos": [], "hoy": ["modelos", "cerebro"]}), frases=[
        "En el video anterior creamos el proyecto y lo ejecutamos en el celular. Recuerda la arquitectura: pantallas arriba, Yarbys en el medio, y los servicios abajo.",
        "Hoy escribimos dos servicios: modelos, que descarga Gemma, y cerebro, que habla con ella. Todavía sin pantallas: primero probamos que funcione, y la pantalla viene en el próximo video.",
    ])

    # ---------------------------------------------------------- TEORÍA
    D.capitulo("¿Qué es un LLM?")
    D.slide(SlideHTML("llm"), frases=[
        "Empecemos por el cerebro: el LLM, o modelo de lenguaje grande. Es una inteligencia artificial que aprendió a escribir leyendo muchísimo texto: libros, páginas web y conversaciones.",
        "Funciona como el autocompletado del teclado de tu celular, pero mucho más inteligente. Divide el texto en pedacitos llamados tokens, y calcula cuál es el siguiente token más probable.",
        "Así, token por token, va escribiendo la respuesta. Por eso, en el código, la respuesta nos va a llegar en pedacitos.",
        "Todo lo que el modelo aprendió se guarda en miles de millones de números, llamados parámetros. Más parámetros suele significar más inteligencia, pero también un archivo más pesado.",
    ])
    D.capitulo("Modelos para celular")
    D.slide(SlideHTML("tamanos"), frases=[
        "Los modelos de la nube tienen cientos de miles de millones de parámetros. Necesitan centros de datos enormes: no caben en un teléfono.",
        "Pero existen modelos pequeños, diseñados para celulares. Y además se comprimen con una técnica llamada cuantización: cada número se guarda con menos bits, como cuando comprimes una foto.",
        "Nosotros usaremos Gemma 4 E2B, de Google. Es gratuito, entiende muy bien el español, y su archivo pesa 2.6 gigas. Lo ejecutaremos con LiteRT-LM, el motor de Google para correr modelos en celulares.",
        "Para usarlo, tu celular necesita Android 11 o superior y, de preferencia, 8 gigas de RAM. Con 6 también funciona, pero más lento.",
    ])

    # ---------------------------------------------------------- PAQUETES
    D.abrir_proyecto(1)
    D.capitulo("Instalar el paquete")
    D.say("Para ejecutar Gemma en Flutter necesitamos un paquete. Los paquetes se buscan en pub.dev, así que abrimos el navegador.")
    D.wait(1.5)
    D.navegador_abrir()
    D.navegador_ir("pub.dev", "pub_inicio")
    D.hold()
    D.say("En el buscador escribimos flutter_edge_ai.")
    D.navegador_escribir("busqueda", "flutter_edge_ai")
    D.navegador_enter("pub.dev/packages?q=flutter_edge_ai", "pub_busqueda")
    D.hold()
    D.say("Y abrimos el primer resultado.")
    D.navegador_clic("resultado", "pub.dev/packages/flutter_edge_ai", "pub_paquete")
    D.hold()
    D.navegador_marcar("titulo", 0.4)
    D.say("Esta es la página del paquete. Dice qué hace: ejecuta modelos de inteligencia artificial dentro del dispositivo, sin servidor. Vamos a la pestaña Installing.", esperar=True)
    D.navegador_clic("instalar", "pub.dev/packages/flutter_edge_ai/install", "pub_instalar")
    D.navegador_marcar("comando", 0.4)
    D.say("Aquí está el comando para instalarlo. Junto con él instalamos su motor, flutter_edge_ai_litertlm, que es el que ejecuta los archivos de Gemma.", esperar=True)
    D.navegador_cerrar()
    D.abrir_terminal()
    D.say("Volvemos a VS Code y, en la terminal, los agregamos con flutter pub add.")
    D.comando("flutter pub add flutter_edge_ai flutter_edge_ai_litertlm")
    D.salida("Resolving dependencies...", R.BLANCO, 1.2)
    D.salida("Downloading packages...", R.BLANCO, 1.0)
    for p, v in [("flutter_edge_ai", "2.3.3"), ("flutter_edge_ai_litertlm", "1.13.3")]:
        D.salida_segs([("+ ", R.G), (f"{p} {v}", R.BLANCO)], 0.15)
    D.salida("Changed 23 dependencies!", R.BLANCO, 0.2)
    D.set(files={**D.s.files, "pubspec.yaml": R.curso.contenido("pubspec.yaml", ETAPA)})
    D.fin_comando()
    D.hold()
    D.abrir_desde_explorador("pubspec.yaml")
    D.resaltar("flutter_edge_ai:", "flutter_edge_ai_litertlm:", titulo="dependencies",
               nota="flutter pub add los anotó aquí\n^2.3.3: esa versión o una compatible",
               frases=["flutter pub add los anotó en pubspec.yaml, en dependencies. El símbolo del sombrerito significa: esta versión, o una más nueva que sea compatible."])

    D.capitulo("Permiso de internet")
    D.say("Y como la app va a descargar el modelo, en el AndroidManifest le damos permiso de usar internet.")
    D.abrir_desde_explorador("android/app/src/main/AndroidManifest.xml")
    D.hold()
    c = D.codigo("android/app/src/main/AndroidManifest.xml", ETAPA)
    D.poner(c, c.rango("<!-- Internet", "android.permission.INTERNET"),
            "Agregamos uses-permission INTERNET, con un comentario: solo lo usamos para descargar los modelos. Después, YARBYS funciona sin internet.",
            titulo="uses-permission", nota="INTERNET: solo para descargar los modelos")
    D.guardar()
    D.terminar(c)

    # ---------------------------------------------------------- LOS ARCHIVOS
    D.capitulo("Los archivos de hoy")
    D.set(term_abierto=False)
    D.say("Ahora creamos los archivos de hoy. En lib, una carpeta servicios, que es la capa de abajo de la arquitectura. Dentro, modelos.dart: el que descarga los modelos de inteligencia artificial.")
    D.nuevo_archivo("lib/servicios/modelos.dart")
    D.hold()
    D.say("Y cerebro.dart: el que le pasa el texto a Gemma y nos devuelve su respuesta.")
    D.nuevo_archivo("lib/servicios/cerebro.dart")
    D.hold()

    # ---------------------------------------------------------- modelos.dart
    D.capitulo("modelos.dart")
    D.abrir_desde_explorador("lib/servicios/modelos.dart")
    c = D.codigo("lib/servicios/modelos.dart", ETAPA)
    D.ficha("modelos.dart", "Descarga Gemma 4 una sola vez. Después, todo funciona sin internet.", [
        ("clase", "Modelos", "Todo lo de los modelos, en un solo lugar"),
        ("constante", "urlGemma", "Dónde descargar Gemma 4"),
        ("getter", "listos", "¿Ya está en el celular?"),
        ("método", "descargarGemma()", "Descarga Gemma 4 y avisa el porcentaje"),
    ])
    D.say("Empezamos por modelos.dart. A la derecha tienes el mapa de este archivo: una clase, Modelos, con la dirección de Gemma, una propiedad para saber si ya está descargada, y un método para descargarla.", esperar=True)
    D.ficha_ocultar()
    D.poner(c, c.rango("import 'package:flutter_edge_ai") + [c.j("import 'package:flutter_edge_ai") + 1],
            "Primero importamos flutter_edge_ai, el paquete que acabamos de instalar. import nos deja usar el código de otro archivo o paquete.",
            titulo="import")
    D.poner(c, c.rango("/// Los modelos de IA", "class Modelos {") + [len(c.nuevas) - 2],
            "Ahora la clase Modelos, con un comentario arriba que dice qué hace. Los comentarios con tres barras son de documentación: VS Code los muestra cuando pasas el mouse sobre la clase.",
            titulo="class Modelos", nota="Una clase agrupa datos y funciones\nde un mismo tema")
    D.ficha_explicar(1, "Primero necesitamos la dirección de Gemma 4. ¿De dónde la sacamos?")
    D.ficha_ocultar()
    D.slide(SlideHTML("hf", {"nombre": "Gemma 4 E2B", "busqueda": "gemma-4-E2B-it-litert-lm", "cuenta": "litert-community",
                             "repo": "gemma-4-E2B-it-litert-lm", "version": "main", "version_txt": "la versión más reciente",
                             "archivo": "gemma-4-E2B-it.litertlm", "peso": "2.6 GB",
                             "nota": "Si el enlace copiado termina en ?download=true, puedes quitar esa parte"}), frases=[
        "Los modelos abiertos se publican en Hugging Face, la plataforma donde Google y otras empresas comparten sus modelos.",
        "Entras a huggingface.co, buscas gemma-4-E2B-it-litert-lm y abres el modelo de la cuenta litert-community. En la pestaña Files and versions está el archivo gemma-4-E2B-it.litertlm, de 2.6 gigas. Haces clic derecho en su botón de descarga y copias la dirección del enlace.",
        "Fíjate en las partes del enlace: el sitio, quién lo publica, el nombre del modelo, la palabra resolve, que significa descargar, la versión, que aquí es main, la más reciente, y el nombre del archivo.",
    ])
    D.poner(c, c.rango("// El cerebro (LLM)", "gemma-4-E2B-it.litertlm';"),
            "Volvemos a VS Code. Escribimos un comentario, y la constante urlGemma. static significa que pertenece a la clase: la usamos como Modelos.urlGemma, sin crear objetos. Y const, que nunca cambia. La dirección no la escribimos a mano: la pegamos.",
            titulo="static const urlGemma", nota="static: se usa como Modelos.urlGemma\nconst: un valor que nunca cambia")
    D.poner(c, [c.j("/// ¿Ya está descargado?") - 1] + c.rango("/// ¿Ya está descargado?", "static bool get listos"),
            "Luego listos: un getter, que es una propiedad calculada. Devuelve un bool, verdadero o falso, según si Gemma ya está en el celular. La flecha devuelve el resultado de hasActiveModel.",
            titulo="get listos", nota="get: se usa como una variable\n=> devuelve el resultado directamente")
    firma = c.firma("static Future<void> descargarGemma")
    D.poner(c, [firma[0] - 1] + firma,
            "Y el método descargarGemma. Recibe progreso: una función a la que le iremos avisando el porcentaje. Future de void significa que termina más tarde y no devuelve nada, y async, que adentro podemos esperar con await.",
            titulo="descargarGemma(progreso)", nota="Future<void>: termina más tarde\nasync: adentro usamos await")
    D.poner(c, c.rango("await FlutterEdgeAi.installModel(", "fileType: ModelFileType.litertlm,"),
            "Adentro, installModel prepara la instalación. Le decimos qué modelo es, Gemma 4, para que sepa cómo hablarle, y que el archivo es .litertlm, el formato del motor LiteRT-LM.",
            titulo="installModel", nota="modelType: gemma4\nfileType: litertlm")
    D.poner(c, c.rango(").fromNetwork(urlGemma)"),
            "Y encadenamos tres pasos: fromNetwork, que lo baje de nuestra dirección; withProgress, que nos avise el porcentaje; e install, que lo descarga y lo instala. Con await esperamos a que termine.",
            titulo="Descargar", nota="fromNetwork → withProgress → install")
    D.guardar()
    D.terminar(c)
    for k in range(4):
        D.ficha_hecho(k)
    D.ficha_ver(None)
    D.say("Y modelos.dart está listo.", esperar=True)
    D.ficha_ocultar()

    # ---------------------------------------------------------- cerebro.dart
    D.capitulo("cerebro.dart")
    D.abrir_desde_explorador("lib/servicios/cerebro.dart")
    c = D.codigo("lib/servicios/cerebro.dart", ETAPA)
    D.ficha("cerebro.dart", "El cerebro: le pasa un texto a Gemma y devuelve su respuesta, token por token.", [
        ("clase", "Cerebro", "Habla con Gemma 4"),
        ("constante", "_personalidad", "Las reglas de YARBYS"),
        ("método", "responder(prompt)", "Devuelve la respuesta en pedacitos"),
    ])
    D.say("Ahora cerebro.dart. Tiene una clase, Cerebro, con la personalidad de YARBYS, y un método, responder.", esperar=True)
    D.ficha_ocultar()
    D.poner(c, [0, 1], "Importamos flutter_edge_ai otra vez, porque aquí también lo usamos.")
    D.poner(c, c.rango("/// El cerebro de YARBYS", "class Cerebro {") + [len(c.nuevas) - 2],
            "Creamos la clase Cerebro, con su comentario.", titulo="class Cerebro")
    D.poner(c, c.rango("// La personalidad", "'Si no sabes algo, lo dices.';"),
            "Primero la personalidad: las reglas que Gemma va a seguir en toda la conversación. Le decimos quién es, que responda en español, en máximo tres oraciones y sin markdown, es decir, sin asteriscos ni listas. El guion bajo al inicio del nombre la hace privada: solo se usa dentro de este archivo.",
            titulo="_personalidad", nota="Las instrucciones de sistema\n_ al inicio: privada (solo este archivo)")
    firma = c.firma("static Stream<String> responder")
    D.poner(c, [firma[0] - 2, firma[0] - 1] + firma,
            "Ahora el método responder. Recibe el prompt: el texto que va a leer Gemma. Y devuelve un Stream de String: no una respuesta completa, sino un flujo de pedacitos de texto que llegan uno tras otro. async con asterisco es lo que nos deja ir entregando esos pedacitos.",
            titulo="Stream<String>", nota="Un flujo: los tokens llegan uno por uno\nasync*: entrega valores con yield")
    D.poner(c, c.rango("final modelo = await FlutterEdgeAi.getActiveModel"),
            "Primero cargamos Gemma en la memoria del celular. getActiveModel nos da el modelo que descargamos. maxTokens, 4096, es el contexto: cuánto texto puede leer Gemma de una vez, sumando la pregunta y la respuesta. Y await espera a que cargue, porque tarda unos segundos.",
            titulo="getActiveModel", nota="maxTokens: 4096 → el contexto\nawait: espera a que cargue")
    D.poner(c, c.rango("final chat = await modelo.createChat(", "    );"),
            "Con el modelo creamos una conversación. systemInstruction es la personalidad que escribimos arriba, y maxOutputTokens, 512, el largo máximo de la respuesta.",
            titulo="createChat", nota="systemInstruction: la personalidad\nmaxOutputTokens: 512 → largo máximo")
    t, f = c.j("    try {"), c.j("    } finally {")
    D.poner(c, [t, f, f + 1, f + 2],
            "Ahora un try con finally. Lo que va en finally se ejecuta siempre, aunque algo falle. Ahí cerramos el chat con close, para liberar la memoria del celular.",
            titulo="try / finally", nota="finally se ejecuta siempre\nclose: libera la memoria")
    D.poner(c, c.rango("await chat.addQueryChunk"),
            "Dentro del try le enviamos el prompt con addQueryChunk. Message es un mensaje, e isUser true le dice a Gemma que lo escribió la persona.",
            titulo="addQueryChunk", nota="isUser: true → lo escribió la persona")
    D.poner(c, c.rango("await for (final r in chat.generateChatResponseAsync())", "      }"),
            "Y aquí la magia. generateChatResponseAsync empieza a generar la respuesta, y await for recorre cada pedacito apenas llega: es un for que espera. Gemma puede devolver distintos tipos de respuesta; nos quedamos con las de texto. Y yield entrega ese token a quien llamó a responder, sin esperar al resto.",
            titulo="await for + yield", nota="await for: recorre el flujo mientras llega\nyield: entrega cada token")
    D.guardar()
    D.terminar(c)
    for k in range(3):
        D.ficha_hecho(k)
    D.ficha_ver(None)
    D.say("El cerebro está listo. Ahora, ¿cómo lo probamos si todavía no tenemos pantalla? Con la consola.", esperar=True)
    D.ficha_ocultar()

    # ---------------------------------------------------------- main.dart: la prueba
    D.capitulo("Probar en main.dart")
    D.borrar_archivo("test/widget_test.dart",
                     "Como vamos a reemplazar la app de ejemplo, primero borramos su prueba, test, widget_test.dart, que ya no nos sirve.")
    D.hold()
    D.abrir_desde_explorador("lib/main.dart")
    c = D.codigo("lib/main.dart", ETAPA)
    D.vaciar(c, "Abrimos main.dart y borramos la app de ejemplo: Control + A y Suprimir.")
    D.hold()
    D.poner(c, c.rango("import 'package:flutter/material.dart';", "flutter_edge_ai_litertlm.dart';") + [3],
            "Importamos material, que trae los widgets de Flutter, flutter_edge_ai, y su motor LiteRT-LM.")
    D.poner(c, c.rango("import 'servicios/cerebro.dart';", "import 'servicios/modelos.dart';") + [6],
            "Y nuestros dos archivos: cerebro y modelos.")
    firma = c.firma("Future<void> main() async {")
    D.poner(c, firma, "La función main ahora es async, porque adentro vamos a esperar con await.",
            titulo="main() async")
    D.poner(c, c.rango("  runApp(", "  );"),
            "Primero, runApp con una pantalla mínima: un texto en el centro que dice Mira la consola. Solo para que el celular no quede en blanco.",
            titulo="Una pantalla mínima")
    D.poner(c, c.rango("// El motor que ejecuta Gemma", "await FlutterEdgeAi.initialize") + [c.j("// El motor que ejecuta Gemma") - 1],
            "Luego encendemos el motor de inteligencia artificial con initialize, y le decimos que use LiteRtLmEngine: el motor que ejecuta los archivos .litertlm.",
            titulo="initialize", nota="LiteRtLmEngine: ejecuta Gemma 4")
    D.poner(c, [c.j("// Prueba: descargamos Gemma") - 1] + c.rango("// Prueba: descargamos Gemma", "  }"),
            "Ahora la prueba. Si Gemma todavía no está en el celular, la descargamos, y en cada aviso de progreso imprimimos el porcentaje con debugPrint. debugPrint escribe en la consola de depuración.",
            titulo="debugPrint", nota="Escribe en la Debug Console\n!Modelos.listos: si NO está descargada")
    D.poner(c, c.rango("debugPrint('Pregunta: ¿Quién eres?');"),
            "Imprimimos la pregunta...", marcar=False)
    D.poner(c, c.rango("final respuesta = await Cerebro.responder"),
            "...le preguntamos al cerebro quién es, y con join juntamos todos los tokens del flujo en un solo texto.",
            titulo="join()", nota="Junta todos los tokens en un texto")
    D.poner(c, c.rango("debugPrint('YARBYS: $respuesta');"),
            "Y lo imprimimos en la consola.")
    D.guardar()
    D.terminar(c)

    # ---------------------------------------------------------- EJECUTAR
    D.capitulo("Resultado: la consola")
    D.say("Momento de la verdad. Presionamos F5.")
    D.depurar()
    D.say("La primera vez, la app descarga los 2.6 gigas de Gemma. Aquí lo aceleré: según tu internet, puede tardar varios minutos. Usa Wi-Fi.")
    for p in range(0, 101):
        D.consola(f"Descargando Gemma: {p}%", app=True, pausa=1 / 30 if p % 10 else 0.12)
    D.hold()
    D.consola("Pregunta: ¿Quién eres?", app=True, pausa=0.3)
    D.say("Ya descargó. Ahora Gemma se carga en la memoria y empieza a pensar... y...", esperar=True)
    D.wait(1.0)
    D.consola(f"YARBYS: {R_QUIEN}", app=True, pausa=0.5)
    D.say("¡Ahí está! La primera respuesta de Gemma, generada dentro del celular.", esperar=True)

    D.capitulo("El depurador")
    D.say("Ahora, otra forma de ver lo que pasa: el depurador. Hago clic a la izquierda del número de línea, en el último debugPrint, y aparece un punto rojo: un punto de parada.")
    lin = D.punto_de_parada("debugPrint('YARBYS: $respuesta');")
    D.hold()
    D.say("Y reinicio la app con Control + Shift + F5. Esta vez Gemma ya está en el celular, así que no descarga nada.")
    D.reiniciar()
    D.hold()
    D.consola("Pregunta: ¿Quién eres?", app=True, pausa=1.8)
    D.pausar_en(lin)
    D.say("La app se detuvo en el punto de parada: la línea amarilla todavía no se ejecutó.", esperar=True)
    D.say("Si paso el mouse sobre la variable respuesta, VS Code me muestra lo que tiene adentro: el texto completo que generó Gemma.")
    D.mostrar_valor("respuesta", f"\"{R_QUIEN}\"")
    D.hold()
    D.say("Así puedes revisar cualquier variable mientras la app corre. Continúo con F5.")
    D.continuar()
    D.consola(f"YARBYS: {R_QUIEN}", app=True, pausa=0.4)
    D.hold()
    D.clic(R.ED_X + 16, R.ED_Y + (lin - D.s.scroll.get(D.s.activo, 0)) * R.LH + R.LH / 2)
    D.set(punto=None)
    D.wait(0.3)

    D.capitulo("Sin internet")
    D.celular("avion", ("plane", "La prueba", "Gemma <span class='acento'>sin internet</span>"), [
        ("decir", "Y la prueba final: en el celular, que solo muestra Mira la consola, activo el modo avión."),
        ("ev", "avion", True), ("nota", "plane", "Modo avión activado", VERDE),
        ("decir", "Y vuelvo a reiniciar la app desde VS Code."),
    ], inicial=[("tema", "basico"), ("pantalla", "consola"), ("debug", True)])
    D.reiniciar()
    D.consola("Pregunta: ¿Quién eres?", app=True, pausa=2.2)
    D.consola(f"YARBYS: {R_QUIEN}", app=True, pausa=0.5)
    D.say("Y Gemma sigue respondiendo, sin internet. Todo ocurre dentro del celular.", esperar=True)
    D.detener()

    # ---------------------------------------------------------- CIERRE
    D.capitulo("Lo que sigue")
    D.slide(SlideHTML("siguiente", {
        "num": 2, "logros": ["Instalaste flutter_edge_ai desde pub.dev", "modelos.dart descarga Gemma 4 desde Hugging Face",
                             "cerebro.dart responde token por token", "Lo probaste en la consola y con el depurador, sin internet"],
        "sig": {"num": 3, "titulo": "Primer chat", "sub": "Una pantalla para hablar con Gemma, donde la respuesta aparece palabra por palabra."}}), frases=[
        "Y listo. Hoy instalamos el paquete, descargamos Gemma, escribimos su cerebro, y lo probamos en la consola y con el depurador. Gemma ya responde dentro del celular.",
        "Pero leer la consola no es muy cómodo. En el próximo video le hacemos su primera pantalla: un chat sencillo, donde vas a escribir tu pregunta y ver la respuesta aparecer palabra por palabra. ¡Nos vemos!",
    ])
