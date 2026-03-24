import streamlit as st
import requests

# 1. Page Config
st.set_page_config(page_title="Team Builder", layout="wide", initial_sidebar_state="expanded")

# 2. Type Colors
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

def calculate_effectiveness(pokemon_types):
    """Calculates defensive weaknesses and resistances based on Pokemon types."""
    weak = []
    resist = []
    immune = []
    
    # We track multipliers: 2.0 = weak, 0.5 = resist, 0.0 = immune
    multipliers = {}

    for t_info in pokemon_types:
        t_name = t_info['type']['name']
        data = get_type_data(t_name)
        if data:
            damage_rel = data['damage_relations']
            # Double Damage From (Weaknesses)
            for t in damage_rel['double_damage_from']:
                multipliers[t['name']] = multipliers.get(t['name'], 1.0) * 2.0
            # Half Damage From (Resistances)
            for t in damage_rel['half_damage_from']:
                multipliers[t['name']] = multipliers.get(t['name'], 1.0) * 0.5
            # No Damage From (Immunities)
            for t in damage_rel['no_damage_from']:
                multipliers[t['name']] = 0.0

    for t_name, mult in multipliers.items():
        if mult > 1.0: weak.append(t_name)
        elif 0.0 < mult < 1.0: resist.append(t_name)
        elif mult == 0.0: immune.append(t_name)
            
    return weak, resist, immune

def render_type_badges(types, label, color):
    if not types: return ""
    badges = "".join([f'<span style="background-color:{TYPE_COLORS.get(t,"#777")}; color:white; padding:2px 6px; border-radius:4px; margin:2px; font-size:10px; display:inline-block;">{t.upper()}</span>' for t in types])
    return f'<div style="margin-bottom:5px;"><b style="color:{color}; font-size:11px;">{label}:</b> {badges}</div>'

# --- CALLBACK FOR AUTO-ADD ---
def add_move_callback(pokemon_index):
    selected_val = st.session_state[f"search_{pokemon_index}"]
    if selected_val:
        current_moves = st.session_state['selected_moves'].get(pokemon_index, [])
        if len(current_moves) < 4 and selected_val not in current_moves:
            current_moves.append(selected_val)
            st.session_state['selected_moves'][pokemon_index] = current_moves
        st.session_state[f"search_{pokemon_index}"] = ""

st.title("🏆 My Pokémon Team Builder")

if 'team' not in st.session_state or not st.session_state['team']:
    st.info("Your team is empty! Go back to the Explorer to add some Pokémon.")
else:
    for i, p_data in enumerate(st.session_state['team']):
        if i not in st.session_state['selected_moves']:
            st.session_state['selected_moves'][i] = []

        with st.container(border=True):
            # Split into 3 columns: Info/Stats | Moves | Type Effectiveness
            col_info, col_moves, col_types = st.columns([1.5, 2, 1.5])
            
            with col_info:
                st.subheader(p_data['name'].capitalize())
                c1, c2 = st.columns(2)
                with c1:
                    st.image(p_data['sprites']['front_default'], width=100)
                    if st.button("🗑️ Remove", key=f"rem_p_{i}"):
                        st.session_state['team'].pop(i)
                        st.session_state['selected_moves'].pop(i, None)
                        st.rerun()
                with c2:
                    for s in p_data['stats']:
                        name = s['stat']['name'].replace("special-", "S.").upper()
                        st.caption(f"**{name}**: {s['base_stat']}")

            with col_moves:
                st.write("**Moves**")
                all_m = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in p_data['moves']])))
                st.selectbox("Add Move", options=[""] + all_m, key=f"search_{i}", on_change=add_move_callback, args=(i,), label_visibility="collapsed")
                
                m_grid = st.columns(2)
                for idx, m_name in enumerate(st.session_state['selected_moves'][i]):
                    api_n = m_name.lower().replace(" ", "-")
                    m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == api_n)
                    m_info = get_move_details(m_url)
                    if m_info:
                        bg = TYPE_COLORS.get(m_info['type']['name'], "#777")
                        with m_grid[idx % 2]:
                            st.markdown(f'<div style="background-color:{bg}; color:white; padding:5px; border-radius:5px; text-align:center; font-size:11px; font-weight:bold;">{m_name.upper()}<br><small>PWR: {m_info.get("power") or "—"}</small></div>', unsafe_allow_html=True)
                            if st.button(f"✖", key=f"del_{i}_{idx}", use_container_width=True):
                                st.session_state['selected_moves'][i].pop(idx)
                                st.rerun()

            with col_types:
                st.write("**Defensive Chart**")
                weak, resist, immune = calculate_effectiveness(p_data['types'])
                
                chart_html = f'''
                    <div style="background-color:rgba(255,255,255,0.05); padding:10px; border-radius:10px; border: 1px solid rgba(255,255,255,0.1);">
                        {render_type_badges(weak, "WEAK TO", "#ff4b4b")}
                        {render_type_badges(resist, "RESISTS", "#2ecc71")}
                        {render_type_badges(immune, "IMMUNE TO", "#f1c40f")}
                    </div>
                '''
                st.markdown(chart_html, unsafe_allow_html=True)

    if st.button("Clear Full Team", type="primary"):
        st.session_state['team'] = []
        st.session_state['selected_moves'] = {}
        st.rerun()
