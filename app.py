"""
Contexto: AI-Powered Language Learning for Expats in Querétaro
Production Version: Working AI mode - Translation + Spanish explanation
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
            pass
        except json.JSONDecodeError:
            pass
    
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
# AI VOCAB RESPONSE - WORKING MODE (Translation + Spanish explanation)
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
    """Display AI-generated vocab (working mode)"""
    if vocab_result["error"]:
        st.error(f"❌ {vocab_result['explanation']}")
        return
    
    # Show translation with emoji
    if vocab_result["is_spanish"]:
        st.markdown(f"### 🇪🇸 Spanish: **{vocab_result['query']}**")
        st.markdown(f"### 🇬🇧 English: **{vocab_result['translation']}**")
    else:
        st.markdown(f"### 🇬🇧 English: **{vocab_result['query']}**")
        st.markdown(f"### 🇪🇸 Spanish: **{vocab_result['translation']}**")
    
    # Show Spanish explanation
    if vocab_result['explanation']:
        st.markdown("### 📚 Explicación (Spanish):")
        st.markdown(f"> {vocab_result['explanation']}")

# ============================================================================
# PAGE HEADER
# ============================================================================

st.title("🌍 Contexto: Language Learning for Real Expat Needs")
st.markdown("**Learn Spanish through real conversations in Querétaro**")

st.info("""
✅ **Querétaro-Specific Content:** Market, Hospital, Paper Store, School  
✅ **Essential References:** Measurements, Time, Numbers, Money  
🚗 **Conveyance Guide:** Transportation options  
⚠️ **AI Vocab:** Spanish explanations for unknown words
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
**Receptionist:** Perfecto. El doctor tiene disponibilidad hoy a las 4 de la tarde.
            """)
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Hi, good morning. I need an appointment with the doctor.  
**Receptionist:** What is your problem or symptom?  
**Jasmine:** I've had a headache and fever for two days.  
**Receptionist:** Do you have health insurance?  
**Jasmine:** Yes, I have Monterrey New York Life.  
**Receptionist:** Perfect. The doctor is available today at 4 PM.
            """)

    elif selected_lesson == "Paper Store":
        st.subheader("📝 Paper Store (Papelería) Conversations")
        
        with st.expander("**Dialogue 1: Printing Documents**"):
            st.markdown("### 🇪🇸 Spanish:")
            st.markdown("""
**Jasmine:** Hola, necesito imprimir estos documentos. ¿Cuánto cuesta?  
**Staff:** Son 15 páginas. Blanco y negro es 0.50 pesos por página.  
**Jasmine:** Dale. ¿Laminado?  
**Staff:** 30 pesos por página laminada. Total 37.50 pesos.
            """)
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Hi, I need to print these documents. How much does it cost?  
**Staff:** It's 15 pages. Black and white is 0.50 pesos per page.  
**Jasmine:** Okay. Laminating?  
**Staff:** 30 pesos per laminated page. Total 37.50 pesos.
            """)

    else:  # School
        st.subheader("🎓 School (Escuela) Conversations")
        
        with st.expander("**Dialogue 1: School Registration**"):
            st.markdown("### 🇪🇸 Spanish:")
            st.markdown("""
**Jasmine:** Buenos días, me interesa inscribir a mi hijo.  
**Director:** ¿En qué grado?  
**Jasmine:** Tercero de primaria.  
**Director:** Perfecto. El costo varía entre 1,000 y 3,000 pesos.
            """)
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Good morning, I'm interested in registering my son.  
**Director:** What grade?  
**Jasmine:** Third grade elementary.  
**Director:** Perfect. The cost ranges from 1,000 to 3,000 pesos.
            """)

# ============================================================================
# TAB 2: GRAMMAR
# ============================================================================

