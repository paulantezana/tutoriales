# Guion de narración · 01-que-vamos-a-construir

Lee cada frase en voz alta en el momento indicado. Los tiempos coinciden con `01-que-vamos-a-construir.mp4`.
El video ya trae esta narración con voz generada (Kokoro). Si prefieres grabar tu propia voz, pon `NARRACION = False` en `render.py` y graba siguiendo estos tiempos.


## Introducción

- **0:00** — Hola, ¿qué tal? Bienvenidos a este curso. Vamos a crear YARBYS: nuestro propio asistente de inteligencia artificial, que vive cien por ciento dentro del celular.
- **0:09** — En este primer video vas a ver el resultado final, vas a entender cómo funciona por dentro, y vamos a preparar el proyecto en Flutter.
- **0:18** — Y al terminar este video ya vas a tener la app corriendo en tu celular. Así que, vamos.

## El resultado final

- **0:25** — Este es YARBYS en mi celular, así queda al final del curso. Y fíjate en algo: está en modo avión. No hay internet.
- **0:32** — Le pregunto qué tengo el miércoles.
- **0:47** — Respondió con mi agenda, que le enseñé antes, y me dice de qué documento sacó la información. Ahora le hablo con el micrófono.
- **1:09** — Me entendió por voz y me respondió hablando. Y todo esto ocurre dentro del teléfono: el modelo de inteligencia artificial, la base de datos y la memoria.

## El plan del curso

- **1:19** — El curso tiene nueve videos, y vamos a avanzar poco a poco. En cada video agregamos una pieza, y siempre terminamos con algo funcionando.
- **1:27** — Primero haremos que Gemma responda en la consola, sin ninguna pantalla. Luego le hacemos un chat sencillo, le damos memoria, y le enseñamos a leer tus documentos.
- **1:37** — Después le agregamos la voz, la dejamos bonita con su núcleo animado, y al final generamos el APK para instalarlo en cualquier celular.

## ¿IA en el celular?

- **1:47** — Antes de programar, un poco de teoría. Cuando usas ChatGPT, tu pregunta viaja por internet hasta un centro de datos lleno de computadoras gigantes. Allí se genera la respuesta, y vuelve a tu teléfono.
- **1:59** — En YARBYS es distinto. El modelo de inteligencia artificial es un archivo que descargamos una sola vez, y que vive dentro del celular. El procesador del teléfono hace todo el trabajo.
- **2:11** — Eso tiene grandes ventajas: tus datos nunca salen del teléfono, funciona sin internet, no pagas por cada pregunta y no esperas a ningún servidor.
- **2:20** — ¿Las desventajas? El modelo es más pequeño que los de la nube, ocupa espacio, y usa la memoria RAM y la batería. Por eso elegiremos un modelo pensado para celulares.

## Las 5 piezas

- **2:31** — Para construir a YARBYS necesitamos cinco piezas, y todas viven dentro del celular.
- **2:37** — Un cerebro, que es el modelo de lenguaje: Gemma 4. Y un traductor de textos a números: EmbeddingGemma.
- **2:43** — Un buscador de información, que es la base de datos vectorial Qdrant Edge. Y una memoria para las conversaciones: SQLite.
- **2:51** — Y la voz, para escuchar y hablar. Flutter será el cuerpo: la app que une todas las piezas. Cada pieza la vamos a explicar en detalle en su propio video.

## La arquitectura

- **3:01** — Ahora, ¿cómo vamos a ordenar el código? En tres capas. Arriba, las pantallas: lo que ve el usuario. Inicio, el chat y tus documentos.
- **3:09** — En el medio, la clase Yarbys: el asistente. Recibe tu pregunta y coordina a todos los demás para responderla.
- **3:16** — Y abajo, los servicios. Cada uno hace una sola cosa: modelos descarga la inteligencia artificial, cerebro habla con Gemma, memoria guarda las conversaciones, conocimiento busca en tus documentos, y voz escucha y habla.
- **3:29** — Y hay una regla importante: las pantallas solo hablan con Yarbys, nunca directamente con Gemma o con la base de datos. Gracias a eso, cada pieza la podemos probar primero en la consola, y después conectarla a la pantalla.

## Flutter

- **3:44** — Y el cuerpo de YARBYS es Flutter, el framework de Google para crear apps. Con un solo código, en lenguaje Dart, tienes tu app para Android y para iPhone.
- **3:53** — En Flutter todo es un widget: un texto, un botón, una lista. Y los combinamos como bloques de Lego para armar cada pantalla.
- **4:01** — Las piezas de inteligencia artificial las agregamos con paquetes de pub.dev, la tienda de librerías de Flutter. Las iremos instalando a medida que las necesitemos.

## Instalación

- **4:12** — Pasemos a la instalación en Windows. Primero, Flutter: lo descargas desde flutter.dev, lo descomprimes, por ejemplo, en C:\flutter, y agregas la carpeta bin al PATH.
- **4:23** — Segundo, Android Studio. Trae el Android SDK, que es lo que necesitamos para compilar apps de Android.
- **4:30** — Tercero, Visual Studio Code con la extensión de Flutter. Y cuarto, tu celular Android con la depuración USB activada.
- **4:37** — Para activarla: en Ajustes, Acerca del teléfono, toca siete veces Número de compilación. Luego, en Opciones de desarrollador, activa Depuración USB, y conecta el celular a la computadora con el cable.

