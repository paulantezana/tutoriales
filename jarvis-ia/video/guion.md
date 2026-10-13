# Guion de narración

Lee cada frase en voz alta en el momento indicado. Los tiempos coinciden con `tutorial.mp4`.
El video ya trae esta narración con voz generada (Kokoro). Si prefieres grabar tu propia voz, pon `NARRACION = False` en `render.py` y graba siguiendo estos tiempos.


## Introducción

- **0:00** — Hola, ¿qué tal? Bienvenidos. Hoy vamos a crear nuestro propio JARVIS: un asistente personal con inteligencia artificial.
- **0:07** — Conoce tu información, recuerda lo que conversan y te responde con voz, desde una página web.
- **0:13** — Y lo haremos en Windows, sin Docker, paso a paso y explicando cada línea de código.

## Resultado final

- **0:21** — Antes de empezar, mira el resultado final. Le pregunto a JARVIS qué tengo el miércoles.
- **0:38** — Sabe lo que tengo en mi agenda porque lee mis documentos, y me responde con voz.
- **0:53** — Y recuerda la conversación: en la segunda pregunta no tuve que explicarle nada más.

## Las 5 piezas

- **0:59** — Para construir a JARVIS necesitamos cinco piezas, y te voy a explicar cada una con calma.
- **1:05** — Un cerebro, que es el modelo de lenguaje, y un traductor de textos a números, que son los embeddings.
- **1:11** — Una base de datos vectorial para buscar información, y una memoria para recordar las conversaciones.
- **1:17** — Y una página web para hablar con él. LangChain será el pegamento que une todas las piezas.

## ¿Qué es un LLM?

- **1:24** — Empecemos por el cerebro: el LLM, o modelo de lenguaje. Es una inteligencia artificial que entiende y escribe texto.
- **1:32** — Funciona así: le envías un mensaje, lo divide en pequeños pedazos llamados tokens, y genera la respuesta token por token.
- **1:39** — ChatGPT, Claude, Gemini o DeepSeek usan LLMs. Pero hay decenas de modelos, cada uno con distinta inteligencia y precio.

## Comparativa de LLMs

- **1:49** — ¿Y cómo elegimos uno? Yo uso Artificial Analysis, una página independiente que compara los modelos de IA por inteligencia, velocidad y precio.
- **1:58** — En este gráfico, más arriba significa más inteligente, y más a la derecha, más caro. El precio es en dólares por millón de tokens de salida.
- **2:07** — Arriba están los más potentes, como Claude Opus 5.5, Claude Sonnet 5.5 o Gemini 4 Argon. Son muy inteligentes, pero cuestan entre 10 y 20 dólares por millón de tokens.
- **2:19** — Y aquí abajo, a la izquierda, está GPT-6 Luna, al que llamamos GptLuna: tiene 38 puntos y cuesta solo 50 centavos. ¡Unas 40 veces más barato que Opus!
- **2:30** — En la misma zona está Claude Haiku 5.5, con el mismo precio y algo más de inteligencia. También sería una gran opción.
- **2:38** — Para un asistente personal que responde preguntas del día a día no necesitamos el modelo más caro. GptLuna nos da una excelente relación entre precio e inteligencia.

## Embeddings

- **2:50** — Ahora, ¿cómo encuentra JARVIS la información correcta dentro de tus documentos? Con embeddings.
- **2:56** — Un embedding convierte un texto en una lista de números, llamada vector. bge-m3, por ejemplo, genera 1024 números por cada texto.
- **3:05** — Lo genial es que los textos con significado parecido quedan cerca. '¿Qué tengo el miércoles?' queda junto a 'Miércoles: entregar el proyecto', aunque usen palabras distintas.
- **3:15** — Hay varios modelos de embeddings. OpenAI tiene text-embedding-3-small, que cuesta 2 centavos por millón de tokens, y uno más grande y preciso. También está nomic-embed-text, que corre en tu PC.
- **3:26** — Nosotros usaremos bge-m3 con Ollama: es gratis, funciona sin internet en tu computadora y entiende más de 100 idiomas, incluido el español.

## Qdrant

- **3:37** — Esos vectores los guardamos en Qdrant, una base de datos vectorial. Es como una biblioteca que ordena los textos por su significado.
- **3:45** — Cuando haces una pregunta, Qdrant la compara con todos los fragmentos guardados y te devuelve los más parecidos, con un puntaje.
- **3:53** — Y lo mejor: Qdrant tiene una versión para Windows. Solo descargas un archivo y lo ejecutas.

