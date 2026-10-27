"""Explicit taxonomy and authored, conditional recommendations, not AI-generated advice."""
from copy import deepcopy

COMPOST_SOURCE = "https://www.epa.gov/recycle/composting-home"
RECYCLE_SOURCE = "https://www.epa.gov/recycle/how-do-i-recycle-common-recyclables"
ELECTRONICS_SOURCE = "https://www.epa.gov/recycle/electronics-donation-and-recycling"
BATTERY_SOURCE = "https://www.epa.gov/recycle/used-household-batteries"
REGROW_SOURCE = "https://eat-move-save.extension.illinois.edu/save/save-your-money/regrowing-scrap-veggies"

COMPOST = dict(action="Compost", title="Turn suitable scraps into compost",
    conditions="Confirm this is an uncontaminated plant-based scrap. Remove stickers and packaging. This advice is for a backyard compost pile, not every composting method.",
    steps=["Collect the suitable scraps in a covered container.", "Chop large pieces and mix with dry leaves or other suitable brown material.", "Maintain air and moisture in the compost pile.", "Allow decomposition and curing; use finished compost to improve soil."],
    note="Raw scraps are not finished fertilizer. Keep meat, dairy, oily food and contaminated material out of a typical backyard compost pile.", source_url=COMPOST_SOURCE)
RECYCLE = dict(action="Recycle", title="Check your local recycling collection",
    conditions="Confirm the material and check that your local collector accepts this item. A visual prediction cannot confirm polymer type, coatings or contamination.",
    steps=["Empty the item.", "Prepare it according to your local collector's instructions.", "Separate it into the accepted material stream, or ask a local waste bank / bank sampah."],
    note="Collection rules vary by location; a material label is not a guarantee of recyclability.", source_url=RECYCLE_SOURCE)

def rule(action, title, conditions, steps, note="", source_url=RECYCLE_SOURCE):
    return dict(action=action, title=title, conditions=conditions, steps=steps, note=note, source_url=source_url)

def item(key, name, prompt, category, recommendations, handling="General household item"):
    return dict(key=key, name=name, prompt="a photo of " + prompt, category=category,
                handling=handling, recommendations=deepcopy(recommendations))

