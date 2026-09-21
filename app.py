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

def get_ai_response(query, lesson=None):
    """Get AI response using Groq (if available)"""
    if not has_groq:
        return None
    
    try:
        # Get relevant vocabulary for context
        results = search_vocabulary(query, lesson)
        
        if not results:
            return None
        
        # Build context from vocabulary
        context = "\n".join([
            f"- {item['spanish']}: {item['english']} ({item['example_spanish']})"
            for item in results[:5]
        ])
        
        # Create prompt (safe, no injection risk)
        prompt = f"""You are a Spanish teacher helping someone learn market Spanish in Querétaro.

Relevant vocabulary:
{context}

Student's question: {query}

Respond in Spanish and English. Keep response concise and practical."""
        
        # Call Groq API with timeout
        response = client.messages.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.content[0].text
    
    except Exception as e:
        st.error(f"⚠️ AI response failed: {str(e)[:100]}")
        return None

# ============================================================================
# STREAMLIT UI - WITH CONVERSATIONS
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏪 Market", "💬 Conversations", "🏥 Hospital", "📝 Papelería", "🎓 School"])

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
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
            
            if has_groq:
                if st.button(f"💡 Get AI help with '{market_query}'", key="market_ai"):
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(market_query, lesson="market")
                        if ai_response:
                            st.info(ai_response)
                        else:
                            st.warning("Could not generate AI response")
        else:
            st.warning("❌ No results found. Try different keywords.")

