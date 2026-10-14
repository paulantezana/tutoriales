import 'datos.dart';
import 'servicios/cerebro.dart';
import 'servicios/conocimiento.dart';
import 'servicios/memoria.dart';

/// YARBYS, el asistente: aquí se une todo lo que sabe hacer.
/// Las pantallas solo hablan con esta clase.
class Yarbys {
  /// Responde una pregunta. Cada vez que Gemma genera un token, entrega
  /// el mensaje de YARBYS con todo el texto que lleva hasta ahora.
  static Stream<Mensaje> preguntar(String pregunta) async* {
    // Memoria: lo último que hablamos
    final historial = await Memoria.mensajes(ultimos: 6);
    await Memoria.guardar(Mensaje('usuario', pregunta));

    // RAG: los fragmentos de tus documentos más parecidos a la pregunta
    final hallazgos = await Conocimiento.buscar(pregunta);
    final fragmentos = [for (final h in hallazgos) h.content];
    final fuentes = {for (final h in hallazgos) Conocimiento.origen(h)};

    // El cerebro responde token por token
    final prompt = armarPrompt(pregunta, fragmentos, historial);
    var texto = '';
    await for (final token in Cerebro.responder(prompt)) {
      texto += token;
      yield Mensaje('yarbys', texto, fuentes.toList());
    }

    // Guardamos la respuesta en la memoria
    await Memoria.guardar(Mensaje('yarbys', texto));
  }

  /// Une los documentos, la conversación y la pregunta en un solo texto.
  static String armarPrompt(
    String pregunta,
    List<String> fragmentos,
    List<Mensaje> historial,
  ) {
    final b = StringBuffer();
    if (fragmentos.isNotEmpty) {
      b.writeln('Información de los documentos del usuario:');
      for (final f in fragmentos) {
        b.writeln('- $f');
      }
      b.writeln();
    }
    if (historial.isNotEmpty) {
      b.writeln('Conversación hasta ahora:');
      for (final m in historial) {
        b.writeln('${m.esUsuario ? 'Usuario' : 'YARBYS'}: ${m.texto}');
      }
      b.writeln();
    }
    b.write('Pregunta del usuario: $pregunta');
    return b.toString();
  }
}
