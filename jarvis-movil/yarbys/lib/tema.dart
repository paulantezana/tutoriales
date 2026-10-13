import 'package:flutter/material.dart';

/// Colores de YARBYS: fondos planos y oscuros, sin degradados.
class Colores {
  static const fondo = Color(0xFF0F1418);
  static const superficie = Color(0xFF1F272E);
  static const borde = Color(0xFF2C3A45);
  static const azul = Color(0xFF007BDF);
  static const celeste = Color(0xFF00CBFF);
  static const dorado = Color(0xFFFBA905);
  static const rojo = Color(0xFFFF3C32);
  static const verde = Color(0xFF4ADE80);
  static const suave = Color(0xFF8A9AA8);
}

ThemeData temaYarbys() {
  return ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: Colores.fondo,
    colorScheme: const ColorScheme.dark(
      primary: Colores.azul,
      secondary: Colores.celeste,
      surface: Colores.superficie,
      error: Colores.rojo,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colores.fondo,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
    ),
    drawerTheme: const DrawerThemeData(backgroundColor: Colores.fondo),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colores.superficie,
      hintStyle: const TextStyle(color: Colores.suave),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(28),
        borderSide: const BorderSide(color: Colores.borde),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(28),
        borderSide: const BorderSide(color: Colores.borde),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(28),
        borderSide: const BorderSide(color: Colores.celeste),
      ),
    ),
  );
}

/// Etiqueta en forma de píldora: "Sin internet", "PRO", etc.
class Pildora extends StatelessWidget {
  const Pildora(
    this.texto, {
    super.key,
    this.color = Colores.verde,
    this.icono,
  });

  final String texto;
  final Color color;
  final IconData? icono;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icono != null) ...[
            Icon(icono, size: 15, color: color),
            const SizedBox(width: 6),
          ],
          Text(
            texto,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w700,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}
