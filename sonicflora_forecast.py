import streamlit as st
import pandas as pd
import io
import zipfile

# Sidan
st.set_page_config(page_title="SonicFlora Intäktsprognos", layout="wide")
st.title("🌱 SonicFlora Intäktsprognosverktyg")

st.markdown("""
Fyll i parametrar för varje marknad nedan. Verktyget räknar ut:
- Tillväxt av odlingsyta (baserat på startyta och individuella tillväxttak per år)
- Årlig intäkt per marknad
- Total intäkt under vald prognosperiod
""")

# Sidopanel: prognosinställningar
st.sidebar.header("Prognosinställningar")
start_year = st.sidebar.number_input("Startår för prognos", value=2027, step=1)
end_year = st.sidebar.number_input("Slutår för prognos", value=2034, step=1)
years = list(range(start_year, end_year + 1))

# Globala parametrar
skordeokning = st.sidebar.slider("Ökning i skörd (%)", 0, 100, 20)
andel_sonicflora = st.sidebar.slider("SonicFloras andel av ökningen (%)", 0, 100, 20)
hardware_units_per_45000 = 724
hardware_unit_price = 500  # kr per enhet

# Grunddata: skörd och pris per land
skord_data = pd.DataFrame({
    "Land": [
        "Sverige", "Norge", "Danmark", "Finland", "Island",
        "Nederländerna", "Storbritannien", "Tyskland", "Belgien",
        "Österrike", "Irland", "Spanien", "Italien"
    ],
    "Skörd (kg/m²)": [42.2, 31.9, 39.2, 44.9, 29.6, 50.5, 35.4, 27.4, 47.4, 29.2, 37.3, 8.8, 5.8],
    "Pris (kr/kg)":   [12.42, 23.94, 27.60, 17.33, 51.97, 8.66, 16.62, 15.77, 8.01, 9.57, 27.12, 3.23, 2.10]
})
skord_data["Grundintäkt (kr/m²)"] = skord_data["Skörd (kg/m²)"] * skord_data["Pris (kr/kg)"]
skord_data["Intäkt för Sonicflora per m² (kr)"] = (
    skord_data["Grundintäkt (kr/m²)"]
    * skordeokning / 100
    * andel_sonicflora / 100
)

# Redigera skörd/pris
st.subheader("📐 Uträkning av intäkt per m²")
st.markdown("Formel: Skörd × Pris × ökning × andel till SonicFlora")
skord_data = st.data_editor(
    skord_data,
    use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        "Skörd (kg/m²)": st.column_config.NumberColumn(),
        "Pris (kr/kg)": st.column_config.NumberColumn(),
        "Grundintäkt (kr/m²)": st.column_config.NumberColumn(disabled=True),
        "Intäkt för Sonicflora per m² (kr)": st.column_config.NumberColumn(disabled=True),
    }
)

# Marknadsdata: startår, startyta, intäkt per m²
st.subheader("🌍 Marknadsdata")
default_market = pd.DataFrame({
    "Land": skord_data["Land"].tolist(),
    "Startår": [2027,2028,2028,2029,2030,2030,2031,2031,2032,2033,2033,2034,2034],
    "Startyta (m²)": [45000] * len(skord_data),
    "Intäkt för Sonicflora per m² (kr)": skord_data["Intäkt för Sonicflora per m² (kr)"].round(2)
})
input_df = st.data_editor(
    default_market,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        "Startår": st.column_config.NumberColumn(),
        "Startyta (m²)": st.column_config.NumberColumn(),
        "Intäkt för Sonicflora per m² (kr)": st.column_config.NumberColumn()
    }
)

# Tillväxttabell (bred)
year_cols = [str(y) for y in years]
wide_growth = pd.DataFrame([
    {"Land": land, **{yr: None for yr in year_cols}}
    for land in skord_data["Land"]
])
wide_growth = wide_growth.merge(
    input_df[["Land", "Startår"]], on="Land", how="left"
)
for idx, row in wide_growth.iterrows():
    for yr in year_cols:
        if int(yr) >= row["Startår"]:
            wide_growth.at[idx, yr] = 10

st.subheader("📈 Tillväxttakt per marknad och år")
wide_growth = st.data_editor(
    wide_growth,
    use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        **{yr: st.column_config.NumberColumn() for yr in year_cols},
        "Startår": st.column_config.NumberColumn(disabled=True)
    }
)

# Konvertera bred → lång för beräkningar
growth_long = wide_growth.melt(
    id_vars=["Land", "Startår"],
    value_vars=year_cols,
    var_name="År", value_name="Tillväxttakt (%/år)"
)
growth_long["År"] = growth_long["År"].astype(int)
growth_long["Tillväxttakt (%/år)"].fillna(0, inplace=True)

