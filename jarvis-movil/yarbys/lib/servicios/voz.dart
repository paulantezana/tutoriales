import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// Oídos y boca de YARBYS, usando los motores de voz del propio celular.
class Voz {
  static final _oido = SpeechToText(); // voz -> texto
  static final _boca = FlutterTts(); // texto -> voz
  static bool _oidoListo = false;
  static bool _bocaLista = false;
  static String _idioma = 'es_ES';

  /// Se llama cuando el micrófono se apaga (silencio, error o fin).
  static void Function()? alDejarDeEscuchar;

  /// Escucha al usuario. [alOir] recibe el texto en vivo y,
  /// al final, `terminado = true`. Devuelve false si no hay permiso.
  static Future<bool> escuchar(
    void Function(String texto, bool terminado) alOir,
  ) async {
    if (!_oidoListo) {
      _oidoListo = await _oido.initialize(
        onStatus: (estado) {
          if (estado == 'done' || estado == 'notListening') {
            alDejarDeEscuchar?.call();
          }
        },
        onError: (_) => alDejarDeEscuchar?.call(),
      );
      if (!_oidoListo) return false;
      final delSistema = await _oido.systemLocale();
      if (delSistema != null && delSistema.localeId.startsWith('es')) {
        _idioma = delSistema.localeId;
      }
    }
    await _boca.stop();
    await _oido.listen(
      onResult: (r) => alOir(r.recognizedWords, r.finalResult),
      listenOptions: SpeechListenOptions(
        localeId: _idioma,
        partialResults: true,
        pauseFor: const Duration(seconds: 3),
      ),
    );
    return true;
  }

  static Future<void> dejarDeEscuchar() => _oido.stop();

  /// Lee el texto en voz alta y espera a que termine.
  static Future<void> hablar(String texto) async {
    if (!_bocaLista) {
      await _boca.setLanguage(_idioma.replaceAll('_', '-'));
      await _boca.awaitSpeakCompletion(true);
      _bocaLista = true;
    }
    await _boca.stop();
    await _boca.speak(texto);
  }

  static Future<void> callar() => _boca.stop();
}
