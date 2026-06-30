#!/bin/bash
# ============================================================
# IntelExtorsión - Despliegue Rápido en VM
# Copiar y ejecutar en la VM
# ============================================================

set -e

echo "=========================================="
echo "  IntelExtorsión - Despliegue Rápido"
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Actualizar sistema
echo -e "\n${YELLOW}[1/7] Actualizando sistema...${NC}"
apt update && apt upgrade -y

# 2. Instalar dependencias
echo -e "\n${YELLOW}[2/7] Instalando dependencias...${NC}"
apt install -y curl wget git ufw fail2ban htop net-tools

# 3. Instalar Docker
echo -e "\n${YELLOW}[3/7] Instalando Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}Docker ya está instalado${NC}"
else
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}Docker instalado correctamente${NC}"
fi

# 4. Configurar firewall
echo -e "\n${YELLOW}[4/7] Configurando firewall...${NC}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo -e "${GREEN}Firewall configurado${NC}"

# 5. Configurar Fail2ban
echo -e "\n${YELLOW}[5/7] Configurando Fail2ban...${NC}"
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

# 6. Verificar .env
echo -e "\n${YELLOW}[6/7] Verificando configuración...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}Error: Archivo .env no encontrado${NC}"
    echo "Copiar deploy/.env.production a .env y configurar"
    exit 1
fi

# Verificar PRIVATE_KEY
if grep -q "AGREGAR_TU_PRIVATE_KEY_AQUI" .env; then
    echo -e "${RED}Error: PRIVATE_KEY no configurada en .env${NC}"
    echo "Editar .env y agregar tu private key de Pali Wallet"
    exit 1
fi

echo -e "${GREEN}Configuración verificada${NC}"

# 7. Desplegar
echo -e "\n${YELLOW}[7/7] Desplegando aplicación...${NC}"
docker compose -f deploy/docker-compose.prod.yml up -d --build

echo -e "\n${GREEN}=========================================="
echo -e "  Despliegue completado"
echo -e "=========================================="
echo -e ""
echo -e "Urls de acceso:"
echo -e "  Portal Ciudadano:   https://intelextorsion.duckdns.org"
echo -e "  Dashboard Policial: https://intelextorsion.duckdns.org/policial/"
echo -e ""
echo -e "Credenciales:"
echo -e "  Usuario: admin"
echo -e "  Password: Admin2026!"
echo -e ""
echo -e "Verificar estado:"
echo -e "  docker compose -f deploy/docker-compose.prod.yml ps"
echo -e ""
echo -e "Ver logs:"
echo -e "  docker compose -f deploy/docker-compose.prod.yml logs -f"
echo -e ""
