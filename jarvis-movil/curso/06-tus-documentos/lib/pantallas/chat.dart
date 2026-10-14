import 'package:flutter/material.dart';

import '../datos.dart';
import '../servicios/memoria.dart';
import '../yarbys.dart';
import 'documentos.dart';

/// La pantalla principal: los mensajes y el campo para escribir.
class PantallaChat extends StatefulWidget {
  const PantallaChat({super.key});

  @override
  State<PantallaChat> createState() => _PantallaChatState();
}

class _PantallaChatState extends State<PantallaChat> {
  final _campo = TextEditingController();
  final _mensajes = <Mensaje>[];
  bool _pensando = false;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  /// Muestra la conversación guardada en la memoria.
  Future<void> _cargar() async {
    final guardados = await Memoria.mensajes();
    setState(() => _mensajes.addAll(guardados));
  }

  Future<void> _enviar(String texto) async {
    if (texto.trim().isEmpty || _pensando) return;
    _campo.clear();
    setState(() {
      _mensajes.add(Mensaje('usuario', texto));
      _mensajes.add(Mensaje('yarbys', ''));
      _pensando = true;
    });
    try {
      await for (final m in Yarbys.preguntar(texto)) {
        setState(() => _mensajes.last = m);
      }
    } catch (e) {
      setState(() => _mensajes.last = Mensaje('yarbys', 'Ups, algo falló: $e'));
    }
    setState(() => _pensando = false);
  }

  Future<void> _nuevaConversacion() async {
    await Memoria.borrarMensajes();
    setState(() => _mensajes.clear());
  }

  void _abrirDocumentos() {
    Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => const PantallaDocumentos()));
  }

  // Cada mensaje: quién lo dijo, el texto y de qué documentos salió
  Widget _mensaje(Mensaje m) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('${m.esUsuario ? 'Tú' : 'YARBYS'}: ${m.texto}'),
          if (m.fuentes.isNotEmpty)
            Text(
              'Fuente: ${m.fuentes.join(', ')}',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('YARBYS'),
        actions: [
          IconButton(
            icon: const Icon(Icons.description_outlined),
            onPressed: _abrirDocumentos,
          ),
          IconButton(
            icon: const Icon(Icons.add_comment_outlined),
            onPressed: _pensando ? null : _nuevaConversacion,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              reverse: true, // empieza desde abajo, como en WhatsApp
              padding: const EdgeInsets.all(16),
              itemCount: _mensajes.length,
              itemBuilder: (_, i) =>
                  _mensaje(_mensajes[_mensajes.length - 1 - i]),
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: TextField(
                controller: _campo,
                enabled: !_pensando,
                decoration: const InputDecoration(
                  hintText: 'Pregúntale a YARBYS',
                ),
                onSubmitted: _enviar,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
