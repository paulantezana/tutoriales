# Guion de narración · 02-gemma-en-consola

Lee cada frase en voz alta en el momento indicado. Los tiempos coinciden con `02-gemma-en-consola.mp4`.
El video ya trae esta narración con voz generada (Kokoro). Si prefieres grabar tu propia voz, pon `NARRACION = False` en `render.py` y graba siguiendo estos tiempos.


## Introducción

- **0:00** — Hola, ¿qué tal? Bienvenidos al video dos del curso de YARBYS.
- **0:03** — Hoy vamos a descargar Gemma 4, vamos a escribir el cerebro de YARBYS, y lo vamos a probar en la consola y con el depurador.
- **0:11** — Al final de este video, Gemma va a responder su primera pregunta dentro del celular, y sin internet.
- **0:19** — En el video anterior creamos el proyecto y lo ejecutamos en el celular. Recuerda la arquitectura: pantallas arriba, Yarbys en el medio, y los servicios abajo.
- **0:28** — Hoy escribimos dos servicios: modelos, que descarga Gemma, y cerebro, que habla con ella. Todavía sin pantallas: primero probamos que funcione, y la pantalla viene en el próximo video.

## ¿Qué es un LLM?

- **0:40** — Empecemos por el cerebro: el LLM, o modelo de lenguaje grande. Es una inteligencia artificial que aprendió a escribir leyendo muchísimo texto: libros, páginas web y conversaciones.
- **0:52** — Funciona como el autocompletado del teclado de tu celular, pero mucho más inteligente. Divide el texto en pedacitos llamados tokens, y calcula cuál es el siguiente token más probable.
- **1:03** — Así, token por token, va escribiendo la respuesta. Por eso, en el código, la respuesta nos va a llegar en pedacitos.
- **1:10** — Todo lo que el modelo aprendió se guarda en miles de millones de números, llamados parámetros. Más parámetros suele significar más inteligencia, pero también un archivo más pesado.

## Modelos para celular

- **1:22** — Los modelos de la nube tienen cientos de miles de millones de parámetros. Necesitan centros de datos enormes: no caben en un teléfono.
- **1:30** — Pero existen modelos pequeños, diseñados para celulares. Y además se comprimen con una técnica llamada cuantización: cada número se guarda con menos bits, como cuando comprimes una foto.
- **1:41** — Nosotros usaremos Gemma 4 E2B, de Google. Es gratuito, entiende muy bien el español, y su archivo pesa 2.6 gigas. Lo ejecutaremos con LiteRT-LM, el motor de Google para correr modelos en celulares.
- **1:55** — Para usarlo, tu celular necesita Android 11 o superior y, de preferencia, 8 gigas de RAM. Con 6 también funciona, pero más lento.

## Instalar el paquete

- **2:05** — Para ejecutar Gemma en Flutter necesitamos un paquete. Los paquetes se buscan en pub.dev, así que abrimos el navegador.
- **2:13** — En el buscador escribimos flutter_edge_ai.
- **2:16** — Y abrimos el primer resultado.
- **2:19** — Esta es la página del paquete. Dice qué hace: ejecuta modelos de inteligencia artificial dentro del dispositivo, sin servidor. Vamos a la pestaña Installing.
- **2:31** — Aquí está el comando para instalarlo. Junto con él instalamos su motor, flutter_edge_ai_litertlm, que es el que ejecuta los archivos de Gemma.
- **2:41** — Volvemos a VS Code y, en la terminal, los agregamos con flutter pub add.
- **2:51** — flutter pub add los anotó en pubspec.yaml, en dependencies. El símbolo del sombrerito significa: esta versión, o una más nueva que sea compatible.

## Permiso de internet

- **3:01** — Y como la app va a descargar el modelo, en el AndroidManifest le damos permiso de usar internet.
- **3:07** — Agregamos uses-permission INTERNET, con un comentario: solo lo usamos para descargar los modelos. Después, YARBYS funciona sin internet.

## Los archivos de hoy

- **3:18** — Ahora creamos los archivos de hoy. En lib, una carpeta servicios, que es la capa de abajo de la arquitectura. Dentro, modelos.dart: el que descarga los modelos de inteligencia artificial.
- **3:29** — Y cerebro.dart: el que le pasa el texto a Gemma y nos devuelve su respuesta.

