#!/usr/bin/env python3
"""
Galactic Conquest - BBS Door Game
A space trading game where players buy/sell goods across the galaxy
"""

import random
import json
import os
import time

class Player:
    def __init__(self, name):
        self.name = name
        self.credits = 2000
        self.current_planet = "Earth"
        self.ship_name = "Trader"
        self.cargo_capacity = 50
        self.cargo = {}
        self.fuel = 100
        self.max_fuel = 100
        self.turns_remaining = 100
        self.net_worth = 2000
        self.reputation = 50  # 0-100
        self.ship_upgrades = {
            "cargo_bay": 0,
            "fuel_tank": 0,
            "shields": 0,
            "engines": 0
        }

    def to_dict(self):
        return self.__dict__
    
    @classmethod
    def from_dict(cls, data):
        player = cls(data['name'])
        for key, value in data.items():
            setattr(player, key, value)
        return player

class Planet:
    def __init__(self, name, distance_from_earth, specialties, dangers):
        self.name = name
        self.distance_from_earth = distance_from_earth
        self.specialties = specialties  # Goods this planet produces cheaply
        self.dangers = dangers  # Risk level 0-10
        self.market_prices = {}
        self.generate_market()
    
    def generate_market(self):
        """Generate market prices for this planet"""
        base_goods = {
            "Food": 10,
            "Medicine": 50,
            "Weapons": 75,
            "Electronics": 100,
            "Minerals": 25,
            "Luxury Goods": 150,
            "Machinery": 200,
            "Spices": 80
        }
        
        for good, base_price in base_goods.items():
            # Specialties are cheaper, others vary
            if good in self.specialties:
                price = int(base_price * random.uniform(0.5, 0.8))
            else:
                price = int(base_price * random.uniform(0.8, 1.5))
            
            # Add some market volatility
            price = int(price * random.uniform(0.9, 1.1))
            self.market_prices[good] = max(1, price)

