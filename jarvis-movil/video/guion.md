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

- **9:10** — Agregamos los paquetes de inteligencia artificial con flutter pub add.
- **9:21** — Y después el resto: sqflite para SQLite, path_provider para las carpetas, file_picker para elegir archivos, flutter_secure_storage para guardar la API key, http, y los dos paquetes de voz.
- **9:36** — Fíjate que flutter pub add los anotó en pubspec.yaml. flutter_edge_ai y su motor LiteRT-LM ejecutan Gemma en el celular, y los paquetes rag y qdrant nos dan la búsqueda con Qdrant Edge.

## Paso 3 · Configurar Android

- **9:49** — Ahora configuramos Android. Abrimos android, app, build.gradle.kts.
- **9:54** — Gemma necesita Android 11 o superior, que es la versión 30 de la API. Cambiamos minSdk por 30.
- **10:02** — Y en android, app, src, main, abrimos AndroidManifest.xml: ahí van los permisos de la app.
- **10:09** — Agregamos el permiso de internet, para descargar los modelos, y el del micrófono, para hablar con YARBYS.
- **10:28** — Cambiamos el nombre visible de la app a YARBYS, en mayúsculas.
- **10:32** — Y en la sección queries avisamos que usaremos el reconocimiento de voz y la lectura en voz alta del sistema.
- **10:52** — Para iPhone necesitas una Mac con Xcode; te dejo los pasos en el README del repositorio.

## Paso 4 · Los modelos

- **10:58** — Ahora sí, a programar. En lib creamos la carpeta servicios, y dentro, el archivo modelos.dart. Aquí descargamos los dos modelos de inteligencia artificial.
- **11:42** — Guardamos las direcciones de los dos modelos. Están en Hugging Face, la plataforma donde se publican los modelos abiertos, y no necesitan cuenta ni token.
- **12:03** — listos nos dice si los dos modelos ya están en el celular, para no descargarlos otra vez.
- **12:40** — installEmbedder descarga EmbeddingGemma, y withModelProgress nos va avisando el porcentaje, para mostrar una barra de progreso.
- **12:50** — Con installModel descargamos Gemma. modelType le dice a la librería que es Gemma 4, y fileType, que es un archivo .litertlm, el formato del motor LiteRT-LM.

## Paso 5 · Memoria con SQLite

- **13:02** — Ahora la memoria. Creamos servicios, memoria.dart.
- **13:32** — Una clase en Dart es como un molde. Mensaje tiene un rol, que dice quién habló, el texto, y las fuentes: los documentos que YARBYS usó para responder.
- **13:42** — Las clases Hilo y Documento son parecidas; las pego para avanzar más rápido.
- **14:35** — openDatabase abre el archivo yarbys.db, dentro de la carpeta de la app. Si no existe, lo crea.
- **14:44** — onCreate se ejecuta solo la primera vez. Con SQL creamos dos tablas: hilos, con cada conversación, y mensajes, donde cada mensaje guarda el id del hilo al que pertenece.
- **14:56** — Y pego también la tabla de documentos y las funciones para leer y guardar; son consultas sencillas.
- **15:02** — guardar inserta una fila nueva en la tabla mensajes.
- **15:08** — Y mensajes trae los mensajes de un hilo. Con limit pedimos solo los últimos, y luego los volteamos para tenerlos en orden. Así le daremos memoria a YARBYS.

## Paso 6 · RAG con Qdrant Edge

- **15:18** — Sigue el conocimiento: tus documentos en Qdrant. Creamos servicios, conocimiento.dart.
- **16:23** — FlutterEdgeAiRag es el sistema de RAG, y le decimos que guarde los vectores con Qdrant Edge.
- **16:31** — Abrimos el índice en una carpeta de la app, y le indicamos que EmbeddingGemma será quien convierta los textos en vectores.
- **16:39** — Ahora la función que corta los documentos en fragmentos. La pego y la explico.
- **16:44** — Separamos el texto por párrafos, y los vamos juntando hasta llegar a unos 800 caracteres. Cuando no cabe uno más, guardamos el fragmento y empezamos otro.
- **17:30** — aprender fragmenta el texto y anota el documento en SQLite. Luego, por cada fragmento, add crea su vector con EmbeddingGemma y lo guarda en Qdrant, junto con el nombre del documento.
- **17:43** — Y flush guarda los cambios en el disco.
- **18:04** — Y la búsqueda: search convierte la pregunta en vector y nos devuelve los tres fragmentos más parecidos. threshold descarta los que se parecen muy poco.

## Paso 7 · El cerebro