with tab2:
    st.header("📚 Spanish Verb Conjugations - Present Tense")
    
    grammar_data = {
        "Ser (To Be)": {"yo": "soy", "tú": "eres", "él/ella/usted": "es", "nosotros": "somos", "vosotros": "sois", "ellos": "son", "example": "Yo soy enfermera"},
        "Estar (To Be)": {"yo": "estoy", "tú": "estás", "él/ella/usted": "está", "nosotros": "estamos", "vosotros": "estáis", "ellos": "están", "example": "Estoy en el mercado"},
        "Tener (To Have)": {"yo": "tengo", "tú": "tienes", "él/ella/usted": "tiene", "nosotros": "tenemos", "vosotros": "tenéis", "ellos": "tienen", "example": "Tengo fiebre"},
        "Ir (To Go)": {"yo": "voy", "tú": "vas", "él/ella/usted": "va", "nosotros": "vamos", "vosotros": "vais", "ellos": "van", "example": "Voy al hospital"},
        "Comprar (To Buy)": {"yo": "compro", "tú": "compras", "él/ella/usted": "compra", "nosotros": "compramos", "vosotros": "compráis", "ellos": "compran", "example": "Compro pescado"},
        "Necesitar (To Need)": {"yo": "necesito", "tú": "necesitas", "él/ella/usted": "necesita", "nosotros": "necesitamos", "vosotros": "necesitáis", "ellos": "necesitan", "example": "Necesito doctor"},
    }
    
    selected_verb = st.selectbox("Choose a verb:", list(grammar_data.keys()))
    
    if selected_verb:
        verb_info = grammar_data[selected_verb]
        st.subheader(selected_verb)
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**yo:** {verb_info['yo']}")
            st.write(f"**tú:** {verb_info['tú']}")
            st.write(f"**él/ella/usted:** {verb_info['él/ella/usted']}")
        with col2:
            st.write(f"**nosotros:** {verb_info['nosotros']}")
            st.write(f"**vosotros:** {verb_info['vosotros']}")
            st.write(f"**ellos:** {verb_info['ellos']}")
        st.info(f"📝 {verb_info['example']}")

# ============================================================================
# TAB 3: MARKET
# ============================================================================

with tab3:
    st.subheader("🏪 Market (Mercado)")
    
    st.info("""
Markets are vibrant community spaces. Fresh produce, seafood, spices available.  
Haggling is normal on bulk purchases. Cash preferred.
    """)
    
    market_query = st.text_input("Search market vocabulary:", placeholder="e.g., fish, fresh, prawn", key="market_search")
    
    if market_query:
        results = search_vocabulary(market_query, lesson="market")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            for item in results:
                display_vocab_entry(item)
        else:
            st.warning("❌ No results found in vocabulary.")
            if has_groq:
                if st.button(f"💡 Ask AI about '{market_query}'", key="market_ai"):
                    with st.spinner("Generating explanation..."):
                        ai_vocab = get_ai_vocab_response(market_query, lesson="market")
                        display_ai_vocab(ai_vocab)

# ============================================================================
# TAB 4: HOSPITAL
# ============================================================================

with tab4:
    st.subheader("🏥 Hospital (Hospital)")
    
    st.info("""
Healthcare options: Private clinics (English speakers), IMSS (public), Pharmacy clinics.  
Common insurance: Monterrey New York Life, AXA.
    """)
    
    hospital_query = st.text_input("Search hospital vocabulary:", placeholder="e.g., fever, doctor", key="hospital_search")
    
    if hospital_query:
        results = search_vocabulary(hospital_query, lesson="hospital")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            for item in results:
                display_vocab_entry(item)
        else:
            st.warning("❌ No results found in vocabulary.")
            if has_groq:
                if st.button(f"💡 Ask AI about '{hospital_query}'", key="hospital_ai"):
                    with st.spinner("Generating explanation..."):
                        ai_vocab = get_ai_vocab_response(hospital_query, lesson="hospital")
                        display_ai_vocab(ai_vocab)

# ============================================================================
# TAB 5: PAPER STORE
# ============================================================================

with tab5:
    st.subheader("📝 Paper Store (Papelería)")
    
    st.info("""
Services: Printing (B&W, color), Copying, Binding, Laminating, Scanning.  
Payment: Usually cash.
    """)
    
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
                if st.button(f"💡 Ask AI about '{pap_query}'", key="pap_ai"):
                    with st.spinner("Generating explanation..."):
                        ai_vocab = get_ai_vocab_response(pap_query, lesson="papeleria")
                        display_ai_vocab(ai_vocab)

# ============================================================================
# TAB 6: SCHOOL
# ============================================================================