## modelos.dart

- **3:35** — Empezamos por modelos.dart. A la derecha tienes el mapa de este archivo: una clase, Modelos, con la dirección de Gemma, una propiedad para saber si ya está descargada, y un método para descargarla.
- **3:47** — Primero importamos flutter_edge_ai, el paquete que acabamos de instalar. import nos deja usar el código de otro archivo o paquete.
- **3:56** — Ahora la clase Modelos, con un comentario arriba que dice qué hace. Los comentarios con tres barras son de documentación: VS Code los muestra cuando pasas el mouse sobre la clase.
- **4:07** — Primero necesitamos la dirección de Gemma 4. ¿De dónde la sacamos?
- **4:12** — Los modelos abiertos se publican en Hugging Face, la plataforma donde Google y otras empresas comparten sus modelos.
- **4:19** — Entras a huggingface.co, buscas gemma-4-E2B-it-litert-lm y abres el modelo de la cuenta litert-community. En la pestaña Files and versions está el archivo gemma-4-E2B-it.litertlm, de 2.6 gigas. Haces clic derecho en su botón de descarga y copias la dirección del enlace.
- **4:38** — Fíjate en las partes del enlace: el sitio, quién lo publica, el nombre del modelo, la palabra resolve, que significa descargar, la versión, que aquí es main, la más reciente, y el nombre del archivo.
- **4:50** — Volvemos a VS Code. Escribimos un comentario, y la constante urlGemma. static significa que pertenece a la clase: la usamos como Modelos.urlGemma, sin crear objetos. Y const, que nunca cambia. La dirección no la escribimos a mano: la pegamos.
- **5:07** — Luego listos: un getter, que es una propiedad calculada. Devuelve un bool, verdadero o falso, según si Gemma ya está en el celular. La flecha devuelve el resultado de hasActiveModel.
- **5:18** — Y el método descargarGemma. Recibe progreso: una función a la que le iremos avisando el porcentaje. Future de void significa que termina más tarde y no devuelve nada, y async, que adentro podemos esperar con await.
- **5:31** — Adentro, installModel prepara la instalación. Le decimos qué modelo es, Gemma 4, para que sepa cómo hablarle, y que el archivo es .litertlm, el formato del motor LiteRT-LM.
- **5:43** — Y encadenamos tres pasos: fromNetwork, que lo baje de nuestra dirección; withProgress, que nos avise el porcentaje; e install, que lo descarga y lo instala. Con await esperamos a que termine.
- **5:56** — Y modelos.dart está listo.

## cerebro.dart

- **6:00** — Ahora cerebro.dart. Tiene una clase, Cerebro, con la personalidad de YARBYS, y un método, responder.
- **6:06** — Importamos flutter_edge_ai otra vez, porque aquí también lo usamos.
- **6:11** — Creamos la clase Cerebro, con su comentario.
- **6:15** — Primero la personalidad: las reglas que Gemma va a seguir en toda la conversación. Le decimos quién es, que responda en español, en máximo tres oraciones y sin markdown, es decir, sin asteriscos ni listas. El guion bajo al inicio del nombre la hace privada: solo se usa dentro de este archivo.
- **6:32** — Ahora el método responder. Recibe el prompt: el texto que va a leer Gemma. Y devuelve un Stream de String: no una respuesta completa, sino un flujo de pedacitos de texto que llegan uno tras otro. async con asterisco es lo que nos deja ir entregando esos pedacitos.
- **6:48** — Primero cargamos Gemma en la memoria del celular. getActiveModel nos da el modelo que descargamos. maxTokens, 4096, es el contexto: cuánto texto puede leer Gemma de una vez, sumando la pregunta y la respuesta. Y await espera a que cargue, porque tarda unos segundos.
- **7:05** — Con el modelo creamos una conversación. systemInstruction es la personalidad que escribimos arriba, y maxOutputTokens, 512, el largo máximo de la respuesta.
- **7:15** — Ahora un try con finally. Lo que va en finally se ejecuta siempre, aunque algo falle. Ahí cerramos el chat con close, para liberar la memoria del celular.
- **7:25** — Dentro del try le enviamos el prompt con addQueryChunk. Message es un mensaje, e isUser true le dice a Gemma que lo escribió la persona.
- **7:34** — Y aquí la magia. generateChatResponseAsync empieza a generar la respuesta, y await for recorre cada pedacito apenas llega: es un for que espera. Gemma puede devolver distintos tipos de respuesta; nos quedamos con las de texto. Y yield entrega ese token a quien llamó a responder, sin esperar al resto.
- **7:52** — El cerebro está listo. Ahora, ¿cómo lo probamos si todavía no tenemos pantalla? Con la consola.

