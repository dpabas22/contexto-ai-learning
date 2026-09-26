"""
Contexto: AI-Powered Language Learning for Expats in Querétaro
Final Production Version: Simple AI, Language Detection, General Info, Conveyance
"""

import streamlit as st
import json
import os
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
# SIMPLE AI VOCAB RESPONSE (1 CALL, LANGUAGE DETECTION)
# ============================================================================

def get_ai_vocab_response(query, lesson=""):
    """
    AI vocab: Simple working mode
    Returns translation + Spanish explanation (2-3 sentences max)
    Format: Not JSON, just clean text
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {
                "query": query,
                "is_spanish": False,
                "translation": "API key not configured",
                "explanation": "",
                "error": True
            }
        
        client = Groq(api_key=api_key)
        
        # Detect language
        spanish_indicators = ['á', 'é', 'í', 'ó', 'ú', 'ñ', 'ü']
        is_spanish = any(char in query.lower() for char in spanish_indicators)
        
        # CALL 1: Get translation
        if is_spanish:
            trans_prompt = f"Translate '{query}' to English. Only one word. No explanation."
        else:
            trans_prompt = f"Translate '{query}' to Spanish. Only one word. No explanation."
        
        trans_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": trans_prompt}],
            max_tokens=20,
            temperature=0.1
        )
        
        translation = trans_response.choices[0].message.content.strip()
        
        # CALL 2: Get Spanish explanation
        if is_spanish:
            exp_prompt = f"Explain '{query}' in Spanish. 2-3 sentences only. Simple, clear."
        else:
            exp_prompt = f"Explain '{query}' in Spanish. 2-3 sentences only. Simple, clear."
        
        exp_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": exp_prompt}],
            max_tokens=100,
            temperature=0.3
        )
        
        explanation = exp_response.choices[0].message.content.strip()
        
        return {
            "query": query,
            "is_spanish": is_spanish,
            "translation": translation,
            "explanation": explanation,
            "error": False
        }
    
    except Exception as e:
        return {
            "query": query,
            "is_spanish": False,
            "translation": "",
            "explanation": f"Could not generate: {str(e)[:50]}",
            "error": True
        }

# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_vocab_entry(item):
    """Display internal vocab entry"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown(f"**{item['spanish']}**")
    
    with col2:
        st.write(f"{item['english']} • {item.get('context', '')}")
    
    with st.expander(f"Details - {item['spanish']}"):
        if st.button(f"🔊 {item['spanish']}", key=f"audio_{item.get('id', item['spanish'])}"):
            audio = create_audio(item['spanish'], lang='es')
            if audio:
                st.audio(audio, format='audio/mp3')
        
        st.write(f"📣 **Pronunciation:** {item.get('pronunciation', 'N/A')}")
        st.write(f"💬 **Example:** {item.get('example_spanish', 'N/A')}")
        
        if st.button("▶️ Hear example", key=f"audio_ex_{item.get('id', item['spanish'])}"):
            audio = create_audio(item.get('example_spanish', ''), lang='es')
            if audio:
                st.audio(audio, format='audio/mp3')
        
        st.write(f"🔤 **English:** {item.get('example_english', 'N/A')}")
        
        if item.get('price_range_pesos'):
            st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
    
    st.divider()

def display_ai_vocab(vocab_result):
    """Display AI-generated vocab in consistent format"""
    if vocab_result["error"]:
        st.error(f"Could not generate vocab: {vocab_result['translation']}")
        return
    
    if vocab_result["is_spanish"]:
        st.markdown(f"### 🇪🇸 Spanish: **{vocab_result['query']}**")
        st.markdown(f"### 🇬🇧 English: **{vocab_result['translation']}**")
    else:
        st.markdown(f"### 🇬🇧 English: **{vocab_result['query']}**")
        st.markdown(f"### 🇪🇸 Spanish: **{vocab_result['translation']}**")
    
    if vocab_result['usage_spanish'] and vocab_result['usage_english']:
        st.write(f"📚 **Usage:**")
        st.write(f"  🇪🇸 {vocab_result['usage_spanish']}")
        st.write(f"  🇬🇧 {vocab_result['usage_english']}")

# ============================================================================
# PAGE HEADER
# ============================================================================

st.title("🌍 Contexto: Language Learning for Real Expat Needs")
st.markdown("**Learn Spanish through real conversations in Querétaro**")

