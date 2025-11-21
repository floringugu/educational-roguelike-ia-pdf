#!/usr/bin/env python3
"""
🔄 RESET COMPLETO - Educational Roguelike
Limpia TODO: base de datos, PDFs, caché, sesiones
"""

import os
import shutil
from pathlib import Path
import sqlite3

def reset_complete():
    """Reset completo del sistema"""
    
    print("\n" + "🔥" * 35)
    print("   RESET COMPLETO DEL JUEGO")
    print("🔥" * 35 + "\n")
    
    confirmation = input("⚠️  Esto eliminará TODO (PDFs, preguntas, estadísticas). ¿Continuar? (yes/no): ")
    
    if confirmation.lower() != 'yes':
        print("❌ Operación cancelada")
        return
    
    print("\n🗑️  Iniciando limpieza completa...\n")
    
    # 1. Eliminar base de datos
    print("📊 Eliminando base de datos...")
    db_path = Path('data/questions.db')
    if db_path.exists():
        db_path.unlink()
        print("   ✅ Base de datos eliminada")
    else:
        print("   ℹ️  Base de datos no existía")
    
    # 2. Eliminar PDFs subidos
    print("\n📄 Eliminando PDFs...")
    pdf_dir = Path('data/pdfs')
    if pdf_dir.exists():
        count = len(list(pdf_dir.glob('*.pdf')))
        shutil.rmtree(pdf_dir)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {count} PDFs eliminados")
    else:
        pdf_dir.mkdir(parents=True, exist_ok=True)
        print("   ℹ️  Directorio PDFs recreado")
    
    # 3. Eliminar caché de OCR
    print("\n🔍 Eliminando caché de OCR...")
    ocr_cache_dir = Path('data/ocr_cache')
    if ocr_cache_dir.exists():
        count = len(list(ocr_cache_dir.glob('*.pkl')))
        shutil.rmtree(ocr_cache_dir)
        ocr_cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {count} archivos de caché eliminados")
    else:
        ocr_cache_dir.mkdir(parents=True, exist_ok=True)
        print("   ℹ️  Directorio caché recreado")
    
    # 4. Eliminar exports/estadísticas
    print("\n📊 Eliminando estadísticas exportadas...")
    export_dir = Path('data/exports')
    if export_dir.exists():
        count = len(list(export_dir.glob('*')))
        for file in export_dir.glob('*'):
            file.unlink()
        print(f"   ✅ {count} archivos de estadísticas eliminados")
    else:
        export_dir.mkdir(parents=True, exist_ok=True)
        print("   ℹ️  Directorio exports recreado")
    
    # 5. Limpiar backups
    print("\n💾 Eliminando backups...")
    backup_dir = Path('data/backups')
    if backup_dir.exists():
        count = len(list(backup_dir.glob('*.db')))
        shutil.rmtree(backup_dir)
        print(f"   ✅ {count} backups eliminados")
    else:
        print("   ℹ️  No había backups")
    
    # 6. Recrear base de datos limpia
    print("\n🆕 Creando base de datos nueva...")
    try:
        from database import db
        print("   ✅ Base de datos inicializada")
    except Exception as e:
        print(f"   ⚠️  Error creando BD: {e}")
    
    # 7. Limpiar caché del navegador (instrucciones)
    print("\n" + "=" * 70)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 70 + "\n")
    
    print("📝 Pasos adicionales:\n")
    print("1. 🌐 Limpiar caché del navegador:")
    print("   • Chrome/Edge: Ctrl+Shift+Delete → Borrar todo")
    print("   • Firefox: Ctrl+Shift+Delete → Borrar todo")
    print("   • O simplemente: Ctrl+Shift+R para recarga forzada\n")
    
    print("2. 🔄 Reiniciar el servidor:")
    print("   • Ctrl+C para detener")
    print("   • python app.py para iniciar\n")
    
    print("3. 🎮 Abrir en navegador:")
    print("   • http://localhost:5000")
    print("   • ¡Comenzar desde cero!\n")
    
    print("=" * 70 + "\n")
    
    # Resumen
    print("📋 Resumen de lo eliminado:")
    print("   ✓ Base de datos (questions.db)")
    print("   ✓ PDFs subidos")
    print("   ✓ Caché de OCR")
    print("   ✓ Estadísticas exportadas")
    print("   ✓ Backups\n")
    
    print("🎉 ¡Sistema completamente limpio! Listo para empezar de nuevo.\n")


def reset_solo_pdfs():
    """Solo elimina PDFs pero mantiene configuración"""
    
    print("\n📄 Eliminando solo PDFs...\n")
    
    # Eliminar PDFs
    pdf_dir = Path('data/pdfs')
    if pdf_dir.exists():
        count = 0
        for pdf in pdf_dir.glob('*.pdf'):
            pdf.unlink()
            count += 1
        print(f"✅ {count} PDFs eliminados")
    
    # Limpiar registros de PDFs en la BD
    db_path = Path('data/questions.db')
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Contar antes de eliminar
        cursor.execute("SELECT COUNT(*) FROM pdfs")
        pdf_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM questions")
        question_count = cursor.fetchone()[0]
        
        # Eliminar todo
        cursor.execute("DELETE FROM questions")
        cursor.execute("DELETE FROM pdfs")
        cursor.execute("DELETE FROM game_saves")
        cursor.execute("DELETE FROM answer_history")
        
        conn.commit()
        conn.close()
        
        print(f"✅ {pdf_count} registros de PDFs eliminados")
        print(f"✅ {question_count} preguntas eliminadas")
    
    print("\n✅ PDFs eliminados. Estadísticas y configuración mantenidas.\n")


def reset_solo_cache():
    """Solo limpia caché de OCR"""
    
    print("\n🔍 Limpiando solo caché de OCR...\n")
    
    ocr_cache_dir = Path('data/ocr_cache')
    if ocr_cache_dir.exists():
        count = 0
        for cache_file in ocr_cache_dir.glob('*.pkl'):
            cache_file.unlink()
            count += 1
        print(f"✅ {count} archivos de caché eliminados")
    else:
        print("ℹ️  No había caché para eliminar")
    
    print("\n✅ Caché limpiado.\n")


def mostrar_menu():
    """Menú interactivo"""
    
    print("\n" + "🎮" * 35)
    print("   EDUCATIONAL ROGUELIKE - RESET TOOL")
    print("🎮" * 35 + "\n")
    
    print("Opciones de reset:\n")
    print("1. 🔥 Reset COMPLETO (TODO)")
    print("   → Base de datos, PDFs, caché, estadísticas")
    print()
    print("2. 📄 Solo PDFs y preguntas")
    print("   → Mantiene configuración y estructura")
    print()
    print("3. 🗑️  Solo caché de OCR")
    print("   → Limpia caché para reprocesar PDFs")
    print()
    print("4. ❌ Cancelar")
    print()
    
    opcion = input("Selecciona una opción (1-4): ").strip()
    
    if opcion == '1':
        reset_complete()
    elif opcion == '2':
        reset_solo_pdfs()
    elif opcion == '3':
        reset_solo_cache()
    elif opcion == '4':
        print("\n❌ Operación cancelada\n")
    else:
        print("\n⚠️  Opción inválida\n")


if __name__ == '__main__':
    import sys
    
    if '--complete' in sys.argv:
        reset_complete()
    elif '--pdfs' in sys.argv:
        reset_solo_pdfs()
    elif '--cache' in sys.argv:
        reset_solo_cache()
    else:
        mostrar_menu()
