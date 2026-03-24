import streamlit as st
import requests

# 1. Page Config
st.set_page_config(page_title="Team Builder", layout="wide")

# --- INITIALIZATION LOGIC ---
if 'team' not in st.session_state:
    st.session_state['team'] = []
if 'selected_moves' not in st.session_state:
    st.session_state['selected_moves'] = {}
if 'shiny_states' not in st.session_state:
    st.session_state['shiny_states'] = {}

# --- CALLBACKS ---
def delete_pokemon(index):
    # 1. Remove from the team list
    st.session_state['team'].pop(index)
    
    # 2. Re-align dictionaries to fix index shifting
    old_moves = st.session_state['selected_moves']
    old_shiny = st.session_state['shiny_states']
    
    new_moves = {}
    new_shiny = {}
    
    # Rebuild the dictionaries based on the new list order
    for new_idx in range(len(st.session_state['team'])):
        # If we deleted index 1, then old index 2 becomes new index 1
        old_idx = new_idx if new_idx < index else new_idx + 1
        if old_idx in old_moves: new_moves[new_idx] = old_moves[old_idx]
        if old_idx in old_shiny: new_shiny[new_idx] = old_shiny[old_idx]
        
    st.session_state['selected_moves'] = new_moves
    st.session_state['shiny_states'] = new_shiny

