# Guion de narración

Lee cada frase en voz alta en el momento indicado. Los tiempos coinciden con `tutorial.mp4`.
El video ya trae esta narración con voz generada (Kokoro). Si prefieres grabar tu propia voz, pon `NARRACION = False` en `render.py` y usa estos tiempos.


## Introducción

- **0:00** — Hola, ¿qué tal? Bienvenidos a este curso, donde vamos a crear nuestro propio asistente de inteligencia artificial.
- **0:07** — No te preocupes si nunca has trabajado con IA: voy a explicar cada concepto y cada línea de código, paso a paso.

## Resultado final

- **0:15** — Antes de empezar, mira lo que vamos a tener al terminar este video.
- **0:35** — Es un asistente que responde usando la información de NUESTROS documentos, en este caso de una cafetería.
- **0:41** — Y además recuerda la conversación: fíjate que en la segunda pregunta no repetí de qué estábamos hablando.

## Conceptos básicos

- **0:49** — Primero, unos conceptos rápidos. Un LLM, o modelo de lenguaje, es una inteligencia artificial que entiende y escribe texto, como ChatGPT.
- **0:59** — Funciona así: le enviamos un mensaje, y nos responde con otro texto. En este curso usaremos GptLuna como nuestro LLM.
- **1:07** — Pero hay un problema: el LLM no conoce la información de TU negocio. No sabe tus horarios, tus precios ni tus productos.
- **1:16** — Para resolverlo usamos embeddings. Un embedding convierte un texto en una lista de números.
- **1:21** — Lo interesante es que textos con significado parecido quedan con números parecidos, es decir, quedan 'cerca' en este mapa.
- **1:29** — Por ejemplo, 'horario de atención' queda cerca de '¿a qué hora abren?', aunque usen palabras distintas.
- **1:35** — Estos números los va a generar Ollama, un programa gratuito que corre en tu propia computadora.
- **1:42** — Esos vectores los guardamos en una base de datos vectorial. Nosotros usaremos Qdrant.
- **1:47** — Cuando llega una pregunta, Qdrant la compara con todos los textos guardados y nos devuelve los más parecidos, con un puntaje.
- **1:56** — Juntando todo tenemos lo que se conoce como RAG. Suena complicado, pero son solo cuatro pasos.
- **2:03** — Llega la pregunta, buscamos la información relevante en Qdrant, la añadimos a la pregunta, y el LLM genera la respuesta.
- **2:11** — Así el asistente responde con datos reales de tu negocio, y no se inventa cosas.
- **2:17** — El último concepto es la memoria. Si pregunto '¿y cuánto cuesta el delivery?', el asistente necesita recordar de qué hablábamos.
- **2:25** — Por eso guardaremos cada conversación, a la que llamaremos 'hilo', en una base de datos PostgreSQL.
- **2:32** — Este es el plan completo. Vamos a escribir dos programas en Python.
- **2:37** — El primero, ingest.py, lee nuestros documentos, los convierte en vectores con Ollama y los guarda en Qdrant. Solo se ejecuta una vez.
- **2:45** — El segundo, app.py, es el chat: busca el contexto en Qdrant, lee el historial en PostgreSQL y le pregunta a GptLuna.
- **2:53** — Y para unir todas estas piezas usaremos LangChain, una librería de Python hecha justamente para esto.
- **3:01** — Para seguir el tutorial necesitas tener instalado Python, Docker y Visual Studio Code.
- **3:07** — Y una API key de GptLuna, que es la clave que nos permite usar su modelo.

## Paso 1 · Docker

- **3:13** — Bien, ¡manos a la obra! Abrí en Visual Studio Code una carpeta vacía llamada 'asistente'.
- **3:19** — Lo primero es levantar los tres servicios que necesitamos: Qdrant, PostgreSQL y Ollama.
- **3:24** — Para no instalarlos uno por uno, usaremos Docker. Creamos un archivo llamado docker-compose.yml.
- **3:38** — Dentro de 'services' definimos cada servicio. El primero es Qdrant.
- **3:42** — 'image' es el programa que Docker va a descargar, y 'ports' es el puerto por el que nos vamos a conectar: el 6333.
- **3:51** — El volumen sirve para que los datos no se borren cuando apaguemos el contenedor.
- **4:12** — Ahora PostgreSQL. Con 'environment' le decimos el usuario, la contraseña y el nombre de la base de datos.
- **4:18** — Recuerda estos datos, porque los usaremos más adelante para conectarnos.
- **4:32** — Y por último Ollama, en el puerto 11434. Él se encargará de generar los embeddings.
- **4:43** — Al final declaramos los tres volúmenes. Guardamos con Control + S.
- **4:47** — Ahora abrimos la terminal integrada de VS Code con Control + comilla invertida.
- **4:53** — Y escribimos 'docker compose up -d'. La '-d' hace que los servicios corran en segundo plano.
- **4:59** — La primera vez tarda un poco, porque Docker descarga las imágenes. Listo, los tres servicios están corriendo.
- **5:05** — Ahora descargamos dentro de Ollama el modelo que genera los embeddings: nomic-embed-text.

