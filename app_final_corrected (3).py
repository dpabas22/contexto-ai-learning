"""
Contexto: AI-Powered Language Learning for Expats in Querétaro
Final Production Version: Fixed Groq, Direct Audio, Animated Conversations
"""

import streamlit as st
import json
import os
from groq import Groq
from gtts import gTTS
import io
import pandas as pd

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
# AI VOCAB RESPONSE - FIXED (Works reliably)
# ============================================================================

def get_ai_vocab_response(query, lesson=""):
    """
    AI vocab: Fixed working mode
    Returns translation + Spanish explanation
    FIXED: Removed restrictive prompts
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
        
        # CALL 1: Get translation (simplified prompt - no restrictive constraints)
        if is_spanish:
            trans_prompt = f"What is the English translation of: {query}"
        else:
            trans_prompt = f"What is the Spanish translation of: {query}"
        
        trans_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": trans_prompt}],
            max_tokens=30,
            temperature=0.1
        )
        
        translation = trans_response.choices[0].message.content.strip()
        # Clean up response - take first meaningful word/phrase
        translation = translation.split('\n')[0].strip()
        
        # CALL 2: Get Spanish explanation
        if is_spanish:
            exp_prompt = f"Explain '{query}' in Spanish. 2-3 sentences, simple and clear."
        else:
            exp_prompt = f"Explain '{query}' in Spanish. 2-3 sentences, simple and clear."
        
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
    """Display internal vocab entry - FIXED: Direct audio, no button"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown(f"**{item['spanish']}**")
    
    with col2:
        st.write(f"{item['english']} • {item.get('context', '')}")
    
    with st.expander(f"Details - {item['spanish']}"):
        # FIXED: Direct audio player (no button needed)
        st.markdown(f"**🔊 Pronunciation:** {item.get('pronunciation', 'N/A')}")
        audio = create_audio(item['spanish'], lang='es')
        if audio:
            st.audio(audio, format='audio/mp3')
        
        st.markdown(f"**💬 Example:** {item.get('example_spanish', 'N/A')}")
        
        # FIXED: Direct audio player for example (no button needed)
        audio_ex = create_audio(item.get('example_spanish', ''), lang='es')
        if audio_ex:
            st.audio(audio_ex, format='audio/mp3')
        
        st.write(f"**🔤 English:** {item.get('example_english', 'N/A')}")
        
        if item.get('price_range_pesos'):
            st.write(f"**💰 Price range:** {item['price_range_pesos']} pesos")
    
    st.divider()

def display_ai_vocab(vocab_result):
    """Display AI-generated vocab - FIXED: Show explanation first"""
    if vocab_result["error"]:
        st.error(f"❌ {vocab_result['explanation']}")
        return
    
    # FIXED: Show explanation FIRST (meaning), then translation
    if vocab_result['explanation']:
        st.markdown("### 📚 Explicación (Spanish):")
        st.markdown(f"> {vocab_result['explanation']}")
    
    # Show translation
    if vocab_result["is_spanish"]:
        st.markdown(f"### 🇪🇸 Spanish: **{vocab_result['query']}**")
        st.markdown(f"### 🇬🇧 English: **{vocab_result['translation']}**")
    else:
        st.markdown(f"### 🇬🇧 English: **{vocab_result['query']}**")
        st.markdown(f"### 🇪🇸 Spanish: **{vocab_result['translation']}**")

def display_conversation_with_animation(speaker, spanish_text, english_text, emoji):
    """Display conversation with animated character"""
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown(f"# {emoji}")
    
    with col2:
        st.markdown(f"**{speaker}**")
        st.markdown(f"*🇪🇸* {spanish_text}")
        st.markdown(f"*🇬🇧* {english_text}")

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
# TAB 1: CONVERSATIONS - WITH ANIMATIONS
# ============================================================================

