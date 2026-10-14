# Guion de narración

Lee cada frase en voz alta en el momento indicado. Los tiempos coinciden con `tutorial.mp4`.
El video ya trae esta narración con voz generada (Kokoro). Si prefieres grabar tu propia voz, pon `NARRACION = False` en `render.py` y graba siguiendo estos tiempos.


## Introducción

- **0:00** — Hola, ¿qué tal? Bienvenidos. Hoy vamos a crear YARBYS: nuestro propio asistente de inteligencia artificial que vive cien por ciento dentro del celular.
- **0:09** — Lee tus documentos, recuerda tus conversaciones y te habla. Y lo mejor: funciona sin internet, incluso en modo avión.
- **0:16** — Lo haremos con Flutter, paso a paso y explicando cada concepto desde cero. Si nunca programaste con inteligencia artificial, este video es para ti.

## Resultado final

- **0:27** — Antes de empezar, mira el resultado final. Este es YARBYS en mi celular. Y fíjate en algo: está en modo avión, no hay internet.
- **0:35** — Le pregunto qué tengo el miércoles.
- **0:49** — Respondió con mi agenda, que guardé en la app, y además me dice de qué documento sacó la información. Ahora le hablo con el micrófono.
- **1:10** — Me entendió por voz y me respondió hablando. Y todo esto ocurre dentro del teléfono: el modelo de inteligencia artificial, la base de datos y la memoria.

## ¿IA en el celular?

- **1:20** — Primero, un poco de teoría. Cuando usas ChatGPT, tu pregunta viaja por internet hasta un centro de datos lleno de computadoras gigantes. Allí se genera la respuesta, y vuelve a tu teléfono.
- **1:32** — En YARBYS es distinto. El modelo de inteligencia artificial es un archivo que descargamos una sola vez, y que vive dentro del celular. El procesador del teléfono hace todo el trabajo.
- **1:43** — Eso tiene grandes ventajas: tus datos nunca salen del teléfono, funciona sin internet, no pagas por cada pregunta y no esperas a ningún servidor.
- **1:52** — ¿Las desventajas? El modelo es más pequeño que los de la nube, ocupa espacio, y usa la memoria RAM y la batería. Por eso elegiremos un modelo pensado para celulares.

## Las 5 piezas

- **2:03** — Para construir a YARBYS necesitamos cinco piezas, y todas viven dentro del celular.
- **2:09** — Un cerebro, que es el modelo de lenguaje: Gemma 4. Y un traductor de textos a números: EmbeddingGemma.
- **2:15** — Un buscador de información, que es la base de datos vectorial Qdrant Edge. Y una memoria para las conversaciones: SQLite.
- **2:23** — Y la voz, para escuchar y hablar. Flutter será el cuerpo: la app que une todas las piezas, y que funciona en Android y en iPhone.

## ¿Qué es un LLM?

- **2:31** — Empecemos por el cerebro: el LLM, o modelo de lenguaje grande. Es una inteligencia artificial que aprendió a escribir leyendo muchísimo texto: libros, páginas web y conversaciones.
- **2:43** — Funciona como el autocompletado del teclado de tu celular, pero mucho más inteligente. Divide el texto en pedacitos llamados tokens, y calcula cuál es el siguiente token más probable.
- **2:54** — Así, token por token, va escribiendo la respuesta. Por eso, en la app, verás que la respuesta aparece poco a poco.
- **3:01** — Todo lo que el modelo aprendió se guarda en miles de millones de números, llamados parámetros. Más parámetros suele significar más inteligencia, pero también un archivo más pesado.

## Modelos para celular

- **3:13** — Los modelos de la nube tienen cientos de miles de millones de parámetros. Necesitan centros de datos enormes: no caben en un teléfono.
- **3:21** — Pero existen modelos pequeños, diseñados para celulares. Y además se comprimen con una técnica llamada cuantización: cada número se guarda con menos bits, como cuando comprimes una foto.
- **3:32** — Nosotros usaremos Gemma 4 E2B, de Google. Es gratuito, entiende muy bien el español, y su archivo pesa 2.6 gigas. Lo ejecutaremos con LiteRT-LM, el motor de Google para correr modelos en celulares.
- **3:46** — Para usarlo, tu celular necesita Android 11 o superior y, de preferencia, 8 gigas de RAM. Con 6 también funciona, pero más lento. Y unos 3 gigas libres.

## Embeddings

- **3:57** — Ahora, ¿cómo encuentra YARBYS la información correcta dentro de tus documentos? Con embeddings.
- **4:03** — Un embedding convierte un texto en una lista de números, llamada vector. EmbeddingGemma 2, que también es de Google y pesa solo 165 megas, genera 768 números por cada texto.
- **4:15** — Lo genial es que los textos con significado parecido quedan cerca, como en un mapa: la agenda por un lado, tu mascota por otro, tus gustos por otro.
- **4:24** — Entonces, la pregunta '¿Qué tengo el miércoles?' queda justo al lado de 'Miércoles: entregar el proyecto', aunque usen palabras distintas.

## Fragmentos

