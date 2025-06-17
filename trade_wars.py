#!/usr/bin/env python3
"""
Trade Wars - BBS Door Game
A classic space conquest and trading game
"""

import random
import json
import os
import time
from datetime import datetime, timedelta

class Player:
    def __init__(self, name):
        self.name = name
        self.credits = 5000
        self.experience = 0
        self.alignment = 0  # -1000 (evil) to +1000 (good)
        self.turns_left = 150
        self.last_played = datetime.now().isoformat()
        
        # Ship stats
        self.ship_type = "Merchant Cruiser"
        self.fighters = 10
        self.shields = 100
        self.max_shields = 100
        self.holds = 20
        self.max_holds = 20
        
        # Location
        self.current_sector = 1
        
        # Cargo
        self.fuel_ore = 0
        self.organics = 0
        self.equipment = 0
        
        # Stats
        self.planets_owned = 0
        self.sectors_controlled = 0
        self.total_kills = 0
        
        # Game progression
        self.rank = "Harmless"
        self.corporation = None
        
    def to_dict(self):
        return self.__dict__
    
    @classmethod
    def from_dict(cls, data):
        player = cls(data['name'])
        for key, value in data.items():
            setattr(player, key, value)
        return player
    
    def calculate_rank(self):
        """Calculate player rank based on experience"""
        if self.experience < 100:
            self.rank = "Harmless"
        elif self.experience < 500:
            self.rank = "Mostly Harmless"
        elif self.experience < 1500:
            self.rank = "Poor"
        elif self.experience < 4000:
            self.rank = "Average"
        elif self.experience < 8000:
            self.rank = "Above Average"
        elif self.experience < 15000:
            self.rank = "Competent"
        elif self.experience < 25000:
            self.rank = "Dangerous"
        elif self.experience < 50000:
            self.rank = "Deadly"
        else:
            self.rank = "Elite"
    
    def get_cargo_used(self):
        return self.fuel_ore + self.organics + self.equipment
    
    def get_cargo_free(self):
        return self.max_holds - self.get_cargo_used()

class Sector:
    def __init__(self, sector_id):
        self.id = sector_id
        self.name = f"Sector {sector_id}"
        self.warps = []
        self.planet = None
        self.port = None
        self.traders = []
        self.mines = 0
        self.fighters = 0
        self.owner = None
        
        # Generate random connections
        self.generate_warps()
        
        # Randomly place ports and planets
        if random.random() < 0.3:  # 30% chance of port
            self.port = self.generate_port()
        
        if random.random() < 0.15:  # 15% chance of planet
            self.planet = self.generate_planet()
    
    def generate_warps(self):
        """Generate 2-6 warp connections to other sectors"""
        num_warps = random.randint(2, 6)
        for _ in range(num_warps):
            # In a real game, these would be bidirectional
            warp_to = random.randint(1, 1000)
            if warp_to != self.id and warp_to not in self.warps:
                self.warps.append(warp_to)
    
    def generate_port(self):
        """Generate a trading port"""
        port_types = [
            {"name": "Stardock", "buys": ["Equipment"], "sells": ["Fuel Ore", "Organics"]},
            {"name": "Ore Refinery", "buys": ["Fuel Ore"], "sells": ["Equipment", "Organics"]},
            {"name": "Agricultural", "buys": ["Organics"], "sells": ["Fuel Ore", "Equipment"]},
            {"name": "Industrial", "buys": ["Fuel Ore", "Organics"], "sells": ["Equipment"]}
        ]
        return random.choice(port_types)
    
    def generate_planet(self):
        """Generate a planet"""
        planet_classes = ["M", "K", "L", "H", "Y"]
        return {
            "name": f"Planet {chr(65 + random.randint(0, 25))}",
            "class": random.choice(planet_classes),
            "owner": None,
            "citadel": False,
            "fighters": 0,
            "shields": 0
        }

class Universe:
    def __init__(self):
        self.sectors = {}
        self.max_sectors = 1000
        
        # Generate starting sectors
        for i in range(1, 101):  # Generate first 100 sectors
            self.sectors[i] = Sector(i)
        
        # Ensure sector 1 has basic connections
        if 1 not in self.sectors:
            self.sectors[1] = Sector(1)
        
        # Make sure starting area is well connected
        for i in range(1, 11):
            if i not in self.sectors[1].warps and i != 1:
                self.sectors[1].warps.append(i)
    
    def get_sector(self, sector_id):
        if sector_id not in self.sectors:
            self.sectors[sector_id] = Sector(sector_id)
        return self.sectors[sector_id]

