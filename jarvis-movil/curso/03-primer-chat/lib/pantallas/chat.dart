import 'package:flutter/material.dart';

import '../datos.dart';
import '../yarbys.dart';

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

  // Cada mensaje: quién lo dijo y el texto
  Widget _mensaje(Mensaje m) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Text('${m.esUsuario ? 'Tú' : 'YARBYS'}: ${m.texto}'),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('YARBYS')),
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
