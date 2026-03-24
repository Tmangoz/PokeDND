import streamlit as st
import requests
import random

# 1. Page Config
st.set_page_config(page_title="Battle Simulator", layout="wide")

# 2. Initialization (Safety check for new users)
if 'team' not in st.session_state or len(st.session_state['team']) < 2:
    st.warning("You need at least 2 Pokémon in your team to simulate a battle!")
    if st.button("Go to Team Builder"):
        st.switch_page("pages/Team_Builder.py")
    st.stop()

# 3. Styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .battle-log {
            background-color: #1e1e1e;
            color: #00ff00;
            padding: 15px;
            border-radius: 10px;
            font-family: 'Courier New', Courier, monospace;
            border: 1px solid #333;
        }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home Page", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button("➡️ Team Builder", use_container_width=True): st.switch_page("pages/Team_Builder.py")

# --- HELPERS ---
def get_mod(stat_value):
    """Converts 0-200 base stat to a D&D modifier (-5 to +10)"""
    return (stat_value - 100) // 10

def get_damage_dice(power):
    """Calculates D&D dice based on Move Power"""
    if power <= 40: return "1d6"
    if power <= 60: return "2d6"
    if power <= 80: return "3d8"
    if power <= 100: return "4d10"
    return "5d12"

# --- MAIN INTERFACE ---
st.title("⚔️ Battle Simulator")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🛡️ Select Attacker")
    attacker_idx = st.selectbox("Choose Attacker", range(len(st.session_state['team'])), 
                                format_func=lambda i: st.session_state['team'][i]['name'].capitalize())
    attacker = st.session_state['team'][attacker_idx]
    st.image(attacker['sprites']['front_default'], width=150)

with col2:
    st.subheader("🎯 Select Defender")
    defender_idx = st.selectbox("Choose Defender", range(len(st.session_state['team'])), 
                                format_func=lambda i: st.session_state['team'][i]['name'].capitalize(), index=1)
    defender = st.session_state['team'][defender_idx]
    st.image(defender['sprites']['front_default'], width=150)

st.divider()

# --- THE BATTLE LOGIC ---
if st.button("🎲 ROLL FOR ATTACK", type="primary", use_container_width=True):
    # Calculate D&D Values
    atk_mod = get_mod(attacker['stats'][1]['base_stat']) # Attack
    def_ac = 10 + get_mod(defender['stats'][2]['base_stat']) # Defense AC
    
    d20 = random.randint(1, 20)
    total_hit = d20 + atk_mod
    
    st.subheader("📜 Combat Log")
    log_text = f"> {attacker['name'].upper()} rolls a d20: **{d20}** + mod **{atk_mod}** = **{total_hit}**\n"
    
    if total_hit >= def_ac:
        # Hit! Let's pretend we used a basic 80 power move
        dmg_dice = 3 # 3d8
        rolls = [random.randint(1, 8) for _ in range(dmg_dice)]
        total_dmg = sum(rolls) + atk_mod
        
        log_text += f"> **HIT!** (Target AC: {def_ac})\n"
        log_text += f"> Damage Roll (3d8 + {atk_mod}): {rolls} = **{total_dmg} Damage!**"
        st.balloons()
    else:
        log_text += f"> **MISS!** (Target AC: {def_ac})\n"
        log_text += f"> The attack bounced off {defender['name'].capitalize()}'s hide."

    st.markdown(f'<div class="battle-log">{log_text}</div>', unsafe_allow_html=True)
