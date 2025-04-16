import streamlit as st
import pandas as pd

st.set_page_config(page_title="SonicFlora Intäktsprognos", layout="wide")
st.title("🌱 SonicFlora Intäktsprognosverktyg")

st.markdown("""
Fyll i parametrar för varje marknad nedan. Verktyget räknar ut:
- Tillväxt av odlingsyta (baserat på startyta och tillväxttakt)
- Årlig intäkt per marknad
- Totalintäkt under vald prognosperiod
""")

# Sidopanel: Inställningar
st.sidebar.header("Prognosinställningar")
start_year = st.sidebar.number_input("Startår för prognos", value=2027)
end_year = st.sidebar.number_input("Slutår för prognos", value=2034)
years = list(range(start_year, end_year + 1))

# Exempeltabell med redigerbara värden
def get_default_data():
    return pd.DataFrame({
        "Land": [
            "Sweden", "Norway", "Denmark", "Finland", "Iceland",
            "Netherlands", "United Kingdom", "Germany", "Belgium",
            "Austria", "Ireland", "Spain", "Italy"
        ],
        "Startår": [
            2027, 2028, 2028, 2029, 2029,
            2030, 2030, 2030, 2031,
            2032, 2032, 2033, 2034
        ],
        "Startyta (m²)": [45000] * 13,
        "Tillväxttakt (%/year)": [10] * 13,
        "Intäkt per m² (kr)": [
            125.79, 183.28, 259.66, 186.75, 369.19,
            173.89, 141.23, 109.01, 160.28,
            67.11, 202.42, 6.81, 2.45
        ]
    })

st.subheader("🌐 Marknadsdata")
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
    growth_rate = float(row["Tillväxttakt (%/year)"]) / 100
    revenue_per_m2 = float(row["Intäkt per m² (kr)"])

    current_area = area
    for year in years:
        if year >= year_intro:
            total_revenue = current_area * revenue_per_m2
            results.append({
                "År": int(year),
                "Land": land,
                "Odlingsyta (m²)": round(current_area),
                "Intäkt per m² (kr)": revenue_per_m2,
                "Total årsintäkt (kr)": round(total_revenue),
                "Total årsintäkt (mSEK)": round(total_revenue / 1_000_000, 2)
            })
            current_area *= (1 + growth_rate)

# Visa resultat
results_df = pd.DataFrame(results)
if not results_df.empty:
    st.subheader(":bar_chart: Resultat")
    st.dataframe(results_df, use_container_width=True)

    total_by_year = results_df.groupby("År")["Total årsintäkt (mSEK)"].sum().reset_index()
    st.line_chart(total_by_year, x="År", y="Total årsintäkt (mSEK)")
