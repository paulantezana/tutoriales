import 'package:flutter/material.dart';
import 'package:flutter_edge_ai/flutter_edge_ai.dart';
import 'package:flutter_edge_ai_litertlm/flutter_edge_ai_litertlm.dart';

import 'pantallas/inicio.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // El motor que ejecuta Gemma dentro del celular
  await FlutterEdgeAi.initialize(inferenceEngines: [LiteRtLmEngine()]);

  runApp(const YarbysApp());
}

class YarbysApp extends StatelessWidget {
  const YarbysApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(title: 'YARBYS', home: PantallaInicio());
  }
}