## RAG

- **4:00** — Juntando estas piezas tenemos la técnica más usada para crear asistentes con IA: RAG.
- **4:06** — Primero llega tu pregunta. Luego buscamos en Qdrant la información relevante.
- **4:11** — Después la añadimos al mensaje, junto con tu pregunta. Y finalmente el LLM genera la respuesta.
- **4:18** — Así JARVIS responde con TUS datos reales, y no se inventa cosas.

## Memoria

- **4:24** — La última pieza es la memoria. Un LLM, por sí solo, no recuerda nada: cada mensaje es como hablar con alguien que te acaba de conocer.
- **4:33** — Si le pregunto '¿y cómo se llama mi perro?' después de hablar de mi agenda, necesita saber de qué estábamos hablando.
- **4:39** — Por eso guardamos cada conversación, a la que llamamos 'hilo', en PostgreSQL. Y en cada pregunta le enviamos los últimos mensajes.
- **4:47** — PostgreSQL también tiene instalador oficial para Windows, así que tampoco necesitamos Docker.

## Arquitectura

- **4:54** — Este es el plan completo. Tú hablas con JARVIS desde una página web, en tu navegador.
- **5:00** — La página le envía tu mensaje a nuestro servidor en Python, hecho con FastAPI, que se lo pasa a asistente.py.
- **5:07** — Ahí buscamos el contexto en Qdrant, con la ayuda de Ollama, y leemos el historial en PostgreSQL.
- **5:13** — Luego le preguntamos a GptLuna, guardamos la respuesta en la memoria, y la página la lee en voz alta.

## Instalación en Windows

- **5:21** — Pasemos a la instalación. Todo funciona directamente en Windows, sin Docker y sin WSL.
- **5:27** — Primero, Python, desde python.org. Muy importante: en el instalador marca la casilla 'Add python.exe to PATH'.
- **5:35** — Segundo, Ollama, desde ollama.com. Se instala como cualquier programa y queda funcionando en segundo plano.
- **5:42** — Tercero, Qdrant. En su página de GitHub, en la sección Releases, descarga el archivo .zip para Windows y descomprímelo, por ejemplo, en C:\qdrant.
- **5:52** — Cuarto, PostgreSQL, con el instalador para Windows de su página oficial. Te pedirá una contraseña para el usuario postgres: anótala, la usaremos después.
- **6:01** — Y por último, tu API key de OpenAI, desde platform.openai.com, para poder usar GptLuna.

## Paso 1 · Servicios

- **6:09** — Con todo instalado, abrimos Visual Studio Code. Creé una carpeta llamada jarvis en C:\proyectos, y la abrí con File, Open Folder.
- **6:18** — Abrimos la terminal con Control + comilla invertida. En Windows, VS Code usa PowerShell.
- **6:24** — Primero descargamos el modelo de embeddings con Ollama: ollama pull bge-m3.
- **6:31** — Ahora encendemos Qdrant. Abro una segunda terminal con Control + Shift + comilla invertida, y ejecuto el programa que descomprimimos en C:\qdrant.
- **6:40** — Qdrant ya está funcionando en el puerto 6333. Deja esta terminal abierta mientras trabajas.

## Paso 2 · Entorno Python

- **6:48** — Volvemos a la primera terminal y creamos un entorno virtual: una carpeta donde se instalan las librerías solo para este proyecto.
- **6:56** — Lo activamos con .venv\Scripts\activate.
- **7:00** — Fíjate que ahora aparece '(.venv)' en verde al inicio. Eso significa que el entorno está activo.
- **7:07** — Si Windows te muestra un error de permisos al activarlo, ejecuta una sola vez: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned.
- **7:15** — Ahora creamos el archivo requirements.txt, con las librerías que vamos a necesitar.
- **7:34** — langchain es la librería principal. Cada 'langchain-algo' es una integración: openai para GptLuna, ollama para los embeddings, y qdrant y postgres para las bases de datos.
- **7:46** — psycopg conecta Python con PostgreSQL, python-dotenv lee nuestra configuración, y fastapi con uvicorn nos permiten crear el servidor web.
- **7:56** — Las instalamos con pip install -r requirements.txt.

## Paso 3 · Configuración