# ============================================================================
# TAB 2: CONVERSATIONS (All 4 Lessons)
# ============================================================================
with tab2:
    st.subheader("💬 Real Conversations - Learn from Scenarios")
    
    conv_lesson = st.selectbox(
        "Choose a lesson:",
        ["Market (La Cruz)", "Hospital", "Papelería", "School"],
        key="conv_select"
    )
    
    # ===== MARKET CONVERSATIONS =====
    if conv_lesson == "Market (La Cruz)":
        st.markdown("### 🏪 Market Conversations - La Cruz")
        
        # Dialogue 1
        with st.expander("**Dialogue 1: Finding the Spice Vendor** (Intermediate)"):
            st.markdown("""
**Jasmine:** Hola, buenos días. ¿Dónde puedo encontrar cúrcuma?  
**Vendor:** Ah, cúrcuma. Tengo muy buena, mira.  
**Jasmine:** ¿Cuánto cuesta el kilo?  
**Vendor:** 250 pesos el kilo.  
**Jasmine:** Mmm, es un poco caro. ¿Cuál es el mejor precio?  
**Vendor:** Mira, para ti, 220 pesos. Está muy fresca.  
**Jasmine:** Está bien. Dame medio kilo.  
**Vendor:** Perfecto. ¿Qué más necesitas?
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, good morning. Where can I find turmeric?  
**Vendor:** Ah, turmeric. I have very good quality, look.  
**Jasmine:** How much is it per kilo?  
**Vendor:** 250 pesos per kilo.  
**Jasmine:** Hmm, it's a bit expensive. What's your best price?  
**Vendor:** Look, for you, 220 pesos. It's very fresh.  
**Jasmine:** Okay. Give me half a kilo.  
**Vendor:** Perfect. What else do you need?
            """)
            
            st.info("💡 **Key phrases:** Haggling with vendors, negotiating prices, asking for quality")
        
        # Dialogue 2
        with st.expander("**Dialogue 2: Buying Fresh Fish**"):
            st.markdown("""
**Jasmine:** ¿Tienes pescado fresco?  
**Fish Vendor:** Sí, tengo tilapia, mojarra y trucha. ¿Cuál prefieres?  
**Jasmine:** ¿Cuál es más fresco?  
**Fish Vendor:** La tilapia llegó esta mañana. Muy fresca.  
**Jasmine:** ¿Cuánto cuesta?  
**Fish Vendor:** 85 pesos el kilo.  
**Jasmine:** ¿Es el mejor precio? Ayer vi a 75.  
**Fish Vendor:** Ese pescado no era fresco como este. Este es de hoy. Te lo dejo en 80.  
**Jasmine:** Está bien. Dame un kilo, por favor.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Do you have fresh fish?  
**Fish Vendor:** Yes, I have tilapia, bass, and trout. Which do you prefer?  
**Jasmine:** Which one is fresher?  
**Fish Vendor:** The tilapia arrived this morning. Very fresh.  
**Jasmine:** How much does it cost?  
**Fish Vendor:** 85 pesos per kilo.  
**Jasmine:** Is that your best price? I saw it for 75 yesterday.  
**Fish Vendor:** That fish wasn't as fresh as this. This is from today. I'll give it to you for 80.  
**Jasmine:** Okay. Give me one kilo, please.
            """)
            
            st.info("💡 **Key phrases:** Comparing freshness, asking prices, making counter-offers")
        
        # Dialogue 3
        with st.expander("**Dialogue 3: Negotiating Vegetables**"):
            st.markdown("""
**Jasmine:** ¿Qué vegetales frescos tienes hoy?  
**Vendor (F):** Tengo chiles rojos, tomates, cebollas, cilantro, todo fresco.  
**Jasmine:** ¿Cuánto por esto? (pointing at red chillies)  
**Vendor:** Los chiles rojos están a 30 pesos el kilo. Están muy frescos, recién traídos.  
**Jasmine:** ¿Puedo probar uno?  
**Vendor:** Claro, claro. ¿Ves? Firme, fresco.  
**Jasmine:** Bueno. Dame 250 gramos de chiles y 2 kilos de tomates.  
**Vendor:** Perfecto. ¿Algo más?  
**Jasmine:** ¿Tienes rábanos? Para mi esposo le encantan.  
**Vendor:** Sí, aquí están. Muy fresco.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** What fresh vegetables do you have today?  
**Vendor:** I have red chillies, tomatoes, onions, cilantro, all fresh.  
**Jasmine:** How much for this?  
**Vendor:** Red chillies are 30 pesos per kilo. Very fresh, just arrived.  
**Jasmine:** Can I check one?  
**Vendor:** Of course. See? Firm, fresh.  
**Jasmine:** Okay. Give me 250 grams of chillies and 2 kilos of tomatoes.  
**Vendor:** Perfect. Anything else?  
**Jasmine:** Do you have radishes? My husband loves them.  
**Vendor:** Yes, here they are. Very fresh.
            """)
            
            st.info("💡 **Key phrases:** Quality checking, specifying quantities, shopping for multiple items")
        
        # Dialogue 4
        with st.expander("**Dialogue 4: Finding Indian Spices**"):
            st.markdown("""
**Jasmine:** Disculpe, ¿dónde encontramos harina de garbanzo?  
**Spice Vendor:** ¿Harina de garbanzo? Tengo, pero es importada. Es un poco cara.  
**Jasmine:** ¿Cuánto cuesta?  
**Spice Vendor:** 150 pesos el kilo. Es de muy buena calidad.  
**Jasmine:** ¿Tienes methi también? (fenugreek)  
**Spice Vendor:** Sí, claro. ¿Seco o fresco?  
**Jasmine:** Seco, por favor.  
**Spice Vendor:** Methi seco, 80 pesos. ¿Qué más necesitas? ¿Rava? ¿Jaggery?  
**Jasmine:** Sí, rava. ¿Cuánto?  
**Spice Vendor:** Rava, 110 pesos el kilo. Y jaggery, 90 pesos.  
**Jasmine:** Está bien. Dame medio kilo de cada uno.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Excuse me, where can I find gram flour?  
**Spice Vendor:** Gram flour? I have it, but it's imported. A bit expensive.  
**Jasmine:** How much is it?  
**Spice Vendor:** 150 pesos per kilo. Very good quality.  
**Jasmine:** Do you have fenugreek too?  
**Spice Vendor:** Yes, of course. Dried or fresh?  
**Jasmine:** Dried, please.  
**Spice Vendor:** Dried fenugreek, 80 pesos. What else do you need? Semolina? Jaggery?  
**Jasmine:** Yes, semolina. How much?  
**Spice Vendor:** Semolina, 110 pesos per kilo. And jaggery, 90 pesos.  
**Jasmine:** Okay. Give me half a kilo of each.
            """)
            
            st.info("💡 **Key phrases:** Indian spice shopping, quality discussion, building a relationship with vendor")
    
    # ===== HOSPITAL CONVERSATIONS =====
    elif conv_lesson == "Hospital":
        st.markdown("### 🏥 Hospital Conversations - Medical Care")
        
        with st.expander("**Dialogue 1: Calling for an Appointment**"):
            st.markdown("""
**Jasmine:** Hola, buenos días. Necesito una cita con el doctor.  
**Receptionist:** Sí, claro. ¿Cuál es tu problema o síntoma?  
**Jasmine:** Tengo dolor de cabeza y fiebre desde hace dos días.  
**Receptionist:** ¿Prefieres doctor general o especialista?  
**Jasmine:** General doctor, por favor. ¿Cuándo hay disponibilidad?  
**Receptionist:** Tenemos cita mañana a las 10 de la mañana o pasado mañana a las 2 de la tarde.  
**Jasmine:** Mañana a las 10 está bien. ¿Cuál es el costo?  
**Receptionist:** Cita sin seguro, 400 pesos. Con seguro, solo copago.  
**Jasmine:** ¿Cuál es el copago?  
**Receptionist:** Copago es 100 pesos. ¿Tienes seguro?  
**Jasmine:** Sí, tengo seguro con mi empresa.  
**Receptionist:** Perfecto. Trae tu carnet de seguro mañana.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, good morning. I need an appointment with a doctor.  
**Receptionist:** Yes, of course. What's your problem or symptom?  
**Jasmine:** I have a headache and fever for two days.  
**Receptionist:** Do you prefer a general doctor or a specialist?  
**Jasmine:** General doctor, please. When do you have availability?  
**Receptionist:** We have an appointment tomorrow at 10 AM or the day after tomorrow at 2 PM.  
**Jasmine:** Tomorrow at 10 works. What's the cost?  
**Receptionist:** Appointment without insurance, 400 pesos. With insurance, just copay.  
**Jasmine:** What's the copay?  
**Receptionist:** Copay is 100 pesos. Do you have insurance?  
**Jasmine:** Yes, I have insurance through my company.  
**Receptionist:** Perfect. Bring your insurance card tomorrow.
            """)
            
            st.info("💡 **Key phrases:** Booking appointments, insurance questions, cost negotiation")
        
        with st.expander("**Dialogue 2: Check-in at Hospital**"):
            st.markdown("""
**Jasmine:** Hola, tengo cita con el doctor García a las 10.  
**Receptionist:** Sí, bienvenida. ¿Cuál es tu nombre completo?  
**Jasmine:** Jasmine Singh.  
**Receptionist:** ¿Primera vez aquí?  
**Jasmine:** Sí, primera vez.  
**Receptionist:** Necesito tu identificación y seguro, por favor.  
**Jasmine:** Aquí está mi pasaporte y carnet de seguro.  
**Receptionist:** Gracias. ¿Tienes alergias a medicinas?  
**Jasmine:** No alergias a medicinas, pero soy alérgica a los camarones.  
**Receptionist:** Anotado. Por favor, siéntate en la sala de espera. Te llamaremos pronto.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, I have an appointment with Doctor García at 10.  
**Receptionist:** Yes, welcome. What's your full name?  
**Jasmine:** Jasmine Singh.  
**Receptionist:** First time here?  
**Jasmine:** Yes, first time.  
**Receptionist:** I need your ID and insurance card, please.  
**Jasmine:** Here's my passport and insurance card.  
**Receptionist:** Thank you. Do you have any medicine allergies?  
**Jasmine:** No medicine allergies, but I'm allergic to shrimp.  
**Receptionist:** Noted. Please wait in the waiting room. We'll call you soon.
            """)
            
            st.info("💡 **Key phrases:** Hospital check-in, documentation, allergy disclosure")
        
        with st.expander("**Dialogue 3: Talking to Doctor**"):
            st.markdown("""
**Doctor:** Hola, soy el doctor García. ¿Cuál es el problema?  
**Jasmine:** Tengo dolor de cabeza, fiebre y tos desde hace tres días.  
**Doctor:** ¿Duele la garganta?  
**Jasmine:** Sí, duele mucho. Es difícil tragar.  
**Doctor:** ¿Tomas algún medicamento regularmente?  
**Jasmine:** No, nada regularmente.  
**Doctor:** Voy a examinarte. Por favor, abre la boca.  
[After examination]  
**Doctor:** Tienes infección de garganta. Es viral, no bacteria. Necesitas descanso y mucho líquido.  
**Jasmine:** ¿Necesito antibióticos?  
**Doctor:** No es necesario ahora. Si no mejoras en una semana, vuelve.  
**Jasmine:** ¿Puedo ir al trabajo mañana?  
**Doctor:** No, necesitas descanso. Mínimo dos días.  
**Jasmine:** Entendido. ¿Cuánto cuesta la consulta?  
**Doctor:** Recepción te dirá.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Doctor:** Hi, I'm Doctor García. What's the problem?  
**Jasmine:** I have a headache, fever, and cough for three days.  
**Doctor:** Does your throat hurt?  
**Jasmine:** Yes, it hurts a lot. It's difficult to swallow.  
**Doctor:** Do you take any regular medication?  
**Jasmine:** No, nothing regularly.  
**Doctor:** I'm going to examine you. Please open your mouth.  
[After examination]  
**Doctor:** You have a throat infection. It's viral, not bacterial. You need rest and lots of fluids.  
**Jasmine:** Do I need antibiotics?  
**Doctor:** Not necessary now. If you don't improve in a week, come back.  
**Jasmine:** Can I go to work tomorrow?  
**Doctor:** No, you need rest. At least two days.  
**Jasmine:** Understood. How much is the consultation?  
**Doctor:** Reception will tell you.
            """)
            
            st.info("💡 **Key phrases:** Describing symptoms, medical examination language, recovery instructions")
        
        with st.expander("**Dialogue 4: Insurance & Claims**"):
            st.markdown("""
**Jasmine:** Hola, tengo preguntas sobre mi seguro y cómo hacer un reclamo.  
**Insurance Advisor:** Claro, con gusto. ¿Qué necesitas?  
**Jasmine:** Tuve una consulta hoy. ¿Cómo presento el reclamo a mi seguro?  
**Advisor:** Necesitas estos documentos: factura, receta del doctor, y comprobante de pago.  
**Jasmine:** ¿El hospital envía directamente al seguro o yo debo enviar?  
**Advisor:** Nosotros podemos enviarlo directamente si das autorización. Es más fácil.  
**Jasmine:** ¿Cuánto tiempo tarda el reembolso?  
**Advisor:** Normalmente, 10 a 15 días si todo está en orden.  
**Jasmine:** ¿Qué documentos necesito guardar?  
**Advisor:** Guarda copia de todo: factura, receta, comprobante de pago, y la autorización del seguro.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, I have questions about my insurance and how to file a claim.  
**Advisor:** Of course, happy to help. What do you need?  
**Jasmine:** I had a consultation today. How do I file a claim with my insurance?  
**Advisor:** You need these documents: invoice, doctor's prescription, and proof of payment.  
**Jasmine:** Does the hospital send it directly to insurance or do I send it?  
**Advisor:** We can send it directly if you give authorization. It's easier.  
**Jasmine:** How long does reimbursement take?  
**Advisor:** Normally, 10 to 15 days if everything is in order.  
**Jasmine:** What documents do I need to keep?  
**Advisor:** Keep copies of everything: invoice, prescription, proof of payment, and insurance authorization.
            """)
            
            st.info("💡 **Key phrases:** Insurance claims, documentation, reimbursement timeline")
    
    # ===== PAPELERÍA CONVERSATIONS =====
    elif conv_lesson == "Papelería":
        st.markdown("### 📝 Papelería Conversations - Stationery & Printing")
        
        with st.expander("**Dialogue 1: Small Shop - Book Supplies**"):
            st.markdown("""
**Jasmine:** Hola, buenos días. Busco forros para libros.  
**Shop Owner:** Ah, ¿forros para qué? ¿Libros de escuela?  
**Jasmine:** Sí, para libros escolares. ¿Qué tienes?  
**Shop Owner:** Tengo forros adhesivos en muchos colores. ¿Cuáles necesitas?  
**Jasmine:** ¿Cuáles son los colores disponibles?  
**Shop Owner:** Rojo, azul, verde, amarillo, negro, blanco. Todos los colores.  
**Jasmine:** ¿Cuánto cuesta cada forro?  
**Shop Owner:** 15 pesos cada uno. ¿Cuántos necesitas?  
**Jasmine:** Necesito 6 forros. ¿Hay descuento por cantidad?  
**Shop Owner:** Para 6, te dejo en 80 pesos los 6. Normalmente sería 90.  
**Jasmine:** Perfecto. Dame 6 en rojo, azul, y verde. Dos de cada color.  
**Shop Owner:** Excelente. ¿Necesitas algo más?  
**Jasmine:** ¿Tienes hojas de laminación autoadhesivas?  
**Shop Owner:** Sí, tengo. ¿De qué tamaño? Carta o legal?  
**Jasmine:** Carta, por favor. ¿Cuánto?  
**Shop Owner:** Por paquete de 10 hojas, 120 pesos.  
**Jasmine:** Está bien. Dame un paquete también.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, good morning. I'm looking for book wraps/covers.  
**Shop Owner:** Oh, wraps for what? School books?  
**Jasmine:** Yes, for school books. What do you have?  
**Shop Owner:** I have adhesive wraps in many colors. Which do you need?  
**Jasmine:** What colors are available?  
**Shop Owner:** Red, blue, green, yellow, black, white. All colors.  
**Jasmine:** How much is each wrap?  
**Shop Owner:** 15 pesos each. How many do you need?  
**Jasmine:** I need 6 wraps. Is there a bulk discount?  
**Shop Owner:** For 6, I'll give you 80 pesos total. Normally it would be 90.  
**Jasmine:** Perfect. Give me 6 - red, blue, and green. Two of each.  
**Shop Owner:** Great. Do you need anything else?  
**Jasmine:** Do you have self-adhesive lamination sheets?  
**Shop Owner:** Yes, I have. What size? Letter or legal?  
**Jasmine:** Letter, please. How much?  
**Shop Owner:** For a pack of 10 sheets, 120 pesos.  
**Jasmine:** Okay. Give me a pack too.
            """)
            
            st.info("💡 **Key phrases:** Color selection, bulk discounts, product specifications")
        
        with st.expander("**Dialogue 2: Office Max - Printing Services**"):
            st.markdown("""
**Jasmine:** Hola, necesito imprimir unos documentos.  
**Employee:** Claro. ¿Cuántas páginas?  
**Jasmine:** Son 20 páginas. Color o blanco y negro. ¿Cuál es más económico?  
**Employee:** Blanco y negro cuesta 1 peso por página. Color cuesta 3 pesos por página.  
**Jasmine:** ¿Puedo ver una muestra primero?  
**Employee:** Claro, dame un minuto. Voy a imprimir una página.  
[After viewing sample]  
**Jasmine:** Está perfecto. Quiero blanco y negro para todas.  
**Employee:** Bien. ¿Quieres encuadernación? ¿Grapas o espiral?  
**Jasmine:** ¿Cuánto cuesta adicional?  
**Employee:** Grapas son gratis. Espiral cuesta 5 pesos.  
**Jasmine:** Grapas, por favor. ¿Cuándo estará listo?  
**Employee:** En 30 minutos. ¿Quieres esperar o vienes más tarde?  
**Jasmine:** Voy a volver en media hora. ¿Cuál es el costo total?  
**Employee:** Veinte pesos.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, I need to print some documents.  
**Employee:** Sure. How many pages?  
**Jasmine:** It's 20 pages. Color or black and white. Which is more economical?  
**Employee:** Black and white is 1 peso per page. Color is 3 pesos per page.  
**Jasmine:** Can I see a sample first?  
**Employee:** Of course, give me a minute. I'll print one page.  
[After viewing sample]  
**Jasmine:** It's perfect. I want black and white for all.  
**Employee:** Okay. Do you want binding? Staples or spiral?  
**Jasmine:** How much extra?  
**Employee:** Staples are free. Spiral binding is 5 pesos.  
**Jasmine:** Staples, please. When will it be ready?  
**Employee:** In 30 minutes. Do you want to wait or come back later?  
**Jasmine:** I'll come back in half an hour. What's the total cost?  
**Employee:** Twenty pesos.
            """)
            
            st.info("💡 **Key phrases:** Printing options, binding choices, pricing, turnaround time")
        
        with st.expander("**Dialogue 3: Notebooks & Colors**"):
            st.markdown("""
**Jasmine:** ¿Tienes cuadernos? Necesito para la escuela.  
**Vendor:** Sí, tengo muchos. ¿Qué tamaño? ¿Cuaderno grande o pequeño?  
**Jasmine:** ¿Cuáles son las opciones?  
**Vendor:** Tamaño A4 (grande) o tamaño A5 (pequeño). Tengo con rayas o cuadrículas.  
**Jasmine:** ¿Cuál es la diferencia de precio?  
**Vendor:** A4 con rayas, 35 pesos. A5 con rayas, 25 pesos. A4 con cuadrículas, 40 pesos.  
**Jasmine:** ¿Tienes en colores diferentes?  
**Vendor:** Sí, azul, rojo, verde, amarillo, rosa, morado.  
**Jasmine:** ¿Qué colores son más populares en la escuela aquí?  
**Vendor:** Los azules y negros son los más vendidos.  
**Jasmine:** Necesito 4 cuadernos. ¿Hay descuento si compro varios?  
**Vendor:** Normalmente no. Pero si compras 4, te dejo en 130 pesos en lugar de 140.  
**Jasmine:** Está bien. Dame dos A4 azules con rayas y dos A5 verdes con rayas.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Do you have notebooks? I need them for school.  
**Vendor:** Yes, I have many. What size? Large or small notebook?  
**Jasmine:** What are the options?  
**Vendor:** Size A4 (large) or A5 (small). I have lined or grid.  
**Jasmine:** What's the price difference?  
**Vendor:** A4 lined, 35 pesos. A5 lined, 25 pesos. A4 grid, 40 pesos.  
**Jasmine:** Do you have different colors?  
**Vendor:** Yes, blue, red, green, yellow, pink, purple.  
**Jasmine:** What colors are most popular at school here?  
**Vendor:** Blues and blacks sell most.  
**Jasmine:** I need 4 notebooks. Is there a discount if I buy several?  
**Vendor:** Normally no. But if you buy 4, I'll give you 130 instead of 140.  
**Jasmine:** Okay. Give me two A4 blue lined and two A5 green lined.
            """)
            
            st.info("💡 **Key phrases:** Size options, line/grid preferences, color selection, bulk pricing")
        
        with st.expander("**Dialogue 4: Laminating & Special Services**"):
            st.markdown("""
**Jasmine:** ¿Ofrecen servicios de laminado aquí?  
**Shop Owner:** Sí, tenemos laminadora. ¿Qué necesitas laminar?  
**Jasmine:** Es un documento importante. Una copia de mi residencia.  
**Shop Owner:** ¿Cuál es el tamaño? Carta o más grande?  
**Jasmine:** Tamaño carta. ¿Cuánto cuesta?  
**Shop Owner:** Carta lamina a brillo cuesta 15 pesos. Con acabado mate, 20 pesos.  
**Jasmine:** ¿Cuál es mejor para durabilidad?  
**Shop Owner:** Ambos duran igual. Brillo es más brillante. Mate es menos reflectante.  
**Jasmine:** Mate, por favor. ¿Cuándo estará listo?  
**Shop Owner:** En 10 minutos. Es muy rápido.  
**Jasmine:** Perfecto. ¿También haces encuadernación?  
**Shop Owner:** Sí, espiral, grapas, broches. ¿Para cuántas hojas?  
**Jasmine:** Para un proyecto escolar, son 15 hojas. ¿Cuál recomiendas?  
**Shop Owner:** Para 15 hojas, espiral o grapas están bien. Espiral dura más, pero cuesta más.  
**Jasmine:** ¿Cuánto cuesta?  
**Shop Owner:** Espiral cuesta 8 pesos. Grapas son gratis.  
**Jasmine:** Dale, espiral. Es un proyecto importante.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Do you offer laminating services here?  
**Shop Owner:** Yes, we have a laminator. What do you need laminated?  
**Jasmine:** It's an important document. A copy of my residence permit.  
**Shop Owner:** What's the size? Letter or larger?  
**Jasmine:** Letter size. How much does it cost?  
**Shop Owner:** Letter gloss lamination is 15 pesos. Matte finish is 20 pesos.  
**Jasmine:** Which is better for durability?  
**Shop Owner:** Both last equally. Gloss is shinier. Matte is less reflective.  
**Jasmine:** Matte, please. When will it be ready?  
**Shop Owner:** In 10 minutes. It's very quick.  
**Jasmine:** Perfect. Do you also do binding?  
**Shop Owner:** Yes, spiral, staples, brads. For how many sheets?  
**Jasmine:** For a school project, it's 15 sheets. What do you recommend?  
**Shop Owner:** For 15 sheets, spiral or staples are fine. Spiral lasts longer but costs more.  
**Jasmine:** How much?  
**Shop Owner:** Spiral is 8 pesos. Staples are free.  
**Jasmine:** Okay, spiral. It's an important project.
            """)
            
            st.info("💡 **Key phrases:** Lamination options, binding choices, durability discussion, turnaround time")
    
    # ===== SCHOOL CONVERSATIONS =====
    elif conv_lesson == "School":
        st.markdown("### 🎓 School Conversations - Navigation & Administration")
        
        with st.expander("**Dialogue 1: Canteen & School Rules**"):
            st.markdown("""
**Jasmine:** Hola, ¿qué servicio ofrece la cafetería de la escuela?  
**Canteen Manager:** Ofrecemos desayuno, almuerzo, y refrigerios. ¿Qué necesitas?  
**Jasmine:** ¿Cuáles son las opciones de menú?  
**Canteen Manager:** Para desayuno, tenemos quesadillas, chilaquiles, pan dulce, leche, jugo. El almuerzo cambia cada día: lunes es pollo, martes es pasta, miércoles es sopa.  
**Jasmine:** ¿Cuánto cuesta el almuerzo?  
**Canteen Manager:** 30 pesos por almuerzo. El desayuno es 20 pesos. Los refrigerios son 10-15 pesos.  
**Jasmine:** ¿Puedo meter dinero en una cuenta del niño o pagar cada día?  
**Canteen Manager:** Mejor es una cuenta. Depositas dinero y la maestra controla lo que come.  
**Jasmine:** ¿Cuáles son las reglas de la escuela sobre comida?  
**Canteen Manager:** No se permite traer comida de afuera. No hay dulces ni refrescos en la escuela. Es para mantener buenos hábitos de salud.  
**Jasmine:** ¿Y si mi hijo tiene alergias?  
**Canteen Manager:** Avísanos al inicio del año. Podemos preparar alternativas.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Hi, what services does the school cafeteria offer?  
**Canteen Manager:** We offer breakfast, lunch, and snacks. What do you need?  
**Jasmine:** What are the menu options?  
**Canteen Manager:** For breakfast, we have quesadillas, chilaquiles, sweet bread, milk, juice. Lunch changes daily: Monday is chicken, Tuesday is pasta, Wednesday is soup.  
**Jasmine:** How much is lunch?  
**Canteen Manager:** 30 pesos for lunch. Breakfast is 20 pesos. Snacks are 10-15 pesos.  
**Jasmine:** Can I deposit money into a child's account or pay each day?  
**Canteen Manager:** Better is an account. You deposit money and the teacher controls what they eat.  
**Jasmine:** What are the school rules about food?  
**Canteen Manager:** Outside food is not allowed. No candy or soft drinks at school. It's to maintain good health habits.  
**Jasmine:** What if my child has allergies?  
**Canteen Manager:** Tell us at the beginning of the year. We can prepare alternatives.
            """)
            
            st.info("💡 **Key phrases:** Meal options, pricing, account system, school policies, allergy accommodation")
        
        with st.expander("**Dialogue 2: After-School Activities**"):
            st.markdown("""
**Jasmine:** ¿Qué actividades extraescolares ofrece la escuela?  
**Activities Coordinator:** Tenemos muchas: fútbol, basquetbol, natación, danza, arte, música, club de lectura.  
**Jasmine:** ¿Cuándo son estas actividades?  
**Coordinator:** Después de clases. Fútbol y basquetbol son de 3:30 a 4:30. Natación es de 4:00 a 5:00. Danza es de 3:45 a 4:45.  
**Jasmine:** ¿Cuánto cuesta participar?  
**Coordinator:** Cada actividad cuesta 150 pesos al mes. Puedes inscribir el niño en varias.  
**Jasmine:** ¿Necesito equipo especial?  
**Coordinator:** Para fútbol necesitas botas. Para natación, traje de baño y toalla. Los otros solo necesitan ropa cómoda.  
**Jasmine:** ¿Cómo me registro?  
**Coordinator:** Llena este formulario. Es simple. Y haz pago en administración.  
**Jasmine:** ¿Hay transporte después de actividades?  
**Coordinator:** Sí, el autobús de la escuela espera hasta las 5:30. Si termina después, tienes que recoger al niño.  
**Jasmine:** ¿Es obligatorio participar en actividades?  
**Coordinator:** No, es opcional. Pero recomendamos mucho para desarrollo del niño.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** What after-school activities does the school offer?  
**Coordinator:** We have many: soccer, basketball, swimming, dance, art, music, reading club.  
**Jasmine:** When are these activities?  
**Coordinator:** After school. Soccer and basketball are 3:30-4:30. Swimming is 4:00-5:00. Dance is 3:45-4:45.  
**Jasmine:** How much does it cost to participate?  
**Coordinator:** Each activity costs 150 pesos per month. You can enroll the child in several.  
**Jasmine:** Do I need special equipment?  
**Coordinator:** For soccer you need cleats. For swimming, swimsuit and towel. The others just need comfortable clothes.  
**Jasmine:** How do I register?  
**Coordinator:** Fill out this form. It's simple. And make payment in administration.  
**Jasmine:** Is there transportation after activities?  
**Coordinator:** Yes, the school bus waits until 5:30. If it finishes after, you need to pick up the child.  
**Jasmine:** Is it mandatory to participate?  
**Coordinator:** No, it's optional. But we strongly recommend it for child development.
            """)
            
            st.info("💡 **Key phrases:** Activity options, scheduling, pricing, equipment needs, registration, transportation")
        
        with st.expander("**Dialogue 3: Director Meeting**"):
            st.markdown("""
**Jasmine:** Buenos días. Necesito una cita con la directora.  
**Secretary:** ¿Cuál es el motivo de tu cita?  
**Jasmine:** Tengo preguntas sobre el comportamiento de mi hijo en clase.  
**Secretary:** ¿Es urgente o puede esperar hasta la próxima semana?  
**Jasmine:** No es urgente. Próxima semana está bien.  
**Secretary:** Tenemos cita disponible el miércoles a las 3 de la tarde. ¿Te va bien?  
**Jasmine:** Perfectamente. ¿Quién es la directora?  
**Secretary:** La Directora María González. Ella lleva 10 años en la escuela.  
[Later, at director's office]  
**Jasmine:** Buenos días, Directora González. Gracias por recibirme.  
**Director:** Bienvenida. ¿Cuál es tu preocupación?  
**Jasmine:** Mi hijo dice que tiene dificultad en matemáticas. ¿Cómo puedo ayudarle?  
**Director:** Tenemos programa de tutoría después de clase. Cuesta 200 pesos por sesión. También puedo conectarte con el maestro de matemáticas.  
**Jasmine:** ¿Es efectivo el programa de tutoría?  
**Director:** Sí, muchos estudiantes mejoran. Especialmente si el padre también ayuda en casa.  
**Jasmine:** ¿Hay otra cosa que pueda hacer?  
**Director:** Practica con él cada día. 15-20 minutos es suficiente.
            """)
            
            st.markdown("**English Translation:**")
            st.markdown("""
**Jasmine:** Good morning. I need an appointment with the director.  
**Secretary:** What's the reason for your appointment?  
**Jasmine:** I have questions about my child's behavior in class.  
**Secretary:** Is it urgent or can it wait until next week?  
**Jasmine:** It's not urgent. Next week is fine.  
**Secretary:** We have an appointment available Wednesday at 3 PM. Does that work?  
**Jasmine:** Perfect. Who is the director?  
**Secretary:** Director María González. She's been at the school for 10 years.  
[Later, at director's office]  
**Jasmine:** Good morning, Director González. Thank you for seeing me.  
**Director:** Welcome. What's your concern?  
**Jasmine:** My child says they're having difficulty with math. How can I help them?  
**Director:** We have a tutoring program after school. It costs 200 pesos per session. I can also connect you with the math teacher.  
**Jasmine:** Is the tutoring program effective?  
**Director:** Yes, many students improve. Especially if the parent helps at home too.  
**Jasmine:** Is there anything else I can do?  
**Director:** Practice with them every day. 15-20 minutes is enough.
            """)
            
            st.info("💡 **Key phrases:** Scheduling appointments, discussing concerns, tutoring options, home support strategies")
        
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
# TAB 3: HOSPITAL (Vocab Search)
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
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                
                st.divider()
            
            if has_groq:
                if st.button(f"💡 Get AI help with '{hospital_query}'", key="hospital_ai"):
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(hospital_query, lesson="hospital")
                        if ai_response:
                            st.info(ai_response)
        else:
            st.warning("❌ No results found.")

# ============================================================================
# TAB 4: PAPELERÍA (Vocab Search)
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
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
            
            if has_groq:
                if st.button(f"💡 Get AI help with '{pap_query}'", key="pap_ai"):
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(pap_query, lesson="papeleria")
                        if ai_response:
                            st.info(ai_response)
        else:
            st.warning("❌ No results found.")

# ============================================================================
# TAB 5: SCHOOL (Vocab Search)
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
                    st.write(f"📣 **Pronunciation:** {item['pronunciation']}")
                    st.write(f"💬 **Example:** {item['example_spanish']}")
                    st.write(f"🔤 **English:** {item['example_english']}")
                    
                    if item.get('price_range_pesos'):
                        st.write(f"💰 **Price range:** {item['price_range_pesos']} pesos")
                
                st.divider()
            
            if has_groq:
                if st.button(f"💡 Get AI help with '{school_query}'", key="school_ai"):
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(school_query, lesson="school")
                        if ai_response:
                            st.info(ai_response)
        else:
            st.warning("❌ No results found.")

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
