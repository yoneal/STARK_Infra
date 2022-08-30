from random import randint

def suggest_graphic(entity_name):
    #FIXME: When STARK data modeling syntax is finalized, it should include a way for
    #   devs to include a type hint for the entity (e.g., "people") to guide the parser
    #   towards choosing a more appropriate default graphic.
    #   Should also include a way to directly specify the desired image name (e.g. "user.png")

    extension = "svg"

    default_icon_map = {
        "award": [f"award.{extension}"],
        "archive": [f"archive.{extension}"],
        "book": [f"book.{extension}"],
        "commerce": [f"bag.{extension}", f"bag-heart.{extension}", f"cart.{extension}", f"cart-check.{extension}"],
        "config": [f"gear.{extension}", f"sliders.{extension}", f"sliders2.{extension}", f"sliders2-vertical.{extension}"],
        "data": [f"pie-chart.{extension}"],
        "document": [f"file-earmark-text.{extension}", f"folder.{extension}", f"folder-fill.{extension}", f"folder2.{extension}"],
        "event": [f"calendar.{extension}",f"calendar-day.{extension}",f"calendar-date.{extension}",f"calendar-event.{extension}",f"calendar2.{extension}",f"calendar2-day.{extension}",f"calendar2-date.{extension}",f"calendar2-event.{extension}" ],
        "item": [f"box.{extension}",f"box-seam.{extension}",f"box2.{extension}"],
        "location": [f"map.{extension}", f"geo-alt-fill.{extension}", f"geo-alt.{extension}"],
        "logistics": [f"truck.{extension}"],
        "person": [f"person.{extension}", f"people.{extension}"],
        "sales": [f"currency-dollar.{extension}", f"credit-card.{extension}", f"credit-card-2-front.{extension}"],
        "tasks": [f"clipboard.{extension}"],
        "travel": [f"briefcase.{extension}"],
        "type": [f"tag.{extension}", f"tags.{extension}"],
    }

    abstract_icons = [ f"square.{extension}", f"triangle.{extension}", f"circle.{extension}", f"hexagon.{extension}", f"star.{extension}"]

    #The order of these types matter. Types that come first take precedence.
    entity_type_map = {
        "type": ["type", "category", "categories", "tag", "price"],
        "tasks": ["task", "to do", "todo", "to-do", "list"],
        "data": ["data", "report"],
        "award": ["award", "prize"],
        "archive": ["archive", "storage", "warehouse"],
        "book": ["book"],
        "commerce": ["order", "shop"],
        "config": ["config", "configuration", "settings", "option"],
        "document": ["document", "file", "form",],
        "event": ["event", "meeting", "date", "call", "conference"],
        "item": ["item", "package", "inventory"],
        "location": ["address", "place", "location", "country", "countries", "city", "cities", "branch", "office"],
        "logistics": ["delivery", "deliveries", "vehicle", "fleet", "shipment"],
        "person": ["customer", "agent", "employee", "student", "teacher", "person", "people", "human"],
        "sales": ["sale", "sale", "purchase", "money", "finance"],
        "travel": ["travel"],
    }

    suggested_type = ''
    entity_name = entity_name.lower()
    for type in entity_type_map:
        #First, try a naive match
        if entity_name in entity_type_map[type]:
            suggested_type = type

        #If no match, see if we can match by attempting to turn name to singular
        if suggested_type == '':
            if entity_name[-1] == "s":
                singular_name = entity_name[0:-1]
                if singular_name in entity_type_map[type]:
                    suggested_type = type

        #If no match, see if we can substr the type map entries into entity name
        if suggested_type == '':
            for keyword in entity_type_map[type]:
                if keyword in entity_name:
                    suggested_type = type

    #If still no match, abstract icons will be assigned to this entity
    if suggested_type == '':
        suggested_type = 'abstract'

    print(suggested_type)
    if suggested_type == 'abstract':
        limit = len(abstract_icons) - 1
        suggested_icon = abstract_icons[randint(0, limit)]
    else:
        limit = len(default_icon_map[suggested_type]) - 1
        suggested_icon = default_icon_map[suggested_type][randint(0, limit)]

    return suggested_icon