- **4:33** — Pero antes de crear los embeddings, cortamos cada documento en fragmentos. ¿Por qué? Porque un solo vector para un documento enorme mezclaría demasiadas ideas.
- **4:43** — Lo cortamos en pedazos de unos 800 caracteres, sin partir los párrafos. Y cada fragmento tendrá su propio vector.

## Qdrant Edge

- **4:52** — Esos vectores los guardamos en una base de datos vectorial. Es como una biblioteca que ordena los textos por su significado, y no por orden alfabético.
- **5:01** — Usaremos Qdrant Edge: la misma tecnología de Qdrant, una de las bases vectoriales más usadas, pero en una versión que corre dentro de la app, sin servidor.
- **5:10** — Cuando haces una pregunta, Qdrant la compara con todos los fragmentos y te devuelve los más parecidos, cada uno con un puntaje de similitud.

## RAG

- **5:20** — Juntando estas piezas tenemos la técnica más usada para crear asistentes con inteligencia artificial: RAG, que en español significa generación aumentada por recuperación.
- **5:31** — Primero llega tu pregunta. La convertimos en vector con EmbeddingGemma, y buscamos en Qdrant los tres fragmentos más parecidos.
- **5:39** — Luego armamos un mensaje para Gemma con esos fragmentos, la conversación reciente y tu pregunta. A ese mensaje lo llamamos prompt.
- **5:48** — Y Gemma responde usando tus propios datos. Así no se inventa las cosas.

## Memoria

- **5:54** — La siguiente pieza es la memoria. Un LLM, por sí solo, no recuerda nada. Cada pregunta es como hablar con alguien que te acaba de conocer.
- **6:03** — Por eso guardamos cada conversación, a la que llamamos hilo, en SQLite: una base de datos que es un solo archivo dentro de la app. Tendremos una tabla de hilos y otra de mensajes.
- **6:14** — Y en cada pregunta le enviamos a Gemma los últimos seis mensajes. Así puede seguir la conversación.

## La voz

- **6:21** — Para la voz usamos los motores que ya trae el celular. Uno convierte tu voz en texto, y otro lee el texto en voz alta. En Flutter los usamos con dos paquetes: speech_to_text y flutter_tts.
- **6:33** — En la mayoría de celulares también funcionan sin internet, si tienes descargado el idioma español.

## Flutter

- **6:41** — Y el cuerpo de YARBYS es Flutter, el framework de Google para crear apps. Con un solo código, en lenguaje Dart, tienes tu app para Android y para iPhone.
- **6:50** — En Flutter todo es un widget: un texto, un botón, una lista. Y los combinamos como bloques de Lego para armar cada pantalla.
- **6:57** — Las piezas de inteligencia artificial las agregamos con paquetes de pub.dev, la tienda de librerías de Flutter. El principal será flutter_edge_ai, que ejecuta Gemma dentro del celular.

## Arquitectura

- **7:10** — Este es el plan completo, y todo ocurre dentro del celular.
- **7:14** — Las pantallas, hechas con Flutter, le pasan tu pregunta a nuestros servicios: memoria, conocimiento, voz y cerebro.
- **7:21** — Conocimiento busca en Qdrant con EmbeddingGemma, memoria lee el historial en SQLite, y cerebro le pregunta a Gemma 4.
- **7:29** — Internet solo se usa una vez, para descargar los modelos desde Hugging Face. Y, si el usuario quiere, para conectarse a un LLM externo como GPT-6 Luna o Claude Haiku. Pero eso es opcional.

## Instalación

- **7:42** — Pasemos a la instalación en Windows. Primero, Flutter: lo descargas desde flutter.dev, lo descomprimes, por ejemplo, en C:\flutter, y agregas la carpeta bin al PATH.
- **7:53** — Segundo, Android Studio. Trae el Android SDK, que es lo que necesitamos para compilar apps de Android.
- **8:00** — Tercero, Visual Studio Code con la extensión de Flutter. Y cuarto, tu celular Android con la depuración USB activada.
- **8:07** — Para activarla: en Ajustes, Acerca del teléfono, toca siete veces Número de compilación. Luego, en Opciones de desarrollador, activa Depuración USB, y conecta el celular a la computadora con el cable.

## Paso 1 · Crear el proyecto

- **8:21** — Con todo instalado, abrimos Visual Studio Code. Yo abrí la carpeta C:\proyectos con File, Open Folder. Y abrimos la terminal con Control + comilla invertida.
- **8:32** — Primero revisamos que todo esté bien instalado con flutter doctor.
- **8:36** — Si todo sale con un check verde, estamos listos. Ahora creamos el proyecto con flutter create.
- **8:43** — Con --org ponemos el identificador de nuestra empresa, y con --platforms indicamos que la app será para Android y para iPhone.
- **8:52** — Listo. Ahora abrimos la carpeta yarbys con File, Open Folder.

## 

- **8:57** — Este es un proyecto de Flutter. Las carpetas android e ios tienen la configuración de cada sistema. En lib va nuestro código en Dart, y pubspec.yaml es como la lista de compras del proyecto: ahí van los paquetes que usamos.

