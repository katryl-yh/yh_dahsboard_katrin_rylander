import taipy.gui.builder as tgb

image_education_area = "../assets/storytelling/insights_education_area.png"
image_admitted_students = "../assets/storytelling/insights_admitted_students.png"


with tgb.Page() as storytelling:
    with tgb.part(class_name="page-container"):
        tgb.navbar()
        with tgb.part(class_name="title-card"):
            tgb.text("# Datainsikter", mode="md")
    
        with tgb.part(style="margin-bottom: 40px;"):
                tgb.image("{image_education_area}", width="80%")
        with tgb.part(style="margin-bottom: 40px;"):
                tgb.image("{image_admitted_students}", width="80%")
            
 