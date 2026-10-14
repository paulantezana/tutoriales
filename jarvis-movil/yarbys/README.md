# YARBYS: tu asistente de IA 100% en el celular

YARBYS es una app de Flutter con un asistente de IA que funciona sin internet. Lee tus documentos, recuerda tus conversaciones y te responde con voz.

| Pieza | Herramienta | Dónde vive |
|---|---|---|
| Cerebro (LLM) | **Gemma 4 E2B** (`.litertlm`, 2.6 GB) con `flutter_edge_ai` | En el celular |
| Embeddings | **EmbeddingGemma 2** (165 MB) | En el celular |
| Base de datos vectorial | **Qdrant Edge** (`flutter_edge_ai_qdrant`) | En el celular |
| Memoria del chat | **SQLite** (`sqflite`) | En el celular |
| Voz | `speech_to_text` + `flutter_tts` (motores del sistema) | En el celular |

Internet solo se usa una vez, para descargar los modelos. Después YARBYS funciona en modo avión.

## Probar el APK ya compilado (Android)

**Descarga directa** (ábrelo desde el celular): https://github.com/paulantezana/tutoriales/releases/download/yarbys-latest/yarbys.apk

Cada cambio en esta carpeta compila el APK en GitHub Actions (`.github/workflows/yarbys-apk.yml`):

1. En GitHub abre la pestaña **Actions**, elige la última ejecución de **YARBYS APK** y descarga el artefacto **yarbys-apk** (un `.zip` con `yarbys.apk`).
2. Pásalo al celular, ábrelo y permite "instalar apps desconocidas".
3. Abre YARBYS y toca **Descargar modelos** (usa Wi-Fi: son unos 2.8 GB).

Si publicas un **Release** en GitHub, el workflow le adjunta el APK, que así es más fácil de descargar desde el celular.

El APK pesa unos 85 MB; los modelos se descargan dentro de la app.

**Requisitos del celular:** Android 11 o superior, procesador de 64 bits (arm64) y, de preferencia, 8 GB de RAM. Con 6 GB funciona, pero más lento.

## Compilar en Windows

1. Instala [Flutter](https://docs.flutter.dev/get-started/install/windows/mobile) (3.47 o superior) y Android Studio (trae el Android SDK). Revisa con `flutter doctor`.
2. En VS Code instala la extensión **Flutter**.
3. Activa la **depuración USB** en tu celular y conéctalo.
4. En PowerShell:

```powershell
cd jarvis-movil\yarbys
flutter pub get
flutter run --release
```

Para generar el APK: `flutter build apk --release --target-platform android-arm64` (queda en `build\app\outputs\flutter-apk\`).

La primera compilación descarga sola las librerías nativas de LiteRT-LM y de Qdrant Edge.

## iPhone

Se compila en una Mac con Xcode (iOS 15 o superior). En Xcode, en **Signing & Capabilities** del target Runner, agrega **Extended Virtual Addressing** e **Increased Memory Limit**. Sin estas opciones, iOS cierra la app al cargar Gemma 4. Después ejecuta `flutter run --release` con el iPhone conectado.

## Cómo está organizado el código (`lib/`)

Tres capas: las **pantallas** solo hablan con **`Yarbys`**, y `Yarbys` usa los **servicios**. Por eso la misma lógica funciona primero en la consola y después en la pantalla.

```
main.dart                  arranca el motor de IA y la memoria
yarbys.dart                el asistente: une memoria + documentos + cerebro
datos.dart                 Mensaje, Documento y EstadoYarbys
tema.dart                  colores (oscuros y planos)
servicios/
  modelos.dart             descarga Gemma 4 y EmbeddingGemma (una sola vez)
  cerebro.dart             le pasa el prompt a Gemma y devuelve los tokens
  memoria.dart             SQLite: mensajes y documentos
  conocimiento.dart        RAG: fragmentar, crear vectores y buscar en Qdrant Edge
  voz.dart                 escuchar (voz a texto) y hablar (texto a voz)
pantallas/
  inicio.dart              descarga los modelos y luego muestra el chat
  chat.dart                el chat con el núcleo animado
  documentos.dart          agregar y borrar archivos .txt/.md
widgets/
  nucleo.dart              el núcleo animado (CustomPainter)
  burbuja.dart             una burbuja del chat
```

Cada pregunta pasa por `Yarbys.preguntar`:

1. Lee los últimos 6 mensajes (SQLite) y guarda tu pregunta.
2. Busca en tus documentos los 3 fragmentos más parecidos (EmbeddingGemma + Qdrant Edge).
3. Arma el prompt y Gemma 4 responde token por token.
4. Guarda la respuesta. La pantalla la muestra y la lee en voz alta.

El código de cada video del curso está en [`../curso/`](../curso/).

## Privacidad

- Nada sale del celular: el modelo, tus documentos, los vectores y la memoria viven en el teléfono.
- La voz usa el reconocimiento del sistema. En la mayoría de celulares funciona sin internet si tienes descargado el paquete de idioma español (Ajustes del teléfono → Idioma → Reconocimiento de voz sin conexión).