## Paso 2 · Paquetes

- **9:10** — Ahora los paquetes. Los paquetes de Flutter se buscan en pub.dev, así que abrimos el navegador.
- **9:16** — En el buscador escribimos flutter_edge_ai.
- **9:20** — Y abrimos el primer resultado.
- **9:23** — Esta es la página del paquete. Aquí dice qué hace, en qué plataformas funciona y cómo se usa. flutter_edge_ai es el que ejecuta Gemma dentro del celular. Vamos a la pestaña Installing.
- **9:36** — Aquí está el comando para instalarlo: flutter pub add flutter_edge_ai.
- **9:41** — Junto con él usaremos tres complementos de la misma familia: flutter_edge_ai_litertlm, el motor que ejecuta los modelos, y flutter_edge_ai_rag y flutter_edge_ai_qdrant, para la búsqueda con Qdrant Edge. Cada uno tiene su página en pub.dev y se instala igual.
- **9:58** — Volvemos a VS Code y, en la terminal, agregamos los cuatro juntos con flutter pub add.
- **10:09** — Y después el resto: sqflite para SQLite, path_provider para las carpetas, file_picker para elegir archivos, flutter_secure_storage para guardar la API key, http, y los dos paquetes de voz.
- **10:23** — Fíjate que flutter pub add los anotó en pubspec.yaml. flutter_edge_ai y su motor LiteRT-LM ejecutan Gemma en el celular, y los paquetes rag y qdrant nos dan la búsqueda con Qdrant Edge.

## Paso 3 · Configurar Android

- **10:36** — Ahora configuramos Android. Abrimos android, app, build.gradle.kts.
- **10:42** — Gemma necesita Android 11 o superior, que es la versión 30 de la API. Cambiamos minSdk por 30.
- **10:50** — Y en android, app, src, main, abrimos AndroidManifest.xml: ahí van los permisos de la app.
- **10:56** — Agregamos el permiso de internet, para descargar los modelos, y el del micrófono, para hablar con YARBYS.
- **11:10** — Cambiamos el nombre visible de la app a YARBYS, en mayúsculas.
- **11:14** — Y en la sección queries avisamos que usaremos el reconocimiento de voz y la lectura en voz alta del sistema.
- **11:27** — Para iPhone necesitas una Mac con Xcode; te dejo los pasos en el README del repositorio.

## Paso 4 · Los archivos

- **11:33** — Antes de escribir código, vamos a crear todos los archivos del proyecto, y te explico para qué sirve cada uno. Así tendrás el mapa completo en la cabeza.
- **11:42** — En lib creamos la carpeta servicios, que es la lógica de YARBYS: no se ve en la pantalla, pero hace todo el trabajo. El primero es modelos.dart, que descarga los dos modelos de inteligencia artificial.
- **11:54** — memoria.dart guarda las conversaciones en SQLite.
- **11:59** — conocimiento.dart aprende tus documentos y busca en ellos con Qdrant.
- **12:05** — cerebro.dart arma el prompt y le pregunta a Gemma.
- **12:10** — voz.dart escucha tu voz y lee las respuestas en voz alta.
- **12:14** — Y ajustes.dart guarda las preferencias del usuario y su API key.
- **12:19** — En la carpeta widgets va nucleo.dart, el círculo animado de YARBYS. Un widget es una pieza visual que podemos reutilizar.
- **12:27** — tema.dart tiene los colores de la app.
- **12:31** — Y en la carpeta pantallas, lo que ve el usuario: inicio, que descarga los modelos,
- **12:36** — chat, la pantalla principal,
- **12:41** — documentos, para agregar tus archivos,
- **12:46** — y ajustes.
- **12:51** — Este es el mapa del proyecto. main.dart ya existía: es el punto de partida, y lo dejaremos para el final.
- **12:58** — Y cada archivo lo escribiremos siempre en el mismo orden: primero para qué sirve, luego sus clases, luego sus métodos, y al final lo que hace cada método por dentro.

## Paso 5 · modelos.dart