# 2. Styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .move-bar-centered {
            color: white; padding: 8px 10px; border-radius: 6px;
            font-size: 11px; font-weight: bold; margin-top: 4px;
            height: 34px; display: flex; align-items: center;
            justify-content: center; text-align: center;
            border-bottom: 3px solid rgba(0,0,0,0.2); text-transform: uppercase;
        }
        .stat-label { font-size: 12px; font-weight: bold; margin-bottom: -5px; }
        .img-container { display: flex; justify-content: center; align-items: center; height: 100%; }
        .analysis-label { font-size: 10px; margin-bottom: 2px; margin-top: 5px; color: #ccc; }
        .column-header { font-size: 11px; font-weight: bold; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

# 3. Helpers
@st.cache_data(ttl=86400)
def get_all_pokemon_names():
    try:
        url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
        return [p['name'] for p in requests.get(url).json()['results']]
    except: return []

@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    if not name: return None
    res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")
    return res.json() if res.status_code == 200 else None

@st.cache_data(ttl=86400)
def get_type_data(type_name):
    try: return requests.get(f"https://pokeapi.co/api/v2/type/{type_name}").json()
    except: return None

@st.cache_data(ttl=86400)
def get_move_details(move_url):
    try: return requests.get(move_url).json()
    except: return None

def calculate_analysis(pokemon_types):
    weak, resist, super_eff, not_very = set(), set(), set(), set()
    def_mults = {}
    for t_info in pokemon_types:
        data = get_type_data(t_info['type']['name'])
        if data:
            rel = data['damage_relations']
            for t in rel['double_damage_from']: def_mults[t['name']] = def_mults.get(t['name'], 1.0) * 2.0
            for t in rel['half_damage_from']: def_mults[t['name']] = def_mults.get(t['name'], 1.0) * 0.5
            for t in rel['no_damage_from']: def_mults[t['name']] = 0.0
            for t in rel['double_damage_to']: super_eff.add(t['name'])
            for t in rel['half_damage_to']: not_very.add(t['name'])
            for t in rel['no_damage_to']: not_very.add(t['name'])
    for t, m in def_mults.items():
        if m > 1.0: weak.add(t)
        elif 0.0 <= m < 1.0: resist.add(t)
    return sorted(list(weak)), sorted(list(resist)), sorted(list(super_eff)), sorted(list(not_very))

def render_badges(types):
    if not types: return '<span style="font-size:10px; color:gray;">None</span>'
    return "".join([f'<span style="background-color:{TYPE_COLORS.get(t,"#777")}; color:white; padding:2px 4px; border-radius:3px; margin:1px; font-size:10px; display:inline-block; font-weight:bold;">{t.upper()[:4]}</span>' for t in types])

def add_move_callback(idx):
    val = st.session_state[f"search_move_{idx}"]
    if val:
        curr = st.session_state['selected_moves'].get(idx, [])
        if len(curr) < 4 and val not in curr:
            curr.append(val)
            st.session_state['selected_moves'][idx] = curr
        st.session_state[f"search_move_{idx}"] = ""

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home Page", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button(f"➡️ Team Builder", use_container_width=True): st.switch_page("pages/Team_Builder.py")
if st.sidebar.button("⚔️ Battle Simulator", use_container_width=True): st.switch_page("pages/Battle_Sim.py")
st.sidebar.divider()
if st.sidebar.button("🗑️ Clear Full Team", type="secondary", use_container_width=True):
    st.session_state['team'] = []; st.session_state['selected_moves'] = {}; st.session_state['shiny_states'] = {}; st.rerun()

# --- MAIN PAGE ---
st.title("🏆 PokéDND Team Builder")
all_names = get_all_pokemon_names()
quick_add = st.selectbox("Quick Add Pokémon:", options=[""] + all_names, format_func=lambda x: x.capitalize() if x else "Search to add...", key="quick_add_team")

if quick_add:
    p_data = get_pokemon_data(quick_add)
    if p_data:
        if len(st.session_state['team']) < 6:
            if not any(p['name'] == p_data['name'] for p in st.session_state['team']):
                st.session_state['team'].append(p_data); st.rerun()
        else: st.error("Team is full!")

st.divider()

if not st.session_state['team']:
    st.info("Your team is empty. Search for a Pokémon above to start.")
else:
    cols = st.columns(3)
    STAT_MAP = {"hp": "HP", "attack": "ATK", "defense": "DEF", "special-attack": "SpA", "special-defense": "SpD", "speed": "Spd"}

    for i in range(len(st.session_state['team'])):
        p_data = st.session_state['team'][i]
        
        if i not in st.session_state['selected_moves']: st.session_state['selected_moves'][i] = []
        if i not in st.session_state['shiny_states']: st.session_state['shiny_states'][i] = False
        
        with cols[i % 3]:
            with st.container(border=True):
                h1, h2, h3 = st.columns([4, 1, 1])
                h1.subheader(p_data['name'].capitalize())
                
                # Shiny Toggle
                shiny_label = "✨" if not st.session_state['shiny_states'][i] else "🌟"
                if h2.button(shiny_label, key=f"shiny_{i}"):
                    st.session_state['shiny_states'][i] = not st.session_state['shiny_states'][i]
                    st.rerun()

                # MODIFIED: Trash Button with Callback
                # We use on_click to ensure the deletion happens before the loop reruns
                h3.button("🗑️", key=f"rem_p_{i}", on_click=delete_pokemon, args=(i,))

                r1c1, r1c2 = st.columns([1.2, 2])
                with r1c1:
                    sprite = 'front_shiny' if st.session_state['shiny_states'][i] else 'front_default'
                    st.image(p_data['sprites'][sprite], width=180)
                with r1c2:
                    for s in p_data['stats']:
                        label = STAT_MAP.get(s['stat']['name'], s['stat']['name'].upper())
                        val = s['base_stat']
                        st.markdown(f'<div class="stat-label">{label}: {val}</div>', unsafe_allow_html=True)
                        st.progress(min(val / 160, 1.0))

                weak, resist, super_eff, not_very = calculate_analysis(p_data['types'])
                st.markdown('<div style="margin-top:10px; border-top:1px solid #444; padding-top:8px;"></div>', unsafe_allow_html=True)
                
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.markdown('<div class="column-header" style="color:#ff4b4b;">🛡️ DEFENSE</div>', unsafe_allow_html=True)
                    st.markdown('<div class="analysis-label">Weak Against:</div>', unsafe_allow_html=True)
                    st.markdown(render_badges(weak), unsafe_allow_html=True)
                    st.markdown('<div class="analysis-label">Resistant to:</div>', unsafe_allow_html=True)
                    st.markdown(render_badges(resist), unsafe_allow_html=True)
                with t_col2:
                    st.markdown('<div class="column-header" style="color:#3498db;">⚔️ OFFENSE</div>', unsafe_allow_html=True)
                    st.markdown('<div class="analysis-label">Super Effective:</div>', unsafe_allow_html=True)
                    st.markdown(render_badges(super_eff), unsafe_allow_html=True)
                    st.markdown('<div class="analysis-label">Not Effective:</div>', unsafe_allow_html=True)
                    st.markdown(render_badges(not_very), unsafe_allow_html=True)

                st.divider()

                all_m = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in p_data['moves']])))
                st.selectbox("Add Move", options=[""] + all_m, key=f"search_move_{i}", on_change=add_move_callback, args=(i,), label_visibility="collapsed")
                
                for m_idx, m_name in enumerate(st.session_state['selected_moves'][i]):
                    api_n = m_name.lower().replace(" ", "-")
                    try:
                        m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == api_n)
                        m_details = get_move_details(m_url)
                        pwr = m_details.get('power')
                        pwr_label = f"({pwr})" if pwr else "(---)"
                        
                        bg_color = TYPE_COLORS.get(m_details['type']['name'], "#978fdb")
                        m_c1, m_c2 = st.columns([5, 1])
                        with m_c1: st.markdown(f'<div class="move-bar-centered" style="background-color: {bg_color};">{m_name} {pwr_label}</div>', unsafe_allow_html=True)
                        with m_c2: 
                            if st.button("✖", key=f"del_m_{i}_{m_idx}"):
                                st.session_state['selected_moves'][i].pop(m_idx); st.rerun()
                    except: continue
