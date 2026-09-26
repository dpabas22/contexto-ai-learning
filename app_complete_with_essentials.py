"""
Contexto: AI-Powered Language Learning for Expats
Complete Version: Bilingual AI Vocab Format + 4 Essential Tabs
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
# STRUCTURED AI VOCAB RESPONSE FUNCTION
# ============================================================================

def get_ai_vocab_response(query, lesson="", context=""):
    """Get structured AI vocab response: {spanish, english, pronunciation, usage, examples}"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {
                "spanish": "N/A",
                "english": "API key not configured",
                "pronunciation": "N/A",
                "usage": "Cannot access AI",
                "examples": []
            }
        
        client = Groq(api_key=api_key)
        lesson_context = f"The user is learning about {lesson}. " if lesson else ""
        
        # CALL 1: Get Spanish vocab word/phrase
        spanish_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a Spanish vocabulary expert. {lesson_context}Given a user query, return ONLY the most relevant Spanish word or short phrase (2-3 words max). Nothing else. No explanation."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            max_tokens=50,
            temperature=0.7
        )
        spanish_word = spanish_response.choices[0].message.content.strip()
        
        # CALL 2: Get English translation
        english_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a translator. Return ONLY the English translation of the Spanish word/phrase. Nothing else."
                },
                {
                    "role": "user",
                    "content": spanish_word
                }
            ],
            max_tokens=50,
            temperature=0.3
        )
        english_word = english_response.choices[0].message.content.strip()
        
        # CALL 3: Get pronunciation guide
        pronunciation_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Spanish pronunciation expert. Given a Spanish word, provide ONLY a simple pronunciation guide using English phonetics (1 line max). Example: 'pes-KAH-doh'"
                },
                {
                    "role": "user",
                    "content": spanish_word
                }
            ],
            max_tokens=50,
            temperature=0.3
        )
        pronunciation = pronunciation_response.choices[0].message.content.strip()
        
        # CALL 4: Get usage/context explanation
        usage_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a Spanish language tutor. {lesson_context}Explain when and how to use this Spanish word/phrase. Keep it 1-2 sentences, simple."
                },
                {
                    "role": "user",
                    "content": spanish_word
                }
            ],
            max_tokens=100,
            temperature=0.7
        )
        usage = usage_response.choices[0].message.content.strip()
        
        # CALL 5: Get 2 example sentences (Spanish)
        examples_sp_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a Spanish language expert. {lesson_context}Provide 2 example sentences using this word. Format: 'Sentence 1. Sentence 2.' Nothing else."
                },
                {
                    "role": "user",
                    "content": spanish_word
                }
            ],
            max_tokens=100,
            temperature=0.7
        )
        examples_spanish_text = examples_sp_response.choices[0].message.content.strip()
        
        # CALL 6: Translate examples to English
        examples_en_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a translator. Translate these Spanish sentences to English. Use same sentence order. Format: 'Translation 1. Translation 2.'"
                },
                {
                    "role": "user",
                    "content": examples_spanish_text
                }
            ],
            max_tokens=100,
            temperature=0.3
        )
        examples_english_text = examples_en_response.choices[0].message.content.strip()
        
        # Parse examples
        sp_examples = examples_spanish_text.split(". ")
        en_examples = examples_english_text.split(". ")
        
        examples = []
        for i in range(min(2, len(sp_examples), len(en_examples))):
            examples.append({
                "spanish": sp_examples[i].strip(),
                "english": en_examples[i].strip()
            })
        
        return {
            "spanish": spanish_word,
            "english": english_word,
            "pronunciation": pronunciation,
            "usage": usage,
            "examples": examples
        }
    except Exception as e:
        return {
            "spanish": "Error",
            "english": f"Error: {str(e)[:50]}",
            "pronunciation": "N/A",
            "usage": "Could not generate response",
            "examples": []
        }

# ============================================================================
# DISPLAY VOCAB ENTRY FUNCTION
# ============================================================================

