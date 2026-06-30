"""
IntelExtorsión - Despliegue Automatizado en VM
Ejecutar desde tu PC local para desplegar en la VM
"""
import paramiko
import sys
import os
import time
from pathlib import Path

# Configuración de la VM
VM_IP = "142.93.240.223"
VM_USER = "root"
VM_PASS = "TatoS69uwu"
VM_PORT = 22

# Rutas
PROJECT_DIR = Path(__file__).parent.parent
PROJECT_NAME = "system-escudo-ciudadanp"

class VMDeployer:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connected = False
    
    def connect(self):
        """Conectar a la VM via SSH."""
        print(f"\n{'='*60}")
        print(f"  Conectando a {VM_USER}@{VM_IP}:{VM_PORT}")
        print(f"{'='*60}")
        
        try:
            self.client.connect(
                hostname=VM_IP,
                port=VM_PORT,
                username=VM_USER,
                password=VM_PASS,
                timeout=30
            )
            self.connected = True
            print("  [OK] Conexion establecida")
            
            # Verificar conexion
            stdin, stdout, stderr = self.client.exec_command("uname -a")
            print(f"  Sistema: {stdout.read().decode().strip()}")
            return True
        except Exception as e:
            print(f"  [ERROR] No se pudo conectar: {e}")
            return False
    
    def execute(self, command, description="", show_output=True):
        """Ejecutar un comando en la VM."""
        if show_output:
            print(f"\n  > {description}")
            print(f"  $ {command[:80]}{'...' if len(command) > 80 else ''}")
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=300)
            
            # Leer salida
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if show_output and output:
                for line in output.split('\n')[:10]:  # Max 10 lineas
                    if line.strip():
                        print(f"    {line}")
            
            if error and "WARNING" not in error and "deprecated" not in error.lower():
                if show_output:
                    # Filtrar warnings normales
                    error_lines = [l for l in error.split('\n') if l.strip() and 'warning' not in l.lower() and 'deprecated' not in l.lower()]
                    if error_lines:
                        print(f"    [stderr] {error_lines[0][:100]}")
            
            return output
        except Exception as e:
            print(f"  [ERROR] {e}")
            return ""
    
    def upload_file(self, local_path, remote_path):
        """Subir un archivo a la VM."""
        print(f"  Subiendo: {local_path.name} -> {remote_path}")
        try:
            sftp = self.client.open_sftp()
            sftp.put(str(local_path), remote_path)
            sftp.close()
            print(f"  [OK] Archivo subido")
            return True
        except Exception as e:
            print(f"  [ERROR] {e}")
            return False
    
    def upload_directory(self, local_dir, remote_dir):
        """Subir un directorio completo a la VM."""
        print(f"\n{'='*60}")
        print(f"  Subiendo proyecto a la VM")
        print(f"{'='*60}")
        
        try:
            sftp = self.client.open_sftp()
            
            files_uploaded = 0
            for root, dirs, files in os.walk(local_dir):
                # Ignorar carpetas pesadas
                dirs[:] = [d for d in dirs if d not in [
                    'node_modules', '__pycache__', '.git', 
                    'artifacts', 'cache', '.next', '.pytest_cache',
                    'venv', '.venv', 'env'
                ]]
                
                for file in files:
                    # Ignorar archivos pesados
                    if any(ext in file for ext in ['.pyc', '.pyo', '.log']):
                        continue
                    
                    local_file = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file, local_dir)
                    remote_file = os.path.join(remote_dir, relative_path).replace('\\', '/')
                    
                    # Crear directorio remoto si no existe
                    remote_dir_path = os.path.dirname(remote_file)
                    self.execute(f"mkdir -p {remote_dir_path}", show_output=False)
                    
                    # Subir archivo
                    try:
                        sftp.put(local_file, remote_file)
                        files_uploaded += 1
                        if files_uploaded % 10 == 0:
                            print(f"    ... {files_uploaded} archivos subidos")
                    except Exception as e:
                        pass
            
            sftp.close()
            print(f"  [OK] {files_uploaded} archivos subidos")
            return True
        except Exception as e:
            print(f"  [ERROR] {e}")
            return False
    
    def install_docker(self):
        """Instalar Docker en la VM."""
        print(f"\n{'='*60}")
        print(f"  Instalando Docker")
        print(f"{'='*60}")
        
        # Verificar si ya esta instalado
        output = self.execute("docker --version", show_output=False)
        if "Docker version" in output:
            print("  [OK] Docker ya esta instalado")
            return True
        
        # Instalar
        commands = [
            ("Actualizando sistema", "apt update && apt upgrade -y"),
            ("Instalando dependencias", "apt install -y curl wget git ufw fail2ban htop net-tools"),
            ("Instalando Docker", "curl -fsSL https://get.docker.com | sh"),
            ("Habilitando Docker", "systemctl enable docker && systemctl start docker"),
        ]
        
        for desc, cmd in commands:
            self.execute(cmd, desc)
        
        # Verificar
        output = self.execute("docker --version", show_output=False)
        if "Docker version" in output:
            print("\n  [OK] Docker instalado correctamente")
            return True
        else:
            print("\n  [ERROR] Docker no se pudo instalar")
            return False
    
    def configure_firewall(self):
        """Configurar el firewall."""
        print(f"\n{'='*60}")
        print(f"  Configurando Firewall")
        print(f"{'='*60}")
        
        commands = [
            ("Reseteando firewall", "ufw --force reset"),
            ("Configurando politica por defecto", "ufw default deny incoming && ufw default allow outgoing"),
            ("Abriendo SSH", "ufw allow 22/tcp"),
            ("Abriendo HTTP", "ufw allow 80/tcp"),
            ("Abriendo HTTPS", "ufw allow 443/tcp"),
            ("Habilitando firewall", "ufw --force enable"),
        ]
        
        for desc, cmd in commands:
            self.execute(cmd, desc)
        
        # Verificar
        output = self.execute("ufw status", show_output=False)
        print(f"\n  Estado del firewall:")
        for line in output.split('\n')[:15]:
            if line.strip():
                print(f"    {line}")
        
        return True
    
    def configure_env(self):
        """Configurar el archivo .env."""
        print(f"\n{'='*60}")
        print(f"  Configurando .env")
        print(f"{'='*60}")
        
        env_content = """# ============================================================
# IntelExtorsión - Variables de Entorno PRODUCCIÓN
# ============================================================

# GROQCLOUD
GROQ_API_KEY=${GROQ_API_KEY}
GROQ_MODEL=llama-3.3-70b-versatile

# BASE DE DATOS
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=IntelExtorsion2026!
POSTGRES_DB=intel_extorsion

# SEGURIDAD
JWT_SECRET_KEY=xK9mP2vL8nQ4wR7tY5uI1oA6sD3fG0hJ2kL5zM8bN4cV7x

# Usuarios seed
SEED_ADMIN_PASSWORD=Admin2026!
SEED_SUPERVISOR_PASSWORD=Supervisor2026!
SEED_ANALISTA_PASSWORD=Analista2026!

# BLOCKCHAIN
WEB3_PROVIDER_URL=https://rpc-zk.tanenbaum.io
CHAIN_ID=57057
EXPLORER_URL=https://explorer-zk.tanenbaum.io
NETWORK_NAME=zkSYS Tanenbaum Testnet

# Wallet institucional (AGREGAR TU PRIVATE KEY DE PALI)
PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000001

# Contratos desplegados en zkSYS Tanenbaum
CONTRACT_EVIDENCE_REGISTRY=0x1A9eB1a4C261AE793e21101a3E5c14003dcF4dEb
CONTRACT_CASE_MANAGER=0x3576cb05B2c4094e8f97639892D235044d7476a1
CONTRACT_DID_REGISTRY=0x8481c85e54f50C676f0fc37f90848030c3B12bB9
CONTRACT_TOKEN=0x622AA147eD0238840ceb215941D5E8CD997896F0

# DOMINIO
DOMAIN=intelextorsion.duckdns.org
ACME_EMAIL=admin@intelextorsion.duckdns.org

# CANALES (opcional)
TELEGRAM_BOT_TOKEN=
DISCORD_BOT_TOKEN=
WHATSAPP_API_TOKEN=

# IPFS (opcional)
IPFS_JWT=
"""
        
        # Crear archivo .env en la VM
        command = f"cat > /root/{PROJECT_NAME}/.env << 'ENVEOF'\n{env_content}\nENVEOF"
        self.execute(command, "Creando archivo .env")
        
        # Verificar
        output = self.execute(f"cat /root/{PROJECT_NAME}/.env | head -5", show_output=False)
        if "GROQ_API_KEY" in output:
            print("  [OK] Archivo .env configurado")
            return True
        else:
            print("  [ERROR] No se pudo crear .env")
            return False
    
    def deploy(self):
        """Desplegar la aplicacion con Docker Compose."""
        print(f"\n{'='*60}")
        print(f"  Desplegando aplicacion")
        print(f"{'='*60}")
        
        commands = [
            ("Navegando al directorio", f"cd /root/{PROJECT_NAME}"),
            ("Construyendo contenedores", f"cd /root/{PROJECT_NAME} && docker compose -f deploy/docker-compose.prod.yml up -d --build"),
        ]
        
        for desc, cmd in commands:
            self.execute(cmd, desc, show_output=True)
        
        # Esperar un momento
        print("\n  Esperando 30 segundos para que los contenedores inicien...")
        time.sleep(30)
        
        # Verificar estado
        output = self.execute(
            f"cd /root/{PROJECT_NAME} && docker compose -f deploy/docker-compose.prod.yml ps",
            "Verificando estado de contenedores"
        )
        
        return True
    
    def verify(self):
        """Verificar que la aplicacion este funcionando."""
        print(f"\n{'='*60}")
        print(f"  Verificando despliegue")
        print(f"{'='*60}")
        
        # Verificar contenedores
        output = self.execute(
            f"cd /root/{PROJECT_NAME} && docker compose -f deploy/docker-compose.prod.yml ps",
            "Contenedores",
            show_output=False
        )
        print(f"\n  Estado de contenedores:")
        for line in output.split('\n'):
            if line.strip():
                print(f"    {line}")
        
        # Verificar health endpoints
        print("\n  Verificando endpoints...")
        
        endpoints = [
            ("Agent API", "http://localhost:8000/health"),
            ("Web3 Backend", "http://localhost:8001/health"),
        ]
        
        for name, url in endpoints:
            output = self.execute(f"curl -s {url} | head -c 100", show_output=False)
            if "ok" in output.lower():
                print(f"    [OK] {name}: {url}")
            else:
                print(f"    [WARN] {name}: {url}")
        
        return True
    
    def disconnect(self):
        """Desconectar de la VM."""
        if self.client:
            self.client.close()
            print("\n  Desconectado de la VM")
    
    def run(self):
        """Ejecutar el despliegue completo."""
        print("\n" + "="*60)
        print("  INTELEXTORSION - DESPLIEGUE EN VM")
        print("="*60)
        print(f"  VM: {VM_USER}@{VM_IP}")
        print(f"  Proyecto: {PROJECT_NAME}")
        print("="*60)
        
        try:
            # 1. Conectar
            if not self.connect():
                return False
            
            # 2. Instalar Docker
            if not self.install_docker():
                return False
            
            # 3. Configurar firewall
            if not self.configure_firewall():
                return False
            
            # 4. Subir proyecto
            if not self.upload_directory(PROJECT_DIR, f"/root/{PROJECT_NAME}"):
                return False
            
            # 5. Configurar .env
            if not self.configure_env():
                return False
            
            # 6. Desplegar
            if not self.deploy():
                return False
            
            # 7. Verificar
            if not self.verify():
                return False
            
            print("\n" + "="*60)
            print("  DESPLIEGUE COMPLETADO")
            print("="*60)
            print("\n  URLs de acceso:")
            print("    Portal Ciudadano:   https://intelextorsion.duckdns.org")
            print("    Dashboard Policial: https://intelextorsion.duckdns.org/policial/")
            print("\n  Credenciales:")
            print("    Usuario: admin")
            print("    Password: Admin2026!")
            print("\n  Comandos utiles:")
            print("    Ver logs: docker compose -f deploy/docker-compose.prod.yml logs -f")
            print("    Ver estado: docker compose -f deploy/docker-compose.prod.yml ps")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n  [ERROR FATAL] {e}")
            return False
        finally:
            self.disconnect()


def main():
    deployer = VMDeployer()
    success = deployer.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