- **13:09** — Empezamos por modelos.dart. A la derecha tienes el mapa de este archivo: una clase, Modelos, con dos direcciones web, una propiedad para saber si los modelos ya están descargados, y dos métodos para descargarlos.
- **13:22** — Primero escribimos la estructura: la clase y los métodos, todavía vacíos.
- **13:36** — Una clase es como un molde que agrupa datos y funciones. Modelos solo agrupa funciones; por eso todo será static: lo usamos sin crear objetos, por ejemplo Modelos.descargarGemma.
- **13:48** — descargarEmbeddings recibe una función, progreso, a la que le avisaremos el porcentaje de la descarga. Es async porque descargar toma tiempo, y así la app no se congela mientras espera.
- **14:00** — descargarGemma es igual, pero para Gemma 4. Future<void> significa que el método termina más tarde y no devuelve ningún valor.
- **14:08** — Ahora necesitamos las direcciones de los modelos. ¿De dónde las sacamos?
- **14:12** — Los modelos abiertos se publican en Hugging Face, la plataforma donde Google y otras empresas comparten sus modelos.
- **14:20** — Entras a huggingface.co, buscas gemma-4-E2B-it-litert-lm y abres el modelo de la cuenta litert-community. En la pestaña Files and versions está el archivo gemma-4-E2B-it.litertlm, de 2.6 gigas. Haces clic derecho en su botón de descarga y copias la dirección del enlace.
- **14:38** — Fíjate en las partes del enlace: el sitio, quién lo publica, el nombre del modelo, la palabra resolve, que significa descargar, la versión, que aquí es main, la más reciente, y el nombre del archivo.
- **14:51** — Volvemos a VS Code y creamos la constante urlGemma. La dirección no la escribimos a mano: la pegamos.
- **15:00** — Para EmbeddingGemma es igual: buscas embeddinggemma-2-text-270m-litert-lm y copias el enlace del archivo .litertlm, de 165 megas.
- **15:11** — Pero hay un detalle. En vez de main, usamos un código de versión exacta, llamado commit. Así, si algún día publican otro archivo con el mismo nombre, YARBYS sigue usando exactamente el mismo modelo.
- **15:23** — ¿Y qué código usamos? El que recomienda la documentación del paquete. Vamos a verla.
- **15:35** — En la página de flutter_edge_ai_litertlm, en la sección EmbeddingGemma 2...
- **15:41** — ...está el código de versión, en la constante revision, y debajo el enlace del modelo, escrito en tres partes.
- **15:47** — Para tener la dirección completa, juntamos las tres partes y cambiamos signo de dólar revision por ese código. O, más fácil: en Hugging Face, en el historial de versiones del modelo, abres esa versión y copias el enlace de descarga del archivo, igual que con Gemma.
- **16:03** — Y lo pegamos en la constante urlEmbeddings.
- **16:14** — Ahora listos: nos dice si los dos modelos ya están en el celular, para no descargarlos otra vez.
- **16:27** — La flecha devuelve el resultado directamente. hasActiveModel revisa Gemma, hasActiveEmbedder revisa EmbeddingGemma, y con el doble ampersand, los dos tienen que estar listos.
- **16:38** — Implementamos descargarEmbeddings.
- **16:48** — installEmbedder prepara la instalación del modelo de embeddings, modelFromNetwork le dice que lo baje de nuestra URL, withModelProgress nos avisa el porcentaje, e install lo descarga. Con await esperamos a que termine.
- **17:02** — Y descargarGemma.
- **17:14** — installModel es lo mismo para el LLM. modelType le dice a la librería que es Gemma 4, y fileType, que es un archivo .litertlm, el formato del motor LiteRT-LM.
- **17:28** — Y modelos.dart está completo.

## Paso 6 · memoria.dart

- **17:32** — Seguimos con memoria.dart. Tendrá cuatro clases: tres pequeñas que representan los datos —un mensaje, un hilo o conversación, y un documento—, y la clase Memoria, que los guarda y los lee de SQLite.
- **17:44** — Escribimos la estructura. Las tres clases de datos son cortas: solo tienen sus campos y un constructor.
- **17:59** — Mensaje tiene tres campos: el rol, que dice quién habló, el texto, y las fuentes. final significa que no cambian después de crearse. La línea de arriba es el constructor: la forma de crear un mensaje.
- **18:12** — Y esUsuario es un getter: una propiedad calculada que nos dice si el mensaje lo escribió el usuario.
- **18:18** — Hilo es una conversación, con su id y un título.
- **18:22** — Y Documento guarda el nombre del archivo y en cuántos fragmentos lo cortamos.
- **18:27** — La clase Memoria guarda la conexión con la base de datos en _db. El guion bajo la hace privada: solo se usa dentro de este archivo.
- **18:36** — abrir abre la base de datos al arrancar la app.
- **18:39** — Y estos métodos trabajan con los hilos: listarlos, borrar uno o borrarlos todos.
- **18:45** — mensajes lee los mensajes de un hilo.
- **18:48** — Implementamos abrir.
- **18:57** — Armamos la ruta del archivo yarbys.db, dentro de la carpeta de la app, y openDatabase lo abre. Si no existe, lo crea.
- **19:07** — onCreate se ejecuta solo la primera vez. Con el lenguaje SQL creamos las tablas: hilos, con cada conversación, y mensajes, donde cada mensaje guarda el id del hilo al que pertenece. La tabla documentos es igual.
- **19:22** — Ahora los hilos. nuevoHilo crea una conversación con insert, que agrega una fila a la tabla, y devuelve su id.
- **19:30** — hilos los lee todos con query, del más nuevo al más viejo, y convierte cada fila en un Hilo.
- **19:40** — borrarHilo borra sus mensajes y luego el hilo.
- **19:43** — Y borrarTodo vacía las dos tablas.
- **19:46** — guardar inserta un mensaje en la tabla mensajes. Las fuentes las unimos con una barra vertical, porque SQLite guarda texto.
- **20:00** — Y mensajes es el que le da memoria a YARBYS.
- **20:10** — Pide los mensajes del hilo del más nuevo al más viejo, y con limit solo los últimos. Luego los volteamos con reversed para leerlos en orden, y convertimos cada fila en un Mensaje.
- **20:21** — Los métodos de documentos son iguales a los de hilos; los pego.
- **20:30** — Memoria lista.

