from taipy.gui import Gui
from frontend.pages.home import home_page
#from frontend.pages.county import county_page
#from frontend.pages.providers import providers_page


pages = {"home": home_page} #, "county": county_page, "providers": providers_page}


if __name__ == "__main__":
    Gui(pages=pages).run(
        dark_mode=False, use_reloader=False, port=8080
    )
