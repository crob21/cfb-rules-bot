#!/usr/bin/env python3
"""
Script to help update league rules from the charter document
"""

import json
import os

def update_league_rules():
    """Interactive script to update league rules"""
    print("🏈 CFB 26 League Rules Updater")
    print("=" * 40)
    
    # Load existing rules
    try:
        with open('data/league_rules.json', 'r') as f:
            rules = json.load(f)
    except FileNotFoundError:
        print("❌ league_rules.json not found. Creating new file...")
        rules = {
            "league_info": {
                "name": "CFB 26 Online Dynasty",
                "season": "2026",
                "platform": "NCAA Football 26",
                "charter_url": "https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit"
            },
            "rules": {}
        }
    
    print("\n📋 Current rule categories:")
    for category in rules.get('rules', {}).keys():
        print(f"  • {category}")
    
    print("\n🔄 Adding/Updating Rules")
    print("Enter rule categories and details (press Enter with empty input to finish)")
    
    while True:
        category = input("\n📝 Rule category (e.g., 'recruiting', 'transfers', 'gameplay'): ").strip()
        if not category:
            break
            
        description = input(f"📄 Description for '{category}': ").strip()
        
        print(f"\n📚 Adding topics for '{category}' (press Enter with empty input to finish):")
        topics = {}
        while True:
            topic = input("  Topic name: ").strip()
            if not topic:
                break
            topic_desc = input(f"  Description for '{topic}': ").strip()
            topics[topic] = topic_desc
        
        # Update rules
        if 'rules' not in rules:
            rules['rules'] = {}
        
        rules['rules'][category] = {
            'description': description,
            'topics': topics
        }
        
        print(f"✅ Added/updated '{category}' with {len(topics)} topics")
    
    # Save updated rules
    os.makedirs('data', exist_ok=True)
    with open('data/league_rules.json', 'w') as f:
        json.dump(rules, f, indent=2)
    
    print(f"\n💾 Rules saved to data/league_rules.json")
    print(f"📊 Total categories: {len(rules['rules'])}")
    
    # Show summary
    print("\n📋 Updated rule categories:")
    for category, data in rules['rules'].items():
        print(f"  • {category}: {len(data.get('topics', {}))} topics")

def add_teams():
    """Add team information"""
    print("\n🏈 Adding Team Information")
    print("=" * 30)
    
    try:
        with open('data/league_rules.json', 'r') as f:
            rules = json.load(f)
    except FileNotFoundError:
        print("❌ league_rules.json not found. Run update_league_rules() first.")
        return
    
    if 'teams' not in rules:
        rules['teams'] = {'conferences': {}}
    
    print("Enter conference information (press Enter with empty input to finish):")
    while True:
        conf_name = input("\n🏆 Conference name: ").strip()
        if not conf_name:
            break
            
        conf_desc = input(f"📄 Description for {conf_name}: ").strip()
        
        print(f"📚 Adding teams to {conf_name} (press Enter with empty input to finish):")
        teams = []
        while True:
            team = input("  Team name: ").strip()
            if not team:
                break
            teams.append(team)
        
        rules['teams']['conferences'][conf_name] = {
            'description': conf_desc,
            'teams': teams
        }
        
        print(f"✅ Added {conf_name} with {len(teams)} teams")
    
    # Save updated rules
    with open('data/league_rules.json', 'w') as f:
        json.dump(rules, f, indent=2)
    
    print(f"\n💾 Team information saved")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Update league rules")
    print("2. Add team information")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        update_league_rules()
    elif choice == "2":
        add_teams()
    elif choice == "3":
        update_league_rules()
        add_teams()
    else:
        print("❌ Invalid choice")
