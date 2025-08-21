import taipy.gui.builder as tgb
from utils.constants import PROJECT_ROOT

image_education_area = f"{PROJECT_ROOT}/assets/storytelling/insights_education_area.png"
image_admitted_students = f"{PROJECT_ROOT}/assets/storytelling/insights_admitted_students.png"


with tgb.Page() as storytelling:
    with tgb.part(class_name="page-container"):
        with tgb.part(class_name="dashboard-content card stack-large"):
            tgb.navbar()
            
            with tgb.part(class_name="card"):
                tgb.text("## Datainsikter", mode="md")
                tgb.text("Visualiseringar av data för att hitta strategiska möjligheter.", mode="md")
                
                # First insight
                with tgb.part(class_name="insight-section"):
                    tgb.text("### Strategiska nischområden", mode="md")
                    tgb.image("{image_education_area}", width="80%")
                    
                    # Comment section for the first insight
                    with tgb.part(class_name="insight-comment"):
                        tgb.text("#### Insikter:  \n"
                        "- Att komplettera kursutbudet med utbildningar inom mer nischade områden kan vara en framgångsfaktor.  \n "
                        "- Diagrammet, baserat på MYH:s statistik, visar tydligt att nischade utbildningsområden ofta har högre beviljandegrad.  \n",
                        mode="md")
                
                # Second insight
                with tgb.part(class_name="insight-section"):
                    tgb.text("### Könsfördelning inom utbildningsområden", mode="md")
                    tgb.image("{image_admitted_students}", width="80%")

                    # Comment section for the second insight
                    with tgb.part(class_name="insight-comment"):
                        tgb.text("#### Insikter:  \n"
                        "- I yrkeshögskolan finns en tydlig ambition att minska könssegregeringen i utbildningar.  \n"
                        "- MYH arbetar aktivt för breddad rekrytering genom att uppmuntra utbildningsanordnare att locka fler från det underrepresenterade könet.  \n"
                        "- Diagrammet visar områden där aktiva insatser skulle kunna förbättra könsbalansen.  \n",
                        mode="md")

                    with tgb.part(class_name="insight-resources"):
                        tgb.text("#### MYH erbjuder stöd:  \n"
                        "- Kommunikationshandledning med tips om inkluderande marknadsföring  \n"
                        "- Stödmaterial för jämställd utbildning och rekrytering  \n"
                        "- Möjlighet till rådgivning och anordnarstöd  \n"
                        "- Tillgång till profilerings- och informationsmaterial för både kurser och program  \n",
                        mode="md")