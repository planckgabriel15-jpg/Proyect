// =============================================================
// poligonos.js
// Cuentas chicas con polígonos 2D (en cm). Puro: se prueba con node --test.
// Lo usan las tapas a medida ("¿entra en la canaleta?") y las boquetas
// puestas en una tapa ("¿entra en la tapa?").
// =============================================================

/** Distancia de un punto a un segmento. */
export function distanciaASegmento(p, a, b) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const largo2 = dx * dx + dy * dy;
  const t = largo2 > 0 ? Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / largo2)) : 0;
  return Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy));
}

/**
 * ¿El punto está adentro del polígono (o sobre el borde, con tolerancia)?
 * El polígono es una lista de puntos; se cierra solo (del último al primero).
 */
export function puntoEnPoligono(p, poligono, tolerancia = 0.05) {
  const n = poligono.length;
  if (n < 3) return false;
  for (let i = 0; i < n; i++) {
    if (distanciaASegmento(p, poligono[i], poligono[(i + 1) % n]) <= tolerancia) return true;
  }
  // Rayo hacia la derecha: si cruza el borde una cantidad impar de veces, está adentro.
  let adentro = false;
  for (let i = 0, j = n - 1; i < n; j = i++) {
    const a = poligono[i];
    const b = poligono[j];
    if ((a.y > p.y) !== (b.y > p.y) && p.x < ((b.x - a.x) * (p.y - a.y)) / (b.y - a.y) + a.x) adentro = !adentro;
  }
  return adentro;
}

/** Corre todos los puntos (dx, dy). */
export function moverPuntos(puntos, dx, dy) {
  return puntos.map((p) => ({ x: p.x + dx, y: p.y + dy }));
}

/** Puntos del contorno de una huella (círculo o rectángulo) centrada en c, para revisar si entra. */
export function contornoDeHuella(c, huella, cantidad = 16) {
  if (huella.forma === 'circulo') {
    const r = huella.diametro / 2;
    return Array.from({ length: cantidad }, (_, i) => {
      const a = (i / cantidad) * Math.PI * 2;
      return { x: c.x + r * Math.cos(a), y: c.y + r * Math.sin(a) };
    });
  }
  const w = huella.ancho / 2;
  const h = huella.alto / 2;
  return [
    { x: c.x - w, y: c.y - h }, { x: c.x, y: c.y - h }, { x: c.x + w, y: c.y - h }, { x: c.x + w, y: c.y },
    { x: c.x + w, y: c.y + h }, { x: c.x, y: c.y + h }, { x: c.x - w, y: c.y + h }, { x: c.x - w, y: c.y },
  ];
}
