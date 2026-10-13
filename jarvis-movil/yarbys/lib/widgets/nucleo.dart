import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import '../tema.dart';

enum EstadoYarbys { reposo, escuchando, pensando, hablando }

/// El núcleo circular de YARBYS, inspirado en el JARVIS de las películas.
/// Son solo círculos, arcos y líneas que giran a distinta velocidad.
class Nucleo extends StatefulWidget {
  const Nucleo({super.key, required this.estado, this.tamano = 260});

  final EstadoYarbys estado;
  final double tamano;

  @override
  State<Nucleo> createState() => _NucleoState();
}

class _NucleoState extends State<Nucleo> with SingleTickerProviderStateMixin {
  late final Ticker _reloj;
  Duration _anterior = Duration.zero;
  double _segundos = 0; // tiempo real, para los pulsos
  double _giro = 0; // tiempo "acelerado" según el estado, para girar

  @override
  void initState() {
    super.initState();
    // El reloj avisa en cada cuadro de pantalla (60 veces por segundo)
    _reloj = createTicker((transcurrido) {
      final dt = (transcurrido - _anterior).inMicroseconds / 1e6;
      _anterior = transcurrido;
      setState(() {
        _segundos += dt;
        _giro += dt * _velocidad(widget.estado);
      });
    })..start();
  }

  // Cada estado hace girar el núcleo a otra velocidad
  double _velocidad(EstadoYarbys estado) => switch (estado) {
    EstadoYarbys.reposo => 1.0,
    EstadoYarbys.escuchando => 1.8,
    EstadoYarbys.pensando => 4.0,
    EstadoYarbys.hablando => 1.4,
  };

  @override
  void dispose() {
    _reloj.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: CustomPaint(
        size: Size.square(widget.tamano),
        painter: _PintorNucleo(
          segundos: _segundos,
          giro: _giro,
          estado: widget.estado,
        ),
      ),
    );
  }
}

class _PintorNucleo extends CustomPainter {
  _PintorNucleo({
    required this.segundos,
    required this.giro,
    required this.estado,
  });

  final double segundos;
  final double giro;
  final EstadoYarbys estado;

  static const c = Colores.celeste;
  static const a = Colores.dorado;

  // Alturas fijas de las barras del "ecualizador" (mismo azar siempre)
  static final List<double> _barras = () {
    var s = 3;
    double azar() => (s = (s * 16807) % 2147483647) / 2147483647;
    return [for (var i = 0; i < 90; i++) 0.025 + pow(azar(), 1.6) * 0.075];
  }();

  // Ángulo en grados (0 = arriba) -> punto en el círculo de radio r
  Offset _punto(double r, double grados) {
    final rad = (grados - 90) * pi / 180;
    return Offset(r * cos(rad), r * sin(rad));
  }

  Paint _trazo(Color color, double ancho, [double opacidad = 1]) => Paint()
    ..color = color.withValues(alpha: opacidad)
    ..style = PaintingStyle.stroke
    ..strokeWidth = ancho;

  void _arco(Canvas canvas, double r, double a0, double a1, Paint p) {
    canvas.drawArc(
      Rect.fromCircle(center: Offset.zero, radius: r),
      (a0 - 90) * pi / 180,
      (a1 - a0) * pi / 180,
      false,
      p,
    );
  }

  // Dibuja algo girado [grados] alrededor del centro
  void _girado(Canvas canvas, double grados, void Function() dibujar) {
    canvas.save();
    canvas.rotate(grados * pi / 180);
    dibujar();
    canvas.restore();
  }

  void _texto(Canvas canvas, String texto, Offset centro, TextStyle estilo) {
    final tp = TextPainter(
      text: TextSpan(text: texto, style: estilo),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, centro - Offset(tp.width / 2, tp.height / 2));
  }

  @override
  void paint(Canvas canvas, Size size) {
    final r = size.width / 2 / 1.14; // deja espacio para los grados
    final t = segundos;
    canvas.translate(size.width / 2, size.height / 2);

    final g = giro;
    final activo = estado != EstadoYarbys.reposo;
    final pulso = 0.5 + 0.5 * sin(t * (activo ? 6 : 2));

    // Halo suave detrás del centro
    canvas.drawCircle(
      Offset.zero,
      r * 0.5,
      Paint()
        ..color = c.withValues(alpha: 0.08 + (activo ? 0.10 : 0.04) * pulso)
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, r * 0.18),
    );

    // 1. Anillo exterior con marcas de medición (gira lento)
    _girado(canvas, g * 2, () {
      canvas.drawCircle(Offset.zero, r, _trazo(c, r * 0.006, 0.35));
      for (var i = 0; i < 120; i++) {
        final largo = i % 10 == 0 ? 0.06 : (i % 5 == 0 ? 0.04 : 0.022);
        canvas.drawLine(
          _punto(r * 0.975, i * 3.0),
          _punto(r * (0.975 - largo), i * 3.0),
          _trazo(
            c,
            r * (i % 10 == 0 ? 0.008 : 0.005),
            i % 10 == 0 ? 0.95 : 0.55,
          ),
        );
      }
    });
    final estiloGrados = TextStyle(
      color: c.withValues(alpha: 0.8),
      fontSize: r * 0.05,
      fontFamily: 'monospace',
    );
    for (final (texto, angulo) in [
      ('000', 0.0),
      ('090', 90.0),
      ('180', 180.0),
      ('270', 270.0),
    ]) {
      _texto(canvas, texto, _punto(r * 1.08, angulo), estiloGrados);
    }

