#!/usr/bin/env python3
"""
The Pit - BBS Door Game
A gladiator combat game where players fight monsters in an arena
"""

import random
import json
import os
import time

class Player:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.experience = 0
        self.health = 100
        self.max_health = 100
        self.strength = 10
        self.defense = 5
        self.gold = 100
        self.wins = 0
        self.losses = 0
        self.weapon = "Rusty Sword"
        self.armor = "Tattered Rags"
        self.turns_today = 10

    def to_dict(self):
        return self.__dict__
    
    @classmethod
    def from_dict(cls, data):
        player = cls(data['name'])
        for key, value in data.items():
            setattr(player, key, value)
        return player

class Monster:
    def __init__(self, name, health, strength, defense, exp_reward, gold_reward):
        self.name = name
        self.health = health
        self.max_health = health
        self.strength = strength
        self.defense = defense
        self.exp_reward = exp_reward
        self.gold_reward = gold_reward

class ThePit:
    def __init__(self):
        self.player_data_dir = "../player_data"
        self.ensure_data_dir()
        self.monsters = [
            Monster("Goblin", 30, 8, 2, 25, 15),
            Monster("Orc Warrior", 50, 12, 4, 40, 25),
            Monster("Skeleton", 40, 10, 6, 35, 20),
            Monster("Troll", 80, 15, 8, 60, 40),
            Monster("Dragon", 120, 20, 12, 100, 75)
        ]
        
    def ensure_data_dir(self):
        if not os.path.exists(self.player_data_dir):
            os.makedirs(self.player_data_dir)
    
    def save_player(self, player):
        filename = os.path.join(self.player_data_dir, f"{player.name.lower()}_pit.json")
        with open(filename, 'w') as f:
            json.dump(player.to_dict(), f, indent=2)
    
    def load_player(self, name):
        filename = os.path.join(self.player_data_dir, f"{name.lower()}_pit.json")
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                return Player.from_dict(data)
        return None
    
    def display_banner(self):
        print("\n" + "="*60)
        print("               THE PIT - GLADIATOR ARENA")
        print("               Fight! Survive! Conquer!")
        print("="*60)
        print()
    
    def display_player_stats(self, player):
        print(f"\n{'='*40}")
        print(f"GLADIATOR: {player.name}")
        print(f"Level: {player.level} | XP: {player.experience}")
        print(f"Health: {player.health}/{player.max_health}")
        print(f"Strength: {player.strength} | Defense: {player.defense}")
        print(f"Gold: {player.gold}")
        print(f"Record: {player.wins}W - {player.losses}L")
        print(f"Equipment: {player.weapon}, {player.armor}")
        print(f"Turns remaining today: {player.turns_today}")
        print(f"{'='*40}\n")
    
    def get_random_monster(self, player_level):
        # Scale monster selection based on player level
        max_monster_index = min(len(self.monsters) - 1, player_level // 2)
        monster_template = random.choice(self.monsters[:max_monster_index + 1])
        
        # Create a copy and scale it slightly
        monster = Monster(
            monster_template.name,
            monster_template.health,
            monster_template.strength,
            monster_template.defense,
            monster_template.exp_reward,
            monster_template.gold_reward
        )
        return monster
    
    def combat(self, player, monster):
        print(f"\n🗡️  A {monster.name} appears in the arena!")
        print(f"Monster Stats: HP:{monster.health} STR:{monster.strength} DEF:{monster.defense}")
        input("\nPress Enter to begin combat...")
        
        while player.health > 0 and monster.health > 0:
            print(f"\n--- COMBAT ROUND ---")
            print(f"{player.name}: {player.health}/{player.max_health} HP")
            print(f"{monster.name}: {monster.health}/{monster.max_health} HP")
            
            # Player attacks first
            damage = max(1, player.strength - monster.defense + random.randint(-2, 2))
            monster.health -= damage
            print(f"\n⚔️  You strike the {monster.name} for {damage} damage!")
            
            if monster.health <= 0:
                print(f"\n🎉 Victory! The {monster.name} falls!")
                player.experience += monster.exp_reward
                player.gold += monster.gold_reward
                player.wins += 1
                print(f"You gain {monster.exp_reward} experience and {monster.gold_reward} gold!")
                
                # Check for level up
                exp_needed = player.level * 100
                if player.experience >= exp_needed:
                    player.level += 1
                    player.max_health += 20
                    player.health = player.max_health
                    player.strength += 3
                    player.defense += 2
                    print(f"\n🌟 LEVEL UP! You are now level {player.level}!")
                    print(f"Health: +20, Strength: +3, Defense: +2")
                
                return True
            
            # Monster attacks
            damage = max(1, monster.strength - player.defense + random.randint(-2, 2))
            player.health -= damage
            print(f"💀 The {monster.name} strikes you for {damage} damage!")
            
            if player.health <= 0:
                print(f"\n💀 Defeat! You have been slain by the {monster.name}!")
                player.losses += 1
                player.health = 1  # Don't let them die completely
                return False
            
            time.sleep(1)
    
    def shop(self, player):
        weapons = [
            ("Iron Sword", 50, 5),
            ("Steel Blade", 150, 8),
            ("Enchanted Sword", 300, 12),
            ("Dragon Slayer", 500, 18)
        ]
        
        armors = [
            ("Leather Armor", 40, 3),
            ("Chain Mail", 120, 6),
            ("Plate Armor", 250, 10),
            ("Dragon Scale", 400, 15)
        ]
        
        while True:
            print("\n🏪 WEAPON SHOP")
            print("1. Buy Weapon")
            print("2. Buy Armor")
            print("3. Rest (Restore Health - 20 gold)")
            print("4. Leave Shop")
            
            choice = input("\nWhat would you like to do? ")
            
            if choice == "1":
                print("\nWeapons Available:")
                for i, (name, cost, bonus) in enumerate(weapons, 1):
                    print(f"{i}. {name} - {cost} gold (+{bonus} strength)")
                
                try:
                    weapon_choice = int(input("Choose weapon (0 to cancel): "))
                    if 1 <= weapon_choice <= len(weapons):
                        name, cost, bonus = weapons[weapon_choice - 1]
                        if player.gold >= cost:
                            player.gold -= cost
                            player.weapon = name
                            player.strength += bonus
                            print(f"You purchased {name}!")
                        else:
                            print("Not enough gold!")
                except ValueError:
                    pass
            
            elif choice == "2":
                print("\nArmor Available:")
                for i, (name, cost, bonus) in enumerate(armors, 1):
                    print(f"{i}. {name} - {cost} gold (+{bonus} defense)")
                
                try:
                    armor_choice = int(input("Choose armor (0 to cancel): "))
                    if 1 <= armor_choice <= len(armors):
                        name, cost, bonus = armors[armor_choice - 1]
                        if player.gold >= cost:
                            player.gold -= cost
                            player.armor = name
                            player.defense += bonus
                            print(f"You purchased {name}!")
                        else:
                            print("Not enough gold!")
                except ValueError:
                    pass
            
            elif choice == "3":
                if player.gold >= 20:
                    player.gold -= 20
                    player.health = player.max_health
                    print("You rest and restore your health!")
                else:
                    print("Not enough gold to rest!")
            
            elif choice == "4":
                break
    
    def main_game_loop(self, player):
        while True:
            self.display_player_stats(player)
            
            if player.turns_today <= 0:
                print("⏰ You have used all your turns for today!")
                print("Come back tomorrow for more arena battles!")
                break
            
            print("What would you like to do?")
            print("1. Enter the Arena (Fight!)")
            print("2. Visit the Shop")
            print("3. Rest at Inn")
            print("4. View High Scores")
            print("5. Quit Game")
            
            choice = input("\nEnter your choice: ")
            
            if choice == "1":
                if player.health < 10:
                    print("\n💀 You are too injured to fight! Rest first.")
                    continue
                    
                monster = self.get_random_monster(player.level)
                player.turns_today -= 1
                
                if self.combat(player, monster):
                    print("\n🏆 Another victory in the arena!")
                else:
                    print("\n😵 You drag yourself from the arena floor...")
                
                input("\nPress Enter to continue...")
            
            elif choice == "2":
                self.shop(player)
            
            elif choice == "3":
                cost = 30
                if player.gold >= cost:
                    player.gold -= cost
                    player.health = player.max_health
                    print(f"\n🏨 You rest at the inn and restore your health! (-{cost} gold)")
                else:
                    print("\n💰 Not enough gold to rest at the inn!")
                input("Press Enter to continue...")
            
            elif choice == "4":
                print("\n🏆 HIGH SCORES - Top Gladiators")
                # Simple high score display
                print(f"Your Record: Level {player.level}, {player.wins} wins")
                input("\nPress Enter to continue...")
            
            elif choice == "5":
                print("\n👋 Thanks for playing The Pit!")
                print("Your progress has been saved.")
                break
            
            # Save progress after each action
            self.save_player(player)
    
    def run(self):
        self.display_banner()
        
        name = input("Enter your gladiator name: ").strip()
        if not name:
            name = "Anonymous"
        
        # Load existing player or create new one
        player = self.load_player(name)
        if player is None:
            player = Player(name)
            print(f"\n🎊 Welcome to the arena, {name}!")
            print("You start with basic equipment and 10 turns per day.")
        else:
            print(f"\n👋 Welcome back, {name}!")
            # Reset daily turns (in a real BBS, this would be date-based)
            if player.turns_today <= 0:
                player.turns_today = 10
                print("Your daily turns have been restored!")
        
        input("\nPress Enter to continue...")
        
        self.main_game_loop(player)
        self.save_player(player)

if __name__ == "__main__":
    game = ThePit()
    game.run()

