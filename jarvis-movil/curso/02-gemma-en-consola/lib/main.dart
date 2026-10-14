import 'package:flutter/material.dart';
import 'package:flutter_edge_ai/flutter_edge_ai.dart';
import 'package:flutter_edge_ai_litertlm/flutter_edge_ai_litertlm.dart';

import 'servicios/cerebro.dart';
import 'servicios/modelos.dart';

Future<void> main() async {
  runApp(
    const MaterialApp(
      home: Scaffold(body: Center(child: Text('Mira la consola'))),
    ),
  );

  // El motor que ejecuta Gemma dentro del celular
  await FlutterEdgeAi.initialize(inferenceEngines: [LiteRtLmEngine()]);

  // Prueba: descargamos Gemma (solo la primera vez) y le preguntamos algo
  if (!Modelos.listos) {
    await Modelos.descargarGemma((p) => debugPrint('Descargando Gemma: $p%'));
  }
  debugPrint('Pregunta: ¿Quién eres?');
  final respuesta = await Cerebro.responder('¿Quién eres?').join();
  debugPrint('YARBYS: $respuesta');
}