with tab1:
    st.header("💬 Real Conversations - Learn from Scenarios")
    
    selected_lesson = st.selectbox(
        "Choose a lesson:",
        ["Market", "Hospital", "Paper Store", "School"],
        key="conv_lesson"
    )
    
    if selected_lesson == "Market":
        st.subheader("🏪 Market (Mercado) - Fresh Fish Purchase")
        st.markdown("---")
        
        # Animated conversation
        display_conversation_with_animation(
            "Jasmine (Customer)",
            "Hola, ¿tiene pescado fresco hoy?",
            "Hi, do you have fresh fish today?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Vendor (Vendedor)",
            "Sí, claro. Tengo pargo, robalo, y trucha. Todos muy frescos.",
            "Yes, of course. I have snapper, bass, and trout. All very fresh.",
            "👨‍🍳"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "¿Cuánto cuesta el pargo?",
            "How much does the snapper cost?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Vendor",
            "120 pesos el kilo. Es de esta mañana.",
            "120 pesos per kilo. It's from this morning.",
            "👨‍🍳"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "¿Qué me recomienda?",
            "What do you recommend?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Vendor",
            "El robalo está delicioso hoy. Perfecto para ceviche.",
            "The bass is delicious today. Perfect for ceviche.",
            "👨‍🍳"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Dale, dame 750 gramos de robalo. ¿Cuál es el precio total?",
            "Okay, give me 750 grams of bass. What's the total price?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Vendor",
            "750 gramos a 130 pesos el kilo... eso son 97 pesos y medio.",
            "750 grams at 130 pesos per kilo... that's 97.50 pesos.",
            "👨‍🍳"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "¿Es el mejor precio?",
            "Is that the best price?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Vendor",
            "Es justo el precio. Muy fresco, ¿ves? Brilla.",
            "That's a fair price. Very fresh, see? It shines.",
            "👨‍🍳"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Dale, listo. ¿Me lo limpias?",
            "Okay, done. Can you clean it for me?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Vendor",
            "Claro. Te lo dejo sin escamas y sin tripas.",
            "Of course. I'll clean off the scales and guts for you.",
            "👨‍🍳"
        )

    elif selected_lesson == "Hospital":
        st.subheader("🏥 Hospital (Hospital) - Doctor's Appointment")
        st.markdown("---")
        
        display_conversation_with_animation(
            "Jasmine (Patient)",
            "Hola, buenos días. Necesito una cita con el doctor.",
            "Hi, good morning. I need an appointment with the doctor.",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Receptionist (Recepcionista)",
            "¿Cuál es tu problema o síntoma?",
            "What is your problem or symptom?",
            "👨‍💼"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Tengo dolor de cabeza y fiebre desde hace dos días.",
            "I've had a headache and fever for two days.",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Receptionist",
            "¿Tienes seguro médico?",
            "Do you have health insurance?",
            "👨‍💼"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Sí, tengo Monterrey New York Life.",
            "Yes, I have Monterrey New York Life.",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Receptionist",
            "Perfecto. El doctor García tiene disponibilidad hoy a las 4 de la tarde, o mañana a las 10 de la mañana.",
            "Perfect. Doctor García is available today at 4 PM, or tomorrow at 10 AM.",
            "👨‍💼"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Prefiero hoy a las 4. ¿Cuál es el costo de la consulta?",
            "I prefer today at 4. What's the consultation cost?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Receptionist",
            "Con tu seguro, solo pagas 300 pesos de copago.",
            "With your insurance, you only pay 300 pesos copay.",
            "👨‍💼"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Dale, confirmo para hoy a las 4. ¿Necesito traer algo?",
            "Okay, I confirm for today at 4. Do I need to bring anything?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Receptionist",
            "Trae tu seguro y una identificación. Llega 10 minutos antes.",
            "Bring your insurance and an ID. Arrive 10 minutes early.",
            "👨‍💼"
        )

    elif selected_lesson == "Paper Store":
        st.subheader("📝 Paper Store (Papelería) - Printing Documents")
        st.markdown("---")
        
        display_conversation_with_animation(
            "Jasmine (Customer)",
            "Hola, necesito imprimir estos documentos. ¿Cuánto cuesta?",
            "Hi, I need to print these documents. How much does it cost?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Staff (Empleado)",
            "A ver cuántas páginas. Uno, dos... son 15 páginas. ¿Blanco y negro o a color?",
            "Let me see how many pages. One, two... it's 15 pages. Black and white or color?",
            "👨‍💻"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Blanco y negro está bien. ¿Cuál es el precio?",
            "Black and white is fine. What's the price?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Staff",
            "Blanco y negro es 0.50 pesos por página. Son 7.50 pesos en total.",
            "Black and white is 0.50 pesos per page. That's 7.50 pesos total.",
            "👨‍💻"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Dale. ¿Cuánto tiempo tarda?",
            "Okay. How long does it take?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Staff",
            "Dos minutos. ¿Necesitas otro servicio? ¿Encuadernación? ¿Laminado?",
            "Two minutes. Do you need another service? Binding? Laminating?",
            "👨‍💻"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Laminado, sí. Una página laminada. ¿Cuánto cuesta?",
            "Laminating, yes. One laminated page. How much does it cost?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Staff",
            "30 pesos por página laminada, tamaño carta.",
            "30 pesos per laminated page, letter size.",
            "👨‍💻"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Perfecto. Lamina esta portada. ¿Cuál es el total?",
            "Perfect. Laminate this cover page. What's the total?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Staff",
            "7.50 de impresión, más 30 de laminado. Total 37.50 pesos. Listo en 5 minutos.",
            "7.50 for printing, plus 30 for laminating. Total 37.50 pesos. Done in 5 minutes.",
            "👨‍💻"
        )

    else:  # School
        st.subheader("🎓 School (Escuela) - School Registration")
        st.markdown("---")
        
        display_conversation_with_animation(
            "Jasmine (Parent)",
            "Buenos días, me interesa inscribir a mi hijo en la escuela.",
            "Good morning, I'm interested in registering my son in school.",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Director (Director)",
            "Bienvenido. ¿En qué grado?",
            "Welcome. What grade?",
            "👨‍🏫"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Tercero de primaria. ¿Cuál es el proceso de admisión?",
            "Third grade elementary. What's the admission process?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Director",
            "Primero necesito documentos: acta de nacimiento, comprobante de domicilio, cartilla de vacunas.",
            "First I need documents: birth certificate, proof of address, vaccination card.",
            "👨‍🏫"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "¿Tengo que hacer un examen de admisión?",
            "Do I need to take an admission exam?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Director",
            "Sí, un examen simple de matemáticas y español. También entrevista con los padres.",
            "Yes, a simple exam in math and Spanish. Also an interview with parents.",
            "👨‍🏫"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "¿Cuándo se pueden hacer los exámenes?",
            "When can the exams be done?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Director",
            "Disponemos de citas. ¿Prefieres próxima semana o en dos semanas?",
            "We have appointments available. Do you prefer next week or in two weeks?",
            "👨‍🏫"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Jasmine",
            "Próxima semana estaría bien. ¿Cuál es el costo de la matrícula?",
            "Next week would be good. What's the tuition cost?",
            "👩‍🦰"
        )
        
        st.markdown("")
        
        display_conversation_with_animation(
            "Director",
            "La matrícula es de 2,500 pesos. La mensualidad es 1,800 pesos, de septiembre a junio.",
            "The enrollment fee is 2,500 pesos. Monthly tuition is 1,800 pesos, from September to June.",
            "👨‍🏫"
        )