- **18:16** — Llegamos al cerebro. Creamos servicios, cerebro.dart.
- **19:04** — Primero, la personalidad de YARBYS. Son las instrucciones de sistema: le decimos quién es, que responda en español, en máximo tres oraciones y sin formato, porque se leen en voz alta.
- **19:58** — armarPrompt construye el mensaje que verá Gemma: primero los fragmentos de tus documentos, luego la conversación reciente y al final tu pregunta. Exactamente lo que vimos en la parte de RAG.
- **20:58** — responder devuelve un Stream: un flujo de datos que llega en pedacitos, token por token. Si el usuario no activó la nube, usamos Gemma en el celular.
- **21:08** — getActiveModel carga Gemma en la memoria. maxTokens es cuánto texto puede leer a la vez, el contexto. Y createChat crea la conversación con la personalidad y un máximo de 512 tokens de respuesta.
- **21:22** — Le enviamos el prompt, y con yield vamos entregando cada token apenas Gemma lo genera. Al final, cerramos el chat.
- **21:30** — La parte del LLM externo es opcional. La pego y te explico lo importante.
- **21:36** — La API key la escribe cada usuario en la app; nunca va escrita en el código.
- **21:43** — Con el paquete http enviamos el mismo prompt a Anthropic, para Claude Haiku, o a OpenAI, para GPT-6 Luna. El resto de la app no cambia nada.

## Paso 8 · Voz y ajustes

- **21:53** — Ahora la voz. Creamos servicios, voz.dart, y pego el código.
- **22:00** — Tenemos dos piezas: el oído, SpeechToText, que convierte tu voz en texto, y la boca, FlutterTts, que lee en voz alta.
- **22:09** — listen escucha en español, nos va mostrando el texto mientras hablas, y termina cuando te quedas en silencio tres segundos.
- **22:18** — Y hablar lee la respuesta en voz alta, y espera a que termine.
- **22:23** — Y servicios, ajustes.dart: aquí se guardan las preferencias.
- **22:31** — Usamos FlutterSecureStorage, que guarda los datos cifrados: en Android con Keystore y en iPhone con Keychain. Ideal para la API key.
- **22:40** — usarNube empieza en false: por defecto, YARBYS es cien por ciento local.
- **22:47** — Y esPro es el interruptor de la versión Pro. Aquí conectarías una compra dentro de la app; en este proyecto viene desbloqueada.

## Paso 9 · El núcleo de YARBYS

- **22:55** — Pasemos a la interfaz. Primero tema.dart, con los colores de la app: fondos oscuros y planos. Lo pego.
- **23:02** — Todos los colores están en un solo lugar, para cambiarlos fácilmente.
- **23:07** — Y ahora, lo más vistoso: el núcleo circular, inspirado en el JARVIS de las películas. Creamos widgets, nucleo.dart.
- **23:15** — YARBYS tiene cuatro estados: en reposo, escuchando, pensando y hablando.
- **23:21** — Un Ticker nos avisa sesenta veces por segundo, y en cada cuadro los anillos giran un poco. Al pensar, giran cuatro veces más rápido.
- **23:31** — Y el dibujo lo hacemos con un CustomPainter: un lienzo donde dibujamos con código, con círculos, arcos y líneas.
- **23:41** — Por ejemplo, estas barras forman un ecualizador circular que baila cuando YARBYS escucha o habla.

## Paso 10 · Las pantallas

- **23:48** — Ahora las pantallas. En lib creamos la carpeta pantallas. Empezamos por inicio.dart, la pantalla que descarga los modelos.
- **23:55** — Si los modelos ya están descargados, vamos directo al chat.
- **24:01** — Si no, el botón descarga los dos modelos. Cada vez que llega un porcentaje nuevo, setState redibuja la pantalla con la barra de progreso.
- **24:11** — La pantalla principal es chat.dart. La pego, y vamos a ver su corazón paso a paso.
- **24:18** — La función enviar hace todo el trabajo. Paso uno, la memoria: si la conversación es nueva, creamos el hilo. Leemos los últimos seis mensajes y guardamos tu pregunta.
- **24:30** — Paso dos, RAG: buscamos en Qdrant los fragmentos más parecidos a la pregunta, y anotamos de qué documentos salieron.
- **24:39** — Paso tres: armamos el prompt, y con await for recibimos cada token y actualizamos la burbuja en la pantalla. Por eso la respuesta aparece poco a poco.
- **24:50** — Paso cuatro: guardamos la respuesta en la memoria.
- **24:56** — Y paso cinco: YARBYS la lee en voz alta, y el núcleo cambia al estado hablando.
- **25:03** — Con el micrófono es igual: cuando terminas de hablar, el texto reconocido se envía con la misma función.
- **25:10** — Siguen documentos.dart, para agregar tus archivos, y ajustes.dart. Los pego.
- **25:18** — Aquí elegimos archivos de texto del celular, los leemos y se los damos a Conocimiento para que los aprenda. También puedes escribir una nota rápida.
- **25:36** — Y en ajustes, si alguien que no es Pro intenta activar el LLM externo, le mostramos la versión Pro.
- **25:44** — Además le explicamos al usuario qué datos salen del celular cuando usa un LLM externo. Es importante ser transparentes.