- **8:03** — Ahora la configuración. Creamos un archivo llamado .env, donde van las claves y direcciones, separadas del código.
- **8:12** — Primero, tu API key de OpenAI y el nombre del modelo: gpt-6-luna. Reemplaza el texto de ejemplo por tu clave real.
- **8:35** — Después las direcciones de Ollama y de Qdrant, con el modelo bge-m3 y el nombre de nuestra colección: jarvis.
- **8:51** — Y la conexión a PostgreSQL. Aquí va la contraseña que elegiste al instalarlo. Usamos la base de datos que viene por defecto, llamada postgres, así no tenemos que crear nada.
- **9:03** — Un consejo importante: este archivo tiene tu clave secreta. ¡Nunca lo subas a GitHub!

## Paso 4 · Tus documentos

- **9:09** — Ahora, la información que JARVIS va a conocer. Creamos la carpeta docs con un archivo perfil.txt.
- **9:29** — Y otro archivo con mi agenda de la semana. Este lo pego para ir más rápido.
- **9:34** — Tú puedes poner aquí lo que quieras: tus notas, tus proyectos, tus contactos. Mientras más información, más útil será JARVIS.

## Paso 5 · ingest.py

- **9:42** — Nuestro primer programa es ingest.py. Su trabajo es leer los documentos, convertirlos en vectores y guardarlos en Qdrant.
- **10:04** — Empezamos importando lo que vamos a usar: os para leer la configuración, Path para buscar archivos, y las piezas de LangChain.
- **10:14** — load_dotenv lee el archivo .env, para poder usar esas variables en el código.
- **10:33** — Recorremos todos los archivos .txt de la carpeta docs, y por cada uno creamos un Document de LangChain, con su texto y el nombre del archivo.
- **10:54** — Los documentos largos se cortan en fragmentos de 500 caracteres, repitiendo 50 entre uno y otro para no cortar una idea por la mitad.
- **11:15** — Creamos el generador de embeddings con Ollama. Con os.getenv leemos el modelo, bge-m3, y la dirección desde el archivo .env.
- **11:39** — Y from_documents hace la magia: le pide a Ollama el vector de cada fragmento y guarda todo en la colección de Qdrant.
- **11:53** — Lo ejecutamos: python ingest.py.
- **11:57** — ¡Funciona! Se guardaron dos fragmentos, uno por cada archivo. Cada vez que cambies tus documentos, vuelve a ejecutarlo.

## Paso 6 · El cerebro

- **12:04** — Ahora el corazón del proyecto: asistente.py. Aquí juntamos el cerebro, la búsqueda y la memoria.
- **12:43** — Importamos una pieza de LangChain por cada servicio: GptLuna, Ollama, Qdrant y la memoria en PostgreSQL.
- **13:04** — Primero el cerebro. ChatOpenAI se conecta con OpenAI usando tu API key, y el modelo gpt-6-luna. Activamos la API de respuestas, que es la más moderna de OpenAI.
- **13:44** — Luego nos conectamos a la colección que creamos con ingest.py, usando el mismo modelo de embeddings.
- **13:50** — Y el retriever es nuestro buscador: por cada pregunta nos devuelve los 3 fragmentos más parecidos.
- **14:17** — Ahora la memoria. Nos conectamos a PostgreSQL y creamos la tabla chat_history, donde se guardan los mensajes.
- **14:23** — La función obtener_historial devuelve los mensajes de un hilo, así cada conversación tiene su propia memoria.
- **14:55** — Esta es la personalidad de JARVIS. Le pedimos respuestas cortas, de máximo tres oraciones, porque se van a leer en voz alta.
- **15:03** — Las llaves con context son un espacio vacío: ahí pondremos los textos que encuentre Qdrant.
- **15:31** — El prompt es el mensaje completo que recibe GptLuna: la personalidad con el contexto, el historial de la conversación y tu pregunta.
- **15:41** — buscar_contexto le pasa tu pregunta al retriever y une el texto de los fragmentos que encuentra.
- **15:56** — Y esta es la cadena. La barra vertical significa 'y luego pásaselo a': agregamos el contexto, armamos el prompt, se lo enviamos a GptLuna y nos quedamos con el texto.
- **16:34** — Por último, preguntar_a_jarvis. Lee el historial del hilo, ejecuta la cadena con los últimos 10 mensajes, y guarda tu pregunta y su respuesta en PostgreSQL.

