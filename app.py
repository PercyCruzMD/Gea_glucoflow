import streamlit as st
from typing import TypedDict, List, Optional, Dict, Any # Added Any for session state flexibility

# --- Constantes ---
GLUCOSE_TARGET_LOW_1 = 75.0
GLUCOSE_TARGET_LOW_2 = 100.0
GLUCOSE_TARGET_MID_1 = 140.0
GLUCOSE_TARGET_MID_2 = 200.0
PAUSE_DURATION_MINUTES = 30
CURRENT_YEAR = 2025 # Based on current context date

# --- Estructuras de Datos ---
class InsulinCalculatorFormData(TypedDict):
    """Estructura para los datos de entrada del formulario."""
    currentGlucose: float
    previousGlucose: float
    currentInsulinFlow: float

class InsulinRecommendation(TypedDict):
    """Estructura para los datos de salida (la recomendación)."""
    actionTitle: str
    details: List[str]
    newFlowRateInfo: str
    originalFlowRateInfo: str
    calculationSummary: Optional[str]
    isCritical: bool
    colorClass: str # ('success', 'info', 'warning', 'error')
    icon: str # Emoji icon

class Deltas(TypedDict):
    """Estructura para los valores delta de ajuste."""
    delta1: float
    delta2: float

# --- Lógica de Cálculo ---
def get_deltas(current_flow: float) -> Deltas:
    """
    Calcula los valores delta (delta1, delta2) para el ajuste de insulina
    basados en el flujo actual (cc/h). Simplificado para evitar redundancia.

    Args:
        current_flow: El flujo actual de insulina en cc/h.

    Returns:
        Un diccionario con los valores de delta1 y delta2.
    """
    if current_flow < 4:
        return {"delta1": 0.5, "delta2": 1.0}
    if 4 <= current_flow < 6.5:
        return {"delta1": 1.0, "delta2": 2.0}
    if 6.5 <= current_flow < 10:
        return {"delta1": 1.5, "delta2": 3.0}
    if 10 <= current_flow < 15:
        return {"delta1": 2.0, "delta2": 4.0}
    if 15 <= current_flow < 20:
        return {"delta1": 3.0, "delta2": 6.0}
    if 20 <= current_flow < 25:
        return {"delta1": 4.0, "delta2": 8.0}
    if current_flow >= 25:
        return {"delta1": 5.0, "delta2": 10.0}
    # Fallback (should not be reached with flow >= 0)
    return {"delta1": 0.0, "delta2": 0.0}