# ============================================================================
# TAB 2: GRAMMAR
# ============================================================================

with tab2:
    st.header("📚 Spanish Pronouns & Verb Conjugations")
    
    # ============ PRONOUNS SECTION ============
    st.subheader("Part 1: Understanding Spanish Pronouns")
    
    st.markdown("""
Before conjugating verbs, you need to master Spanish pronouns. They change form based on their role:
- **Subject pronouns** → Tell WHO is doing the action
- **Object pronouns** → Tell WHO receives the action
- **Possessive pronouns** → Tell WHO something belongs to
    """)
    
    # Pronouns table data
    pronouns_data = {
        "Person": ["I", "You (singular)", "He", "She", "We", "You (plural)", "They"],
        "Subject\n(who does it)": ["Yo", "Tú", "Él", "Ella", "Nosotros", "Ustedes", "Ellos"],
        "Object\n(receives action)": ["Me", "Te", "Lo", "La", "Nos", "Os", "Los"],
        "Possessive\n(belongs to)": ["Mío/Mía", "Tuyo/Tuya", "Suyo", "Suya", "Nuestro", "Vuestro", "Suyo"],
        "Spanish Example": [
            "Yo hablo español",
            "Tú hablas inglés",
            "Él trabaja aquí",
            "Ella estudia medicina",
            "Nosotros vivimos en Querétaro",
            "Ustedes comen en el mercado",
            "Ellos viajan mañana"
        ],
        "English Translation": [
            "I speak Spanish",
            "You speak English",
            "He works here",
            "She studies medicine",
            "We live in Querétaro",
            "You all eat at the market",
            "They travel tomorrow"
        ]
    }
    
    df_pronouns = pd.DataFrame(pronouns_data)
    st.dataframe(df_pronouns, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Interactive pronouns with audio - ALL THREE TYPES
    st.subheader("Part 2: Hear Each Pronoun (Subject, Object & Possessive)")
    
    pronouns_with_audio = [
        {
            "person": "I (Yo)",
            "subject": "Yo",
            "object": "Me",
            "possessive": "Mío/Mía",
            "subject_example": "Yo hablo español",
            "subject_english": "I speak Spanish",
            "object_example": "Él me ve",
            "object_english": "He sees me",
            "possessive_example": "Esto es mío",
            "possessive_english": "This is mine",
        },
        {
            "person": "You - singular (Tú)",
            "subject": "Tú",
            "object": "Te",
            "possessive": "Tuyo/Tuya",
            "subject_example": "Tú hablas inglés",
            "subject_english": "You speak English",
            "object_example": "Yo te veo",
            "object_english": "I see you",
            "possessive_example": "Eso es tuyo",
            "possessive_english": "That is yours",
        },
        {
            "person": "He (Él)",
            "subject": "Él",
            "object": "Lo",
            "possessive": "Suyo",
            "subject_example": "Él trabaja aquí",
            "subject_english": "He works here",
            "object_example": "Nosotros lo vemos",
            "object_english": "We see him",
            "possessive_example": "Eso es suyo",
            "possessive_english": "That is his",
        },
        {
            "person": "She (Ella)",
            "subject": "Ella",
            "object": "La",
            "possessive": "Suya",
            "subject_example": "Ella estudia medicina",
            "subject_english": "She studies medicine",
            "object_example": "Yo la ayudo",
            "object_english": "I help her",
            "possessive_example": "Eso es suya",
            "possessive_english": "That is hers",
        },
        {
            "person": "We (Nosotros)",
            "subject": "Nosotros",
            "object": "Nos",
            "possessive": "Nuestro",
            "subject_example": "Nosotros vivimos en Querétaro",
            "subject_english": "We live in Querétaro",
            "object_example": "Ellos nos ayudan",
            "object_english": "They help us",
            "possessive_example": "Esto es nuestro",
            "possessive_english": "This is ours",
        },
        {
            "person": "You - plural (Ustedes)",
            "subject": "Ustedes",
            "object": "Os",
            "possessive": "Vuestro",
            "subject_example": "Ustedes comen en el mercado",
            "subject_english": "You all eat at the market",
            "object_example": "Yo os veo",
            "object_english": "I see you all",
            "possessive_example": "Eso es vuestro",
            "possessive_english": "That is yours (all)",
        },
        {
            "person": "They (Ellos)",
            "subject": "Ellos",
            "object": "Los",
            "possessive": "Suyo",
            "subject_example": "Ellos viajan mañana",
            "subject_english": "They travel tomorrow",
            "object_example": "Nosotros los vemos",
            "object_english": "We see them",
            "possessive_example": "Eso es suyo",
            "possessive_english": "That is theirs",
        },
    ]
    
    for item in pronouns_with_audio:
        with st.expander(f"**{item['person']}** → Subject: {item['subject']} | Object: {item['object']} | Possessive: {item['possessive']}"):
            
            # SUBJECT PRONOUN
            st.markdown("### 🟦 Subject (WHO is doing the action)")
            col1, col2 = st.columns([1.5, 1.5])
            with col1:
                st.markdown("🇪🇸 Spanish:")
                st.write(item['subject_example'])
                audio_subject = create_audio(item['subject_example'], lang='es')
                if audio_subject:
                    st.audio(audio_subject, format='audio/mp3')
            with col2:
                st.markdown("🇬🇧 English:")
                st.write(item['subject_english'])
            
            st.divider()
            
            # OBJECT PRONOUN
            st.markdown("### 🟩 Object (WHO receives the action)")
            col1, col2 = st.columns([1.5, 1.5])
            with col1:
                st.markdown("🇪🇸 Spanish:")
                st.write(item['object_example'])
                audio_object = create_audio(item['object_example'], lang='es')
                if audio_object:
                    st.audio(audio_object, format='audio/mp3')
            with col2:
                st.markdown("🇬🇧 English:")
                st.write(item['object_english'])
            
            st.divider()
            
            # POSSESSIVE PRONOUN
            st.markdown("### 🟨 Possessive (WHO it belongs to)")
            col1, col2 = st.columns([1.5, 1.5])
            with col1:
                st.markdown("🇪🇸 Spanish:")
                st.write(item['possessive_example'])
                audio_possessive = create_audio(item['possessive_example'], lang='es')
                if audio_possessive:
                    st.audio(audio_possessive, format='audio/mp3')
            with col2:
                st.markdown("🇬🇧 English:")
                st.write(item['possessive_english'])
    
    st.divider()
    
    st.markdown("""
### 💡 Key Rules:
- **Subject pronouns** (Yo, Tú, Él...) → Use with verbs to say WHO is doing something
- **Object pronouns** (Me, Te, Lo...) → Use to show WHO receives the action
- **Possessive pronouns** (Mío, Tuyo, Suyo...) → Show ownership
    """)
    
    st.divider()
    
    st.subheader("Part 3: Conjugate Verbs by Pronoun")
    st.write("Now that you know the pronouns, let's see how verbs change for each one!")
    
    grammar_data = {
        "Ser (To Be)": {
            "yo": {"conjugation": "soy", "example": "Yo soy enfermera", "example_en": "I am a nurse"},
            "tú": {"conjugation": "eres", "example": "Tú eres amable", "example_en": "You are kind"},
            "él": {"conjugation": "es", "example": "Él es doctor", "example_en": "He is a doctor"},
            "ella": {"conjugation": "es", "example": "Ella es ingeniera", "example_en": "She is an engineer"},
            "nosotros": {"conjugation": "somos", "example": "Nosotros somos amigos", "example_en": "We are friends"},
            "ustedes": {"conjugation": "son", "example": "Ustedes son estudiantes", "example_en": "You all are students"},
            "ellos": {"conjugation": "son", "example": "Ellos son hermanos", "example_en": "They are brothers"},
        },
        "Estar (To Be - Location/Feeling)": {
            "yo": {"conjugation": "estoy", "example": "Yo estoy en el mercado", "example_en": "I am at the market"},
            "tú": {"conjugation": "estás", "example": "Tú estás feliz", "example_en": "You are happy"},
            "él": {"conjugation": "está", "example": "Él está aquí", "example_en": "He is here"},
            "ella": {"conjugation": "está", "example": "Ella está enferma", "example_en": "She is sick"},
            "nosotros": {"conjugation": "estamos", "example": "Nosotros estamos cansados", "example_en": "We are tired"},
            "ustedes": {"conjugation": "están", "example": "Ustedes están ocupados", "example_en": "You all are busy"},
            "ellos": {"conjugation": "están", "example": "Ellos están viajando", "example_en": "They are traveling"},
        },
        "Tener (To Have)": {
            "yo": {"conjugation": "tengo", "example": "Yo tengo un libro", "example_en": "I have a book"},
            "tú": {"conjugation": "tienes", "example": "Tú tienes fiebre", "example_en": "You have a fever"},
            "él": {"conjugation": "tiene", "example": "Él tiene un coche", "example_en": "He has a car"},
            "ella": {"conjugation": "tiene", "example": "Ella tiene dos hijos", "example_en": "She has two children"},
            "nosotros": {"conjugation": "tenemos", "example": "Nosotros tenemos hambre", "example_en": "We are hungry"},
            "ustedes": {"conjugation": "tienen", "example": "Ustedes tienen tiempo", "example_en": "You all have time"},
            "ellos": {"conjugation": "tienen", "example": "Ellos tienen dinero", "example_en": "They have money"},
        },
        "Ir (To Go)": {
            "yo": {"conjugation": "voy", "example": "Yo voy al hospital", "example_en": "I go to the hospital"},
            "tú": {"conjugation": "vas", "example": "Tú vas a la escuela", "example_en": "You go to school"},
            "él": {"conjugation": "va", "example": "Él va al trabajo", "example_en": "He goes to work"},
            "ella": {"conjugation": "va", "example": "Ella va al mercado", "example_en": "She goes to the market"},
            "nosotros": {"conjugation": "vamos", "example": "Nosotros vamos juntos", "example_en": "We go together"},
            "ustedes": {"conjugation": "van", "example": "Ustedes van rápido", "example_en": "You all go fast"},
            "ellos": {"conjugation": "van", "example": "Ellos van mañana", "example_en": "They go tomorrow"},
        },
        "Hablar (To Speak)": {
            "yo": {"conjugation": "hablo", "example": "Yo hablo español", "example_en": "I speak Spanish"},
            "tú": {"conjugation": "hablas", "example": "Tú hablas inglés", "example_en": "You speak English"},
            "él": {"conjugation": "habla", "example": "Él habla francés", "example_en": "He speaks French"},
            "ella": {"conjugation": "habla", "example": "Ella habla con claridad", "example_en": "She speaks clearly"},
            "nosotros": {"conjugation": "hablamos", "example": "Nosotros hablamos de trabajo", "example_en": "We talk about work"},
            "ustedes": {"conjugation": "hablan", "example": "Ustedes hablan muy bien", "example_en": "You all speak very well"},
            "ellos": {"conjugation": "hablan", "example": "Ellos hablan entre sí", "example_en": "They speak to each other"},
        },
        "Comprar (To Buy)": {
            "yo": {"conjugation": "compro", "example": "Yo compro pescado", "example_en": "I buy fish"},
            "tú": {"conjugation": "compras", "example": "Tú compras frutas", "example_en": "You buy fruits"},
            "él": {"conjugation": "compra", "example": "Él compra pan", "example_en": "He buys bread"},
            "ella": {"conjugation": "compra", "example": "Ella compra verduras", "example_en": "She buys vegetables"},
            "nosotros": {"conjugation": "compramos", "example": "Nosotros compramos comida", "example_en": "We buy food"},
            "ustedes": {"conjugation": "compran", "example": "Ustedes compran en el mercado", "example_en": "You all buy at the market"},
            "ellos": {"conjugation": "compran", "example": "Ellos compran en línea", "example_en": "They buy online"},
        },
        "Necesitar (To Need)": {
            "yo": {"conjugation": "necesito", "example": "Yo necesito un doctor", "example_en": "I need a doctor"},
            "tú": {"conjugation": "necesitas", "example": "Tú necesitas agua", "example_en": "You need water"},
            "él": {"conjugation": "necesita", "example": "Él necesita dormir", "example_en": "He needs to sleep"},
            "ella": {"conjugation": "necesita", "example": "Ella necesita ayuda", "example_en": "She needs help"},
            "nosotros": {"conjugation": "necesitamos", "example": "Nosotros necesitamos dinero", "example_en": "We need money"},
            "ustedes": {"conjugation": "necesitan", "example": "Ustedes necesitan descanso", "example_en": "You all need rest"},
            "ellos": {"conjugation": "necesitan", "example": "Ellos necesitan información", "example_en": "They need information"},
        },
        "Comer (To Eat)": {
            "yo": {"conjugation": "como", "example": "Yo como en el mercado", "example_en": "I eat at the market"},
            "tú": {"conjugation": "comes", "example": "Tú comes pizza", "example_en": "You eat pizza"},
            "él": {"conjugation": "come", "example": "Él come arroz", "example_en": "He eats rice"},
            "ella": {"conjugation": "come", "example": "Ella come sano", "example_en": "She eats healthy"},
            "nosotros": {"conjugation": "comemos", "example": "Nosotros comemos juntos", "example_en": "We eat together"},
            "ustedes": {"conjugation": "comen", "example": "Ustedes comen bien", "example_en": "You all eat well"},
            "ellos": {"conjugation": "comen", "example": "Ellos comen pescado", "example_en": "They eat fish"},
        },
    }
    
    selected_verb = st.selectbox("Choose a verb:", list(grammar_data.keys()))
    
    if selected_verb:
        verb_info = grammar_data[selected_verb]
        st.subheader(selected_verb)
        
        st.markdown("#### Conjugation Table:")
        
        # Display conjugation for each person
        people = [
            ("yo", "🟦 I"),
            ("tú", "🟩 You (singular)"),
            ("él", "🟨 He"),
            ("ella", "🟧 She"),
            ("nosotros", "🟪 We"),
            ("ustedes", "🟫 You (plural)"),
            ("ellos", "🟥 They")
        ]
        
        for key, label in people:
            if key in verb_info:
                data = verb_info[key]
                with st.expander(f"**{label}** → {data['conjugation']}"):
                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        st.markdown(f"**Conjugation:**")
                        st.write(f"### {data['conjugation']}")
                    
                    with col2:
                        st.markdown(f"**Example:**")
                        st.write(f"🇪🇸 {data['example']}")
                        audio_es = create_audio(data['example'], lang='es')
                        if audio_es:
                            st.audio(audio_es, format='audio/mp3')
                    
                    st.write(f"🇬🇧 {data['example_en']}")

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
        {"spanish": "medio", "english": "half", "pronunciation": "MEH-dee-oh", "example_spanish": "Quiero medio kilo", "example_english": "I want half a kilo"},
        {"spanish": "cuarto", "english": "quarter", "pronunciation": "KWAHR-toh", "example_spanish": "Un cuarto de kilo", "example_english": "A quarter kilo"},
        {"spanish": "gramo", "english": "gram", "pronunciation": "GRAH-moh", "example_spanish": "500 gramos", "example_english": "500 grams"},
        {"spanish": "kilogramo", "english": "kilogram", "pronunciation": "kee-loh-GRAH-moh", "example_spanish": "Un kilogramo de arroz", "example_english": "One kilogram of rice"},
        {"spanish": "litro", "english": "liter", "pronunciation": "LEE-troh", "example_spanish": "Un litro de leche", "example_english": "One liter of milk"},
        {"spanish": "taza", "english": "cup", "pronunciation": "TAH-sah", "example_spanish": "Una taza de café", "example_english": "A cup of coffee"},
    ]
    
    for m in measurements:
        m['context'] = 'Measurements'
        m['id'] = m['spanish']
        display_vocab_entry(m)

