# YARBYS: tu asistente de IA 100% en el celular

YARBYS es una app de Flutter con un asistente de IA que funciona sin internet. Lee tus documentos, recuerda tus conversaciones y te responde con voz.

| Pieza | Herramienta | Dónde vive |
|---|---|---|
| Cerebro (LLM) | **Gemma 4 E2B** (`.litertlm`, 2.6 GB) con `flutter_edge_ai` | En el celular |
| Embeddings | **EmbeddingGemma 2** (165 MB) | En el celular |
| Base de datos vectorial | **Qdrant Edge** (`flutter_edge_ai_qdrant`) | En el celular |
| Memoria del chat | **SQLite** (`sqflite`) | En el celular |
| Voz | `speech_to_text` + `flutter_tts` (motores del sistema) | En el celular |
| LLM externo (opcional, Pro) | OpenAI (`gpt-6-luna`) o Anthropic (`claude-haiku-5-5`) con tu API key | En la nube |

Internet solo se usa una vez, para descargar los modelos. Después YARBYS funciona en modo avión. El LLM externo es opcional y se activa en **Ajustes**.

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

```
main.dart                  arranca el motor de IA, la memoria y la app
tema.dart                  colores (oscuros y planos) y la píldora de estado
servicios/
  modelos.dart             descarga Gemma 4 y EmbeddingGemma (una sola vez)
  memoria.dart             SQLite: hilos, mensajes y documentos
  conocimiento.dart        RAG: fragmentar, crear vectores y buscar en Qdrant Edge
  cerebro.dart             arma el prompt y responde con Gemma 4 o con un LLM externo
  voz.dart                 escuchar (voz a texto) y hablar (texto a voz)
  ajustes.dart             modo local/externo, API key cifrada y la versión Pro
pantallas/
  inicio.dart              descarga de los modelos
  chat.dart                el chat con el núcleo animado
  documentos.dart          agregar archivos .txt/.md o escribir notas
  ajustes.dart             elegir el cerebro, la voz y borrar la memoria
widgets/
  nucleo.dart              el núcleo circular estilo JARVIS (CustomPainter)
```

El flujo de cada pregunta está en `pantallas/chat.dart` (`_enviar`):

1. Lee los últimos mensajes del hilo (SQLite).
2. Busca en tus documentos los 3 fragmentos más parecidos (EmbeddingGemma + Qdrant Edge).
3. Arma el prompt y Gemma 4 responde token por token.
4. Guarda la respuesta en la memoria.
5. La lee en voz alta.

## Privacidad

- **Modo local (por defecto):** nada sale del celular.
- **LLM externo:** la pregunta y los fragmentos encontrados se envían al proveedor que elijas. Tus documentos, los vectores y la memoria siguen en el celular. La API key se guarda cifrada (Keystore en Android, Keychain en iPhone) y nunca va en el código.
- La voz usa el reconocimiento del sistema. En la mayoría de celulares funciona sin internet si tienes descargado el paquete de idioma español (Ajustes del teléfono → Idioma → Reconocimiento de voz sin conexión).

## Versión Pro

`Ajustes.esPro` (en `servicios/ajustes.dart`) controla el acceso al LLM externo. En este proyecto viene en `true`. Para venderlo como compra única, conéctalo con el paquete [`in_app_purchase`](https://pub.dev/packages/in_app_purchase).