## Paso 7 · El servidor

- **16:45** — Ahora el servidor web: app.py. Es muy cortito, gracias a FastAPI.
- **17:06** — Mensaje describe lo que nos envía la página: el texto de tu pregunta y el id del hilo.
- **17:24** — Esta ruta, /api/chat, recibe el mensaje, se lo pregunta a JARVIS y devuelve la respuesta.
- **17:39** — Y con app.mount servimos la página web, que va en la carpeta web.

## Paso 8 · La página web

- **17:45** — Ahora la página. Creamos la carpeta web con el archivo index.html. El HTML lo pego para ir más rápido.
- **17:53** — Tiene tres partes. El núcleo animado de JARVIS: tres anillos y un centro brillante.
- **18:00** — El chat, donde aparecen los mensajes.
- **18:05** — Y la entrada: un botón de micrófono para hablarle, el cuadro de texto y el botón de enviar.
- **18:11** — Los estilos también los pego: estilo.css.
- **18:17** — Lo más interesante es la animación: cada anillo gira a una velocidad distinta, y el centro late como un corazón.
- **18:26** — Y cambia según el estado: cuando piensa, gira rápido y se pone naranja; cuando habla, late más rápido.
- **18:34** — Y el último archivo, app.js, que le da vida a la página. Este sí lo escribimos y lo explico.
- **18:51** — Primero el hilo: creamos un identificador único y lo guardamos en el navegador. Así, aunque recargues la página, JARVIS sigue recordando la conversación.
- **19:48** — cambiarEstado actualiza el núcleo y el texto de estado, y agregarMensaje pone cada mensaje en el chat.
- **20:15** — Con SpeechSynthesis, el navegador lee la respuesta en voz alta, en español y gratis.
- **21:02** — preguntar envía tu mensaje a nuestro servidor con fetch, muestra la respuesta, y la lee en voz alta. Si algo falla, te avisa.
- **22:02** — Y al final, el reconocimiento de voz: al presionar el micrófono, el navegador escucha, convierte tu voz en texto y se lo pregunta a JARVIS.

## Paso 9 · ¡Probamos JARVIS!

- **22:12** — ¡Llegó el momento! Encendemos el servidor con uvicorn app:app --reload.
- **22:18** — Hacemos Control + clic en la dirección, y se abre JARVIS en el navegador.
- **22:24** — Probemos con otra pregunta.
- **22:45** — Ahora la prueba de fuego para la memoria: recargo la página...
- **22:50** — ...y le pregunto de qué hablamos antes.
- **23:04** — ¡Lo recuerda todo! Porque cada mensaje quedó guardado en PostgreSQL, en el mismo hilo.
- **23:10** — Y en la terminal puedes ver cada mensaje que llegó al servidor.

## Resumen

- **23:14** — ¡Y listo! Hagamos un resumen de lo que construimos.
- **23:17** — Un JARVIS que usa GptLuna como cerebro, bge-m3 y Qdrant para buscar en tus documentos, y PostgreSQL para recordar las conversaciones.
- **23:26** — Todo en Windows, sin Docker, y con una página web que te responde con voz.
- **23:31** — Como reto, agrega tus propios documentos a la carpeta docs, vuelve a ejecutar ingest.py, y pregúntale lo que quieras.
- **23:40** — El código completo está en GitHub; te dejo el enlace en la descripción.
- **23:45** — Si te gustó, dale like, suscríbete y cuéntame en los comentarios qué le agregarías a tu JARVIS. ¡Nos vemos en el próximo video!

## Capítulos para la descripción de YouTube

```
0:00 Introducción
0:20 Resultado final
0:59 Las 5 piezas
1:24 ¿Qué es un LLM?
1:49 Comparativa de LLMs
2:50 Embeddings
3:37 Qdrant
4:00 RAG
4:24 Memoria
4:54 Arquitectura
5:21 Instalación en Windows
6:09 Paso 1 · Servicios
6:48 Paso 2 · Entorno Python
8:03 Paso 3 · Configuración
9:09 Paso 4 · Tus documentos
9:42 Paso 5 · ingest.py
12:04 Paso 6 · El cerebro
16:45 Paso 7 · El servidor
17:45 Paso 8 · La página web
22:12 Paso 9 · ¡Probamos JARVIS!
23:14 Resumen
```
