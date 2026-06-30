"""
IntelExtorsión - Preparación del Proyecto para Despliegue
Elimina carpetas pesadas y archivos innecesarios antes de subir a la VM.
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Carpetas y archivos a eliminar (pesados/inútiles para producción)
CLEAN_TARGETS = [
    # Node
    "node_modules",
    ".next",
    "out",
    ".cache",
    # Python
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    "htmlcov",
    ".coverage",
    # Hardhat
    "artifacts",
    "cache",
    "typechain-types",
    # Git
    ".git",
    ".gitignore",
    # IDE
    ".vscode",
    ".idea",
    "*.swp",
    "*.swo",
    # OS
    "Thumbs.db",
    ".DS_Store",
    # Docs innecesarias para producción
    "MIGRATION_REPORT.md",
    "QA_REPORT.md",
    "API_KEYS_GUIDE.md",
]

# Archivos/carpetas que SÍ debemos mantener
KEEP_PATTERNS = [
    "docker-compose.yml",
    "docker-compose.prod.yml",
    ".env",
    ".env.production",
    "AGENTS.md",
    "INSTALL.md",
    "RUN.md",
    "CHECKLIST_DEPLOY.md",
    "deploy",
]

def get_size_mb(path):
    """Obtiene el tamaño total de un directorio en MB."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total / (1024 * 1024)

def clean_directory(directory, patterns):
    """Limpia archivos/carpetas que coincidan con los patrones."""
    removed = []
    for pattern in patterns:
        if pattern.startswith("*"):
            # Glob pattern
            for item in directory.rglob(pattern):
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    removed.append(str(item.relative_to(ROOT)))
                except Exception as e:
                    print(f"  Error eliminando {item}: {e}")
        else:
            # Nombre exacto
            for item in directory.rglob(pattern):
                if item.name == pattern or (item.is_dir() and item.name == pattern):
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        removed.append(str(item.relative_to(ROOT)))
                    except Exception as e:
                        print(f"  Error eliminando {item}: {e}")
    return removed

def main():
    print("=" * 60)
    print("  IntelExtorsión - Preparación para Despliegue")
    print("=" * 60)
    
    # Calcular tamaño inicial
    initial_size = get_size_mb(ROOT)
    print(f"\nTamaño inicial del proyecto: {initial_size:.1f} MB")
    
    print("\n[1/3] Eliminando carpetas pesadas...")
    removed = clean_directory(ROOT, CLEAN_TARGETS)
    print(f"  Eliminados: {len(removed)} items")
    
    print("\n[2/3] Limpiando contenedores Docker huérfanos...")
    try:
        os.system("docker system prune -f")
    except Exception:
        print("  (saltado - Docker no disponible en Windows)")
    
    print("\n[3/3] Calculando tamaño final...")
    final_size = get_size_mb(ROOT)
    saved = initial_size - final_size
    
    print(f"\n{'=' * 60}")
    print(f"  Tamaño inicial:  {initial_size:.1f} MB")
    print(f"  Tamaño final:    {final_size:.1f} MB")
    print(f"  Espacio ahorrado: {saved:.1f} MB")
    print(f"{'=' * 60}")
    
    # Verificar que los archivos críticos existen
    critical_files = [
        "docker-compose.yml",
        "intel_extorsion_agent_system/requirements.txt",
        "intel_extorsion_web3_system/backend/requirements.txt",
        "intel_extorsion_frontend_citizen/Dockerfile",
        "intel_extorsion_frontend_police/Dockerfile",
    ]
    
    print("\nVerificación de archivos críticos:")
    all_ok = True
    for f in critical_files:
        exists = (ROOT / f).exists()
        status = "OK" if exists else "FALTA"
        print(f"  [{status}] {f}")
        if not exists:
            all_ok = False
    
    if all_ok:
        print("\nProyecto listo para despliegue")
        print(f"\nSiguiente paso: SCP a la VM")
        print(f"  scp -r {ROOT.name} root@142.93.240.223:/root/")
    else:
        print("\nFaltan archivos criticos. Revisar antes de desplegar.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
