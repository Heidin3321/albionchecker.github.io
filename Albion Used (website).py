from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from collections import defaultdict
import os
import json

app = Flask(__name__)

TIER_KEYWORDS = {
    "Beginner": "Tier 1", "Novice": "Tier 2", "Journeyman": "Tier 3",
    "Adept's": "Tier 4", "Expert's": "Tier 5", "Master's": "Tier 6",
    "Grandmaster's": "Tier 7", "Elder's": "Tier 8"
}

def load_item_categories_from_json():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(script_dir, 'item_categories.json')
    with open(json_path) as f:
        return json.load(f)


ITEM_CATEGORIES = load_item_categories_from_json()

def generate_item_image_urls():
    ITEM_IMAGE_URLS = {}
    
    # Define the pattern for item names and their corresponding image URLs
    item_patterns = {
        "Hallowfall": "T8_MAIN_HOLYSTAFF_AVALON.png",
        "Fallen Staff": "T8_2H_HOLYSTAFF_HELL.png",
        "Blight Staff": "T8_2H_NATURESTAFF_HELL.png",
        "Great Holy Staff": "T8_2H_HOLYSTAFF.png",
        "Rampant Staff": "T8_2H_NATURESTAFF_KEEPER",
        "Wild Staff": "T8_2H_WILDSTAFF",
        "Eye of Secrets": "T8_OFF_ORB_MORGANA",
        "Celestial Censer": "T8_OFF_CENSER_AVALON",
        "Sarcophagus": "T8_OFF_TOWERSHIELD_UNDEAD",
        "Mistcaller": "T8_OFF_HORN_KEEPER",
        "Cleric Cowl": "T8_HEAD_CLOTH_SET2",
        "Assassin Hood": "T8_HEAD_LEATHER_SET3",
        "Guardian He": "T8_HEAD_PLATE_SET3",
        "Knight Helmet": "T8_HEAD_PLATE_SET2",
        "Robe of Purity": "T8_ARMOR_CLOTH_AVALON",
        "Feyscale Robe" : "T8_ARMOR_CLOTH_FEY",
        "Cleric Robe": "T8_ARMOR_CLOTH_SET2",
        "Judicator Armor": "T8_ARMOR_PLATE_KEEPER",
        "Graveguard Boots": "T8_SHOES_PLATE_UNDEAD",
        "Boots of Valor": "T8_SHOES_PLATE_AVALON",
        "Stalker Shoes": "T8_SHOES_LEATHER_MORGANA",
        "Adept's Lymhurst Cape": "T8_CAPEITEM_FW_LYMHURST",
        "Adept's Martlock Cape": "T8_CAPEITEM_FW_MARTLOCK",
        "Major Gigantify Potion": "T7_POTION_REVIVE",
        "Major Resistance Potion": "T7_POTION_STONESKIN",
        "Dusthole Crab Omelette": "T7_MEAL_OMELETTE_FISH@1",
        "Avalonian Pork Omelette": "T7_MEAL_OMELETTE_AVALON@2",
        "Pork Omelette": "T7_MEAL_OMELETTE@2",
        "Swiftclaw": "T5_MOUNT_COUGAR_KEEPER",
        "Brecilien Cape": "T8_CAPEITEM_FW_BRECILIEN",
        "Scholar Cowl": "T8_HEAD_CLOTH_SET1",
        # Add more patterns for other item categories as needed
    }
    
    # Generate the ITEM_IMAGE_URLS dictionary based on the patterns
    for category, items in ITEM_CATEGORIES.items():
        for item in items:
            for pattern, image_name in item_patterns.items():
                if pattern.lower() in item.lower():
                    ITEM_IMAGE_URLS[item] = f"https://render.albiononline.com/v1/item/{image_name}"
                    break
    
    return ITEM_IMAGE_URLS

ITEM_IMAGE_URLS = generate_item_image_urls()

def parse_additional_logs(file_path):
    try:
        additional_logs = pd.read_csv(file_path, delimiter='\t').values.tolist()
        return additional_logs
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def parse_and_summarize_logs(logs):
    gear_summary = defaultdict(lambda: {"category": "", "tier": "", "enchantment": "", "withdraw": 0, "added": 0})
    for log in logs:
        try:
            item_name = log[2]
            tier = next((tier_number for keyword, tier_number in TIER_KEYWORDS.items() if keyword in item_name), "")
            enchantment_level = int(log[3])
            
            category = ""
            for cat, items in ITEM_CATEGORIES.items():
                if any(item in item_name for item in items):
                    category = cat
                    break
            
            amount = int(log[5])
            if amount > 0:
                gear_summary[item_name]["added"] += amount
            elif amount < 0:
                gear_summary[item_name]["withdraw"] += abs(amount)
            gear_summary[item_name].update({"category": category, "tier": tier, "enchantment": enchantment_level})
        except IndexError as e:
            print(f"Error processing log: {log} - {e}")
            continue

    # Update gear summary with image URLs
    for item_name, details in gear_summary.items():
        gear_summary[item_name]["image_url"] = ITEM_IMAGE_URLS.get(item_name, "")

    return gear_summary

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        print("No file part")
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        print("No selected file")
        return redirect(request.url)
    
    if file:
        file_path = os.path.join('uploaded_logs.csv')
        file.save(file_path)
        print(f"File saved to {file_path}")
        logs = parse_additional_logs(file_path)
        if not logs:
            print("No logs found after parsing")
            return redirect(request.url)
        gear_summary = parse_and_summarize_logs(logs)
        print(f"Gear summary: {gear_summary}")
        
        return render_template('summary.html', gear_summary=gear_summary, item_image_urls=ITEM_IMAGE_URLS)

if __name__ == '__main__':
    app.run(debug=True)
