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
            background-color: #0e1117; color: #00ff00; padding: 15px;
            border-radius: 8px; font-family: 'Courier New', monospace;
            border: 1px solid #333; line-height: 1.4; font-size: 14px;
        }
        .mini-breakdown-box {
            background: rgba(151, 143, 219, 0.1);
            padding: 12px;
            border-radius: 6px;
            border: 1px solid rgba(151, 143, 219, 0.3);
            margin-top: 10px;
            font-size: 13px;
        }
        .turn-order-banner {
            background: #1e1e1e;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #444;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .stat-badge { font-size: 12px; color: #888; margin-left: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. Poke Camp Logic
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
        move_list = []
        for m in res['moves']:
            learn_methods = [v['move_learn_method']['name'] for v in m['version_group_details']]
            if 'level-up' in learn_methods or 'machine' in learn_methods:
                move_list.append(m['move']['name'].replace("-", " ").title())
        return sorted(list(set(move_list)))
    except: return []

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button(f"➡️ Team ({len(st.session_state['team'])}/6)", use_container_width=True): st.switch_page("pages/Team_Builder.py")
if st.sidebar.button("⚔️ Battle Sim", use_container_width=True): st.switch_page("pages/Battle_Sim.py")

# --- INTERFACE ---
st.title("⚔️ Poke Camp Battle Sim")

# Turn Order Logic
attacker_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{st.session_state['attacker_search'].lower()}").json() if st.session_state['attacker_search'] else None
defender_name_raw = st.session_state.get('def_s', "")
defender_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{defender_name_raw.lower()}").json() if defender_name_raw else None

if attacker_data and defender_data:
    atk_spd = attacker_data['stats'][5]['base_stat'] // 15
    def_spd = defender_data['stats'][5]['base_stat'] // 15
    
    if atk_spd >= def_spd:
        st.markdown(f'<div class="turn-order-banner">🏃 {attacker_data["name"].capitalize()} attacks FIRST (Speed: {atk_spd} vs {def_spd})</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="turn-order-banner">🏃 {defender_data["name"].capitalize()} attacks FIRST (Speed: {def_spd} vs {atk_spd})</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
all_names = [p['name'] for p in requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000").json()['results']]

# --- COLUMN 1: ATTACKER ---
with col1:
    st.subheader("🛡️ Attacker")
    a_name = st.selectbox("Attacker", options=[""] + all_names, label_visibility="collapsed",
                          index=all_names.index(st.session_state['attacker_search']) + 1 if st.session_state['attacker_search'] in all_names else 0)
    attacker = requests.get(f"https://pokeapi.co/api/v2/pokemon/{a_name}").json() if a_name else None
    
    if attacker:
        atk_hp = attacker['stats'][0]['base_stat'] // 10
        atk_spd = attacker['stats'][5]['base_stat'] // 15
        st.markdown(f"**HP:** {atk_hp} | **Speed:** {atk_spd}")
        st.image(attacker['sprites']['front_default'], width=120)
        
        all_learnable = get_all_learnable_moves(attacker['name'])
        selected_move = st.selectbox("Choose Move", options=[""] + all_learnable)
        
        # Breakdown ONLY on Attacker Side
        if selected_move and defender_data:
            m_url = f"https://pokeapi.co/api/v2/move/{selected_move.lower().replace(' ', '-')}"
            m_data = requests.get(m_url).json()
            
            p_bonus = get_move_power_bonus(m_data.get('power', 0))
            a_bonus = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
            d_types = [t['type']['name'] for t in defender_data['types']]
            type_mod = get_type_modifier(m_data['type']['name'], d_types)
            d_red = max(defender_data['stats'][2]['base_stat'], defender_data['stats'][4]['base_stat']) // 40
            
            total_pre_roll = a_bonus + p_bonus + (type_mod if type_mod != -999 else 0) - d_red
            
            st.markdown(f"""
            <div class="mini-breakdown-box">
                <b>Atk Bonus:</b> +{a_bonus} | <b>Move:</b> +{p_bonus}<br>
                <b>Type Mod:</b> {type_mod if type_mod != -999 else 'Immune'} | <b>Def Reduct:</b> -{d_red}<br>
                <hr style="margin:5px 0; border-color:rgba(255,255,255,0.1);">
                <b>Expected Damage: <span style="color:#978fdb;">{max(0, total_pre_roll)}</span></b>
            </div>
            """, unsafe_allow_html=True)

# --- COLUMN 2: DEFENDER ---
with col2:
    st.subheader("🎯 Target")
    d_name = st.selectbox("Target", options=[""] + all_names, key="def_s", label_visibility="collapsed")
    defender = requests.get(f"https://pokeapi.co/api/v2/pokemon/{d_name}").json() if d_name else None
    if defender:
        def_hp = defender['stats'][0]['base_stat'] // 10
        def_spd = defender['stats'][5]['base_stat'] // 15
        st.markdown(f"**HP:** {def_hp} | **Speed:** {def_spd}")
        st.image(defender['sprites']['front_default'], width=120)
        
        def_val = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat'])
        def_reduction = def_val // 40
        st.write(f"**Defensive Reduction:** -{def_reduction}")

st.divider()

if st.button("🎲 ROLL ATTACK", type="primary", use_container_width=True):
    if attacker and defender and selected_move:
        m_url = f"https://pokeapi.co/api/v2/move/{selected_move.lower().replace(' ', '-')}"
        m_data = requests.get(m_url).json()
        d20 = random.randint(1, 20)
        
        if d20 >= 8:
            p_bonus = get_move_power_bonus(m_data.get('power', 0))
            a_bonus = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
            d_types = [t['type']['name'] for t in defender['types']]
            type_mod = get_type_modifier(m_data['type']['name'], d_types)
            d_red = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
            
            if type_mod == -999:
                dmg = 0
                res_txt = "🚫 IMMUNE!"
            else:
                dmg = max(0, a_bonus + p_bonus + type_mod + (5 if d20 == 20 else 0) - d_red)
                res_txt = f"💥 HIT for **{dmg}** damage!"
            
            st.markdown(f'<div class="battle-log">Roll: <b>{d20}</b> (8+ hits)<br>{res_txt} {"⭐ NAT 20!" if d20 == 20 else ""}</div>', unsafe_allow_html=True)
            if d20 == 20: st.balloons()
        else:
            st.markdown(f'<div class="battle-log">❌ MISS! Roll: <b>{d20}</b></div>', unsafe_allow_html=True)