## Paso 2 · Entorno Python

- **5:15** — Ahora preparamos Python. Primero creamos un entorno virtual: una carpeta donde se instalan las librerías solo para este proyecto.
- **5:23** — Mira, en el explorador apareció la carpeta .venv.
- **5:27** — Lo activamos. En Windows el comando es '.venv\Scripts\activate'.
- **5:32** — Fíjate que ahora la terminal muestra '(.venv)' al inicio: eso significa que el entorno está activo.
- **5:39** — Ahora creamos el archivo requirements.txt, con la lista de librerías que vamos a necesitar.
- **5:57** — 'langchain' es la librería principal que une todas las piezas.
- **6:01** — Cada 'langchain-algo' es una integración: openai para hablar con GptLuna, ollama para los embeddings, y qdrant y postgres para las bases de datos.
- **6:12** — text-splitters sirve para cortar textos largos, psycopg conecta Python con PostgreSQL, y python-dotenv lee nuestra configuración.
- **6:21** — Las instalamos con 'pip install -r requirements.txt'.
- **6:28** — ¡Perfecto! Ya tenemos todo instalado.

## Paso 3 · Configuración

- **6:31** — Ahora la configuración. Creamos un archivo llamado .env: aquí van las claves y direcciones, separadas del código.
- **6:45** — GptLuna funciona igual que la API de OpenAI, así que solo necesitamos tres datos: la URL, la API key y el nombre del modelo.
- **6:53** — Revisa los valores exactos en el panel de tu cuenta de GptLuna, y reemplaza 'tu_api_key' por tu clave.
- **7:21** — Debajo van las direcciones de los servicios que levantamos con Docker, con los mismos puertos.
- **7:27** — Fíjate que en PG_URL aparecen el usuario, la contraseña y la base de datos que definimos en docker-compose.
- **7:36** — Un consejo importante: este archivo tiene tu clave secreta. ¡Nunca lo subas a GitHub!

## Paso 4 · Documentos

- **7:41** — Ahora necesitamos los documentos que el asistente va a 'leer'. Creamos una carpeta docs con un archivo empresa.txt.
- **8:00** — Como ejemplo, uso la información de una cafetería imaginaria: Luna Café. Su horario, su producto estrella, el delivery y el contacto.
- **8:08** — Tú aquí puedes poner la información de tu negocio, tus manuales o tus preguntas frecuentes.

## Paso 5 · ingest.py

- **8:14** — Ahora sí, nuestro primer programa: ingest.py. Su trabajo es leer los documentos, convertirlos en vectores y guardarlos en Qdrant.
- **8:36** — Empezamos importando lo que vamos a usar. 'os' nos permite leer variables de configuración, y 'Path' trabajar con archivos.
- **8:43** — De LangChain traemos Document, el cortador de textos, los embeddings de Ollama y la conexión con Qdrant.
- **8:52** — load_dotenv() lee el archivo .env, para que podamos usar esas variables en el código.
- **9:11** — Aquí recorremos todos los archivos .txt de la carpeta docs.
- **9:15** — Por cada archivo creamos un Document de LangChain: page_content es el texto, y en metadata guardamos el nombre del archivo.
- **9:35** — Los documentos largos se cortan en fragmentos de 500 caracteres. Así, luego buscamos solo el pedazo que importa.
- **9:43** — chunk_overlap repite 50 caracteres entre un fragmento y el siguiente, para no cortar una idea por la mitad.
- **10:01** — Creamos el generador de embeddings con Ollama. Con os.getenv leemos el modelo y la dirección desde el archivo .env.
- **10:21** — Y aquí la magia: from_documents toma cada fragmento, le pide a Ollama su vector, y guarda todo en la colección de Qdrant.
- **10:35** — Al final mostramos un mensaje con cuántos fragmentos se guardaron. Guardamos el archivo.
- **10:40** — Vamos a ejecutarlo en la terminal: python ingest.py.
- **10:44** — ¡Funciona! Como nuestro documento es corto, quedó en un solo fragmento. Ya está guardado en Qdrant.

## Paso 6 · app.py

