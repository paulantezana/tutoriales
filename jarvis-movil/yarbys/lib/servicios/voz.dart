import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// Oídos y boca de YARBYS, con los motores de voz del propio celular.
class Voz {
  static final _oido = SpeechToText(); // voz -> texto
  static final _boca = FlutterTts(); // texto -> voz

  /// Se llama cuando el micrófono se apaga.
  static void Function()? alApagarse;

  /// Pide el permiso del micrófono y prepara la voz en español.
  static Future<void> preparar() async {
    await _boca.setLanguage('es-ES');
    await _boca.awaitSpeakCompletion(true);
    await _oido.initialize(
      onStatus: (estado) {
        if (estado == 'done') alApagarse?.call();
      },
    );
  }

  /// Escucha y llama a [alTerminar] con lo que dijiste.
  /// Devuelve false si no hay permiso del micrófono.
  static Future<bool> escuchar(void Function(String texto) alTerminar) async {
    if (!_oido.isAvailable) return false;
    await _boca.stop();
    await _oido.listen(
      onResult: (r) {
        if (r.finalResult) alTerminar(r.recognizedWords);
      },
      listenOptions: SpeechListenOptions(
        localeId: 'es_ES',
        pauseFor: const Duration(seconds: 3),
      ),
    );
    return true;
  }

  static Future<void> dejarDeEscuchar() => _oido.stop();

  /// Lee el texto en voz alta y espera a que termine.
  static Future<void> hablar(String texto) => _boca.speak(texto);
}
