import 'package:flutter_edge_ai/flutter_edge_ai.dart';

/// Los modelos de IA que viven dentro del celular.
/// Se descargan una sola vez; después todo funciona sin internet.
class Modelos {
  // El cerebro (LLM): Gemma 4 E2B de Google. Pesa 2.6 GB.
  static const urlGemma =
      'https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/resolve/main/gemma-4-E2B-it.litertlm';

  /// ¿Ya está descargado?
  static bool get listos => FlutterEdgeAi.hasActiveModel();

  static Future<void> descargarGemma(void Function(int) progreso) async {
    await FlutterEdgeAi.installModel(
      modelType: ModelType.gemma4,
      fileType: ModelFileType.litertlm,
    ).fromNetwork(urlGemma).withProgress(progreso).install();
  }
}
