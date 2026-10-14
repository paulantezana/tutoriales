# Curso YARBYS: el código de cada video

Cada carpeta tiene el código **tal como queda al final de ese video**. Solo están los archivos que cambian respecto a `flutter create --org com.paulantezana --platforms android,ios yarbys`. Para seguir el curso desde un video, crea el proyecto y copia encima la carpeta del video anterior.

| Video | Carpeta | Lo que se programa | Termina mostrando |
|---|---|---|---|
| 1 · Qué vamos a construir | `01-proyecto` | Crear el proyecto y configurar Android (`minSdk = 30`, nombre YARBYS) | La app de ejemplo en el celular con el título "Hola, soy YARBYS" |
| 2 · Gemma responde, en la consola | `02-gemma-en-consola` | `servicios/modelos.dart`, `servicios/cerebro.dart` y una prueba en `main.dart` | La respuesta de Gemma en la **Debug Console**, sin internet |
| 3 · Primer chat | `03-primer-chat` | `datos.dart`, `yarbys.dart`, `pantallas/inicio.dart`, `pantallas/chat.dart` | Un chat sencillo: la respuesta aparece palabra por palabra |
| 4 · Memoria con SQLite | `04-memoria` | `servicios/memoria.dart`; `Yarbys` usa el historial | Cierras la app, la abres, y YARBYS recuerda tu nombre |
| 5 · Buscar por significado | `05-buscar-por-significado` | `servicios/conocimiento.dart` y su prueba automática; descarga de EmbeddingGemma | `All tests passed!` y la búsqueda en la consola con su puntaje |
| 6 · Preguntar a tus documentos | `06-tus-documentos` | `pantallas/documentos.dart`; `Yarbys` agrega los fragmentos al prompt | Responde con tu agenda y muestra la fuente |
| 7 · La voz | `07-la-voz` | `servicios/voz.dart`, el botón del micrófono y el estado de YARBYS | Le hablas y te responde hablando |
| 8 · Interfaz bonita | `08-diseno-final` | `tema.dart`, `widgets/burbuja.dart`, `widgets/nucleo.dart` | El diseño final con el núcleo animado |
| 9 · Prueba final y APK | (igual que 08) | `flutter build apk` | El APK instalado y funcionando en modo avión |

`08-diseno-final` es igual a [`../yarbys/`](../yarbys/), el proyecto completo.

## La arquitectura

```
PANTALLAS   inicio · chat · documentos         (lo que ves)
     │ solo hablan con ↓
YARBYS      preguntar(texto) → mensajes         (el asistente: une todo)
     │ usa ↓
SERVICIOS   modelos · cerebro · memoria · conocimiento · voz   (sin pantallas)
```

- Una tarea por clase: `Memoria` guarda y lee; `Cerebro` habla con Gemma.
- Las pantallas nunca llaman a Gemma ni a SQLite directamente: así la lógica se prueba primero en la consola y después se conecta a la pantalla.
- El estado de cada pantalla se maneja con `setState`.
