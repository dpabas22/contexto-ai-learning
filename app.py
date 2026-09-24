"""
Contexto: AI-Powered Language Learning for Expats
Market Spanish Learning with RAG
"""

import streamlit as st
import json
import os
from pathlib import Path

# Configure Streamlit
st.set_page_config(
    page_title="Contexto - Market Spanish",
    page_icon="🌍",
    layout="wide"
)

from groq import Groq
from gtts import gTTS
import io

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
# SECURITY: Load environment variables safely
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Check if API key exists (fail gracefully)
has_groq = GROQ_API_KEY is not None

if has_groq:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        has_groq = False
        st.warning("⚠️ Groq API connection failed. Using vocab-only mode.")

# ============================================================================
# LOAD VOCABULARY DATA (All 4 lessons)
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
# SECURITY: Input validation
# ============================================================================

def sanitize_input(text):
    """Prevent injection attacks"""
    if not text:
        return ""
    # Limit length (prevent DoS)
    if len(text) > 500:
        return text[:500]
    # Remove dangerous characters
    text = text.replace("<", "").replace(">", "").replace("&", "")
    return text.strip()

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def search_vocabulary(query, lesson=None):
    """Search vocabulary with optional lesson filter"""
    query = sanitize_input(query).lower()
    
    if not query:
        return []
    
    results = []
    
    # Search in specific lesson or all lessons
    lessons_to_search = [lesson] if lesson else vocab_data.keys()
    
    for lesson_name in lessons_to_search:
        if lesson_name not in vocab_data:
            continue
            
        vocab_list = vocab_data[lesson_name].get('vocabulary', [])
        
        for item in vocab_list:
            spanish = item.get('spanish', '').lower()
            english = item.get('english', '').lower()
            
            # Match on Spanish or English
            if query in spanish or query in english:
                # Add lesson context to item
                item_copy = item.copy()
                item_copy['lesson'] = lesson_name
                results.append(item_copy)
    
    return results

def get_ai_response(query, lesson="", context=""):
    """Get AI response from Groq with lesson context"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "⚠️ API key not configured. Please add GROQ_API_KEY to Streamlit Secrets."
        
        client = Groq(api_key=api_key)
        
        # Build lesson context
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
# STREAMLIT UI - WITH CONVERSATIONS & GRAMMAR
# ============================================================================

# Configure page
st.title("🌍 Contexto: Language Learning for Real Expat Needs")
st.markdown("**Learn Spanish through real conversations in Querétaro**")

st.info("""
✅ **Querétaro-Specific Content:** Market (La Cruz), Hospital, Papelería, School  
⚠️ **Generic Responses:** Questions outside these 4 topics use general knowledge  
📅 **Phase 2 Roadmap:** Restaurants, neighborhoods, transportation, shopping
""")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏪 Market", "💬 Conversations", "🏥 Hospital", "📝 Papelería", "🎓 School", "📚 Grammar"])

# ============================================================================
# TAB 1: MARKET (Vocab Search)
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
                    col_audio1, col_audio2 = st.columns([1, 4])
                    with col_audio1:
                        if st.button("🔊", key=f"market_word_{item['id']}", help="Hear pronunciation"):
                            audio = create_audio(item['spanish'], lang='es')
                            if audio:
                                st.audio(audio, format='audio/mp3')
                    with col_audio2:
                        st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    
                    if st.button("▶️", key=f"market_ex_{item['id']}", help="Hear example"):
                        audio = create_audio(item['example_spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
        
        else:
            st.warning("❌ No results found.")
        
        # AI BUTTON (OUTSIDE if/else - correct indentation)
        if has_groq:
            if st.button(f"💡 Get AI help with '{market_query}'", key="market_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(market_query, lesson="market")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 2: CONVERSATIONS (16 Dialogues - All 4 Lessons)
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
            
            st.markdown("**English Translation:**")
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
            
            st.markdown("**English Translation:**")
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
            
            st.info("💡 **Key phrases:** Spice pricing, haggling tactics, comparing vendors, bulk discounts, quality indicators")
        
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
            
            st.markdown("**English Translation:**")
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
            
            st.info("💡 **Key phrases:** Vegetable types, freshness indicators, bulk quantities, pricing, guarantee")
        
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
            
            st.markdown("**English Translation:**")
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
            
            st.info("💡 **Key phrases:** Price comparison, bulk pricing, product varieties, seasonal items, customer loyalty")
    
    elif selected_lesson == "Hospital":
        st.subheader("🏥 Hospital Conversations - Medical Care")
        
        with st.expander("**Dialogue 1: Calling for an Appointment**"):
            st.markdown("""
