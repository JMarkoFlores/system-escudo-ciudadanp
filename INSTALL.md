# IntelExtorsión - Guía de Instalación

## Requisitos Previos

- **Docker Desktop** (Windows/Mac/Linux) o Docker Engine + Docker Compose
- **Node.js** 20+ (solo si se ejecuta frontend fuera de Docker)
- **Python** 3.11+ (solo si se ejecuta backend fuera de Docker)
- **Git**

## Instalación Rápida (Docker - Recomendado)

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-org/IntelExtorsion.git
cd IntelExtorsion
```

### Paso 2: Configurar variables de entorno

```bash
# Windows (PowerShell)
cp .env.example .env
notepad .env

# Linux / macOS
cp .env.example .env
nano .env
```

**Mínimo requerido en .env:**
```
GROQ_API_KEY=gsk_tu-clave-aqui
POSTGRES_PASSWORD=tu-password-segura
PRIVATE_KEY=0x...                    # Wallet institucional para Web3

# Red oficial: zkSYS Tanenbaum Testnet (Chain ID 57057)
WEB3_PROVIDER_URL=https://rpc-zk.tanenbaum.io
CHAIN_ID=57057
EXPLORER_URL=https://explorer-zk.tanenbaum.io
NETWORK_NAME=zkSYS Tanenbaum Testnet

# Contratos desplegados en Tanenbaum
CONTRACT_EVIDENCE_REGISTRY=0x1A9eB1a4C261AE793e21101a3E5c14003dcF4dEb
CONTRACT_CASE_MANAGER=0x3576cb05B2c4094e8f97639892D235044d7476a1
CONTRACT_DID_REGISTRY=0x8481c85e54f50C676f0fc37f90848030c3B12bB9
CONTRACT_TOKEN=0x622AA147eD0238840ceb215941D5E8CD997896F0

# JWT para dashboard policial
JWT_SECRET_KEY=tu-clave-secreta-jwt-minimo-32-caracteres

# Notificaciones push de alertas (opcional)
ALERT_EMAIL_SMTP_HOST=
ALERT_EMAIL_SMTP_USER=
ALERT_EMAIL_SMTP_PASSWORD=
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=
ALERT_WEBHOOK_URL=
```

### Paso 3: Levantar infraestructura base

```bash
docker compose up -d postgres qdrant redis
```

Verificar que estén saludables:
```bash
docker compose ps
```

### Paso 4: Construir y levantar servicios de aplicación

```bash
docker compose build --no-cache
docker compose up -d
```

Servicios levantados:
- Frontend Ciudadano: http://localhost:3000
- Frontend Policial: http://localhost:3001
- DApp Web3: http://localhost:3002
- Agent System API: http://localhost:8000/docs
- Web3 Backend API: http://localhost:8001/docs

### Paso 5: Verificar instalación

```bash
# Agent System
curl http://localhost:8000/health

# Web3 Backend
curl http://localhost:8001/health

# Frontend
open http://localhost:3000
```

---

## Instalación Manual (Desarrollo)

### 1. Infraestructura Base

```bash
# PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=agent_user \
  -e POSTGRES_PASSWORD=agent_pass \
  -e POSTGRES_DB=intel_extorsion \
  -p 5432:5432 \
  postgres:16-alpine

# Qdrant
docker run -d --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant:v1.9.1

# Redis
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 2. Agent System (Python)

```bash
cd intel_extorsion_agent_system
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt

# Crear .env con GROQ_API_KEY
python scripts/setup.py init

# Iniciar servidor
python main.py
```

Accesible en: http://localhost:8000/docs

### 3. Web3 Backend (Python)

```bash
cd intel_extorsion_web3_system/backend
python -m venv venv
venv\Scripts\activate  # o source venv/bin/activate
pip install -r requirements.txt

# Configurar CONTRACT_* en .env
python main.py
```

Accesible en: http://localhost:8001/docs

### 4. Frontends (Next.js)

```bash
# Frontend Ciudadano
cd intel_extorsion_frontend_citizen
npm install
npm run dev
# Accesible en: http://localhost:3000

# Frontend Policial
cd intel_extorsion_frontend_police
npm install
npm run dev
# Accesible en: http://localhost:3001

# DApp Web3
cd intel_extorsion_web3_system/dapp
npm install
npm run dev
# Accesible en: http://localhost:5173 (o el puerto que indique Vite)
```

### 5. Smart Contracts (Hardhat)

```bash
cd intel_extorsion_web3_system
npm install
npx hardhat compile
npx hardhat test

# Deploy local (para desarrollo)
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
```

---

## Verificación Post-Instalación

```bash
# 1. Todos los contenedores corriendo
docker compose ps

# 2. Agent System responde
curl http://localhost:8000/health

# 3. Web3 Backend responde
curl http://localhost:8001/health

# 4. Frontend Ciudadano accesible
# Abrir navegador en http://localhost:3000

# 5. Frontend Policial accesible
# Abrir navegador en http://localhost:3001

# 6. DApp Web3 accesible
# Abrir navegador en http://localhost:3002

# 5. Login policial funciona
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!" | jq -r '.access_token')
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/denuncias?limit=1

# 6. PostgreSQL tiene tablas
docker exec -it intel_extorsion_postgres psql -U agent_user -d intel_extorsion -c "\dt"

# 7. Qdrant accesible
curl http://localhost:6333

# 8. Tests de integración (opcional)
docker compose -f docker-compose.yml -f docker-compose.test.yml up test-runner --build --abort-on-container-exit
```

---

## Solución de Problemas

### Puerto 5432 ocupado
```bash
# Windows
netstat -ano | findstr 5432
# Linux/macOS
lsof -i :5432
```

### Error "GROQ_API_KEY not set"
Asegúrate de crear el archivo `.env` en la raíz del proyecto y definir `GROQ_API_KEY`.

### Error de permisos en Docker (Linux)
```bash
sudo usermod -aG docker $USER
# Cerrar sesión y volver a iniciar
```

---

*Guía generada por el equipo de Arquitectura de IntelExtorsión.*
