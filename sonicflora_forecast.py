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
skord_data["Grundintäkt (kr/m²)"] = skord_data["Skörd (kg/m²)"] * skord_data["Pris (kr/kg)"]
skord_data["Intäkt för Sonicflora per m² (kr)"] = (
    skord_data["Grundintäkt (kr/m²)"]
    * (skordeokning / 100)
    * (andel_sonicflora / 100)
)

st.subheader("📐 Uträkning av intäkt per m²")
st.markdown("Formel: Skörd × Pris × (1 + ökning) × andel till SonicFlora")
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

# Defaultdata för marknadsstart utan tillväxttakt
def get_default_market_data():
    return pd.DataFrame({
        "Land": skord_data["Land"].tolist(),
        "Startår": [
            2027, 2028, 2028, 2029, 2029,
            2030, 2030, 2030, 2031,
            2032, 2032, 2033, 2034
        ],
        "Startyta (m²)": [45000] * len(skord_data),
        "Intäkt för Sonicflora per m² (kr)": skord_data["Intäkt för Sonicflora per m² (kr)"].round(2).tolist()
    })

st.subheader("🌍 Marknadsdata")
input_df = st.data_editor(
    get_default_market_data(),
    num_rows="dynamic",
    use_container_width=True
)

# Skapa tillväxttakt per marknad och år
default_growth = []
for land in skord_data["Land"]:
    for year in years:
        default_growth.append({
            "Land": land,
            "År": year,
            "Tillväxttakt (%/år)": 10
        })
growth_df = pd.DataFrame(default_growth)

st.subheader("📈 Tillväxttakt per marknad och år")
growth_df = st.data_editor(
    growth_df,
    use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        "År": st.column_config.NumberColumn(disabled=True),
        "Tillväxttakt (%/år)": st.column_config.NumberColumn()
    }
)

# Beräkningar med årlig tillväxt per marknad
results = []
for _, row in input_df.iterrows():
    land = row["Land"]
    start_year = int(row["Startår"])
    area = float(row["Startyta (m²)"])
    revenue_per_m2 = float(row["Intäkt för Sonicflora per m² (kr)"])
    current_area = area

    for year in years:
        if year >= start_year:
            # Hämta tillväxttakt för aktuell marknad och år
            gr = (
                growth_df[
                    (growth_df["Land"] == land) &
                    (growth_df["År"] == year)
                ]["Tillväxttakt (%/år)"].iloc[0]
                / 100
            )
            total_revenue = current_area * revenue_per_m2
            hardware_units = (current_area / 45000) * hardware_units_per_45000
            hardware_revenue = hardware_units * hardware_unit_price
            results.append({
                "År": year,
                "Land": land,
                "Odlingsyta (m²)": round(current_area),
                "Tillväxttakt (%/år)": gr * 100,
                "Mjukvaruintäkt (kr)": round(total_revenue),
                "Hårdvaruintäkt (kr)": round(hardware_revenue),
                "Total intäkt (kr)": round(total_revenue + hardware_revenue)
            })
            # Uppdatera area för nästa år
            current_area *= (1 + gr)

results_df = pd.DataFrame(results)

if not results_df.empty:
    st.subheader("📊 Resultat per marknad")

    # Formatering och visualisering som tidigare
    results_df_formatted = results_df.copy()
    for col in ["Mjukvaruintäkt (kr)", "Hårdvaruintäkt (kr)", "Total intäkt (kr)"]:
        results_df_formatted[col] = (
            results_df_formatted[col]
            .apply(lambda x: f"{x:,.0f}".replace(",", " ") + " kr")
        )
    st.dataframe(results_df_formatted, use_container_width=True)

    total_by_year = results_df.groupby("År")[
        ["Mjukvaruintäkt (kr)", "Hårdvaruintäkt (kr)", "Total intäkt (kr)"]
    ].sum().reset_index()
    etablerad_yta_per_ar = results_df.groupby("År")["Odlingsyta (m²)"].sum().reset_index()
    etablerad_yta_per_ar = etablerad_yta_per_ar.rename(columns={"Odlingsyta (m²)": "Etablerad yta (m²)"})
    total_by_year = pd.merge(total_by_year, etablerad_yta_per_ar, on="År")

    sum_row = total_by_year.drop(columns=["År"]).sum(numeric_only=True).to_frame().T
    sum_row.insert(0, "År", "Totalt")
    total_by_year = pd.concat([total_by_year, sum_row], ignore_index=True)

    cols = total_by_year.columns.tolist()
    cols.insert(1, cols.pop(cols.index("Etablerad yta (m²)")))
    total_by_year = total_by_year[cols]

    st.markdown("**Mjukvaruintäkt, Hårdvaruintäkt och Total intäkt (kr)**")
    st.line_chart(
        data=total_by_year[total_by_year["År"] != "Totalt"]
        .set_index("År")[
            ["Mjukvaruintäkt (kr)", "Hårdvaruintäkt (kr)", "Total intäkt (kr)"]
        ]
    )

    st.subheader("📘 Sammanställning per år")
    # Anpassad HTML-tabell och export som tidigare

# Exportera data som ZIP för nedladdning
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("intakt_per_m2.csv", skord_data.to_csv(index=False))
    zf.writestr("marknadsdata.csv", input_df.to_csv(index=False))
    zf.writestr("tillvaxt_per_ar.csv", growth_df.to_csv(index=False))
    zf.writestr("detaljer_per_ar.csv", results_df.to_csv(index=False))
    zf.writestr("sum_per_ar.csv", total_by_year.to_csv(index=False))
zip_buffer.seek(0)

st.download_button(
    label="Ladda ner all data som ZIP",
    data=zip_buffer,
    file_name="sonicflora_prognos_data.zip",
    mime="application/zip"
)
