import streamlit as st
import pandas as pd
import io
import zipfile

# ---- Page config ----
st.set_page_config(page_title="SonicFlora Intäktsprognos", layout="wide")
st.title("🌱 SonicFlora Intäktsprognosverktyg")

st.markdown("""
Fyll i parametrar för varje marknad nedan. Verktyget räknar ut:
- Tillväxt av odlingsyta (baserat på startyta och individuella tillväxttak per år)
- Årlig intäkt per marknad
- Total intäkt under vald prognosperiod
""")

# ---- Sidebar ----
st.sidebar.header("Prognosinställningar")
start_year = st.sidebar.number_input("Startår för prognos", value=2027, step=1)
end_year = st.sidebar.number_input("Slutår för prognos", value=2034, step=1)
years = list(range(start_year, end_year + 1))
skordeokning = st.sidebar.slider("Ökning i skörd (%)", 0, 100, 20)
andel_sonicflora = st.sidebar.slider("SonicFloras andel av ökningen (%)", 0, 100, 20)
hardware_units_per_45000 = 724
hardware_unit_price = 500  # kr per enhet

# ---- Grunddata: skörd & pris ----
skord_data = pd.DataFrame({
    "Land": ["Sverige","Norge","Danmark","Finland","Island","Nederländerna","Storbritannien","Tyskland","Belgien","Österrike","Irland","Spanien","Italien"],
    "Skörd (kg/m²)": [42.2,31.9,39.2,44.9,29.6,50.5,35.4,27.4,47.4,29.2,37.3,8.8,5.8],
    "Pris (kr/kg)": [12.42,23.94,27.60,17.33,51.97,8.66,16.62,15.77,8.01,9.57,27.12,3.23,2.10]
})
skord_data["Grundintäkt (kr/m²)"] = skord_data["Skörd (kg/m²)"] * skord_data["Pris (kr/kg)"]
skord_data["Intäkt för Sonicflora per m² (kr)"] = (
    skord_data["Grundintäkt (kr/m²)"] * skordeokning/100 * andel_sonicflora/100
)

st.subheader("📐 Uträkning av intäkt per m²")
skord_data = st.data_editor(
    skord_data, use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        "Skörd (kg/m²)": st.column_config.NumberColumn(),
        "Pris (kr/kg)": st.column_config.NumberColumn(),
        "Grundintäkt (kr/m²)": st.column_config.NumberColumn(disabled=True),
        "Intäkt för Sonicflora per m² (kr)": st.column_config.NumberColumn(disabled=True)
    }
)

# ---- Marknadsdata ----
st.subheader("🌍 Marknadsdata")
default_market = pd.DataFrame({
    "Land": skord_data["Land"],
    "Startår": [2027,2028,2028,2029,2030,2030,2031,2031,2032,2033,2033,2034,2034],
    "Startyta (m²)": [45000]*len(skord_data),
    "Intäkt per m² (kr)": skord_data["Intäkt för Sonicflora per m² (kr)"].round(2)
})
input_df = st.data_editor(
    default_market, num_rows="dynamic", use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        "Startår": st.column_config.NumberColumn(),
        "Startyta (m²)": st.column_config.NumberColumn(),
        "Intäkt per m² (kr)": st.column_config.NumberColumn()
    }
)

# ---- Tillväxttak per år ----
year_cols = [str(y) for y in years]
wide_growth = pd.DataFrame([
    {"Land": land, **{yr: 0 for yr in year_cols}}
    for land in skord_data["Land"]
]).merge(input_df[["Land","Startår"]], on="Land", how="left")
for i, r in wide_growth.iterrows():
    for yr in year_cols:
        if int(yr) >= r["Startår"]:
            wide_growth.at[i, yr] = 10
st.subheader("📈 Tillväxttakt per marknad och år")
wide_growth = st.data_editor(
    wide_growth, use_container_width=True,
    column_config={
        "Land": st.column_config.TextColumn(disabled=True),
        **{yr: st.column_config.NumberColumn() for yr in year_cols},
        "Startår": st.column_config.NumberColumn(disabled=True)
    }
)
growth_long = wide_growth.melt(
    id_vars=["Land","Startår"], value_vars=year_cols,
    var_name="År", value_name="Tillväxttakt (%/år)"
)
growth_long["År"] = growth_long["År"].astype(int)
growth_long["Tillväxttakt (%/år)"].fillna(0, inplace=True)

# ---- Beräkningar per marknad ----
results = []
for _, row in input_df.iterrows():
    land = row["Land"]
    start = int(row["Startår"])
    area = float(row["Startyta (m²)"])
    rev_m2 = float(row["Intäkt per m² (kr)"])
    cur = area
    for year in years:
        if year >= start:
            gr = growth_long.query("Land == @land and År == @year")["Tillväxttakt (%/år)"].iloc[0]/100
            soft = cur * rev_m2
            hard = (cur/45000)*hardware_units_per_45000*hardware_unit_price
            results.append({
                "År":year,
                "Land":land,
                "Odlingsyta (m²)":round(cur),
                "Mjukvaruintäkt (kr)":round(soft),
                "Hårdvaruintäkt (kr)":round(hard),
                "Total intäkt (kr)":round(soft+hard)
            })
            cur *= 1+gr
results_df = pd.DataFrame(results)

# ---- Resultat per marknad ----
st.subheader("📊 Resultat per marknad")
disp = results_df.copy()
disp[["Mjukvaruintäkt (kr)","Hårdvaruintäkt (kr)","Total intäkt (kr)"]] = disp[["Mjukvaruintäkt (kr)","Hårdvaruintäkt (kr)","Total intäkt (kr)"]].applymap(lambda x: f"{x:,.0f}".replace(","," ")+" kr")
st.dataframe(disp, use_container_width=True)

# ---- Diagram ----
st.markdown("**Mjukvaruintäkt, Hårdvaruintäkt och Total intäkt (kr)**")
total_by_year = results_df.groupby("År")[[
    "Mjukvaruintäkt (kr)","Hårdvaruintäkt (kr)","Total intäkt (kr)"
]].sum().reset_index()
total_by_year["År"] = total_by_year["År"].astype(str)
st.line_chart(total_by_year.set_index("År"))

# ---- Sammanställning per år ----
total_summary = total_by_year.copy()
total_summary["Etablerad yta (m²)"] = results_df.groupby("År")["Odlingsyta (m²)"].sum().map(lambda x: f"{int(x):,}".replace(","," ")+" m²")
for col in ["Mjukvaruintäkt (kr)","Hårdvaruintäkt (kr)","Total intäkt (kr)"]:
    total_summary[col] = total_summary[col].map(lambda x: f"{int(x):,}".replace(","," ")+" kr")
# totalsumma
sums = {c: total_summary[c].str.replace("[^0-9]","",regex=True).astype(int).sum() for c in total_summary.columns if c!="År"}
    # Lägg till totalsumma-rad    row = {"År": "Totalt"}
    row.update({
        k: f"{v:,}".replace(",", " ") + (" m²" if "yta" in k else " kr")
        for k, v in sums.items()
    })
    # Lägg till formaterade värden i totalsummeringsraden
    row.update({
        k: f"{v:,}".replace(","," ") + (" m²" if "yta" in k else " kr")
        for k, v in sums.items()
    })
