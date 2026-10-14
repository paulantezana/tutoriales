import 'package:flutter/material.dart';

import '../servicios/conocimiento.dart';
import '../servicios/modelos.dart';
import 'chat.dart';

/// La puerta de entrada: descarga los modelos (una sola vez)
/// y después muestra el chat.
class PantallaInicio extends StatefulWidget {
  const PantallaInicio({super.key});

  @override
  State<PantallaInicio> createState() => _PantallaInicioState();
}

class _PantallaInicioState extends State<PantallaInicio> {
  String _aviso = 'Necesito descargar mis modelos de IA. Usa Wi-Fi.';
  double? _progreso; // de 0 a 1; null mientras no descarga
  bool _ocupado = false;
  bool _listo = false;

  @override
  void initState() {
    super.initState();
    // Si los modelos ya están en el celular, entramos directo
    if (Modelos.listos) {
      _ocupado = true;
      _abrir();
    }
  }

  Future<void> _descargar() async {
    setState(() => _ocupado = true);
    try {
      setState(() => _aviso = 'Descargando EmbeddingGemma (165 MB)');
      await Modelos.descargarEmbeddings(
        (p) => setState(() => _progreso = p / 100),
      );
      setState(() => _aviso = 'Descargando Gemma 4 (2.6 GB)');
      await Modelos.descargarGemma((p) => setState(() => _progreso = p / 100));
      await _abrir();
    } catch (e) {
      setState(() {
        _aviso = 'No se pudo descargar: $e';
        _ocupado = false;
      });
    }
  }

  /// Abre Qdrant y muestra el chat.
  Future<void> _abrir() async {
    await Conocimiento.abrir();
    setState(() => _listo = true);
  }

  @override
  Widget build(BuildContext context) {
    if (_listo) return const PantallaChat();
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_aviso, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              if (_progreso != null) LinearProgressIndicator(value: _progreso),
              if (!_ocupado)
                FilledButton(
                  onPressed: _descargar,
                  child: const Text('Descargar modelos'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
