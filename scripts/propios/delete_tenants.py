#!/usr/bin/env python3
"""
Script para borrar todos los tenants excepto default_tenant.
Como ChromaDB no permite borrar tenants directamente, borramos todas sus bases de datos.
"""
import os
import sys
from pathlib import Path
import requests

# Obtener el directorio donde está este script
SCRIPT_DIR = Path(__file__).parent.resolve()
ENV_FILE = SCRIPT_DIR / ".env"

# Cargar variables de entorno desde el archivo .env si existe
if ENV_FILE.exists():
    try:
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=ENV_FILE, override=True)
        except ImportError:
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip('"\'')
                        os.environ[key.strip()] = value
    except Exception as e:
        print(f"⚠️  Error al cargar .env: {e}", file=sys.stderr)

def main():
    """Borra todas las bases de datos de los tenants (excepto default_tenant)."""
    host = os.getenv("CHROMA_HOST", "localhost")
    port = os.getenv("CHROMA_PORT", "8000")
    api_key = os.getenv("CHROMA_API_KEY", "")
    
    base_url = f"http://{host}:{port}/api/v2"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    # Lista de tenants conocidos a limpiar (excepto default_tenant)
    tenants_to_clean = ["autocasion_symfony", "test_tenant"]
    
    print("🗑️  Limpiando tenants (excepto default_tenant)...")
    print("   (Borrando todas las bases de datos de cada tenant)")
    
    cleaned_count = 0
    for tenant_name in tenants_to_clean:
        try:
            # Verificar si el tenant existe
            check_url = f"{base_url}/tenants/{tenant_name}"
            response = requests.get(check_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                print(f"\n🔍 Procesando tenant '{tenant_name}'...")
                
                # Intentar listar bases de datos del tenant
                # Nota: ChromaDB puede no tener un endpoint directo para listar databases
                # Intentamos borrar las bases de datos conocidas
                databases_to_delete = ["default_database"]
                
                for db_name in databases_to_delete:
                    try:
                        # Intentar borrar la base de datos
                        delete_url = f"{base_url}/tenants/{tenant_name}/databases/{db_name}"
                        delete_response = requests.delete(delete_url, headers=headers, timeout=5)
                        
                        if delete_response.status_code in [200, 204]:
                            print(f"  ✅ Base de datos '{db_name}' borrada")
                        elif delete_response.status_code == 404:
                            print(f"  ℹ️  Base de datos '{db_name}' no existe")
                        else:
                            print(f"  ⚠️  No se pudo borrar '{db_name}' (código: {delete_response.status_code})")
                    except Exception as e:
                        print(f"  ⚠️  Error al borrar base de datos '{db_name}': {e}")
                
                # Intentar borrar el tenant directamente (puede que funcione en algunas versiones)
                try:
                    delete_tenant_url = f"{base_url}/tenants/{tenant_name}"
                    delete_response = requests.delete(delete_tenant_url, headers=headers, timeout=5)
                    
                    if delete_response.status_code in [200, 204]:
                        print(f"  ✅ Tenant '{tenant_name}' borrado exitosamente")
                        cleaned_count += 1
                    elif delete_response.status_code == 405:
                        print(f"  ℹ️  El tenant '{tenant_name}' no se puede borrar directamente (405 Method Not Allowed)")
                        print(f"     ChromaDB no permite borrar tenants mediante la API REST")
                    else:
                        print(f"  ⚠️  Respuesta al intentar borrar tenant: {delete_response.status_code}")
                except Exception as e:
                    print(f"  ⚠️  Error al intentar borrar tenant: {e}")
                    
            elif response.status_code == 404:
                print(f"ℹ️  Tenant '{tenant_name}' no existe, omitiendo")
            else:
                print(f"⚠️  Error al verificar '{tenant_name}' (código: {response.status_code})")
        except Exception as e:
            print(f"⚠️  Error procesando '{tenant_name}': {e}")
    
    print(f"\n✅ Proceso completado.")
    print(f"\n⚠️  Nota: ChromaDB no permite borrar tenants directamente mediante la API REST.")
    print(f"   Los tenants pueden quedar vacíos pero seguir existiendo.")
    print(f"   Si necesitas eliminarlos completamente, puede ser necesario reiniciar ChromaDB")
    print(f"   o acceder directamente a la base de datos subyacente.")
    
    # Verificar que default_tenant sigue existiendo
    try:
        check_url = f"{base_url}/tenants/default_tenant"
        response = requests.get(check_url, headers=headers, timeout=5)
        if response.status_code == 200:
            print("\n✅ default_tenant sigue existiendo correctamente")
        else:
            print(f"\n⚠️  default_tenant no se encontró (código: {response.status_code})")
    except Exception as e:
        print(f"\n⚠️  Error al verificar default_tenant: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