class TradeWars:
    def __init__(self):
        self.player_data_dir = "../player_data"
        self.universe_file = "../player_data/trade_wars_universe.json"
        self.ensure_data_dir()
        self.universe = Universe()
        self.load_universe()
        
    def ensure_data_dir(self):
        if not os.path.exists(self.player_data_dir):
            os.makedirs(self.player_data_dir)
    
    def save_player(self, player):
        filename = os.path.join(self.player_data_dir, f"{player.name.lower()}_tradewars.json")
        with open(filename, 'w') as f:
            json.dump(player.to_dict(), f, indent=2)
    
    def load_player(self, name):
        filename = os.path.join(self.player_data_dir, f"{name.lower()}_tradewars.json")
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                return Player.from_dict(data)
        return None
    
    def save_universe(self):
        """Save universe state (simplified)"""
        # In a real game, this would save the entire universe state
        pass
    
    def load_universe(self):
        """Load universe state (simplified)"""
        # In a real game, this would load persistent universe state
        pass
    
    def display_banner(self):
        banner = [
            "",
            "" + "="*60,
            "                    T R A D E   W A R S",
            "                 Space Conquest & Trading",
            "" + "="*60,
            "",
            "The year is 2391. Humanity has spread across the galaxy",
            "in a network of interconnected space lanes. You are a",
            "trader, warrior, and explorer in this vast frontier.",
            "",
            "Your mission: Build an empire among the stars!",
            "",
        ]
        
        for line in banner:
            print(line)
    
    def display_player_status(self, player):
        player.calculate_rank()
        print(f"\n{'='*50}")
        print(f"COMMANDER: {player.name} [{player.rank}]")
        print(f"Credits: {player.credits:,} | Experience: {player.experience}")
        print(f"Alignment: {player.alignment} | Turns: {player.turns_left}")
        print(f"")
        print(f"Ship: {player.ship_type}")
        print(f"Shields: {player.shields}/{player.max_shields} | Fighters: {player.fighters}")
        print(f"Cargo Hold: {player.get_cargo_used()}/{player.max_holds}")
        if player.get_cargo_used() > 0:
            print(f"  Fuel Ore: {player.fuel_ore} | Organics: {player.organics} | Equipment: {player.equipment}")
        print(f"Current Sector: {player.current_sector}")
        print(f"{'='*50}\n")
    
    def display_sector_info(self, player):
        sector = self.universe.get_sector(player.current_sector)
        print(f"\n--- {sector.name} ---")
        
        if sector.port:
            print(f"\nPort: {sector.port['name']}")
            print(f"   Buying: {', '.join(sector.port['buys'])}")
            print(f"   Selling: {', '.join(sector.port['sells'])}")
        
        if sector.planet:
            print(f"\nPlanet: {sector.planet['name']} (Class {sector.planet['class']})")
            if sector.planet['owner']:
                print(f"   Owner: {sector.planet['owner']}")
            else:
                print(f"   Status: Unexplored")
        
        if sector.fighters > 0:
            print(f"\nDefensive Fighters: {sector.fighters}")
            if sector.owner:
                print(f"   Controlled by: {sector.owner}")
        
        print(f"\nWarp Gates to: {', '.join(map(str, sector.warps[:6]))}")
        if len(sector.warps) > 6:
            print(f"   (and {len(sector.warps) - 6} more...)")
    
    def main_menu(self, player):
        while player.turns_left > 0:
            self.display_player_status(player)
            self.display_sector_info(player)
            
            print("Commands:")
            print("  [M]ove to sector    [T]rade at port     [P]lanet operations")
            print("  [A]ttack fighters   [D]eploy fighters   [S]can sector")
            print("  [C]omputer          [R]eport            [Q]uit game")
            
            command = input("\nEnter command: ").strip().upper()
            
            if command in ['Q', 'QUIT']:
                print("\nThanks for playing Trade Wars!")
                print("Your progress has been saved.")
                break
            elif command in ['M', 'MOVE']:
                self.move_command(player)
            elif command in ['T', 'TRADE']:
                self.trade_command(player)
            elif command in ['P', 'PLANET']:
                self.planet_command(player)
            elif command in ['A', 'ATTACK']:
                self.attack_command(player)
            elif command in ['D', 'DEPLOY']:
                self.deploy_command(player)
            elif command in ['S', 'SCAN']:
                self.scan_command(player)
            elif command in ['C', 'COMPUTER']:
                self.computer_command(player)
            elif command in ['R', 'REPORT']:
                self.report_command(player)
            else:
                print("\nInvalid command. Try again.")
            
            input("\nPress Enter to continue...")
            
            # Save progress
            self.save_player(player)
        
        if player.turns_left <= 0:
            print("\nYou have used all your turns for today!")
            print("Return tomorrow for more space adventures!")
    
    def move_command(self, player):
        sector = self.universe.get_sector(player.current_sector)
        print(f"\nWarp Gates from Sector {player.current_sector}:")
        
        for i, warp in enumerate(sector.warps[:10], 1):
            print(f"  {i}. Sector {warp}")
        
        try:
            choice = input("\nChoose destination (number or sector ID): ")
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(sector.warps):
                    destination = sector.warps[choice_num - 1]
                else:
                    destination = choice_num
            else:
                print("Invalid input.")
                return
            
            if destination in sector.warps or destination == int(choice):
                player.current_sector = destination
                player.turns_left -= 1
                print(f"\nWarping to Sector {destination}...")
                
                # Random encounters
                if random.random() < 0.1:  # 10% chance
                    self.random_encounter(player)
            else:
                print(f"\nNo warp gate to Sector {destination} from here.")
        
        except ValueError:
            print("Invalid input.")
    
    def trade_command(self, player):
        sector = self.universe.get_sector(player.current_sector)
        
        if not sector.port:
            print("\nNo trading port in this sector.")
            return
        
        port = sector.port
        print(f"\nWelcome to {port['name']} Trading Post")
        print("\n[B]uy goods | [S]ell goods | [L]eave port")
        
        choice = input("\nWhat would you like to do? ").strip().upper()
        
        if choice in ['B', 'BUY']:
            self.buy_goods(player, port)
        elif choice in ['S', 'SELL']:
            self.sell_goods(player, port)
        elif choice in ['L', 'LEAVE']:
            print("\nLeaving port.")
        else:
            print("\nInvalid choice.")
    
    def buy_goods(self, player, port):
        print(f"\n{port['name']} - BUYING GOODS")
        print(f"Available goods: {', '.join(port['sells'])}")
        print(f"Your credits: {player.credits:,}")
        print(f"Cargo space: {player.get_cargo_free()} holds available")
        
        # Simplified pricing
        prices = {"Fuel Ore": 15, "Organics": 25, "Equipment": 50}
        
        for good in port['sells']:
            price = prices[good]
            max_affordable = player.credits // price
            max_cargo = player.get_cargo_free()
            max_buy = min(max_affordable, max_cargo)
            
            if max_buy > 0:
                print(f"\n{good}: {price} credits each (max: {max_buy})")
                try:
                    amount = int(input(f"Buy how many {good}? (0 to skip): "))
                    if 0 < amount <= max_buy:
                        cost = amount * price
                        player.credits -= cost
                        
                        if good == "Fuel Ore":
                            player.fuel_ore += amount
                        elif good == "Organics":
                            player.organics += amount
                        elif good == "Equipment":
                            player.equipment += amount
                        
                        print(f"\nPurchased {amount} {good} for {cost:,} credits!")
                except ValueError:
                    continue
    
    def sell_goods(self, player, port):
        print(f"\n{port['name']} - SELLING GOODS")
        print(f"Port buying: {', '.join(port['buys'])}")
        
        # Simplified pricing (sell for more than buy)
        prices = {"Fuel Ore": 20, "Organics": 35, "Equipment": 75}
        
        cargo = {
            "Fuel Ore": player.fuel_ore,
            "Organics": player.organics,
            "Equipment": player.equipment
        }
        
        for good in port['buys']:
            if cargo[good] > 0:
                price = prices[good]
                print(f"\n{good}: {cargo[good]} units at {price} credits each")
                try:
                    amount = int(input(f"Sell how many {good}? (0 to skip): "))
                    if 0 < amount <= cargo[good]:
                        earnings = amount * price
                        player.credits += earnings
                        
                        if good == "Fuel Ore":
                            player.fuel_ore -= amount
                        elif good == "Organics":
                            player.organics -= amount
                        elif good == "Equipment":
                            player.equipment -= amount
                        
                        print(f"\nSold {amount} {good} for {earnings:,} credits!")
                except ValueError:
                    continue
    
    def planet_command(self, player):
        sector = self.universe.get_sector(player.current_sector)
        
        if not sector.planet:
            print("\nNo planet in this sector.")
            return
        
        planet = sector.planet
        print(f"\nPlanet: {planet['name']} (Class {planet['class']})")
        
        if planet['owner'] == player.name:
            print(f"This is your planet!")
            print("[V]iew status | [U]pgrade defenses | [L]eave")
        elif planet['owner']:
            print(f"Planet controlled by: {planet['owner']}")
            print("[A]ttack planet | [L]eave")
        else:
            print("Unexplored planet available for colonization!")
            print("[C]olonize planet | [L]eave")
        
        choice = input("\nWhat would you like to do? ").strip().upper()
        
        if choice in ['C', 'COLONIZE'] and not planet['owner']:
            cost = 10000
            if player.credits >= cost:
                player.credits -= cost
                planet['owner'] = player.name
                player.planets_owned += 1
                player.experience += 500
                print(f"\nPlanet colonized! Cost: {cost:,} credits")
            else:
                print(f"\nNeed {cost:,} credits to colonize.")
        
        elif choice in ['L', 'LEAVE']:
            print("\nLeaving planet orbit.")
    
    def attack_command(self, player):
        sector = self.universe.get_sector(player.current_sector)
        
        if sector.fighters <= 0:
            print("\nNo enemy fighters to attack in this sector.")
            return
        
        print(f"\nAttacking {sector.fighters} enemy fighters!")
        print(f"Your fighters: {player.fighters}")
        
        if player.fighters <= 0:
            print("You have no fighters to attack with!")
            return
        
        # Simple combat resolution
        enemy_fighters = sector.fighters
        battle_rounds = 0
        
        while player.fighters > 0 and enemy_fighters > 0 and battle_rounds < 5:
            # Player attacks
            player_damage = random.randint(1, player.fighters)
            enemy_fighters = max(0, enemy_fighters - player_damage)
            
            # Enemy attacks back
            if enemy_fighters > 0:
                enemy_damage = random.randint(1, enemy_fighters)
                player.fighters = max(0, player.fighters - enemy_damage)
            
            battle_rounds += 1
            print(f"Round {battle_rounds}: Enemy fighters: {enemy_fighters}, Your fighters: {player.fighters}")
        
        if enemy_fighters <= 0:
            print(f"\nVictory! Sector conquered!")
            reward = sector.fighters * 100
            player.credits += reward
            player.experience += sector.fighters * 50
            player.total_kills += sector.fighters
            sector.fighters = 0
            sector.owner = player.name
            player.sectors_controlled += 1
            print(f"Reward: {reward:,} credits and experience!")
        else:
            print(f"\nRetreat! Enemy forces too strong.")
        
        player.turns_left -= 1
    
    def deploy_command(self, player):
        if player.fighters <= 0:
            print("\nYou have no fighters to deploy.")
            return
        
        print(f"\nDeploy Fighters")
        print(f"Available fighters: {player.fighters}")
        
        try:
            amount = int(input("Deploy how many fighters? "))
            if 0 < amount <= player.fighters:
                sector = self.universe.get_sector(player.current_sector)
                player.fighters -= amount
                sector.fighters += amount
                sector.owner = player.name
                player.turns_left -= 1
                print(f"\nDeployed {amount} fighters to defend this sector!")
            else:
                print("\nInvalid amount.")
        except ValueError:
            print("\nInvalid input.")
    
    def scan_command(self, player):
        print(f"\nLong Range Scan from Sector {player.current_sector}")
        
        sector = self.universe.get_sector(player.current_sector)
        
        print(f"\nAdjacent sectors:")
        for warp in sector.warps[:8]:
            scan_sector = self.universe.get_sector(warp)
            info = f"Sector {warp}: "
            
            if scan_sector.port:
                info += f"Port({scan_sector.port['name']}) "
            if scan_sector.planet:
                info += f"Planet "
            if scan_sector.fighters > 0:
                info += f"Fighters({scan_sector.fighters}) "
            if not any([scan_sector.port, scan_sector.planet, scan_sector.fighters]):
                info += "Empty space"
            
            print(f"  {info}")
        
        player.turns_left -= 1
    
    def computer_command(self, player):
        print(f"\nShip Computer - Trade Wars Database")
        print("\n[1] Sector database")
        print("[2] Player rankings")
        print("[3] Trading analysis")
        print("[4] Exit computer")
        
        choice = input("\nSelect option: ")
        
        if choice == "1":
            print(f"\nKnown sectors with special features:")
            count = 0
            for sector_id, sector in self.universe.sectors.items():
                if sector.port or sector.planet:
                    if count < 10:  # Show first 10
                        features = []
                        if sector.port:
                            features.append(f"Port({sector.port['name']})")
                        if sector.planet:
                            features.append(f"Planet({sector.planet['name']})")
                        print(f"  Sector {sector_id}: {', '.join(features)}")
                        count += 1
                    else:
                        break
        
        elif choice == "3":
            print(f"\nTrading Analysis:")
            print(f"Recommended trade routes:")
            print(f"  - Buy Fuel Ore (15cr) -> Sell to Stardock (20cr)")
            print(f"  - Buy Organics (25cr) -> Sell to Industrial (35cr)")
            print(f"  - Buy Equipment (50cr) -> Sell to Agricultural (75cr)")
    
    def report_command(self, player):
        print(f"\nCommander Report for {player.name}")
        print(f"Rank: {player.rank}")
        print(f"Total Experience: {player.experience:,}")
        print(f"Net Worth: {player.credits:,} credits")
        print(f"Planets Owned: {player.planets_owned}")
        print(f"Sectors Controlled: {player.sectors_controlled}")
        print(f"Total Kills: {player.total_kills}")
        print(f"Alignment: {player.alignment} {'(Good)' if player.alignment > 0 else '(Evil)' if player.alignment < 0 else '(Neutral)'}")
    
    def random_encounter(self, player):
        """Random events during travel"""
        encounters = [
            "space_pirates", "alien_trader", "derelict_ship", "cosmic_storm"
        ]
        
        encounter = random.choice(encounters)
        
        if encounter == "space_pirates":
            print(f"\nSpace Pirates attack!")
            if player.fighters > 0:
                damage = random.randint(1, 3)
                player.fighters = max(0, player.fighters - damage)
                print(f"Lost {damage} fighters in the battle!")
            else:
                credits_lost = min(player.credits // 4, 1000)
                player.credits = max(0, player.credits - credits_lost)
                print(f"Pirates steal {credits_lost:,} credits!")
        
        elif encounter == "alien_trader":
            print(f"\nFriendly alien trader offers a deal!")
            if player.credits >= 500:
                player.credits -= 500
                player.fighters += random.randint(1, 3)
                print(f"Traded 500 credits for fighters!")
        
        elif encounter == "derelict_ship":
            print(f"\nFound a derelict ship!")
            salvage = random.randint(200, 800)
            player.credits += salvage
            print(f"Salvaged {salvage:,} credits worth of equipment!")
        
        elif encounter == "cosmic_storm":
            print(f"\nCaught in a cosmic storm!")
            if player.shields > 20:
                damage = random.randint(10, 30)
                player.shields = max(0, player.shields - damage)
                print(f"Storm damages shields by {damage} points!")
    
    def run(self):
        self.display_banner()
        
        name = input("Enter your commander name: ").strip()
        if not name:
            name = "Anonymous"
        
        # Load existing player or create new one
        player = self.load_player(name)
        if player is None:
            player = Player(name)
            print(f"\nWelcome to Trade Wars, Commander {name}!")
            print("You begin your journey in Sector 1 with a basic ship.")
            print("Your mission: Explore, trade, and conquer the galaxy!")
        else:
            print(f"\nWelcome back, Commander {name}!")
            # Reset daily turns (in real BBS, this would be date-based)
            last_played = datetime.fromisoformat(player.last_played)
            if datetime.now() - last_played > timedelta(hours=6):  # 6 hour reset for demo
                player.turns_left = 150
                player.last_played = datetime.now().isoformat()
                print("Your turns have been restored!")
        
        input("\nPress Enter to begin your space adventure...")
        
        self.main_game_loop(player)
        self.save_player(player)
    
    def main_game_loop(self, player):
        try:
            self.main_menu(player)
        except KeyboardInterrupt:
            print("\n\nGame interrupted. Progress saved.")
            self.save_player(player)

if __name__ == "__main__":
    game = TradeWars()
    game.run()
