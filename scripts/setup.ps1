# AI Ops Suite - Setup Script for Windows
Write-Host "🚀 Configurando AI Ops Suite..." -ForegroundColor Green

# Verificar que Python 3.9+ esté instalado
try {
    $pythonVersion = python --version 2>&1
    $versionNumber = [regex]::Match($pythonVersion, '(\d+\.\d+)').Groups[1].Value
    
    if ([version]$versionNumber -lt [version]"3.9") {
        Write-Host "❌ Error: Se requiere Python 3.9 o superior. Versión actual: $versionNumber" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Python $versionNumber encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python no encontrado. Por favor instala Python 3.9+" -ForegroundColor Red
    exit 1
}

# Crear entorno virtual si no existe
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
}

# Activar entorno virtual
Write-Host "🔌 Activando entorno virtual..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Actualizar pip
Write-Host "📥 Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Instalar dependencias
Write-Host "📚 Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt

# Instalar el paquete en modo desarrollo
Write-Host "🔧 Instalando AI Ops Suite en modo desarrollo..." -ForegroundColor Yellow
pip install -e .

# Crear archivo .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host "⚙️ Creando archivo de configuración..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
    Write-Host "📝 Por favor, edita el archivo .env con tus configuraciones" -ForegroundColor Cyan
}

# Crear directorios necesarios
Write-Host "📁 Creando estructura de directorios..." -ForegroundColor Yellow
$directories = @(
    "core\database", "core\auth", "core\utils", "core\config",
    "ai_monitor\api", "ai_monitor\collectors", "ai_monitor\alerting", "ai_monitor\dashboard", "ai_monitor\models",
    "cost_optimizer\scheduler", "cost_optimizer\predictor", "cost_optimizer\optimizer", "cost_optimizer\api",
    "compliance_guardian\regulations", "compliance_guardian\auditing", "compliance_guardian\reporting", "compliance_guardian\api",
    "tests\unit", "tests\integration", "tests\e2e",
    "docs\api", "docs\deployment", "docs\user_guide",
    "config\grafana\dashboards", "config\grafana\datasources",
    "frontend\src", "frontend\public",
    "scripts"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# Crear archivos __init__.py
Write-Host "🐍 Creando archivos __init__.py..." -ForegroundColor Yellow
$initFiles = @(
    "core\__init__.py", "core\database\__init__.py", "core\auth\__init__.py", "core\utils\__init__.py", "core\config\__init__.py",
    "ai_monitor\__init__.py", "ai_monitor\api\__init__.py", "ai_monitor\collectors\__init__.py", "ai_monitor\alerting\__init__.py", "ai_monitor\dashboard\__init__.py", "ai_monitor\models\__init__.py",
    "cost_optimizer\__init__.py", "cost_optimizer\scheduler\__init__.py", "cost_optimizer\predictor\__init__.py", "cost_optimizer\optimizer\__init__.py", "cost_optimizer\api\__init__.py",
    "compliance_guardian\__init__.py", "compliance_guardian\regulations\__init__.py", "compliance_guardian\auditing\__init__.py", "compliance_guardian\reporting\__init__.py", "compliance_guardian\api\__init__.py"
)

foreach ($file in $initFiles) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

# Verificar Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker encontrado" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Docker no está instalado. Instálalo para usar el stack completo de desarrollo" -ForegroundColor Yellow
}

# Verificar Docker Compose
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose encontrado" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Docker Compose no está instalado. Instálalo para usar el stack completo de desarrollo" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 ¡Setup completado!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Edita el archivo .env con tus configuraciones" -ForegroundColor White
Write-Host "2. Ejecuta: docker-compose up -d (para servicios de base de datos)" -ForegroundColor White
Write-Host "3. Ejecuta: python -m core.main (para iniciar la API)" -ForegroundColor White
Write-Host ""
Write-Host "URLs útiles:" -ForegroundColor Cyan
Write-Host "- API: http://localhost:8000" -ForegroundColor White
Write-Host "- API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "- Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host "- Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "" 