st.info("""
✅ **Querétaro-Specific Content:** Market, Hospital, Paper Store, School  
✅ **Essential References:** Measurements, Time, Numbers, Money  
🚗 **Conveyance Guide:** Transportation options in Querétaro  
⚠️ **AI Vocab:** Generate meanings for unknown words (any language)  
📅 **Phase 2 Roadmap:** Restaurants, neighborhoods, shopping
""")

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "💬 Conversations", "📚 Grammar", "🏪 Market (Mercado)", "🏥 Hospital (Hospital)", 
    "📝 Paper Store (Papelería)", "🎓 School (Escuela)", "📐 Measurements (Medidas)", 
    "⏰ Time (Tiempo)", "🔢 Numbers (Números)", "💰 Money (Dinero)", "🚗 Conveyance (Transporte)"
])

# ============================================================================
# TAB 1: CONVERSATIONS
# ============================================================================

with tab1:
    st.header("💬 Real Conversations - Learn from Scenarios")
    
    selected_lesson = st.selectbox(
        "Choose a lesson:",
        ["Market", "Hospital", "Paper Store", "School"],
        key="conv_lesson"
    )
    
    if selected_lesson == "Market":
        st.subheader("🏪 Market (Mercado) Conversations")
        
        with st.expander("**Dialogue 1: Buying Fresh Fish**"):
            st.markdown("### 🇪🇸 Spanish:")
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
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Hi, do you have fresh fish today?  
**Vendor:** Yes, of course. I have snapper, bass, and trout. All very fresh.  
**Jasmine:** How much does the snapper cost?  
**Vendor:** 120 pesos per kilo. It's from this morning.  
**Jasmine:** What do you recommend?  
**Vendor:** The bass is delicious today. Perfect for ceviche.  
**Jasmine:** Okay, give me 750 grams of bass. What's the total price?  
**Vendor:** 750 grams at 130 pesos per kilo... that's 97.50 pesos.  
**Jasmine:** Is that the best price?  
**Vendor:** That's a fair price. Very fresh, see? It shines.  
**Jasmine:** Okay, done. Can you clean it for me?  
**Vendor:** Of course. I'll clean off the scales and guts for you.
            """)

    elif selected_lesson == "Hospital":
        st.subheader("🏥 Hospital (Hospital) Conversations")
        
        with st.expander("**Dialogue 1: Calling for an Appointment**"):
            st.markdown("### 🇪🇸 Spanish:")
            st.markdown("""
