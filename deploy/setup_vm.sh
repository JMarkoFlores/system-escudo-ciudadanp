#!/bin/bash
# ============================================================
# IntelExtorsión - Script de Instalación en VM
# Ejecutar como root en la VM
# ============================================================

set -e

echo "=========================================="
echo "  IntelExtorsión - Instalación en VM"
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Actualizar sistema
echo -e "\n${YELLOW}[1/6] Actualizando sistema...${NC}"
apt update && apt upgrade -y

# 2. Instalar dependencias
echo -e "\n${YELLOW}[2/6] Instalando dependencias...${NC}"
apt install -y \
    curl \
    wget \
    git \
    ufw \
    fail2ban \
    htop \
    net-tools

# 3. Instalar Docker
echo -e "\n${YELLOW}[3/6] Instalando Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}Docker ya está instalado${NC}"
else
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}Docker instalado correctamente${NC}"
fi

# 4. Instalar Docker Compose plugin
echo -e "\n${YELLOW}[4/6] Verificando Docker Compose...${NC}"
if docker compose version &> /dev/null; then
    echo -e "${GREEN}Docker Compose ya está disponible${NC}"
else
    echo -e "${RED}Docker Compose no encontrado. Instalar manualmente.${NC}"
    exit 1
fi

# 5. Configurar firewall
echo -e "\n${YELLOW}[5/6] Configurando firewall...${NC}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (Traefik)
ufw allow 443/tcp   # HTTPS (Traefik)
ufw --force enable
echo -e "${GREEN}Firewall configurado${NC}"

# 6. Configurar Fail2ban
echo -e "\n${YELLOW}[6/6] Configurando Fail2ban...${NC}"
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF
systemctl enable fail2ban
systemctl restart fail2ban

echo -e "\n${GREEN}=========================================="
echo -e "  Instalación completada"
echo -e "=========================================="
echo -e ""
echo -e "Siguientes pasos:"
echo -e "  1. Subir el proyecto: scp -r system-escudo-ciudadanp root@IP:/root/"
echo -e "  2. Entrar al directorio: cd /root/system-escudo-ciudadanp"
echo -e "  3. Configurar .env: cp deploy/.env.production .env && nano .env"
echo -e "  4. Desplegar: docker compose -f deploy/docker-compose.prod.yml up -d"
echo -e ""
echo -e "Puertos abiertos:"
echo -e "  - 22 (SSH)"
echo -e "  - 80 (HTTP → HTTPS)"
echo -e "  - 443 (HTTPS)"
echo -e ""
echo -e "Dominio: intelextorsion.duckdns.org"