- **10:51** — Ahora la parte principal: el asistente. Creamos el archivo app.py.
- **11:28** — Importamos os, uuid para crear un identificador único para cada conversación, y psycopg para conectarnos a PostgreSQL.
- **11:38** — Luego, una pieza de LangChain por cada servicio: GptLuna, Ollama, Qdrant y la memoria en PostgreSQL.
- **11:46** — Y estas son herramientas para armar la 'cadena', que es el camino que sigue cada pregunta. Las veremos en un momento.
- **12:11** — Configuramos el LLM. Como GptLuna es compatible con OpenAI, usamos ChatOpenAI y solo cambiamos la base_url por la de GptLuna.
- **12:20** — La temperatura controla la creatividad: con 0.3 las respuestas son más precisas y menos inventadas.
- **12:52** — Ahora nos conectamos a la colección que ya creamos con ingest.py. Es importante usar el mismo modelo de embeddings.
- **13:06** — El retriever es nuestro buscador: por cada pregunta nos devolverá los 3 fragmentos más parecidos.
- **13:26** — Ahora la memoria. Nos conectamos a PostgreSQL con la dirección del .env, y creamos la tabla chat_history, donde se guardarán los mensajes.
- **13:43** — Esta función recibe el identificador de un hilo, el session_id, y devuelve el historial de esa conversación.
- **13:50** — Así, cada conversación tiene su propia memoria, separada de las demás.
- **14:13** — Estas son las instrucciones del asistente: le decimos que sea amable, que responda solo con el contexto, y que si no sabe, lo diga.
- **14:21** — Las llaves con 'context' son un espacio vacío: ahí LangChain pondrá los textos que encuentre Qdrant.
- **14:38** — El prompt es el mensaje completo que le enviaremos a GptLuna, y tiene tres partes.
- **14:43** — Las instrucciones con el contexto, el historial de la conversación, y la pregunta actual del usuario.
- **15:00** — buscar_contexto toma la pregunta, le pide al retriever los fragmentos parecidos, y une sus textos en uno solo.
- **15:16** — Y esta es la cadena. El símbolo de la barra vertical significa 'y luego pásaselo a'.
- **15:21** — Primero agregamos el contexto, luego armamos el prompt, se lo pasamos a GptLuna, y al final nos quedamos solo con el texto de la respuesta.
- **15:42** — Finalmente envolvemos la cadena con RunnableWithMessageHistory. Esto le agrega la memoria.
- **15:48** — En cada mensaje lee el historial del hilo, y al terminar guarda automáticamente la pregunta y la respuesta en PostgreSQL.
- **16:10** — Ya solo falta el chat en la consola. Primero pedimos el id del hilo: si presionamos Enter, se crea uno nuevo con uuid4.
- **16:38** — Y este bucle se repite para siempre: pide una pregunta, se la envía al asistente junto con el session_id, y muestra la respuesta.
- **16:46** — Si escribimos 'salir', el programa termina.
- **16:50** — ¡Y listo! Todo el asistente en unas 90 líneas de código. Vamos a probarlo.

## Paso 7 · ¡A probar!

- **16:56** — Maximizo la terminal para verlo mejor, y ejecutamos python app.py.
- **17:09** — Presioné Enter, así que se creó un hilo nuevo. Le pregunto por el producto estrella... ¡y responde con la información de nuestro documento!
- **17:25** — Ahora pregunto '¿Y hasta qué hora atienden?'. Funciona porque recibe el historial de la conversación.
- **17:38** — Ahora la prueba de fuego para la memoria: salimos, y volvemos a entrar con el mismo id de hilo.
- **17:57** — ¡Lo recuerda todo! Porque cada mensaje quedó guardado en PostgreSQL.
- **18:03** — Si quieres comprobarlo, podemos ver la tabla chat_history directamente en la base de datos.
- **18:09** — Ahí están: los mensajes del usuario como 'human' y los del asistente como 'ai'.

## Resumen

- **18:14** — Hagamos un resumen. Levantamos Qdrant, PostgreSQL y Ollama con Docker.
- **18:19** — Con ingest.py convertimos nuestros documentos en vectores y los guardamos en Qdrant.
- **18:24** — Y con app.py creamos un asistente con RAG y memoria, usando GptLuna y LangChain.
- **18:31** — Como reto, prueba agregar tus propios documentos a la carpeta docs, vuelve a ejecutar ingest.py, y hazle preguntas.
- **18:40** — El código completo está en GitHub, el enlace está en la descripción.
- **18:44** — Si te sirvió, dale like, suscríbete y déjame en los comentarios tus dudas. En la próxima clase le crearemos una interfaz web. ¡Nos vemos!

## Capítulos para la descripción de YouTube

```
0:00 Introducción
0:15 Resultado final
0:49 Conceptos básicos
3:13 Paso 1 · Docker
5:15 Paso 2 · Entorno Python
6:31 Paso 3 · Configuración
7:41 Paso 4 · Documentos
8:14 Paso 5 · ingest.py
10:51 Paso 6 · app.py
16:55 Paso 7 · ¡A probar!
18:14 Resumen
```
