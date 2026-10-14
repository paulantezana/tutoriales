import 'package:flutter_test/flutter_test.dart';
import 'package:yarbys/servicios/conocimiento.dart';

void main() {
  test('un texto corto queda en un solo fragmento', () {
    expect(Conocimiento.fragmentar('Hola, soy YARBYS.'), ['Hola, soy YARBYS.']);
  });

  test('los párrafos se juntan hasta llegar al máximo', () {
    final texto = List.filled(10, 'a' * 300).join('\n\n');
    final partes = Conocimiento.fragmentar(texto);
    expect(partes.length, 5);
    expect(partes.every((p) => p.length <= 800), isTrue);
  });

  test('un párrafo gigante se corta en los espacios', () {
    final texto = List.filled(500, 'palabra').join(' ');
    final partes = Conocimiento.fragmentar(texto);
    expect(partes.every((p) => p.length <= 800), isTrue);
    expect(partes.join(' ').split(' ').length, 500);
  });
}