# ============================================================================
# TAB 8: TIME
# ============================================================================

with tab8:
    st.header("⏰ Time (Tiempo)")
    st.info("Days, months, time expressions.")
    
    time_data = {
        "Days": [
            {"spanish": "lunes", "english": "Monday", "pronunciation": "LOO-nes", "example_spanish": "El lunes voy al mercado", "example_english": "On Monday I go to the market"},
            {"spanish": "martes", "english": "Tuesday", "pronunciation": "MAHR-tes", "example_spanish": "El martes tengo cita", "example_english": "On Tuesday I have an appointment"},
            {"spanish": "miércoles", "english": "Wednesday", "pronunciation": "mee-EHR-koh-les", "example_spanish": "El miércoles es festivo", "example_english": "Wednesday is a holiday"},
            {"spanish": "jueves", "english": "Thursday", "pronunciation": "HWE-ves", "example_spanish": "El jueves trabajo", "example_english": "On Thursday I work"},
            {"spanish": "viernes", "english": "Friday", "pronunciation": "vee-EHR-nes", "example_spanish": "El viernes es mi día favorito", "example_english": "Friday is my favorite day"},
            {"spanish": "sábado", "english": "Saturday", "pronunciation": "SAH-bah-doh", "example_spanish": "El sábado salgo de compras", "example_english": "On Saturday I go shopping"},
            {"spanish": "domingo", "english": "Sunday", "pronunciation": "doh-MEEN-goh", "example_spanish": "El domingo vamos a la iglesia", "example_english": "On Sunday we go to church"},
        ],
        "Time Expressions": [
            {"spanish": "ahora", "english": "now", "pronunciation": "AH-oh-rah", "example_spanish": "Ahora es la una", "example_english": "It is now one o'clock"},
            {"spanish": "hoy", "english": "today", "pronunciation": "OY", "example_spanish": "Hoy es lunes", "example_english": "Today is Monday"},
            {"spanish": "mañana", "english": "tomorrow", "pronunciation": "mah-YAH-nah", "example_spanish": "Mañana es martes", "example_english": "Tomorrow is Tuesday"},
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
✨ 11 tabs | 📚 15 verbs | 🇪🇸🇬🇧 Bilingual | 🤖 Smart AI vocab (working mode)  
📐 Essential references | 🚗 Conveyance guide | 💬 Animated conversations  
Built with ❤️ for Querétaro expats | November 2026
""")
