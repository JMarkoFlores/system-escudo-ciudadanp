# CHECKLIST DE DESPLIEGUE — IntelExtorsión a Producción

## Información de la VM
- **IP:** 142.93.240.223
- **Usuario:** root
- **Password:** TatoS69uwu
- **Dominio:** intelextorsion.duckdns.org
- **SSH:** `ssh root@142.93.240.223`

---

## FASE 0: Preparación Local (en tu PC)

### 0.1 Obtener API Keys (GRATIS)
- [ ] **GroqCloud:** https://console.groq.com → Crear cuenta → Generar API Key
- [ ] **Pali Wallet:** Crear wallet nueva → Exportar private key (para `PRIVATE_KEY`)

### 0.2 Preparar el proyecto
```bash
# Ejecutar script de limpieza
python deploy/prepare_project.py
```

### 0.3 Subir a la VM
```bash
# Opción A: SCP (desde PowerShell o Git Bash)
scp -r system-escudo-ciudadanp root@142.93.240.223:/root/

# Opción B: Si SCP no funciona, comprimir primero
tar -czf system-escudo-ciudadanp.tar.gz --exclude='node_modules' --exclude='__pycache__' --exclude='.git' --exclude='artifacts' --exclude='cache' system-escudo-ciudadanp/
scp system-escudo-ciudadanp.tar.gz root@142.93.240.223:/root/
```

---

## FASE 1: Configurar la VM

### 1.1 Conectarse a la VM
```bash
ssh root@142.93.240.223
Password: TatoS69uwu
```

### 1.2 Instalar Docker y dependencias
```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar dependencias
apt install -y curl wget git ufw fail2ban htop net-tools

# Instalar Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Verificar Docker
docker --version
docker compose version
```

### 1.3 Configurar Firewall
```bash
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
ufw status
```

### 1.4 Configurar Fail2ban
```bash
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
```

---

## FASE 2: Configurar DuckDNS

### 2.1 Apuntar el dominio a la IP
1. Ir a: https://www.duckdns.org
2. Login con tu cuenta
3. En "Domains", agregar:
   - **Domain:** intelextorsion
   - **IP:** 142.93.240.223
4. Click "Update IP"
5. Esperar 1-5 minutos para propagación

### 2.2 Verificar propagación
```bash
# Desde tu PC local
nslookup intelextorsion.duckdns.org
# Debe resolver a 142.93.240.223

# O desde la VM
ping intelextorsion.duckdns.org
```

---

## FASE 3: Configurar el Proyecto

### 3.1 Entrar al directorio
```bash
cd /root/system-escudo-ciudadanp
```

### 3.2 Crear archivo .env
```bash
cp deploy/.env.production .env
nano .env
```

### 3.3 Completar variables en .env
```bash
# Cambiar passwords por seguros
POSTGRES_PASSWORD=TU_PASSWORD_SEGURO_AQUI
JWT_SECRET_KEY=CLAVE_ALEATORIA_LARGA_AQUI

# Agregar API key de Groq
GROQ_API_KEY=gsk_TU_API_KEY_DE_GROQ

# Agregar private key de wallet
PRIVATE_KEY=0xTU_PRIVATE_KEY_DE_PALI

# Verificar contratos
CONTRACT_EVIDENCE_REGISTRY=0x1A9eB1a4C261AE793e21101a3E5c14003dcF4dEb
CONTRACT_CASE_MANAGER=0x3576cb05B2c4094e8f97639892D235044d7476a1
CONTRACT_DID_REGISTRY=0x8481c85e54f50C676f0fc37f90848030c3B12bB9
CONTRACT_TOKEN=0x622AA147eD0238840ceb215941D5E8CD997896F0
```

### 3.4 Generar hash para Traefik Dashboard (opcional)
```bash
# Si quieres acceso al dashboard de Traefik
apt install -y apache2-utils
htpasswd -nb admin TU_PASSWORD_AQUI
# Copiar el output y pegarlo en TRAEFIK_DASHBOARD_AUTH
```

---

## FASE 4: Desplegar

### 4.1 Construir y levantar
```bash
# Desplegar con docker-compose de producción
docker compose -f deploy/docker-compose.prod.yml up -d --build

# Verificar que todos los contenedores estén corriendo
docker compose -f deploy/docker-compose.prod.yml ps
```

