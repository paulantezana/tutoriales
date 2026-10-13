import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Ajustes de YARBYS. Se guardan cifrados dentro del celular
/// (Keystore en Android, Keychain en iPhone), igual que tu API key.
class Ajustes {
  static const _cofre = FlutterSecureStorage();

  static const modelosPorDefecto = {
    'openai': 'gpt-6-luna',
    'anthropic': 'claude-haiku-5-5',
  };

  static bool usarNube = false; // false = 100% en el celular (por defecto)
  static String proveedor = 'openai'; // 'openai' o 'anthropic'
  static String modeloNube = modelosPorDefecto['openai']!;
  static bool hablar = true; // leer las respuestas en voz alta

  // Versión Pro: aquí conectarías tu compra única (por ejemplo con el
  // paquete in_app_purchase). En este proyecto viene desbloqueada.
  static bool esPro = true;

  static Future<void> cargar() async {
    final datos = await _cofre.readAll();
    usarNube = datos['usar_nube'] == 'si';
    proveedor = datos['proveedor'] ?? 'openai';
    modeloNube = datos['modelo_nube'] ?? modelosPorDefecto[proveedor]!;
    hablar = datos['hablar'] != 'no';
  }

  static Future<void> guardar() async {
    await _cofre.write(key: 'usar_nube', value: usarNube ? 'si' : 'no');
    await _cofre.write(key: 'proveedor', value: proveedor);
    await _cofre.write(key: 'modelo_nube', value: modeloNube);
    await _cofre.write(key: 'hablar', value: hablar ? 'si' : 'no');
  }

  // La API key nunca se escribe en el código: el usuario la pega en la app.
  static Future<String?> leerClave() => _cofre.read(key: 'clave_$proveedor');

  static Future<void> guardarClave(String clave) =>
      _cofre.write(key: 'clave_$proveedor', value: clave.trim());

  /// Texto corto para mostrar qué cerebro está respondiendo.
  static String get nombreCerebro =>
      usarNube ? modeloNube.toUpperCase() : 'GEMMA 4 · LOCAL';
}