## Paso 7 · conocimiento.dart

- **20:33** — Sigue conocimiento.dart: aquí vive el RAG. La clase Conocimiento guarda tus documentos en Qdrant y busca en ellos.
- **20:49** — _indice es el índice de Qdrant, donde están los vectores. late significa que le daremos valor más tarde, en abrir.
- **20:57** — _perfil identifica el tipo de vectores que crea EmbeddingGemma 2. Qdrant lo guarda para no mezclar vectores de modelos distintos.
- **21:05** — fragmentar recibe un texto y devuelve una lista de fragmentos.
- **21:10** — aprender recibe el nombre y el texto de un documento, y devuelve cuántos fragmentos guardó.
- **21:16** — Y buscar recibe la pregunta y devuelve los fragmentos más parecidos.
- **21:20** — Implementamos abrir.
- **21:31** — FlutterEdgeAiRag es el sistema de RAG, y le decimos que guarde los vectores con Qdrant Edge.
- **21:39** — Abrimos el índice en una carpeta de la app, y le indicamos que EmbeddingGemma será quien convierta los textos en vectores.
- **21:47** — fragmentar es un poco más largo; lo pego y lo explicamos.
- **21:52** — Separamos el texto por párrafos y los vamos juntando hasta llegar a unos 800 caracteres. Cuando no cabe uno más, guardamos el fragmento y empezamos otro.
- **22:04** — Y si un párrafo solo ya es muy largo, lo cortamos en el último espacio antes del límite, para no partir una palabra.
- **22:12** — Ahora aprender.
- **22:22** — Fragmentamos el texto y anotamos el documento en SQLite. Luego, por cada fragmento, add crea su vector con EmbeddingGemma y lo guarda en Qdrant, junto con el nombre del documento.
- **22:35** — Y flush guarda los cambios en el disco.
- **22:39** — olvidar hace lo contrario: borra los fragmentos del documento. Lo pego.
- **22:44** — Y buscar.
- **22:53** — search convierte la pregunta en vector y nos devuelve los tres fragmentos más parecidos. threshold descarta los que se parecen muy poco.
- **23:03** — origen lee el nombre del documento desde los datos que guardamos con el fragmento.
- **23:09** — Conocimiento listo.

## Paso 8 · cerebro.dart

- **23:12** — Llegamos al cerebro. La clase Cerebro tiene la personalidad de YARBYS y los métodos para armar el prompt y responder.
- **23:28** — armarPrompt recibe la pregunta, los fragmentos encontrados, y el historial de la conversación, y devuelve el texto completo que leerá Gemma.
- **23:37** — responder devuelve un Stream: un flujo de datos que llega en pedacitos. Así recibimos la respuesta token por token.
- **23:44** — _local responde con Gemma, dentro del celular. async con asterisco significa que va entregando valores poco a poco.
- **23:52** — Y _externo usa un LLM de internet. Es opcional.
- **23:56** — Primero la personalidad: las instrucciones de sistema.
- **24:11** — Le decimos quién es, que responda en español, en máximo tres oraciones y sin formato, porque las respuestas se leen en voz alta.
- **24:19** — Ahora armarPrompt.
- **24:30** — StringBuffer va juntando texto. Primero escribimos los fragmentos de tus documentos, luego la conversación reciente, y al final la pregunta. Exactamente lo que vimos en la parte de RAG.
- **24:42** — responder elige el cerebro.
- **24:48** — Si el usuario activó la nube, usa el LLM externo; si no, Gemma en el celular. Ese signo de pregunta es un if en una sola línea.
- **24:57** — Y _local, la parte más importante.
- **25:08** — getActiveModel carga Gemma en la memoria. maxTokens es cuánto texto puede leer a la vez: el contexto. Y createChat crea la conversación con la personalidad y un máximo de 512 tokens de respuesta.
- **25:23** — Le enviamos el prompt, y con yield entregamos cada token apenas Gemma lo genera. Al final, en finally, cerramos el chat.
- **25:31** — La parte del LLM externo es opcional. La pego y te explico lo importante.
- **25:37** — La API key la escribe cada usuario en la app; nunca va escrita en el código.
- **25:44** — Con el paquete http enviamos el mismo prompt a Anthropic, para Claude Haiku, o a OpenAI, para GPT-6 Luna. El resto de la app no cambia.
- **25:54** — Y _leer convierte la respuesta en datos, o lanza un error si algo falló.
- **25:59** — El cerebro está completo.

## Paso 9 · voz.dart y ajustes.dart

