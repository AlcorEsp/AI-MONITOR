#!/bin/bash

# AI Ops Suite - Setup Script
echo "🚀 Configurando AI Ops Suite..."

# Verificar que Python 3.9+ esté instalado
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Se requiere Python 3.9 o superior. Versión actual: $python_version"
    exit 1
fi

echo "✅ Python $python_version encontrado"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "📥 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Instalar el paquete en modo desarrollo
echo "🔧 Instalando AI Ops Suite en modo desarrollo..."
pip install -e .

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️ Creando archivo de configuración..."
    cp .env.example .env
    echo "📝 Por favor, edita el archivo .env con tus configuraciones"
fi

# Crear directorios necesarios
echo "📁 Creando estructura de directorios..."
mkdir -p core/{database,auth,utils,config}
mkdir -p ai_monitor/{api,collectors,alerting,dashboard,models}
mkdir -p cost_optimizer/{scheduler,predictor,optimizer,api}
mkdir -p compliance_guardian/{regulations,auditing,reporting,api}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docs/{api,deployment,user_guide}
mkdir -p config/{grafana/dashboards,grafana/datasources}
mkdir -p frontend/{src,public}
mkdir -p scripts

# Crear archivos __init__.py
echo "🐍 Creando archivos __init__.py..."
touch core/__init__.py
touch core/database/__init__.py
touch core/auth/__init__.py
touch core/utils/__init__.py
touch core/config/__init__.py
touch ai_monitor/__init__.py
touch ai_monitor/api/__init__.py
touch ai_monitor/collectors/__init__.py
touch ai_monitor/alerting/__init__.py
touch ai_monitor/dashboard/__init__.py
touch ai_monitor/models/__init__.py
touch cost_optimizer/__init__.py
touch cost_optimizer/scheduler/__init__.py
touch cost_optimizer/predictor/__init__.py
touch cost_optimizer/optimizer/__init__.py
touch cost_optimizer/api/__init__.py
touch compliance_guardian/__init__.py
touch compliance_guardian/regulations/__init__.py
touch compliance_guardian/auditing/__init__.py
touch compliance_guardian/reporting/__init__.py
touch compliance_guardian/api/__init__.py

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️ Docker no está instalado. Instálalo para usar el stack completo de desarrollo"
else
    echo "✅ Docker encontrado"
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️ Docker Compose no está instalado. Instálalo para usar el stack completo de desarrollo"
else
    echo "✅ Docker Compose encontrado"
fi

echo ""
echo "🎉 ¡Setup completado!"
echo ""
echo "Próximos pasos:"
echo "1. Edita el archivo .env con tus configuraciones"
echo "2. Ejecuta: docker-compose up -d (para servicios de base de datos)"
echo "3. Ejecuta: python -m core.main (para iniciar la API)"
echo ""
echo "URLs útiles:"
echo "- API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo "- Prometheus: http://localhost:9090"
echo "" 