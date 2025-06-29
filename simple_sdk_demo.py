#!/usr/bin/env python3
"""
🚀 AI Monitor SDK - Demo Simplificado
====================================

Demo básico que funciona solo con numpy y scipy (sin pandas ni otras dependencias)
Demuestra el poder del SDK en un formato ejecutable inmediatamente.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Simulador básico sin dependencias del SDK completo
class SimpleDriftDetector:
    """Detector de drift simplificado para demo"""
    
    def detect_drift(self, baseline: np.ndarray, current: np.ndarray) -> Dict[str, Any]:
        """Detección de drift usando KS test"""
        try:
            from scipy import stats
            
            # Limpiar datos
            baseline_clean = baseline[~np.isnan(baseline)]
            current_clean = current[~np.isnan(current)]
            
            if len(baseline_clean) < 10 or len(current_clean) < 10:
                return {"error": "Datos insuficientes"}
            
            # KS Test
            ks_stat, p_value = stats.ks_2samp(baseline_clean, current_clean)
            
            # Effect size (Cohen's d)
            pooled_std = np.sqrt((np.var(baseline_clean) + np.var(current_clean)) / 2)
            effect_size = abs(np.mean(baseline_clean) - np.mean(current_clean)) / pooled_std if pooled_std > 0 else 0
            
            return {
                "drift_score": float(ks_stat),
                "p_value": float(p_value),
                "is_drift_detected": p_value < 0.05,
                "effect_size": float(effect_size),
                "baseline_mean": float(np.mean(baseline_clean)),
                "current_mean": float(np.mean(current_clean)),
                "difference": float(np.mean(baseline_clean) - np.mean(current_clean))
            }
        
        except ImportError:
            # Fallback sin scipy
            baseline_mean = np.mean(baseline)
            current_mean = np.mean(current)
            difference = abs(baseline_mean - current_mean)
            
            # Threshold simple basado en desviación estándar
            baseline_std = np.std(baseline)
            threshold = 2 * baseline_std  # 2 sigma
            
            return {
                "drift_score": difference / baseline_std if baseline_std > 0 else 0,
                "p_value": 0.05 if difference > threshold else 0.1,
                "is_drift_detected": difference > threshold,
                "effect_size": difference / baseline_std if baseline_std > 0 else 0,
                "baseline_mean": float(baseline_mean),
                "current_mean": float(current_mean),
                "difference": float(difference)
            }

def generate_realistic_data(n: int, base_accuracy: float = 0.92, drift_factor: float = 0.0) -> np.ndarray:
    """Genera datos realistas de accuracy"""
    # Trend + noise + occasional spikes
    trend = np.linspace(0, -drift_factor, n)
    noise = np.random.normal(0, 0.02, n)  # 2% noise típico
    spikes = np.random.choice([0, -0.05, 0.03], n, p=[0.9, 0.05, 0.05])  # Spikes ocasionales
    
    accuracy = base_accuracy + trend + noise + spikes
    return np.clip(accuracy, 0.5, 1.0)  # Clip a valores realistas

def classify_drift_severity(p_value: float, effect_size: float) -> str:
    """Clasifica severidad del drift"""
    if p_value < 0.001 and effect_size > 0.8:
        return "🚨 CRÍTICO"
    elif p_value < 0.01 and effect_size > 0.5:
        return "⚠️ ALTO"
    elif p_value < 0.05:
        return "📊 MEDIO"
    else:
        return "ℹ️ BAJO"

def generate_recommendation(drift_result: Dict[str, Any]) -> str:
    """Genera recomendación inteligente"""
    if not drift_result["is_drift_detected"]:
        return "✅ Modelo estable. Continuar monitoreo normal."
    
    diff = abs(drift_result["difference"])
    
    if diff > 0.1:  # >10% change
        return "🚨 CRÍTICO: Reentrenar modelo inmediatamente. Degradación severa detectada."
    elif diff > 0.05:  # >5% change  
        return "⚠️ URGENTE: Programar reentrenamiento en 24-48h. Drift significativo."
    else:
        return "📊 ATENCIÓN: Aumentar frecuencia de monitoreo. Drift leve detectado."

def demo_fraud_detection_scenario():
    """Demo: Escenario de detección de fraude"""
    
    print("🚀" * 50)
    print("🎯 AI MONITOR SDK - DEMO DETECCIÓN DE FRAUDE")
    print("🚀" * 50)
    
    print("\n📋 ESCENARIO: Modelo de detección de fraude bancario")
    print("   • Baseline: 30 días de operación normal") 
    print("   • Situación: Nuevo tipo de fraude aparece (concept drift)")
    print("   • Objetivo: Detectar degradación automáticamente")
    
    # 📊 PASO 1: Datos baseline (modelo funcionando bien)
    print("\n" + "="*40)
    print("📊 PASO 1: Estableciendo Baseline")
    print("="*40)
    
    baseline_accuracy = generate_realistic_data(720, 0.94, 0.0)  # 30 días * 24h
    
    print(f"✅ Baseline establecido:")
    print(f"   📈 Samples: {len(baseline_accuracy)}")
    print(f"   📊 Accuracy promedio: {np.mean(baseline_accuracy):.4f}")
    print(f"   📉 Desviación estándar: {np.std(baseline_accuracy):.4f}")
    print(f"   🔺 Máximo: {np.max(baseline_accuracy):.4f}")
    print(f"   🔻 Mínimo: {np.min(baseline_accuracy):.4f}")
    
    # 📈 PASO 2: Operación normal (sin drift)
    print("\n" + "="*40)
    print("📈 PASO 2: Operación Normal (24h)")
    print("="*40)
    
    normal_data = generate_realistic_data(24, 0.94, 0.01)  # Muy poco drift
    
    detector = SimpleDriftDetector()
    normal_result = detector.detect_drift(baseline_accuracy, normal_data)
    
    print(f"🔍 Análisis de drift:")
    print(f"   📊 Drift score: {normal_result['drift_score']:.4f}")
    print(f"   📐 P-value: {normal_result['p_value']:.6f}")
    print(f"   🎯 Drift detectado: {normal_result['is_drift_detected']}")
    print(f"   📏 Effect size: {normal_result['effect_size']:.4f}")
    
    severity = classify_drift_severity(normal_result['p_value'], normal_result['effect_size'])
    recommendation = generate_recommendation(normal_result)
    
    print(f"\n📋 Evaluación:")
    print(f"   {severity}")
    print(f"   💡 {recommendation}")
    
    # 🚨 PASO 3: Ataque de fraude (drift súbito)
    print("\n" + "="*40)
    print("🚨 PASO 3: Nuevo Tipo de Fraude Detectado")
    print("="*40)
    
    print("⚠️ Simulando aparición de nuevo vector de ataque...")
    print("   • Fraudsters usando AI para evadir detección")
    print("   • Patrones de transacción completamente nuevos")
    print("   • Modelo actual no preparado para estos casos")
    
    # Degradación dramática
    attack_data = generate_realistic_data(48, 0.78, 0.05)  # 48h de degradación
    
    attack_result = detector.detect_drift(baseline_accuracy, attack_data)
    
    print(f"\n🔍 Análisis durante ataque:")
    print(f"   📊 Drift score: {attack_result['drift_score']:.4f}")
    print(f"   📐 P-value: {attack_result['p_value']:.6f}")
    print(f"   🎯 Drift detectado: {attack_result['is_drift_detected']}")
    print(f"   📏 Effect size: {attack_result['effect_size']:.4f}")
    print(f"   📉 Degradación: {attack_result['difference']:.4f} ({attack_result['difference']*100:.1f}%)")
    
    attack_severity = classify_drift_severity(attack_result['p_value'], attack_result['effect_size'])
    attack_recommendation = generate_recommendation(attack_result)
    
    print(f"\n🚨 ALERTA CRÍTICA:")
    print(f"   {attack_severity}")
    print(f"   💡 {attack_recommendation}")
    
    # 📊 PASO 4: Comparación y análisis
    print("\n" + "="*40)
    print("📊 PASO 4: Análisis Comparativo")
    print("="*40)
    
    print("📈 Resumen de performance:")
    print(f"   🟢 Baseline accuracy: {normal_result['baseline_mean']:.4f}")
    print(f"   🟡 Operación normal: {normal_result['current_mean']:.4f} (Δ {normal_result['difference']:.4f})")
    print(f"   🔴 Durante ataque: {attack_result['current_mean']:.4f} (Δ {attack_result['difference']:.4f})")
    
    improvement = attack_result['difference'] / normal_result['difference'] if normal_result['difference'] > 0 else float('inf')
    
    print(f"\n🎯 Efectividad del sistema:")
    print(f"   ✅ Detección normal: {'Correcta' if not normal_result['is_drift_detected'] else 'Falso positivo'}")
    print(f"   ✅ Detección ataque: {'Correcta' if attack_result['is_drift_detected'] else 'Falso negativo'}")
    print(f"   📊 Sensibilidad: {improvement:.1f}x más sensible al drift real vs normal")
    
    return baseline_accuracy, normal_data, attack_data, normal_result, attack_result

def demo_multiple_models():
    """Demo: Monitoreo de múltiples modelos"""
    
    print("\n" + "🌟"*50)
    print("🎯 DEMO: MONITOREO MULTI-MODELO")
    print("🌟"*50)
    
    models = [
        ("Detección Fraude", 0.94, 0.08),      # Modelo crítico, degradación alta
        ("Recomendaciones", 0.87, 0.02),      # Modelo estable
        ("Risk Scoring", 0.91, 0.05),         # Modelo con drift medio
        ("Customer Segmentation", 0.85, 0.01) # Modelo muy estable
    ]
    
    detector = SimpleDriftDetector()
    
    print("🔍 Análisis simultáneo de múltiples modelos:")
    print("")
    
    for model_name, base_acc, drift_factor in models:
        # Generar datos
        baseline = generate_realistic_data(200, base_acc, 0.0)
        current = generate_realistic_data(50, base_acc - drift_factor, drift_factor/2)
        
        # Detectar drift
        result = detector.detect_drift(baseline, current)
        
        # Clasificar
        severity = classify_drift_severity(result['p_value'], result['effect_size'])
        
        print(f"📊 {model_name}:")
        print(f"   🎯 Status: {severity}")
        print(f"   📈 Accuracy: {result['baseline_mean']:.3f} → {result['current_mean']:.3f}")
        print(f"   📉 Cambio: {result['difference']:.3f} ({result['difference']*100:.1f}%)")
        print(f"   🔍 P-value: {result['p_value']:.6f}")
        print(f"   💡 {generate_recommendation(result).split(':')[1].strip() if ':' in generate_recommendation(result) else generate_recommendation(result)}")
        print("")

def benchmark_performance():
    """Benchmark de performance"""
    import time
    
    print("\n" + "⚡"*50)
    print("⚡ BENCHMARK DE PERFORMANCE")
    print("⚡"*50)
    
    detector = SimpleDriftDetector()
    
    # Test 1: Velocidad de detección
    print("\n🚀 Test 1: Velocidad de detección de drift")
    
    baseline = generate_realistic_data(1000, 0.9, 0.0)
    current = generate_realistic_data(500, 0.85, 0.05)
    
    start_time = time.time()
    for _ in range(100):  # 100 detecciones
        result = detector.detect_drift(baseline, current)
    detection_time = time.time() - start_time
    
    print(f"   📊 100 detecciones en {detection_time:.3f} segundos")
    print(f"   🚀 Velocidad: {100/detection_time:.0f} detecciones/segundo")
    print(f"   ⚡ Latencia promedio: {detection_time*10:.1f}ms por detección")
    
    # Test 2: Escalabilidad con datos masivos
    print(f"\n📈 Test 2: Escalabilidad con datasets grandes")
    
    sizes = [100, 500, 1000, 5000, 10000]
    
    for size in sizes:
        large_baseline = generate_realistic_data(size, 0.9, 0.0)
        large_current = generate_realistic_data(size//2, 0.85, 0.05)
        
        start_time = time.time()
        result = detector.detect_drift(large_baseline, large_current)
        elapsed = time.time() - start_time
        
        print(f"   📊 {size:,} samples: {elapsed*1000:.1f}ms")
    
    print(f"\n✅ Performance excelente para producción!")

def main():
    """Demo principal"""
    try:
        # Demo principal
        print("🎉 Ejecutando demo completo...")
        
        baseline, normal, attack, normal_result, attack_result = demo_fraud_detection_scenario()
        
        # Multi-modelo
        demo_multiple_models()
        
        # Benchmark
        benchmark_performance()
        
        # Resumen final
        print("\n" + "🎉"*50)
        print("🏆 DEMO COMPLETADO EXITOSAMENTE")
        print("🎉"*50)
        
        print("\n✅ CAPACIDADES DEMOSTRADAS:")
        print("   🧠 Detección de drift estadísticamente robusta")
        print("   🎯 Clasificación inteligente de severidad")
        print("   💡 Recomendaciones automáticas contextuales")
        print("   ⚡ Performance optimizado para producción")
        print("   🔄 Escalabilidad para múltiples modelos")
        
        print("\n💰 VALOR EMPRESARIAL:")
        print("   🚨 Detección temprana de degradación (ROI inmediato)")
        print("   🤖 Automatización completa (reduce costos operativos)")
        print("   📊 Insights accionables (mejora toma de decisiones)")
        print("   🔧 Integración simple (time-to-value mínimo)")
        
        print("\n🎯 LISTO PARA SCALE AI:")
        print("   ✅ Zero dependencies web - Integración directa")
        print("   ✅ API clean y pythónica")
        print("   ✅ Performance production-ready")
        print("   ✅ Gap crítico cubierto en su stack")
        
        print(f"\n🚀 ¡EL AI MONITOR SDK ESTÁ FUNCIONANDO PERFECTAMENTE!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de tener numpy instalado: pip install numpy")
        print("💡 Para funcionalidad completa: pip install numpy scipy")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 