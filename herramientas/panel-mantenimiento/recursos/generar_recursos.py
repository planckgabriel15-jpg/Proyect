"""Genera los sonidos (.wav) y el icono (.ico) del Panel de Mantenimiento.

Todo es sintetizado desde cero (ondas, ruido y envolventes): no se usa ningún
audio ni imagen del juego original. Uso:  python generar_recursos.py
Requiere numpy y Pillow.
"""
import os
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SR = 22050  # Hz, mono 16 bit: liviano y suficiente para efectos "de monitor viejo"
AQUI = os.path.dirname(os.path.abspath(__file__))
SONIDOS = os.path.join(AQUI, "sonidos")
rng = np.random.default_rng(1983)


def t(dur):
    return np.arange(int(SR * dur)) / SR


def env(n, ataque=0.005, caida=0.05):
    """Envolvente lineal ataque/caída (en segundos) para evitar clics."""
    e = np.ones(n)
    a, c = int(SR * ataque), int(SR * caida)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if c:
        e[-c:] *= np.linspace(1, 0, c)
    return e


def cuadrada(f, x, duty=0.5):
    return np.where((x * f) % 1.0 < duty, 1.0, -1.0)


def ruido(n):
    return rng.uniform(-1, 1, n)


def pasa_bajos(x, alfa):
    """Filtro RC de un polo (alfa chico = más grave)."""
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alfa * (v - acc)
        y[i] = acc
    return y


def guardar(nombre, x, vol=0.8):
    x = np.asarray(x, dtype=float)
    pico = np.max(np.abs(x)) or 1.0
    datos = (x / pico * vol * 32767).astype("<i2")
    with wave.open(os.path.join(SONIDOS, nombre), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(datos.tobytes())


def zumbido_base(dur):
    """Zumbido eléctrico: 50 Hz de la red + armónicos + siseo filtrado."""
    x = t(dur)
    z = (0.6 * np.sin(2 * np.pi * 50 * x) + 0.35 * np.sin(2 * np.pi * 100 * x)
         + 0.2 * np.sin(2 * np.pi * 150 * x) + 0.08 * np.sin(2 * np.pi * 250 * x))
    return z + 0.12 * pasa_bajos(ruido(len(x)), 0.08)


def main():
    os.makedirs(SONIDOS, exist_ok=True)

    # Ambiente en bucle: 4 s (200 ciclos exactos de 50 Hz -> el loop no "salta").
    amb = zumbido_base(4.0)
    # Chasquidos de estática aleatorios, sutiles.
    for _ in range(9):
        p = rng.integers(0, len(amb) - 900)
        amb[p:p + 900] += 0.5 * ruido(900) * np.linspace(1, 0, 900) ** 2
    guardar("ambiente.wav", amb, vol=0.55)

    # Encendido CRT: golpe grave + silbido agudo (flyback ~15.7 kHz bajado a 7.8k) que se apaga.
    x = t(1.4)
    golpe = np.sin(2 * np.pi * 55 * x) * np.exp(-x * 9) + 0.6 * ruido(len(x)) * np.exp(-x * 25)
    silbido = 0.15 * np.sin(2 * np.pi * 7800 * x) * np.exp(-x * 2.5) * (x > 0.05)
    subida = 0.5 * zumbido_base(1.4) * np.clip(x / 1.2, 0, 1)
    guardar("encendido.wav", (golpe + silbido + subida) * env(len(x), 0.002, 0.2), vol=0.85)

    # Apagado CRT: "tump" descendente.
    x = t(0.7)
    f = 400 * np.exp(-x * 6) + 40
    fase = 2 * np.pi * np.cumsum(f) / SR
    apag = np.sin(fase) * np.exp(-x * 4) + 0.3 * ruido(len(x)) * np.exp(-x * 12)
    guardar("apagado.wav", apag * env(len(x), 0.002, 0.1), vol=0.8)

    # Mover selección: clic corto metálico.
    x = t(0.045)
    clic = cuadrada(1800, x, 0.3) * np.exp(-x * 120) + 0.4 * ruido(len(x)) * np.exp(-x * 200)
    guardar("mover.wav", clic * env(len(x), 0.001, 0.01), vol=0.5)

    # Confirmar: doble bip.
    x = t(0.09)
    bip = cuadrada(1046, x, 0.5) * env(len(x), 0.002, 0.02)
    sil = np.zeros(int(SR * 0.04))
    guardar("seleccionar.wav", np.concatenate([bip, sil, bip * 0.9]), vol=0.45)

    # Tic de progreso durante el reinicio.
    x = t(0.06)
    tic = cuadrada(660, x, 0.25) * np.exp(-x * 50)
    guardar("tic.wav", tic * env(len(x), 0.001, 0.01), vol=0.35)

    # OK: arpegio ascendente de tres notas.
    partes = []
    for f in (784, 988, 1318):
        x = t(0.09)
        partes.append(cuadrada(f, x, 0.5) * env(len(x), 0.002, 0.03))
    guardar("ok.wav", np.concatenate(partes), vol=0.45)

    # Error: zumbador áspero con batido (dos cuadradas desafinadas).
    x = t(0.55)
    err = cuadrada(110, x, 0.5) + cuadrada(116.5, x, 0.5) + 0.3 * ruido(len(x))
    err *= (np.sin(2 * np.pi * 8 * x) > -0.2)  # entrecortado
    guardar("error.wav", err * env(len(x), 0.003, 0.08), vol=0.6)

    # Ráfaga de estática (glitches).
    n = int(SR * 0.35)
    est = ruido(n) * (0.5 + 0.5 * cuadrada(23, t(0.35), 0.6)) * env(n, 0.002, 0.1)
    guardar("estatica.wav", est, vol=0.5)

    # Alerta (pregunta en pantalla): dos tonos alternados.
    partes = []
    for f in (880, 660, 880, 660):
        x = t(0.12)
        partes.append(cuadrada(f, x, 0.5) * env(len(x), 0.002, 0.02))
    guardar("alerta.wav", np.concatenate(partes), vol=0.45)

    generar_icono()


def generar_icono():
    """Monitor CRT verde con un símbolo de encendido: icono para la barra de tareas."""
    S = 256
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 20, 248, 220), radius=34, fill=(28, 30, 28, 255), outline=(70, 75, 70, 255), width=6)
    d.rounded_rectangle((30, 40, 226, 196), radius=26, fill=(6, 22, 10, 255))
    brillo = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    db = ImageDraw.Draw(brillo)
    verde = (120, 255, 140, 255)
    cx, cy, r = 128, 120, 46
    db.arc((cx - r, cy - r, cx + r, cy + r), start=-60, end=240, fill=verde, width=14)
    db.line((cx, cy - r - 10, cx, cy + 4), fill=verde, width=14)
    halo = brillo.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(halo)
    img.alpha_composite(brillo)
    for y in range(42, 196, 8):  # líneas de barrido
        d.line((32, y, 224, y), fill=(0, 0, 0, 45), width=1)
    d.rectangle((96, 222, 160, 240), fill=(40, 42, 40, 255))
    d.rounded_rectangle((64, 236, 192, 250), radius=6, fill=(55, 58, 55, 255))
    img.save(os.path.join(AQUI, "icono.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])


if __name__ == "__main__":
    main()