with tab6:
    st.subheader("🎓 School (Escuela)")
    
    st.info("""
School types: Public, private, bilingual, international.  
Enrollment: July-August. Typical fees: 800-3,000 pesos/month.
    """)
    
    school_query = st.text_input("Search school vocabulary:", placeholder="e.g., uniform, teacher", key="school_search")
    
    if school_query:
        results = search_vocabulary(school_query, lesson="school")
        
        if results:
            st.success(f"✅ Found {len(results)} result(s)")
            for item in results:
                display_vocab_entry(item)
        else:
            st.warning("❌ No results found in vocabulary.")
            if has_groq:
                if st.button(f"💡 Ask AI about '{school_query}'", key="school_ai"):
                    with st.spinner("Generating explanation..."):
                        ai_vocab = get_ai_vocab_response(school_query, lesson="school")
                        display_ai_vocab(ai_vocab)

# ============================================================================
# TAB 7: MEASUREMENTS
# ============================================================================

with tab7:
    st.header("📐 Measurements (Medidas)")
    st.info("Common measurements: Fractions (medio, cuarto), weight (gramo, kilo), volume (litro, taza).")
    
    measurements = [
        {"spanish": "medio", "english": "half"},
        {"spanish": "cuarto", "english": "quarter"},
        {"spanish": "gramo", "english": "gram"},
        {"spanish": "kilogramo", "english": "kilogram"},
        {"spanish": "litro", "english": "liter"},
        {"spanish": "taza", "english": "cup"},
    ]
    
    for m in measurements:
        st.write(f"**{m['spanish']}** = {m['english']}")

# ============================================================================
# TAB 8: TIME
# ============================================================================

with tab8:
    st.header("⏰ Time (Tiempo)")
    st.info("Days, months, time expressions.")
    
    time_info = {
        "Days": "lunes, martes, miércoles, jueves, viernes, sábado, domingo",
        "Expressions": "ahora (now), hoy (today), mañana (tomorrow), ayer (yesterday)"
    }
    
    for cat, items in time_info.items():
        st.write(f"**{cat}:** {items}")

# ============================================================================
# TAB 9: NUMBERS
# ============================================================================

with tab9:
    st.header("🔢 Numbers (Números)")
    st.info("0-10: cero, uno, dos, tres, cuatro, cinco, seis, siete, ocho, nueve, diez")
    
    numbers = {
        "0-5": "cero, uno, dos, tres, cuatro, cinco",
        "6-10": "seis, siete, ocho, nueve, diez",
        "Tens": "diez, veinte, treinta, cien, mil"
    }
    
    for cat, nums in numbers.items():
        st.write(f"**{cat}:** {nums}")

# ============================================================================
# TAB 10: MONEY
# ============================================================================

with tab10:
    st.header("💰 Money (Dinero)")
    st.info("Currency: peso, centavo, billete. Payment: dinero, precio, pago, cambio, efectivo.")
    
    money = {
        "Currency": "peso, centavo, moneda, billete",
        "Payment": "dinero, precio, pago, cambio, efectivo"
    }
    
    for cat, items in money.items():
        st.write(f"**{cat}:** {items}")

# ============================================================================
# TAB 11: CONVEYANCE
# ============================================================================

with tab11:
    st.header("🚗 Conveyance (Transporte)")
    
    st.info("""
**Options:** Taxis (metered), Buses (9-13 pesos), Uber/Didi (app), Bikes (rentals), Cars (rentals), Walking.
    """)
    
    transport = {
        "Taxis": "Hail on street or call. Negotiate price.",
        "Buses": "Fixed routes. Pay upon boarding (cash).",
        "Uber/Didi": "App-based. Card payment.",
        "Bikes": "Rentals in city center.",
        "Driving": "Rental agencies available. License + passport needed."
    }
    
    for trans, info in transport.items():
        st.write(f"**{trans}:** {info}")

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
**Contexto: Language Learning for Querétaro Expats**  
✅ 11 tabs | 📚 Grammar | 🇪🇸🇬🇧 Bilingual | 🤖 AI vocab (working) | 📐 References | 🚗 Conveyance  
Built for real expat needs | November 2026
""")
