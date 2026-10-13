import 'package:flutter/material.dart';

import '../servicios/conocimiento.dart';
import '../servicios/modelos.dart';
import '../tema.dart';
import '../widgets/nucleo.dart';
import 'chat.dart';

/// Primera pantalla: descarga los modelos (una sola vez) y abre el chat.
class PantallaInicio extends StatefulWidget {
  const PantallaInicio({super.key});

  @override
  State<PantallaInicio> createState() => _PantallaInicioState();
}

class _PantallaInicioState extends State<PantallaInicio> {
  int _progresoEmbeddings = 0;
  int _progresoGemma = 0;
  bool _descargando = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    // Si los modelos ya están en el celular, vamos directo al chat
    if (Modelos.listos) _entrar();
  }

  Future<void> _descargar() async {
    setState(() {
      _descargando = true;
      _error = null;
    });
    try {
      await Modelos.descargarEmbeddings(
        (p) => setState(() => _progresoEmbeddings = p),
      );
      await Modelos.descargarGemma((p) => setState(() => _progresoGemma = p));
      await _entrar();
    } catch (e) {
      setState(() {
        _descargando = false;
        _error = 'No se pudo descargar: $e';
      });
    }
  }

  Future<void> _entrar() async {
    try {
      await Conocimiento.abrir(); // abre Qdrant con EmbeddingGemma
    } catch (e) {
      setState(() => _error = 'No pude abrir mi memoria de documentos: $e');
      return;
    }
    if (!mounted) return;
    Navigator.of(
      context,
    ).pushReplacement(MaterialPageRoute(builder: (_) => const PantallaChat()));
  }

  @override
  Widget build(BuildContext context) {
    // Modelos ya descargados: solo mostramos el núcleo mientras despierta
    if (Modelos.listos && !_descargando && _error == null) {
      return const Scaffold(
        body: Center(child: Nucleo(estado: EstadoYarbys.pensando, tamano: 260)),
      );
    }
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const SizedBox(height: 12),
            Center(
              child: Nucleo(
                estado: _descargando
                    ? EstadoYarbys.pensando
                    : EstadoYarbys.reposo,
                tamano: 240,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Hola, soy YARBYS',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            const Text(
              'Para funcionar sin internet necesito descargar mi cerebro una sola vez. '
              'Usa Wi-Fi: son unos 2.8 GB.',
              style: TextStyle(fontSize: 16, color: Colores.suave, height: 1.4),
            ),
            const SizedBox(height: 24),
            _Descarga(
              icono: Icons.hub_outlined,
              titulo: 'EmbeddingGemma 2',
              detalle: 'Convierte texto en vectores · 165 MB',
              progreso: _progresoEmbeddings,
            ),
            const SizedBox(height: 12),
            _Descarga(
              icono: Icons.psychology_outlined,
              titulo: 'Gemma 4 E2B',
              detalle: 'El cerebro (LLM) · 2.6 GB',
              progreso: _progresoGemma,
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: Colores.rojo)),
            ],
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _descargando ? null : _descargar,
              icon: const Icon(Icons.download),
              label: Text(
                _descargando ? 'Descargando...' : 'Descargar modelos',
              ),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(56),
                backgroundColor: Colores.azul,
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Descarga extends StatelessWidget {
  const _Descarga({
    required this.icono,
    required this.titulo,
    required this.detalle,
    required this.progreso,
  });

  final IconData icono;
  final String titulo;
  final String detalle;
  final int progreso;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colores.superficie,
        border: Border.all(color: Colores.borde),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icono, color: Colores.celeste),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      titulo,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                      ),
                    ),
                    Text(detalle, style: const TextStyle(color: Colores.suave)),
                  ],
                ),
              ),
              Text(
                progreso == 100 ? 'Listo' : '$progreso%',
                style: TextStyle(
                  color: progreso == 100 ? Colores.verde : Colores.celeste,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          LinearProgressIndicator(
            value: progreso / 100,
            minHeight: 6,
            borderRadius: BorderRadius.circular(3),
            color: progreso == 100 ? Colores.verde : Colores.celeste,
            backgroundColor: Colores.borde,
          ),
        ],
      ),
    );
  }
}
