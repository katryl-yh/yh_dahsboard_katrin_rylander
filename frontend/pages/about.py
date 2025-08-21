import taipy.gui.builder as tgb
from utils.constants import PROJECT_ROOT

# Project images
dashboard_overview = f"{PROJECT_ROOT}/assets/about/dashboard_overview.png"
process_diagram = f"{PROJECT_ROOT}/assets/about/process.png"

with tgb.Page() as about_page:
    with tgb.part(class_name="page-container"):
        with tgb.part(class_name="dashboard-content card stack-large"):
            tgb.navbar()
            
            with tgb.part(class_name="card about-header"):
                tgb.text("## Om YH Dashboard", mode="md")
                tgb.text("""
                YH Dashboard är ett datadrivet verktyg utvecklat för att stödja utbildningsanordnare
                inom yrkeshögskolan med bättre beslutsunderlag. Dashboarden sammanställer och 
                visualiserar data från MYH och SCB på ett lättillgängligt sätt, vilket möjliggör
                effektivare strategiska beslut kring utbildningsutbud och rekrytering.
                """, mode="md")
            
            # Project assignment section
            with tgb.part(class_name="about-section"):
                tgb.text("### 1. Uppdraget", mode="md")
                
                with tgb.part(class_name="about-content"):
                    tgb.text("""
                    **Målsättning:**
                    - Att skapa ett verktyg som ger möjlighet att analysera trender och stödja strategiska beslut gällande YH-kurser
                    - Att utveckla en Minimum Viable Product där olika komponenter samverkar logiskt för att skapa sammanhang och värde
                    
                    **Framgångskriterier:**
                    - Tydlig struktur med logiskt organiserad data
                    - Flera funktionella sidor med användbar statistik och visualiseringar
                    - Konsekvent design genom hela applikationen
                    - Fokus på relevanta nyckeltal för YH-utbildningsdata
                    """, mode="md")
            
            # Project process section
            with tgb.part(class_name="about-section"):
                tgb.text("### 2. Projektprocess", mode="md")
                
                with tgb.part(class_name="about-content"):
                    tgb.text("""
                    **Arbetsmetodik:**
                    - Analys av YH-data från SCB och MYH för att förstå datakällorna och deras struktur
                    - Identifiering av nyckelinsikter och KPI:er som skapar värde för utbildningsanordnare
                    - Användning av LLM som kodpartner för att effektivisera utvecklingsprocessen
                    - Kontinuerlig utvärdering och anpassning baserat på nya insikter
                    
                    **Rollfördelning:**
                    - **Utvecklare:** Grundläggande projektstruktur, domänkunskap om YH-utbildningar, anpassningar och integration av förslag, originaldesign och koncept
                    - **AI-assistans:** Stöd med specifika funktioner och kodlösningar
                    """, mode="md")
                    
                    # Optional: Add process diagram if available
                    # tgb.image("{process_diagram}", width="80%")
            
            # Main features section
            with tgb.part(class_name="about-section"):
                tgb.text("### 3. Huvudfunktioner i dashboarden", mode="md")
                
                with tgb.part(class_name="about-content"):
                    tgb.text("""
                    **Översiktssida**
                    - Snabb överblick över nyckeltal för YH-utbildningar
                    - Design som gör data lättillgänglig och begriplig
                    
                    **Studentanalys**
                    - Fokus på könsfördelning inom YH-utbildningar
                    - Kritiskt underlag för utbildningsanordnare att förstå rekryteringsbehov och arbeta mot jämställdhetsmål
                    
                    **Länsfördelning**
                    - Geografisk visualisering av utbildningsmöjligheter i Sverige
                    - Underlag för att identifiera områden där utbildningsutbudet kan behöva utökas
                    
                    **Anordnaranalys**
                    - Filtreringsmöjligheter för specifika anordnare
                    - Verktyg för att jämföra prestationer och dra lärdomar från konkurrerande anordnare
                    """, mode="md")
                    
                    # Dashboard overview image
                    # tgb.image("{dashboard_overview}", width="80%")
            
            # Lessons learned section
            with tgb.part(class_name="about-section"):
                tgb.text("### 4. Huvudlärdomar", mode="md")
                
                with tgb.part(class_name="about-content strengths"):
                    tgb.text("""
                    **Tre främsta styrkorna:**
                    
                    1. **Välorganiserad kodstruktur**
                       - Tydlig och logisk uppdelning mellan frontend, backend och utilities
                       - Separata moduler för databearbetning, visualisering och användargränssnitt
                       
                    2. **Omfattande datavisualisering**
                       - Implementation av olika diagramtyper (stapeldiagram, geografiska kartor)
                       - Filtreringsmöjligheter och dynamisk uppdatering baserat på användarval
                       
                    3. **Väl genomtänkta KPI:er** 
                       - Relevanta nyckeltal som ger meningsfull insikt i data
                       - Tydlig presentation som underlättar förståelse
                    """, mode="md")
                
                with tgb.part(class_name="about-content improvements"):
                    tgb.text("""
                    **Tre förbättringsområden:** 
                    
                    1. **Layout och responsivitet**
                       - Vissa delar av gränssnittet kan förbättras för bättre skärmstorlekanpassning
                       - Mer konsekvent användning av rutnät och marginaler skulle förbättra det visuella flödet
                       
                    2. **Datalogik och felhantering**
                       - Utökad felhantering, särskilt för saknade data eller oväntade dataformat
                       - Fler validerings- och sanitetskontroller för indata
                       
                    3. **Kodstruktur och återanvändning**
                       - Viss duplicering mellan sidor kan brytas ut till gemensamma komponenter
                    """, mode="md")
            