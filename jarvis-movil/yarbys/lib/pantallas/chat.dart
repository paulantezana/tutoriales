import 'package:flutter/material.dart';

import '../datos.dart';
import '../servicios/memoria.dart';
import '../servicios/voz.dart';
import '../widgets/burbuja.dart';
import '../widgets/nucleo.dart';
import '../yarbys.dart';
import 'documentos.dart';

/// La pantalla principal: el núcleo, los mensajes y el campo para hablar.
class PantallaChat extends StatefulWidget {
  const PantallaChat({super.key});

  @override
  State<PantallaChat> createState() => _PantallaChatState();
}

class _PantallaChatState extends State<PantallaChat> {
  final _campo = TextEditingController();
  final _mensajes = <Mensaje>[];
  var _estado = EstadoYarbys.reposo;

  @override
  void initState() {
    super.initState();
    _cargar();
    Voz.preparar();
    Voz.alApagarse = () {
      if (_estado == EstadoYarbys.escuchando) {
        setState(() => _estado = EstadoYarbys.reposo);
      }
    };
  }

  /// Muestra la conversación guardada en la memoria.
  Future<void> _cargar() async {
    final guardados = await Memoria.mensajes();
    setState(() => _mensajes.addAll(guardados));
  }

  Future<void> _enviar(String texto) async {
    if (texto.trim().isEmpty || _estado == EstadoYarbys.pensando) return;
    _campo.clear();
    setState(() {
      _mensajes.add(Mensaje('usuario', texto));
      _mensajes.add(Mensaje('yarbys', ''));
      _estado = EstadoYarbys.pensando;
    });
    try {
      await for (final m in Yarbys.preguntar(texto)) {
        setState(() => _mensajes.last = m);
      }
      setState(() => _estado = EstadoYarbys.hablando);
      await Voz.hablar(_mensajes.last.texto);
    } catch (e) {
      setState(() => _mensajes.last = Mensaje('yarbys', 'Ups, algo falló: $e'));
    }
    setState(() => _estado = EstadoYarbys.reposo);
  }

  /// Escucha tu voz y envía lo que dijiste.
  Future<void> _microfono() async {
    if (_estado == EstadoYarbys.escuchando) {
      await Voz.dejarDeEscuchar();
      return;
    }
    setState(() => _estado = EstadoYarbys.escuchando);
    final ok = await Voz.escuchar((texto) {
      setState(() => _estado = EstadoYarbys.reposo);
      _enviar(texto);
    });
    if (!ok) setState(() => _estado = EstadoYarbys.reposo);
  }

  Future<void> _nuevaConversacion() async {
    await Memoria.borrarMensajes();
    setState(() => _mensajes.clear());
  }

  void _abrirDocumentos() {
    Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => const PantallaDocumentos()));
  }

  @override
  Widget build(BuildContext context) {
    final libre = _estado == EstadoYarbys.reposo;
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
            onPressed: libre ? _nuevaConversacion : null,
          ),
        ],
      ),
      body: Column(
        children: [
          Nucleo(estado: _estado, tamano: _mensajes.isEmpty ? 260 : 140),
          Expanded(
            child: ListView.builder(
              reverse: true, // empieza desde abajo, como en WhatsApp
              padding: const EdgeInsets.all(16),
              itemCount: _mensajes.length,
              itemBuilder: (_, i) =>
                  Burbuja(_mensajes[_mensajes.length - 1 - i]),
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _campo,
                      enabled: libre,
                      decoration: const InputDecoration(
                        hintText: 'Pregúntale a YARBYS',
                      ),
                      onSubmitted: _enviar,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    icon: Icon(
                      _estado == EstadoYarbys.escuchando
                          ? Icons.stop
                          : Icons.mic,
                    ),
                    onPressed: libre || _estado == EstadoYarbys.escuchando
                        ? _microfono
                        : null,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