**Jasmine:** Hola, buenos días. Necesito una cita con el doctor.  
**Receptionist:** ¿Cuál es tu problema o síntoma?  
**Jasmine:** Tengo dolor de cabeza y fiebre desde hace dos días.  
**Receptionist:** ¿Tienes seguro médico?  
**Jasmine:** Sí, tengo Seguros Monterrey New York Life.  
**Receptionist:** Perfecto. El doctor García tiene disponibilidad hoy a las 4 de la tarde, o mañana a las 10 de la mañana. ¿Cuál prefieres?  
**Jasmine:** Prefiero hoy a las 4. ¿Cuál es el costo de la consulta?  
**Receptionist:** Con tu seguro, solo pagas 300 pesos de copago. Sin seguro sería 800 pesos.  
**Jasmine:** Dale, confirmo para hoy a las 4. ¿Necesito traer algo?  
**Receptionist:** Trae tu seguro y una identificación. Llega 10 minutos antes.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, good morning. I need an appointment with the doctor.  
**Receptionist:** What is your problem or symptom?  
**Jasmine:** I've had a headache and fever for two days.  
**Receptionist:** Do you have health insurance?  
**Jasmine:** Yes, I have Seguros Monterrey New York Life.  
**Receptionist:** Perfect. Doctor García is available today at 4 PM, or tomorrow at 10 AM. Which do you prefer?  
**Jasmine:** I prefer today at 4. What's the consultation cost?  
**Receptionist:** With your insurance, you only pay 300 pesos copay. Without insurance it would be 800 pesos.  
**Jasmine:** Okay, I confirm for today at 4. Do I need to bring anything?  
**Receptionist:** Bring your insurance and an ID. Arrive 10 minutes early.
            """)
            
            st.info("💡 **Key phrases:** Symptoms, insurance types, copay, appointment scheduling, required documents")
        
        with st.expander("**Dialogue 2: Visiting the Doctor**"):
            st.markdown("""
**Doctor:** Buenos días, Jasmine. ¿Cuál es el problema?  
**Jasmine:** Tengo fiebre, dolor de cabeza y estoy muy cansada.  
**Doctor:** ¿Cuándo empezó?  
**Jasmine:** Hace dos días. También tengo dolor en la garganta.  
**Doctor:** Voy a revisarte. Abre la boca, por favor. Ahora tose. ¿Te duele al tragar?  
**Jasmine:** Sí, mucho. Y tengo frío, aunque tengo fiebre.  
**Doctor:** Probablemente es una infección viral. Voy a hacer un test rápido para descartar bacteria.  
**Jasmine:** ¿Qué me recomienda?  
**Doctor:** Reposo, mucha agua, y estos medicamentos. Toma paracetamol cada 6 horas para la fiebre.  
**Jasmine:** ¿Cuántos días debo faltar al trabajo?  
**Doctor:** Mínimo 3 días. Luego vuelves si no mejoras.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Doctor:** Good morning, Jasmine. What's the problem?  
**Jasmine:** I have fever, headache, and I'm very tired.  
**Doctor:** When did it start?  
**Jasmine:** Two days ago. I also have a sore throat.  
**Doctor:** I'm going to examine you. Open your mouth, please. Now cough. Does it hurt to swallow?  
**Jasmine:** Yes, a lot. And I'm cold, even though I have fever.  
**Doctor:** It's probably a viral infection. I'm going to do a quick test to rule out bacteria.  
**Jasmine:** What do you recommend?  
**Doctor:** Rest, lots of water, and these medicines. Take paracetamol every 6 hours for the fever.  
**Jasmine:** How many days should I miss work?  
**Doctor:** Minimum 3 days. Then come back if you don't improve.
            """)
            
            st.info("💡 **Key phrases:** Symptoms explanation, medical examination, diagnosis, medication instructions, rest period")
        
        with st.expander("**Dialogue 3: Pharmacy & Prescriptions**"):
            st.markdown("""
