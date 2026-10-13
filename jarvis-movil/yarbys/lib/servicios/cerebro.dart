import 'dart:convert';

import 'package:flutter_edge_ai/flutter_edge_ai.dart';
import 'package:http/http.dart' as http;

import 'ajustes.dart';
import 'memoria.dart';

/// El cerebro de YARBYS: Gemma 4 dentro del celular (por defecto)
/// o, si tú lo activas, un LLM externo con tu propia API key.
class Cerebro {
  // La personalidad de YARBYS
  static const sistema = '''
Eres YARBYS, un asistente personal amable que vive dentro del celular del usuario.
Responde siempre en español, en máximo 3 oraciones y sin formato markdown,
porque tus respuestas se leen en voz alta.
Usa la información de los documentos del usuario cuando sea útil.
Si no sabes algo, dilo con honestidad.''';

  /// Arma el prompt: documentos encontrados + conversación reciente + pregunta.
  static String armarPrompt(
    String pregunta,
    List<String> contexto,
    List<Mensaje> historial,
  ) {
    final b = StringBuffer();
    if (contexto.isNotEmpty) {
      b.writeln('Información de los documentos del usuario:');
      for (final fragmento in contexto) {
        b.writeln('- $fragmento');
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

  /// Devuelve la respuesta en pedacitos (tokens) a medida que se genera.
  static Stream<String> responder(String prompt) {
    return Ajustes.usarNube ? _externo(prompt) : _local(prompt);
  }

  // --- 1. Gemma 4, dentro del celular y sin internet ---
  static Stream<String> _local(String prompt) async* {
    final modelo = await FlutterEdgeAi.getActiveModel(maxTokens: 4096);
    final chat = await modelo.createChat(
      systemInstruction: sistema,
      maxOutputTokens: 512,
    );
    try {
      await chat.addQueryChunk(Message(text: prompt, isUser: true));
      await for (final respuesta in chat.generateChatResponseAsync()) {
        if (respuesta is TextResponse) yield respuesta.token;
      }
    } finally {
      await chat.close();
    }
  }

  // --- 2. LLM externo (opcional): OpenAI o Anthropic ---
  static Stream<String> _externo(String prompt) async* {
    final clave = await Ajustes.leerClave();
    if (clave == null || clave.isEmpty) {
      throw Exception('Falta tu API key. Agrégala en Ajustes.');
    }
    if (Ajustes.proveedor == 'anthropic') {
      final r = await http.post(
        Uri.parse('https://api.anthropic.com/v1/messages'),
        headers: {
          'x-api-key': clave,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
        },
        body: jsonEncode({
          'model': Ajustes.modeloNube,
          'max_tokens': 512,
          'system': sistema,
          'messages': [
            {'role': 'user', 'content': prompt},
          ],
        }),
      );
      final datos = _leer(r);
      yield [
        for (final bloque in datos['content'] as List)
          if (bloque['type'] == 'text') bloque['text'],
      ].join();
    } else {
      final r = await http.post(
        Uri.parse('https://api.openai.com/v1/responses'),
        headers: {
          'Authorization': 'Bearer $clave',
          'content-type': 'application/json',
        },
        body: jsonEncode({
          'model': Ajustes.modeloNube,
          'instructions': sistema,
          'input': prompt,
        }),
      );
      final datos = _leer(r);
      yield [
        for (final item in datos['output'] as List)
          if (item['type'] == 'message')
            for (final c in item['content'] as List)
              if (c['type'] == 'output_text') c['text'],
      ].join();
    }
  }

  static Map<String, dynamic> _leer(http.Response r) {
    final datos = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    if (r.statusCode != 200) {
      final error = datos['error'];
      throw Exception(
        error is Map ? error['message'] : 'Error ${r.statusCode}',
      );
    }
    return datos;
  }
}
