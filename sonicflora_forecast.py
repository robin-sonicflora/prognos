import streamlit as st
import pandas as pd
import io
import zipfile

st.set_page_config(page_title="SonicFlora Intäktsprognos", layout="wide")
st.title("🌱 SonicFlora Intäktsprognosverktyg")

st.markdown("""
Fyll i parametrar för varje marknad nedan. Verktyget räknar ut:
- Tillväxt av odlingsyta (baserat på startyta och individuella tillväxttak per år)
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

# Grunddata för skörd och pris per land
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
skord_data["Grundintäkt (kr/m²)"] = skord_data["Skörd (kg/m²)"] * skord_data["Pris (kr/kg)"]
skord_data["Intäkt för Sonicflora per m² (kr)"] = (
    skord_data["Grundintäkt (kr/m²)"]
    * (skordeokning / 100)
    * (andel_sonicflora / 100)
)

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

# Data för marknadsstart
st.subheader("🌍 Marknadsdata")
default_market = pd.DataFrame({
    "Land": skord_data["Land"].tolist(),
    "Startår": [
        2027, 2028, 2028, 2029, 2029,
        2030, 2030, 2030, 2031,
        2032, 2032, 2033, 2034
    ],
    "Startyta (m²)": [45000] * len(skord_data),
    "Intäkt för Sonicflora per m² (kr)": skord_data["Intäkt för Sonicflora per m² (kr)"].round(2).tolist()
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

# Breddformat för tillväxttakt per land och år
year_cols = [str(y) for y in years]
wide_growth = pd.DataFrame([
    {"Land": land, **{yr: 10 for yr in year_cols}}
    for land in skord_data["Land"]
])
# Lägg till startår för att maskera år före marknadsstart
wide_growth = wide_growth.merge(
    input_df[["Land", "Startår"]], on="Land", how="left"
)
# Maskera tillväxttakt före startår
for yr in year_cols:
    wide_growth.loc[wide_growth["Startår"] > int(yr), yr] = None

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

# Konvertera bred tillväxttabell till lång
growth_long = (
    wide_growth
    .melt(
        id_vars=["Land", "Startår"],
        value_vars=year_cols,
        var_name="År", value_name="Tillväxttakt (%/år)"
    )
)
growth_long["År"] = growth_long["År"].astype(int)
growth_long["Tillväxttakt (%/år)"].fillna(0, inplace=True)

# Beräkningar med individuell tillväxt
results = []
for _, row in input_df.iterrows():
    land = row["Land"]
    start = int(row["Startår"])
    area = float(row["Startyta (m²)"])
    rev_m2 = float(row["Intäkt för Sonicflora per m² (kr)"])
    current_area = area
    for year in years:
        if year >= start:
            gr = (
                growth_long.loc[
                    (growth_long["Land"] == land) &
                    (growth_long["År"] == year),
                    "Tillväxttakt (%/år)"
                ].iloc[0] / 100
            )
            # Räkna intäkter
            soft_rev = current_area * rev_m2
            hard_units = (current_area / 45000) * hardware_units_per_45000
            hard_rev = hard_units * hardware_unit_price
            results.append({
                "År": year,
                "Land": land,
                "Odlingsyta (m²)": round(current_area),
                "Tillväxttakt (%/år)": gr * 100,
                "Mjukvaruintäkt (kr)": round(soft_rev),
                "Hårdvaruintäkt (kr)": round(hard_rev),
                "Total intäkt (kr)": round(soft_rev + hard_rev)
            })
            current_area *= (1 + gr)

results_df = pd.DataFrame(results)
if not results_df.empty:
    st.subheader("📊 Resultat per marknad")
    # Formatera och visa data...
    # (samma som tidigare, st.dataframe + aggregeringar + diagram)

# Exportera data som ZIP
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("intakt_per_m2.csv", skord_data.to_csv(index=False))
    zf.writestr("marknadsdata.csv", input_df.to_csv(index=False))
    zf.writestr("tillvaxt_per_ar.csv", growth_long.to_csv(index=False))
    zf.writestr("detaljer_per_ar.csv", results_df.to_csv(index=False))
zip_buffer.seek(0)

st.download_button(
    label="Ladda ner all data som ZIP",
    data=zip_buffer,
    file_name="sonicflora_prognos_data.zip",
    mime="application/zip"
)
