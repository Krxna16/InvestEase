import streamlit as st
import bcrypt
import os
import database as db
from sqlalchemy.exc import SQLAlchemyError

def hash_password(password):
    """Hashes a password natively utilizing bcrypt salt embeddings."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def register_user(username, password):
    """Registers a new user inside the PostgreSQL SaaS layer."""
    if not username or not password:
        return False, "Username and password cannot be empty."
        
    session = db.SessionLocal()
    try:
        # Prevent duplicates
        existing_user = session.query(db.User).filter(db.User.username == username).first()
        if existing_user:
            return False, "Username already exists. Please choose another."
            
        hashed_pw = hash_password(password)
        new_user = db.User(username=username, password_hash=hashed_pw)
        session.add(new_user)
        session.commit()
        return True, "Registration successful! You can now log in."
    except SQLAlchemyError as e:
        session.rollback()
        return False, "An internal connection error occurred."
    finally:
        session.close()

def verify_user(username, password):
    """Verifies user credentials referencing Postgres and bcrypt checkpw."""
    session = db.SessionLocal()
    try:
        user = session.query(db.User).filter(db.User.username == username).first()
        if not user:
            return False, None
            
        # bcrypt checkpw matches the newly requested plaintext bytes against stored encoded bytes
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return True, user.id
        return False, None
    except SQLAlchemyError as e:
        print(f"Auth Auth Error: {e}")
        return False, None
    finally:
        session.close()

def render_login_ui():
    """Renders the login and registration UI, returning True if logged in."""
    # Ensure session state variables exist
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_id'] = None
        st.session_state['username'] = None

    if st.session_state['logged_in']:
        return True
        
    import random
    
    # Generate 40 particles for Layer 4
    particles_html = ""
    for _ in range(40):
        size = random.uniform(2, 4)
        top = random.uniform(0, 100)
        left = random.uniform(0, 100)
        anim_type = random.choice(["float-anim", "pulse-anim"])
        anim_dur = random.uniform(12, 20) if anim_type == "float-anim" else random.uniform(1.5, 3)
        anim_delay = random.uniform(0, 5)
        opacity = random.uniform(0.3, 0.7)
        particles_html += f'<div class="particle {anim_type}" style="width: {size}px; height: {size}px; top: {top}%; left: {left}%; animation-duration: {anim_dur}s; animation-delay: -{anim_delay}s; opacity: {opacity};"></div>\n        '

    # Fixed: removed f-string to avoid CSS % conflict
    login_html = f"""
    <!-- Layer 1: Gradient Base -->
    <div class="fintech-bg-layer1"></div>
    
    <!-- Layer 2: Deep Graph Lines -->
    <div class="fintech-bg-layer2">
        <div class="scroll-wrapper deep-anim-1" style="top: 15%;">
            <svg preserveAspectRatio="none" viewBox="0 0 1000 100" width="200vw" height="150px">
                <path d="M 0 50 C 150 10, 350 90, 500 50 C 650 10, 850 90, 1000 50" fill="none" stroke="rgba(0, 200, 220, 0.08)" stroke-width="1.2"/>
            </svg>
        </div>
        <div class="scroll-wrapper deep-anim-2" style="top: 40%;">
            <svg preserveAspectRatio="none" viewBox="0 0 1000 100" width="200vw" height="150px">
                <path d="M 0 70 C 100 90, 400 30, 500 70 C 600 90, 900 30, 1000 70" fill="none" stroke="rgba(0, 200, 220, 0.07)" stroke-width="1"/>
            </svg>
        </div>
        <div class="scroll-wrapper deep-anim-3" style="top: 70%;">
            <svg preserveAspectRatio="none" viewBox="0 0 1000 100" width="200vw" height="150px">
                <path d="M 0 30 C 200 0, 300 80, 500 30 C 700 0, 800 80, 1000 30" fill="none" stroke="rgba(0, 200, 220, 0.09)" stroke-width="1.5"/>
            </svg>
        </div>
    </div>
    
    <!-- Layer 3: Foreground Graph Lines -->
    <div class="fintech-bg-layer3">
        <svg style="width: 0; height: 0; position: absolute;"><defs>
            <filter id="neonGlowLine" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs></svg>
        <div class="scroll-wrapper fore-anim-1" style="top: 35%;">
            <svg preserveAspectRatio="none" viewBox="0 0 1000 100" width="200vw" height="180px">
                <path filter="url(#neonGlowLine)" d="M 0 60 C 150 0, 350 100, 500 60 C 650 0, 850 100, 1000 60" fill="none" stroke="rgba(0, 180, 255, 0.20)" stroke-width="1.8"/>
            </svg>
        </div>
        <div class="scroll-wrapper fore-anim-2" style="top: 65%;">
            <svg preserveAspectRatio="none" viewBox="0 0 1000 100" width="200vw" height="180px">
                <path filter="url(#neonGlowLine)" d="M 0 80 C 200 100, 300 20, 500 80 C 700 100, 800 20, 1000 80" fill="none" stroke="rgba(80, 220, 255, 0.22)" stroke-width="2"/>
            </svg>
        </div>
    </div>
    
    <!-- Layer 4: Floating Particle Field -->
    <div class="fintech-bg-layer4">
        {particles_html}
    </div>
    """
    
    # Fixed: removed f-string to avoid CSS % conflict
    login_css = """
    <style>
        /* Hide native Streamlit Chrome during Login */
        [data-testid="stSidebar"], header, footer { display: none !important; }
        
        /* Complete Viewport Takeover & Centering */
        [data-testid="block-container"] {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 0 !important;
            max-width: 100% !important;
            position: relative;
            z-index: 10;
        }

        /* --- 4-LAYER BACKGROUND ARCHITECTURE --- */
        .fintech-bg-layer1, .fintech-bg-layer2, .fintech-bg-layer3, .fintech-bg-layer4 {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            pointer-events: none;
            overflow: hidden;
        }
        
        /* Layer 1: Gradient Base */
        .fintech-bg-layer1 {
            z-index: -4;
            background: linear-gradient(135deg, #020818, #050f1f, #0d0d2b);
            background-size: 200% 200%;
            animation: breatheGradient 25s ease-in-out infinite alternate;
        }
        @keyframes breatheGradient {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
        }

        /* Layer 2: Deep Graph Lines */
        .fintech-bg-layer2 {
            z-index: -3;
            filter: blur(0.6px);
        }
        .scroll-wrapper {
            position: absolute;
            left: 0;
            width: 200vw;
        }
        .deep-anim-1 { animation: lineScroll1 35s linear infinite; will-change: transform; }
        .deep-anim-2 { animation: lineScroll2 28s linear infinite; will-change: transform; }
        .deep-anim-3 { animation: lineScroll3 40s linear infinite; will-change: transform; }
        
        /* Layer 3: Foreground Graph Lines */
        .fintech-bg-layer3 {
            z-index: -2;
        }
        .fore-anim-1 { animation: lineScroll1 22s linear infinite; will-change: transform; }
        .fore-anim-2 { animation: lineScroll2 18s linear infinite; will-change: transform; }

        /* Tilted Parallax Scrolling */
        @keyframes lineScroll1 {
            0% { transform: rotate(-1deg) translateX(0); }
            100% { transform: rotate(-1deg) translateX(-100vw); }
        }
        @keyframes lineScroll2 {
            0% { transform: rotate(-1.5deg) translateX(0); }
            100% { transform: rotate(-1.5deg) translateX(-100vw); }
        }
        @keyframes lineScroll3 {
            0% { transform: rotate(-0.5deg) translateX(0); }
            100% { transform: rotate(-0.5deg) translateX(-100vw); }
        }

        /* Layer 4: Floating Particle Field */
        .fintech-bg-layer4 {
            z-index: -1;
        }
        .particle {
            position: absolute;
            background: rgba(180, 240, 255, 0.55);
            border-radius: 50%;
            box-shadow: 0 0 6px 2px rgba(100, 220, 255, 0.4);
        }
        .float-anim {
            animation-name: particleFloatUp;
            animation-iteration-count: infinite;
            animation-timing-function: ease-in-out;
        }
        .pulse-anim {
            animation-name: particlePulse;
            animation-iteration-count: infinite;
            animation-timing-function: ease-in-out;
            animation-direction: alternate;
        }

        @keyframes particleFloatUp {
            0% { transform: translateY(0) translateX(0); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-80px) translateX(20px); opacity: 0; }
        }
        @keyframes particlePulse {
            0% { opacity: 0.1; }
            100% { opacity: 0.8; }
        }

        /* Radial glow behind the card via massive diffused shadow */
        div[data-testid="stVerticalBlock"]:has(> div.element-container > div > .login-wrapper-marker) {
            background: rgba(15, 20, 30, 0.6) !important;
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 24px;
            padding: 40px;
            width: 420px !important;
            max-width: 90vw;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5), 0 0 120px rgba(59, 130, 246, 0.12), 0 0 40px rgba(6, 182, 212, 0.15); /* Soft focused light spread */
            animation: cardFloat 6s ease-in-out infinite, fadeInLogin 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            position: relative;
        }

        /* Hover border glowing composite */
        div[data-testid="stVerticalBlock"]:has(> div.element-container > div > .login-wrapper-marker)::before {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 24px;
            padding: 1px;
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.3), rgba(139, 92, 246, 0.1));
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            opacity: 0.8;
            pointer-events: none;
        }

        @keyframes fadeInLogin {
            0% { opacity: 0; transform: translateY(40px) scale(0.95); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes cardFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }

        /* Typography & Logo Animation */
        @keyframes logoPulse {
            0% { transform: scale(1); opacity: 0.9; }
            100% { transform: scale(1.04); opacity: 1; filter: brightness(1.2); }
        }
        .ie-monogram {
            animation: logoPulse 4s ease-in-out infinite alternate;
            display: block;
            margin: 0 auto;
        }
        .login-logo-title {
            text-align: center; 
            font-size: 32px; 
            font-weight: 800; 
            background: -webkit-linear-gradient(45deg, #3B82F6, #06B6D4); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            margin-top: 15px;
            margin-bottom: 5px; 
            letter-spacing: -0.5px;
        }
        .login-subtitle {
            text-align: center; 
            color: #9CA3AF; 
            font-size: 15px; 
            margin-bottom: 30px; 
            font-weight: 400;
        }

        /* Minimalistic Tab styling overrides for Auth Mode toggles */
        div[data-testid="stTabs"] button {
            border-bottom: 2px solid rgba(255,255,255,0.05) !important;
            transition: all 0.3s;
            background: transparent !important;
            padding-bottom: 8px;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #06B6D4 !important;
            border-bottom: 2px solid #06B6D4 !important;
        }

        /* Inputs Upgrade */
        .stTextInput>div>div>input {
            background: rgba(10, 15, 25, 0.8) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 12px !important;
            color: white !important;
            transition: all 0.3s ease !important;
            padding: 12px 14px !important;
            font-size: 15px !important;
        }
        .stTextInput>div>div>input:focus {
            border-color: #06B6D4 !important;
            box-shadow: 0 0 0 1px #06B6D4 inset, 0 0 15px rgba(6, 182, 212, 0.2) !important;
            background: rgba(15, 20, 30, 0.9) !important;
        }

        /* High Impact Form Submission Button */
        div[data-testid="stFormSubmitButton"]>button {
            background: linear-gradient(135deg, #3B82F6, #06B6D4) !important;
            border: none !important;
            border-radius: 12px !important;
            color: white !important;
            font-weight: 600 !important;
            height: 48px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            margin-top: 10px !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }
        div[data-testid="stFormSubmitButton"]>button:hover {
            transform: scale(1.02) translateY(-2px) !important;
            box-shadow: 0 10px 25px rgba(6, 182, 212, 0.5) !important;
        }
    </style>
    """
    
    # Establish a clean container targeting the CSS isolate wrapper logic
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(login_html, unsafe_allow_html=True)
        st.markdown(login_css, unsafe_allow_html=True)
        st.markdown('<div class="login-wrapper-marker" style="display:none;"></div>', unsafe_allow_html=True)
        
        # IE SVG Monogram
        monogram_html = """
        <div style="display:flex; justify-content:center; align-items:center; flex-direction:column; margin-bottom: 5px;">
            <svg width="60" height="60" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" class="ie-monogram">
                <defs>
                    <linearGradient id="ieGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#3B82F6" />
                        <stop offset="100%" stop-color="#06B6D4" />
                    </linearGradient>
                    <filter id="neonGlowLogo" x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation="8" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>
                <g filter="url(#neonGlowLogo)">
                    <!-- I -->
                    <rect x="25" y="20" width="12" height="60" fill="url(#ieGrad)" rx="4"/>
                    <!-- E -->
                    <path d="M45 20 h30 a4 4 0 0 1 4 4 v8 a4 4 0 0 1 -4 4 h-16 v10 h12 a4 4 0 0 1 4 4 v8 a4 4 0 0 1 -4 4 h-12 v10 h16 a4 4 0 0 1 4 4 v8 a4 4 0 0 1 -4 4 h-30 a4 4 0 0 1 -4 -4 v-56 a4 4 0 0 1 4 -4 z" fill="url(#ieGrad)"/>
                </g>
            </svg>
            <div class='login-logo-title'>InvestEase</div>
        </div>
        """
        st.markdown(monogram_html, unsafe_allow_html=True)
        st.markdown("<p class='login-subtitle'>Analyze. Predict. Grow.</p>", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔒 Log In", "🚀 Sign Up"])
        
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Access Portfolio")
                
                if submitted:
                    if username and password:
                        success, user_id = verify_user(username, password)
                        if success:
                            st.session_state['logged_in'] = True
                            st.session_state['user_id'] = user_id
                            st.session_state['username'] = username
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                    else:
                        st.warning("Please enter both username and password.")
                        
        with tab_signup:
            with st.form("signup_form"):
                new_username = st.text_input("Username", placeholder="Choose a secure username")
                new_password = st.text_input("Password", type="password", placeholder="Create a strong password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                submitted = st.form_submit_button("Create Account")
                
                if submitted:
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        success, message = register_user(new_username, new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

    return st.session_state['logged_in']

def build_logout_button():
    """Adds a logout button to the sidebar."""
    if st.session_state.get('logged_in', False):
        st.sidebar.markdown(f"**Logged in as:** `{st.session_state['username']}`")
        if st.sidebar.button("Logout", type="primary"):
            st.session_state['logged_in'] = False
            st.session_state['user_id'] = None
            st.session_state['username'] = None
            # Clear caches so data isn't leaked across sessions
            st.cache_data.clear()
            st.rerun()
        st.sidebar.markdown("---")
