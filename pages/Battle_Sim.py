import streamlit as st
import requests
import random

# 1. Page Config
st.set_page_config(page_title="Battle Simulator", layout="wide")

# --- INITIALIZATION ---
if 'team' not in st.session_state: st.session_state['team'] = []
if 'selected_moves' not in st.session_state: st.session_state['selected_moves'] = {}
if 'attacker_search' not in st.session_state: st.session_state['attacker_search'] = ""

# 2. Styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .battle-log {
            background-color: #0e1117; color: #00ff00; padding: 20px;
            border-radius: 10px; font-family: 'Courier New', monospace;
            border: 1px solid #333; line-height: 1.6;
        }
        .stat-chip { background: #333; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# 3. Poke Camp Logic Functions
def get_move_power_bonus(power):
    if not power: return 0
    if 10 <= power <= 40: return 1
    if 41 <= power <= 60: return 2
    if 61 <= power <= 75: return 3
    if 76 <= power <= 90: return 4
    if 91 <= power <= 110: return 5
    if 111 <= power <= 130: return 6
    if power >= 131: return 7
    return 0

@st.cache_data(ttl=86400)
def get_type_modifier(move_type, defender_types):
    url = f"https://pokeapi.co/api/v2/type/{move_type.lower()}"
    res = requests.get(url).json()
    relations = res['damage_relations']
    
    mod = 0
    for d_type in defender_types:
        if any(t['name'] == d_type for t in relations['double_damage_to']): mod += 2
        if any(t['name'] == d_type for t in relations['half_damage_to']): mod -= 2
        if any(t['name'] == d_type for t in relations['no_damage_to']): return -999 # Indicator for Immunity
    return mod

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home Page", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button(f"➡️ Team Builder ({len(st.session_state['team'])}/6)", use_container_width=True): st.switch_page("pages/Team_Builder.py")
if st.sidebar.button("⚔️ Battle Simulator", use_container_width=True): st.switch_page("pages/Battle_Sim.py")

# --- MAIN INTERFACE ---
st.title("⚔️ Poke Camp Battle Sim")

# Team Ribbon for Quick Select
if st.session_state['team']:
    st.write("### 👥 Quick Select Attacker")
    ribbon = st.columns(6)
    for i, p in enumerate(st.session_state['team']):
        with ribbon[i]:
            st.image(p['sprites']['front_default'], width=80)
            if st.button(f"Select {p['name'].capitalize()}", key=f"q_{i}"):
                st.session_state['attacker_search'] = p['name']; st.rerun()

st.divider()

col1, col2 = st.columns(2)
all_names = [p['name'] for p in requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000").json()['results']]

with col1:
    st.subheader("🛡️ Attacker")
    a_name = st.selectbox("Search Attacker", options=[""] + all_names, 
                          index=all_names.index(st.session_state['attacker_search']) + 1 if st.session_state['attacker_search'] in all_names else 0)
    attacker = requests.get(f"https://pokeapi.co/api/v2/pokemon/{a_name}").json() if a_name else None
    if attacker:
        st.image(attacker['sprites']['front_default'], width=150)
        atk_stat = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat'])
        atk_bonus = atk_stat // 20
        speed_val = attacker['stats'][5]['base_stat'] // 15
        st.write(f"**Offensive Bonus:** +{atk_bonus} | **Speed:** {speed_val}")
        
        team_idx = next((i for i, p in enumerate(st.session_state['team']) if p['name'] == attacker['name']), None)
        moves = st.session_state.get('selected_moves', {}).get(team_idx, []) if team_idx is not None else [m['move']['name'].title() for m in attacker['moves']]
        selected_move = st.selectbox("Choose Move", options=[""] + moves)

with col2:
    st.subheader("🎯 Target")
    d_name = st.selectbox("Search Target", options=[""] + all_names, key="def_s")
    defender = requests.get(f"https://pokeapi.co/api/v2/pokemon/{d_name}").json() if d_name else None
    if defender:
        st.image(defender['sprites']['front_default'], width=150)
        def_stat = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat'])
        def_reduction = def_stat // 40
        hp_val = defender['stats'][0]['base_stat'] // 10
        st.write(f"**Defensive Reduction:** -{def_reduction} | **Total HP:** {hp_val}")

st.divider()

# --- BATTLE ENGINE ---
if st.button("🎲 ROLL ATTACK", type="primary", use_container_width=True):
    if attacker and defender and selected_move:
        # Fetch move details
        m_url = f"https://pokeapi.co/api/v2/move/{selected_move.lower().replace(' ', '-')}"
        m_data = requests.get(m_url).json()
        
        d20 = random.randint(1, 20)
        log = f"**{attacker['name'].upper()}** uses **{selected_move.upper()}**!<br>"
        log += f"Accuracy Roll: **{d20}** (8+ Hits)<br>"
        
        if d20 >= 8:
            # 1. Start with Move Power Bonus
            p_bonus = get_move_power_bonus(m_data.get('power', 0))
            
            # 2. Add Attacker Stat Bonus
            a_bonus = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
            
            # 3. Type Effectiveness
            d_types = [t['type']['name'] for t in defender['types']]
            type_mod = get_type_modifier(m_data['type']['name'], d_types)
            
            # 4. Nat 20 Bonus
            crit_bonus = 5 if d20 == 20 else 0
            
            # 5. Defender Reduction
            d_reduction = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
            
            if type_mod == -999:
                final_damage = 0
                log += "🚫 **IMMUNE!** The target is unaffected.<br>"
            else:
                final_damage = p_bonus + a_bonus + type_mod + crit_bonus - d_reduction
                final_damage = max(0, final_damage) # Can't do negative damage
                
                log += f"--- Math Breakdown ---<br>"
                log += f"Move Power ({m_data.get('power',0)}): +{p_bonus}<br>"
                log += f"Attacker Stat: +{a_bonus}<br>"
                if type_mod != 0: log += f"Type Advantage: {'+' if type_mod>0 else ''}{type_mod}<br>"
                if d20 == 20: log += "⭐ **NAT 20:** +5<br>"
                log += f"Defender Reduction: -{d_reduction}<br>"
                log += f"**TOTAL DAMAGE: {final_damage}**"
                
            st.markdown(f'<div class="battle-log">{log}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="battle-log">❌ **MISS!** ({d20} is below 8)</div>', unsafe_allow_html=True)
    else:
        st.error("Select Attacker, Target, and Move.")
