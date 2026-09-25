"""
Contexto: AI-Powered Language Learning for Expats
Priority Updates: Tab reordering, Quick Ref, GIFs, English, Expanded Grammar
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
# TABS - REORDERED (Conversations first)
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["💬 Conversations", "📚 Grammar", "🏪 Market", "🏥 Hospital", "📝 Papelería", "🎓 School"])

# ============================================================================
# TAB 1: CONVERSATIONS (WITH GIFS + ENGLISH)
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
        
        # GIF for market
        st.image("https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif", width=400)
        
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
            
            st.info("💡 **Key phrases:** Spice pricing, haggling tactics, comparing vendors, bulk discounts")
        
        with st.expander("**Dialogue 3: Buying Fresh Produce**"):
            st.markdown("### 🇪🇸 Spanish:")
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
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** How much is the fresh cilantro?  
**Vendor:** 15 pesos per bunch.  
**Jasmine:** Do you have romaine lettuce today?  
**Vendor:** Yes, very fresh. Just arrived this morning. 12 pesos each.  
**Jasmine:** Give me three lettuces and two bunches of cilantro. And tomatoes?  
**Vendor:** I have red tomatoes and cherry tomatoes. The cherry tomatoes are better right now. 25 pesos per kilo.  
**Jasmine:** Okay, give me a kilo of cherry tomatoes and two white onions.  
**Vendor:** Perfect. That's 50 pesos for tomatoes, 15 for onions... 85 pesos total.  
**Jasmine:** Is everything fresh?  
**Vendor:** Guaranteed. If not, you come back tomorrow and I'll change it all.
            """)
            
            st.info("💡 **Key phrases:** Vegetable types, freshness indicators, bulk quantities, pricing")
        
        with st.expander("**Dialogue 4: Comparing Prices & Making Deals**"):
            st.markdown("### 🇪🇸 Spanish:")
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
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Is this the best price for dried chiles?  
**Vendor:** What did they ask you somewhere else?  
**Jasmine:** 80 pesos per handful.  
**Vendor:** Look, I'll give you 70 pesos, but you have to buy minimum three handfuls.  
**Jasmine:** That's 210 pesos. Do the bags come included?  
**Vendor:** Of course, they come with bags.  
**Jasmine:** What varieties do you have?  
**Vendor:** Guajillo, ancho, chipotle, and pasilla.  
**Jasmine:** Give me one of each. Any other products you recommend?  
**Vendor:** The epazote from this region is excellent. 20 pesos a bunch.  
**Jasmine:** Okay, add two bunches. How much is everything?  
**Vendor:** Three handfuls of chiles, 70 each, plus two epazote... that's 250 pesos. I'll give you the cilantro bunch free because you're a new customer.
            """)
            
            st.info("💡 **Key phrases:** Price comparison, bulk pricing, product varieties, customer loyalty")
    
    elif selected_lesson == "Hospital":
        st.subheader("🏥 Hospital Conversations - Medical Care")
        
        # GIF for hospital
        st.image("https://media.giphy.com/media/l0HlNaQ9L61wJm1PE/giphy.gif", width=400)
        
        with st.expander("**Dialogue 1: Calling for an Appointment**"):
            st.markdown("### 🇪🇸 Spanish:")
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
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Jasmine:** Hi, good morning. I need an appointment with the doctor.  
**Receptionist:** What is your problem or symptom?  
**Jasmine:** I've had a headache and fever for two days.  
**Receptionist:** Do you have health insurance?  
**Jasmine:** Yes, I have Seguros Monterrey New York Life.  
**Receptionist:** Perfect. Doctor García is available today at 4 PM, or tomorrow at 10 AM.  
**Jasmine:** I prefer today at 4. What's the consultation cost?  
**Receptionist:** With your insurance, you only pay 300 pesos copay.  
**Jasmine:** Okay, I confirm for today at 4. Do I need to bring anything?  
**Receptionist:** Bring your insurance and an ID. Arrive 10 minutes early.
            """)
            
            st.info("💡 **Key phrases:** Symptoms, insurance types, copay, appointment scheduling")
        
        with st.expander("**Dialogue 2: Visiting the Doctor**"):
            st.markdown("### 🇪🇸 Spanish:")
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
            
            st.markdown("### 🇬🇧 English:")
            st.markdown("""
**Doctor:** Good morning, Jasmine. What's the problem?  
**Jasmine:** I have fever, headache, and I'm very tired.  
**Doctor:** When did it start?  
**Jasmine:** Two days ago. I also have a sore throat.  
**Doctor:** I'm going to examine you. Open your mouth, please. Now cough. Does it hurt to swallow?  
**Jasmine:** Yes, a lot. And I'm cold, even though I have fever.  
**Doctor:** It's probably a viral infection. I'm going to do a quick test.  
**Jasmine:** What do you recommend?  
**Doctor:** Rest, lots of water, and these medicines. Take paracetamol every 6 hours.  
**Jasmine:** How many days should I miss work?  
**Doctor:** Minimum 3 days. Then come back if you don't improve.
            """)
            
            st.info("💡 **Key phrases:** Symptoms, medical examination, diagnosis, medication instructions")

    elif selected_lesson == "Papelería":
        st.subheader("📝 Papelería Conversations - Office & Printing")
        
        # GIF for office
        st.image("https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif", width=400)
        
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
            
            st.info("💡 **Key phrases:** Printing services, page costs, laminating, binding options")

    else:  # School
        st.subheader("🎓 School Conversations - Education & Administration")
        
        # GIF for school
        st.image("https://media.giphy.com/media/l0HlKt7snLsrwxhlm/giphy.gif", width=400)
        
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
**Director:** 1,500 pesos. Incluye libros, materiales, y seguro escolar.
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
**Director:** 1,500 pesos. Includes books, materials, and school insurance.
            """)
            
            st.info("💡 **Key phrases:** Registration documents, admission process, enrollment fees")

# ============================================================================
# TAB 2: GRAMMAR (EXPANDED TO 15 VERBS)
# ============================================================================

with tab2:
    st.header("📚 Spanish Verb Conjugations - Present Tense")
    st.info("Learn verbs used in Contexto conversations. All 6 persons shown.")
    
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
        },
        "Costar (To Cost)": {
            "yo": "cuesta",
            "tú": "cuesta",
            "él/ella/usted": "cuesta",
            "nosotros": "cuesta",
            "vosotros": "cuesta",
            "ellos/ellas/ustedes": "cuestan",
            "example": "¿Cuánto cuesta? = How much does it cost?"
        },
        "Dar (To Give)": {
            "yo": "doy",
            "tú": "das",
            "él/ella/usted": "da",
            "nosotros": "damos",
            "vosotros": "dais",
            "ellos/ellas/ustedes": "dan",
            "example": "Te doy 70 pesos = I give you 70 pesos"
        },
        "Pedir (To Ask For/Request)": {
            "yo": "pido",
            "tú": "pides",
            "él/ella/usted": "pide",
            "nosotros": "pedimos",
            "vosotros": "pedís",
            "ellos/ellas/ustedes": "piden",
            "example": "¿Cuánto me pides? = How much do you ask for?"
        },
        "Incluir (To Include)": {
            "yo": "incluyo",
            "tú": "incluyes",
            "él/ella/usted": "incluye",
            "nosotros": "incluimos",
            "vosotros": "incluís",
            "ellos/ellas/ustedes": "incluyen",
            "example": "Incluye los libros = It includes the books"
        },
        "Aceptar (To Accept)": {
            "yo": "acepto",
            "tú": "aceptas",
            "él/ella/usted": "acepta",
            "nosotros": "aceptamos",
            "vosotros": "aceptáis",
            "ellos/ellas/ustedes": "aceptan",
            "example": "¿Qué métodos de pago aceptan? = What payment methods do you accept?"
        },
        "Llamar (To Call)": {
            "yo": "llamo",
            "tú": "llamas",
            "él/ella/usted": "llama",
            "nosotros": "llamamos",
            "vosotros": "llamáis",
            "ellos/ellas/ustedes": "llaman",
            "example": "Te llamamos en una hora = We'll call you in an hour"
        },
        "Empezar (To Start)": {
            "yo": "empiezo",
            "tú": "empiezas",
            "él/ella/usted": "empieza",
            "nosotros": "empezamos",
            "vosotros": "empezáis",
            "ellos/ellas/ustedes": "empiezan",
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
# TAB 3: MARKET (WITH QUICK REF)
# ============================================================================

with tab3:
    st.subheader("Market (La Cruz) - Shopping, Haggling, Groceries")
    
    # QUICK REFERENCE (TOP 15 WORDS)
    st.markdown("### 🏪 Quick Reference - Top Market Words")
    
    quick_ref_market = [
        {"spanish": "pescado", "english": "fish"},
        {"spanish": "fresco", "english": "fresh"},
        {"spanish": "precio", "english": "price"},
        {"spanish": "cúrcuma", "english": "turmeric"},
        {"spanish": "descuento", "english": "discount"},
        {"spanish": "mercado", "english": "market"},
        {"spanish": "kilogramo", "english": "kilogram"},
        {"spanish": "negociar", "english": "negotiate"},
        {"spanish": "caro", "english": "expensive"},
        {"spanish": "barato", "english": "cheap"},
        {"spanish": "vendedor", "english": "vendor"},
        {"spanish": "comprar", "english": "to buy"},
        {"spanish": "verdura", "english": "vegetable"},
        {"spanish": "especias", "english": "spices"},
        {"spanish": "cantidad", "english": "quantity"},
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
        
        if has_groq:
            if st.button(f"💡 Get AI help with '{market_query}'", key="market_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(market_query, lesson="market")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 4: HOSPITAL (WITH QUICK REF)
# ============================================================================

with tab4:
    st.subheader("Hospital - Medical Appointments, Specialists, Insurance")
    
    # QUICK REFERENCE
    st.markdown("### 🏥 Quick Reference - Top Hospital Words")
    
    quick_ref_hospital = [
        {"spanish": "doctor", "english": "doctor"},
        {"spanish": "fiebre", "english": "fever"},
        {"spanish": "dolor", "english": "pain"},
        {"spanish": "cita", "english": "appointment"},
        {"spanish": "medicina", "english": "medicine"},
        {"spanish": "seguro", "english": "insurance"},
        {"spanish": "síntoma", "english": "symptom"},
        {"spanish": "garganta", "english": "throat"},
        {"spanish": "copago", "english": "copay"},
        {"spanish": "farmacia", "english": "pharmacy"},
        {"spanish": "enfermera", "english": "nurse"},
        {"spanish": "receta", "english": "prescription"},
        {"spanish": "tratamiento", "english": "treatment"},
        {"spanish": "especialista", "english": "specialist"},
        {"spanish": "cansado", "english": "tired"},
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
        
        if has_groq:
            if st.button(f"💡 Get AI help with '{hospital_query}'", key="hospital_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(hospital_query, lesson="hospital")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 5: PAPELERÍA (WITH QUICK REF)
# ============================================================================

with tab5:
    st.subheader("Papelería - Stationery, Printing, Office Supplies")
    
    # QUICK REFERENCE
    st.markdown("### 📝 Quick Reference - Top Papelería Words")
    
    quick_ref_pap = [
        {"spanish": "imprimir", "english": "to print"},
        {"spanish": "laminado", "english": "laminating"},
        {"spanish": "copias", "english": "copies"},
        {"spanish": "encuadernación", "english": "binding"},
        {"spanish": "cuaderno", "english": "notebook"},
        {"spanish": "lápiz", "english": "pencil"},
        {"spanish": "papel", "english": "paper"},
        {"spanish": "costo", "english": "cost"},
        {"spanish": "página", "english": "page"},
        {"spanish": "mochila", "english": "backpack"},
        {"spanish": "goma", "english": "eraser"},
        {"spanish": "marcadores", "english": "markers"},
        {"spanish": "regla", "english": "ruler"},
        {"spanish": "servicio", "english": "service"},
        {"spanish": "tiempo", "english": "time"},
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
        
        if has_groq:
            if st.button(f"💡 Get AI help with '{pap_query}'", key="pap_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(pap_query, lesson="papeleria")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 6: SCHOOL (WITH QUICK REF)
# ============================================================================

with tab6:
    st.subheader("School - Uniforms, Activities, Admin, Canteen, Rules")
    
    # QUICK REFERENCE
    st.markdown("### 🎓 Quick Reference - Top School Words")
    
    quick_ref_school = [
        {"spanish": "escuela", "english": "school"},
        {"spanish": "uniforme", "english": "uniform"},
        {"spanish": "cuota", "english": "fee"},
        {"spanish": "inscripción", "english": "registration"},
        {"spanish": "actividad", "english": "activity"},
        {"spanish": "maestro", "english": "teacher"},
        {"spanish": "estudiante", "english": "student"},
        {"spanish": "grado", "english": "grade"},
        {"spanish": "calificaciones", "english": "grades"},
        {"spanish": "materia", "english": "subject"},
        {"spanish": "tutoría", "english": "tutoring"},
        {"spanish": "admisión", "english": "admission"},
        {"spanish": "director", "english": "principal"},
        {"spanish": "comida", "english": "food/lunch"},
        {"spanish": "pago", "english": "payment"},
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
        
        if has_groq:
            if st.button(f"💡 Get AI help with '{school_query}'", key="school_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(school_query, lesson="school")
                    if ai_response:
                        st.info(ai_response)

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
✨ Reordered tabs | 📖 Quick References | 🖼️ Scene GIFs | 📚 15 Verbs | 🔤 English translations  
Built with ❤️ for Querétaro expats | November 2026
""")
