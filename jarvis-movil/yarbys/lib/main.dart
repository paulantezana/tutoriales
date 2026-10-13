import 'package:flutter/material.dart';
import 'package:flutter_edge_ai/flutter_edge_ai.dart';
import 'package:flutter_edge_ai_litertlm/flutter_edge_ai_litertlm.dart';

import 'pantallas/inicio.dart';
import 'servicios/ajustes.dart';
import 'servicios/memoria.dart';
import 'tema.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 1. El motor que ejecuta los modelos .litertlm dentro del celular:
  //    Gemma 4 (el cerebro) y EmbeddingGemma (los embeddings).
  await FlutterEdgeAi.initialize(
    inferenceEngines: [LiteRtLmEngine()],
    embeddingBackends: const [LiteRtEmbeddingBackend()],
  );

  // 2. La memoria (SQLite) y los ajustes guardados.
  await Memoria.abrir();
  await Ajustes.cargar();

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
