import taipy.gui.builder as tgb
from taipy.gui import Gui
import pandas as pd
from utils.constants import DATA_DIRECTORY
from frontend.charts import create_county_bar
from backend.data_processing import df, get_county_data




def filter_data(state):
    print(state)
    state.df_county, state.df_stats = get_county_data(state.df, state.selected_county)
    state.county_chart = create_county_bar(state.df_county, state.selected_county)


selected_county = "Stockholm"
df_county, df_stats = get_county_data(df, selected_county)
county_chart = create_county_bar(df_county, selected_county)


# --- National statistics ---
# Calculate approval stats for Sweden for the selected year
decisions = df["Beslut"].value_counts()
approved = decisions.get("Beviljad", 0)
total = decisions.sum()
approval_rate = round(approved / total * 100, 1) if total > 0 else 0

with tgb.Page() as page:
    with tgb.part(class_name="container card stack-large"):
        # Title
        tgb.text("# MYH dashboard kurser 2025", mode="md")
        tgb.text(
            """
            Denna dashboard visar statistik över ansökningar till YH-kurser för 2025. 
            Denna dashboard syftar till att vara ett verktyg för intressenter inom yrkeshögskola
            att läsa av KPIer för olika utbildningsanordnare. 
            För utbildningsanordnare skulle man exempelvis kunna se vad konkurrenterna ansökt 
            och ta inspiration från dem.
            """, 
            mode="md"
        )
        
        # Subtitle and explanation
        tgb.text("## Statistik för Sverige", mode="md")
        tgb.text(
            """
            Nedan syns KPIer och information för hela ansökningsomgången för hela Sverige. 
            Detta innebär samtliga kommuner, utbildningsområden och utbildningsanordnare
            i landet.
            """, 
            mode="md"
        )
        
        # Statistics cards
        with tgb.layout(columns="1 1 1"):
            with tgb.part(class_name="stat-card"):
                tgb.text("#### Ansökta kurser", mode="md")
                tgb.text(f"**{total}**", mode="md")
            
            with tgb.part(class_name="stat-card"):
                tgb.text("#### Beviljade", mode="md")
                tgb.text(f"**{approved}**", mode="md")
            
            with tgb.part(class_name="stat-card"):
                tgb.text("#### Beviljandegrad", mode="md")
                tgb.text(f"**{approval_rate}%**", mode="md")

        with tgb.layout(columns="2 1"):
            with tgb.part(class_name="card"):
                tgb.text(
                    "## Antalet ansökta och beviljade YH kurser per utbildningsområde i {selected_county}",
                    class_name="title-chart",
                    mode="md",
                )
                tgb.chart(figure="{county_chart}")

            with tgb.part(class_name="card left-margin-md"):
                tgb.text("## Filtrera data", mode="md")
                #tgb.text("Filtrera antalet kommuner", mode="md")

                tgb.text("Välj Län", mode="md")
                tgb.selector(
                    "{selected_county}",
                    lov=df["Län"].unique(),
                    dropdown=True,
                    on_change=filter_data
                )

                # TODO this part does not get updated after filtering
                with tgb.part(class_name="stats-container"):  # New container for stats
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Ansökta kurser", mode="md")
                        tgb.text(f"**{df_stats['Ansökta Kurser']}**", mode="md")

                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljade", mode="md")
                        tgb.text(f"**{df_stats['Beviljade']}**", mode="md")

                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljandegrad", mode="md")
                        tgb.text(f"**{df_stats['Beviljandegrad (%)']}%**", mode="md")

        with tgb.part(class_name="card"):
            tgb.text("Raw data")
            tgb.table("{df_county}")

# Run the app
if __name__ == "__main__":
    Gui(page, css_file="assets/main.css").run(dark_mode=False, use_reloader=False, port=8080)