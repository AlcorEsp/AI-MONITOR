# 🚀 AI Ops Suite - Guía de Inicio Rápido

## ⚡ Setup en 5 Minutos

### 1. **Ejecutar Setup**
```powershell
# En Windows PowerShell
.\scripts\setup.ps1
```

### 2. **Crear archivo .env**
```powershell
# El script ya lo crea, solo editarlo si necesitas
notepad .env
```

### 3. **Verificar que funciona**
```powershell
# Ejecutar la API (sin Docker por ahora)
python -m core.main
```

### 4. **Probar la API**
- Abre: http://localhost:8000
- Docs: http://localhost:8000/docs
- Prueba endpoints:
  - `/monitor/health`
  - `/optimizer/costs`
  - `/compliance/status`

---

## 🧪 Test de Funcionalidad

### AI Monitor
```bash
curl http://localhost:8000/monitor/metrics
curl http://localhost:8000/monitor/alerts
curl http://localhost:8000/monitor/drift
```

### Cost Optimizer
```bash
curl http://localhost:8000/optimizer/costs
curl http://localhost:8000/optimizer/recommendations
curl http://localhost:8000/optimizer/savings
```

### Compliance Guardian
```bash
curl http://localhost:8000/compliance/status
curl http://localhost:8000/compliance/reports
curl http://localhost:8000/compliance/audit
```

---

## 🎯 Próximo Paso: Elegir Desarrollo

### Opción A: AI Monitor Real (Recomendado)
```bash
# Crear detector de drift real
# Archivo: ai_monitor/models/drift_detector.py
```

### Opción B: Cost Optimizer
```bash
# Crear predictor de costos
# Archivo: cost_optimizer/predictor/cost_predictor.py
```

### Opción C: Frontend Dashboard
```bash
# Setup React/Next.js
npx create-next-app@latest frontend --typescript --tailwind --app
```

---

## 🐳 Con Docker (Opcional)

Si tienes Docker instalado:

```powershell
# Levantar servicios de base de datos
docker-compose up -d postgres redis

# Verificar que funcionan
docker ps
```

---

## ❗ Si algo no funciona

### Error común: Falta Python
```powershell
# Instalar Python 3.9+
# Descargar de: https://python.org
```

### Error común: Falta dependencias
```powershell
# Reinstalar dependencias
pip install -r requirements.txt
```

### Error común: Puerto ocupado
```powershell
# Cambiar puerto en core/config/settings.py
api_port: int = 8001  # En lugar de 8000
```

---

## 🎉 ¡Listo para desarrollar!

El proyecto está configurado y listo. Ahora puedes:

1. **Explorar la API** en http://localhost:8000/docs
2. **Elegir un módulo** para desarrollar
3. **Implementar funcionalidad real** (reemplazar mock data)
4. **Crear el frontend** cuando tengas la API lista

¿Por cuál módulo empezamos? 🚀 