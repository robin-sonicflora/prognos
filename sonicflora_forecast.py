import streamlit as st
import pandas as pd

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

editable_skord_data = st.data_editor(skord_data, use_container_width=True)
editable_skord_data["Intäkt per m² (kr)"] = editable_skord_data["Skörd (kg/m²)"] * editable_skord_data["Pris (kr/kg)"] * (1 + skordeokning / 100) * (andel_sonicflora / 100)

skord_data["Intäkt per m² (kr)"] = skord_data["Skörd (kg/m²)"] * skord_data["Pris (kr/kg)"] * (1 + skordeokning / 100) * (andel_sonicflora / 100)

st.subheader("📐 Uträkning av intäkt per m²")
st.markdown("Formel: Skörd × Pris × (1 + ökning) × andel till SonicFlora")
editable_skord_data = st.data_editor(
    skord_data,
    use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        "Skörd (kg/m²)": st.column_config.NumberColumn(disabled=False),
        "Pris (kr/kg)": st.column_config.NumberColumn(disabled=False),
        "Grundintäkt (kr/m²)": st.column_config.NumberColumn(disabled=True),
        "Intäkt per m² (kr)": st.column_config.NumberColumn(disabled=True)
    }
)
editable_skord_data["Grundintäkt (kr/m²)"] = editable_skord_data["Skörd (kg/m²)"] * editable_skord_data["Pris (kr/kg)"]
editable_skord_data["Intäkt per m² (kr)"] = editable_skord_data["Grundintäkt (kr/m²)"] * (1 + skordeokning / 100) * (andel_sonicflora / 100)

# Standarddata för redigering

def get_default_data():
    return pd.DataFrame({
        "Land": editable_skord_data["Land"].tolist(),
        "Startår": [
            2027, 2028, 2028, 2029, 2029,
            2030, 2030, 2030, 2031,
            2032, 2032, 2033, 2034
        ],
        "Startyta (m²)": [45000] * 13,
        "Tillväxttakt (%/år)": [10] * 13,
        "Intäkt per m² (kr)": editable_skord_data["Intäkt per m² (kr)"].round(2).tolist()
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

    results_df_formatted = results_df.copy()
    for col in ["Mjukvaruintäkt (kr)", "Hårdvaruintäkt (kr)", "Total intäkt (kr)"]:
        results_df_formatted[col] = results_df_formatted[col].apply(lambda x: f"{x:,.0f}".replace(",", " ") + " kr")

    st.dataframe(results_df_formatted, use_container_width=True)

    total_by_year = results_df.groupby("År")[["Mjukvaruintäkt (kr)", "Hårdvaruintäkt (kr)", "Total intäkt (kr)"]].sum().reset_index()
    total_by_year = total_by_year.sort_values("År")
    total_by_year["År"] = pd.to_numeric(total_by_year["År"], errors="coerce")

    etablerad_yta_per_ar = results_df.groupby("År")["Odlingsyta (m²)"].sum().reset_index()
    etablerad_yta_per_ar = etablerad_yta_per_ar.rename(columns={"Odlingsyta (m²)": "Etablerad yta (m²)"})
    total_by_year = pd.merge(total_by_year, etablerad_yta_per_ar, on="År", how="left")

    sum_row = total_by_year.drop(columns=["År"]).sum(numeric_only=True).to_frame().T
    sum_row.insert(0, "År", "Totalt")
    total_by_year = pd.concat([total_by_year, sum_row], ignore_index=True)

    cols = total_by_year.columns.tolist()
    if "Etablerad yta (m²)" in cols:
        cols.insert(1, cols.pop(cols.index("Etablerad yta (m²)")))
    total_by_year = total_by_year[cols]

    # Visa diagram
    total_by_year_plot = total_by_year[total_by_year["År"] != "Totalt"].copy()
    total_by_year_plot["År"] = total_by_year_plot["År"].astype(str)
    st.markdown("**Mjukvaruintäkt, Hårdvaruintäkt och Total intäkt (kr)**")
    st.line_chart(data=total_by_year_plot.set_index("År")[["Mjukvaruintäkt (kr)", "Hårdvaruintäkt (kr)", "Total intäkt (kr)"]])

    # Anpassad HTML-tabell med kopieringsknappar
    st.subheader("📘 Sammanställning per år")
    html_table = """
    <style>
body, table, td, th, .copy-btn, * {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}
html, body, table.custom-table, .copy-btn {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
    button.copy-btn {
      background: none;
      border: none;
      cursor: pointer;
      font-size: 14px;
      padding-left: 4px;
    }
    table.custom-table {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      width: 100%;
      border-collapse: collapse;
    }
    table.custom-table th, table.custom-table td {
      border: 1px solid #ddd;
      padding: 6px;
      text-align: left;
      font-size: 14px;
    }
    table.custom-table th {
      background-color: #f5f5f5;
    }
    </style>
    <script>
    function copyToClipboard(value) {
      navigator.clipboard.writeText(value);
    }
    </script>
    <table class='custom-table'>
    <thead><tr>"""
    for col in total_by_year.columns:
        html_table += f"<th>{col}</th>"
    html_table += "</tr></thead><tbody>"

    for _, row in total_by_year.iterrows():
        html_table += "<tr>"
        for col in total_by_year.columns:
            val = row[col]
            if isinstance(val, (int, float)) and "intäkt" in col:
                display_val = f"{val:,.0f}".replace(",", " ") + " kr"
                html_table += f"<td>{display_val} <button class='copy-btn' onclick=\"copyToClipboard('{int(val)}')\">📋</button></td>"
            elif isinstance(val, (int, float)) and "yta" in col:
                display_val = f"{val:,.0f}".replace(",", " ") + " m²"
                html_table += f"<td>{display_val}</td>"
            else:
                html_table += f"<td>{val}</td>"
        html_table += "</tr>"
    html_table += "</tbody></table>"
    import streamlit.components.v1 as components

copy_table_html = """
<style>
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
  font-size: 14px;
}
table.custom-table th {
  background-color: #f5f5f5;
}
</style>
<script>
function copyText(value) {
  navigator.clipboard.writeText(value);
  
}
</script>
<table class='custom-table'>
<thead><tr>"""
for col in total_by_year.columns:
    copy_table_html += f"<th>{col}</th>"
copy_table_html += "</tr></thead><tbody>"

for _, row in total_by_year.iterrows():
    copy_table_html += "<tr>"
    for col in total_by_year.columns:
        val = row[col]
        if isinstance(val, (int, float)) and "intäkt" in col:
            display_val = f"{val:,.0f}".replace(",", " ") + " kr"
            copy_table_html += f"<td>{display_val}<button class='copy-btn' onclick=\"copyText('{int(val)}')\">Kopiera</button></td>"
        elif isinstance(val, (int, float)) and "yta" in col:
            display_val = f"{val:,.0f}".replace(",", " ") + " m²"
            copy_table_html += f"<td>{display_val}</td>"
        else:
            copy_table_html += f"<td>{val}</td>"
    copy_table_html += "</tr>"
copy_table_html += "</tbody></table>"

components.html(copy_table_html, height=600, scrolling=True)
