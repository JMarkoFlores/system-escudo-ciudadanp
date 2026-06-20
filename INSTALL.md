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
docker compose build agent-api web3-backend frontend
docker compose up -d
```

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

### 4. Frontend (Next.js)

```bash
cd intel_extorsion_frontend
npm install
npm run dev
```

Accesible en: http://localhost:3000

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

# 4. Frontend accesible
# Abrir navegador en http://localhost:3000

# 5. PostgreSQL tiene tablas
docker exec -it intel_extorsion_postgres psql -U agent_user -d intel_extorsion -c "\dt"

# 6. Qdrant accesible
curl http://localhost:6333
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