## Paso 11 · main.dart

- **25:53** — Por último, main.dart: el punto de entrada de la app. Lo abrimos: trae el ejemplo del contador de Flutter. Lo borramos todo.
- **26:50** — Al arrancar, encendemos el motor de inteligencia artificial: LiteRtLmEngine para Gemma, y LiteRtEmbeddingBackend para EmbeddingGemma.
- **27:00** — Abrimos la memoria y cargamos los ajustes.
- **27:23** — Y la app: MaterialApp con nuestro tema oscuro, y la pantalla de inicio como primera pantalla.
- **27:30** — Y listo. Así queda el proyecto: los servicios con la inteligencia artificial, el núcleo y las pantallas.

## Paso 12 · Probar en el celular

- **27:37** — Conectamos el celular por USB y revisamos que Flutter lo vea con flutter devices.
- **27:43** — Ahí está mi Pixel 8. Ejecutamos la app con flutter run --release. En modo release, Gemma corre mucho más rápido.
- **27:50** — La primera compilación tarda unos minutos, porque descarga las librerías nativas de LiteRT-LM y de Qdrant Edge.
- **27:58** — Y se abre en el celular. La primera vez, YARBYS nos pide descargar los modelos. Usa Wi-Fi: son unos 2.8 gigas.
- **28:06** — Aquí aceleré el video. Según tu internet, la descarga puede tardar varios minutos, pero se hace una sola vez.
- **28:14** — Ya tenemos el chat. Primero le enseñamos nuestros documentos: toco el ícono de documentos, y Agregar archivo.
- **28:21** — YARBYS lee cada archivo, lo corta en fragmentos, crea los embeddings y los guarda en Qdrant. Todo dentro del celular.
- **28:28** — Ahora activo el modo avión, para comprobar que todo funciona sin internet.
- **28:32** — Y le pregunto.
- **28:57** — Perfecto. Ahora, la prueba de la memoria: cierro la app y la vuelvo a abrir.
- **29:02** — Abro el menú, entro a la conversación de antes, y le pregunto de qué hablamos.
- **29:19** — ¡Lo recuerda todo! Porque cada mensaje quedó guardado en SQLite, en el mismo hilo.
- **29:24** — Y si quieres, en Ajustes puedes activar un LLM externo con tu propia API key. Es opcional: por defecto, YARBYS es cien por ciento local.

## Generar el APK

- **29:33** — Para compartir la app sin cable, generamos el APK con flutter build apk. Con --target-platform android-arm64 compilamos solo para los celulares modernos.
- **29:44** — Y en el repositorio de GitHub dejé un workflow de GitHub Actions que compila el APK automáticamente. Así puedes descargarlo y probarlo sin instalar nada.

## Bonus · Ganar dinero

- **29:54** — Bonus: ¿cómo podrías ganar dinero con una app como YARBYS?
- **29:58** — Una idea: la versión gratuita es cien por ciento local, sin límites. Eso atrae a muchos usuarios, porque sus datos nunca salen del celular.
- **30:06** — Luego, una versión Pro de pago único, con funciones extra como el LLM externo. Como cada usuario pone su propia API key, tú no pagas los tokens.
- **30:16** — Y para empresas: clínicas, estudios de abogados o colegios valoran mucho la privacidad. Puedes ofrecerles una versión a medida.
- **30:24** — Y más adelante, si quieres, una suscripción con tu propio servidor. Pero empieza simple.

## Resumen

- **30:31** — ¡Y listo! Hagamos un resumen de lo que construimos.
- **30:34** — Un asistente que usa Gemma 4 como cerebro dentro del celular, EmbeddingGemma y Qdrant Edge para buscar en tus documentos, SQLite para recordar las conversaciones, y los motores de voz del teléfono.
- **30:47** — Además, un LLM externo opcional para la versión Pro, y el APK listo con GitHub Actions. Como reto, agrégale tus propios documentos y pregúntale lo que quieras.
- **30:58** — El código completo está en GitHub; te dejo el enlace en la descripción.
- **31:03** — Si te gustó, dale like, suscríbete, y cuéntame en los comentarios qué le agregarías a tu YARBYS. ¡Nos vemos en el próximo video!

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
9:49 Paso 3 · Configurar Android
10:58 Paso 4 · Los modelos
13:02 Paso 5 · Memoria con SQLite
15:18 Paso 6 · RAG con Qdrant Edge
18:16 Paso 7 · El cerebro
21:53 Paso 8 · Voz y ajustes
22:55 Paso 9 · El núcleo de YARBYS
23:48 Paso 10 · Las pantallas
25:53 Paso 11 · main.dart
27:36 Paso 12 · Probar en el celular
29:33 Generar el APK
29:54 Bonus · Ganar dinero
30:31 Resumen
```
