
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
end_year = st.sidebar.number_input("Slutår för prognos", value=2035)
years = list(range(start_year, end_year + 1))

# Exempeltabell med redigerbara värden
def get_default_data():
    return pd.DataFrame({
        "Land": ["Sweden", "Norway", "Netherlands"],
        "Startår": [2027, 2028, 2029],
        "Startyta (m²)": [45000, 45000, 45000],
        "Tillväxttakt (%/year)": [10, 10, 10],
        "Intäkt per m² (kr)": [125.79, 183.28, 173.89]
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
                "År": year,
                "Land": land,
                "Odlingsyta (m²)": round(current_area),
                "Intäkt per m² (kr)": revenue_per_m2,
                "Total årsintäkt (kr)": round(total_revenue)
            })
            current_area *= (1 + growth_rate)

# Visa resultat
results_df = pd.DataFrame(results)
if not results_df.empty:
    st.subheader(":bar_chart: Resultat")
    st.dataframe(results_df, use_container_width=True)

    total_by_year = results_df.groupby("År")["Total årsintäkt (kr)"].sum().reset_index()
    st.line_chart(total_by_year, x="År", y="Total årsintäkt (kr)")