- **26:03** — Ahora la voz. La clase Voz tiene un oído, que convierte tu voz en texto, y una boca, que lee en voz alta.
- **26:18** — _oido es un SpeechToText y _boca un FlutterTts: vienen de los dos paquetes de voz que instalamos.
- **26:25** — alDejarDeEscuchar es una función que la pantalla del chat nos dará, para avisarle cuando el micrófono se apague.
- **26:32** — escuchar recibe la función alOir, a la que le pasaremos el texto mientras hablas, y devuelve false si no hay permiso de micrófono.
- **26:39** — Implementamos escuchar; lo pego y lo vemos por partes.
- **26:44** — La primera vez, initialize prepara el reconocimiento de voz y pide el permiso del micrófono. Y si el celular está en español, usamos su idioma.
- **26:55** — listen escucha, nos va pasando el texto mientras hablas, y termina cuando te quedas en silencio tres segundos.
- **27:03** — dejarDeEscuchar apaga el micrófono.
- **27:08** — Y hablar.
- **27:20** — La primera vez configuramos la boca en español, y le pedimos que espere a terminar de hablar. Luego speak lee el texto.
- **27:28** — Y callar la detiene.
- **27:35** — Y ajustes.dart guarda las preferencias.
- **27:47** — _cofre es un FlutterSecureStorage: guarda los datos cifrados, en Android con Keystore y en iPhone con Keychain. Ideal para la API key.
- **27:55** — Estas son las preferencias. usarNube empieza en false: por defecto, YARBYS es cien por ciento local.
- **28:02** — Y esPro es el interruptor de la versión Pro. Aquí conectarías una compra dentro de la app; en este proyecto viene desbloqueada.
- **28:10** — cargar lee el cofre al arrancar la app.
- **28:22** — readAll lee todo el cofre, y cada preferencia toma su valor. El doble signo de pregunta pone un valor por defecto si todavía no se guardó nada.
- **28:32** — guardar escribe cada valor; lo pego.
- **28:35** — Y estas dos funciones leen y guardan la API key, una por proveedor.
- **28:48** — nombreCerebro es el texto que mostramos debajo del núcleo.
- **29:00** — Los servicios están listos. Ahora, la parte visual.

## Paso 10 · tema.dart y el núcleo

- **29:05** — tema.dart tiene los colores, el tema y un pequeño widget: la píldora que dice Sin internet.
- **29:12** — Colores agrupa la paleta: así cambiamos un color en un solo lugar.
- **29:18** — Pildora es un StatelessWidget: un widget sin estado, que siempre se dibuja igual con los datos que recibe. Recibe un texto, un color y un ícono.
- **29:27** — Todo widget tiene un método build, que devuelve lo que se dibuja en la pantalla.
- **29:32** — temaYarbys devuelve el tema oscuro de Material; lo pego.
- **29:36** — Le decimos que es oscuro y le damos nuestros colores. Todos los botones, campos y barras los usarán.
- **29:44** — Y el build de la píldora.
- **29:48** — Aquí se ve la idea de los bloques: un Container con fondo redondeado, que adentro tiene una fila, Row, con el ícono y el texto.
- **29:58** — Y ahora lo más vistoso: el núcleo. Aquí aparece un concepto clave de Flutter: el StatefulWidget.
- **30:06** — Un enum es una lista de opciones fijas: los cuatro estados de YARBYS.
- **30:11** — Un StatefulWidget tiene dos partes. El widget, Nucleo, recibe la configuración: el estado y el tamaño...
- **30:18** — ...y su State, _NucleoState, guarda los datos que cambian con el tiempo: los segundos y el giro. Cada vez que cambian, llamamos a setState y Flutter vuelve a dibujar.
- **30:28** — Y _PintorNucleo es un CustomPainter: un lienzo donde dibujamos con código.
- **30:33** — initState se ejecuta una vez, cuando el widget aparece.
- **30:38** — Creamos un Ticker, que nos avisa en cada cuadro de la pantalla, sesenta veces por segundo. En cada aviso, setState suma el tiempo y el giro, y Flutter redibuja el núcleo.
- **30:49** — _velocidad dice qué tan rápido gira cada estado: al pensar, cuatro veces más rápido.
- **30:55** — dispose apaga el reloj cuando el widget desaparece, para no gastar batería.
- **30:59** — build entrega el lienzo: CustomPaint con nuestro pintor.
- **31:03** — Estas son funciones de ayuda para dibujar: un punto en el círculo, un trazo, un arco, girar y escribir texto. Las pego.
- **31:11** — Y paint dibuja el núcleo, anillo por anillo. Pego la primera parte.
- **31:16** — Calculamos el radio según el tamaño, y nos movemos al centro del lienzo.
- **31:23** — El primer anillo es un círculo fino con 120 marcas, como un reloj, que gira despacio.
- **31:32** — Luego vienen los bloques gruesos, los puntos, y este ecualizador: noventa barras que bailan cuando YARBYS escucha o habla.
- **31:44** — Y al final, el centro, con el nombre y el estado actual.
- **31:48** — shouldRepaint le dice a Flutter cuándo volver a pintar: cuando cambia el tiempo o el estado.
- **31:57** — El núcleo está listo.

## Paso 11 · Las pantallas

