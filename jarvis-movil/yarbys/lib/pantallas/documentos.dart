import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../datos.dart';
import '../servicios/conocimiento.dart';
import '../servicios/memoria.dart';

/// Los documentos que YARBYS aprendió.
class PantallaDocumentos extends StatefulWidget {
  const PantallaDocumentos({super.key});

  @override
  State<PantallaDocumentos> createState() => _PantallaDocumentosState();
}

class _PantallaDocumentosState extends State<PantallaDocumentos> {
  List<Documento> _documentos = [];
  bool _aprendiendo = false;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    final docs = await Memoria.documentos();
    setState(() => _documentos = docs);
  }

  /// Elige archivos .txt o .md y se los enseña a YARBYS.
  Future<void> _agregar() async {
    final archivos = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['txt', 'md'],
    );
    setState(() => _aprendiendo = true);
    for (final archivo in archivos) {
      final bytes = await archivo.readAsBytes();
      final texto = utf8.decode(bytes, allowMalformed: true);
      await Conocimiento.aprender(archivo.name, texto);
    }
    setState(() => _aprendiendo = false);
    await _cargar();
  }

  Future<void> _olvidar(Documento doc) async {
    await Conocimiento.olvidar(doc);
    await _cargar();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mis documentos')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _aprendiendo ? null : _agregar,
        icon: const Icon(Icons.add),
        label: Text(_aprendiendo ? 'Aprendiendo...' : 'Agregar archivo'),
      ),
      body: ListView(
        children: [
          for (final doc in _documentos)
            ListTile(
              leading: const Icon(Icons.description_outlined),
              title: Text(doc.nombre),
              subtitle: Text('${doc.fragmentos} fragmentos'),
              trailing: IconButton(
                icon: const Icon(Icons.delete_outline),
                onPressed: () => _olvidar(doc),
              ),
            ),
        ],
      ),
    );
  }
}
