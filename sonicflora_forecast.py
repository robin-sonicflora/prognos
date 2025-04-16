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

# Justerbara parametrar för uträkning
skordeokning = st.sidebar.slider("Ökning i skörd (%)", min_value=0, max_value=100, value=20)
andel_sonicflora = st.sidebar.slider("SonicFloras andel (%)", min_value=0, max_value=100, value=20)

# Parametrar från sidopanelen för justering av intäkt per m²
skordeokning = st.sidebar.slider("Skördeökning (%)", 0, 100, 20)
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

skord_data["Intäkt per m² (kr)"] = skord_data["Skörd (kg/m²)"] * skord_data["Pris (kr/kg)"] * (1 + skordeokning / 100) * (andel_sonicflora / 100)