**Jasmine:** Hola, buenos días. Necesito una cita con el doctor.  
**Receptionist:** ¿Cuál es tu problema o síntoma?  
**Jasmine:** Tengo dolor de cabeza y fiebre desde hace dos días.  
**Receptionist:** ¿Tienes seguro médico?  
**Jasmine:** Sí, tengo Monterrey New York Life.  
**Receptionist:** Perfecto. El doctor García tiene disponibilidad hoy a las 4 de la tarde, o mañana a las 10 de la mañana.  
**Jasmine:** Prefiero hoy a las 4. ¿Cuál es el costo de la consulta?  
**Receptionist:** Con tu seguro, solo pagas 300 pesos de copago.  
**Jasmine:** Dale, confirmo para hoy a las 4. ¿Necesito traer algo?  
**Receptionist:** Trae tu seguro y una identificación. Llega 10 minutos antes.
            """)
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Hi, good morning. I need an appointment with the doctor.  
**Receptionist:** What is your problem or symptom?  
**Jasmine:** I've had a headache and fever for two days.  
**Receptionist:** Do you have health insurance?  
**Jasmine:** Yes, I have Monterrey New York Life.  
**Receptionist:** Perfect. Doctor García is available today at 4 PM, or tomorrow at 10 AM.  
**Jasmine:** I prefer today at 4. What's the consultation cost?  
**Receptionist:** With your insurance, you only pay 300 pesos copay.  
**Jasmine:** Okay, I confirm for today at 4. Do I need to bring anything?  
**Receptionist:** Bring your insurance and an ID. Arrive 10 minutes early.
            """)

    elif selected_lesson == "Paper Store":
        st.subheader("📝 Paper Store (Papelería) Conversations")
        
        with st.expander("**Dialogue 1: Printing Documents**"):
            st.markdown("### 🇪🇸 Spanish:")
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
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Hi, I need to print these documents. How much does it cost?  
**Staff:** Let me see how many pages. One, two... it's 15 pages. Black and white or color?  
**Jasmine:** Black and white is fine. What's the price?  
**Staff:** Black and white is 0.50 pesos per page. That's 7.50 pesos total.  
**Jasmine:** Okay. How long does it take?  
**Staff:** Two minutes. Do you need another service? Binding? Laminating?  
**Jasmine:** Laminating, yes. One laminated page. How much does it cost?  
**Staff:** 30 pesos per laminated page, letter size.  
**Jasmine:** Perfect. Laminate this cover page. What's the total?  
**Staff:** 7.50 for printing, plus 30 for laminating. Total 37.50 pesos. Done in 5 minutes.
            """)

    else:  # School
        st.subheader("🎓 School (Escuela) Conversations")
        
        with st.expander("**Dialogue 1: School Registration**"):
            st.markdown("### 🇪🇸 Spanish:")
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
**Director:** Depende de la escuela. Puede variar entre 1,000 y 3,000 pesos. Incluye libros, materiales, y seguro escolar.
            """)
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Good morning, I'm interested in registering my son at the school.  
**Director:** Welcome. What grade?  
**Jasmine:** Third grade elementary. What's the admission process?  
**Director:** First I need documents: birth certificate, proof of residence, and vaccination card.  
**Jasmine:** Do I have to take an admission exam?  
**Director:** Yes, a simple exam in math and Spanish. Also an interview with parents.  
**Jasmine:** When can we do the exam?  
**Director:** Next week. Do you have availability Monday at 9 AM?  
**Jasmine:** Yes, perfect. What's the registration cost?  
**Director:** It depends on the school. It can range from 1,000 to 3,000 pesos. Includes books, materials, and school insurance.
            """)

# ============================================================================
# TAB 2: GRAMMAR
# ============================================================================

with tab2:
    st.header("📚 Spanish Verb Conjugations - Present Tense")
    st.info("Learn verbs used in Contexto conversations. All 6 persons shown.")
    
    grammar_data = {
        "Ser (To Be - Permanent)": {
            "yo": "soy", "tú": "eres", "él/ella/usted": "es",
            "nosotros": "somos", "vosotros": "sois", "ellos/ellas/ustedes": "son",
            "example": "Yo soy enfermera = I am a nurse"
        },
        "Estar (To Be - Location/Condition)": {
            "yo": "estoy", "tú": "estás", "él/ella/usted": "está",
            "nosotros": "estamos", "vosotros": "estáis", "ellos/ellas/ustedes": "están",
            "example": "Estoy en el mercado = I am at the market"
        },
        "Tener (To Have)": {
            "yo": "tengo", "tú": "tienes", "él/ella/usted": "tiene",
            "nosotros": "tenemos", "vosotros": "tenéis", "ellos/ellas/ustedes": "tienen",
            "example": "Tengo fiebre = I have fever"
        },
        "Hacer (To Do/Make)": {
            "yo": "hago", "tú": "haces", "él/ella/usted": "hace",
            "nosotros": "hacemos", "vosotros": "hacéis", "ellos/ellas/ustedes": "hacen",
            "example": "¿Qué haces? = What do you do?"
        },
        "Ir (To Go)": {
            "yo": "voy", "tú": "vas", "él/ella/usted": "va",
            "nosotros": "vamos", "vosotros": "vais", "ellos/ellas/ustedes": "van",
            "example": "Voy al hospital = I go to the hospital"
        },
        "Hablar (To Speak)": {
            "yo": "hablo", "tú": "hablas", "él/ella/usted": "habla",
            "nosotros": "hablamos", "vosotros": "habláis", "ellos/ellas/ustedes": "hablan",
            "example": "Hablo español = I speak Spanish"
        },
        "Comprar (To Buy)": {
            "yo": "compro", "tú": "compras", "él/ella/usted": "compra",
            "nosotros": "compramos", "vosotros": "compráis", "ellos/ellas/ustedes": "compran",
            "example": "Compro pescado fresco = I buy fresh fish"
        },
        "Necesitar (To Need)": {
            "yo": "necesito", "tú": "necesitas", "él/ella/usted": "necesita",
            "nosotros": "necesitamos", "vosotros": "necesitáis", "ellos/ellas/ustedes": "necesitan",
            "example": "Necesito un doctor = I need a doctor"
        },
        "Costar (To Cost)": {
            "yo": "cuesta", "tú": "cuesta", "él/ella/usted": "cuesta",
            "nosotros": "cuesta", "vosotros": "cuesta", "ellos/ellas/ustedes": "cuestan",
            "example": "¿Cuánto cuesta? = How much does it cost?"
        },
        "Dar (To Give)": {
            "yo": "doy", "tú": "das", "él/ella/usted": "da",
            "nosotros": "damos", "vosotros": "dais", "ellos/ellas/ustedes": "dan",
            "example": "Te doy 70 pesos = I give you 70 pesos"
        },
        "Pedir (To Ask For/Request)": {
            "yo": "pido", "tú": "pides", "él/ella/usted": "pide",
            "nosotros": "pedimos", "vosotros": "pedís", "ellos/ellas/ustedes": "piden",
            "example": "¿Cuánto me pides? = How much do you ask for?"
        },
        "Incluir (To Include)": {
            "yo": "incluyo", "tú": "incluyes", "él/ella/usted": "incluye",
            "nosotros": "incluimos", "vosotros": "incluís", "ellos/ellas/ustedes": "incluyen",
            "example": "Incluye los libros = It includes the books"
        },
        "Aceptar (To Accept)": {
            "yo": "acepto", "tú": "aceptas", "él/ella/usted": "acepta",
            "nosotros": "aceptamos", "vosotros": "aceptáis", "ellos/ellas/ustedes": "aceptan",
            "example": "¿Qué métodos de pago aceptan? = What payment methods do you accept?"
        },
        "Llamar (To Call)": {
            "yo": "llamo", "tú": "llamas", "él/ella/usted": "llama",
            "nosotros": "llamamos", "vosotros": "llamáis", "ellos/ellas/ustedes": "llaman",
            "example": "Te llamamos en una hora = We'll call you in an hour"
        },
        "Empezar (To Start)": {
            "yo": "empiezo", "tú": "empiezas", "él/ella/usted": "empieza",
            "nosotros": "empezamos", "vosotros": "empezáis", "ellos/ellas/ustedes": "empiezan",
            "example": "¿Cuándo empieza? = When does it start?"
        }
    }
    
    selected_verb = st.selectbox("Choose a verb:", list(grammar_data.keys()))
    
    if selected_verb:
        verb_info = grammar_data[selected_verb]
        st.subheader(selected_verb)
        
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

# ============================================================================
# TAB 3: MARKET
# ============================================================================

with tab3:
    st.subheader("🏪 Market (Mercado)")
    
    st.info("""
