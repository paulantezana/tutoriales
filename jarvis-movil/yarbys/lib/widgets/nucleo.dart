import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import '../datos.dart';
import '../tema.dart';

/// El núcleo de YARBYS: tres anillos que giran según lo que está haciendo.
class Nucleo extends StatefulWidget {
  const Nucleo({super.key, required this.estado, this.tamano = 220});

  final EstadoYarbys estado;
  final double tamano;

  @override
  State<Nucleo> createState() => _NucleoState();
}

class _NucleoState extends State<Nucleo> with SingleTickerProviderStateMixin {
  late final Ticker _reloj;
  Duration _anterior = Duration.zero;
  double _segundos = 0; // el tiempo que pasó
  double _giro = 0; // cuánto giraron los anillos

  @override
  void initState() {
    super.initState();
    // El reloj avisa en cada cuadro de la pantalla (60 veces por segundo)
    _reloj = createTicker((transcurrido) {
      final dt = (transcurrido - _anterior).inMicroseconds / 1e6;
      _anterior = transcurrido;
      setState(() {
        _segundos += dt;
        _giro += dt * _velocidad();
      });
    })..start();
  }

  // Al pensar gira rápido; en reposo, despacio
  double _velocidad() => switch (widget.estado) {
    EstadoYarbys.pensando => 4.0,
    EstadoYarbys.reposo => 0.6,
    _ => 1.5,
  };

  @override
  void dispose() {
    _reloj.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.square(widget.tamano),
      painter: _Pintor(widget.estado, _segundos, _giro),
    );
  }
}

/// Dibuja el núcleo con círculos y arcos.
class _Pintor extends CustomPainter {
  _Pintor(this.estado, this.segundos, this.giro);

  final EstadoYarbys estado;
  final double segundos;
  final double giro;

  @override
  void paint(Canvas canvas, Size size) {
    final centro = size.center(Offset.zero);
    final r = size.width / 2;
    final color = estado == EstadoYarbys.pensando
        ? Colores.dorado
        : Colores.celeste;

    // Un "pincel" para dibujar líneas del grosor que queramos
    Paint linea(double grosor) => Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = grosor
      ..strokeCap = StrokeCap.round;

    // 1. Anillo exterior: un círculo fino
    canvas.drawCircle(centro, r * 0.95, linea(2));

    // 2. Dos arcos gruesos que giran juntos
    final caja = Rect.fromCircle(center: centro, radius: r * 0.8);
    canvas.drawArc(caja, giro, pi * 0.7, false, linea(8));
    canvas.drawArc(caja, giro + pi, pi * 0.7, false, linea(8));

    // 3. Un arco fino que gira al revés
    final caja2 = Rect.fromCircle(center: centro, radius: r * 0.64);
    canvas.drawArc(caja2, -giro * 1.5, pi * 1.2, false, linea(3));

    // 4. El centro: late cuando escucha o habla
    final activo =
        estado == EstadoYarbys.escuchando || estado == EstadoYarbys.hablando;
    final pulso = activo ? 0.04 * sin(segundos * 8) : 0.0;
    final radio = r * (0.42 + pulso);
    canvas.drawCircle(centro, radio, Paint()..color = color.withAlpha(40));
    canvas.drawCircle(centro, radio, linea(2));
  }

  @override
  bool shouldRepaint(_Pintor viejo) => true;
}
