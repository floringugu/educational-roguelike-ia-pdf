#!/usr/bin/env python3
"""
Script de Prueba Rápida - Educational Roguelike OCR
Verifica la instalación y funcionalidad de OCR
"""

import sys
from pathlib import Path

print("=" * 70)
print("🔍 VERIFICACIÓN DE INSTALACIÓN - OCR SUPPORT")
print("=" * 70)
print()

# ═══════════════════════════════════════════════════════════════════
# 1. Verificar dependencias de Python
# ═══════════════════════════════════════════════════════════════════

print("📦 Verificando paquetes de Python...")
print()

missing_packages = []
installed_packages = []

# Verificar pytesseract
try:
    import pytesseract
    installed_packages.append("✅ pytesseract")
except ImportError:
    missing_packages.append("pytesseract")
    print("❌ pytesseract NO instalado")

# Verificar pdf2image
try:
    from pdf2image import convert_from_path
    installed_packages.append("✅ pdf2image")
except ImportError:
    missing_packages.append("pdf2image")
    print("❌ pdf2image NO instalado")

# Verificar Pillow
try:
    from PIL import Image
    installed_packages.append("✅ Pillow (PIL)")
except ImportError:
    missing_packages.append("Pillow")
    print("❌ Pillow NO instalado")

# Verificar pdfplumber
try:
    import pdfplumber
    installed_packages.append("✅ pdfplumber")
except ImportError:
    missing_packages.append("pdfplumber")
    print("❌ pdfplumber NO instalado")

# Mostrar paquetes instalados
if installed_packages:
    print("Paquetes instalados:")
    for pkg in installed_packages:
        print(f"  {pkg}")
    print()