**Jasmine:** Buenas tardes. Tengo esta receta. ¿Tienen todos estos medicamentos?  
**Pharmacist:** A ver... sí, tenemos paracetamol 500mg, amoxicilina, y este jarabe. ¿De qué marca prefieres el paracetamol?  
**Jasmine:** La marca que recomendó el doctor, si la tienen.  
**Pharmacist:** Perfecto. El total es 450 pesos. ¿Cómo prefieres pagar?  
**Jasmine:** Tarjeta de crédito, por favor.  
**Pharmacist:** Aquí están. Toma una bolsa. El paracetamol cada 6 horas, la amoxicilina cada 8 horas, y el jarabe cada 12 horas.  
**Jasmine:** ¿Tengo que tomar esto con comida?  
**Pharmacist:** La amoxicilina es mejor con comida. El paracetamol puede ser con o sin comida. ¿Alguna alergia conocida?  
**Jasmine:** No, soy alérgica a la penicilina, pero veo que está en la receta.  
**Pharmacist:** Espera, esto es amoxicilina que tiene penicilina. Tenemos alternativa. Vamos a cambiar.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Good afternoon. I have this prescription. Do you have all these medications?  
**Pharmacist:** Let me see... yes, we have paracetamol 500mg, amoxicillin, and this syrup. What brand do you prefer for paracetamol?  
**Jasmine:** The brand the doctor recommended, if you have it.  
**Pharmacist:** Perfect. The total is 450 pesos. How do you want to pay?  
**Jasmine:** Credit card, please.  
**Pharmacist:** Here you go. Take a bag. Paracetamol every 6 hours, amoxicillin every 8 hours, and syrup every 12 hours.  
**Jasmine:** Do I have to take this with food?  
**Pharmacist:** Amoxicillin is better with food. Paracetamol can be with or without food. Any known allergies?  
**Jasmine:** No, I'm allergic to penicillin, but I see that's in the prescription.  
**Pharmacist:** Wait, this amoxicillin has penicillin. We have an alternative. Let's change it.
            """)
            
            st.info("💡 **Key phrases:** Prescriptions, medication instructions, dosages, food interactions, allergies")
        
        with st.expander("**Dialogue 4: Specialist Referral**"):
            st.markdown("""
**Jasmine:** Doctor, tengo dudas sobre mi vista. Veo borroso frecuentemente.  
**Doctor:** Debes ver a un oftalmólogo. Te doy una referencia.  
**Jasmine:** ¿Dónde puedo encontrar un oftalmólogo? ¿Mi seguro cubre esto?  
**Doctor:** Sí, tu seguro cubre. Te recomiendo a la Dra. Sánchez. Ella trabaja en Clínica Ángeles, que está en Avenida Universidad.  
**Jasmine:** ¿Cuál es el teléfono?  
**Doctor:** Aquí está. Di que vienes por referencia mía. No necesitas copago adicional.  
**Jasmine:** ¿Cuánto tiempo espero para la cita?  
**Doctor:** Normalmente una semana. Pero llama hoy y pregunta si hay cancelación.  
**Jasmine:** Gracias, doctor. ¿Necesito algún otro especialista?  
**Doctor:** No por ahora. Vuelve en un mes después de que veas al oftalmólogo.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Doctor, I have concerns about my eyesight. I frequently see blurry.  
**Doctor:** You should see an ophthalmologist. I'll give you a referral.  
**Jasmine:** Where can I find an ophthalmologist? Does my insurance cover this?  
**Doctor:** Yes, your insurance covers it. I recommend Dr. Sánchez. She works at Clínica Ángeles, which is on Avenida Universidad.  
**Jasmine:** What's the phone number?  
**Doctor:** Here it is. Tell her you come with my referral. You don't need additional copay.  
**Jasmine:** How long do I wait for an appointment?  
**Doctor:** Usually a week. But call today and ask if there's a cancellation.  
**Jasmine:** Thanks, doctor. Do I need any other specialist?  
**Doctor:** Not for now. Come back in a month after you see the ophthalmologist.
            """)
            
            st.info("💡 **Key phrases:** Health concerns, specialist referrals, insurance coverage, appointment wait times")
    
    elif selected_lesson == "Papelería":
        st.subheader("📝 Papelería Conversations - Office & Printing Services")
        
        with st.expander("**Dialogue 1: Printing Documents**"):
            st.markdown("""