**About Markets in Querétaro:**  
Markets are vibrant community spaces where locals shop for fresh produce, seafood, spices, and household items. Haggling is normal practice, especially on bulk purchases.

**Typical Market Items:**
- Pescado (fish): Pargo, robalo, trucha
- Frutas (fruits): Manzanas, plátanos, naranjas
- Verduras (vegetables): Lechuga, tomate, cebolla
- Especias (spices): Cúrcuma, comino, chiles

**Market Etiquette:**
- Compare prices at different stalls
- Negotiate on bulk quantities (3+ kilos)
- Cash (efectivo) is preferred
- "¿Es el mejor precio?" (Is that your best price?) is acceptable
    """)
    
    st.markdown("### 🏪 Quick Reference - Top Market Words")
    quick_ref_market = [
        {"spanish": "pescado", "english": "fish"},
        {"spanish": "fresco", "english": "fresh"},
        {"spanish": "precio", "english": "price"},
        {"spanish": "descuento", "english": "discount"},
        {"spanish": "kilo", "english": "kilogram"},
    ]
    
    cols = st.columns(5)
    for i, item in enumerate(quick_ref_market):
        with cols[i % 5]:
            st.write(f"**{item['spanish']}**")
            st.write(f"*{item['english']}*")
            if st.button("🔊", key=f"qref_market_{i}"):
                audio = create_audio(item['spanish'])
                if audio:
                    st.audio(audio, format='audio/mp3')
    
    st.divider()
    market_query = st.text_input("Search market vocabulary:", placeholder="e.g., fish, fresh, price", key="market_search")
    
    if market_query:
        results = search_vocabulary(market_query, lesson="market")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            for item in results:
                display_vocab_entry(item)
        else:
            st.warning("❌ No results found in vocabulary.")
            if has_groq:
                if st.button(f"💡 Generate AI vocab for '{market_query}'", key="market_ai_gen"):
                    with st.spinner("Generating..."):
                        ai_vocab = get_ai_vocab_response(market_query, lesson="market")
                        display_ai_vocab(ai_vocab)

# ============================================================================
# TAB 4: HOSPITAL
# ============================================================================

with tab4:
    st.subheader("🏥 Hospital (Hospital)")
    
    st.info("""
**About Healthcare in Querétaro:**  
Querétaro has both private hospitals/clinics and public healthcare facilities. Private healthcare often has English-speaking staff and shorter wait times.

**Healthcare Types:**
- Clínicas Privadas (Private clinics): English available, appointment-based
- IMSS (Public health): For Mexican residents/affiliates
- Farmacias con Consultorio (Pharmacy clinics): Walk-in service

**Common Insurance Providers:**
- Monterrey New York Life
- AXA
- Seguros Inbursa

