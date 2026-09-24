"""
Contexto: AI-Powered Language Learning for Expats
Complete Version with Audio, AI, and Grammar
"""

import streamlit as st
import json
import os
from pathlib import Path
from groq import Groq
from gtts import gTTS
import io

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Contexto - Spanish Learning",
    page_icon="🌍",
    layout="wide"
)

# ============================================================================
# AUDIO FUNCTION
# ============================================================================

def create_audio(text, lang='es'):
    """Create MP3 audio from Spanish text using gTTS"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        st.warning(f"Audio generation failed: {str(e)[:50]}")
        return None

# ============================================================================
# GROQ SETUP
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
has_groq = GROQ_API_KEY is not None

if has_groq:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        has_groq = False
        st.warning("⚠️ Groq API connection failed. Using vocab-only mode.")

# ============================================================================
# LOAD VOCABULARY DATA
# ============================================================================

@st.cache_resource
def load_vocabulary():
    """Load all vocabulary files once (cached for performance)"""
    vocab_files = {
        "market": "vocab_json/market_vocab.json",
        "hospital": "vocab_json/hospital_vocab.json",
        "papeleria": "vocab_json/papeleria_vocab.json",
        "school": "vocab_json/school_context_vocab.json"
    }
    
    all_vocab = {}
    for lesson_name, filename in vocab_files.items():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                all_vocab[lesson_name] = json.load(f)
        except FileNotFoundError:
            st.warning(f"⚠️ {filename} not found")
        except json.JSONDecodeError:
            st.warning(f"⚠️ {filename} has invalid JSON")
    
    return all_vocab

vocab_data = load_vocabulary()

# ============================================================================
# INPUT VALIDATION
# ============================================================================

def sanitize_input(text):
    """Prevent injection attacks"""
    if not text:
        return ""
    if len(text) > 500:
        return text[:500]
    text = text.replace("<", "").replace(">", "").replace("&", "")
    return text.strip()

# ============================================================================
# SEARCH FUNCTION
# ============================================================================

def search_vocabulary(query, lesson=None):
    """Search vocabulary with optional lesson filter"""
    query = sanitize_input(query).lower()
    
    if not query:
        return []
    
    results = []
    lessons_to_search = [lesson] if lesson else vocab_data.keys()
    
    for lesson_name in lessons_to_search:
        if lesson_name not in vocab_data:
            continue
            
        vocab_list = vocab_data[lesson_name].get('vocabulary', [])
        
        for item in vocab_list:
            spanish = item.get('spanish', '').lower()
            english = item.get('english', '').lower()
            
            if query in spanish or query in english:
                item_copy = item.copy()
                item_copy['lesson'] = lesson_name
                results.append(item_copy)
    
    return results

# ============================================================================
# AI RESPONSE FUNCTION
# ============================================================================

def get_ai_response(query, lesson="", context=""):
    """Get AI response from Groq with lesson context"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "⚠️ API key not configured."
        
        client = Groq(api_key=api_key)
        lesson_context = f"The user is learning about {lesson}. " if lesson else ""
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a Spanish language tutor helping expats learn Spanish in Querétaro. {lesson_context}{context}"
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)[:100]}"

# ============================================================================
# PAGE HEADER
# ============================================================================

st.title("🌍 Contexto: Language Learning for Real Expat Needs")
st.markdown("**Learn Spanish through real conversations in Querétaro**")

st.info("""
✅ **Querétaro-Specific Content:** Market (La Cruz), Hospital, Papelería, School  
⚠️ **Generic Responses:** Questions outside these 4 topics use general knowledge  
📅 **Phase 2 Roadmap:** Restaurants, neighborhoods, transportation, shopping
""")

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏪 Market", "💬 Conversations", "🏥 Hospital", "📝 Papelería", "🎓 School", "📚 Grammar"])

# ============================================================================
# TAB 1: MARKET
# ============================================================================

