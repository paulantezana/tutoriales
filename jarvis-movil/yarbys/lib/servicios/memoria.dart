import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

class Mensaje {
  Mensaje(this.rol, this.texto, [this.fuentes = const []]);

  final String rol; // 'usuario' o 'yarbys'
  final String texto;
  final List<String> fuentes; // documentos que usó para responder

  bool get esUsuario => rol == 'usuario';
}

class Hilo {
  Hilo(this.id, this.titulo);

  final int id;
  final String titulo;
}

class Documento {
  Documento(this.id, this.nombre, this.fragmentos);

  final int id;
  final String nombre;
  final int fragmentos;
}

/// La memoria de YARBYS: una base de datos SQLite dentro del celular.
class Memoria {
  static late Database _db;

  static Future<void> abrir() async {
    final ruta = p.join(await getDatabasesPath(), 'yarbys.db');
    _db = await openDatabase(
      ruta,
      version: 1,
      onCreate: (db, version) async {
        // Cada conversación es un "hilo"
        await db.execute('''
          CREATE TABLE hilos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            creado INTEGER NOT NULL
          )''');
        // Cada mensaje pertenece a un hilo
        await db.execute('''
          CREATE TABLE mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hilo_id INTEGER NOT NULL,
            rol TEXT NOT NULL,
            texto TEXT NOT NULL,
            fuentes TEXT NOT NULL DEFAULT '',
            creado INTEGER NOT NULL
          )''');
        // Los documentos que YARBYS aprendió
        await db.execute('''
          CREATE TABLE documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fragmentos INTEGER NOT NULL,
            creado INTEGER NOT NULL
          )''');
      },
    );
  }

  static int get _ahora => DateTime.now().millisecondsSinceEpoch;

  // --- Hilos ---
  static Future<int> nuevoHilo(String titulo) =>
      _db.insert('hilos', {'titulo': titulo, 'creado': _ahora});

  static Future<List<Hilo>> hilos() async {
    final filas = await _db.query('hilos', orderBy: 'id DESC');
    return [for (final f in filas) Hilo(f['id'] as int, f['titulo'] as String)];
  }

  static Future<void> borrarHilo(int hilo) async {
    await _db.delete('mensajes', where: 'hilo_id = ?', whereArgs: [hilo]);
    await _db.delete('hilos', where: 'id = ?', whereArgs: [hilo]);
  }

  static Future<void> borrarTodo() async {
    await _db.delete('mensajes');
    await _db.delete('hilos');
  }

  // --- Mensajes ---
  static Future<void> guardar(int hilo, Mensaje m) => _db.insert('mensajes', {
    'hilo_id': hilo,
    'rol': m.rol,
    'texto': m.texto,
    'fuentes': m.fuentes.join('|'),
    'creado': _ahora,
  });

  /// Los mensajes de un hilo. Con [ultimos] trae solo los más recientes.
  static Future<List<Mensaje>> mensajes(int hilo, {int? ultimos}) async {
    final filas = await _db.query(
      'mensajes',
      where: 'hilo_id = ?',
      whereArgs: [hilo],
      orderBy: 'id DESC',
      limit: ultimos,
    );
    return [
      for (final f in filas.reversed)
        Mensaje(
          f['rol'] as String,
          f['texto'] as String,
          (f['fuentes'] as String)
              .split('|')
              .where((s) => s.isNotEmpty)
              .toList(),
        ),
    ];
  }

  // --- Documentos ---
  static Future<int> guardarDocumento(String nombre, int fragmentos) =>
      _db.insert('documentos', {
        'nombre': nombre,
        'fragmentos': fragmentos,
        'creado': _ahora,
      });

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