**What to Bring:**
- Identification (ID/passport)
- Health insurance card
- List of medications you're taking
    """)
    
    st.markdown("### 🏥 Quick Reference - Top Hospital Words")
    quick_ref_hospital = [
        {"spanish": "doctor", "english": "doctor"},
        {"spanish": "fiebre", "english": "fever"},
        {"spanish": "dolor", "english": "pain"},
        {"spanish": "cita", "english": "appointment"},
        {"spanish": "seguro", "english": "insurance"},
    ]
    
    cols = st.columns(5)
    for i, item in enumerate(quick_ref_hospital):
        with cols[i % 5]:
            st.write(f"**{item['spanish']}**")
            st.write(f"*{item['english']}*")
            if st.button("🔊", key=f"qref_hosp_{i}"):
                audio = create_audio(item['spanish'])
                if audio:
                    st.audio(audio, format='audio/mp3')
    
    st.divider()
    hospital_query = st.text_input("Search hospital vocabulary:", placeholder="e.g., fever, doctor, insurance", key="hospital_search")
    
    if hospital_query:
        results = search_vocabulary(hospital_query, lesson="hospital")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            for item in results:
                display_vocab_entry(item)
        else:
            st.warning("❌ No results found in vocabulary.")
            if has_groq:
                if st.button(f"💡 Generate AI vocab for '{hospital_query}'", key="hospital_ai_gen"):
                    with st.spinner("Generating..."):
                        ai_vocab = get_ai_vocab_response(hospital_query, lesson="hospital")
                        display_ai_vocab(ai_vocab)

# ============================================================================
# TAB 5: PAPER STORE
# ============================================================================

with tab5:
    st.subheader("📝 Paper Store (Papelería)")
    
    st.info("""
**About Papelerías in Querétaro:**  
Papelerías are common stationery stores offering various services beyond office supplies. Useful for students, workers, and expats needing to get documents prepared.

**Common Services:**
- Impresión (Printing): B&W and color
- Fotocopias (Photocopying)
- Encuadernación (Binding): Coil, spiral, glue
- Laminado (Laminating)
- Plastificado (Plastic covering)
- Escaneo (Scanning)

**Typical Uses:**
- Print resumes/CVs
- Copy important documents
- Bind projects/reports
- Laminate IDs/documents

**Payment:**
- Usually cash (efectivo)
- Some accept cards
    """)
    
    st.markdown("### 📝 Quick Reference - Top Paper Store Words")
    quick_ref_pap = [
        {"spanish": "imprimir", "english": "to print"},
        {"spanish": "copias", "english": "copies"},
        {"spanish": "laminado", "english": "laminating"},
        {"spanish": "blanco y negro", "english": "black and white"},
        {"spanish": "a color", "english": "color"},
    ]
    
    cols = st.columns(5)
    for i, item in enumerate(quick_ref_pap):
        with cols[i % 5]:
            st.write(f"**{item['spanish']}**")
            st.write(f"*{item['english']}*")
            if st.button("🔊", key=f"qref_pap_{i}"):
                audio = create_audio(item['spanish'])
                if audio:
                    st.audio(audio, format='audio/mp3')
    
    st.divider()
    pap_query = st.text_input("Search paper store vocabulary:", placeholder="e.g., print, laminate", key="pap_search")
    
    if pap_query:
        results = search_vocabulary(pap_query, lesson="papeleria")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            for item in results:
                display_vocab_entry(item)
        else:
            st.warning("❌ No results found in vocabulary.")
            if has_groq:
                if st.button(f"💡 Generate AI vocab for '{pap_query}'", key="pap_ai_gen"):
                    with st.spinner("Generating..."):
                        ai_vocab = get_ai_vocab_response(pap_query, lesson="papeleria")
                        display_ai_vocab(ai_vocab)

# ============================================================================
# TAB 6: SCHOOL
# ============================================================================

with tab6:
    st.subheader("🎓 School (Escuela)")
    
    st.info("""
**About Schools in Querétaro:**  
Querétaro has various educational options including public, private, bilingual, and international schools. Many expat families enroll their children in bilingual schools.

**School Types:**
- Escuela Pública (Public school): Free, Spanish-language
- Colegio Privado (Private school): Fee-based, various languages
- Escuela Bilingüe (Bilingual school): Spanish + English
- International School: Curriculum for expat families

**Typical Enrollment Process:**
- Contact school for availability
- Submit documents: Acta de nacimiento (birth certificate), Comprobante de domicilio (proof of residence), Cartilla de vacunas (vaccination card)
- Admission exam: Math and Spanish
- Parent interview
- Enroll and pay registration fees

**School Year:**
- Typically starts: September
- Ends: June
- Enrollment/registration: July-August

