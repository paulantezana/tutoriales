import 'package:flutter_edge_ai/flutter_edge_ai.dart';

/// Los dos modelos de IA que viven dentro del celular.
/// Se descargan una sola vez; después todo funciona sin internet.
class Modelos {
  // El cerebro (LLM): Gemma 4 E2B de Google. Pesa 2.6 GB.
  static const urlGemma =
      'https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm'
      '/resolve/main/gemma-4-E2B-it.litertlm';

  // Los embeddings: EmbeddingGemma 2 convierte texto en vectores. Pesa 165 MB.
  static const urlEmbeddings =
      'https://huggingface.co/litert-community/embeddinggemma-2-text-270m-litert-lm'
      '/resolve/9be6e8b90982095dc05c2bd162e4b954ee4dbac7/embeddinggemma-2-text-270m.litertlm';

  /// ¿Ya están descargados los dos modelos?
  static bool get listos =>
      FlutterEdgeAi.hasActiveModel() && FlutterEdgeAi.hasActiveEmbedder();

  static Future<void> descargarEmbeddings(void Function(int) progreso) async {
    await FlutterEdgeAi.installEmbedder()
        .modelFromNetwork(urlEmbeddings)
        .withModelProgress(progreso)
        .install();
  }

  static Future<void> descargarGemma(void Function(int) progreso) async {
    await FlutterEdgeAi.installModel(
      modelType: ModelType.gemma4,
      fileType: ModelFileType.litertlm,
    ).fromNetwork(urlGemma).withProgress(progreso).install();
  }
}
