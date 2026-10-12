# Guion de narración

Lee cada frase en voz alta mientras se ve la escena. Los tiempos coinciden con `tutorial.mp4`.


## 0:00 · Introducción

- **0:00** — Hola a todos. Hoy vamos a crear nuestro propio asistente de inteligencia artificial en Python.
- **0:04** — Usaremos GptLuna, LangChain, Qdrant, Ollama y PostgreSQL.

## 0:09 · Introducción

- **0:09** — Vamos a construir un chat que responde usando nuestros propios documentos. A esto se le llama RAG.
- **0:14** — GptLuna será el cerebro, Ollama generará los embeddings y Qdrant guardará los vectores.
- **0:19** — PostgreSQL recordará cada conversación, y LangChain unirá todas las piezas.

## 0:24 · Arquitectura

- **0:24** — Primero, ingest.py lee los documentos y los divide en fragmentos.
- **0:27** — Ollama convierte cada fragmento en un vector, y los guardamos en Qdrant.
- **0:31** — Luego, cuando el usuario pregunta, app.py busca el contexto más parecido en Qdrant...
- **0:35** — ...y lee el historial del hilo desde PostgreSQL.
- **0:39** — Con todo eso arma el prompt y se lo envía a GptLuna, que genera la respuesta.

## 0:43 · Requisitos

- **0:43** — Solo necesitas Python 3.10 o superior, Docker y una API key de GptLuna.

## 0:51 · Paso 1 · Servicios con Docker

- **0:51** — Paso uno: levantamos los servicios con Docker. Creamos el archivo docker-compose.yml.
- **0:55** — Qdrant, nuestra base de datos vectorial, en el puerto 6333.
- **0:59** — PostgreSQL en el puerto 5432, con usuario, contraseña y la base de datos 'asistente'.
- **1:03** — Y Ollama en el puerto 11434. Cada servicio tiene su volumen para no perder los datos.

## 1:08 · Paso 1 · Servicios con Docker

- **1:08** — Levantamos todo con docker compose up -d.
- **1:13** — Y descargamos el modelo de embeddings nomic-embed-text dentro de Ollama.

## 1:19 · Paso 2 · Entorno de Python

- **1:19** — Paso dos: preparamos Python. Estas son las librerías que vamos a usar.
- **1:24** — Las integraciones de LangChain para OpenAI, Ollama, Qdrant y Postgres, más psycopg y python-dotenv.

## 1:28 · Paso 2 · Entorno de Python

- **1:28** — Creamos un entorno virtual, lo activamos e instalamos las dependencias.

## 1:40 · Paso 2 · Configuración

- **1:40** — Ahora creamos el archivo .env con la configuración.
- **1:43** — GptLuna expone una API compatible con OpenAI: solo necesitamos la URL base, la API key y el modelo.
- **1:47** — Revisa en el panel de GptLuna la URL y el nombre del modelo exactos de tu cuenta.
- **1:50** — También las URLs de Ollama, Qdrant y PostgreSQL que levantamos con Docker.

## 1:53 · Paso 3 · Nuestros documentos

- **1:53** — Como ejemplo, usaremos un documento sobre una cafetería ficticia: Luna Café.
- **1:58** — Aquí puedes poner tus propios archivos: manuales, preguntas frecuentes, políticas...

## 2:02 · Paso 3 · Ingesta de documentos

- **2:02** — Paso tres: el script de ingesta, ingest.py.
- **2:07** — Leemos todos los archivos .txt de la carpeta docs y los convertimos en documentos de LangChain.
- **2:12** — Los dividimos en fragmentos de 500 caracteres, con un pequeño solapamiento.
- **2:17** — Creamos el generador de embeddings con Ollama, usando el modelo nomic-embed-text.
- **2:21** — Y con from_documents guardamos todos los fragmentos en una colección de Qdrant.

## 2:26 · Paso 3 · Ingesta de documentos

- **2:26** — Lo ejecutamos... y nuestros documentos ya están en Qdrant.
- **2:30** — Puedes revisarlos en el panel web de Qdrant, en localhost:6333/dashboard.