CATALOG = [
    item("banana_peel", "Banana peel", "a banana peel", "Organic", [COMPOST]),
    item("orange_peel", "Orange peel", "an orange peel", "Organic", [COMPOST]),
    item("apple_core", "Apple core", "an apple core", "Organic", [COMPOST]),
    item("eggshell", "Eggshell", "a broken egg shell", "Organic", [rule("Compost", "Add crushed eggshells to compost", "Confirm this is an eggshell without packaging or chemical contamination.", ["Crush the shell into small pieces.", "Mix it into the compost pile with other appropriate ingredients.", "Screen out remaining shell pieces when harvesting compost."], "Shell fragments decompose slowly; this does not promise an immediate fertilizer effect.", COMPOST_SOURCE)]),
    item("dry_leaf", "Dry leaf", "dry leaves", "Organic", [rule("Compost", "Use dry leaves as compost browns", "Use untreated leaves suitable for backyard composting; check for disease or herbicide contamination.", ["Break up large leaves.", "Mix with suitable food scraps in the compost pile.", "Keep the pile aerated and moist."], source_url=COMPOST_SOURCE)]),
    item("vegetable_scraps", "Vegetable scraps", "vegetable scraps", "Organic", [COMPOST]),
    item("fruit", "Fruit / fruit scraps", "discarded fruit", "Organic", [rule("Check", "Confirm whether it is actually waste", "A photograph cannot determine food safety, spoilage or whether an object has been discarded.", ["Confirm the item's condition and intended use.", "If it is a suitable discarded plant-based scrap, follow composting guidance."], "Do not infer edibility from this prediction.", COMPOST_SOURCE), COMPOST]),
    item("spring_onion", "Spring onion / rooted scrap", "a spring onion with roots", "Organic", [rule("Regrow", "Try regrowing a suitable rooted base", "Only applies after confirming a spring-onion base with suitable roots and condition. The model cannot verify plant viability.", ["Identify the plant and retain a suitable rooted base.", "Follow the linked extension guide for regrowing and care.", "Monitor growth; compost unsuitable plant scraps instead."], "Not every organic object can be planted.", REGROW_SOURCE), COMPOST]),
    item("glass_bottle", "Glass bottle", "a glass beer bottle", "Inorganic", [RECYCLE]),
    item("plastic_bottle", "Plastic bottle", "a plastic water bottle", "Inorganic", [rule("Reuse", "Make a small non-food organizer", "Use only a clean, undamaged household bottle of known origin. Do not reuse containers that held hazardous chemicals.", ["Clean and dry the suitable container.", "Use it for small non-food items; choose a design that avoids sharp exposed edges.", "Recycle it later if accepted locally."], "Reuse idea authored for this application; applicability requires inspection."), RECYCLE]),
    item("metal_can", "Metal can", "metal can", "Inorganic", [rule("Reuse", "Use a suitable can as a desk organizer", "Only use a clean, undamaged can with no sharp or rusty edges. Excludes aerosol and chemical containers.", ["Inspect the can and discard the reuse option if its edges are sharp.", "Clean and dry it.", "Use it to hold non-food stationery."], "Do not attempt to flatten or cut a can for this suggestion."), RECYCLE]),
    item("metal_lid", "Metal lid", "a metal can lid", "Inorganic", [RECYCLE], "Check for sharp edges"),
    item("plastic_bag", "Plastic bag", "plastic bag", "Inorganic", [rule("Reuse", "Reuse a suitable bag", "Only applies to a clean, intact bag that has not held contaminated material.", ["Inspect and clean it if appropriate.", "Reuse for carrying non-food items.", "Check for a local film-plastic collection when worn out."], "Many curbside recycling programs do not accept flexible plastic bags."), RECYCLE]),
    item("cardboard", "Cardboard", "a stack of corrugated cardboard", "Inorganic", [rule("Reuse", "Make drawer dividers", "Use clean, dry, uncontaminated cardboard.", ["Measure the drawer compartments.", "Prepare cardboard dividers with appropriate tools and supervision.", "Arrange them to separate small household items."], "This app uses the common dry-recyclables sorting convention; cardboard is plant-derived."), RECYCLE]),
    item("paper", "Paper", "crumpled paper", "Inorganic", [rule("Reuse", "Use clean paper for packing", "Use clean, dry paper without sensitive information or contamination.", ["Keep usable sheets for notes.", "Use suitable crumpled paper to cushion non-food items.", "Recycle when no longer reusable, if locally accepted."], "Paper is plant-derived; its Inorganic label here means the dry-recyclables bin."), RECYCLE]),
    item("drink_carton", "Drink carton", "a milk carton", "Inorganic", [RECYCLE], "Often a composite material"),
    item("plastic_cup", "Plastic cup", "a plastic cup", "Inorganic", [RECYCLE]),
    item("paper_cup", "Paper cup", "a paper cup", "Inorganic", [RECYCLE], "Check lining and local acceptance"),
    item("glass_jar", "Glass jar", "a glass jar", "Inorganic", [rule("Reuse", "Store small non-food items", "Use a clean jar with no chips, cracks or hazardous previous contents.", ["Inspect, clean and dry the jar.", "Use it for buttons, clips or other small non-food items.", "Keep breakable glass in a suitable place."], "Reuse idea requires inspection."), RECYCLE]),
    item("aluminium_foil", "Aluminium foil", "aluminum foil", "Inorganic", [RECYCLE]),
    item("plastic_utensils", "Plastic utensils", "plastic cutlery", "Inorganic", [RECYCLE]),
    item("styrofoam", "Foam packaging", "styrofoam packaging", "Inorganic", [RECYCLE], "Special collection may be required"),
    item("cigarette_butt", "Cigarette butt", "cigarette butts", "Inorganic", [rule("Dispose", "Use the appropriate residual-waste collection", "Confirm the item is a discarded cigarette butt and completely extinguished.", ["Keep it out of compost and normal recyclables.", "Follow local residual-waste collection instructions."], "No craft, composting or planting recommendation applies.")], "Residual waste; confirm local handling"),
    item("battery", "Battery", "a battery", "Inorganic", [rule("Special collection", "Find a battery collection service", "Confirm battery type and condition using appropriate local guidance.", ["Keep batteries separate from ordinary household recycling.", "Consult the linked battery guidance and an appropriate local collector."], "No dismantling, heating or craft reuse is recommended.", BATTERY_SOURCE)], "Special handling"),
    item("mobile_phone", "Mobile phone", "a mobile phone", "Inorganic", [rule("Repair / collect", "Consider repair or electronics collection", "First confirm ownership and whether the device is actually discarded.", ["Consider repair, continued use or donation if appropriate.", "Before transfer, follow the manufacturer's process to protect personal data.", "Use an appropriate electronics collector for an unusable device."], "Do not dismantle the device or battery for a craft project.", ELECTRONICS_SOURCE)], "Electronics collection"),
    item("camera", "Camera", "a camera", "Inorganic", [rule("Repair / collect", "Repair, donate or collect as electronics", "Confirm ownership, condition and whether the device is discarded.", ["Consider repair or donation if usable.", "Follow local electronics collection instructions if unusable."], "The model cannot assess electrical or battery condition.", ELECTRONICS_SOURCE)], "Electronics collection"),
    item("calculator", "Calculator", "a calculator", "Inorganic", [rule("Repair / collect", "Reuse or collect as electronics", "Confirm whether the calculator is usable and whether it contains a battery.", ["Continue using or donate it if appropriate.", "Use an appropriate electronics / battery collection service when unusable."], source_url=ELECTRONICS_SOURCE)], "Electronics collection"),
    item("biodegradable", "Biodegradable material", "plant based food waste", "Organic", [rule("Check", "Identify the material before choosing treatment", "This is a broad dataset label, not confirmation that the item is suitable for a home compost pile.", ["Confirm the actual material and whether it is contaminated.", "Only follow composting guidance for suitable ingredients."], "Biodegradability, home compostability and plant viability are different properties.", COMPOST_SOURCE)]),
    item("plastic", "Plastic material", "plastic packaging", "Inorganic", [RECYCLE]),
    item("glass", "Glass material", "discarded glass", "Inorganic", [RECYCLE], "Inspect for broken glass"),
    item("metal", "Metal material", "scrap metal", "Inorganic", [RECYCLE], "Inspect for sharp edges"),
]
BY_KEY = {x["key"]: x for x in CATALOG}
# Broad dataset labels are supported for an optionally trained YOLO model but
# are not queried alongside specific objects by the default open-vocabulary model.
DEFAULT_KEYS = [x["key"] for x in CATALOG if x["key"] not in {"biodegradable", "plastic", "glass", "metal", "metal_lid"}]

def lookup(key):
    return deepcopy(BY_KEY.get(key, dict(key=key, name=key.replace("_", " "),
        category="Needs review", handling="Unmapped model class", recommendations=[])))
