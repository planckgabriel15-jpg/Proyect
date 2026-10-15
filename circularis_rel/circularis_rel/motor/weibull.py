"""Ajuste de Weibull (Plan §5).

Selección del método:
    0–2 fallas, con β de referencia ........ Weibayes: η = [Σ tᵢ^β / r]^(1/β) (fallas y suspensiones)
    3–19 fallas, suspensiones ≤ 50 % ........ RRX con rangos de Johnson y medianos de Benard
    ≥ 20 fallas, > 50 % suspensiones o intervalo  MLE (con RBA si fallas < 30)

Intervalos de confianza al 90 % bilateral: razón de verosimilitud para MLE y bootstrap paramétrico
para RRX. La matriz de Fisher solo existe para validación cruzada (D-004): con pocos datos da
intervalos demasiado estrechos.

Referencias: Abernethy, R. B. (2006), The New Weibull Handbook, 5.ª ed. (rangos de Johnson y Benard,
RRX, RBA, Weibayes, valor crítico de correlación); Meeker, Escobar y Pascual (2021), Statistical
Methods for Reliability Data, 2.ª ed. (verosimilitud con censura e intervalos por razón de
verosimilitud). Citadas como en el Plan §17 (sin verificación de ediciones).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy import optimize, special, stats

from circularis_rel.motor import __version__
from circularis_rel.motor.tipos import AjusteWeibull, Configuracion, Observacion, ResultadoPar

_TABLA_CCC = Path(__file__).parent / "tablas" / "ccc_p10.csv"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def contar(obs: list[Observacion]) -> tuple[int, int, int]:
    nf = sum(o.estado == "F" for o in obs)
    ns = sum(o.estado == "S" for o in obs)
    ni = sum(o.estado == "I" for o in obs)
    return nf, ns, ni


def hash_datos(obs: list[Observacion]) -> str:
    datos = sorted((round(o.edad, 6), o.estado, None if o.edad_inf is None else round(o.edad_inf, 6)) for o in obs)
    return hashlib.sha256(json.dumps(datos).encode()).hexdigest()


@lru_cache(maxsize=1)
def _tabla_ccc() -> dict[int, float]:
    filas = _TABLA_CCC.read_text(encoding="utf-8").strip().splitlines()[1:]
    return {int(n): float(v) for n, v in (f.split(",") for f in filas)}


def r2_critico(n_fallas: int) -> float | None:
    """Percentil 10 del r² de la recta de Weibull para n fallas (tabla generada por Monte Carlo)."""
    if n_fallas < 3:
        return None
    tabla = _tabla_ccc()
    return tabla[min(n_fallas, max(tabla))]


# ---------------------------------------------------------------------------
# Rangos de Johnson y Benard, RRX
# ---------------------------------------------------------------------------


def rangos_johnson(obs: list[Observacion]) -> list[tuple[float, float, float]]:
    """(edad de falla, rango ajustado, F mediana de Benard) de cada falla.

    Rango ajustado (Johnson): incremento = (n + 1 − rango anterior) / (1 + n.º de ítems desde este en adelante).
    Con edades iguales, las fallas se ordenan antes que las suspensiones.
    """
    datos = sorted((o for o in obs if o.estado in ("F", "S")), key=lambda o: (o.edad, o.estado != "F"))
    n = len(datos)
    anterior = 0.0
    salida = []
    for k, o in enumerate(datos):
        if o.estado != "F":
            continue
        inverso = n - k
        anterior += (n + 1 - anterior) / (1 + inverso)
        salida.append((o.edad, anterior, (anterior - 0.3) / (n + 0.4)))
    return salida


def rango_mediano_exacto(i: float, n: int) -> float:
    """Mediana de la distribución beta(i, n − i + 1): el rango mediano exacto que aproxima Benard.
    La tabla de la UNIDAD 2 (diap. 34) usa estos valores (B-015)."""
    return float(stats.beta.median(i, n - i + 1))


def _rrx_puntos(edades: np.ndarray, f_mediana: np.ndarray) -> tuple[float, float, float]:
    x = np.log(edades)
    y = np.log(-np.log(1.0 - f_mediana))
    pendiente, ordenada = np.polyfit(y, x, 1)  # X sobre Y (Abernethy)
    beta = 1.0 / pendiente
    eta = float(np.exp(ordenada))
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
    return float(beta), eta, r2


def rrx(obs: list[Observacion]) -> tuple[float, float, float, list[tuple[float, float, float]]]:
    rangos = rangos_johnson(obs)
    if len(rangos) < 2:
        raise ValueError("RRX necesita al menos 2 fallas")
    edades = np.array([r[0] for r in rangos])
    if np.any(edades <= 0):
        raise ValueError("RRX necesita edades positivas")
    beta, eta, r2 = _rrx_puntos(edades, np.array([r[2] for r in rangos]))
    return beta, eta, r2, rangos


def bootstrap_rrx(obs: list[Observacion], beta: float, eta: float, replicas: int, nivel: float,
                  semilla: int) -> tuple[tuple[float, float], tuple[float, float]]:
    """IC por bootstrap paramétrico: se simula con el mismo patrón de censura (cada suspendida en cᵢ
    se observa como min(Tᵢ, cᵢ)) y se reajusta RRX en cada réplica; percentiles bilaterales."""
    rng = np.random.default_rng(semilla)
    base = [o for o in obs if o.estado in ("F", "S")]
    censuras = np.array([o.edad if o.estado == "S" else np.inf for o in base])
    betas, etas = [], []
    for _ in range(replicas):
        t = eta * rng.weibull(beta, len(base))
        observado = np.minimum(t, censuras)
        estados = np.where(t <= censuras, "F", "S")
        if (estados == "F").sum() < 2:
            continue
        muestra = [Observacion(float(e), str(st)) for e, st in zip(observado, estados, strict=True)]
        try:
            b, h, _r2, _ = rrx(muestra)
        except (ValueError, np.linalg.LinAlgError):
            continue
        if np.isfinite(b) and np.isfinite(h) and b > 0:
            betas.append(b)
            etas.append(h)
    if len(betas) < replicas * 0.5:
        raise ValueError("El bootstrap no convergió en suficientes réplicas")
    a = (1 - nivel) / 2
    return ((float(np.quantile(betas, a)), float(np.quantile(betas, 1 - a))),
            (float(np.quantile(etas, a)), float(np.quantile(etas, 1 - a))))


# ---------------------------------------------------------------------------
# Verosimilitud y MLE
# ---------------------------------------------------------------------------


def _separar(obs: list[Observacion]):
    f = np.array([o.edad for o in obs if o.estado == "F"], dtype=float)
    s = np.array([o.edad for o in obs if o.estado == "S"], dtype=float)
    ia = np.array([o.edad_inf for o in obs if o.estado == "I"], dtype=float)
    ib = np.array([o.edad for o in obs if o.estado == "I"], dtype=float)
    return f, s, ia, ib


def log_verosimilitud(beta: float, eta: float, obs_sep) -> float:
    f, s, ia, ib = obs_sep
    if beta <= 0 or eta <= 0:
        return -np.inf
    ll = 0.0
    if f.size:
        z = f / eta
        ll += np.sum(np.log(beta / eta) + (beta - 1) * np.log(z) - z**beta)
    if s.size:
        ll -= np.sum((s / eta) ** beta)
    if ia.size:
        fa = -np.expm1(-((ia / eta) ** beta))
        fb = -np.expm1(-((ib / eta) ** beta))
        dif = np.clip(fb - fa, 1e-300, None)
        ll += np.sum(np.log(dif))
    return float(ll)


def _eta_dado_beta(beta: float, obs_sep) -> float:
    """MLE de η con β fijo. Cerrado si no hay intervalos: η = [Σ tᵢ^β / r]^(1/β)."""
    f, s, ia, ib = obs_sep
    if ia.size == 0:
        r = max(f.size, 1)
        return float((np.sum(f**beta) + np.sum(s**beta)) / r) ** (1.0 / beta)
    res = optimize.minimize_scalar(lambda le: -log_verosimilitud(beta, math.exp(le), obs_sep),
                                   bounds=(math.log(max(1e-6, np.min(ib) / 100)), math.log(np.max(ib) * 100 + 1)),
                                   method="bounded", options={"xatol": 1e-10})
    return math.exp(res.x)


def _perfil_beta(beta: float, obs_sep) -> float:
    return log_verosimilitud(beta, _eta_dado_beta(beta, obs_sep), obs_sep)


def mle(obs: list[Observacion]) -> tuple[float, float, float]:
    """(β, η, log-verosimilitud máxima) con censura por derecha y por intervalo."""
    sep = _separar(obs)
    nf, _ns, ni = contar(obs)
    if nf + ni < 2:
        raise ValueError("MLE necesita al menos 2 fallas (exactas o por intervalo)")
    res = optimize.minimize_scalar(lambda lb: -_perfil_beta(math.exp(lb), sep), bounds=(math.log(0.05), math.log(50)),
                                   method="bounded", options={"xatol": 1e-10})
    beta = math.exp(res.x)
    eta = _eta_dado_beta(beta, sep)
    return beta, eta, log_verosimilitud(beta, eta, sep)


def ic_razon_verosimilitud(obs: list[Observacion], beta: float, eta: float, nivel: float
                           ) -> tuple[tuple[float, float], tuple[float, float]]:
    """IC por perfil de verosimilitud: {θ: 2[ℓ(θ̂) − ℓ_p(θ)] ≤ χ²₁(nivel)}."""
    sep = _separar(obs)
    lmax = log_verosimilitud(beta, eta, sep)
    umbral = stats.chi2.ppf(nivel, 1) / 2

    def perfil_eta(e: float) -> float:
        r = optimize.minimize_scalar(lambda lb: -log_verosimilitud(math.exp(lb), e, sep),
                                     bounds=(math.log(0.02), math.log(80)), method="bounded", options={"xatol": 1e-10})
        return -r.fun

    def limite(fun, centro: float, factor: float) -> float:
        """Busca el borde del intervalo alejándose de `centro` (×factor) y lo afina con Brent. Si la verosimilitud
        perfil no cae lo suficiente (pocas fallas, mucha censura), el intervalo queda abierto de ese lado:
        devuelve ∞ (o 0) en lugar de un número inventado (D-034)."""
        g = lambda v: lmax - fun(v) - umbral  # noqa: E731  (negativa adentro del intervalo, positiva afuera)
        afuera = centro
        for _ in range(80):
            afuera *= factor
            if g(afuera) > 0:
                a, b = sorted((centro, afuera))
                return optimize.brentq(g, a, b, xtol=1e-9 * centro)
        return math.inf if factor > 1 else 0.0

    b_inf = limite(lambda b: _perfil_beta(b, sep), beta, 0.85)
    b_sup = limite(lambda b: _perfil_beta(b, sep), beta, 1.15)
    e_inf = limite(perfil_eta, eta, 0.9)
    e_sup = limite(perfil_eta, eta, 1.1)
    return (b_inf, b_sup), (e_inf, e_sup)


def ic_fisher(obs: list[Observacion], beta: float, eta: float, nivel: float
              ) -> tuple[tuple[float, float], tuple[float, float]]:
    """IC de matriz de Fisher (normal en escala log). SOLO para validación cruzada (D-004)."""
    sep = _separar(obs)

    def nll(p):
        return -log_verosimilitud(p[0], p[1], sep)

    x = np.array([beta, eta])
    h = np.zeros((2, 2))
    paso = 1e-4 * x
    for i in range(2):
        for j in range(2):
            ei = np.zeros(2)
            ej = np.zeros(2)
            ei[i], ej[j] = paso[i], paso[j]
            h[i, j] = (nll(x + ei + ej) - nll(x + ei - ej) - nll(x - ei + ej) + nll(x - ei - ej)) / (4 * paso[i] * paso[j])
    cov = np.linalg.inv(h)
    z = stats.norm.ppf(1 - (1 - nivel) / 2)
    sb, se = math.sqrt(cov[0, 0]), math.sqrt(cov[1, 1])
    return ((beta * math.exp(-z * sb / beta), beta * math.exp(z * sb / beta)),
            (eta * math.exp(-z * se / eta), eta * math.exp(z * se / eta)))


def factor_rba(n_fallas: int) -> float:
    """C4^3,5 con C4 = √(2/(N−1))·Γ(N/2)/Γ((N−1)/2), N = n.º de fallas (Abernethy, RBA; D-005)."""
    if n_fallas < 2:
        return 1.0
    n = n_fallas
    c4 = math.sqrt(2.0 / (n - 1)) * math.exp(special.gammaln(n / 2) - special.gammaln((n - 1) / 2))
    return c4**3.5


# ---------------------------------------------------------------------------
# Weibayes
# ---------------------------------------------------------------------------


def weibayes(obs: list[Observacion], beta_ref: float, nivel: float
             ) -> tuple[float, tuple[float, float] | None]:
    """η = [Σ tᵢ^β / r]^(1/β) con β de referencia. Con r = 0 se usa r = 1 (cota conservadora, D-011).
    IC de η por χ² (Σ(t/η)^β ~ Gamma(r)): inferior con 2r+2 grados de libertad, superior con 2r."""
    t = np.array([o.edad for o in obs if o.estado in ("F", "S")], dtype=float)
    r = sum(o.estado == "F" for o in obs)
    suma = float(np.sum(t**beta_ref))
    eta = (suma / max(r, 1)) ** (1.0 / beta_ref)
    a = (1 - nivel) / 2
    inf = (2 * suma / stats.chi2.ppf(1 - a, 2 * r + 2)) ** (1.0 / beta_ref)
    sup = (2 * suma / stats.chi2.ppf(a, 2 * r)) ** (1.0 / beta_ref) if r > 0 else math.inf
    return eta, (inf, sup)


# ---------------------------------------------------------------------------
# Confianza, interpretación, selección y ajuste completo
# ---------------------------------------------------------------------------


def confianza(n_fallas: int, cfg: Configuracion) -> str:
    if n_fallas >= cfg.confianza_alta_desde:
        return "ALTA"
    if n_fallas >= cfg.confianza_media_desde:
        return "MEDIA"
    if n_fallas >= cfg.confianza_baja_desde:
        return "BAJA"
    return "GRIS"


def interpretar(beta: float, beta_ic: tuple[float, float] | None, cfg: Configuracion) -> str:
    """D-006: aleatoria si el IC de β contiene a 1 o β está en la banda; si no, por β."""
    if cfg.beta_aleatoria_min <= beta <= cfg.beta_aleatoria_max:
        return "ALEATORIA"
    if cfg.beta_aleatoria_por_ic and beta_ic is not None and beta_ic[0] <= 1.0 <= beta_ic[1]:
        return "ALEATORIA"
    if beta < 1:
        return "MORTALIDAD_INFANTIL"
    if beta > cfg.beta_desgaste_rapido:
        return "DESGASTE_RAPIDO"
    return "DESGASTE"


RECOMENDACIONES = {
    "MORTALIDAD_INFANTIL": "Fallas de juventud: no hacer preventivo por tiempo (cada cambio agrega riesgo). "
                           "Revisar montaje, calidad del repuesto y proveedor.",
    "ALEATORIA": "Fallas al azar: el preventivo por tiempo no sirve. Inspección, mantenimiento por condición o rediseño.",
    "DESGASTE": "Desgaste: el preventivo por tiempo es efectivo si Cf/Cp lo justifica.",
    "DESGASTE_RAPIDO": "Desgaste rápido, fin de vida bien definido: reemplazo a edad fija, muy predecible.",
}


def seleccionar_metodo(n_f: int, n_s: int, n_i: int, beta_ref: float | None, cfg: Configuracion) -> str:
    if n_f + n_i < cfg.min_fallas_rrx:
        return "WEIBAYES" if beta_ref else "NINGUNO"
    total = n_f + n_s + n_i
    if n_f >= cfg.min_fallas_mle or n_i > 0 or (total and n_s / total > cfg.max_frac_suspensiones_rrx):
        return "MLE"
    return "RRX"


def _ajuste_rrx(obs, cfg: Configuracion, con_ic: bool) -> AjusteWeibull:
    beta, eta, r2, rangos = rrx(obs)
    nf, ns, ni = contar(obs)
    a = AjusteWeibull("RRX", beta, eta, r2=r2, r2_critico=r2_critico(nf), n_fallas=nf, n_suspensiones=ns,
                      n_intervalo=ni, nivel_ic=cfg.nivel_ic, rangos=rangos)
    if con_ic:
        try:
            a.beta_ic, a.eta_ic = bootstrap_rrx(obs, beta, eta, cfg.bootstrap_replicas, cfg.nivel_ic, cfg.semilla)
            a.metodo_ic = "BOOTSTRAP"
        except ValueError as e:
            a.advertencias.append(f"Sin IC: {e}")
    if a.r2_critico is not None and r2 < a.r2_critico:
        a.advertencias.append("La recta no ajusta bien (r² menor que el crítico): posible mezcla de modos o γ > 0")
    return a


def _ajuste_mle(obs, cfg: Configuracion, con_ic: bool) -> AjusteWeibull:
    beta, eta, _ll = mle(obs)
    nf, ns, ni = contar(obs)
    a = AjusteWeibull("MLE", beta, eta, n_fallas=nf, n_suspensiones=ns, n_intervalo=ni, nivel_ic=cfg.nivel_ic,
                      beta_mle_sin_corregir=beta)
    if con_ic:
        try:
            a.beta_ic, a.eta_ic = ic_razon_verosimilitud(obs, beta, eta, cfg.nivel_ic)
            a.metodo_ic = "LR"
        except (ValueError, RuntimeError) as e:
            a.advertencias.append(f"Sin IC: {e}")
    if nf + ni < cfg.n_max_rba:
        beta_rba = beta * factor_rba(nf + ni)
        a.beta = beta_rba
        a.eta = _eta_dado_beta(beta_rba, _separar(obs))
        a.metodo = "MLE_RBA"
    if nf >= 2 and ni == 0:
        try:
            _b, _e, r2, rangos = rrx(obs)
            a.r2, a.r2_critico, a.rangos = r2, r2_critico(nf), rangos
        except ValueError:
            pass
    return a


def _completar(a: AjusteWeibull, cfg: Configuracion) -> AjusteWeibull:
    a.confianza = confianza(a.n_fallas + a.n_intervalo, cfg)
    if a.valido:
        a.interpretacion = interpretar(a.beta, a.beta_ic, cfg)
    a.version_motor = __version__
    return a


def comparar_distribuciones(obs: list[Observacion]) -> tuple[dict[str, dict] | None, float | None]:
    """AICc, Anderson-Darling y log-verosimilitud de Weibull 2P, Weibull 3P, lognormal y exponencial
    (librería `reliability`). Solo con censura por derecha. Devuelve (tabla, AD de Weibull 2P)."""
    nf, _ns, ni = contar(obs)
    if ni or nf < 3:
        return None, None
    import warnings

    import matplotlib

    matplotlib.use("Agg")
    from reliability import Fitters

    fallas = [o.edad for o in obs if o.estado == "F"]
    suspensiones = [o.edad for o in obs if o.estado == "S"] or None
    tabla: dict[str, dict] = {}
    for nombre, clase in (("Weibull_2P", Fitters.Fit_Weibull_2P), ("Weibull_3P", Fitters.Fit_Weibull_3P),
                          ("Lognormal_2P", Fitters.Fit_Lognormal_2P), ("Exponential_1P", Fitters.Fit_Exponential_1P)):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                f = clase(failures=fallas, right_censored=suspensiones, show_probability_plot=False, print_results=False)
            tabla[nombre] = {"AICc": float(f.AICc), "AD": float(f.AD), "loglik": float(f.loglik)}
        except Exception as e:  # una distribución que no ajusta no frena a las demás
            tabla[nombre] = {"error": str(e)[:120]}
    ad = tabla.get("Weibull_2P", {}).get("AD")
    return tabla, ad


def ajustar(obs: list[Observacion], cfg: Configuracion | None = None, *, beta_ref: float | None = None,
            metodo_forzado: str | None = None, con_ic: bool = True) -> ResultadoPar:
    """Ajuste completo de una población. Excluye las observaciones marcadas `solo_pronostico`."""
    cfg = cfg or Configuracion()
    datos = [o for o in obs if not o.solo_pronostico]
    nf, ns, ni = contar(datos)
    metodo = metodo_forzado or seleccionar_metodo(nf, ns, ni, beta_ref, cfg)
    alternativa: AjusteWeibull | None = None
    if metodo == "NINGUNO":
        vigente = AjusteWeibull("NINGUNO", None, None, n_fallas=nf, n_suspensiones=ns, n_intervalo=ni)
        vigente.advertencias.append("Datos insuficientes: solo KPIs empíricos (seguí cargando partes y avisos)")
    elif metodo == "WEIBAYES":
        if not beta_ref:
            raise ValueError("Weibayes necesita un β de referencia")
        eta, eta_ic = weibayes(datos, beta_ref, cfg.nivel_ic)
        vigente = AjusteWeibull("WEIBAYES", beta_ref, eta, eta_ic=eta_ic, metodo_ic="CHI2", nivel_ic=cfg.nivel_ic,
                                n_fallas=nf, n_suspensiones=ns, n_intervalo=ni)
        vigente.advertencias.append(f"β = {beta_ref:g} es un supuesto declarado (β de referencia), no un dato medido")
    elif metodo == "RRX":
        vigente = _ajuste_rrx(datos, cfg, con_ic)
        if nf >= 2:
            try:
                alternativa = _ajuste_mle(datos, cfg, con_ic)
            except ValueError:
                alternativa = None
    elif metodo in ("MLE", "MLE_RBA"):
        vigente = _ajuste_mle(datos, cfg, con_ic)
        if ni == 0 and nf >= 2:
            alternativa = _ajuste_rrx(datos, cfg, con_ic)
    else:
        raise ValueError(f"Método desconocido: {metodo}")
    vigente = _completar(vigente, cfg)
    if alternativa is not None:
        alternativa = _completar(alternativa, cfg)
    if cfg.comparar_distribuciones and vigente.n_fallas >= 3 and ni == 0:
        vigente.comparacion, vigente.ad = comparar_distribuciones(datos)
        if alternativa is not None:
            alternativa.comparacion, alternativa.ad = vigente.comparacion, vigente.ad
    return ResultadoPar(vigente, alternativa, hash_datos(datos))


def sin_ic(cfg: Configuracion) -> Configuracion:
    return replace(cfg, comparar_distribuciones=False)


# ---------------------------------------------------------------------------
# Flota: prueba de razón de verosimilitud (Plan §5)
# ---------------------------------------------------------------------------


def prueba_flota(grupos: dict[str, list[Observacion]]) -> tuple[float, float, int]:
    """LR = 2(Σ ℓᵢ − ℓ_agrupado) ~ χ²(2(k−1)). Devuelve (LR, p-valor, grados de libertad).
    Si p > 0,05 no hay evidencia de que sean poblaciones distintas: se pueden agrupar."""
    if len(grupos) < 2:
        raise ValueError("La prueba de flota necesita al menos dos grupos")
    suma = 0.0
    todos: list[Observacion] = []
    for obs in grupos.values():
        _b, _e, ll = mle(obs)
        suma += ll
        todos += obs
    _b, _e, ll_todos = mle(todos)
    lr = max(0.0, 2 * (suma - ll_todos))
    gl = 2 * (len(grupos) - 1)
    return lr, float(stats.chi2.sf(lr, gl)), gl