### 4.2 Verificar logs
```bash
# Ver logs del agent-api
docker compose -f deploy/docker-compose.prod.yml logs -f agent-api

# Ver logs del web3-backend
docker compose -f deploy/docker-compose.prod.yml logs -f web3-backend

# Ver logs de Traefik
docker compose -f deploy/docker-compose.prod.yml logs -f traefik
```

### 4.3 Verificar health checks
```bash
# Agent API
curl -k https://intelextorsion.duckdns.org/api/health

# Web3 Backend
curl -k https://intelextorsion.duckdns.org/web3api/health

# Frontend ciudadano
curl -k https://intelextorsion.duckdns.org/

# Frontend policial
curl -k https://intelextorsion.duckdns.org/policial/
```

---

## FASE 5: Probar la App

### 5.1 Frontend Ciudadano
- [ ] Abrir: https://intelextorsion.duckdns.org
- [ ] Navegar por el landing page
- [ ] Ir a "Portal Ciudadano"
- [ ] Conectar wallet (Pali Wallet)
- [ ] Crear denuncia de prueba
- [ ] Verificar código de tracking

### 5.2 Frontend Policial
- [ ] Abrir: https://intelextorsion.duckdns.org/policial/
- [ ] Login: admin / (tu password)
- [ ] Ver dashboard con métricas
- [ ] Ver lista de denuncias
- [ ] Verificar que la denuncia de prueba aparece

### 5.3 Agentes IA
- [ ] Crear denuncia con texto detallado
- [ ] Verificar que los agentes procesan (logs)
- [ ] Verificar que se genera tracking code
- [ ] Verificar que se sella en blockchain (si hay fondos)

### 5.4 Blockchain
- [ ] Verificar conexión a zkSYS Tanenbaum
- [ ] Verificar que los contratos están configurados
- [ ] Probar sellado de evidencia (si hay fondos en wallet)

---

## FASE 6: Monitoreo y Mantenimiento

### 6.1 Comandos útiles
```bash
# Ver estado de contenedores
docker compose -f deploy/docker-compose.prod.yml ps

# Reiniciar un servicio
docker compose -f deploy/docker-compose.prod.yml restart agent-api

# Ver logs en tiempo real
docker compose -f deploy/docker-compose.prod.yml logs -f

# Detener todo
docker compose -f deploy/docker-compose.prod.yml down

# Limpiar imágenes Docker
docker system prune -f
```

### 6.2 Backup de PostgreSQL
```bash
# Crear backup
docker compose -f deploy/docker-compose.prod.yml exec postgres pg_dump -U agent_user intel_extorsion > backup_$(date +%Y%m%d).sql

# Restaurar backup
cat backup_YYYYMMDD.sql | docker compose -f deploy/docker-compose.prod.yml exec -T postgres psql -U agent_user intel_extorsion
```

### 6.3 Actualizar el proyecto
```bash
# En tu PC local
python deploy/prepare_project.py
scp -r system-escudo-ciudadanp root@142.93.240.223:/root/

# En la VM
cd /root/system-escudo-ciudadanp
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

---

## URLs de Acceso

| Servicio | URL |
|----------|-----|
| Portal Ciudadano | https://intelextorsion.duckdns.org |
| Dashboard Policial | https://intelextorsion.duckdns.org/policial/ |
| Agent API | https://intelextorsion.duckdns.org/api/health |
| Web3 API | https://intelextorsion.duckdns.org/web3api/health |
| Traefik Dashboard | https://traefik.intelextorsion.duckdns.org |

---

## Credenciales por Defecto (CAMBIAR)

| Usuario | Password | Rol |
|---------|----------|-----|
| admin | (configurar en .env) | Administrador |
| supervisor | (configurar en .env) | Supervisor |
| analista | (configurar en .env) | Analista |

---

## Solución de Problemas

### Los contenedores no inician
```bash
docker compose -f deploy/docker-compose.prod.yml logs
# Buscar errores en los logs
```

### No se puede conectar a la base de datos
```bash
docker compose -f deploy/docker-compose.prod.yml exec postgres psql -U agent_user intel_extorsion
```

### SSL no funciona
```bash
# Verificar que DuckDNS resuelve
nslookup intelextorsion.duckdns.org

# Verificar logs de Traefik
docker compose -f deploy/docker-compose.prod.yml logs traefik
```

### Frontend no carga
```bash
# Verificar que el contenedor está corriendo
docker compose -f deploy/docker-compose.prod.yml ps frontend-citizen

# Verificar logs
docker compose -f deploy/docker-compose.prod.yml logs frontend-citizen
```