# Si faltan paquetes
if missing_packages:
    print("❌ FALTAN PAQUETES:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    print()
    print("Instalar con:")
    print(f"  pip install {' '.join(missing_packages)}")
    print()

# ═══════════════════════════════════════════════════════════════════
# 2. Verificar Tesseract OCR
# ═══════════════════════════════════════════════════════════════════

print("-" * 70)
print("🔍 Verificando Tesseract OCR...")
print()

tesseract_installed = False
tesseract_version = None

try:
    import pytesseract
    import subprocess
    
    # Intentar ejecutar tesseract
    try:
        result = subprocess.run(
            ['tesseract', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            tesseract_installed = True
            # Extraer versión
            version_line = result.stdout.split('\n')[0]
            tesseract_version = version_line.replace('tesseract ', '')
            print(f"✅ Tesseract instalado: {tesseract_version}")
        else:
            print("❌ Tesseract NO responde correctamente")
            
    except FileNotFoundError:
        print("❌ Tesseract NO encontrado en PATH")
        print()
        print("Instalar Tesseract:")
        print("  - Linux:   sudo apt-get install tesseract-ocr")
        print("  - macOS:   brew install tesseract")
        print("  - Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print()
        
except ImportError:
    print("⚠️ No se puede verificar (pytesseract no instalado)")

# Verificar idiomas disponibles
if tesseract_installed:
    print()
    print("Verificando idiomas instalados...")
    try:
        result = subprocess.run(
            ['tesseract', '--list-langs'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            langs = result.stdout.strip().split('\n')[1:]  # Skip first line
            print(f"Idiomas disponibles: {', '.join(langs)}")
            
            # Verificar idiomas clave
            required_langs = ['eng', 'spa']
            missing_langs = [lang for lang in required_langs if lang not in langs]
            
            if missing_langs:
                print()
                print("⚠️ Idiomas recomendados faltantes:")
                for lang in missing_langs:
                    print(f"  - {lang}")
                print()
                print("Instalar idiomas (Linux/Debian):")
                for lang in missing_langs:
                    print(f"  sudo apt-get install tesseract-ocr-{lang}")
            else:
                print("✅ Idiomas requeridos (eng, spa) están instalados")
        else:
            print("⚠️ No se pudieron listar los idiomas")
            
    except Exception as e:
        print(f"⚠️ Error al verificar idiomas: {e}")

print()

# ═══════════════════════════════════════════════════════════════════
# 3. Verificar Poppler (para pdf2image)
# ═══════════════════════════════════════════════════════════════════

print("-" * 70)
print("📄 Verificando Poppler (para pdf2image)...")
print()

poppler_installed = False

try:
    import subprocess
    
    # Intentar ejecutar pdftoppm (parte de poppler)
    try:
        result = subprocess.run(
            ['pdftoppm', '-v'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        poppler_installed = True
        version_info = result.stderr.strip().split('\n')[0] if result.stderr else "Versión desconocida"
        print(f"✅ Poppler instalado: {version_info}")
        
    except FileNotFoundError:
        print("❌ Poppler NO encontrado")
        print()
        print("Instalar Poppler:")
        print("  - Linux:   sudo apt-get install poppler-utils")
        print("  - macOS:   brew install poppler")
        print("  - Windows: Descargar de https://github.com/oschwartz10612/poppler-windows")
        print()
        
except Exception as e:
    print(f"⚠️ Error al verificar Poppler: {e}")

print()

# ═══════════════════════════════════════════════════════════════════
# 4. Prueba de Funcionalidad
# ═══════════════════════════════════════════════════════════════════

print("-" * 70)
print("🧪 Prueba de Funcionalidad...")
print()

if not missing_packages and tesseract_installed:
    print("Intentando crear una imagen de prueba y extraer texto...")
    print()
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import pytesseract
        import tempfile
        
        # Crear imagen de prueba
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Dibujar texto
        try:
            # Intentar usar fuente del sistema
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            # Fallback a fuente por defecto
            font = ImageFont.load_default()
        
        draw.text((10, 30), "Educational Roguelike Test", fill='black', font=font)
        
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name
        
        # Intentar OCR
        extracted_text = pytesseract.image_to_string(img, lang='eng')
        
        print("✅ OCR funcional!")
        print(f"   Texto extraído: '{extracted_text.strip()}'")
        print()
        
        # Limpiar
        Path(tmp_path).unlink()
        
    except Exception as e:
        print(f"❌ Error en prueba de OCR: {e}")
        print()
else:
    print("⚠️ No se puede realizar prueba (faltan dependencias)")
    print()

# ═══════════════════════════════════════════════════════════════════
# 5. Resumen y Recomendaciones
# ═══════════════════════════════════════════════════════════════════

print("=" * 70)
print("📊 RESUMEN")
print("=" * 70)
print()

all_ok = (
    not missing_packages and 
    tesseract_installed and 
    poppler_installed
)

if all_ok:
    print("🎉 ¡TODO INSTALADO CORRECTAMENTE!")
    print()
    print("✅ Paquetes de Python: OK")
    print("✅ Tesseract OCR: OK")
    print("✅ Poppler: OK")
    print()
    print("Tu sistema está listo para procesar:")
    print("  • PDFs con texto ⚡")
    print("  • PDFs escaneados 🔍")
    print("  • Imágenes (JPG, PNG, etc.) 🖼️")
    print()
    print("Siguiente paso:")
    print("  python app.py")
    print()
else:
    print("⚠️ INSTALACIÓN INCOMPLETA")
    print()
    
    if missing_packages:
        print("❌ Faltan paquetes de Python:")
        print(f"   pip install {' '.join(missing_packages)}")
        print()
    
    if not tesseract_installed:
        print("❌ Falta Tesseract OCR")
        print("   Ver instrucciones arriba")
        print()
    
    if not poppler_installed:
        print("❌ Falta Poppler")
        print("   Ver instrucciones arriba")
        print()
    
    print("Funcionalidad disponible:")
    if not missing_packages:
        print("  ✅ PDFs con texto")
    else:
        print("  ❌ PDFs con texto (requiere pdfplumber)")
    
    if not missing_packages and tesseract_installed:
        print("  ✅ PDFs escaneados e imágenes (OCR)")
    else:
        print("  ❌ PDFs escaneados e imágenes (requiere OCR)")
    print()

print("=" * 70)
print()

# Código de salida
sys.exit(0 if all_ok else 1)