- **32:01** — Ahora las pantallas. Empezamos por inicio: la que descarga los modelos la primera vez.
- **32:07** — Su estado guarda el progreso de cada descarga, si está descargando, y el error, si lo hay.
- **32:13** — initState: si los modelos ya están en el celular, entramos directo.
- **32:23** — _descargar baja los dos modelos.
- **32:27** — Usa los métodos de Modelos. Cada vez que llega un porcentaje nuevo, setState lo guarda y Flutter redibuja la barra de progreso. Si algo falla, catch muestra el error.
- **32:37** — _entrar abre Qdrant y cambia a la pantalla del chat.
- **32:42** — Navigator cambia de pantalla. Con pushReplacement, la pantalla de inicio se reemplaza y no se puede volver a ella.
- **32:50** — Y build arma la pantalla.
- **32:54** — Scaffold es la página, SafeArea evita la cámara y los bordes del celular, y ListView pone todo en una lista que se puede desplazar: el núcleo, los textos, las dos tarjetas y el botón.
- **33:06** — El botón llama a _descargar, y se desactiva mientras descarga.
- **33:11** — _Descarga es la tarjeta de cada modelo; la pego.
- **33:17** — La pantalla del chat es la principal. Su método más importante es enviar: el corazón de toda la app.
- **33:24** — Su estado guarda el controlador del campo de texto, la lista de mensajes en pantalla, los hilos, el hilo actual y el estado del núcleo.
- **33:33** — Y aquí está enviar, todavía vacío. Lo escribiremos paso a paso.
- **33:37** — initState carga los hilos y le da a la voz el aviso para cuando se apague el micrófono.
- **33:42** — _cargarHilos lee las conversaciones de la memoria...
- **33:46** — ...y _abrirHilo muestra los mensajes de una conversación.
- **33:49** — Ahora sí, enviar. Paso uno, la memoria.
- **34:01** — Si la conversación es nueva, creamos el hilo. Leemos los últimos seis mensajes y guardamos tu pregunta. Luego, setState la muestra en pantalla y pone el núcleo en pensando.
- **34:12** — Pasos dos y tres: buscar y responder.
- **34:23** — Buscamos en Qdrant los fragmentos más parecidos a la pregunta, y anotamos de qué documentos salieron.
- **34:31** — Armamos el prompt, y con await for recibimos cada token y actualizamos la burbuja. Por eso la respuesta aparece poco a poco.
- **34:40** — Y los pasos cuatro y cinco: guardar y hablar.
- **34:52** — Guardamos la respuesta en la memoria...
- **34:56** — ...y YARBYS la lee en voz alta, con el núcleo en el estado hablando.
- **35:01** — _microfono hace lo mismo, pero con tu voz: cuando terminas de hablar, envía el texto reconocido.
- **35:07** — Estas son funciones de ayuda: limpiar el markdown, mostrar avisos, bajar la lista y cambiar de pantalla. Las pego.
- **35:14** — Y build, la pantalla. La pego y vemos sus bloques.
- **35:19** — Arriba, una AppBar con el nombre, la píldora y los botones de documentos y ajustes. Y drawer es el menú lateral de conversaciones.
- **35:29** — Luego el núcleo, que se achica con una animación cuando ya hay mensajes.
- **35:35** — La lista de mensajes, una burbuja por mensaje...
- **35:40** — ...y abajo el campo de texto, que al enviar llama a nuestra función enviar.
- **35:45** — _menuHilos es el menú de conversaciones; lo pego.
- **35:49** — Y _Burbuja dibuja cada mensaje: azul a la derecha si es tuyo, gris a la izquierda si es de YARBYS, con sus fuentes debajo.
- **35:58** — La pantalla de documentos es parecida, así que la armamos más rápido.
- **36:07** — _aprender le pasa el texto a Conocimiento y muestra un aviso con cuántos fragmentos guardó.
- **36:13** — _elegirArchivos usa file_picker.
- **36:17** — pickFiles abre el selector de archivos del celular, solo para .txt y .md. Leemos cada archivo, lo convertimos en texto y se lo damos a _aprender.
- **36:28** — _escribirNota abre un diálogo para escribir o pegar una nota.
- **36:32** — Y el resto: borrar, avisar y la pantalla.
- **36:40** — Y la última pantalla, ajustes.
- **36:49** — _cambiarModo activa el LLM externo.
- **36:54** — Si alguien que no es Pro intenta activarlo, le mostramos la versión Pro.
- **36:59** — _cambiarProveedor cambia entre OpenAI y Anthropic.
- **37:03** — Y build arma la pantalla.
- **37:07** — Con SegmentedButton se elige el cerebro: en el celular o externo.
- **37:13** — Y le explicamos al usuario qué datos salen del celular cuando usa un LLM externo. Es importante ser transparentes.
- **37:24** — Las cuatro pantallas están listas.

## Paso 12 · main.dart

- **37:27** — Por último, main.dart: el punto de partida. Lo abrimos: trae el ejemplo del contador de Flutter. Lo borramos todo.
- **37:43** — main es lo primero que se ejecuta al abrir la app.
- **37:47** — Y YarbysApp es el widget raíz de toda la app.
- **37:50** — Implementamos main.
- **38:01** — Encendemos el motor de inteligencia artificial: LiteRtLmEngine para Gemma, y LiteRtEmbeddingBackend para EmbeddingGemma.
- **38:11** — Abrimos la memoria, cargamos los ajustes, y runApp arranca la app.
- **38:16** — Y build devuelve la app.
- **38:26** — MaterialApp con nuestro tema oscuro, y la pantalla de inicio como primera pantalla.
- **38:33** — Y main.dart está listo.
- **38:36** — Así queda el proyecto completo: los servicios con la inteligencia artificial, el núcleo y las pantallas.