def display_vocab_entry(item, show_audio=True):
    """Display a vocab entry in consistent format"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown(f"**{item['spanish']}**")
    
    with col2:
        st.write(f"{item['english']} • {item.get('context', '')}")
    
    with st.expander(f"Details - {item['spanish']}"):
        # Audio button
        if show_audio:
            if st.button(f"🔊 {item['spanish']}", key=f"audio_{item.get('id', item['spanish'])}"):
                audio = create_audio(item['spanish'], lang='es')
                if audio:
                    st.audio(audio, format='audio/mp3')
        
        # Pronunciation
        st.write(f"📣 **Pronunciation:** {item.get('pronunciation', 'N/A')}")
        
        # Example
        st.write(f"💬 **Example:** {item.get('example_spanish', 'N/A')}")
        
        if st.button("▶️ Hear example", key=f"audio_ex_{item.get('id', item['spanish'])}"):
            audio = create_audio(item.get('example_spanish', ''), lang='es')
            if audio:
                st.audio(audio, format='audio/mp3')
        
        # English translation
        st.write(f"🔤 **English:** {item.get('example_english', 'N/A')}")
        
        # Price if applicable
        if item.get('price_range_pesos'):
            st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
    
    st.divider()

# ============================================================================
# PAGE HEADER
# ============================================================================

st.title("🌍 Contexto: Language Learning for Real Expat Needs")
st.markdown("**Learn Spanish through real conversations in Querétaro**")

st.info("""
✅ **Querétaro-Specific Content:** Market (La Cruz), Hospital, Papelería, School  
✅ **Essential References:** Measurements, Time, Numbers, Money  
⚠️ **Generic Responses:** Questions outside these topics use general knowledge  
📅 **Phase 2 Roadmap:** Restaurants, neighborhoods, transportation, shopping
""")

# ============================================================================
# TABS - COMPLETE
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "💬 Conversations", "📚 Grammar", "🏪 Market", "🏥 Hospital", 
    "📝 Papelería", "🎓 School", "📐 Measurements", "⏰ Time", "🔢 Numbers", "💰 Money"
])

# ============================================================================
# TAB 1: CONVERSATIONS
# ============================================================================

with tab1:
    st.header("💬 Real Conversations - Learn from Scenarios")
    
    selected_lesson = st.selectbox(
        "Choose a lesson:",
        ["Market", "Hospital", "Papelería", "School"],
        key="conv_lesson"
    )
    
    if selected_lesson == "Market":
        st.subheader("🏪 Market Conversations - La Cruz Market")
        
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
            
            st.info("💡 **Key phrases:** Fresh fish types, pricing per kilo, negotiating, cleaning fish")
        
        with st.expander("**Dialogue 2: Haggling for Indian Spices**"):
            st.markdown("### 🇪🇸 Spanish:")
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
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** How much is the turmeric?  
**Vendor:** 250 pesos for 250 grams.  
**Jasmine:** That's too expensive. The other vendor asked me 200 pesos.  
**Vendor:** Really? Show me where. My turmeric is first quality.  
**Jasmine:** Well, maybe you're right. But I want 500 grams. Is there a discount?  
**Vendor:** If you buy two bags, I'll give you 10% off.  
**Jasmine:** Okay, give me two bags of turmeric and one of cumin too.  
**Vendor:** Excellent. That's 450 pesos total with the discount.  
**Jasmine:** Is this the best you have?  
**Vendor:** The best in the whole market. It comes from India, fresh. Smell, smell.
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
        
        if st.button(f"🔊 Hear: {selected_verb}", key=f"grammar_audio_{selected_verb}"):
            infinitive = selected_verb.split("(")[0].strip()
            audio = create_audio(infinitive, lang='es')
            if audio:
                st.audio(audio, format='audio/mp3')

# ============================================================================
# TAB 3: MARKET
# ============================================================================

with tab3:
    st.subheader("🏪 Market (La Cruz) - Shopping, Haggling, Groceries")
    
    st.markdown("### 🏪 Quick Reference - Top Market Words")
    quick_ref_market = [
        {"spanish": "pescado", "english": "fish"},
        {"spanish": "fresco", "english": "fresh"},
        {"spanish": "precio", "english": "price"},
        {"spanish": "cúrcuma", "english": "turmeric"},
        {"spanish": "descuento", "english": "discount"},
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
                    with st.spinner("Creating vocab entry..."):
                        ai_vocab = get_ai_vocab_response(market_query, lesson="market")
                        if ai_vocab['spanish'] != 'Error':
                            st.markdown(f"### 🇪🇸 Spanish: **{ai_vocab['spanish']}**")
                            st.markdown(f"### 🇬🇧 English: **{ai_vocab['english']}**")
                            st.write(f"📣 **Pronunciation:** {ai_vocab['pronunciation']}")
                            st.write(f"📚 **Usage:** {ai_vocab['usage']}")
                            st.write(f"💬 **Examples:**")
                            for ex in ai_vocab['examples']:
                                st.write(f"  • {ex['spanish']} = {ex['english']}")

# ============================================================================
# TAB 4: HOSPITAL
# ============================================================================

with tab4:
    st.subheader("🏥 Hospital - Medical Appointments, Specialists, Insurance")
    
    st.markdown("### 🏥 Quick Reference - Top Hospital Words")
    quick_ref_hospital = [
        {"spanish": "doctor", "english": "doctor"},
        {"spanish": "fiebre", "english": "fever"},
        {"spanish": "dolor", "english": "pain"},
        {"spanish": "cita", "english": "appointment"},
        {"spanish": "medicina", "english": "medicine"},
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
                    with st.spinner("Creating vocab entry..."):
                        ai_vocab = get_ai_vocab_response(hospital_query, lesson="hospital")
                        if ai_vocab['spanish'] != 'Error':
                            st.markdown(f"### 🇪🇸 Spanish: **{ai_vocab['spanish']}**")
                            st.markdown(f"### 🇬🇧 English: **{ai_vocab['english']}**")
                            st.write(f"📣 **Pronunciation:** {ai_vocab['pronunciation']}")
                            st.write(f"📚 **Usage:** {ai_vocab['usage']}")
                            st.write(f"💬 **Examples:**")
                            for ex in ai_vocab['examples']:
                                st.write(f"  • {ex['spanish']} = {ex['english']}")

# ============================================================================
# TAB 5: PAPELERÍA
# ============================================================================

with tab5:
    st.subheader("📝 Papelería - Stationery, Printing, Office Supplies")
    
    st.markdown("### 📝 Quick Reference - Top Papelería Words")
    quick_ref_pap = [
        {"spanish": "imprimir", "english": "to print"},
        {"spanish": "laminado", "english": "laminating"},
        {"spanish": "copias", "english": "copies"},
        {"spanish": "cuaderno", "english": "notebook"},
        {"spanish": "lápiz", "english": "pencil"},
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
    pap_query = st.text_input("Search papelería vocabulary:", placeholder="e.g., print, laminate, notebook", key="pap_search")
    
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
                    with st.spinner("Creating vocab entry..."):
                        ai_vocab = get_ai_vocab_response(pap_query, lesson="papeleria")
                        if ai_vocab['spanish'] != 'Error':
                            st.markdown(f"### 🇪🇸 Spanish: **{ai_vocab['spanish']}**")
                            st.markdown(f"### 🇬🇧 English: **{ai_vocab['english']}**")
                            st.write(f"📣 **Pronunciation:** {ai_vocab['pronunciation']}")
                            st.write(f"📚 **Usage:** {ai_vocab['usage']}")
                            st.write(f"💬 **Examples:**")
                            for ex in ai_vocab['examples']:
                                st.write(f"  • {ex['spanish']} = {ex['english']}")

# ============================================================================
# TAB 6: SCHOOL
# ============================================================================

with tab6:
    st.subheader("🎓 School - Uniforms, Activities, Admin, Canteen, Rules")
    
    st.markdown("### 🎓 Quick Reference - Top School Words")
    quick_ref_school = [
        {"spanish": "escuela", "english": "school"},
        {"spanish": "uniforme", "english": "uniform"},
        {"spanish": "cuota", "english": "fee"},
        {"spanish": "maestro", "english": "teacher"},
        {"spanish": "estudiante", "english": "student"},
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
    school_query = st.text_input("Search school vocabulary:", placeholder="e.g., uniform, activity, fee", key="school_search")
    
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
                    with st.spinner("Creating vocab entry..."):
                        ai_vocab = get_ai_vocab_response(school_query, lesson="school")
                        if ai_vocab['spanish'] != 'Error':
                            st.markdown(f"### 🇪🇸 Spanish: **{ai_vocab['spanish']}**")
                            st.markdown(f"### 🇬🇧 English: **{ai_vocab['english']}**")
                            st.write(f"📣 **Pronunciation:** {ai_vocab['pronunciation']}")
                            st.write(f"📚 **Usage:** {ai_vocab['usage']}")
                            st.write(f"💬 **Examples:**")
                            for ex in ai_vocab['examples']:
                                st.write(f"  • {ex['spanish']} = {ex['english']}")

# ============================================================================
# TAB 7: MEASUREMENTS
# ============================================================================

with tab7:
    st.header("📐 Measurements & Quantities")
    st.info("Common measurements used in markets, cooking, and shopping.")
    
    measurements_data = {
        "Fractions & Multiples": [
            {"spanish": "medio", "english": "half", "pronunciation": "MEH-dee-oh", "example_spanish": "Medio kilogramo de café", "example_english": "Half a kilogram of coffee"},
            {"spanish": "cuarto", "english": "quarter", "pronunciation": "KWAR-toh", "example_spanish": "Un cuarto de hora", "example_english": "A quarter of an hour"},
            {"spanish": "doble", "english": "double", "pronunciation": "DOH-bleh", "example_spanish": "Doble ración", "example_english": "Double portion"},
            {"spanish": "mitad", "english": "half", "pronunciation": "mee-TAHD", "example_spanish": "La mitad del precio", "example_english": "Half the price"},
        ],
        "Weight": [
            {"spanish": "gramo", "english": "gram", "pronunciation": "GRAH-moh", "example_spanish": "500 gramos de queso", "example_english": "500 grams of cheese"},
            {"spanish": "kilogramo", "english": "kilogram", "pronunciation": "kee-loh-GRAH-moh", "example_spanish": "Un kilogramo de papa", "example_english": "One kilogram of potato"},
            {"spanish": "onza", "english": "ounce", "pronunciation": "OHN-sah", "example_spanish": "Una onza de oro", "example_english": "One ounce of gold"},
            {"spanish": "libra", "english": "pound", "pronunciation": "LEE-brah", "example_spanish": "Dos libras de pollo", "example_english": "Two pounds of chicken"},
        ],
        "Volume": [
            {"spanish": "litro", "english": "liter", "pronunciation": "LEE-troh", "example_spanish": "Un litro de leche", "example_english": "One liter of milk"},
            {"spanish": "mililitro", "english": "milliliter", "pronunciation": "mee-lee-LEE-troh", "example_spanish": "250 mililitros", "example_english": "250 milliliters"},
            {"spanish": "taza", "english": "cup", "pronunciation": "TAH-sah", "example_spanish": "Una taza de café", "example_english": "One cup of coffee"},
            {"spanish": "cucharada", "english": "tablespoon", "pronunciation": "koo-chah-RAH-dah", "example_spanish": "Una cucharada de azúcar", "example_english": "One tablespoon of sugar"},
            {"spanish": "cucharita", "english": "teaspoon", "pronunciation": "koo-chah-REE-tah", "example_spanish": "Una cucharita de sal", "example_english": "One teaspoon of salt"},
        ],
        "Length": [
            {"spanish": "metro", "english": "meter", "pronunciation": "MEH-troh", "example_spanish": "Dos metros de tela", "example_english": "Two meters of fabric"},
            {"spanish": "centímetro", "english": "centimeter", "pronunciation": "sen-TEE-meh-troh", "example_spanish": "5 centímetros", "example_english": "5 centimeters"},
            {"spanish": "kilómetro", "english": "kilometer", "pronunciation": "kee-LOH-meh-troh", "example_spanish": "10 kilómetros de distancia", "example_english": "10 kilometers away"},
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
    st.header("⏰ Time & Dates")
    st.info("Words for telling time, days, months, and time expressions.")
    
    time_data = {
        "Time Units": [
            {"spanish": "hora", "english": "hour", "pronunciation": "OH-rah", "example_spanish": "Una hora de espera", "example_english": "One hour of waiting"},
            {"spanish": "minuto", "english": "minute", "pronunciation": "mee-NOO-toh", "example_spanish": "Cinco minutos", "example_english": "Five minutes"},
            {"spanish": "segundo", "english": "second", "pronunciation": "seh-GOON-doh", "example_spanish": "Un segundo", "example_english": "One second"},
        ],
        "Days": [
            {"spanish": "lunes", "english": "Monday", "pronunciation": "LOO-nes", "example_spanish": "Nos vemos el lunes", "example_english": "See you on Monday"},
            {"spanish": "martes", "english": "Tuesday", "pronunciation": "MAR-tes", "example_spanish": "Cita el martes", "example_english": "Appointment on Tuesday"},
            {"spanish": "miércoles", "english": "Wednesday", "pronunciation": "MYER-koh-les", "example_spanish": "Reunión el miércoles", "example_english": "Meeting on Wednesday"},
            {"spanish": "jueves", "english": "Thursday", "pronunciation": "HWAY-ves", "example_spanish": "Clase el jueves", "example_english": "Class on Thursday"},
            {"spanish": "viernes", "english": "Friday", "pronunciation": "vee-EHR-nes", "example_spanish": "Pago el viernes", "example_english": "Payment on Friday"},
            {"spanish": "sábado", "english": "Saturday", "pronunciation": "SAH-bah-doh", "example_spanish": "Mercado el sábado", "example_english": "Market on Saturday"},
            {"spanish": "domingo", "english": "Sunday", "pronunciation": "doh-MEEN-goh", "example_spanish": "Iglesia el domingo", "example_english": "Church on Sunday"},
        ],
        "Months": [
            {"spanish": "enero", "english": "January", "pronunciation": "eh-NEH-roh", "example_spanish": "Enero es frío", "example_english": "January is cold"},
            {"spanish": "febrero", "english": "February", "pronunciation": "feh-BREH-roh", "example_spanish": "En febrero", "example_english": "In February"},
            {"spanish": "marzo", "english": "March", "pronunciation": "MAR-soh", "example_spanish": "Marzo es primavera", "example_english": "March is spring"},
            {"spanish": "abril", "english": "April", "pronunciation": "ah-BREEL", "example_spanish": "Lluvias en abril", "example_english": "Rain in April"},
            {"spanish": "mayo", "english": "May", "pronunciation": "MAH-yoh", "example_spanish": "Mayo es hermoso", "example_english": "May is beautiful"},
            {"spanish": "junio", "english": "June", "pronunciation": "HOO-nee-oh", "example_spanish": "Junio comienza el verano", "example_english": "June begins summer"},
            {"spanish": "julio", "english": "July", "pronunciation": "HOO-lee-oh", "example_spanish": "Julio es caluroso", "example_english": "July is hot"},
            {"spanish": "agosto", "english": "August", "pronunciation": "ah-GOST-oh", "example_spanish": "Vacaciones en agosto", "example_english": "Vacation in August"},
            {"spanish": "septiembre", "english": "September", "pronunciation": "sep-tee-EHM-breh", "example_spanish": "Escuela en septiembre", "example_english": "School in September"},
            {"spanish": "octubre", "english": "October", "pronunciation": "ok-TOO-breh", "example_spanish": "Octubre es otoño", "example_english": "October is autumn"},
            {"spanish": "noviembre", "english": "November", "pronunciation": "noh-vee-EHM-breh", "example_spanish": "Noviembre", "example_english": "November"},
            {"spanish": "diciembre", "english": "December", "pronunciation": "dee-see-EHM-breh", "example_spanish": "Navidad en diciembre", "example_english": "Christmas in December"},
        ],
        "Time Expressions": [
            {"spanish": "ahora", "english": "now", "pronunciation": "ah-OH-rah", "example_spanish": "¿Qué hora es ahora?", "example_english": "What time is it now?"},
            {"spanish": "hoy", "english": "today", "pronunciation": "OY", "example_spanish": "Hoy es lunes", "example_english": "Today is Monday"},
            {"spanish": "mañana", "english": "tomorrow", "pronunciation": "mah-NYAH-nah", "example_spanish": "Mañana es martes", "example_english": "Tomorrow is Tuesday"},
            {"spanish": "ayer", "english": "yesterday", "pronunciation": "ah-YEH", "example_spanish": "Ayer fue domingo", "example_english": "Yesterday was Sunday"},
            {"spanish": "semana", "english": "week", "pronunciation": "seh-MAH-nah", "example_spanish": "Próxima semana", "example_english": "Next week"},
            {"spanish": "mes", "english": "month", "pronunciation": "mes", "example_spanish": "El mes pasado", "example_english": "Last month"},
            {"spanish": "año", "english": "year", "pronunciation": "AH-nyoh", "example_spanish": "El próximo año", "example_english": "Next year"},
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
    st.header("🔢 Numbers")
    st.info("Spanish numbers from 0 to beyond 1 million.")
    
    numbers_data = {
        "0-10": [
            {"spanish": "cero", "english": "zero", "pronunciation": "SEH-roh", "example_spanish": "Cero pesos", "example_english": "Zero pesos"},
            {"spanish": "uno", "english": "one", "pronunciation": "OO-noh", "example_spanish": "Un kilogramo", "example_english": "One kilogram"},
            {"spanish": "dos", "english": "two", "pronunciation": "dohs", "example_spanish": "Dos personas", "example_english": "Two people"},
            {"spanish": "tres", "english": "three", "pronunciation": "tres", "example_spanish": "Tres manzanas", "example_english": "Three apples"},
            {"spanish": "cuatro", "english": "four", "pronunciation": "KWAH-troh", "example_spanish": "Cuatro hijos", "example_english": "Four children"},
            {"spanish": "cinco", "english": "five", "pronunciation": "SEEN-koh", "example_spanish": "Cinco dólares", "example_english": "Five dollars"},
            {"spanish": "seis", "english": "six", "pronunciation": "says", "example_spanish": "Seis días", "example_english": "Six days"},
            {"spanish": "siete", "english": "seven", "pronunciation": "see-EH-teh", "example_spanish": "Siete noches", "example_english": "Seven nights"},
            {"spanish": "ocho", "english": "eight", "pronunciation": "OH-choh", "example_spanish": "Ocho años", "example_english": "Eight years"},
            {"spanish": "nueve", "english": "nine", "pronunciation": "noo-EH-veh", "example_spanish": "Nueve horas", "example_english": "Nine hours"},
            {"spanish": "diez", "english": "ten", "pronunciation": "dee-es", "example_spanish": "Diez pesos", "example_english": "Ten pesos"},
        ],
        "11-20": [
            {"spanish": "once", "english": "eleven", "pronunciation": "OHN-seh", "example_spanish": "Once libros", "example_english": "Eleven books"},
            {"spanish": "doce", "english": "twelve", "pronunciation": "DOH-seh", "example_spanish": "Doce meses", "example_english": "Twelve months"},
            {"spanish": "trece", "english": "thirteen", "pronunciation": "TREH-seh", "example_spanish": "Trece pesos", "example_english": "Thirteen pesos"},
            {"spanish": "catorce", "english": "fourteen", "pronunciation": "kah-TOR-seh", "example_spanish": "Catorce días", "example_english": "Fourteen days"},
            {"spanish": "quince", "english": "fifteen", "pronunciation": "KEEN-seh", "example_spanish": "Quince minutos", "example_english": "Fifteen minutes"},
            {"spanish": "dieciséis", "english": "sixteen", "pronunciation": "dee-eh-see-SAYS", "example_spanish": "Dieciséis años", "example_english": "Sixteen years"},
            {"spanish": "diecisiete", "english": "seventeen", "pronunciation": "dee-eh-see-see-EH-teh", "example_spanish": "Diecisiete estudiantes", "example_english": "Seventeen students"},
            {"spanish": "dieciocho", "english": "eighteen", "pronunciation": "dee-eh-see-OH-choh", "example_spanish": "Dieciocho pesos", "example_english": "Eighteen pesos"},
            {"spanish": "diecinueve", "english": "nineteen", "pronunciation": "dee-eh-see-noo-EH-veh", "example_spanish": "Diecinueve personas", "example_english": "Nineteen people"},
            {"spanish": "veinte", "english": "twenty", "pronunciation": "VAYN-teh", "example_spanish": "Veinte años", "example_english": "Twenty years"},
        ],
        "Tens & Hundreds": [
            {"spanish": "treinta", "english": "thirty", "pronunciation": "TRAYN-tah", "example_spanish": "Treinta y cinco", "example_english": "Thirty-five"},
            {"spanish": "cuarenta", "english": "forty", "pronunciation": "kwah-REHN-tah", "example_spanish": "Cuarenta kilos", "example_english": "Forty kilos"},
            {"spanish": "cincuenta", "english": "fifty", "pronunciation": "seen-KWEHN-tah", "example_spanish": "Cincuenta pesos", "example_english": "Fifty pesos"},
            {"spanish": "sesenta", "english": "sixty", "pronunciation": "seh-SEHN-tah", "example_spanish": "Sesenta minutos", "example_english": "Sixty minutes"},
            {"spanish": "setenta", "english": "seventy", "pronunciation": "seh-TEHN-tah", "example_spanish": "Setenta y dos", "example_english": "Seventy-two"},
            {"spanish": "ochenta", "english": "eighty", "pronunciation": "oh-CHEHN-tah", "example_spanish": "Ochenta y ocho", "example_english": "Eighty-eight"},
            {"spanish": "noventa", "english": "ninety", "pronunciation": "noh-VEHN-tah", "example_spanish": "Noventa y nueve", "example_english": "Ninety-nine"},
            {"spanish": "cien", "english": "one hundred", "pronunciation": "see-en", "example_spanish": "Cien pesos", "example_english": "One hundred pesos"},
            {"spanish": "mil", "english": "one thousand", "pronunciation": "meel", "example_spanish": "Mil pesos", "example_english": "One thousand pesos"},
            {"spanish": "millón", "english": "one million", "pronunciation": "mee-YOHN", "example_spanish": "Un millón de pesos", "example_english": "One million pesos"},
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
    st.header("💰 Money & Payment")
    st.info("Currency, payment methods, and money-related vocabulary.")
    
    money_data = {
        "Currency": [
            {"spanish": "peso", "english": "peso (Mexican currency)", "pronunciation": "PEH-soh", "example_spanish": "¿Cuántos pesos?", "example_english": "How many pesos?"},
            {"spanish": "centavo", "english": "cent (1/100 of peso)", "pronunciation": "sen-TAH-voh", "example_spanish": "50 centavos", "example_english": "50 cents"},
            {"spanish": "moneda", "english": "coin", "pronunciation": "moh-NEH-dah", "example_spanish": "Una moneda de 5 pesos", "example_english": "A 5-peso coin"},
            {"spanish": "billete", "english": "bill/note", "pronunciation": "bee-YEH-teh", "example_spanish": "Billete de 500 pesos", "example_english": "500-peso bill"},
            {"spanish": "dólar", "english": "dollar", "pronunciation": "DOH-lar", "example_spanish": "Cien dólares", "example_english": "One hundred dollars"},
        ],
        "Payment": [
            {"spanish": "dinero", "english": "money", "pronunciation": "dee-NEH-roh", "example_spanish": "¿Cuánto dinero?", "example_english": "How much money?"},
            {"spanish": "precio", "english": "price", "pronunciation": "PREH-see-oh", "example_spanish": "¿Cuál es el precio?", "example_english": "What's the price?"},
            {"spanish": "costo", "english": "cost", "pronunciation": "KOS-toh", "example_spanish": "El costo total", "example_english": "The total cost"},
            {"spanish": "pago", "english": "payment", "pronunciation": "PAH-goh", "example_spanish": "Método de pago", "example_english": "Payment method"},
            {"spanish": "cambio", "english": "change", "pronunciation": "KAHM-bee-oh", "example_spanish": "¿Me das el cambio?", "example_english": "Can you give me the change?"},
            {"spanish": "factura", "english": "invoice/receipt", "pronunciation": "fahk-TOO-rah", "example_spanish": "Dame la factura", "example_english": "Give me the receipt"},
            {"spanish": "tarjeta", "english": "card", "pronunciation": "tar-HEH-tah", "example_spanish": "Tarjeta de crédito", "example_english": "Credit card"},
            {"spanish": "efectivo", "english": "cash", "pronunciation": "eh-fehk-TEE-voh", "example_spanish": "Pago en efectivo", "example_english": "Cash payment"},
        ],
        "Financial Terms": [
            {"spanish": "descuento", "english": "discount", "pronunciation": "des-KWEHN-toh", "example_spanish": "10% de descuento", "example_english": "10% discount"},
            {"spanish": "propina", "english": "tip", "pronunciation": "proh-PEE-nah", "example_spanish": "Una propina de 20 pesos", "example_english": "A 20-peso tip"},
            {"spanish": "préstamo", "english": "loan", "pronunciation": "PREHS-tah-moh", "example_spanish": "Solicitar un préstamo", "example_english": "Request a loan"},
            {"spanish": "interés", "english": "interest", "pronunciation": "een-teh-RES", "example_spanish": "Interés bancario", "example_english": "Bank interest"},
            {"spanish": "impuesto", "english": "tax", "pronunciation": "eem-PWES-toh", "example_spanish": "Impuesto sobre ventas", "example_english": "Sales tax"},
        ],
    }
    
    for category, items in money_data.items():
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
✨ 10 tabs | 📚 15 verbs | 🇪🇸🇬🇧 Bilingual content | 📐 Essentials (Measurements, Time, Numbers, Money)  
🤖 Structured AI vocab generation (Spanish + English + pronunciation + usage + examples)  
Built with ❤️ for Querétaro expats | November 2026
""")