**Jasmine:** Hola, necesito imprimir estos documentos. ¿Cuánto cuesta?  
**Staff:** A ver cuántas páginas. Uno, dos... son 15 páginas. Impresión a color o blanco y negro?  
**Jasmine:** Blanco y negro está bien. ¿Cuál es el precio?  
**Staff:** Blanco y negro es 0.50 pesos por página. Son 7.50 pesos en total.  
**Jasmine:** Dale. ¿Cuánto tiempo tarda?  
**Staff:** Dos minutos. ¿Necesitas otro servicio? ¿Encuadernación? ¿Laminado?  
**Jasmine:** Laminado, sí. Una página laminada. ¿Cuánto cuesta?  
**Staff:** 30 pesos por página laminada, tamaño carta.  
**Jasmine:** Perfecto. Lamina esta portada. ¿Cuál es el total?  
**Staff:** 7.50 de impresión, más 30 de laminado. Total 37.50 pesos. Listo en 5 minutos.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, I need to print these documents. How much does it cost?  
**Staff:** Let me see how many pages. One, two... it's 15 pages. Color or black and white printing?  
**Jasmine:** Black and white is fine. What's the price?  
**Staff:** Black and white is 0.50 pesos per page. That's 7.50 pesos total.  
**Jasmine:** Okay. How long does it take?  
**Staff:** Two minutes. Do you need another service? Binding? Laminating?  
**Jasmine:** Laminating, yes. One laminated page. How much does it cost?  
**Staff:** 30 pesos per laminated page, letter size.  
**Jasmine:** Perfect. Laminate this cover page. What's the total?  
**Staff:** 7.50 for printing, plus 30 for laminating. Total 37.50 pesos. Done in 5 minutes.
            """)
            
            st.info("💡 **Key phrases:** Printing services, page costs, laminating, binding options, turnaround time")
        
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
**Jasmine:** Esa está bien. ¿Qué más necesito para tercero de primaria?  
**Staff:** Goma, tijeras, regla, marcadores, y un sacapuntas. Tengo kits escolares completos a 150 pesos.  
**Jasmine:** Perfecto. Dame un kit. ¿Cuánto es todo?  
**Staff:** 75 de cuadernos, 15 de lápices, 200 de mochila, 150 del kit. Total 440 pesos.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Good morning. I need school supplies for my son.  
**Staff:** What grade is your son in?  
**Jasmine:** Third grade elementary. I need notebooks, pencils, and backpacks.  
**Staff:** Let's see. We have 100-page notebooks at 25 pesos, or 200-page at 40 pesos.  
**Jasmine:** Give me three 100-page ones. Pencils?  
**Staff:** HB pencils at 1 peso each, or sets of 12 pencils at 15 pesos.  
**Jasmine:** Give me a set of 12. And backpacks?  
**Staff:** Backpacks from 150 to 300 pesos, depending on the model. These below are good quality, 200 pesos.  
**Jasmine:** That one is good. What else do I need for third grade?  
**Staff:** Eraser, scissors, ruler, markers, and a pencil sharpener. I have complete school kits at 150 pesos.  
**Jasmine:** Perfect. Give me a kit. How much is everything?  
**Staff:** 75 for notebooks, 15 for pencils, 200 for backpack, 150 for kit. Total 440 pesos.
            """)
            
            st.info("💡 **Key phrases:** School supplies, paper products, writing tools, pricing, school kits, quantities")
        
        with st.expander("**Dialogue 4: Laminating & Binding Services**"):
            st.markdown("""
**Jasmine:** Hola, ¿puedes encuadernar estos documentos? Necesito 5 copias.  
**Staff:** ¿Qué tipo de encuadernación? ¿Espiral, canutillo, o a través de pasadores?  
**Jasmine:** ¿Cuál es más profesional?  
**Staff:** Espiral se ve más profesional y es más durable. 50 pesos por trabajo.  
**Jasmine:** Perfecto, espiral entonces. ¿Y puedo laminan la portada?  
**Staff:** Claro, laminado brillo o mate?  
**Jasmine:** Brillo. ¿Cuánto cuesta?  
**Staff:** Laminado es 30 pesos por página, tamaño carta.  
**Jasmine:** Dale. ¿En cuánto tiempo?  
**Staff:** Todo listo en una hora. Deja tu número de teléfono para que te llamemos cuando esté.  
**Jasmine:** Mi número es 442-1234-5678. Gracias.  
**Staff:** De nada. Te llamamos en una hora.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, can you bind these documents? I need 5 copies.  
**Staff:** What type of binding? Spiral, plastic comb, or prong fasteners?  
**Jasmine:** Which one looks more professional?  
**Staff:** Spiral looks more professional and is more durable. 50 pesos per job.  
**Jasmine:** Perfect, spiral then. And can I laminate the cover?  
**Staff:** Of course, glossy or matte lamination?  
**Jasmine:** Glossy. How much does it cost?  
**Staff:** Lamination is 30 pesos per page, letter size.  
**Jasmine:** Okay. How long will it take?  
**Staff:** Everything ready in one hour. Leave your phone number so we can call you when it's done.  
**Jasmine:** My number is 442-1234-5678. Thanks.  
**Staff:** You're welcome. We'll call you in an hour.
            """)
            
            st.info("💡 **Key phrases:** Binding types, lamination finishes, document finishing, pricing, turnaround time, contact info")
    
    else:  # School
        st.subheader("🎓 School Conversations - Education & Administration")
        
        with st.expander("**Dialogue 1: School Registration**"):
            st.markdown("""
**Jasmine:** Buenos días, me interesa inscribir a mi hijo en la escuela.  
**Director:** Bienvenido. ¿En qué grado?  
**Jasmine:** Tercero de primaria. ¿Cuál es el proceso de admisión?  
**Director:** Primero necesito documentos: acta de nacimiento, comprobante de domicilio, y cartilla de vacunas.  
**Jasmine:** ¿Tengo que hacer un examen de admisión?  
**Director:** Sí, un examen simple de matemáticas y español. También entrevista con los padres.  
**Jasmine:** ¿Cuándo podemos hacer el examen?  
**Director:** Próxima semana. ¿Tienes disponibilidad el lunes a las 9 de la mañana?  
**Jasmine:** Sí, perfecto. ¿Cuál es el costo de inscripción?  
**Director:** 1,500 pesos. Incluye libros, materiales, y seguro escolar.
            """)
            
            st.markdown("**English Translation:**")
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
            
            st.info("💡 **Key phrases:** Registration documents, admission process, exams, enrollment fees, insurance")
        
        with st.expander("**Dialogue 2: Parent-Teacher Conference**"):
            st.markdown("""
**Teacher:** Buenos días, Jasmine. Gracias por venir. Quería hablar sobre el desempeño de tu hijo.  
**Jasmine:** ¿Hay algún problema?  
**Teacher:** No, no hay problema. Su académico va bien. Pero socialmente es un poco tímido.  
**Jasmine:** ¿Qué puedo hacer para ayudar?  
**Teacher:** Motívalo a participar en actividades extracurriculares. Tenemos fútbol, danza, y arte.  
**Jasmine:** ¿Cuánto cuesta?  
**Teacher:** Actividades son 150 pesos cada una al mes. Y te recomiendo que practique lectura en casa.  
**Jasmine:** ¿Cuántos minutos al día?  
**Teacher:** 20-30 minutos es suficiente. Eso mejora mucho su confianza y vocabulario.  
**Jasmine:** Dale, lo voy a hacer. ¿Alguna otra cosa?  
**Teacher:** Trae firmados los comunicados. Se los envío cada viernes. Eso es importante.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Teacher:** Good morning, Jasmine. Thanks for coming. I wanted to talk about your son's performance.  
**Jasmine:** Is there a problem?  
**Teacher:** No, there's no problem. Academically he's doing well. But socially he's a bit shy.  
**Jasmine:** What can I do to help?  
**Teacher:** Encourage him to participate in after-school activities. We have soccer, dance, and art.  
**Jasmine:** How much does it cost?  
**Teacher:** Activities are 150 pesos each per month. And I recommend you practice reading at home.  
**Jasmine:** How many minutes a day?  
**Teacher:** 20-30 minutes is enough. That improves his confidence and vocabulary a lot.  
**Jasmine:** Okay, I'll do it. Anything else?  
**Teacher:** Bring signed communications. I send them every Friday. That's important.
            """)
            
            st.info("💡 **Key phrases:** Academic performance, extracurricular activities, home practice, parent communication")
        
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
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, I see you offer tutoring. My son needs help with math.  
**Coordinator:** What specific topics?  
**Jasmine:** He has trouble with multiplication and division.  
**Coordinator:** We offer one-hour sessions, once or twice a week. 200 pesos per session.  
**Jasmine:** Twice a week?  
**Coordinator:** Yes, it's recommended for quick results. You usually see improvement in a month.  
**Jasmine:** What's the schedule?  
**Coordinator:** Monday and Wednesday 4-5 PM, or Tuesday and Thursday. You choose.  
**Jasmine:** Monday and Wednesday is good. Do I need a contract?  
**Coordinator:** Yes, a minimum 1-month contract. But you can cancel with one week notice.  
**Jasmine:** Okay, I'm interested. When does it start?  
**Coordinator:** Next week. Do you have your phone to confirm?
            """)
            
            st.info("💡 **Key phrases:** Tutoring subjects, session frequency, pricing, schedule, contracts, cancellation policy")
        
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
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, I need information about enrollment fees.  
**Administrator:** Is it a new student or current?  
**Jasmine:** New student. It's their first year at school.  
**Administrator:** For new students, the enrollment fee is 1,500 pesos.  
**Jasmine:** What does that include?  
**Administrator:** It includes books, teaching materials, digital platform access, school insurance.  
**Jasmine:** Is there a monthly fee too?  
**Administrator:** Yes. The monthly fee is 3,000 pesos. It's paid on the first of each month.  
**Jasmine:** What payment methods do you accept?  
**Administrator:** Cash, bank transfer, or credit card.  
**Jasmine:** Is there a discount if I pay several months in advance?  
**Administrator:** If you pay 6 months in advance, we give you 5% discount.  
**Jasmine:** Are there additional expenses?  
**Administrator:** Yes. Uniform (400 pesos), additional books (800 pesos), activities (150 pesos each).  
**Jasmine:** Can I make a payment plan?  
**Administrator:** Of course. If it's hard to pay all at once, we can split the initial expenses into 2-3 payments.
            """)
            
            st.info("💡 **Key phrases:** Fees breakdown, payment methods, discounts, payment plans, what's included")

