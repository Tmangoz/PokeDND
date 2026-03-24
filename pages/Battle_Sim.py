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
        .breakdown-box {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #978fdb;
            margin-bottom: 20px;
        }
        .bonus-val { color: #978fdb; font-weight: bold; float: right; }
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
    try:
        url = f"https://pokeapi.co/api/v2/type/{move_type.lower()}"
        res = requests.get(url).json()
        relations = res['damage_relations']
        
        mod = 0
        for d_type in defender_types:
            if any(t['name'] == d_type for t in relations['double_damage_to']): mod += 2
            if any(t['name'] == d_type for t in relations['half_damage_to']): mod -= 2
            if any(t['name'] == d_type for t in relations['no_damage_to']): return -999 
        return mod
    except: return 0

@st.cache_data(ttl=86400)
def get_all_learnable_moves(pokemon_name):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        res = requests.get(url).json()
        # Filter for Level-up or Machine (TM) moves
        move_list = []
        for m in res['moves']:
            learn_methods = [v['move_learn_method']['name'] for v in m['version_group_details']]
            if 'level-up' in learn_methods or 'machine' in learn_methods:
                move_list.append(m['move']['name'].replace("-", " ").title())
        return sorted(list(set(move_list)))
    except: return []

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home Page", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button(f"➡️ Team Builder ({len(st.session_state['team'])}/6)", use_container_width=True): st.switch_page("pages/Team_Builder.py")
if st.sidebar.button("⚔️ Battle Simulator", use_container_width=True): st.switch_page("pages/Battle_Sim.py")

# --- MAIN INTERFACE ---
st.title("⚔️ Poke Camp Battle Sim")

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

# --- COLUMN 1: ATTACKER ---
with col1:
    st.subheader("🛡️ Attacker")
    a_name = st.selectbox("Search Attacker", options=[""] + all_names, 
                          index=all_names.index(st.session_state['attacker_search']) + 1 if st.session_state['attacker_search'] in all_names else 0)
    attacker = requests.get(f"https://pokeapi.co/api/v2/pokemon/{a_name}").json() if a_name else None
    
    if attacker:
        st.image(attacker['sprites']['front_default'], width=150)
        
        # Stat Calculations
        atk_val = attacker['stats'][1]['base_stat']
        spa_val = attacker['stats'][3]['base_stat']
        max_atk = max(atk_val, spa_val)
        stat_name = "ATK" if atk_val >= spa_val else "SpA"
        atk_bonus = max_atk // 20
        
        # Fetch ALL Learnable Moves (Natural + TM)
        all_learnable = get_all_learnable_moves(attacker['name'])
        selected_move = st.selectbox("Choose Move:", options=[""] + all_learnable)

# --- COLUMN 2: TARGET ---
with col2:
    st.subheader("🎯 Target")
    d_name = st.selectbox("Select Target", options=[""] + all_names, key="def_s")
    defender = requests.get(f"https://pokeapi.co/api/v2/pokemon/{d_name}").json() if d_name else None
    if defender:
        st.image(defender['sprites']['front_default'], width=150)
        def_val = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat'])
        def_reduction = def_val // 40
        hp_val = defender['stats'][0]['base_stat'] // 10
        st.info(f"❤️ Max HP: {hp_val} | 🛡️ Reduction: -{def_reduction}")

# --- OFFENSIVE BONUS BREAKDOWN ---
if attacker and selected_move:
    st.write("### 📊 Offensive Bonus Breakdown")
    m_url = f"https://pokeapi.co/api/v2/move/{selected_move.lower().replace(' ', '-')}"
    m_data = requests.get(m_url).json()
    
    p_bonus = get_move_power_bonus(m_data.get('power', 0))
    type_mod = 0
    if defender:
        d_types = [t['type']['name'] for t in defender['types']]
        type_mod = get_type_modifier(m_data['type']['name'], d_types)

    with st.container():
        st.markdown(f"""
        <div class="breakdown-box">
            <div><b>Stat Bonus</b> ({stat_name}: {max_atk}) <span class="bonus-val">+{atk_bonus}</span></div>
            <div style="margin-top:5px;"><b>Move Power</b> ({m_data.get('power', 0) if m_data.get('power') else 'Status'}) <span class="bonus-val">+{p_bonus}</span></div>
            <div style="margin-top:5px;"><b>Type Advantage</b> <span class="bonus-val">{'0' if type_mod == -999 else (f'+{type_mod}' if type_mod > 0 else type_mod)}</span></div>
            <hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1);">
            <div style="font-size: 1.1em;"><b>Total Pre-Roll Bonus:</b> <span class="bonus-val">+{atk_bonus + p_bonus + (type_mod if type_mod != -999 else 0)}</span></div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# --- BATTLE ENGINE ---
if st.button("🎲 ROLL ATTACK", type="primary", use_container_width=True):
    if attacker and defender and selected_move:
        m_url = f"https://pokeapi.co/api/v2/move/{selected_move.lower().replace(' ', '-')}"
        m_data = requests.get(m_url).json()
        
        d20 = random.randint(1, 20)
        log = f"**{attacker['name'].upper()}** uses **{selected_move.upper()}**!<br>"
        log += f"Accuracy Roll: <span class='dice-roll'>{d20}</span> (8+ Hits)<br>"
        
        if d20 >= 8:
            p_bonus = get_move_power_bonus(m_data.get('power', 0))
            a_bonus = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
            d_types = [t['type']['name'] for t in defender['types']]
            type_mod = get_type_modifier(m_data['type']['name'], d_types)
            crit_bonus = 5 if d20 == 20 else 0
            d_reduction = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
            
            if type_mod == -999:
                log += "🚫 **IMMUNE!** Target took 0 damage.<br>"
            else:
                final_damage = p_bonus + a_bonus + type_mod + crit_bonus - d_reduction
                final_damage = max(0, final_damage)
                log += f"💥 **HIT!** Dealt **{final_damage} damage**!<br>"
                if d20 == 20: log += "⭐ **NAT 20:** +5 Critical Damage applied!"
                st.balloons()
            st.markdown(f'<div class="battle-log">{log}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="battle-log">❌ **MISS!** ({d20} is less than 8)</div>', unsafe_allow_html=True)
