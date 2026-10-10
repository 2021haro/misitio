import re
import sys
import urllib.request
from pathlib import Path

# ========== CONFIGURACIÓN ==========
# URL del reproductor embebido (sustituye esta si hace falta)
PLAYER_URL = "https://noticiasnrt.com/la-caliente/"
NOMBRE_CANAL = "La Caliente"
ARCHIVO_M3U = Path("canales.m3u")

# Filtro: el audio (aac-128) o video (h264-480). Pon "aac" para radio.
FILTRO_STREAM = "aac"

# Headers para parecer un navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
}
# ===================================


def descargar(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")


def extraer_iframe(html):
    """Busca el iframe del reproductor en la página principal."""
    match = re.search(r'<iframe[^>]+src="([^"]+)"', html)
    return match.group(1) if match else None


def extraer_stream_url(html, filtro):
    """
    Busca la URL completa del .m3u8 en el HTML del reproductor.
    El patrón es: https://...dmcdn.net/sec2(TOKEN)/.../xxx-live-aac-128.m3u8
    """
    # Buscamos cualquier URL que contenga dmcdn.net y termine en .m3u8
    patron = r'https?://[^\s"\'<>]*dmcdn\.net/[^\s"\'<>]*\.m3u8'
    candidatas = re.findall(patron, html)
    if not candidatas:
        return None

    # Preferimos las que coincidan con el filtro (aac / h264)
    for url in candidatas:
        if filtro in url.lower():
            return url

    # Si no hay coincidencia con el filtro, devolvemos la primera
    return candidatas[0]


def actualizar_canal_en_m3u(archivo, nombre, url_stream):
    if not archivo.exists():
        archivo.write_text(f"#EXTM3U\n\n#EXTINF:-1,{nombre}\n{url_stream}\n",
                           encoding="utf-8")
        return

    contenido = archivo.read_text(encoding="utf-8")
    lineas = contenido.splitlines()

    encontrado = False
    for i, linea in enumerate(lineas):
        if linea.startswith("#EXTINF") and nombre in linea:
            if i + 1 < len(lineas) and not lineas[i + 1].startswith("#"):
                lineas[i + 1] = url_stream
                encontrado = True
                print(f"Actualizado '{nombre}' en línea {i+2}")
                break

    if not encontrado:
        if lineas and lineas[-1] != "":
            lineas.append("")
        lineas.append(f"#EXTINF:-1,{nombre}")
        lineas.append(url_stream)
        print(f"Canal '{nombre}' agregado al final")

    archivo.write_text("\n".join(lineas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(f"Descargando: {PLAYER_URL}")
    try:
        html = descargar(PLAYER_URL)
        print(f"Descargado: {len(html)} bytes")
    except Exception as e:
        print(f"Error al descargar: {e}")
        sys.exit(1)

    # 1. Intentar extraer directo del HTML
    url = extraer_stream_url(html, FILTRO_STREAM)

    # 2. Si no aparece, buscar iframe y descargarlo
    if not url:
        print("No encontrado en el HTML principal. Buscando iframe...")
        iframe = extraer_iframe(html)
        if iframe:
            if iframe.startswith("//"):
                iframe = "https:" + iframe
            elif iframe.startswith("/"):
                iframe = "https://noticiasnrt.com" + iframe
            print(f"Iframe: {iframe}")
            try:
                html_iframe = descargar(iframe)
                print(f"Iframe descargado: {len(html_iframe)} bytes")
                url = extraer_stream_url(html_iframe, FILTRO_STREAM)
            except Exception as e:
                print(f"Error al descargar iframe: {e}")

    # 3. Resultado final
    if not url:
        print("❌ No se encontró el .m3u8.")
        print("--- Primeros 2000 caracteres del HTML para depurar ---")
        print(html[:2000])
        sys.exit(1)

    print(f"✅ URL del stream: {url}")
    actualizar_canal_en_m3u(ARCHIVO_M3U, NOMBRE_CANAL, url)