with tab1:
    st.subheader("Market (La Cruz) - Shopping, Haggling, Groceries")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        market_query = st.text_input(
            "Search market vocabulary:",
            placeholder="e.g., fish, fresh, price",
            key="market_search"
        )
    
    with col2:
        search_type = st.selectbox(
            "Search type:",
            ["All", "Seafood", "Vegetables", "Spices", "Actions"],
            key="market_type"
        )
    
    if market_query:
        results = search_vocabulary(market_query, lesson="market")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            
            for item in results:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**{item['spanish']}**")
                
                with col2:
                    st.write(f"{item['english']} • {item['context']}")
                
                with st.expander(f"Details - {item['spanish']}"):
                    if st.button(f"🔊 {item['spanish']}", key=f"audio_market_{item['id']}"):
                        audio = create_audio(item['spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    
                    if st.button("▶️ Hear example", key=f"audio_ex_market_{item['id']}"):
                        audio = create_audio(item['example_spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
        
        else:
            st.warning("❌ No results found.")
        
        # AI BUTTON OUTSIDE if/else (shows for all queries)
        if has_groq:
            if st.button(f"💡 Get AI help with '{market_query}'", key="market_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(market_query, lesson="market")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 2: CONVERSATIONS
# ============================================================================

with tab2:
    st.header("💬 Real Conversations - Learn from Scenarios")
    
    selected_lesson = st.selectbox(
        "Choose a lesson:",
        ["Market", "Hospital", "Papelería", "School"],
        key="conv_lesson"
    )
    
    if selected_lesson == "Market":
        st.subheader("🏪 Market Conversations - La Cruz Market")
        
        with st.expander("**Dialogue 1: Buying Fresh Fish**"):
            st.markdown("""
**Jasmine:** Hola, ¿tiene pescado fresco hoy?  
**Vendor:** Sí, claro. Tengo pargo, robalo, y trucha. Todos muy frescos.  
**Jasmine:** ¿Cuánto cuesta el pargo?  
**Vendor:** 120 pesos el kilo. Es de esta mañana.  
**Jasmine:** ¿Qué me recomienda?  
**Vendor:** El robalo está delicioso hoy. Perfecto para ceviche.  
**Jasmine:** Dale, dame 750 gramos de robalo. ¿Cuál es el precio total?  
**Vendor:** 750 gramos a 130 pesos el kilo... eso son 97 pesos y medio.  
**Jasmine:** ¿Es el mejor precio?  
**Vendor:** Es justo el precio. Muy fresco, ¿ves? Brilla.  
**Jasmine:** Dale, listo. ¿Me lo limpias?  
**Vendor:** Claro. Te lo dejo sin escamas y sin tripas.
            """)
            st.info("💡 **Key phrases:** Fresh fish types, pricing per kilo, negotiating, cleaning fish")
        
        with st.expander("**Dialogue 2: Haggling for Indian Spices**"):
            st.markdown("""
**Jasmine:** ¿Cuánto cuesta la cúrcuma?  
**Vendor:** 250 pesos por 250 gramos.  
**Jasmine:** Eso es muy caro. El otro vendedor me pidió 200 pesos.  
**Vendor:** ¿En serio? Muestrame dónde. Mi cúrcuma es de primera calidad.  
**Jasmine:** Bueno, quizás tienes razón. Pero quiero 500 gramos. ¿Hay descuento?  
**Vendor:** Si compras dos bolsas, te doy 10% de descuento.  
**Jasmine:** Dale, dame dos bolsas de cúrcuma y una de comino también.  
**Vendor:** Excelente. Eso son 450 pesos en total con el descuento.  
**Jasmine:** ¿Es el mejor que tienes?  
**Vendor:** El mejor de todo el mercado. Viene de la India, fresco. Huele, huele.
            """)
            st.info("💡 **Key phrases:** Spice pricing, haggling tactics, comparing vendors, bulk discounts")
        
        with st.expander("**Dialogue 3: Buying Fresh Produce**"):
            st.markdown("""
**Jasmine:** ¿Cuánto cuesta el cilantro fresco?  
**Vendor:** 15 pesos el manojo.  
**Jasmine:** ¿Tienes lechuga romana hoy?  
**Vendor:** Sí, muy fresca. Acaba de llegar esta mañana. 12 pesos la pieza.  
**Jasmine:** Dame tres lechugas y dos manojos de cilantro. ¿Y tomates?  
**Vendor:** Tengo tomates rojos y jitomates. Los jitomates están mejor ahora. 25 pesos el kilo.  
**Jasmine:** Dale, dame un kilo de jitomates y dos cebollas blancas.  
**Vendor:** Perfecto. Eso son 50 pesos de tomates, 15 de cebollas... 85 pesos en total.  
**Jasmine:** ¿Es todo fresco?  
**Vendor:** Garantizado. Sino, vuelves mañana y te cambio todo.
            """)
            st.info("💡 **Key phrases:** Vegetable types, freshness indicators, bulk quantities, pricing")
        
        with st.expander("**Dialogue 4: Comparing Prices & Making Deals**"):
            st.markdown("""
**Jasmine:** ¿Es el mejor precio en chiles secos?  
**Vendor:** En otro lugar, ¿cuánto te pidieron?  
**Jasmine:** 80 pesos el puño.  
**Vendor:** Mira, yo te doy 70 pesos, pero tienes que comprar tres puños mínimo.  
**Jasmine:** Eso son 210 pesos. ¿Incluyes bolsas?  
**Vendor:** Claro, van con bolsa.  
**Jasmine:** ¿Qué variedades tienes?  
**Vendor:** Guajillo, ancho, chipotle y pasilla.  
**Jasmine:** Dame uno de cada. ¿Algún otro producto que recomiendas?  
**Vendor:** Los epazotes de esta región son excelentes. 20 pesos un manojo.  
**Jasmine:** Dale, agrega dos manojos. ¿Cuánto es todo?  
**Vendor:** Tres puños de chiles, 70 cada uno, más dos epazotes... son 250 pesos. Te regalo el manojo de cilantro porque eres cliente nuevo.
            """)
            st.info("💡 **Key phrases:** Price comparison, bulk pricing, product varieties, customer loyalty")
    
    elif selected_lesson == "Hospital":
        st.subheader("🏥 Hospital Conversations - Medical Care")
        
        with st.expander("**Dialogue 1: Calling for an Appointment**"):
            st.markdown("""
**Jasmine:** Hola, buenos días. Necesito una cita con el doctor.  
**Receptionist:** ¿Cuál es tu problema o síntoma?  
**Jasmine:** Tengo dolor de cabeza y fiebre desde hace dos días.  
**Receptionist:** ¿Tienes seguro médico?  
**Jasmine:** Sí, tengo Seguros Monterrey New York Life.  
**Receptionist:** Perfecto. El doctor García tiene disponibilidad hoy a las 4 de la tarde, o mañana a las 10 de la mañana.  
**Jasmine:** Prefiero hoy a las 4. ¿Cuál es el costo de la consulta?  
**Receptionist:** Con tu seguro, solo pagas 300 pesos de copago.  
**Jasmine:** Dale, confirmo para hoy a las 4. ¿Necesito traer algo?  
**Receptionist:** Trae tu seguro y una identificación. Llega 10 minutos antes.
            """)
            st.info("💡 **Key phrases:** Symptoms, insurance types, copay, appointment scheduling")
        
        with st.expander("**Dialogue 2: Visiting the Doctor**"):
            st.markdown("""
**Doctor:** Buenos días, Jasmine. ¿Cuál es el problema?  
**Jasmine:** Tengo fiebre, dolor de cabeza y estoy muy cansada.  
**Doctor:** ¿Cuándo empezó?  
**Jasmine:** Hace dos días. También tengo dolor en la garganta.  
**Doctor:** Voy a revisarte. Abre la boca, por favor. Ahora tose. ¿Te duele al tragar?  
**Jasmine:** Sí, mucho. Y tengo frío, aunque tengo fiebre.  
**Doctor:** Probablemente es una infección viral. Voy a hacer un test rápido.  
**Jasmine:** ¿Qué me recomienda?  
**Doctor:** Reposo, mucha agua, y estos medicamentos. Toma paracetamol cada 6 horas.  
**Jasmine:** ¿Cuántos días debo faltar al trabajo?  
**Doctor:** Mínimo 3 días. Luego vuelves si no mejoras.
            """)
            st.info("💡 **Key phrases:** Symptoms, medical examination, diagnosis, medication instructions")
        
        with st.expander("**Dialogue 3: Pharmacy & Prescriptions**"):
            st.markdown("""
**Jasmine:** Buenas tardes. Tengo esta receta. ¿Tienen todos estos medicamentos?  
**Pharmacist:** A ver... sí, tenemos paracetamol 500mg, amoxicilina, y este jarabe.  
**Jasmine:** La marca que recomendó el doctor, si la tienen.  
**Pharmacist:** Perfecto. El total es 450 pesos. ¿Cómo prefieres pagar?  
**Jasmine:** Tarjeta de crédito, por favor.  
**Pharmacist:** Aquí están. El paracetamol cada 6 horas, la amoxicilina cada 8 horas, el jarabe cada 12 horas.  
**Jasmine:** ¿Tengo que tomar esto con comida?  
**Pharmacist:** La amoxicilina es mejor con comida. El paracetamol puede ser con o sin comida. ¿Alguna alergia?  
**Jasmine:** Soy alérgica a la penicilina.  
**Pharmacist:** Espera, esto tiene penicilina. Vamos a cambiar.
            """)
            st.info("💡 **Key phrases:** Prescriptions, medication instructions, dosages, food interactions")
        
        with st.expander("**Dialogue 4: Specialist Referral**"):
            st.markdown("""
**Jasmine:** Doctor, tengo dudas sobre mi vista. Veo borroso frecuentemente.  
**Doctor:** Debes ver a un oftalmólogo. Te doy una referencia.  
**Jasmine:** ¿Dónde puedo encontrar un oftalmólogo? ¿Mi seguro cubre esto?  
**Doctor:** Sí, tu seguro cubre. Te recomiendo a la Dra. Sánchez. Ella trabaja en Clínica Ángeles.  
**Jasmine:** ¿Cuál es el teléfono?  
**Doctor:** Aquí está. Di que vienes por referencia mía. No necesitas copago adicional.  
**Jasmine:** ¿Cuánto tiempo espero para la cita?  
**Doctor:** Normalmente una semana. Pero llama hoy y pregunta si hay cancelación.  
**Jasmine:** Gracias, doctor. ¿Necesito algún otro especialista?  
**Doctor:** No por ahora. Vuelve en un mes después de que veas al oftalmólogo.
            """)
            st.info("💡 **Key phrases:** Health concerns, specialist referrals, insurance coverage, wait times")
    
    elif selected_lesson == "Papelería":
        st.subheader("📝 Papelería Conversations - Office & Printing")
        
        with st.expander("**Dialogue 1: Printing Documents**"):
            st.markdown("""
**Jasmine:** Hola, necesito imprimir estos documentos. ¿Cuánto cuesta?  
**Staff:** A ver cuántas páginas. Uno, dos... son 15 páginas. Blanco y negro o a color?  
**Jasmine:** Blanco y negro está bien. ¿Cuál es el precio?  
**Staff:** Blanco y negro es 0.50 pesos por página. Son 7.50 pesos en total.  
**Jasmine:** Dale. ¿Cuánto tiempo tarda?  
**Staff:** Dos minutos. ¿Necesitas otro servicio? ¿Encuadernación? ¿Laminado?  
**Jasmine:** Laminado, sí. Una página laminada. ¿Cuánto cuesta?  
**Staff:** 30 pesos por página laminada, tamaño carta.  
**Jasmine:** Perfecto. Lamina esta portada. ¿Cuál es el total?  
**Staff:** 7.50 de impresión, más 30 de laminado. Total 37.50 pesos. Listo en 5 minutos.
            """)
            st.info("💡 **Key phrases:** Printing services, page costs, laminating, binding options")
        
        with st.expander("**Dialogue 2: Buying School Supplies**"):
            st.markdown("""
**Jasmine:** Buenos días. Necesito material para la escuela de mi hijo.  
**Staff:** ¿Qué año está tu hijo?  
**Jasmine:** Tercero de primaria. Necesito cuadernos, lápices, y mochilas.  
**Staff:** Vamos. Tenemos cuadernos de 100 hojas a 25 pesos, o de 200 hojas a 40 pesos.  
**Jasmine:** Dame tres de 100 hojas. ¿Lápices?  
**Staff:** Lápices HB a 1 peso cada uno, o estuches de 12 lápices a 15 pesos.  
**Jasmine:** Dame un estuche de 12. ¿Y mochilas?  
**Staff:** Mochilas de 150 a 300 pesos, depende del modelo. Estas de abajo son de buena calidad, 200 pesos.  
**Jasmine:** Esa está bien. ¿Qué más necesito?  
**Staff:** Goma, tijeras, regla, marcadores. Tengo kits escolares completos a 150 pesos.  
**Jasmine:** Perfecto. Dame un kit. ¿Cuánto es todo?  
**Staff:** 75 de cuadernos, 15 de lápices, 200 de mochila, 150 del kit. Total 440 pesos.
            """)
            st.info("💡 **Key phrases:** School supplies, paper products, writing tools, pricing")
        
        with st.expander("**Dialogue 3: Copying & Document Services**"):
            st.markdown("""
**Jasmine:** ¿Hacen copias aquí? Necesito 20 copias de este documento.  
**Staff:** Sí. ¿Blanco y negro o a color?  
**Jasmine:** Blanco y negro. ¿Cuánto cuesta?  
**Staff:** Blanco y negro es 0.50 pesos por copia. 20 copias son 10 pesos.  
**Jasmine:** ¿Puedo pedir que me encuadernen las copias juntas?  
**Staff:** Claro. Encuadernación espiral es 50 pesos. O grapas es gratis.  
**Jasmine:** Espiral está bien. ¿En cuánto tiempo?  
**Staff:** En una hora. ¿Tu nombre para el pedido?  
**Jasmine:** Jasmine. ¿Cuál es el total?  
**Staff:** 10 de copias, 50 de encuadernación. Total 60 pesos.
            """)
            st.info("💡 **Key phrases:** Copying, binding options, pricing, turnaround time")
        
        with st.expander("**Dialogue 4: Laminating & Finishing**"):
            st.markdown("""
**Jasmine:** Hola, ¿puedes laminar estos documentos? Necesito 5 copias.  
**Staff:** ¿Qué tipo de laminado? ¿Brillo o mate?  
**Jasmine:** Brillo. ¿Cuánto cuesta?  
**Staff:** Laminado es 30 pesos por página, tamaño carta.  
**Jasmine:** Dale. ¿En cuánto tiempo?  
**Staff:** Una hora. Deja tu número de teléfono para que te llamemos.  
**Jasmine:** Mi número es 442-1234-5678. Gracias.  
**Staff:** De nada. Te llamamos en una hora.
            """)
            st.info("💡 **Key phrases:** Lamination types, pricing, turnaround time, contact info")
    
    else:  # School
        st.subheader("🎓 School Conversations - Education & Administration")
        
        with st.expander("**Dialogue 1: School Registration**"):
            st.markdown("""
**Jasmine:** Buenos días, me interesa inscribir a mi hijo en la escuela.  
**Director:** Bienvenido. ¿En qué grado?  
**Jasmine:** Tercero de primaria. ¿Cuál es el proceso de admisión?  
**Director:** Primero necesito documentos: acta de nacimiento, comprobante de domicilio, cartilla de vacunas.  
**Jasmine:** ¿Tengo que hacer un examen de admisión?  
**Director:** Sí, un examen simple de matemáticas y español. También entrevista con los padres.  
**Jasmine:** ¿Cuándo podemos hacer el examen?  
**Director:** Próxima semana. ¿Tienes disponibilidad el lunes a las 9 de la mañana?  
**Jasmine:** Sí, perfecto. ¿Cuál es el costo de inscripción?  
**Director:** 1,500 pesos. Incluye libros, materiales, y seguro escolar.
            """)
            st.info("💡 **Key phrases:** Registration documents, admission process, enrollment fees")
        
        with st.expander("**Dialogue 2: Parent-Teacher Conference**"):
            st.markdown("""
**Teacher:** Buenos días, Jasmine. Gracias por venir. Quería hablar sobre el desempeño de tu hijo.  
**Jasmine:** ¿Hay algún problema?  
**Teacher:** No, no hay problema. Su académico va bien. Pero socialmente es un poco tímido.  
**Jasmine:** ¿Qué puedo hacer para ayudar?  
**Teacher:** Motívalo a participar en actividades extracurriculares. Tenemos fútbol, danza, y arte.  
**Jasmine:** ¿Cuánto cuesta?  
**Teacher:** Actividades son 150 pesos cada una al mes. Te recomiendo que practique lectura en casa.  
**Jasmine:** ¿Cuántos minutos al día?  
**Teacher:** 20-30 minutos es suficiente. Eso mejora mucho su confianza y vocabulario.  
**Jasmine:** Dale, lo voy a hacer. ¿Alguna otra cosa?  
**Teacher:** Trae firmados los comunicados. Se los envío cada viernes. Eso es importante.
            """)
            st.info("💡 **Key phrases:** Academic performance, extracurricular activities, home practice")
        
        with st.expander("**Dialogue 3: Tutoring Services**"):
            st.markdown("""
**Jasmine:** Hola, veo que ofrecen tutorías. Mi hijo necesita ayuda en matemáticas.  
**Coordinator:** ¿En qué temas específicamente?  
**Jasmine:** Tiene dificultad con multiplicación y división.  
**Coordinator:** Ofrecemos sesiones de una hora, una o dos veces por semana. 200 pesos por sesión.  
**Jasmine:** ¿Dos veces por semana?  
**Coordinator:** Sí, es lo recomendado para resultados rápidos. Generalmente ves mejora en un mes.  
**Jasmine:** ¿Cuál es el horario?  
**Coordinator:** Lunes y miércoles de 4 a 5 de la tarde, o martes y jueves. Tú eliges.  
**Jasmine:** Lunes y miércoles está bien. ¿Necesito un contrato?  
**Coordinator:** Sí, un contrato de 1 mes mínimo. Pero puedes cancelar con una semana de anticipación.  
**Jasmine:** Dale, me interesa. ¿Empieza cuándo?  
**Coordinator:** Próxima semana. ¿Tienes el teléfono para confirmar?
            """)
            st.info("💡 **Key phrases:** Tutoring subjects, session frequency, pricing, schedules")
        
        with st.expander("**Dialogue 4: Admin Payments & Registration**"):
            st.markdown("""
**Jasmine:** Hola, necesito información sobre las cuotas de inscripción.  
**Administrator:** ¿Es nuevo alumno o actual?  
**Jasmine:** Nuevo alumno. Es mi primer año en la escuela.  
**Administrator:** Para estudiantes nuevos, la cuota de inscripción es 1,500 pesos.  
**Jasmine:** ¿Qué incluye eso?  
**Administrator:** Incluye libros, material didáctico, acceso a plataforma digital, seguro escolar.  
**Jasmine:** ¿Hay cuota mensual también?  
**Administrator:** Sí. La mensualidad es 3,000 pesos. Se paga el primer día de cada mes.  
**Jasmine:** ¿Qué métodos de pago aceptan?  
**Administrator:** Efectivo, transferencia bancaria, o tarjeta de crédito.  
**Jasmine:** ¿Hay descuento si pago varios meses adelantado?  
**Administrator:** Si pagas 6 meses adelantados, te damos 5% de descuento.  
**Jasmine:** ¿Hay gastos adicionales?  
**Administrator:** Sí. Uniforme (400 pesos), libros adicionales (800 pesos), actividades (150 pesos cada una).  
**Jasmine:** ¿Puedo hacer un plan de pagos?  
**Administrator:** Claro. Si es difícil pagar todo de una vez, podemos dividir los gastos iniciales en 2-3 pagos.
            """)
            st.info("💡 **Key phrases:** Fees breakdown, payment methods, discounts, payment plans")

# ============================================================================
# TAB 3: HOSPITAL
# ============================================================================

with tab3:
    st.subheader("Hospital - Medical Appointments, Specialists, Insurance")
    
    hospital_query = st.text_input(
        "Search hospital vocabulary:",
        placeholder="e.g., fever, doctor, insurance",
        key="hospital_search"
    )
    
    if hospital_query:
        results = search_vocabulary(hospital_query, lesson="hospital")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            
            for item in results:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**{item['spanish']}**")
                
                with col2:
                    st.write(f"{item['english']} • {item['context']}")
                
                with st.expander(f"Details - {item['spanish']}"):
                    if st.button(f"🔊 {item['spanish']}", key=f"audio_hosp_{item['id']}"):
                        audio = create_audio(item['spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    
                    if st.button("▶️ Hear example", key=f"audio_ex_hosp_{item['id']}"):
                        audio = create_audio(item['example_spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"🔤 **English:** {item['example_english']}")
                
                st.divider()
        
        else:
            st.warning("❌ No results found.")
        
        # AI BUTTON OUTSIDE if/else
        if has_groq:
            if st.button(f"💡 Get AI help with '{hospital_query}'", key="hospital_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(hospital_query, lesson="hospital")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 4: PAPELERÍA
# ============================================================================

with tab4:
    st.subheader("Papelería - Stationery, Printing, Office Supplies")
    
    pap_query = st.text_input(
        "Search papelería vocabulary:",
        placeholder="e.g., print, laminate, notebook",
        key="pap_search"
    )
    
    if pap_query:
        results = search_vocabulary(pap_query, lesson="papeleria")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            
            for item in results:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**{item['spanish']}**")
                
                with col2:
                    st.write(f"{item['english']} • {item['context']}")
                
                with st.expander(f"Details - {item['spanish']}"):
                    if st.button(f"🔊 {item['spanish']}", key=f"audio_pap_{item['id']}"):
                        audio = create_audio(item['spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    
                    if st.button("▶️ Hear example", key=f"audio_ex_pap_{item['id']}"):
                        audio = create_audio(item['example_spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
        
        else:
            st.warning("❌ No results found.")
        
        # AI BUTTON OUTSIDE if/else
        if has_groq:
            if st.button(f"💡 Get AI help with '{pap_query}'", key="pap_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(pap_query, lesson="papeleria")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 5: SCHOOL
# ============================================================================

with tab5:
    st.subheader("School - Uniforms, Activities, Admin, Canteen, Rules")
    
    school_query = st.text_input(
        "Search school vocabulary:",
        placeholder="e.g., uniform, activity, fee",
        key="school_search"
    )
    
    if school_query:
        results = search_vocabulary(school_query, lesson="school")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            
            for item in results:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**{item['spanish']}**")
                
                with col2:
                    st.write(f"{item['english']} • {item['context']}")
                
                with st.expander(f"Details - {item['spanish']}"):
                    if st.button(f"🔊 {item['spanish']}", key=f"audio_sch_{item['id']}"):
                        audio = create_audio(item['spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    
                    if st.button("▶️ Hear example", key=f"audio_ex_sch_{item['id']}"):
                        audio = create_audio(item['example_spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
        
        else:
            st.warning("❌ No results found.")
        
        # AI BUTTON OUTSIDE if/else
        if has_groq:
            if st.button(f"💡 Get AI help with '{school_query}'", key="school_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(school_query, lesson="school")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 6: GRAMMAR
# ============================================================================

with tab6:
    st.header("📚 Spanish Verb Conjugations - Present Tense")
    
    st.info("Learn essential verbs for daily Querétaro conversations. All persons shown below.")
    
    grammar_data = {
        "Ser (To Be - Permanent)": {
            "yo": "soy",
            "tú": "eres",
            "él/ella/usted": "es",
            "nosotros": "somos",
            "vosotros": "sois",
            "ellos/ellas/ustedes": "son",
            "example": "Yo soy enfermera = I am a nurse"
        },
        "Estar (To Be - Location/Condition)": {
            "yo": "estoy",
            "tú": "estás",
            "él/ella/usted": "está",
            "nosotros": "estamos",
            "vosotros": "estáis",
            "ellos/ellas/ustedes": "están",
            "example": "Estoy en el mercado = I am at the market"
        },
        "Tener (To Have)": {
            "yo": "tengo",
            "tú": "tienes",
            "él/ella/usted": "tiene",
            "nosotros": "tenemos",
            "vosotros": "tenéis",
            "ellos/ellas/ustedes": "tienen",
            "example": "Tengo fiebre = I have fever"
        },
        "Hacer (To Do/Make)": {
            "yo": "hago",
            "tú": "haces",
            "él/ella/usted": "hace",
            "nosotros": "hacemos",
            "vosotros": "hacéis",
            "ellos/ellas/ustedes": "hacen",
            "example": "¿Qué haces? = What do you do?"
        },
        "Ir (To Go)": {
            "yo": "voy",
            "tú": "vas",
            "él/ella/usted": "va",
            "nosotros": "vamos",
            "vosotros": "vais",
            "ellos/ellas/ustedes": "van",
            "example": "Voy al hospital = I go to the hospital"
        },
        "Hablar (To Speak)": {
            "yo": "hablo",
            "tú": "hablas",
            "él/ella/usted": "habla",
            "nosotros": "hablamos",
            "vosotros": "habláis",
            "ellos/ellas/ustedes": "hablan",
            "example": "Hablo español = I speak Spanish"
        },
        "Comprar (To Buy)": {
            "yo": "compro",
            "tú": "compras",
            "él/ella/usted": "compra",
            "nosotros": "compramos",
            "vosotros": "compráis",
            "ellos/ellas/ustedes": "compran",
            "example": "Compro pescado fresco = I buy fresh fish"
        },
        "Necesitar (To Need)": {
            "yo": "necesito",
            "tú": "necesitas",
            "él/ella/usted": "necesita",
            "nosotros": "necesitamos",
            "vosotros": "necesitáis",
            "ellos/ellas/ustedes": "necesitan",
            "example": "Necesito un doctor = I need a doctor"
        }
    }
    
    selected_verb = st.selectbox("Choose a verb:", list(grammar_data.keys()))
    
    if selected_verb:
        verb_info = grammar_data[selected_verb]
        st.subheader(selected_verb)
        
        # Display all conjugations in 2 columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**yo** → {verb_info['yo']}")
            st.write(f"**tú** → {verb_info['tú']}")
            st.write(f"**él/ella/usted** → {verb_info['él/ella/usted']}")
        
        with col2:
            st.write(f"**nosotros** → {verb_info['nosotros']}")
            st.write(f"**vosotros** → {verb_info['vosotros']}")
            st.write(f"**ellos/ellas/ustedes** → {verb_info['ellos/ellas/ustedes']}")
        
        st.info(f"📝 **Example:** {verb_info['example']}")
        
        # Audio for verb infinitive
        if st.button(f"🔊 Hear: {selected_verb}", key=f"grammar_audio_{selected_verb}"):
            infinitive = selected_verb.split("(")[0].strip()
            audio = create_audio(infinitive, lang='es')
            if audio:
                st.audio(audio, format='audio/mp3')

# ============================================================================
# FOOTER
# ============================================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    total_vocab = sum(len(lesson.get('vocabulary', [])) for lesson in vocab_data.values())
    st.metric("Total Vocabulary", total_vocab)

with col2:
    lessons_loaded = len(vocab_data)
    st.metric("Lessons Loaded", lessons_loaded)

with col3:
    if has_groq:
        st.metric("AI Mode", "🟢 Active")
    else:
        st.metric("AI Mode", "🔴 Offline")

st.markdown("""
---
**Contexto: Language Learning for Real Expat Needs**  
Built with ❤️ for Querétaro expats | November 2026
""")
