import 'package:flutter/material.dart';

import '../datos.dart';
import '../tema.dart';

/// Una burbuja del chat: azul a la derecha si es tuya,
/// gris a la izquierda si es de YARBYS.
class Burbuja extends StatelessWidget {
  const Burbuja(this.mensaje, {super.key});

  final Mensaje mensaje;

  @override
  Widget build(BuildContext context) {
    final mio = mensaje.esUsuario;
    return Align(
      alignment: mio ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 300),
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: mio ? Colores.azul : Colores.superficie,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(mensaje.texto.isEmpty ? '...' : mensaje.texto),
            if (mensaje.fuentes.isNotEmpty)
              Text(
                'Fuente: ${mensaje.fuentes.join(', ')}',
                style: const TextStyle(fontSize: 12, color: Colores.suave),
              ),
          ],
        ),
      ),
    );
  }
}