    // 2. Anillo de bloques gruesos (gira al revés)
    _girado(canvas, -g * 6, () {
      const bloques = [
        [4, 52],
        [56, 60],
        [64, 118],
        [124, 128],
        [132, 196],
        [202, 206],
        [210, 262],
        [268, 272],
        [276, 356],
      ];
      for (var i = 0; i < bloques.length; i++) {
        _arco(
          canvas,
          r * 0.86,
          bloques[i][0].toDouble(),
          bloques[i][1].toDouble(),
          _trazo(c, r * 0.05, i.isOdd ? 1 : 0.85),
        );
      }
      for (final b in const [
        [96, 100],
        [300, 304],
      ]) {
        _arco(
          canvas,
          r * 0.86,
          b[0].toDouble(),
          b[1].toDouble(),
          _trazo(a, r * 0.05),
        );
      }
    });

    // 3. Anillo punteado
    _girado(canvas, g * 10, () {
      final punto = Paint()..color = c.withValues(alpha: 0.7);
      for (var i = 0; i < 160; i++) {
        canvas.drawCircle(_punto(r * 0.795, i * 2.25), r * 0.004, punto);
      }
    });

    // 4. Ecualizador circular: las barras "bailan" cuando escucha o habla
    _girado(canvas, g * 1.5, () {
      for (var i = 0; i < 90; i++) {
        var h = _barras[i];
        if (estado == EstadoYarbys.escuchando ||
            estado == EstadoYarbys.hablando) {
          h *=
              0.6 +
              1.4 *
                  (0.5 + 0.5 * sin(t * 9 + i * 0.9)) *
                  (0.5 + 0.5 * sin(t * 3.7 + i * 0.31));
        }
        canvas.drawLine(
          _punto(r * 0.70, i * 4.0),
          _punto(r * (0.70 + h), i * 4.0),
          _trazo(c, r * 0.016, 0.85),
        );
      }
    });

    // 5. Dos arcos opuestos con remates y puntos dorados
    _girado(canvas, -g * 12, () {
      final p = _trazo(c, r * 0.012);
      for (final (a0, a1) in [(20.0, 150.0), (200.0, 330.0)]) {
        _arco(canvas, r * 0.62, a0, a1, p);
        for (final ang in [a0, a1]) {
          canvas.drawLine(_punto(r * 0.585, ang), _punto(r * 0.655, ang), p);
        }
      }
      for (final ang in [85.0, 265.0]) {
        canvas.drawCircle(_punto(r * 0.62, ang), r * 0.018, Paint()..color = a);
      }
    });

    // 6. Media luna gruesa y tenue (gira rápido al pensar)
    _girado(canvas, g * 20, () {
      _arco(canvas, r * 0.53, 210, 500, _trazo(c, r * 0.06, 0.35));
    });

    // 7. Anillo interior con muescas en cruz
    _girado(canvas, -g * 4, () {
      canvas.drawCircle(Offset.zero, r * 0.45, _trazo(c, r * 0.008, 0.9));
      for (final ang in [0.0, 90.0, 180.0, 270.0]) {
        canvas.drawLine(
          _punto(r * 0.41, ang),
          _punto(r * 0.49, ang),
          _trazo(c, r * 0.014),
        );
      }
      for (var i = 0; i < 36; i++) {
        canvas.drawLine(
          _punto(r * 0.425, i * 10.0 + 5),
          _punto(r * 0.44, i * 10.0 + 5),
          _trazo(c, r * 0.005, 0.6),
        );
      }
    });

    // 8. Centro: nombre y estado
    canvas.drawCircle(
      Offset.zero,
      r * 0.38,
      Paint()..color = const Color(0xD906131A),
    );
    canvas.drawLine(
      Offset(-r * 0.2, -r * 0.1),
      Offset(r * 0.2, -r * 0.1),
      _trazo(c, r * 0.005, 0.6),
    );
    _texto(
      canvas,
      'YARBYS',
      Offset(0, -r * 0.01),
      TextStyle(
        color: const Color(0xFFE9FBFF),
        fontSize: r * 0.13,
        fontWeight: FontWeight.w800,
        letterSpacing: r * 0.02,
      ),
    );
    final etiqueta = switch (estado) {
      EstadoYarbys.reposo => 'EN LÍNEA',
      EstadoYarbys.escuchando => 'ESCUCHANDO',
      EstadoYarbys.pensando => 'PENSANDO',
      EstadoYarbys.hablando => 'HABLANDO',
    };
    _texto(
      canvas,
      etiqueta,
      Offset(0, r * 0.13),
      TextStyle(
        color: estado == EstadoYarbys.pensando ? a : c,
        fontSize: r * 0.048,
        fontWeight: FontWeight.w700,
        letterSpacing: r * 0.012,
        fontFamily: 'monospace',
      ),
    );
  }

  @override
  bool shouldRepaint(_PintorNucleo old) =>
      old.segundos != segundos || old.estado != estado;
}
