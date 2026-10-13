import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../servicios/conocimiento.dart';
import '../servicios/memoria.dart';
import '../tema.dart';

/// Los documentos que YARBYS aprendió (viven en Qdrant, dentro del celular).
class PantallaDocumentos extends StatefulWidget {
  const PantallaDocumentos({super.key});

  @override
  State<PantallaDocumentos> createState() => _PantallaDocumentosState();
}

class _PantallaDocumentosState extends State<PantallaDocumentos> {
  List<Documento> _documentos = [];
  String? _aprendiendo; // nombre del documento que se está procesando

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    final docs = await Memoria.documentos();
    setState(() => _documentos = docs);
  }

  Future<void> _aprender(String nombre, String texto) async {
    setState(() => _aprendiendo = nombre);
    try {
      final partes = await Conocimiento.aprender(nombre, texto);
      _avisar('Aprendí "$nombre" en $partes fragmentos');
    } catch (e) {
      _avisar('No pude aprender "$nombre": $e');
    }
    setState(() => _aprendiendo = null);
    _cargar();
  }

  // Elegir archivos .txt o .md del celular
  Future<void> _elegirArchivos() async {
    final archivos = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['txt', 'md'],
    );
    for (final archivo in archivos) {
      final texto = utf8.decode(
        await archivo.readAsBytes(),
        allowMalformed: true,
      );
      await _aprender(archivo.name, texto);
    }
  }

  // Escribir o pegar una nota rápida
  Future<void> _escribirNota() async {
    final titulo = TextEditingController();
    final texto = TextEditingController();
    final guardar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colores.superficie,
        title: const Text('Nueva nota'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: titulo,
              decoration: const InputDecoration(
                hintText: 'Título (ej: agenda)',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: texto,
              minLines: 5,
              maxLines: 10,
              decoration: const InputDecoration(
                hintText: 'Escribe o pega el texto...',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Aprender'),
          ),
        ],
      ),
    );
    if (guardar == true && texto.text.trim().isNotEmpty) {
      final nombre = titulo.text.trim().isEmpty ? 'nota' : titulo.text.trim();
      await _aprender('$nombre.txt', texto.text);
    }
  }

  Future<void> _olvidar(Documento doc) async {
    await Conocimiento.olvidar(doc);
    _avisar('Olvidé "${doc.nombre}"');
    _cargar();
  }

  void _avisar(String texto) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(texto)));
  }

  @override
  Widget build(BuildContext context) {
    final ocupado = _aprendiendo != null;
    return Scaffold(
      appBar: AppBar(title: const Text('Mis documentos')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'YARBYS lee estos documentos, los convierte en vectores con '
            'EmbeddingGemma y los guarda en Qdrant, dentro de tu celular.',
            style: TextStyle(color: Colores.suave, height: 1.4),
          ),
          const SizedBox(height: 16),
          if (ocupado)
            Card(
              color: Colores.superficie,
              child: ListTile(
                leading: const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colores.celeste,
                  ),
                ),
                title: Text('Aprendiendo $_aprendiendo...'),
                subtitle: const Text('Creando los embeddings'),
              ),
            ),
          if (_documentos.isEmpty && !ocupado)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 48),
              child: Text(
                'Todavía no hay documentos.\nAgrega tu agenda, notas o lo que quieras que YARBYS sepa.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colores.suave, height: 1.5),
              ),
            ),
          for (final doc in _documentos)
            Card(
              color: Colores.superficie,
              shape: RoundedRectangleBorder(
                side: const BorderSide(color: Colores.borde),
                borderRadius: BorderRadius.circular(16),
              ),
              child: ListTile(
                leading: const Icon(
                  Icons.description_outlined,
                  color: Colores.dorado,
                ),
                title: Text(doc.nombre),
                subtitle: Text('${doc.fragmentos} fragmentos'),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline),
                  onPressed: ocupado ? null : () => _olvidar(doc),
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          FloatingActionButton.extended(
            heroTag: 'nota',
            onPressed: ocupado ? null : _escribirNota,
            backgroundColor: Colores.superficie,
            foregroundColor: Colors.white,
            icon: const Icon(Icons.edit_note),
            label: const Text('Escribir nota'),
          ),
          const SizedBox(height: 12),
          FloatingActionButton.extended(
            heroTag: 'archivo',
            onPressed: ocupado ? null : _elegirArchivos,
            backgroundColor: Colores.azul,
            foregroundColor: Colors.white,
            icon: const Icon(Icons.upload_file),
            label: const Text('Agregar archivo'),
          ),
        ],
      ),
    );
  }
}
