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
TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

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
            background: #1e1e1e; padding: 10px; border-radius: 10px;
            text-align: center; border: 1px solid #444; margin-bottom: 20px; font-weight: bold;
        }
        .type-badge {
            color: white; padding: 2px 8px; border-radius: 4px;
            font-size: 10px; font-weight: bold; text-transform: uppercase;
            margin-left: 5px; display: inline-block;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Helpers
def get_mod(stat_value):
    return (stat_value - 100) // 10

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

def render_type_badges(pokemon_data):
    badges = ""
    for t in pokemon_data['types']:
        t_name = t['type']['name']
        color = TYPE_COLORS.get(t_name, "#777")
        badges += f'<span class="type-badge" style="background-color: {color};">{t_name}</span>'
    return badges

@st.cache_data(ttl=86400)
def get_type_modifier(move_type, defender_types):
    try:
        url = f"https://pokeapi.co/api/v2/type/{move_type.lower()}"
        res = requests.get(url).json()
        rel = res['damage_relations']
        mod = 0
        for d_type in defender_types:
            if any(t['name'] == d_type for t in rel['double_damage_to']): mod += 2
            if any(t['name'] == d_type for t in rel['half_damage_to']): mod -= 2
            if any(t['name'] == d_type for t in rel['no_damage_to']): return -999 
        return mod
    except: return 0

@st.cache_data(ttl=86400)
def get_all_learnable_moves(pokemon_name):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        res = requests.get(url).json()
        move_list = [m['move']['name'].replace("-", " ").title() for m in res['moves']]
        return sorted(list(set(move_list)))
    except: return []

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button(f"➡️ Team Builder", use_container_width=True): st.switch_page("pages/Team_Builder.py")
if st.sidebar.button("⚔️ Battle Sim", use_container_width=True): st.switch_page("pages/Battle_Sim.py")

# --- INTERFACE ---
st.title("⚔️ Poke Camp Battle Sim")

# Data fetching for Banner
atk_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{st.session_state['attacker_search'].lower()}").json() if st.session_state['attacker_search'] else None
def_name_raw = st.session_state.get('def_s', "")
def_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{def_name_raw.lower()}").json() if def_name_raw else None

if atk_data and def_data:
    atk_spd = atk_data['stats'][5]['base_stat'] // 15
    def_spd = def_data['stats'][5]['base_stat'] // 15
    first = atk_data['name'].capitalize() if atk_spd >= def_spd else def_data['name'].capitalize()
    st.markdown(f'<div class="turn-order-banner">🏃 {first} attacks FIRST (Speed: {max(atk_spd, def_spd)} vs {min(atk_spd, def_spd)})</div>', unsafe_allow_html=True)

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
        st.markdown(f"**HP:** {atk_hp} | **Speed:** {atk_spd} {render_type_badges(attacker)}", unsafe_allow_html=True)
        st.image(attacker['sprites']['front_default'], width=120)
        
        selected_move = st.selectbox("Choose Move", options=[""] + get_all_learnable_moves(attacker['name']))
        
        if selected_move and def_data:
            m_res = requests.get(f"https://pokeapi.co/api/v2/move/{selected_move.lower().replace(' ', '-')}").json()
            p_bonus = get_move_power_bonus(m_res.get('power', 0))
            a_bonus = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
            d_types = [t['type']['name'] for t in def_data['types']]
            type_mod = get_type_modifier(m_res['type']['name'], d_types)
            d_red = max(def_data['stats'][2]['base_stat'], def_data['stats'][4]['base_stat']) // 40
            
            total_pre = a_bonus + p_bonus + (type_mod if type_mod != -999 else 0) - d_red
            st.markdown(f"""
            <div class="mini-breakdown-box">
                <b>Atk:</b> +{a_bonus} | <b>Move:</b> +{p_bonus}<br>
                <b>Type:</b> {type_mod if type_mod != -999 else 'Immune'} | <b>Def Reduct:</b> -{d_red}<br>
                <hr style="margin:5px 0; border-color:rgba(255,255,255,0.1);">
                <b>Expected Damage: <span style="color:#978fdb;">{max(0, total_pre)}</span></b>
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
        st.markdown(f"**HP:** {def_hp} | **Speed:** {def_spd} {render_type_badges(defender)}", unsafe_allow_html=True)
        st.image(defender['sprites']['front_default'], width=120)
        def_red = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
        st.write(f"**Defensive Reduction:** -{def_red}")

st.divider()

if st.button("🎲 ROLL ATTACK", type="primary", use_container_width=True):
    if attacker and defender and selected_move:
        m_res = requests.get(f"https://pokeapi.co/api/v2/move/{selected_move.lower().replace(' ', '-')}").json()
        d20 = random.randint(1, 20)
        if d20 >= 8:
            p_bonus = get_move_power_bonus(m_res.get('power', 0))
            a_bonus = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
            type_mod = get_type_modifier(m_res['type']['name'], [t['type']['name'] for t in defender['types']])
            d_red = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
            
            if type_mod == -999: dmg = 0
            else: dmg = max(0, a_bonus + p_bonus + type_mod + (5 if d20 == 20 else 0) - d_red)
            
            st.markdown(f'<div class="battle-log">Roll: <b>{d20}</b> (8+ hits)<br>💥 DEALT **{dmg}** DAMAGE! {"⭐ NAT 20!" if d20 == 20 else ""}</div>', unsafe_allow_html=True)
            if d20 == 20: st.balloons()
        else:
            st.markdown(f'<div class="battle-log">❌ MISS! Roll: <b>{d20}</b></div>', unsafe_allow_html=True)