**Payment:**
- Monthly tuition: Varies by school
- Registration fee: One-time, at enrollment
- Additional: Uniforms, supplies, extracurricular activities
    """)
    
    st.markdown("### 🎓 Quick Reference - Top School Words")
    quick_ref_school = [
        {"spanish": "escuela", "english": "school"},
        {"spanish": "uniforme", "english": "uniform"},
        {"spanish": "maestro", "english": "teacher"},
        {"spanish": "estudiante", "english": "student"},
        {"spanish": "grado", "english": "grade"},
    ]
    
    cols = st.columns(5)
    for i, item in enumerate(quick_ref_school):
        with cols[i % 5]:
            st.write(f"**{item['spanish']}**")
            st.write(f"*{item['english']}*")
            if st.button("🔊", key=f"qref_sch_{i}"):
                audio = create_audio(item['spanish'])
                if audio:
                    st.audio(audio, format='audio/mp3')
    
    st.divider()
    school_query = st.text_input("Search school vocabulary:", placeholder="e.g., uniform, teacher, grade", key="school_search")
    
    if school_query:
        results = search_vocabulary(school_query, lesson="school")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            for item in results:
                display_vocab_entry(item)
        else:
            st.warning("❌ No results found in vocabulary.")
            if has_groq:
                if st.button(f"💡 Generate AI vocab for '{school_query}'", key="school_ai_gen"):
                    with st.spinner("Generating..."):
                        ai_vocab = get_ai_vocab_response(school_query, lesson="school")
                        display_ai_vocab(ai_vocab)

# ============================================================================
# TAB 7: MEASUREMENTS
# ============================================================================

with tab7:
    st.header("📐 Measurements (Medidas)")
    st.info("Common measurements used in markets, cooking, and shopping.")
    
    measurements_data = {
        "Fractions & Multiples": [
            {"spanish": "medio", "english": "half", "pronunciation": "MEH-dee-oh", "example_spanish": "Medio kilogramo de café", "example_english": "Half a kilogram of coffee"},
            {"spanish": "cuarto", "english": "quarter", "pronunciation": "KWAR-toh", "example_spanish": "Un cuarto de hora", "example_english": "A quarter of an hour"},
            {"spanish": "doble", "english": "double", "pronunciation": "DOH-bleh", "example_spanish": "Doble ración", "example_english": "Double portion"},
        ],
        "Weight": [
            {"spanish": "gramo", "english": "gram", "pronunciation": "GRAH-moh", "example_spanish": "500 gramos de queso", "example_english": "500 grams of cheese"},
            {"spanish": "kilogramo", "english": "kilogram", "pronunciation": "kee-loh-GRAH-moh", "example_spanish": "Un kilogramo de papa", "example_english": "One kilogram of potato"},
            {"spanish": "libra", "english": "pound", "pronunciation": "LEE-brah", "example_spanish": "Dos libras de pollo", "example_english": "Two pounds of chicken"},
        ],
        "Volume": [
            {"spanish": "litro", "english": "liter", "pronunciation": "LEE-troh", "example_spanish": "Un litro de leche", "example_english": "One liter of milk"},
            {"spanish": "taza", "english": "cup", "pronunciation": "TAH-sah", "example_spanish": "Una taza de café", "example_english": "One cup of coffee"},
            {"spanish": "cucharada", "english": "tablespoon", "pronunciation": "koo-chah-RAH-dah", "example_spanish": "Una cucharada de azúcar", "example_english": "One tablespoon of sugar"},
        ],
    }
    
    for category, items in measurements_data.items():
        st.subheader(category)
        for item in items:
            item['context'] = category
            item['id'] = item['spanish']
            display_vocab_entry(item)

# ============================================================================
# TAB 8: TIME
# ============================================================================

with tab8:
    st.header("⏰ Time (Tiempo)")
    st.info("Words for telling time, days, months, and time expressions.")
    
    time_data = {
        "Days": [
            {"spanish": "lunes", "english": "Monday", "pronunciation": "LOO-nes", "example_spanish": "Nos vemos el lunes", "example_english": "See you on Monday"},
            {"spanish": "martes", "english": "Tuesday", "pronunciation": "MAR-tes", "example_spanish": "Cita el martes", "example_english": "Appointment on Tuesday"},
            {"spanish": "miércoles", "english": "Wednesday", "pronunciation": "MYER-koh-les", "example_spanish": "Reunión el miércoles", "example_english": "Meeting on Wednesday"},
            {"spanish": "jueves", "english": "Thursday", "pronunciation": "HWAY-ves", "example_spanish": "Clase el jueves", "example_english": "Class on Thursday"},
            {"spanish": "viernes", "english": "Friday", "pronunciation": "vee-EHR-nes", "example_spanish": "Pago el viernes", "example_english": "Payment on Friday"},
        ],
        "Time Expressions": [
            {"spanish": "ahora", "english": "now", "pronunciation": "ah-OH-rah", "example_spanish": "¿Qué hora es ahora?", "example_english": "What time is it now?"},
            {"spanish": "hoy", "english": "today", "pronunciation": "OY", "example_spanish": "Hoy es lunes", "example_english": "Today is Monday"},
            {"spanish": "mañana", "english": "tomorrow", "pronunciation": "mah-NYAH-nah", "example_spanish": "Mañana es martes", "example_english": "Tomorrow is Tuesday"},
            {"spanish": "ayer", "english": "yesterday", "pronunciation": "ah-YEH", "example_spanish": "Ayer fue domingo", "example_english": "Yesterday was Sunday"},
        ],
    }
    
    for category, items in time_data.items():
        st.subheader(category)
        for item in items:
            item['context'] = category
            item['id'] = item['spanish']
            display_vocab_entry(item)

# ============================================================================
# TAB 9: NUMBERS
# ============================================================================

with tab9:
    st.header("🔢 Numbers (Números)")
    st.info("Spanish numbers for counting and transactions.")
    
    numbers_data = {
        "0-10": [
            {"spanish": "cero", "english": "zero", "pronunciation": "SEH-roh", "example_spanish": "Cero pesos", "example_english": "Zero pesos"},
            {"spanish": "uno", "english": "one", "pronunciation": "OO-noh", "example_spanish": "Un kilogramo", "example_english": "One kilogram"},
            {"spanish": "dos", "english": "two", "pronunciation": "dohs", "example_spanish": "Dos personas", "example_english": "Two people"},
            {"spanish": "tres", "english": "three", "pronunciation": "tres", "example_spanish": "Tres manzanas", "example_english": "Three apples"},
            {"spanish": "cuatro", "english": "four", "pronunciation": "KWAH-troh", "example_spanish": "Cuatro hijos", "example_english": "Four children"},
            {"spanish": "cinco", "english": "five", "pronunciation": "SEEN-koh", "example_spanish": "Cinco dólares", "example_english": "Five dollars"},
        ],
        "Tens": [
            {"spanish": "diez", "english": "ten", "pronunciation": "dee-es", "example_spanish": "Diez pesos", "example_english": "Ten pesos"},
            {"spanish": "veinte", "english": "twenty", "pronunciation": "VAYN-teh", "example_spanish": "Veinte años", "example_english": "Twenty years"},
            {"spanish": "treinta", "english": "thirty", "pronunciation": "TRAYN-tah", "example_spanish": "Treinta y cinco", "example_english": "Thirty-five"},
            {"spanish": "cien", "english": "one hundred", "pronunciation": "see-en", "example_spanish": "Cien pesos", "example_english": "One hundred pesos"},
            {"spanish": "mil", "english": "one thousand", "pronunciation": "meel", "example_spanish": "Mil pesos", "example_english": "One thousand pesos"},
        ],
    }
    
    for category, items in numbers_data.items():
        st.subheader(category)
        for item in items:
            item['context'] = category
            item['id'] = item['spanish']
            display_vocab_entry(item)

# ============================================================================
# TAB 10: MONEY
# ============================================================================

with tab10:
    st.header("💰 Money (Dinero)")
    st.info("Currency, payment methods, and money-related vocabulary.")
    
    money_data = {
        "Currency": [
            {"spanish": "peso", "english": "peso (Mexican currency)", "pronunciation": "PEH-soh", "example_spanish": "¿Cuántos pesos?", "example_english": "How many pesos?"},
            {"spanish": "centavo", "english": "cent (1/100 of peso)", "pronunciation": "sen-TAH-voh", "example_spanish": "50 centavos", "example_english": "50 cents"},
            {"spanish": "moneda", "english": "coin", "pronunciation": "moh-NEH-dah", "example_spanish": "Una moneda de 5 pesos", "example_english": "A 5-peso coin"},
            {"spanish": "billete", "english": "bill/note", "pronunciation": "bee-YEH-teh", "example_spanish": "Billete de 500 pesos", "example_english": "500-peso bill"},
        ],
        "Payment": [
            {"spanish": "dinero", "english": "money", "pronunciation": "dee-NEH-roh", "example_spanish": "¿Cuánto dinero?", "example_english": "How much money?"},
            {"spanish": "precio", "english": "price", "pronunciation": "PREH-see-oh", "example_spanish": "¿Cuál es el precio?", "example_english": "What's the price?"},
            {"spanish": "pago", "english": "payment", "pronunciation": "PAH-goh", "example_spanish": "Método de pago", "example_english": "Payment method"},
            {"spanish": "cambio", "english": "change", "pronunciation": "KAHM-bee-oh", "example_spanish": "¿Me das el cambio?", "example_english": "Can you give me the change?"},
            {"spanish": "efectivo", "english": "cash", "pronunciation": "eh-fehk-TEE-voh", "example_spanish": "Pago en efectivo", "example_english": "Cash payment"},
        ],
    }
    
    for category, items in money_data.items():
        st.subheader(category)
        for item in items:
            item['context'] = category
            item['id'] = item['spanish']
            display_vocab_entry(item)

# ============================================================================
# TAB 11: CONVEYANCE (TRANSPORTATION)
# ============================================================================

with tab11:
    st.header("🚗 Conveyance (Transporte)")
    st.info("Transportation options and related vocabulary for getting around Querétaro.")
    
    st.markdown("""
