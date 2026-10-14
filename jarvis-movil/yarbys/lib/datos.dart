/// Un mensaje del chat.
class Mensaje {
  Mensaje(this.rol, this.texto, [this.fuentes = const []]);

  final String rol; // 'usuario' o 'yarbys'
  final String texto;
  final List<String> fuentes; // los documentos que usó para responder

  bool get esUsuario => rol == 'usuario';
}

/// Un documento que YARBYS aprendió.
class Documento {
  Documento(this.id, this.nombre, this.fragmentos);

  final int id;
  final String nombre;
  final int fragmentos;
}

/// Lo que está haciendo YARBYS en este momento.
enum EstadoYarbys { reposo, escuchando, pensando, hablando }