## Probar en main.dart

- **7:58** — Como vamos a reemplazar la app de ejemplo, primero borramos su prueba, test, widget_test.dart, que ya no nos sirve.
- **8:06** — Abrimos main.dart y borramos la app de ejemplo: Control + A y Suprimir.
- **8:11** — Importamos material, que trae los widgets de Flutter, flutter_edge_ai, y su motor LiteRT-LM.
- **8:18** — Y nuestros dos archivos: cerebro y modelos.
- **8:23** — La función main ahora es async, porque adentro vamos a esperar con await.
- **8:29** — Primero, runApp con una pantalla mínima: un texto en el centro que dice Mira la consola. Solo para que el celular no quede en blanco.
- **8:38** — Luego encendemos el motor de inteligencia artificial con initialize, y le decimos que use LiteRtLmEngine: el motor que ejecuta los archivos .litertlm.
- **8:49** — Ahora la prueba. Si Gemma todavía no está en el celular, la descargamos, y en cada aviso de progreso imprimimos el porcentaje con debugPrint. debugPrint escribe en la consola de depuración.
- **9:01** — Imprimimos la pregunta...
- **9:03** — ...le preguntamos al cerebro quién es, y con join juntamos todos los tokens del flujo en un solo texto.
- **9:10** — Y lo imprimimos en la consola.

## Resultado: la consola

- **9:14** — Momento de la verdad. Presionamos F5.
- **9:20** — La primera vez, la app descarga los 2.6 gigas de Gemma. Aquí lo aceleré: según tu internet, puede tardar varios minutos. Usa Wi-Fi.
- **9:29** — Ya descargó. Ahora Gemma se carga en la memoria y empieza a pensar... y...
- **9:35** — ¡Ahí está! La primera respuesta de Gemma, generada dentro del celular.

## El depurador

- **9:39** — Ahora, otra forma de ver lo que pasa: el depurador. Hago clic a la izquierda del número de línea, en el último debugPrint, y aparece un punto rojo: un punto de parada.
- **9:49** — Y reinicio la app con Control + Shift + F5. Esta vez Gemma ya está en el celular, así que no descarga nada.
- **9:58** — La app se detuvo en el punto de parada: la línea amarilla todavía no se ejecutó.
- **10:03** — Si paso el mouse sobre la variable respuesta, VS Code me muestra lo que tiene adentro: el texto completo que generó Gemma.
- **10:11** — Así puedes revisar cualquier variable mientras la app corre. Continúo con F5.

## Sin internet

- **10:18** — Y la prueba final: en el celular, que solo muestra Mira la consola, activo el modo avión.
- **10:23** — Y vuelvo a reiniciar la app desde VS Code.
- **10:30** — Y Gemma sigue respondiendo, sin internet. Todo ocurre dentro del celular.

## Lo que sigue

- **10:36** — Y listo. Hoy instalamos el paquete, descargamos Gemma, escribimos su cerebro, y lo probamos en la consola y con el depurador. Gemma ya responde dentro del celular.
- **10:46** — Pero leer la consola no es muy cómodo. En el próximo video le hacemos su primera pantalla: un chat sencillo, donde vas a escribir tu pregunta y ver la respuesta aparecer palabra por palabra. ¡Nos vemos!

## Capítulos para la descripción de YouTube

```
0:00 Introducción
0:40 ¿Qué es un LLM?
1:22 Modelos para celular
2:05 Instalar el paquete
3:01 Permiso de internet
3:18 Los archivos de hoy
3:34 modelos.dart
5:58 cerebro.dart
7:58 Probar en main.dart
9:14 Resultado: la consola
9:39 El depurador
10:17 Sin internet
10:36 Lo que sigue
```
