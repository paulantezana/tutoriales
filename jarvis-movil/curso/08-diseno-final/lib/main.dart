import 'package:flutter/material.dart';
import 'package:flutter_edge_ai/flutter_edge_ai.dart';
import 'package:flutter_edge_ai_litertlm/flutter_edge_ai_litertlm.dart';

import 'pantallas/inicio.dart';
import 'servicios/memoria.dart';
import 'tema.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // El motor que ejecuta Gemma y EmbeddingGemma dentro del celular
  await FlutterEdgeAi.initialize(
    inferenceEngines: [LiteRtLmEngine()],
    embeddingBackends: const [LiteRtEmbeddingBackend()],
  );
  await Memoria.abrir();

  runApp(const YarbysApp());
}

class YarbysApp extends StatelessWidget {
  const YarbysApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'YARBYS',
      debugShowCheckedModeBanner: false,
      theme: temaYarbys(),
      home: const PantallaInicio(),
    );
  }
}