# ============================================================================
# TAB 3: HOSPITAL (Vocab Search with Audio)
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
                    if st.button(f"🔊 {item['spanish']}", key=f"audio_hospital_{item['id']}"):
                        audio = create_audio(item['spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                
                st.divider()
        
        else:
            st.warning("❌ No results found.")
        
        # AI BUTTON (OUTSIDE if/else)
        if has_groq:
            if st.button(f"💡 Get AI help with '{hospital_query}'", key="hospital_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(hospital_query, lesson="hospital")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 4: PAPELERÍA (Vocab Search with Audio)
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
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
        
        else:
            st.warning("❌ No results found.")
        
        # AI BUTTON (OUTSIDE if/else)
        if has_groq:
            if st.button(f"💡 Get AI help with '{pap_query}'", key="pap_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(pap_query, lesson="papeleria")
                    if ai_response:
                        st.info(ai_response)
# ============================================================================
# TAB 5: SCHOOL (Vocab Search with Audio)
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
                    if st.button(f"🔊 {item['spanish']}", key=f"audio_school_{item['id']}"):
                        audio = create_audio(item['spanish'], lang='es')
                        if audio:
                            st.audio(audio, format='audio/mp3')
                    
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
        
        else:
            st.warning("❌ No results found.")
        
        # AI BUTTON (OUTSIDE if/else)
        if has_groq:
            if st.button(f"💡 Get AI help with '{school_query}'", key="school_ai"):
                with st.spinner("Thinking..."):
                    ai_response = get_ai_response(school_query, lesson="school")
                    if ai_response:
                        st.info(ai_response)

# ============================================================================
# TAB 6: GRAMMAR (Present Tense Verb Conjugations)
# ============================================================================
with tab6:
    st.header("📚 Spanish Verb Conjugations - Present Tense")
    
    st.info("Learn essential verbs for daily Querétaro conversations. Click audio buttons to hear pronunciation.")
    
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
    
    # Display grammar
    selected_verb = st.selectbox("Choose a verb:", list(grammar_data.keys()))
    
    if selected_verb:
        verb_info = grammar_data[selected_verb]
        
        st.subheader(selected_verb)
        
        # Create columns for conjugation table
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
        if st.button(f"🔊 Hear: {selected_verb}", key=f"grammar_verb_{selected_verb}"):
            # Extract infinitive from "Verb (English)"
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
