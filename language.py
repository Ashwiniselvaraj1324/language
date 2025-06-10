import streamlit as st
import google.generativeai as genai
import random
from datetime import datetime

# Initialize Gemini API
def initialize_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini 2.0 flash')

# App configuration
st.set_page_config(
    page_title="Language Learning with Gemini",
    page_icon="🌍",
    layout="wide"
)

# Sidebar for API key and settings
with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("AIzaSyDtN3HAFM7BFlaJu82EysVh0vwEoSQ5sdY", type="password")
    if api_key:
        try:
            model = initialize_gemini("gemini-2.0 Flash")
            st.success("API connected successfully!")
        except Exception as e:
            st.error(f"Error connecting to Gemini API: {e}")
            st.stop()
    else:
        st.info("Please enter your Gemini API key to continue")
        st.stop()
    
    st.divider()
    st.subheader("Learning Preferences")
    target_language = st.selectbox(
        "Choose target language:",
        ["German", "French", "Spanish", "Italian", "Japanese", "Chinese"]
    )
    difficulty = st.select_slider(
        "Difficulty level:",
        options=["Beginner", "Intermediate", "Advanced"]
    )
    gamification_mode = st.checkbox("Enable Gamification", value=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""
if 'last_feedback' not in st.session_state:
    st.session_state.last_feedback = ""
if 'vocabulary_tip' not in st.session_state:
    st.session_state.vocabulary_tip = ""

# Main app
st.title(f"🌍 {target_language} Learning with Gemini")
st.caption(f"Practice {target_language} at {difficulty} level")

# Gamification elements
if gamification_mode:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Score", st.session_state.score)
    with col2:
        st.metric("Questions Completed", len(st.session_state.conversation_history))
    with col3:
        if st.session_state.conversation_history:
            last_interaction = st.session_state.conversation_history[-1]['timestamp']
            st.metric("Last Interaction", last_interaction.split()[1][:5])

# Generate a new question
def generate_question():
    prompt = f"""
    Generate a {difficulty.lower()} level question in {target_language} for language practice.
    The question should be about everyday situations and require a response of 1-2 sentences.
    Return ONLY the question in {target_language}, nothing else.
    """
    response = model.generate_content(prompt)
    st.session_state.current_question = response.text

# Get feedback on user response
def get_feedback(user_response):
    # Check grammar and vocabulary
    grammar_prompt = f"""
    Analyze this {target_language} sentence for grammar and vocabulary mistakes:
    "{user_response}"
    
    Provide:
    1. A correctness score (0-100)
    2. Brief explanation of any errors
    3. A corrected version
    4. One vocabulary tip related to the response
    
    Format as:
    Score: [score]
    Errors: [explanation]
    Corrected: [corrected sentence]
    Tip: [vocabulary tip]
    """
    
    feedback_response = model.generate_content(grammar_prompt)
    feedback_text = feedback_response.text
    
    # Parse the feedback
    try:
        score_line = [line for line in feedback_text.split('\n') if line.startswith('Score:')][0]
        score = int(score_line.split(':')[1].strip())
        
        errors = next(line.split(':', 1)[1].strip() for line in feedback_text.split('\n') if line.startswith('Errors:'))
        corrected = next(line.split(':', 1)[1].strip() for line in feedback_text.split('\n') if line.startswith('Corrected:'))
        tip = next(line.split(':', 1)[1].strip() for line in feedback_text.split('\n') if line.startswith('Tip:'))
        
        # Update session state
        st.session_state.last_feedback = {
            'score': score,
            'errors': errors,
            'corrected': corrected,
            'tip': tip
        }
        st.session_state.vocabulary_tip = tip
        
        # Update score
        st.session_state.score += score // 10
        
        # Add to history
        st.session_state.conversation_history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'question': st.session_state.current_question,
            'response': user_response,
            'feedback': st.session_state.last_feedback
        })
        
    except Exception as e:
        st.error(f"Couldn't parse feedback: {e}")
        st.session_state.last_feedback = {
            'score': 0,
            'errors': "Feedback parsing failed",
            'corrected': user_response,
            'tip': "No tip available"
        }

# Main interaction area
tab1, tab2, tab3 = st.tabs(["Practice", "Feedback", "History"])

with tab1:
    if not st.session_state.current_question:
        generate_question()
    
    st.subheader("Current Question")
    st.markdown(f"**{st.session_state.current_question}**")
    
    user_response = st.text_area(
        "Your response:",
        placeholder=f"Type your response in {target_language} here...",
        key="response_input"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Answer"):
            if user_response.strip():
                get_feedback(user_response)
                st.rerun()
            else:
                st.warning("Please enter a response before submitting")
    with col2:
        if st.button("New Question"):
            generate_question()
            st.rerun()

with tab2:
    if st.session_state.last_feedback:
        feedback = st.session_state.last_feedback
        st.subheader("Your Feedback")
        
        st.metric("Score", f"{feedback['score']}/100")
        
        st.markdown("#### Corrections")
        if feedback['errors'].lower() == "none":
            st.success("No errors found! Perfect response!")
        else:
            st.warning(feedback['errors'])
            st.info(f"Corrected version: {feedback['corrected']}")
        
        st.markdown("#### Vocabulary Tip")
        st.info(feedback['tip'])
    else:
        st.info("Complete a practice question to see feedback here")

with tab3:
    if st.session_state.conversation_history:
        st.subheader("Your Practice History")
        for i, interaction in enumerate(st.session_state.conversation_history[::-1], 1):
            with st.expander(f"Practice {i} - {interaction['timestamp']}"):
                st.markdown(f"**Question:** {interaction['question']}")
                st.markdown(f"**Your Response:** {interaction['response']}")
                st.markdown(f"**Score:** {interaction['feedback']['score']}/100")
                if interaction['feedback']['errors'].lower() != "none":
                    st.markdown(f"**Corrections:** {interaction['feedback']['errors']}")
                    st.markdown(f"**Corrected Version:** {interaction['feedback']['corrected']}")
                st.markdown(f"**Vocabulary Tip:** {interaction['feedback']['tip']}")
    else:
        st.info("Your practice history will appear here")

# Vocabulary tips section
st.divider()
st.subheader("Vocabulary Tips")
if st.session_state.vocabulary_tip:
    st.info(st.session_state.vocabulary_tip)
else:
    st.info("Complete a practice question to see vocabulary tips here")

# Instructions
with st.expander("How to use this app"):
    st.markdown("""
    1. Enter your Gemini API key in the sidebar
    2. Select your target language and difficulty level
    3. Click 'New Question' to get a practice question
    4. Type your response in the target language
    5. Click 'Submit Answer' to get feedback
    6. Check the Feedback tab for corrections and tips
    7. Track your progress in the History tab
    
    **Gamification Features:**
    - Earn points for each correct answer
    - Track your learning streak
    - Collect vocabulary tips
    """)