### **Transportation Options in Querétaro**

**🚕 Taxis (Taxis)**
- Available throughout the city
- Hail on the street or call
- Metered (taximetro)
- Fixed rates for airport/suburbs
- Negotiate price before entering (especially at night)
- Common phrases: "¿Cuánto cuesta al Centro?" (How much to downtown?)

**🚌 Buses (Autobuses)**
- Cheapest local transportation
- Run throughout the city (major neighborhoods)
- Fixed routes (rutas fijas)
- Pay upon boarding (cash only)
- Typical fare: 9-13 pesos
- Common phrases: "¿Este autobús va al Centro?" (Does this bus go downtown?)

**🛵 Uber/Didi**
- App-based ride services
- Available throughout Querétaro
- Payment through app (card)
- Typically more expensive than taxis but convenient
- Generally safer for late-night travel
- Can split rides with others

**🚴 Bike (Bicicleta)**
- Bike rentals available in city center
- Some bike lanes exist (ciclovías)
- Good for short distances
- Affordable daily rentals

**🚗 Rental Car (Rentadora de Autos)**
- Multiple rental agencies
- Mexican driving license acceptable (+ passport)
- Insurance recommended
- Gas stations (gasolineras) throughout city
- Parking (estacionamiento) available in most areas

**🚶 Walking (A Pie)**
- Downtown and many neighborhoods are walkable
- Some areas safer than others
- Use sidewalks and crossings
- Daylight walking preferred in unfamiliar areas