def calculate_insulin_adjustment(data: InsulinCalculatorFormData) -> InsulinRecommendation:
    """
    Calcula la recomendación de ajuste de insulina basada en los datos proporcionados,
    siguiendo un protocolo clínico específico.

    Args:
        data: Un diccionario tipo InsulinCalculatorFormData con los datos del paciente.

    Returns:
        Un diccionario tipo InsulinRecommendation con la sugerencia de ajuste.
    """
    current_glucose = data['currentGlucose']
    previous_glucose = data['previousGlucose']
    current_insulin_flow = data['currentInsulinFlow']

    # --- Validación de Entrada Básica ---
    if not (current_glucose > 0 and previous_glucose > 0 and current_insulin_flow >= 0):
        # Código de validación... (sin cambios respecto a la versión anterior)
        return {
            "actionTitle": "ERROR EN DATOS",
            "details": ["Verifique que los valores de glucosa sean positivos (> 0) y el flujo de insulina sea no negativo (>= 0)."],
            "newFlowRateInfo": "N/A",
            "originalFlowRateInfo": "N/A",
            "calculationSummary": None,
            "isCritical": True,
            "colorClass": "error",
            "icon": "🚨"
        }

    # --- Inicialización ---
    glucose_change = current_glucose - previous_glucose
    try:
        deltas = get_deltas(current_insulin_flow)
    except Exception as e:
        # Código de manejo de error en get_deltas... (sin cambios)
         return {
            "actionTitle": "ERROR INTERNO",
            "details": [f"Error calculando los deltas: {e}", "Revise el flujo de insulina ingresado."],
            "newFlowRateInfo": "N/A",
            "originalFlowRateInfo": f"Flujo ingresado: {current_insulin_flow:.1f} cc/h",
            "calculationSummary": None,
            "isCritical": True,
            "colorClass": "error",
            "icon": "⚙️"
        }

    # Valores por defecto
    action_title = "Revisar Datos/Protocolo"
    details: List[str] = ["Los valores ingresados no generaron una recomendación estándar. Verifique los datos o consulte el protocolo clínico."]
    new_flow = current_insulin_flow # Mantener flujo por defecto
    is_critical = False
    color_class = "warning" # Default to warning if no rule matches
    icon = "❓"
    original_flow_rate_info = f"Flujo actual: {current_insulin_flow:.1f} cc/h"
    new_flow_rate_info = f"Mantener flujo: {current_insulin_flow:.1f} cc/h" # Default message
    calculation_summary = f"Cambio de glucosa: {glucose_change:+.0f} mg/dL ({previous_glucose:.0f} -> {current_glucose:.0f} mg/dL)."

    # --- Lógica Principal del Protocolo ---
    # (Esta sección es idéntica a la versión anterior con el protocolo detallado)
    # 1. Hipoglucemia (< 75)
    if current_glucose < GLUCOSE_TARGET_LOW_1:
        action_title = "¡HIPOGLUCEMIA!"
        details = [f"Glucosa actual ({current_glucose:.0f}) < {GLUCOSE_TARGET_LOW_1}. CONSIDERAR SUSPENDER.", "Administrar carbohidratos según protocolo.", "Evaluar causa."]
        new_flow = 0.0
        new_flow_rate_info = f"Nuevo flujo sugerido: {new_flow:.1f} cc/h (SUSPENDER)"
        calculation_summary += " Suspensión sugerida por hipoglucemia."
        is_critical = True; color_class = "error"; icon = "🚨"

    # 2. Rango Bajo-Normal (75-99)
    elif GLUCOSE_TARGET_LOW_1 <= current_glucose < GLUCOSE_TARGET_LOW_2:
        calculation_summary += f" Rango: {GLUCOSE_TARGET_LOW_1:.0f}-{GLUCOSE_TARGET_LOW_2:.0f}."
        if glucose_change > 0:
            action_title = "CONTINUAR SIN CAMBIOS"; details = ["Glucosa 75-99 y subiendo."]; new_flow_rate_info = f"Mantener: {current_insulin_flow:.1f}"; color_class = "success"; icon = "✅"
        elif 0 >= glucose_change > -25:
            action_title = "DISMINUIR FLUJO (1 Delta)"; flow_change_amount = -deltas["delta1"]; new_flow = max(0.0, current_insulin_flow + flow_change_amount); details = [f"Glucosa 75-99, estable o descenso < 25. Disminuir {deltas['delta1']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: -{deltas['delta1']:.1f}."; color_class = "info"; icon = "⬇️"
        elif glucose_change <= -25:
            action_title = f"PAUSAR ({PAUSE_DURATION_MINUTES} min) Y AJUSTAR (2 Deltas)"; flow_change_amount = -deltas["delta2"]; new_flow_after_pause = max(0.0, current_insulin_flow + flow_change_amount); details = [f"Glucosa 75-99, descenso >= 25.", f"Pausar {PAUSE_DURATION_MINUTES} min.", f"Reanudar y disminuir {deltas['delta2']:.1f}."]; new_flow_rate_info = f"Post-pausa: {new_flow_after_pause:.1f}"; calculation_summary += f" Pausa + \u0394: -{deltas['delta2']:.1f}."; is_critical = True; color_class = "warning"; icon = "⏸️⬇️"; new_flow = new_flow_after_pause

    # 3. Rango Objetivo (100-139)
    elif GLUCOSE_TARGET_LOW_2 <= current_glucose < GLUCOSE_TARGET_MID_1:
        calculation_summary += f" Rango: {GLUCOSE_TARGET_LOW_2:.0f}-{GLUCOSE_TARGET_MID_1:.0f}."
        if glucose_change > 25:
            action_title = "AUMENTAR FLUJO (1 Delta)"; flow_change_amount = deltas["delta1"]; new_flow = current_insulin_flow + flow_change_amount; details = [f"Glucosa 100-139, aumento > 25. Aumentar {deltas['delta1']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: +{deltas['delta1']:.1f}."; color_class = "info"; icon = "⬆️"
        elif -25 < glucose_change <= 25:
            action_title = "CONTINUAR SIN CAMBIOS"; details = ["Glucosa 100-139, cambio -25 a +25."]; new_flow_rate_info = f"Mantener: {current_insulin_flow:.1f}"; color_class = "success"; icon = "✅"
        elif -50 <= glucose_change <= -26:
            action_title = "DISMINUIR FLUJO (1 Delta)"; flow_change_amount = -deltas["delta1"]; new_flow = max(0.0, current_insulin_flow + flow_change_amount); details = [f"Glucosa 100-139, descenso 26-50. Disminuir {deltas['delta1']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: -{deltas['delta1']:.1f}."; color_class = "info"; icon = "⬇️"
        elif glucose_change < -50:
            action_title = f"PAUSAR ({PAUSE_DURATION_MINUTES} min) Y AJUSTAR (2 Deltas)"; flow_change_amount = -deltas["delta2"]; new_flow_after_pause = max(0.0, current_insulin_flow + flow_change_amount); details = [f"Glucosa 100-139, descenso > 50.", f"Pausar {PAUSE_DURATION_MINUTES} min.", f"Reanudar y disminuir {deltas['delta2']:.1f}."]; new_flow_rate_info = f"Post-pausa: {new_flow_after_pause:.1f}"; calculation_summary += f" Pausa + \u0394: -{deltas['delta2']:.1f}."; is_critical = True; color_class = "warning"; icon = "⏸️⬇️"; new_flow = new_flow_after_pause

    # 4. Rango Alto (140-199)
    elif GLUCOSE_TARGET_MID_1 <= current_glucose < GLUCOSE_TARGET_MID_2:
        calculation_summary += f" Rango: {GLUCOSE_TARGET_MID_1:.0f}-{GLUCOSE_TARGET_MID_2:.0f}."
        if glucose_change > 50:
             action_title = "AUMENTAR FLUJO (2 Deltas)"; flow_change_amount = deltas["delta2"]; new_flow = current_insulin_flow + flow_change_amount; details = [f"Glucosa 140-199, aumento > 50. Aumentar {deltas['delta2']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: +{deltas['delta2']:.1f}."; color_class = "info"; icon = "⬆️⬆️"
        elif 0 <= glucose_change <= 50:
            action_title = "AUMENTAR FLUJO (1 Delta)"; flow_change_amount = deltas["delta1"]; new_flow = current_insulin_flow + flow_change_amount; details = [f"Glucosa 140-199, aumento <= 50 o estable. Aumentar {deltas['delta1']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: +{deltas['delta1']:.1f}."; color_class = "info"; icon = "⬆️"
        elif -49 < glucose_change < 0:
            action_title = "CONTINUAR SIN CAMBIOS"; details = ["Glucosa 140-199, descenso < 50."]; new_flow_rate_info = f"Mantener: {current_insulin_flow:.1f}"; color_class = "success"; icon = "✅"
        elif -75 <= glucose_change <= -50:
            action_title = "DISMINUIR FLUJO (1 Delta)"; flow_change_amount = -deltas["delta1"]; new_flow = max(0.0, current_insulin_flow + flow_change_amount); details = [f"Glucosa 140-199, descenso 50-75. Disminuir {deltas['delta1']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: -{deltas['delta1']:.1f}."; color_class = "info"; icon = "⬇️"
        elif glucose_change < -75:
            action_title = f"PAUSAR ({PAUSE_DURATION_MINUTES} min) Y AJUSTAR (2 Deltas)"; flow_change_amount = -deltas["delta2"]; new_flow_after_pause = max(0.0, current_insulin_flow + flow_change_amount); details = [f"Glucosa 140-199, descenso > 75.", f"Pausar {PAUSE_DURATION_MINUTES} min.", f"Reanudar y disminuir {deltas['delta2']:.1f}."]; new_flow_rate_info = f"Post-pausa: {new_flow_after_pause:.1f}"; calculation_summary += f" Pausa + \u0394: -{deltas['delta2']:.1f}."; is_critical = True; color_class = "warning"; icon = "⏸️⬇️"; new_flow = new_flow_after_pause

    # 5. Rango Muy Alto (>= 200)
    elif current_glucose >= GLUCOSE_TARGET_MID_2:
        calculation_summary += f" Rango: >= {GLUCOSE_TARGET_MID_2:.0f}."
        if glucose_change > 0:
            action_title = "AUMENTAR FLUJO (2 Deltas)"; flow_change_amount = deltas["delta2"]; new_flow = current_insulin_flow + flow_change_amount; details = [f"Glucosa >= 200 y subiendo. Aumentar {deltas['delta2']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: +{deltas['delta2']:.1f}."; color_class = "info"; icon = "⬆️⬆️"
        elif -24 < glucose_change <= 0:
            action_title = "AUMENTAR FLUJO (1 Delta)"; flow_change_amount = deltas["delta1"]; new_flow = current_insulin_flow + flow_change_amount; details = [f"Glucosa >= 200, estable o descenso < 25. Aumentar {deltas['delta1']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: +{deltas['delta1']:.1f}."; color_class = "info"; icon = "⬆️"
        elif -75 <= glucose_change <= -25:
            action_title = "CONTINUAR SIN CAMBIOS"; details = ["Glucosa >= 200, descenso 25-75."]; new_flow_rate_info = f"Mantener: {current_insulin_flow:.1f}"; color_class = "success"; icon = "✅"
        elif -100 <= glucose_change < -75:
             action_title = "DISMINUIR FLUJO (1 Delta)"; flow_change_amount = -deltas["delta1"]; new_flow = max(0.0, current_insulin_flow + flow_change_amount); details = [f"Glucosa >= 200, descenso 75-100. Disminuir {deltas['delta1']:.1f}."]; new_flow_rate_info = f"Nuevo: {new_flow:.1f}"; calculation_summary += f" \u0394: -{deltas['delta1']:.1f}."; color_class = "info"; icon = "⬇️"
        elif glucose_change < -100:
            action_title = f"PAUSAR ({PAUSE_DURATION_MINUTES} min) Y AJUSTAR (2 Deltas)"; flow_change_amount = -deltas["delta2"]; new_flow_after_pause = max(0.0, current_insulin_flow + flow_change_amount); details = [f"Glucosa >= 200, descenso > 100.", f"Pausar {PAUSE_DURATION_MINUTES} min.", f"Reanudar y disminuir {deltas['delta2']:.1f}."]; new_flow_rate_info = f"Post-pausa: {new_flow_after_pause:.1f}"; calculation_summary += f" Pausa + \u0394: -{deltas['delta2']:.1f}."; is_critical = True; color_class = "warning"; icon = "⏸️⬇️"; new_flow = new_flow_after_pause

    # --- Construcción Final del Resultado ---
    recommendation: InsulinRecommendation = {
        "actionTitle": action_title, "details": details, "newFlowRateInfo": new_flow_rate_info,
        "originalFlowRateInfo": original_flow_rate_info, "calculationSummary": calculation_summary,
        "isCritical": is_critical, "colorClass": color_class, "icon": icon
    }
    return recommendation

# --- Función para Resetear Valores ---
def reset_values():
    """Resetea los valores de entrada y el resultado en session_state."""
    st.session_state.current_glucose = None
    st.session_state.previous_glucose = None
    st.session_state.current_flow = None
    # También limpiamos cualquier resultado previo almacenado
    if 'recommendation' in st.session_state:
        del st.session_state['recommendation']
    st.session_state.recommendation_calculated = False # Flag para ocultar resultados

# --- Interfaz de Usuario Streamlit (UI) ---
st.set_page_config(
    page_title="GEA GlucoFlow", page_icon="💧", layout="centered", initial_sidebar_state="auto"
)

# --- Inicialización de Session State ---
# Inicializar claves ANTES de usarlas en los widgets
if 'current_glucose' not in st.session_state:
    st.session_state.current_glucose = None
if 'previous_glucose' not in st.session_state:
    st.session_state.previous_glucose = None
if 'current_flow' not in st.session_state:
    st.session_state.current_flow = None
if 'recommendation_calculated' not in st.session_state:
    st.session_state.recommendation_calculated = False

# --- Header ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://img.icons8.com/fluency/96/diabetes.png", width=80)
with col2:
    st.title("GEA GlucoFlow")
    st.caption("Asistente para el ajuste de infusión de insulina intravenosa")

st.markdown("---")

# --- Formulario de Entrada ---
with st.form("calculator_form"):
    st.subheader("Ingrese los Datos del Paciente")


    st.number_input(
            "Glucosa Actual (mg/dL)", min_value=1.0, max_value=1500.0,
            step=1.0, format="%.0f", placeholder="Ej: 185",
            help="Glucometría más reciente.", key="current_glucose" # KEY es crucial
        )

    st.number_input(
            "Glucosa Previa (mg/dL)", min_value=1.0, max_value=1500.0,
            step=1.0, format="%.0f", placeholder="Ej: 210",
            help="Glucometría anterior a la actual.", key="previous_glucose" # KEY
        )

    st.number_input(
            "Flujo Insulina (cc/h)", min_value=0.0, max_value=100.0,
            step=0.1, format="%.1f", placeholder="Ej: 4.2",
            help="Flujo actual de la bomba de infusión.", key="current_flow" # KEY
        )

    # Botón de envío dentro del form
    submitted = st.form_submit_button("Calcular Ajuste", use_container_width=True, type="primary")

# --- Lógica de Cálculo (Se activa SOLO al hacer submit) ---
if submitted:
    if (st.session_state.current_glucose is None or
        st.session_state.previous_glucose is None or
        st.session_state.current_flow is None):
        st.error("❌ Por favor, complete todos los campos.")
        st.session_state.recommendation_calculated = False # Asegurar que no se muestren resultados
    else:
        input_data: InsulinCalculatorFormData = {
            "currentGlucose": float(st.session_state.current_glucose),
            "previousGlucose": float(st.session_state.previous_glucose),
            "currentInsulinFlow": float(st.session_state.current_flow),
        }
        try:
            st.session_state.recommendation = calculate_insulin_adjustment(input_data)
            st.session_state.recommendation_calculated = True # Marcar que se calculó
        except Exception as e:
            st.error(f"🤕 Ocurrió un error inesperado durante el cálculo: {e}")
            # st.exception(e) # Descomentar para depuración
            st.session_state.recommendation_calculated = False

# --- Botón de Reset (Fuera del formulario) ---
st.button("Limpiar Campos / Reset", on_click=reset_values, use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True) # Añadir un pequeño espacio

# --- Visualización de Resultados (depende del estado 'recommendation_calculated') ---
if st.session_state.get('recommendation_calculated', False) and 'recommendation' in st.session_state:
    recommendation = st.session_state.recommendation # Recuperar del estado

    st.markdown("---")
    st.subheader(f"Recomendación Calculada {recommendation['icon']}")

    alert_map = {"success": st.success, "info": st.info, "warning": st.warning, "error": st.error}
    alert_function = alert_map.get(recommendation["colorClass"], st.info)
    alert_function(f"**{recommendation['actionTitle']}**")

    st.markdown(f"📉 **{recommendation['originalFlowRateInfo']}**")
    st.markdown(f"📈 **{recommendation['newFlowRateInfo']}**")

    with st.expander("Ver Detalles y Cálculo", expanded=recommendation["isCritical"]):
        st.markdown("**Detalles de la acción:**")
        for detail in recommendation["details"]:
            st.markdown(f"- {detail}")
        if recommendation["calculationSummary"]:
            st.caption(f"📝 *Resumen: {recommendation['calculationSummary']}*")
        if recommendation["isCritical"] and recommendation['actionTitle'] != "¡HIPOGLUCEMIA!":
            st.warning("⚠️ **Atención:** Acción significativa. Monitoreo estricto requerido.")

# --- Disclaimer y Footer ---
st.markdown("---")
st.warning("""
**⚠️ Descargo de Responsabilidad Importante:**

* Esta herramienta es **solo para fines informativos y educativos**. NO reemplaza el juicio clínico profesional.
* Las decisiones de tratamiento deben ser tomadas por **personal médico calificado**, basándose en la evaluación completa del paciente y los protocolos de su institución.
* **No utilice esta calculadora como única fuente** para la toma de decisiones médicas críticas. Verifique siempre los cálculos y considere el contexto clínico completo.
* Los autores no se hacen responsables del uso indebido de esta herramienta ni de sus resultados.
* **Esto es una travesura de Percy Cruz**
""")
st.markdown("---")
# Usar st.query_params (API recomendada) y obtener año actual o default
footer_year = st.query_params.get("year", CURRENT_YEAR)
st.caption(f"© {footer_year} GEA GlucoFlow (Nombre Ficticio). Herramienta educativa.")