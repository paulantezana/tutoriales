import 'datos.dart';
import 'servicios/cerebro.dart';

/// YARBYS, el asistente: aquí se une todo lo que sabe hacer.
/// Las pantallas solo hablan con esta clase.
class Yarbys {
  /// Responde una pregunta. Cada vez que Gemma genera un token, entrega
  /// el mensaje de YARBYS con todo el texto que lleva hasta ahora.
  static Stream<Mensaje> preguntar(String pregunta) async* {
    var texto = '';
    await for (final token in Cerebro.responder(pregunta)) {
      texto += token;
      yield Mensaje('yarbys', texto);
    }
  }
}
