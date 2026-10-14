/// Un mensaje del chat.
class Mensaje {
  Mensaje(this.rol, this.texto);

  final String rol; // 'usuario' o 'yarbys'
  final String texto;

  bool get esUsuario => rol == 'usuario';
}
