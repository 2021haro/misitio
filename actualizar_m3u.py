import subprocess
import sys
import re
from pathlib import Path

PAGINA_URL = "https://noticiasnrt.com/la-caliente/"
NOMBRE_CANAL = "La Caliente"
ARCHIVO_M3U = Path("canales.m3u")

def obtener_stream_url(pagina_url):
    try:
        resultado = subprocess.run(
            ["yt-dlp", "-g", "--no-warnings", pagina_url],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        return resultado.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None
    except FileNotFoundError:
        print("yt-dlp no encontrado")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Timeout")
        return None

def actualizar_canal_en_m3u(archivo, nombre, url_stream):
    if not archivo.exists():
        print(f"No existe {archivo}, creando uno nuevo.")
        archivo.write_text(f"#EXTM3U\n\n#EXTINF:-1,{nombre}\n{url_stream}\n", encoding="utf-8")
        return

    contenido = archivo.read_text(encoding="utf-8")
    lineas = contenido.splitlines()

    # Buscar bloque de La Caliente: la línea #EXTINF que contiene el nombre,
    # seguida de la URL.
    encontrado = False
    for i, linea in enumerate(lineas):
        if linea.startswith("#EXTINF") and nombre in linea:
            # La URL está en la línea siguiente
            if i + 1 < len(lineas) and not lineas[i + 1].startswith("#"):
                lineas[i + 1] = url_stream
                encontrado = True
                print(f"Actualizado canal '{nombre}' en línea {i+2}")
                break

    if not encontrado:
        # Agregar al final
        if lineas and lineas[-1] != "":
            lineas.append("")
        lineas.append(f"#EXTINF:-1,{nombre}")
        lineas.append(url_stream)
        print(f"Canal '{nombre}' agregado al final")

    archivo.write_text("\n".join(lineas) + "\n", encoding="utf-8")

if __name__ == "__main__":
    print("Obteniendo URL del stream...")
    url = obtener_stream_url(PAGINA_URL)

    if url:
        print(f"URL obtenida: {url}")
        actualizar_canal_en_m3u(ARCHIVO_M3U, NOMBRE_CANAL, url)
    else:
        print("No se pudo obtener la URL.")
        sys.exit(1)
