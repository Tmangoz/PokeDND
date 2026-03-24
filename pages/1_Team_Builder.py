import streamlit as st
import requests

# 1. Page Config
st.set_page_config(page_title="Team Builder", layout="wide", initial_sidebar_state="expanded")

TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

@st.cache_data(ttl=86400)
def get_type_data(type_name):
    try: return requests.get(f"https://pokeapi.co/api/v2/type/{type_name}").json()
    except: return None

@st.cache_data(ttl=86400)
def get_move_details(move_url):
    try: return requests.get(move_url).json()
    except: return None

def calculate_analysis(pokemon_types):
    weak, resist, immune_def = [], [], [] # Fixed: Initialized immune_def here
    super_eff = set()
    def_mults = {}
    
    for t_info in pokemon_types:
        data = get_type_data(t_info['type']['name'])
        if data:
            rel = data['damage_relations']
            # Defensive
            for t in rel['double_damage_from']: def_mults[t['name']] = def_mults.get(t['name'], 1.0) * 2.0
            for t in rel['half_damage_from']: def_mults[t['name']] = def_mults.get(t['name'], 1.0) * 0.5
            for t in rel['no_damage_from']: def_mults[t['name']] = 0.0
            # Offensive
            for t in rel['double_damage_to']: super_eff.add(t['name'])
            
    for t, m in def_mults.items():
        if m > 1.0: weak.append(t)
        elif 0.0 < m < 1.0: resist.append(t)
        elif m == 0.0: immune_def.append(t)
            
    return sorted(weak), sorted(resist), sorted(list(super_eff))

def render_badges(types):
    if not types: return '<span style="font-size:10px; color:gray;">None</span>'
    return "".join([f'<span style="background-color:{TYPE_COLORS.get(t,"#777")}; color:white; padding:1px 4px; border-radius:4px; margin:1px; font-size:9px; display:inline-block; font-weight:bold;">{t.upper()}</span>' for t in types])

def add_move_callback(idx):
    val = st.session_state[f"search_{idx}"]
    if val:
        curr = st.session_state['selected_moves'].get(idx, [])
        if len(curr) < 4 and val not in curr:
            curr.append(val)
            st.session_state['selected_moves'][idx] = curr
        st.session_state[f"search_{idx}"] = ""

st.title("🏆 PokéDND Team Builder")

if 'team' not in st.session_state or not st.session_state['team']:
    st.info("Your team is empty! Go back to the Explorer to add some Pokémon.")
else:
    cols = st.columns(3)
    
    for i, p_data in enumerate(st.session_state['team']):
        if i not in st.session_state['selected_moves']: st.session_state['selected_moves'][i] = []
        
        with cols[i % 3]:
            with st.container(border=True):
                # Header
                h1, h2 = st.columns([4, 1])
                h1.subheader(p_data['name'].capitalize())
                if h2.button("🗑️", key=f"rem_p_{i}"):
                    st.session_state['team'].pop(i); st.session_state['selected_moves'].pop(i, None); st.rerun()

                # Row 1: Image & Large Stats
                r1c1, r1c2 = st.columns([1, 1.1])
                with r1c1:
                    st.image(p_data['sprites']['front_default'], width=110)
                with r1c2:
                    # Bolder, larger stats (13px)
                    stats_html = "".join([f'<div style="font-size:13px; line-height:1.5; margin-bottom:1px;"><b>{s["stat"]["name"].replace("special-","S").upper()[:5]}:</b> {s["base_stat"]}</div>' for s in p_data['stats']])
                    st.markdown(stats_html, unsafe_allow_html=True)

                # Row 2: Type Analysis
                weak, resist, super_eff = calculate_analysis(p_data['types'])
                st.markdown(f'''
                    <div style="background:rgba(255,255,255,0.07); padding:6px; border-radius:5px; margin:8px 0;">
                        <div style="font-size:10px; margin-bottom:2px;"><b>WEAK:</b> {render_badges(weak)}</div>
                        <div style="font-size:10px; margin-bottom:2px;"><b>RESIST:</b> {render_badges(resist)}</div>
                        <div style="font-size:10px; color:#3498db;"><b>STR VS:</b> {render_badges(super_eff)}</div>
                    </div>
                ''', unsafe_allow_html=True)

                # Row 3: Move Selection
                all_m = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in p_data['moves']])))
                st.selectbox("Add Move", options=[""] + all_m, key=f"search_{i}", on_change=add_move_callback, args=(i,), label_visibility="collapsed")
                
                # Row 4: Active Moves
                for m_idx, m_name in enumerate(st.session_state['selected_moves'][i]):
                    api_n = m_name.lower().replace(" ", "-")
                    try:
                        m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == api_n)
                        m_details = get_move_details(m_url)
                        if m_details:
                            bg = TYPE_COLORS.get(m_details['type']['name'], "#777")
                            m_col, x_col = st.columns([5, 1.2])
                            m_col.markdown(f'''
                                <div style="background-color:{bg}; color:white; padding:4px 10px; border-radius:4px; font-size:11px; font-weight:bold; margin-top:3px; height:28px; display:flex; align-items:center;">
                                    {m_name.upper()}
                                </div>
                            ''', unsafe_allow_html=True)
                            if x_col.button("✖", key=f"del_{i}_{m_idx}"):
                                st.session_state['selected_moves'][i].pop(m_idx); st.rerun()
                    except: continue

    st.markdown("---")
    if st.button("Clear Full Team", type="primary"):
        st.session_state['team'] = []; st.session_state['selected_moves'] = {}; st.rerun()