### **Key Vocabulary**
    """)
    
    conveyance_vocab = {
        "Transportation Types": [
            {"spanish": "autobús", "english": "bus", "pronunciation": "ow-toh-BOOS", "example_spanish": "Tomo el autobús al trabajo", "example_english": "I take the bus to work"},
            {"spanish": "taxi", "english": "taxi", "pronunciation": "TAHK-see", "example_spanish": "Un taxi al aeropuerto", "example_english": "A taxi to the airport"},
            {"spanish": "bicicleta", "english": "bicycle", "pronunciation": "bee-see-KLEH-tah", "example_spanish": "Voy en bicicleta", "example_english": "I go by bicycle"},
            {"spanish": "coche", "english": "car", "pronunciation": "KOH-cheh", "example_spanish": "Mi coche está aquí", "example_english": "My car is here"},
            {"spanish": "metro", "english": "subway (not in Querétaro but useful)", "pronunciation": "MEH-troh", "example_spanish": "El metro es rápido", "example_english": "The subway is fast"},
        ],
        "Actions & Phrases": [
            {"spanish": "ir a pie", "english": "to walk/go on foot", "pronunciation": "eer ah pee-eh", "example_spanish": "Voy a pie al mercado", "example_english": "I walk to the market"},
            {"spanish": "parar un taxi", "english": "to hail a taxi", "pronunciation": "pah-RAHR", "example_spanish": "Paro un taxi en la calle", "example_english": "I hail a taxi on the street"},
            {"spanish": "¿Cuánto cuesta?", "english": "How much does it cost?", "pronunciation": "KWAHN-toh KWEHS-tah", "example_spanish": "¿Cuánto cuesta al Centro?", "example_english": "How much does it cost to downtown?"},
            {"spanish": "estacionamiento", "english": "parking", "pronunciation": "es-tah-see-oh-nah-mee-EHN-toh", "example_spanish": "¿Dónde hay estacionamiento?", "example_english": "Where is parking?"},
            {"spanish": "gasolinera", "english": "gas station", "pronunciation": "gah-soh-lee-NEH-rah", "example_spanish": "Necesito ir a la gasolinera", "example_english": "I need to go to the gas station"},
        ],
    }
    
    for category, items in conveyance_vocab.items():
        st.subheader(category)
        for item in items:
            item['context'] = category
            item['id'] = item['spanish']
            display_vocab_entry(item)

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
✨ 11 tabs | 📚 15 verbs | 🇪🇸🇬🇧 Bilingual | 🤖 Smart AI vocab (language detection)  
📐 Essential references | 🚗 Conveyance guide | ℹ️ General local context  
Built with ❤️ for Querétaro expats | November 2026
""")
