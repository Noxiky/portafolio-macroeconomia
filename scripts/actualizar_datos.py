#!/usr/bin/env python3
"""Actualiza data/macro.json con datos del BCB (IPC/INE republicado, tipo de cambio oficial, UFV).
Uso: python scripts/actualizar_datos.py
Sin dependencias externas: solo urllib + re.
"""
import json, re, html, sys, datetime, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "macro.json"
UA = {"User-Agent": "Mozilla/5.0 (portafolio-macro; +github pages)"}
MESES = {m:i+1 for i,m in enumerate(["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"])}

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def strip(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    s = html.unescape(re.sub(r"<[^>]+>", " | ", s))
    s = re.sub(r"(\s*\|\s*)+", " | ", s)
    return re.sub(r"\s+", " ", s)

def num(x):
    return float(x.replace(".", "").replace(",", ".")) if x.count(",")==1 and x.count(".")<=1 and x.rfind(",")>x.rfind(".") else float(x.replace(",", ""))

def ipc(paginas=4):
    rows = {}
    for p in range(paginas):
        url = "https://www.bcb.gob.bo/?q=indicadores_inflacion" + (f"&page={p}" if p else "")
        try: t = strip(fetch(url))
        except Exception:
            if p == 0: raise
            break
        for m in re.finditer(r"(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre) (\d{4}) \| ((?:[\d.,]+ \| )?)(-?[\d,]+)% \| (-?[\d,]+)% \| (-?[\d,]+)%", t):
            mes, anio, idx, mensual, acum, anual = m.groups()
            per = f"{anio}-{MESES[mes.lower()]:02d}"
            rows[per] = {"periodo": per, "mes": mes, "anio": int(anio),
                "indice": num(idx.strip(" |")) if idx.strip(" |") else None,
                "mensual": num(mensual), "acumulada": num(acum), "interanual": num(anual)}
    return [rows[k] for k in sorted(rows)]

def tipo_cambio():
    t = strip(fetch("https://www.bcb.gob.bo/librerias/indicadores/otras/ultimo.php"))
    fecha = re.search(r"TABLA DE COTIZACIONES DEL (\d{1,2}) DE (\w+) DE (\d{4})", t, re.I)
    tco = re.search(r"ESTADOS UNIDOS \| D[ÓO]LAR \| USD \| ([\d.,]+)", t)
    tabla = re.search(r"TABLA No\. ([\d-]+)", t)
    monedas = {}
    for m in re.finditer(r"\| ([A-ZÁÉÍÓÚÑ. ]+?) \| ([A-ZÁÉÍÓÚÑ ]+?) \| ([A-Z]{3}) \| ([\d.,]+) \| ([\d.,]+)", t):
        pais, moneda, cod, bs, me = m.groups()
        monedas[cod] = {"pais": pais.strip(), "moneda": moneda.strip(), "bs_por_unidad": num(bs), "unidades_por_usd": num(me)}
    f = None
    if fecha:
        d, mes, a = fecha.groups()
        f = f"{a}-{MESES[mes.lower()]:02d}-{int(d):02d}"
    return {"fecha": f, "tabla": tabla.group(1) if tabla else None, "oficial_bs_usd": num(tco.group(1)) if tco else None, "monedas": monedas}

def ufv():
    t = strip(fetch("https://www.bcb.gob.bo/librerias/indicadores/ufv/ultimo.php"))
    fecha = re.search(r"FECHA: \| (\d{1,2}) de (\w+) (\d{4})", t)
    val = re.search(r"Bs \| ([\d.,]+) por unidad", t)
    f = None
    if fecha:
        d, mes, a = fecha.groups(); f = f"{a}-{MESES[mes.lower()]:02d}-{int(d):02d}"
    return {"fecha": f, "valor": num(val.group(1)) if val else None}

def main():
    prev = {}
    if OUT.exists():
        try: prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception: prev = {}
    data = {"actualizado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "fuentes": {
        "ipc": "INE (IPC base 2016=100), republicado por BCB · https://www.bcb.gob.bo/?q=indicadores_inflacion",
        "tipo_cambio": "BCB · Tabla de cotizaciones · https://www.bcb.gob.bo/?q=cotizaciones_tc",
        "ufv": "BCB · Unidad de Fomento de Vivienda · https://www.bcb.gob.bo/?q=servicios/ufv/datos_estadisticos"}}
    errores = []
    for key, fn in (("ipc", ipc), ("tipo_cambio", tipo_cambio), ("ufv", ufv)):
        try:
            v = fn()
            if not v or (isinstance(v, list) and len(v) < 12): raise ValueError("respuesta vacía o incompleta")
            data[key] = v
        except Exception as e:
            errores.append(f"{key}: {e}")
            if key in prev: data[key] = prev[key]
    # serie histórica de tipo de cambio: acumular una observación por fecha
    hist = {h["fecha"]: h["oficial"] for h in prev.get("tc_historico", [])}
    tc = data.get("tipo_cambio", {})
    if tc.get("fecha") and tc.get("oficial_bs_usd"): hist[tc["fecha"]] = tc["oficial_bs_usd"]
    # semillas del cuaderno de apuntes (BCB)
    hist.setdefault("2025-11-30", 6.96); hist.setdefault("2026-08-20", 11.52); hist.setdefault("2026-09-03", 12.32)
    data["tc_historico"] = [{"fecha": k, "oficial": v} for k, v in sorted(hist.items())]
    data["errores"] = errores
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK -> {OUT}  ipc:{len(data.get('ipc',[]))} filas  tc:{tc.get('oficial_bs_usd')} ({tc.get('fecha')})  ufv:{data.get('ufv',{}).get('valor')}")
    if errores: print("AVISOS:", *errores, sep="\n  ")
    return 0

if __name__ == "__main__":
    sys.exit(main())