class GalacticConquest:
    def __init__(self):
        self.player_data_dir = "../player_data"
        self.ensure_data_dir()
        self.planets = {
            "Earth": Planet("Earth", 0, ["Food", "Medicine"], 1),
            "Mars": Planet("Mars", 5, ["Minerals", "Machinery"], 2),
            "Alpha Centauri": Planet("Alpha Centauri", 15, ["Electronics", "Luxury Goods"], 4),
            "Rigel VII": Planet("Rigel VII", 25, ["Weapons", "Minerals"], 6),
            "Tau Ceti": Planet("Tau Ceti", 20, ["Spices", "Food"], 3),
            "Wolf 359": Planet("Wolf 359", 30, ["Machinery", "Electronics"], 7),
            "Vega Station": Planet("Vega Station", 35, ["Luxury Goods", "Spices"], 8),
            "Frontier Outpost": Planet("Frontier Outpost", 45, ["Weapons", "Medicine"], 9)
        }
        
    def ensure_data_dir(self):
        if not os.path.exists(self.player_data_dir):
            os.makedirs(self.player_data_dir)
    
    def save_player(self, player):
        filename = os.path.join(self.player_data_dir, f"{player.name.lower()}_galactic.json")
        with open(filename, 'w') as f:
            json.dump(player.to_dict(), f, indent=2)
    
    def load_player(self, name):
        filename = os.path.join(self.player_data_dir, f"{name.lower()}_galactic.json")
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                return Player.from_dict(data)
        return None
    
    def display_banner(self):
        print("\n" + "="*60)
        print("           GALACTIC CONQUEST - SPACE TRADER")
        print("         Buy Low, Sell High, Rule the Galaxy!")
        print("="*60)
        print()
    
    def display_player_status(self, player):
        print(f"\n{'='*50}")
        print(f"CAPTAIN: {player.name} | SHIP: {player.ship_name}")
        print(f"Location: {player.current_planet}")
        print(f"Credits: {player.credits:,} | Net Worth: {player.net_worth:,}")
        print(f"Fuel: {player.fuel}/{player.max_fuel} | Turns: {player.turns_remaining}")
        print(f"Cargo: {sum(player.cargo.values())}/{player.cargo_capacity}")
        print(f"Reputation: {player.reputation}/100")
        if player.cargo:
            print("Current Cargo:")
            for item, quantity in player.cargo.items():
                print(f"  {item}: {quantity}")
        print(f"{'='*50}\n")
    
    def display_market(self, planet):
        print(f"\n📊 {planet.name} MARKET PRICES")
        print(f"Planet Specialty: {', '.join(planet.specialties)}")
        print(f"Danger Level: {planet.dangers}/10")
        print("-" * 40)
        print(f"{'Item':<15} {'Price':<8} {'Stock':<8}")
        print("-" * 40)
        
        for item, price in planet.market_prices.items():
            stock = "High" if item in planet.specialties else "Normal"
            print(f"{item:<15} {price:<8} {stock:<8}")
        print()
    
    def travel_menu(self, player):
        current_planet = self.planets[player.current_planet]
        print("\n🚀 NAVIGATION - Available Destinations")
        print("-" * 50)
        
        destinations = []
        for name, planet in self.planets.items():
            if name != player.current_planet:
                distance = abs(planet.distance_from_earth - current_planet.distance_from_earth)
                fuel_cost = max(5, distance)
                destinations.append((name, planet, fuel_cost))
        
        destinations.sort(key=lambda x: x[2])  # Sort by fuel cost
        
        for i, (name, planet, fuel_cost) in enumerate(destinations, 1):
            affordable = "✓" if fuel_cost <= player.fuel else "✗"
            print(f"{i}. {name:<20} Fuel: {fuel_cost:<3} Danger: {planet.dangers}/10 {affordable}")
        
        print("0. Cancel")
        
        try:
            choice = int(input("\nChoose destination: "))
            if 1 <= choice <= len(destinations):
                name, planet, fuel_cost = destinations[choice - 1]
                if fuel_cost <= player.fuel:
                    return self.travel_to_planet(player, name, fuel_cost)
                else:
                    print("\n⛽ Not enough fuel for that journey!")
                    input("Press Enter to continue...")
            elif choice == 0:
                return
        except ValueError:
            pass
    
    def travel_to_planet(self, player, destination, fuel_cost):
        planet = self.planets[destination]
        print(f"\n🚀 Traveling to {destination}...")
        
        # Random events during travel
        if random.randint(1, 100) <= planet.dangers * 2:
            event = random.choice([
                "pirates", "asteroid_field", "engine_trouble", "customs"
            ])
            
            if event == "pirates":
                print("\n⚔️ PIRATE ATTACK!")
                if random.randint(1, 100) <= player.reputation:
                    print("Your reputation intimidates the pirates. They flee!")
                else:
                    loss = random.randint(100, min(500, player.credits // 4))
                    player.credits = max(0, player.credits - loss)
                    print(f"Pirates steal {loss} credits!")
            
            elif event == "asteroid_field":
                print("\n☄️ Asteroid field detected!")
                extra_fuel = random.randint(5, 15)
                player.fuel = max(0, player.fuel - extra_fuel)
                print(f"Navigation through asteroids costs {extra_fuel} extra fuel!")
            
            elif event == "engine_trouble":
                print("\n⚙️ Engine malfunction!")
                repair_cost = random.randint(50, 200)
                player.credits = max(0, player.credits - repair_cost)
                print(f"Emergency repairs cost {repair_cost} credits!")
            
            elif event == "customs":
                print("\n🛃 Customs inspection!")
                if "Weapons" in player.cargo and player.cargo["Weapons"] > 0:
                    fine = player.cargo["Weapons"] * 25
                    player.credits = max(0, player.credits - fine)
                    print(f"Weapons tax: {fine} credits!")
            
            input("\nPress Enter to continue...")
        
        player.fuel -= fuel_cost
        player.current_planet = destination
        player.turns_remaining -= 1
        
        # Regenerate market prices for realistic trading
        self.planets[destination].generate_market()
        
        print(f"\n✅ Arrived at {destination}!")
        input("Press Enter to continue...")
    
    def trade_menu(self, player):
        planet = self.planets[player.current_planet]
        
        while True:
            self.display_market(planet)
            print(f"Your Credits: {player.credits:,}")
            print(f"Cargo Space: {sum(player.cargo.values())}/{player.cargo_capacity}")
            print("\n1. Buy Goods")
            print("2. Sell Goods")
            print("3. Back to Main Menu")
            
            choice = input("\nWhat would you like to do? ")
            
            if choice == "1":
                self.buy_goods(player, planet)
            elif choice == "2":
                self.sell_goods(player, planet)
            elif choice == "3":
                break
    
    def buy_goods(self, player, planet):
        print("\n💰 BUY GOODS")
        items = list(planet.market_prices.keys())
        
        for i, item in enumerate(items, 1):
            price = planet.market_prices[item]
            max_affordable = player.credits // price
            max_cargo = player.cargo_capacity - sum(player.cargo.values())
            max_buyable = min(max_affordable, max_cargo)
            print(f"{i}. {item} - {price} credits each (max: {max_buyable})")
        
        print("0. Cancel")
        
        try:
            choice = int(input("\nChoose item to buy: "))
            if 1 <= choice <= len(items):
                item = items[choice - 1]
                price = planet.market_prices[item]
                max_affordable = player.credits // price
                max_cargo = player.cargo_capacity - sum(player.cargo.values())
                max_buyable = min(max_affordable, max_cargo)
                
                if max_buyable <= 0:
                    print("\n❌ Cannot buy - insufficient credits or cargo space!")
                    input("Press Enter to continue...")
                    return
                
                quantity = int(input(f"How many {item} to buy (max {max_buyable}): "))
                if 1 <= quantity <= max_buyable:
                    total_cost = quantity * price
                    player.credits -= total_cost
                    player.cargo[item] = player.cargo.get(item, 0) + quantity
                    print(f"\n✅ Bought {quantity} {item} for {total_cost:,} credits!")
                    input("Press Enter to continue...")
        except ValueError:
            pass
    
    def sell_goods(self, player, planet):
        if not player.cargo:
            print("\n📦 No cargo to sell!")
            input("Press Enter to continue...")
            return
        
        print("\n💸 SELL GOODS")
        items = list(player.cargo.keys())
        
        for i, item in enumerate(items, 1):
            quantity = player.cargo[item]
            price = planet.market_prices.get(item, 0)
            total_value = quantity * price
            print(f"{i}. {item} x{quantity} - {price} each = {total_value:,} total")
        
        print("0. Cancel")
        
        try:
            choice = int(input("\nChoose item to sell: "))
            if 1 <= choice <= len(items):
                item = items[choice - 1]
                available = player.cargo[item]
                price = planet.market_prices.get(item, 0)
                
                quantity = int(input(f"How many {item} to sell (max {available}): "))
                if 1 <= quantity <= available:
                    total_value = quantity * price
                    player.credits += total_value
                    player.cargo[item] -= quantity
                    if player.cargo[item] <= 0:
                        del player.cargo[item]
                    
                    # Increase reputation for successful trades
                    player.reputation = min(100, player.reputation + 1)
                    
                    print(f"\n✅ Sold {quantity} {item} for {total_value:,} credits!")
                    input("Press Enter to continue...")
        except ValueError:
            pass
    
    def ship_services(self, player):
        print("\n🔧 SHIP SERVICES")
        print("1. Refuel Ship (5 credits per unit)")
        print("2. Upgrade Cargo Bay (1000 credits, +10 capacity)")
        print("3. Upgrade Fuel Tank (800 credits, +20 max fuel)")
        print("4. Buy Insurance (100 credits, reduces losses)")
        print("5. Back")
        
        choice = input("\nChoose service: ")
        
        if choice == "1":
            needed = player.max_fuel - player.fuel
            cost = needed * 5
            if player.credits >= cost and needed > 0:
                player.credits -= cost
                player.fuel = player.max_fuel
                print(f"\n⛽ Refueled! Cost: {cost} credits")
            elif needed <= 0:
                print("\n⛽ Fuel tank is already full!")
            else:
                print("\n💰 Not enough credits to refuel!")
            input("Press Enter to continue...")
        
        elif choice == "2":
            cost = 1000 * (player.ship_upgrades["cargo_bay"] + 1)
            if player.credits >= cost:
                player.credits -= cost
                player.ship_upgrades["cargo_bay"] += 1
                player.cargo_capacity += 10
                print(f"\n📦 Cargo bay upgraded! New capacity: {player.cargo_capacity}")
            else:
                print(f"\n💰 Need {cost:,} credits for this upgrade!")
            input("Press Enter to continue...")
        
        elif choice == "3":
            cost = 800 * (player.ship_upgrades["fuel_tank"] + 1)
            if player.credits >= cost:
                player.credits -= cost
                player.ship_upgrades["fuel_tank"] += 1
                player.max_fuel += 20
                player.fuel = player.max_fuel
                print(f"\n⛽ Fuel tank upgraded! New capacity: {player.max_fuel}")
            else:
                print(f"\n💰 Need {cost:,} credits for this upgrade!")
            input("Press Enter to continue...")
    
    def calculate_net_worth(self, player):
        """Calculate total net worth including cargo value"""
        cargo_value = 0
        current_planet = self.planets[player.current_planet]
        
        for item, quantity in player.cargo.items():
            price = current_planet.market_prices.get(item, 0)
            cargo_value += quantity * price
        
        player.net_worth = player.credits + cargo_value
    
    def main_game_loop(self, player):
        while player.turns_remaining > 0:
            self.calculate_net_worth(player)
            self.display_player_status(player)
            
            print("What would you like to do?")
            print("1. View Market / Trade")
            print("2. Travel to Another Planet")
            print("3. Ship Services")
            print("4. View Galactic Map")
            print("5. Save and Quit")
            
            choice = input("\nEnter your choice: ")
            
            if choice == "1":
                self.trade_menu(player)
            
            elif choice == "2":
                if player.fuel < 5:
                    print("\n⛽ Not enough fuel to travel anywhere!")
                    input("Press Enter to continue...")
                else:
                    self.travel_menu(player)
            
            elif choice == "3":
                self.ship_services(player)
            
            elif choice == "4":
                self.show_galactic_map()
            
            elif choice == "5":
                print("\n💾 Game saved. Safe travels, Captain!")
                break
            
            # Save progress after each action
            self.save_player(player)
            
            # Check for game over conditions
            if player.credits <= 0 and not player.cargo and player.fuel < 5:
                print("\n💸 GAME OVER: You're broke and stranded!")
                print(f"Final Net Worth: {player.net_worth:,} credits")
                input("Press Enter to continue...")
                break
        
        if player.turns_remaining <= 0:
            print("\n⏰ Your trading license has expired!")
            print(f"Final Net Worth: {player.net_worth:,} credits")
            if player.net_worth >= 10000:
                print("🎉 Congratulations! You're a successful trader!")
            elif player.net_worth >= 5000:
                print("👍 Not bad for a space trader!")
            else:
                print("📈 Keep practicing your trading skills!")
    
    def show_galactic_map(self):
        print("\n🗺️  GALACTIC MAP")
        print("-" * 60)
        for name, planet in self.planets.items():
            specialties = ", ".join(planet.specialties)
            print(f"{name:<20} Distance: {planet.distance_from_earth:<3} "
                  f"Danger: {planet.dangers}/10 Specialties: {specialties}")
        input("\nPress Enter to continue...")
    
    def run(self):
        self.display_banner()
        
        name = input("Enter your captain name: ").strip()
        if not name:
            name = "Anonymous"
        
        # Load existing player or create new one
        player = self.load_player(name)
        if player is None:
            player = Player(name)
            print(f"\n🚀 Welcome to the galaxy, Captain {name}!")
            print("You start with 2000 credits and 100 turns.")
            print("Buy low, sell high, and build your trading empire!")
        else:
            print(f"\n👋 Welcome back, Captain {name}!")
        
        input("\nPress Enter to begin trading...")
        
        self.main_game_loop(player)
        self.save_player(player)

if __name__ == "__main__":
    game = GalacticConquest()
    game.run()

