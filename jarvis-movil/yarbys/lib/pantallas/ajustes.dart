import 'package:flutter/material.dart';

import '../servicios/ajustes.dart';
import '../servicios/memoria.dart';
import '../tema.dart';

class PantallaAjustes extends StatefulWidget {
  const PantallaAjustes({super.key});

  @override
  State<PantallaAjustes> createState() => _PantallaAjustesState();
}

class _PantallaAjustesState extends State<PantallaAjustes> {
  final _clave = TextEditingController();
  final _modelo = TextEditingController(text: Ajustes.modeloNube);

  @override
  void initState() {
    super.initState();
    _leerClave();
  }

  Future<void> _leerClave() async {
    _clave.text = await Ajustes.leerClave() ?? '';
  }

  Future<void> _guardar() async {
    Ajustes.modeloNube = _modelo.text.trim();
    await Ajustes.guardarClave(_clave.text);
    await Ajustes.guardar();
  }

  @override
  void dispose() {
    _guardar(); // guardamos al salir de la pantalla
    super.dispose();
  }

  void _cambiarModo(bool nube) {
    if (nube && !Ajustes.esPro) {
      showDialog(
        context: context,
        builder: (_) => const AlertDialog(
          title: Text('YARBYS Pro'),
          content: Text('Conectar un LLM externo es parte de la versión Pro.'),
        ),
      );
      return;
    }
    setState(() => Ajustes.usarNube = nube);
  }

  Future<void> _cambiarProveedor(String proveedor) async {
    await _guardar();
    Ajustes.proveedor = proveedor;
    Ajustes.modeloNube = Ajustes.modelosPorDefecto[proveedor]!;
    _modelo.text = Ajustes.modeloNube;
    await _leerClave();
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ajustes')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const _Titulo('Cerebro'),
          SegmentedButton<bool>(
            segments: const [
              ButtonSegment(
                value: false,
                icon: Icon(Icons.phone_android),
                label: Text('En el celular'),
              ),
              ButtonSegment(
                value: true,
                icon: Icon(Icons.cloud_outlined),
                label: Text('LLM externo'),
              ),
            ],
            selected: {Ajustes.usarNube},
            onSelectionChanged: (s) => _cambiarModo(s.first),
          ),
          const SizedBox(height: 12),
          if (!Ajustes.usarNube)
            const Text(
              'Gemma 4 responde dentro de tu celular. Nada sale del teléfono '
              'y funciona en modo avión.',
              style: TextStyle(color: Colores.suave, height: 1.4),
            )
          else ...[
            const Row(
              children: [
                Pildora(
                  'PRO',
                  color: Colores.dorado,
                  icono: Icons.workspace_premium,
                ),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Usa tu propia API key.',
                    style: TextStyle(color: Colores.suave),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'openai', label: Text('OpenAI')),
                ButtonSegment(value: 'anthropic', label: Text('Anthropic')),
              ],
              selected: {Ajustes.proveedor},
              onSelectionChanged: (s) => _cambiarProveedor(s.first),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _modelo,
              decoration: const InputDecoration(labelText: 'Modelo'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _clave,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'API key'),
            ),
            const SizedBox(height: 12),
            const Text(
              'Con un LLM externo, tu pregunta y los fragmentos encontrados se '
              'envían a ese proveedor. Tus documentos, tus vectores y tu memoria '
              'siguen guardados en el celular.',
              style: TextStyle(color: Colores.dorado, height: 1.4),
            ),
          ],
          const SizedBox(height: 28),
          const _Titulo('Voz'),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Leer las respuestas en voz alta'),
            value: Ajustes.hablar,
            onChanged: (v) => setState(() => Ajustes.hablar = v),
          ),
          const SizedBox(height: 28),
          const _Titulo('Memoria'),
          OutlinedButton.icon(
            icon: const Icon(Icons.delete_sweep_outlined, color: Colores.rojo),
            label: const Text('Borrar todas las conversaciones'),
            onPressed: () async {
              await Memoria.borrarTodo();
              if (!context.mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Conversaciones borradas')),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _Titulo extends StatelessWidget {
  const _Titulo(this.texto);

  final String texto;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        texto.toUpperCase(),
        style: const TextStyle(
          color: Colores.celeste,
          fontWeight: FontWeight.w800,
          letterSpacing: 2,
          fontSize: 13,
        ),
      ),
    );
  }
}
