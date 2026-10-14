import 'dart:convert';

import 'package:flutter_edge_ai_qdrant/flutter_edge_ai_qdrant.dart';
import 'package:flutter_edge_ai_rag/flutter_edge_ai_rag.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// Lo que YARBYS sabe de ti: tus documentos convertidos en vectores
/// y guardados en Qdrant Edge, una base de datos vectorial en el celular.
class Conocimiento {
  static late RagIndex _indice;

  // El tipo de vectores que crea EmbeddingGemma 2
  static const _perfil = 'embeddinggemma2-litertlm-text-4410a540ce75-prefix-v1';

  /// Abre Qdrant y le dice que EmbeddingGemma crea los vectores.
  static Future<void> abrir() async {
    final carpeta = await getApplicationDocumentsDirectory();
    final rag = FlutterEdgeAiRag(
      providers: const [QdrantVectorStoreProvider()],
    );
    _indice = await rag.open(
      spec: VectorStoreSpec(
        providerId: 'qdrant',
        location: p.join(carpeta.path, 'yarbys_qdrant'),
      ),
      embedder: FlutterEdgeAiActiveEmbedder(profileId: _perfil),
    );
  }

  /// Corta un texto en fragmentos de unos 800 caracteres,
  /// sin partir los párrafos.
  static List<String> fragmentar(String texto, {int maximo = 800}) {
    final fragmentos = <String>[];
    var actual = '';
    for (final parrafo in texto.split(RegExp(r'\n\s*\n'))) {
      var limpio = parrafo.trim();
      if (limpio.isEmpty) continue;
      if (actual.isNotEmpty && actual.length + limpio.length > maximo) {
        fragmentos.add(actual);
        actual = '';
      }
      // Un párrafo gigante se corta en el último espacio antes del límite
      while (limpio.length > maximo) {
        var corte = limpio.lastIndexOf(' ', maximo);
        if (corte <= 0) corte = maximo;
        fragmentos.add(limpio.substring(0, corte).trim());
        limpio = limpio.substring(corte).trim();
      }
      actual = actual.isEmpty ? limpio : '$actual\n\n$limpio';
    }
    if (actual.isNotEmpty) fragmentos.add(actual);
    return fragmentos;
  }

  /// Aprende un documento: guarda un vector por fragmento.
  /// Devuelve cuántos fragmentos guardó.
  static Future<int> aprender(String nombre, String texto) async {
    final partes = fragmentar(texto);
    for (var i = 0; i < partes.length; i++) {
      await _indice.add(
        id: '$nombre-$i',
        document: EmbeddingInput.text(partes[i]),
        metadata: jsonEncode({'documento': nombre}),
      );
    }
    await _indice.flush(); // guarda los cambios en el disco
    return partes.length;
  }

  /// Búsqueda semántica: los 3 fragmentos más parecidos a la pregunta.
  static Future<List<RetrievalResult>> buscar(String pregunta) {
    return _indice.search(
      query: EmbeddingInput.text(pregunta),
      topK: 3,
      threshold: 0.3,
    );
  }

  /// El nombre del documento de donde salió un fragmento.
  static String origen(RetrievalResult r) {
    final datos = jsonDecode(r.metadata ?? '{}') as Map<String, dynamic>;
    return datos['documento'] as String? ?? 'documento';
  }
}