## Paso 13 · Probar en el celular

- **38:43** — Conectamos el celular por USB y revisamos que Flutter lo vea con flutter devices.
- **38:49** — Ahí está mi Pixel 8. Ejecutamos la app con flutter run --release. En modo release, Gemma corre mucho más rápido.
- **38:56** — La primera compilación tarda unos minutos, porque descarga las librerías nativas de LiteRT-LM y de Qdrant Edge.
- **39:04** — Y se abre en el celular. La primera vez, YARBYS nos pide descargar los modelos. Usa Wi-Fi: son unos 2.8 gigas.
- **39:12** — Aquí aceleré el video. Según tu internet, la descarga puede tardar varios minutos, pero se hace una sola vez.
- **39:20** — Ya tenemos el chat. Primero le enseñamos nuestros documentos: toco el ícono de documentos, y Agregar archivo.
- **39:27** — YARBYS lee cada archivo, lo corta en fragmentos, crea los embeddings y los guarda en Qdrant. Todo dentro del celular.
- **39:34** — Ahora activo el modo avión, para comprobar que todo funciona sin internet.
- **39:38** — Y le pregunto.
- **40:03** — Perfecto. Ahora, la prueba de la memoria: cierro la app y la vuelvo a abrir.
- **40:08** — Abro el menú, entro a la conversación de antes, y le pregunto de qué hablamos.
- **40:25** — ¡Lo recuerda todo! Porque cada mensaje quedó guardado en SQLite, en el mismo hilo.
- **40:30** — Y si quieres, en Ajustes puedes activar un LLM externo con tu propia API key. Es opcional: por defecto, YARBYS es cien por ciento local.

## Generar el APK

- **40:39** — Para compartir la app sin cable, generamos el APK con flutter build apk. Con --target-platform android-arm64 compilamos solo para los celulares modernos.
- **40:50** — Y en el repositorio de GitHub dejé un workflow de GitHub Actions que compila el APK automáticamente. Así puedes descargarlo y probarlo sin instalar nada.

## Bonus · Ganar dinero

- **41:00** — Bonus: ¿cómo podrías ganar dinero con una app como YARBYS?
- **41:04** — Una idea: la versión gratuita es cien por ciento local, sin límites. Eso atrae a muchos usuarios, porque sus datos nunca salen del celular.
- **41:12** — Luego, una versión Pro de pago único, con funciones extra como el LLM externo. Como cada usuario pone su propia API key, tú no pagas los tokens.
- **41:22** — Y para empresas: clínicas, estudios de abogados o colegios valoran mucho la privacidad. Puedes ofrecerles una versión a medida.
- **41:30** — Y más adelante, si quieres, una suscripción con tu propio servidor. Pero empieza simple.

## Resumen

- **41:37** — ¡Y listo! Hagamos un resumen de lo que construimos.
- **41:40** — Un asistente que usa Gemma 4 como cerebro dentro del celular, EmbeddingGemma y Qdrant Edge para buscar en tus documentos, SQLite para recordar las conversaciones, y los motores de voz del teléfono.
- **41:53** — Además, un LLM externo opcional para la versión Pro, y el APK listo con GitHub Actions. Como reto, agrégale tus propios documentos y pregúntale lo que quieras.
- **42:04** — El código completo está en GitHub; te dejo el enlace en la descripción.
- **42:09** — Si te gustó, dale like, suscríbete, y cuéntame en los comentarios qué le agregarías a tu YARBYS. ¡Nos vemos en el próximo video!

## Capítulos para la descripción de YouTube

```
0:00 Introducción
0:27 Resultado final
1:20 ¿IA en el celular?
2:03 Las 5 piezas
2:31 ¿Qué es un LLM?
3:13 Modelos para celular
3:57 Embeddings
4:33 Fragmentos
4:52 Qdrant Edge
5:20 RAG
5:54 Memoria
6:21 La voz
6:41 Flutter
7:10 Arquitectura
7:42 Instalación
8:21 Paso 1 · Crear el proyecto
9:10 Paso 2 · Paquetes
10:36 Paso 3 · Configurar Android
11:33 Paso 4 · Los archivos
13:08 Paso 5 · modelos.dart
17:31 Paso 6 · memoria.dart
20:32 Paso 7 · conocimiento.dart
23:11 Paso 8 · cerebro.dart
26:02 Paso 9 · voz.dart y ajustes.dart
29:04 Paso 10 · tema.dart y el núcleo
31:59 Paso 11 · Las pantallas
37:27 Paso 12 · main.dart
38:43 Paso 13 · Probar en el celular
40:39 Generar el APK
41:00 Bonus · Ganar dinero
41:37 Resumen
```
