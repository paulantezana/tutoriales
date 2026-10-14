import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../datos.dart';

/// La memoria de YARBYS: una base de datos SQLite dentro del celular.
class Memoria {
  static late Database _db;

  /// Abre el archivo yarbys.db y crea las tablas la primera vez.
  static Future<void> abrir() async {
    final ruta = p.join(await getDatabasesPath(), 'yarbys.db');
    _db = await openDatabase(ruta);
    await _db.execute('''
      CREATE TABLE IF NOT EXISTS mensajes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rol TEXT NOT NULL,
        texto TEXT NOT NULL
      )''');
    await _db.execute('''
      CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        fragmentos INTEGER NOT NULL
      )''');
  }

  // --- Mensajes ---
  static Future<void> guardar(Mensaje m) async {
    await _db.insert('mensajes', {'rol': m.rol, 'texto': m.texto});
  }

  /// Los últimos mensajes, del más viejo al más nuevo.
  static Future<List<Mensaje>> mensajes({int ultimos = 50}) async {
    final filas = await _db.query(
      'mensajes',
      orderBy: 'id DESC',
      limit: ultimos,
    );
    return [
      for (final f in filas.reversed)
        Mensaje(f['rol'] as String, f['texto'] as String),
    ];
  }

  static Future<void> borrarMensajes() => _db.delete('mensajes');

  // --- Documentos ---
  static Future<void> guardarDocumento(String nombre, int fragmentos) async {
    await _db.insert('documentos', {
      'nombre': nombre,
      'fragmentos': fragmentos,
    });
  }

  static Future<List<Documento>> documentos() async {
    final filas = await _db.query('documentos', orderBy: 'id DESC');
    return [
      for (final f in filas)
        Documento(
          f['id'] as int,
          f['nombre'] as String,
          f['fragmentos'] as int,
        ),
    ];
  }

  static Future<void> borrarDocumento(int id) =>
      _db.delete('documentos', where: 'id = ?', whereArgs: [id]);
}
