"""Genera el logo de Paul Antezana en alta resolución (reconstruido como vector)."""
from PIL import Image, ImageDraw

AZUL, NARANJA, BLANCO = (19, 93, 188), (252, 179, 51), (255, 255, 255)
N = 59.1        # diámetro del círculo, en "celdas" de la cuadrícula
DY = -0.9       # ajuste vertical de la cuadrícula


def logo(S=1024):
    k = S / N
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, S - 1, S - 1), fill=AZUL)

    def rect(c0, r0, c1, r1, col, rad=0, esquinas=None):
        caja = (c0 * k, (r0 + DY) * k, (c1 + 1) * k, (r1 + 1 + DY) * k)
        if rad:
            d.rounded_rectangle(caja, rad * k, fill=col, corners=esquinas)
        else:
            d.rectangle(caja, fill=col)

    rect(17, 18, 23, 48, BLANCO, 3.5, (True, False, False, False))   # asta de la P
    rect(17, 33, 37, 39, BLANCO, 3.5, (False, False, True, False))   # base del ojo
    rect(31, 25, 37, 39, BLANCO, 3.5, (False, False, True, False))   # lado derecho
    rect(24, 18, 30, 24, NARANJA)
    rect(31, 12, 35, 16, NARANJA)
    rect(38, 21, 41, 24, NARANJA)
    return img


if __name__ == "__main__":
    logo(1024).save("logo.png")
