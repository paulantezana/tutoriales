import 'package:flutter/material.dart';

/// Los colores de YARBYS: fondos oscuros y planos.
class Colores {
  static const fondo = Color(0xFF0F1418);
  static const superficie = Color(0xFF1F272E);
  static const azul = Color(0xFF007BDF);
  static const celeste = Color(0xFF00CBFF);
  static const dorado = Color(0xFFFBA905);
  static const suave = Color(0xFF8A9AA8);
}

/// El tema oscuro de la app: todos los widgets toman estos colores.
ThemeData temaYarbys() {
  return ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: Colores.fondo,
    colorScheme: const ColorScheme.dark(
      primary: Colores.azul,
      secondary: Colores.celeste,
      surface: Colores.superficie,
    ),
    appBarTheme: const AppBarTheme(backgroundColor: Colores.fondo),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colores.superficie,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(28),
        borderSide: BorderSide.none,
      ),
    ),
  );
}