## 2:34 · Paso 4 · El asistente

- **2:34** — Paso cuatro: el asistente, app.py. Primero importamos LangChain y sus integraciones.

## 2:44 · Paso 4 · El LLM: GptLuna

- **2:44** — Configuramos GptLuna con ChatOpenAI. El truco está en cambiar la base_url.
- **2:49** — Así funciona con cualquier API compatible con OpenAI. Una temperatura baja da respuestas más precisas.

## 2:53 · Paso 4 · Búsqueda en Qdrant

- **2:53** — Nos conectamos a la colección que ya existe en Qdrant, con los mismos embeddings de Ollama.
- **2:59** — El retriever devolverá los 3 fragmentos más parecidos a cada pregunta.

## 3:05 · Paso 4 · Memoria en PostgreSQL

- **3:05** — Ahora la memoria. Nos conectamos a PostgreSQL y creamos la tabla chat_history.
- **3:11** — La función obtener_historial devuelve los mensajes de un hilo según su session_id.

## 3:16 · Paso 4 · Prompt y cadena RAG

- **3:16** — El prompt tiene tres partes: las instrucciones con el contexto, el historial y la pregunta.
- **3:21** — buscar_contexto consulta Qdrant y une el texto de los fragmentos encontrados.
- **3:25** — La cadena: agrega el contexto, arma el prompt, llama a GptLuna y devuelve texto.
- **3:30** — RunnableWithMessageHistory lee y guarda automáticamente cada mensaje en PostgreSQL.

## 3:34 · Paso 4 · Chat en consola

- **3:34** — Por último, un bucle de chat. Si no escribimos un ID de hilo, se crea uno nuevo.
- **3:41** — Cada pregunta se envía con su session_id, así cada hilo tiene su propia memoria.

## 3:48 · Paso 5 · ¡A probar!

- **3:48** — ¡Ahora sí, a probar! Ejecutamos python app.py y dejamos que cree un hilo nuevo.
- **3:54** — Preguntamos por el producto estrella: responde con la información de nuestro documento.
- **4:00** — Las preguntas de seguimiento funcionan porque, en cada mensaje, el asistente recibe el historial del hilo.
- **4:06** — Y toda la información sale de Qdrant, no de lo que el modelo 'cree' saber.

## 4:12 · Paso 5 · Memoria persistente

- **4:12** — Si cerramos el programa y lo abrimos con el mismo ID de hilo...
- **4:19** — ...el asistente recuerda toda la conversación, porque está guardada en PostgreSQL.
- **4:27** — Podemos comprobarlo consultando directamente la tabla chat_history.

## 4:34 · Resumen

- **4:34** — ¡Y listo! Ya tienes un asistente con RAG y memoria persistente, todo en menos de 100 líneas.
- **4:41** — Como siguiente paso puedes cargar PDFs, crear una interfaz web con Streamlit o FastAPI, o mostrar las respuestas en streaming.

## 4:48 · Introducción

- **4:48** — Si te sirvió, dale like, suscríbete y déjame en los comentarios qué quieres que construyamos después. ¡Nos vemos!

## Capítulos para la descripción de YouTube

```
0:00 Introducción
0:24 Arquitectura
0:43 Requisitos
0:51 Paso 1 · Servicios con Docker
1:19 Paso 2 · Entorno de Python
1:40 Paso 2 · Configuración
1:53 Paso 3 · Nuestros documentos
2:02 Paso 3 · Ingesta de documentos
2:34 Paso 4 · El asistente
2:44 Paso 4 · El LLM: GptLuna
2:53 Paso 4 · Búsqueda en Qdrant
3:05 Paso 4 · Memoria en PostgreSQL
3:16 Paso 4 · Prompt y cadena RAG
3:34 Paso 4 · Chat en consola
3:48 Paso 5 · ¡A probar!
4:12 Paso 5 · Memoria persistente
4:34 Resumen
4:48 Introducción
```
