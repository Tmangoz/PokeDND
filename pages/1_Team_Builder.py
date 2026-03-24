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
    try:
        return requests.get(f"https://pokeapi.co/api/v2/type/{type_name}").json()
    except: return None

@st.cache_data(ttl=86400)
def get_move_details(move_url):
    try:
        return requests.get(move_url).json()
    except: return None

def calculate_full_analysis(pokemon_types):
    """Calculates all relations for the simplified columns."""
    # Defensive side (Incoming)
    weak, resist, immune_def = [], [], []
    def_mults = {}
    # Offensive side (Outgoing)
    super_eff, not_very, no_effect = set(), set(), set()
    
    for t_info in pokemon_types:
        data = get_type_data(t_info['type']['name'])
        if data:
            rel = data['damage_relations']
            # Defense
            for t in rel['double_damage_from']: def_mults[t['name']] = def_mults.get(t['name'], 1.0) * 2.0
            for t in rel['half_damage_from']: def_mults[t['name']] = def_mults.get(t['name'], 1.0) * 0.5
            for t in rel['no_damage_from']: def_mults[t['name']] = 0.0
            # Offense
            for t in rel['double_damage_to']: super_eff.add(t['name'])
            for t in rel['half_damage_to']: not_very.add(t['name'])
            for t in rel['no_damage_to']: no_effect.add(t['name'])

    for t, m in def_mults.items():
        if m > 1.0: weak.append(t)
        elif 0.0 < m < 1.0: resist.append(t)
        elif m == 0.0: immune_def.append(t)
            
    return {
        "weak": sorted(weak), "resist": sorted(resist), "immune_def": sorted(immune_def),
        "super": sorted(list(super_eff)), "not_very": sorted(list(not_very)), "no_effect": sorted(list(no_effect))
    }

def render_badges(types):
    if not types: return "None"
    badges = "".join([f'<span style="background-color:{TYPE_COLORS.get(t,"#777")}; color:white; padding:2px 6px; border-radius:10px; margin:2px; font-size:10px; display:inline-block; font-weight:bold;">{t.upper()}</span>' for t in types])
    return badges

def add_move_callback(pokemon_index):
    val = st.session_state[f"search_{pokemon_index}"]
    if val:
        current = st.session_state['selected_moves'].get(pokemon_index, [])
        if len(current) < 4 and val not in current:
            current.append(val)
            st.session_state['selected_moves'][pokemon_index] = current
        st.session_state[f"search_{pokemon_index}"] = ""

st.title("🏆 PokéDND Team Builder")

if 'team' not in st.session_state or not st.session_state['team']:
    st.info("Your team is empty! Go back to the Explorer to add some Pokémon.")
else:
    for i, p_data in enumerate(st.session_state['team']):
        if i not in st.session_state['selected_moves']: st.session_state['selected_moves'][i] = []
        
        with st.container(border=True):
            col_info, col_moves, col_chart = st.columns([1, 1.5, 2.5])
            
            with col_info:
                st.subheader(p_data['name'].capitalize())
                st.image(p_data['sprites']['front_default'], width=100)
                if st.button("🗑️ Remove Pokémon", key=f"rem_p_{i}"):
                    st.session_state['team'].pop(i); st.session_state['selected_moves'].pop(i, None); st.rerun()
                for s in p_data['stats']:
                    st.caption(f"**{s['stat']['name'].replace('special-','S.').upper()}**: {s['base_stat']}")

            with col_moves:
                st.write("**Move Selection**")
                all_m = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in p_data['moves']])))
                st.selectbox("Add Move", options=[""] + all_m, key=f"search_{i}", on_change=add_move_callback, args=(i,), label_visibility="collapsed")
                
                m_grid = st.columns(2)
                for idx, m_name in enumerate(st.session_state['selected_moves'][i]):
                    api_n = m_name.lower().replace(" ", "-")
                    m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == api_n)
                    m_details = get_move_details(m_url)
                    if m_details:
                        bg = TYPE_COLORS.get(m_details['type']['name'], "#777")
                        with m_grid[idx % 2]:
                            st.markdown(f'<div style="background-color:{bg}; color:white; padding:5px; border-radius:5px; text-align:center; font-size:10px; font-weight:bold;">{m_name.upper()}</div>', unsafe_allow_html=True)
                            if st.button("✖", key=f"del_{i}_{idx}", use_container_width=True):
                                st.session_state['selected_moves'][i].pop(idx); st.rerun()

            with col_chart:
                res = calculate_full_analysis(p_data['types'])
                
                # --- LAYOUT FOR TYPE ANALYSIS ---
                st.write("**Type Compatibility (Base Types)**")
                c1, c2 = st.columns(2)
                
                with c1:
                    st.caption("🛡️ **DEFENSE**")
                    st.write("**Weak To:**")
                    st.markdown(render_badges(res['weak']), unsafe_allow_html=True)
                    st.write("**Resists:**")
                    st.markdown(render_badges(res['resist']), unsafe_allow_html=True)
                    st.write("**Immune To:**")
                    st.markdown(render_badges(res['immune_def']), unsafe_allow_html=True)

                with c2:
                    st.caption("⚔️ **OFFENSE**")
                    st.write("**Super Effective Vs:**")
                    st.markdown(render_badges(res['super']), unsafe_allow_html=True)
                    st.write("**Not Very Effective Vs:**")
                    st.markdown(render_badges(res['not_very']), unsafe_allow_html=True)
                    st.write("**No Effect Vs:**")
                    st.markdown(render_badges(res['no_effect']), unsafe_allow_html=True)

    if st.button("Clear Full Team", type="primary"):
        st.session_state['team'] = []; st.session_state['selected_moves'] = {}; st.rerun()
