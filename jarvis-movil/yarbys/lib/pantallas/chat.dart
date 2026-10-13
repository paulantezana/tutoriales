import 'package:flutter/material.dart';

import '../servicios/ajustes.dart';
import '../servicios/cerebro.dart';
import '../servicios/conocimiento.dart';
import '../servicios/memoria.dart';
import '../servicios/voz.dart';
import '../tema.dart';
import '../widgets/nucleo.dart';
import 'ajustes.dart';
import 'documentos.dart';

class PantallaChat extends StatefulWidget {
  const PantallaChat({super.key});

  @override
  State<PantallaChat> createState() => _PantallaChatState();
}

class _PantallaChatState extends State<PantallaChat> {
  final _campo = TextEditingController();
  final _scroll = ScrollController();
  final List<Mensaje> _mensajes = [];
  List<Hilo> _hilos = [];
  int? _hiloId; // la conversación actual (null = nueva)
  EstadoYarbys _estado = EstadoYarbys.reposo;

  bool get _ocupado => _estado == EstadoYarbys.pensando;

  @override
  void initState() {
    super.initState();
    _cargarHilos();
    Voz.alDejarDeEscuchar = () {
      if (mounted && _estado == EstadoYarbys.escuchando) {
        setState(() => _estado = EstadoYarbys.reposo);
      }
    };
  }

  Future<void> _cargarHilos() async {
    final hilos = await Memoria.hilos();
    setState(() => _hilos = hilos);
  }

  Future<void> _abrirHilo(Hilo? hilo) async {
    final mensajes = hilo == null
        ? <Mensaje>[]
        : await Memoria.mensajes(hilo.id);
    setState(() {
      _hiloId = hilo?.id;
      _mensajes
        ..clear()
        ..addAll(mensajes);
    });
  }

  // Quita asteriscos y otros símbolos de markdown para mostrar y leer en voz alta
  String _limpiar(String texto) =>
      texto.replaceAll(RegExp(r'[*#_`]'), '').trim();

  /// El corazón de la app: pregunta -> buscar -> pensar -> responder -> hablar
  Future<void> _enviar(String texto) async {
    texto = texto.trim();
    if (texto.isEmpty || _ocupado) return;
    _campo.clear();
    await Voz.callar();

    // 1. Memoria: el hilo y los últimos mensajes de la conversación
    _hiloId ??= await Memoria.nuevoHilo(
      texto.length > 40 ? '${texto.substring(0, 40)}...' : texto,
    );
    final hilo = _hiloId!;
    final historial = await Memoria.mensajes(hilo, ultimos: 6);
    final pregunta = Mensaje('usuario', texto);
    await Memoria.guardar(hilo, pregunta);
    setState(() {
      _mensajes.add(pregunta);
      _mensajes.add(Mensaje('yarbys', ''));
      _estado = EstadoYarbys.pensando;
    });
    _bajar();

    final respuesta = StringBuffer();
    var fuentes = <String>[];
    try {
      // 2. RAG: buscamos en tus documentos lo más parecido a la pregunta
      final hallazgos = await Conocimiento.buscar(texto);
      fuentes = {for (final h in hallazgos) Conocimiento.origen(h)}.toList();

      // 3. El LLM responde, token por token
      final prompt = Cerebro.armarPrompt(texto, [
        for (final h in hallazgos) h.content,
      ], historial);
      await for (final token in Cerebro.responder(prompt)) {
        respuesta.write(token);
        setState(
          () => _mensajes.last = Mensaje(
            'yarbys',
            _limpiar(respuesta.toString()),
            fuentes,
          ),
        );
        _bajar();
      }
    } catch (e) {
      respuesta.write('Ups, algo falló: $e');
    }

    // 4. Guardamos la respuesta en la memoria
    final respuestaFinal = Mensaje(
      'yarbys',
      _limpiar(respuesta.toString()),
      fuentes,
    );
    await Memoria.guardar(hilo, respuestaFinal);
    setState(() => _mensajes.last = respuestaFinal);
    _cargarHilos();

    // 5. Y la decimos en voz alta
    if (Ajustes.hablar && respuestaFinal.texto.isNotEmpty) {
      setState(() => _estado = EstadoYarbys.hablando);
      await Voz.hablar(respuestaFinal.texto);
    }
    if (mounted) setState(() => _estado = EstadoYarbys.reposo);
  }

  Future<void> _microfono() async {
    if (_estado == EstadoYarbys.escuchando) {
      await Voz.dejarDeEscuchar();
      setState(() => _estado = EstadoYarbys.reposo);
      return;
    }
    if (_ocupado) return;
    setState(() => _estado = EstadoYarbys.escuchando);
    final funciona = await Voz.escuchar((texto, terminado) {
      _campo.text = texto;
      if (terminado) {
        setState(() => _estado = EstadoYarbys.reposo);
        _enviar(texto);
      }
    });
    if (!funciona) {
      setState(() => _estado = EstadoYarbys.reposo);
      _avisar('No tengo permiso para usar el micrófono.');
    }
  }

