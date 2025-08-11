import taipy.gui.builder as tgb
from taipy.gui import Gui
import pandas as pd
from utils.constants import DATA_DIRECTORY
from frontend.charts import create_county_bar
from backend.data_processing import filter_per_county, df




def filter_data(state):
    print(state)
    state.df_county = filter_per_county(state.df, state.selected_county)
    state.county_chart = create_county_bar(state.df_county, state.selected_county)


selected_county = "Stockholm"
df_county = filter_per_county(df, county="Stockholm")
county_chart = create_county_bar(df_county, selected_county)

with tgb.Page() as page:
    with tgb.part(class_name="container card stack-large"):
        tgb.text("# MYH dashboard 2025", mode="md")

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

                #tgb.button("FILTRERA DATA", class_name="button-color", )

        with tgb.part(class_name="card"):
            tgb.text("Raw data")
            tgb.table("{df_county}")

# Run the app
if __name__ == "__main__":
    Gui(page, css_file="assets/main.css").run(dark_mode=False, use_reloader=False, port=8080)