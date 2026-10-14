import 'package:flutter_edge_ai/flutter_edge_ai.dart';

/// El cerebro de YARBYS: Gemma 4, dentro del celular.
class Cerebro {
  // La personalidad: las reglas que Gemma sigue en toda la conversación
  static const _personalidad =
      'Eres YARBYS, un asistente que vive dentro del celular. '
      'Respondes en español, en máximo 3 oraciones y sin markdown. '
      'Si no sabes algo, lo dices.';

  /// Le pasa el prompt a Gemma y devuelve la respuesta token por token.
  static Stream<String> responder(String prompt) async* {
    final modelo = await FlutterEdgeAi.getActiveModel(maxTokens: 4096);
    final chat = await modelo.createChat(
      systemInstruction: _personalidad,
      maxOutputTokens: 512,
    );
    try {
      await chat.addQueryChunk(Message(text: prompt, isUser: true));
      await for (final r in chat.generateChatResponseAsync()) {
        if (r is TextResponse) yield r.token;
      }
    } finally {
      await chat.close();
    }
  }
}