  void _avisar(String texto) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(texto)));
  }

  void _bajar() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _ir(Widget pantalla) async {
    await Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => pantalla));
    // Al volver: quizá cambió el modo o se borraron conversaciones
    await _cargarHilos();
    if (_hilos.every((h) => h.id != _hiloId)) _abrirHilo(null);
  }

  @override
  Widget build(BuildContext context) {
    final conMensajes = _mensajes.isNotEmpty;
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'YARBYS',
          style: TextStyle(
            color: Colores.celeste,
            fontWeight: FontWeight.w800,
            letterSpacing: 4,
          ),
        ),
        actions: [
          Ajustes.usarNube
              ? const Pildora(
                  'Nube',
                  color: Colores.dorado,
                  icono: Icons.cloud_outlined,
                )
              : const Pildora('Sin internet', icono: Icons.airplanemode_active),
          IconButton(
            tooltip: 'Documentos',
            icon: const Icon(Icons.description_outlined),
            onPressed: () => _ir(const PantallaDocumentos()),
          ),
          IconButton(
            tooltip: 'Ajustes',
            icon: const Icon(Icons.tune),
            onPressed: () => _ir(const PantallaAjustes()),
          ),
        ],
      ),
      drawer: _menuHilos(),
      body: Column(
        children: [
          // El núcleo se hace más pequeño cuando hay conversación
          AnimatedContainer(
            duration: const Duration(milliseconds: 400),
            height: conMensajes ? 170 : 300,
            child: FittedBox(child: Nucleo(estado: _estado, tamano: 300)),
          ),
          Text(
            Ajustes.nombreCerebro,
            style: const TextStyle(
              color: Colores.celeste,
              fontFamily: 'monospace',
              fontWeight: FontWeight.w700,
              letterSpacing: 2,
              fontSize: 12,
            ),
          ),
          Expanded(
            child: conMensajes
                ? ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                    itemCount: _mensajes.length,
                    itemBuilder: (_, i) => _Burbuja(_mensajes[i]),
                  )
                : const Center(
                    child: Padding(
                      padding: EdgeInsets.all(32),
                      child: Text(
                        'Pregúntame algo o toca el micrófono.\n'
                        'Agrega tus documentos para que te conozca mejor.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colores.suave, height: 1.5),
                      ),
                    ),
                  ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _campo,
                      enabled: !_ocupado,
                      textInputAction: TextInputAction.send,
                      onSubmitted: _enviar,
                      decoration: const InputDecoration(
                        hintText: 'Habla con YARBYS...',
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 16,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  ValueListenableBuilder(
                    valueListenable: _campo,
                    builder: (_, valor, _) {
                      final escribiendo =
                          valor.text.trim().isNotEmpty &&
                          _estado != EstadoYarbys.escuchando;
                      return IconButton.filled(
                        iconSize: 26,
                        style: IconButton.styleFrom(
                          backgroundColor: _estado == EstadoYarbys.escuchando
                              ? Colores.rojo
                              : Colores.azul,
                          foregroundColor: Colors.white,
                          minimumSize: const Size(56, 56),
                        ),
                        onPressed: _ocupado
                            ? null
                            : escribiendo
                            ? () => _enviar(_campo.text)
                            : _microfono,
                        icon: Icon(escribiendo ? Icons.send : Icons.mic),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _menuHilos() {
    return Drawer(
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 20, 20, 8),
              child: Text(
                'Conversaciones',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.add, color: Colores.celeste),
              title: const Text('Nueva conversación'),
              onTap: () {
                Navigator.pop(context);
                _abrirHilo(null);
              },
            ),
            const Divider(color: Colores.borde),
            Expanded(
              child: ListView(
                children: [
                  for (final hilo in _hilos)
                    ListTile(
                      selected: hilo.id == _hiloId,
                      selectedColor: Colores.celeste,
                      leading: const Icon(Icons.chat_bubble_outline),
                      title: Text(
                        hilo.titulo,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: IconButton(
                        icon: const Icon(
                          Icons.delete_outline,
                          color: Colores.suave,
                        ),
                        onPressed: () async {
                          await Memoria.borrarHilo(hilo.id);
                          if (hilo.id == _hiloId) _abrirHilo(null);
                          _cargarHilos();
                        },
                      ),
                      onTap: () {
                        Navigator.pop(context);
                        _abrirHilo(hilo);
                      },
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Burbuja extends StatelessWidget {
  const _Burbuja(this.mensaje);

  final Mensaje mensaje;

  @override
  Widget build(BuildContext context) {
    final tuyo = mensaje.esUsuario;
    return Align(
      alignment: tuyo ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width * 0.8,
        ),
        decoration: BoxDecoration(
          color: tuyo ? Colores.azul : Colores.superficie,
          border: tuyo ? null : Border.all(color: Colores.borde),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(20),
            topRight: const Radius.circular(20),
            bottomLeft: Radius.circular(tuyo ? 20 : 6),
            bottomRight: Radius.circular(tuyo ? 6 : 20),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            mensaje.texto.isEmpty
                ? const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colores.celeste,
                    ),
                  )
                : Text(
                    mensaje.texto,
                    style: const TextStyle(fontSize: 16, height: 1.4),
                  ),
            for (final fuente in mensaje.fuentes)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.description_outlined,
                      size: 15,
                      color: Colores.dorado,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      fuente,
                      style: const TextStyle(
                        color: Colores.dorado,
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