## Crear el proyecto

- **4:51** — Con todo instalado, abrimos Visual Studio Code. Yo abrí la carpeta C:\proyectos con File, Open Folder. Y abrimos la terminal con Control + comilla invertida.
- **5:02** — Primero revisamos que todo esté bien instalado con flutter doctor.
- **5:07** — Si todo sale con un check verde, estamos listos. Fíjate en Connected device: ahí aparece el celular conectado por USB.
- **5:14** — Ahora creamos el proyecto con flutter create. Con --org ponemos el identificador de nuestra empresa, y con --platforms indicamos que la app será para Android y para iPhone.
- **5:25** — Listo. Ahora abrimos la carpeta yarbys con File, Open Folder.

## 

- **5:30** — Este es un proyecto de Flutter. Las carpetas android e ios tienen la configuración de cada sistema. En lib va nuestro código en Dart, y pubspec.yaml es como la lista de compras del proyecto: ahí van los paquetes que usamos.

## La app de ejemplo

- **5:43** — flutter create nos dejó una app de ejemplo en lib, main.dart. Vamos a leerla juntos, porque así se arma cualquier app de Flutter.
- **5:52** — Todo empieza en la función main: es lo primero que se ejecuta. Y runApp toma un widget, MyApp, y lo muestra en la pantalla.
- **6:02** — MyApp es un StatelessWidget: un widget que no cambia. Su método build devuelve un MaterialApp, que define el título de la app, los colores, y en home, la primera pantalla.
- **6:14** — MyHomePage, en cambio, es un StatefulWidget: tiene datos que cambian con el tiempo. Esos datos viven en otra clase, su estado: _MyHomePageState.
- **6:26** — El estado guarda un contador. Y fíjate en setState: cambia el dato y le avisa a Flutter que vuelva a dibujar la pantalla. Esta idea la vamos a usar muchísimo.
- **6:38** — Y build arma la pantalla con bloques: un Scaffold, que es la página, con una AppBar arriba, que muestra el título.
- **6:46** — En el cuerpo, un Center con una columna de textos, y el botón flotante con el signo más, que al tocarlo llama a _incrementCounter.

## Configurar Android

- **6:55** — Antes de ejecutarla, dos ajustes de Android. Abrimos android, app, build.gradle.kts.
- **7:02** — Gemma necesita Android 11 o superior, que es la versión 30 de la API. Así que cambiamos minSdk por 30, con un comentario que explica por qué.
- **7:12** — Y en android, app, src, main, abrimos AndroidManifest.xml.
- **7:17** — Aquí cambiamos el nombre que se ve debajo del ícono: YARBYS, en mayúsculas.

## Ejecutar en el celular

- **7:23** — Ahora sí, a ejecutarla. Con el celular conectado, abrimos main.dart y presionamos F5. Abajo a la derecha, en la barra de estado, se ve el dispositivo elegido: mi Pixel 8.
- **7:40** — La primera vez tarda un poco: Flutter compila la app, la instala en el celular, y conecta el depurador. Todo lo que pase se ve aquí abajo, en la Debug Console.
- **7:50** — Y ahí está, en mi celular. Esta es la app de ejemplo de Flutter. Si toco el botón más, el contador sube.
- **7:56** — Cada toque llama a setState, y Flutter vuelve a dibujar el número. Fíjate también en la cinta que dice DEBUG: estamos en modo depuración.

## Hot reload

- **8:05** — Ahora, la magia de Flutter: el hot reload. Con la app corriendo, cambio el título de la pantalla.
- **8:11** — En lugar de Flutter Demo Home Page, escribo: Hola, soy YARBYS.
- **8:17** — Y guardo con Control + S.
- **8:19** — Y el cambio aparece en el celular al instante, sin volver a compilar, y sin perder el contador, que sigue en tres.
- **8:26** — Así vamos a trabajar todo el curso: escribimos, guardamos, y vemos el resultado de inmediato.

## Lo que sigue

- **8:33** — Y listo. En este video viste el resultado final, entendiste cómo funciona, y ya tienes el proyecto corriendo en tu celular.
- **8:41** — En el próximo video empieza lo bueno: descargamos Gemma 4, escribimos su cerebro, y le hacemos su primera pregunta, todavía sin pantalla, mirando la respuesta en la consola. ¡Nos vemos en el siguiente video!

## Capítulos para la descripción de YouTube

```
0:00 Introducción
0:24 El resultado final
1:19 El plan del curso
1:47 ¿IA en el celular?
2:31 Las 5 piezas
3:01 La arquitectura
3:44 Flutter
4:12 Instalación
4:51 Crear el proyecto
5:43 La app de ejemplo
6:55 Configurar Android
7:23 Ejecutar en el celular
8:05 Hot reload
8:33 Lo que sigue
```
