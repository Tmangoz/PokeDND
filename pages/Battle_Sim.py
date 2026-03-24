import streamlit as st
import requests
import random

# 1. Page Config
st.set_page_config(page_title="Battle Simulator", layout="wide")

# --- INITIALIZATION ---
# Ensure all state keys exist so they don't reset to None
if 'team' not in st.session_state: st.session_state['team'] = []
if 'selected_moves' not in st.session_state: st.session_state['selected_moves'] = {}
if 'attacker_search' not in st.session_state: st.session_state['attacker_search'] = ""
if 'def_s' not in st.session_state: st.session_state['def_s'] = ""
if 'atk_tmp' not in st.session_state: st.session_state['atk_tmp'] = []
if 'def_moves_list' not in st.session_state: st.session_state['def_moves_list'] = []

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
            border: 1px solid #333; line-height: 1.4; font-size: 14px; margin-top: 10px;
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
        .move-card {
            border: 1px solid #444; border-radius: 8px; padding: 10px;
            text-align: center; background: rgba(255,255,255,0.03);
            margin-bottom: 10px; min-height: 150px;
        }
        .breakdown-text { font-size: 11px; color: #aaa; line-height: 1.1; }
        .total-dmg { font-size: 15px; color: #978fdb; font-weight: bold; margin-top: 5px;}
    </style>
""", unsafe_allow_html=True)

# 3. Helpers
def get_move_power_bonus(power):
    if not power: return 0
    if 10 <= power <= 40: return 1
    elif 41 <= power <= 60: return 2
    elif 61 <= power <= 75: return 3
    elif 76 <= power <= 90: return 4
    elif 91 <= power <= 110: return 5
    elif 111 <= power <= 130: return 6
    return 7 if power >= 131 else 0

def render_type_badges(p_data):
    badges = ""
    for t in p_data.get('types', []):
        t_name = t['type']['name']
        badges += f'<span class="type-badge" style="background-color: {TYPE_COLORS.get(t_name, "#777")};">{t_name}</span>'
    return badges

@st.cache_data(ttl=86400)
def get_type_modifier(move_type, defender_types):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/type/{move_type.lower()}").json()
        rel = res['damage_relations']
        mod = 0
        for d_type in defender_types:
            if any(t['name'] == d_type for t in rel['double_damage_to']): mod += 2
            if any(t['name'] == d_type for t in rel['half_damage_to']): mod -= 2
            if any(t['name'] == d_type for t in rel['no_damage_to']): return -999 
        return mod
    except: return 0

@st.cache_data(ttl=86400)
def get_move_info(move_name):
    try: return requests.get(f"https://pokeapi.co/api/v2/move/{move_name.lower().replace(' ', '-')}").json()
    except: return None

@st.cache_data(ttl=86400)
def get_all_learnable_moves(pokemon_name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}").json()
        return sorted(list(set([m['move']['name'].replace("-", " ").title() for m in res['moves']])))
    except: return []

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home Page", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button(f"➡️ Team Builder ({len(st.session_state['team'])}/6)", use_container_width=True): st.switch_page("pages/Team_Builder.py")
if st.sidebar.button("⚔️ Battle Simulator", use_container_width=True): st.switch_page("pages/Battle_Sim.py")
st.sidebar.divider()
force_crit = st.sidebar.checkbox("🎯 Force Nat 20 (Crit Hit)")

# --- MAIN INTERFACE ---
st.title("⚔️ Poke Camp Battle Sim")

# Team Ribbon
if st.session_state['team']:
    ribbon = st.columns(6)
    for i, p in enumerate(st.session_state['team']):
        with ribbon[i]:
            shiny = st.session_state.get('shiny_states', {}).get(i, False)
            st.image(p['sprites']['front_shiny' if shiny else 'front_default'], width=80)
            if st.button(f"Select {p['name'].capitalize()}", key=f"q_{i}", use_container_width=True):
                st.session_state['attacker_search'] = p['name']
                st.rerun()

st.divider()

# Get Full List of Pokemon
all_p = [p['name'] for p in requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000").json()['results']]

col1, col2 = st.columns(2)

# Roll Processor
def process_roll(p_atk, p_def, m_name, m_info):
    roll = 20 if force_crit else random.randint(1, 20)
    p_bon = get_move_power_bonus(m_info.get('power', 0))
    a_bon = max(p_atk['stats'][1]['base_stat'], p_atk['stats'][3]['base_stat']) // 20
    tm = get_type_modifier(m_info['type']['name'], [t['type']['name'] for t in p_def['types']])
    dr = max(p_def['stats'][2]['base_stat'], p_def['stats'][4]['base_stat']) // 40
    if roll >= 8:
        final = 0 if tm == -999 else max(0, a_bon + p_bon + tm + (5 if roll == 20 else 0) - dr)
        st.session_state['last_log'] = f"🎲 **{roll}** | **{p_atk['name'].capitalize()}** dealt **{final}** Damage with **{m_name}**"
    else: st.session_state['last_log'] = f"🎲 **{roll}** | **{p_atk['name'].capitalize()}** missed!"
    st.rerun()

# --- COLUMN 1: ATTACKER ---
with col1:
    st.subheader("🛡️ Attacker")
    val_a = st.selectbox("Search Attacker", options=[""] + all_p, index=all_p.index(st.session_state['attacker_search']) + 1 if st.session_state['attacker_search'] in all_p else 0, key="atk_selector")
    if val_a != st.session_state['attacker_search']:
        st.session_state['attacker_search'] = val_a
        st.session_state['atk_tmp'] = []
        st.rerun()

    atk_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{val_a.lower()}").json() if val_a else None
    if atk_data:
        a_red = max(atk_data['stats'][2]['base_stat'], atk_data['stats'][4]['base_stat']) // 40
        st.markdown(f"**HP:** {atk_data['stats'][0]['base_stat']//10} | **Speed:** {atk_data['stats'][5]['base_stat']//15} {render_type_badges(atk_data)}", unsafe_allow_html=True)
        st.image(atk_data['sprites']['front_default'], width=100)
        st.write(f"**Reduction:** -{a_red}")

        # Moves
        team_idx = next((i for i, p in enumerate(st.session_state['team']) if p['name'] == val_a), None)
        if team_idx is not None:
            a_moves = st.session_state.get('selected_moves', {}).get(team_idx, [])
        else:
            sm_a = st.selectbox("Add Attacker Move", options=[""] + get_all_learnable_moves(val_a), key="atk_move_adder")
            if sm_a and sm_a not in st.session_state['atk_tmp'] and len(st.session_state['atk_tmp']) < 4:
                st.session_state['atk_tmp'].append(sm_a); st.rerun()
            a_moves = st.session_state['atk_tmp']
            if st.button("Clear Attacker Moves", key="cl_atk"): st.session_state['atk_tmp'] = []; st.rerun()

# --- COLUMN 2: TARGET ---
with col2:
    st.subheader("🎯 Target")
    val_d = st.selectbox("Search Target", options=[""] + all_p, index=all_p.index(st.session_state['def_s']) + 1 if st.session_state['def_s'] in all_p else 0, key="def_selector")
    if val_d != st.session_state['def_s']:
        st.session_state['def_s'] = val_d
        st.session_state['def_moves_list'] = []
        st.rerun()

    def_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{val_d.lower()}").json() if val_d else None
    if def_data:
        d_red = max(def_data['stats'][2]['base_stat'], def_data['stats'][4]['base_stat']) // 40
        st.markdown(f"**HP:** {def_data['stats'][0]['base_stat']//10} | **Speed:** {def_data['stats'][5]['base_stat']//15} {render_type_badges(def_data)}", unsafe_allow_html=True)
        st.image(def_data['sprites']['front_default'], width=100)
        st.write(f"**Reduction:** -{d_red}")

        # Moves
        def_team_idx = next((i for i, p in enumerate(st.session_state['team']) if p['name'] == val_d), None)
        if def_team_idx is not None:
            d_moves = st.session_state.get('selected_moves', {}).get(def_team_idx, [])
        else:
            sm_d = st.selectbox("Add Target Move", options=[""] + get_all_learnable_moves(val_d), key="def_move_adder")
            if sm_d and sm_d not in st.session_state['def_moves_list'] and len(st.session_state['def_moves_list']) < 4:
                st.session_state['def_moves_list'].append(sm_d); st.rerun()
            d_moves = st.session_state['def_moves_list']
            if st.button("Clear Target Moves", key="cl_def"): st.session_state['def_moves_list'] = []; st.rerun()

# --- BATTLE GRIDS ---
st.divider()
if atk_data and def_data:
    # Banner
    as_val, ds_val = atk_data['stats'][5]['base_stat'] // 15, def_data['stats'][5]['base_stat'] // 15
    f_p = atk_data['name'].capitalize() if as_val >= ds_val else def_data['name'].capitalize()
    st.markdown(f'<div class="turn-order-banner">🏃 {f_p} acts FIRST (Speed: {max(as_val, ds_val)} vs {min(as_val, ds_val)})</div>', unsafe_allow_html=True)

    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        st.write(f"**{atk_data['name'].capitalize()} Actions**")
        m_g1 = st.columns(2)
        for i, mn in enumerate(a_moves):
            mi = get_move_info(mn)
            if mi:
                pb, ab = get_move_power_bonus(mi.get('power', 0)), max(atk_data['stats'][1]['base_stat'], atk_data['stats'][3]['base_stat']) // 20
                tm = get_type_modifier(mi['type']['name'], [t['type']['name'] for t in def_data['types']])
                dr = max(def_data['stats'][2]['base_stat'], def_data['stats'][4]['base_stat']) // 40
                exp = 0 if tm == -999 else max(0, ab + pb + tm + (5 if force_crit else 0) - dr)
                with m_g1[i % 2]:
                    st.markdown(f'<div class="move-card"><b style="color:{TYPE_COLORS.get(mi["type"]["name"],"#444")};">{mn.upper()}</b><br><div class="breakdown-text">Atk: +{ab} | Pwr: +{pb}<br>Type: {tm if tm != -999 else "Immune"} | Crit: {5 if force_crit else 0}<br>Tgt Red: -{dr}</div><div class="total-dmg">Total: {exp}</div></div>', unsafe_allow_html=True)
                    if st.button("Roll", key=f"aroll_{i}"): process_roll(atk_data, def_data, mn, mi)

    with g_col2:
        st.write(f"**{def_data['name'].capitalize()} Actions**")
        m_g2 = st.columns(2)
        for i, mn in enumerate(d_moves):
            mi = get_move_info(mn)
            if mi:
                pb, ab = get_move_power_bonus(mi.get('power', 0)), max(def_data['stats'][1]['base_stat'], def_data['stats'][3]['base_stat']) // 20
                tm = get_type_modifier(mi['type']['name'], [t['type']['name'] for t in atk_data['types']])
                dr = max(atk_data['stats'][2]['base_stat'], atk_data['stats'][4]['base_stat']) // 40
                exp = 0 if tm == -999 else max(0, ab + pb + tm + (5 if force_crit else 0) - dr)
                with m_g2[i % 2]:
                    st.markdown(f'<div class="move-card"><b style="color:{TYPE_COLORS.get(mi["type"]["name"],"#444")};">{mn.upper()}</b><br><div class="breakdown-text">Atk: +{ab} | Pwr: +{pb}<br>Type: {tm if tm != -999 else "Immune"} | Crit: {5 if force_crit else 0}<br>Tgt Red: -{dr}</div><div class="total-dmg">Total: {exp}</div></div>', unsafe_allow_html=True)
                    if st.button("Roll", key=f"droll_{i}"): process_roll(def_data, atk_data, mn, mi)

if 'last_log' in st.session_state:
    st.markdown(f'<div class="battle-log">{st.session_state["last_log"]}</div>', unsafe_allow_html=True)
