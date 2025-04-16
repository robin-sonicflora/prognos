import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="SonicFlora Intäktsprognos", layout="wide")
st.title("🌱 SonicFlora Intäktsprognosverktyg")

st.markdown("""
Fyll i parametrar för varje marknad nedan. Verktyget räknar ut:
- Tillväxt av odlingsyta (baserat på startyta och tillväxttakt)
- Årlig intäkt per marknad
- Total intäkt under vald prognosperiod
""")

# Sidopanel: Inställningar
st.sidebar.header("Prognosinställningar")
start_year = st.sidebar.number_input("Startår för prognos", value=2027)
end_year = st.sidebar.number_input("Slutår för prognos", value=2034)
years = list(range(start_year, end_year + 1))

# Justerbara parametrar för intäkt per m²
skordeokning = st.sidebar.slider("Ökning i skörd (%)", 0, 100, 20)
andel_sonicflora = st.sidebar.slider("SonicFloras andel av ökningen (%)", 0, 100, 20)

# Parametrar för hårdvara
hardware_units_per_45000 = 724
hardware_unit_price = 500  # kr per enhet

# Uträkning: Intäkt per m² per land baserat på skörd, pris, ökning och andel
skord_data = pd.DataFrame({
    "Land": [
        "Sverige", "Norge", "Danmark", "Finland", "Island",
        "Nederländerna", "Storbritannien", "Tyskland", "Belgien",
        "Österrike", "Irland", "Spanien", "Italien"
    ],
    "Skörd (kg/m²)": [
        42.2, 31.9, 39.2, 44.9, 29.6,
        50.5, 35.4, 27.4, 47.4,
        29.2, 37.3, 8.8, 5.8
    ],
    "Pris (kr/kg)": [
        12.42, 23.94, 27.60, 17.33, 51.97,
        8.66, 16.62, 15.77, 8.01,
        9.57, 27.12, 3.23, 2.10
    ]
})

skord_data["Intäkt per m² (kr)"] = (
    skord_data["Skörd (kg/m²)"] *
    skord_data["Pris (kr/kg)"] *
    (1 + skordeokning / 100) *
    (andel_sonicflora / 100)
)

st.subheader("📐 Uträkning av intäkt per m²")
st.markdown("Formel: Skörd × Pris × (1 + ökning) × andel till SonicFlora")
st.dataframe(skord_data, use_container_width=True)

# Standarddata för redigering
def get_default_data():
    return pd.DataFrame({
        "Land": skord_data["Land"].tolist(),
        "Startår": [
            2027, 2028, 2028, 2029, 2029,
            2030, 2030, 2030, 2031,
            2032, 2032, 2033, 2034
        ],
        "Startyta (m²)": [45000] * 13,
        "Tillväxttakt (%/år)": [10] * 13,
        "Intäkt per m² (kr)": skord_data["Intäkt per m² (kr)"].round(2).tolist()
    })

st.subheader("🌍 Marknadsdata")
input_df = st.data_editor(
    get_default_data(),
    num_rows="dynamic",
    use_container_width=True
)

# Beräkningar
results = []
for _, row in input_df.iterrows():
    land = row["Land"]
    year_intro = int(row["Startår"])
    area = float(row["Startyta (m²)"])
    growth_rate = float(row["Tillväxttakt (%/år)"]) / 100
    revenue_per_m2 = float(row["Intäkt per m² (kr)"])

    current_area = area
    for year in years:
        if year >= year_intro:
            total_revenue = current_area * revenue_per_m2
            if year == year_intro:
                new_area = current_area
            else:
                new_area = current_area * (1 / (1 + growth_rate)) * growth_rate
            hardware_units = (new_area / 45000) * hardware_units_per_45000
            hardware_revenue = hardware_units * hardware_unit_price

            results.append({
                "År": int(year),
                "Land": land,
                "Odlingsyta (m²)": round(current_area),
                "Intäkt per m² (kr)": revenue_per_m2,
                "Mjukvaruintäkt (kr)": round(total_revenue),
                "Hårdvaruintäkt (kr)": round(hardware_revenue),
                "Total intäkt (kr)": round(total_revenue + hardware_revenue)
            })
            current_area *= (1 + growth_rate)

results_df = pd.DataFrame(results)
if not results_df.empty:
    st.subheader("📊 Resultat per marknad")

    # ... (tidigare kod för att formatera och plotta resultat) ...

    # Skapa sammanställning per år med anpassad HTML
    st.subheader("📘 Sammanställning per år")
    # Bygg CSS med rätt font-family
    css = """
    <style>
    table.custom-table, table.custom-table th, table.custom-table td, .copy-btn {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
      font-size: 14px;
    }
    .copy-btn {
      font-size: 12px;
      padding: 2px 6px;
      border: 1px solid #aaa;
      border-radius: 6px;
      background-color: #f9f9f9;
      margin-left: 8px;
      cursor: pointer;
    }
    .copy-btn:hover {
      background-color: #eee;
    }
    table.custom-table {
      width: 100%;
      border-collapse: collapse;
    }
    table.custom-table th, table.custom-table td {
      border: 1px solid #ddd;
      padding: 6px;
      text-align: left;
    }
    table.custom-table th {
      background-color: #f5f5f5;
    }
    </style>
    """

    # Bygg HTML-tabellen
    rows_html = ""
    for _, row in total_by_year.iterrows():
        rows_html += "<tr>"
        for col in total_by_year.columns:
            val = row[col]
            if isinstance(val, (int, float)) and "intäkt" in col:
                display = f"{val:,.0f}".replace(",", " ") + " kr"
                rows_html += f"<td>{display}<button class='copy-btn' onclick=\"navigator.clipboard.writeText('{int(val)}')\">Kopiera</button></td>"
            elif isinstance(val, (int, float)) and "yta" in col:
                display = f"{val:,.0f}".replace(",", " ") + " m²"
                rows_html += f"<td>{display}</td>"
            else:
                rows_html += f"<td>{val}</td>"
        rows_html += "</tr>"

    table_html = f"""
    {css}
    <table class='custom-table'>
      <thead>
        <tr>{''.join(f'<th>{c}</th>' for c in total_by_year.columns)}</tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    """

    components.html(table_html, height=600, scrolling=True)
