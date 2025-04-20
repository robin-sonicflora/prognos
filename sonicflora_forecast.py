hardware_units_per_45000 = 724
hardware_unit_price = 500  # kr per enhet

# Uträkning: Intäkt per m² per land baserat på skörd, pris, ökning och andel
# Grunddata för skörd och pris per land
skord_data = pd.DataFrame({
"Land": [
"Sverige", "Norge", "Danmark", "Finland", "Island",
@@ -53,7 +53,7 @@
)

st.subheader("📐 Uträkning av intäkt per m²")
st.markdown("Formel: Skörd × Pris × (1 + ökning) × andel till SonicFlora")
st.markdown("Formel: Skörd × Pris × ökning × andel till SonicFlora")
skord_data = st.data_editor(
skord_data,
use_container_width=True,
@@ -66,130 +66,112 @@
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
    get_default_market_data(),
    default_market,
num_rows="dynamic",
    use_container_width=True
    use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        "Startår": st.column_config.NumberColumn(),
        "Startyta (m²)": st.column_config.NumberColumn(),
        "Intäkt för Sonicflora per m² (kr)": st.column_config.NumberColumn()
    }
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
growth_df = st.data_editor(
    growth_df,
wide_growth = st.data_editor(
    wide_growth,
use_container_width=True,
column_config={
"Land": st.column_config.TextColumn(disabled=True),
        "År": st.column_config.NumberColumn(disabled=True),
        "Tillväxttakt (%/år)": st.column_config.NumberColumn()
        **{yr: st.column_config.NumberColumn() for yr in year_cols},
        "Startår": st.column_config.NumberColumn(disabled=True)
}
)

# Beräkningar med årlig tillväxt per marknad
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
    start_year = int(row["Startår"])
    start = int(row["Startår"])
area = float(row["Startyta (m²)"])
    revenue_per_m2 = float(row["Intäkt för Sonicflora per m² (kr)"])
    rev_m2 = float(row["Intäkt för Sonicflora per m² (kr)"])
current_area = area

for year in years:
        if year >= start_year:
            # Hämta tillväxttakt för aktuell marknad och år
        if year >= start:
gr = (
                growth_df[
                    (growth_df["Land"] == land) &
                    (growth_df["År"] == year)
                ]["Tillväxttakt (%/år)"].iloc[0]
                / 100
                growth_long.loc[
                    (growth_long["Land"] == land) &
                    (growth_long["År"] == year),
                    "Tillväxttakt (%/år)"
                ].iloc[0] / 100
)
            total_revenue = current_area * revenue_per_m2
            hardware_units = (current_area / 45000) * hardware_units_per_45000
            hardware_revenue = hardware_units * hardware_unit_price
            # Räkna intäkter
            soft_rev = current_area * rev_m2
            hard_units = (current_area / 45000) * hardware_units_per_45000
            hard_rev = hard_units * hardware_unit_price
results.append({
"År": year,
"Land": land,
"Odlingsyta (m²)": round(current_area),
"Tillväxttakt (%/år)": gr * 100,
                "Mjukvaruintäkt (kr)": round(total_revenue),
                "Hårdvaruintäkt (kr)": round(hardware_revenue),
                "Total intäkt (kr)": round(total_revenue + hardware_revenue)
                "Mjukvaruintäkt (kr)": round(soft_rev),
                "Hårdvaruintäkt (kr)": round(hard_rev),
                "Total intäkt (kr)": round(soft_rev + hard_rev)
})
            # Uppdatera area för nästa år
current_area *= (1 + gr)

results_df = pd.DataFrame(results)

if not results_df.empty:
st.subheader("📊 Resultat per marknad")
    # Formatera och visa data...
    # (samma som tidigare, st.dataframe + aggregeringar + diagram)

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
# Exportera data som ZIP
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
zf.writestr("intakt_per_m2.csv", skord_data.to_csv(index=False))
zf.writestr("marknadsdata.csv", input_df.to_csv(index=False))
    zf.writestr("tillvaxt_per_ar.csv", growth_df.to_csv(index=False))
    zf.writestr("tillvaxt_per_ar.csv", growth_long.to_csv(index=False))
zf.writestr("detaljer_per_ar.csv", results_df.to_csv(index=False))
    zf.writestr("sum_per_ar.csv", total_by_year.to_csv(index=False))
zip_buffer.seek(0)

st.download_button(