# Beräkningar per marknad och år
results = []
for _, row in input_df.iterrows():
    land = row["Land"]
    start = int(row["Startår"])
    area = float(row["Startyta (m²)"])
    rev_m2 = float(row["Intäkt för Sonicflora per m² (kr)"])
    current_area = area
    for year in years:
        if year >= start:
            gr = growth_long.loc[
                (growth_long["Land"]==land) &
                (growth_long["År"]==year),
                "Tillväxttakt (%/år)"
            ].iloc[0] / 100
            soft_rev = current_area * rev_m2
            hard_units = (current_area / 45000) * hardware_units_per_45000
            hard_rev = hard_units * hardware_unit_price
            results.append({
                "År": year,
                "Land": land,
                "Odlingsyta (m²)": round(current_area),
                "Mjukvaruintäkt (kr)": round(soft_rev),
                "Hårdvaruintäkt (kr)": round(hard_rev),
                "Total intäkt (kr)": round(soft_rev + hard_rev)
            })
            current_area *= (1 + gr)

results_df = pd.DataFrame(results)

# Visa resultat
if not results_df.empty:
    st.subheader("📊 Resultat per marknad")
    display_cols = ["År","Land","Odlingsyta (m²)","Mjukvaruintäkt (kr)","Hårdvaruintäkt (kr)","Total intäkt (kr)"]
    disp = results_df[display_cols].copy()
    for c in ["Mjukvaruintäkt (kr)","Hårdvaruintäkt (kr)","Total intäkt (kr)"]:
        disp[c] = disp[c].apply(lambda x: f"{x:,.0f}".replace(","," ") + " kr")
    st.dataframe(disp, use_container_width=True)

    # Diagram
    st.markdown("**Mjukvaruintäkt, Hårdvaruintäkt och Total intäkt (kr)**")
    total_by_year = results_df.groupby("År")["Mjukvaruintäkt (kr)", "Hårdvaruintäkt (kr)", "Total intäkt (kr)"].sum().reset_index()
    total_by_year["År"] = total_by_year["År"].astype(str)
    st.line_chart(data=total_by_year.set_index("År"))

    # Sammanställning per år med HTML
    st.subheader("📘 Sammanställning per år")
    html_table = """
    <style>
      body, table, td, th { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
      table.custom-table { width:100%; border-collapse:collapse; }
      table.custom-table th, table.custom-table td { border:1px solid #ddd; padding:6px; text-align:left; }
      table.custom-table th { background-color:#f5f5f5; }
      button.copy-btn { background:none; border:none; cursor:pointer; font-size:12px; margin-left:8px; }
    </style>
    <script>
      function copyText(val) { navigator.clipboard.writeText(val); }
    </script>
    <table class='custom-table'><thead><tr>"""
    for h in total_by_year.columns:
        html_table += f"<th>{h}</th>"
    html_table += "</tr></thead><tbody>"
    for _, r in total_by_year.iterrows():
        html_table += "<tr>"
        for c in total_by_year.columns:
            v = r[c]
            if c == "År":
                html_table += f"<td>{v}</td>"
            else:
                if isinstance(v, (int, float)):
                    unit = 'm²' if 'yta' in c else 'kr'
                    disp = f"{v:,.0f}".replace(","," ") + (f" {unit}" if unit=='m²' else " kr")
                    if unit=='kr':
                        html_table += f"<td>{disp}<button class='copy-btn' onclick=\"copyText('{int(v)}')\">📋</button></td>"
                    else:
                        html_table += f"<td>{disp}</td>"
                else:
                    html_table += f"<td>{v}</td>"
        html_table += "</tr>"
    html_table += "</tbody></table>"
    import streamlit.components.v1 as components
    components.html(html_table, height=600, scrolling=True)

# Manuellt testscenario
st.subheader("🧪 Testa ett scenario manuellt")
col1, _ = st.columns([1,2])
with col1:
    test_area = st.number_input("Odlingsyta (m²)", value=45000)
    test_skord = st.number_input("Skörd (kg/m²)", value=42.2)
    test_pris = st.number_input("Pris (kr/kg)", value=12.42)
    test_okning = st.slider("Skördeökning (%) (test)", 0, 100, 20)
    test_andel = st.slider("SonicFloras andel av ökningen (%) (test)", 0, 100, 20)

    grundintakt = test_skord * test_pris
    okning_per_m2 = grundintakt * test_okning / 100
    sf_per_m2 = okning_per_m2 * test_andel / 100
    total_int = sf_per_m2 * test_area
    total_str = f"{total_int:,.0f}".replace(","," ")

    st.markdown(f"""
    **Grundintäkt per m²:** {grundintakt:.2f} kr  
    **Ökning per m²:** {okning_per_m2:.2f} kr  
    **Sonicfloras andel per m²:** {sf_per_m2:.2f} kr  
    **Total intäkt:** {total_str} kr
    """
)

# Exportera till ZIP
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("intakt_per_m2.csv", skord_data.to_csv(index=False))
    zf.writestr("marknadsdata.csv", input_df.to_csv(index=False))
    zf.writestr("tillvaxt_per_ar.csv", growth_long.to_csv(index=False))
    zf.writestr("detaljer_per_ar.csv", results_df.to_csv(index=False))
    zf.writestr("sum_per_ar.csv", total_by_year.to_csv(index=False))
zip_buffer.seek(0)

st.download_button(
    label="Ladda ner all data som ZIP",
    data=zip_buffer,
    file_name="sonicflora_prognos_data.zip",
    mime="application/zip"
)
