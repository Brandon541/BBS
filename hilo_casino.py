#!/usr/bin/env python3
"""
Hi-Lo Casino - BBS Door Game
A classic number guessing game with betting mechanics
"""

import random
import json
import os
import time

class Player:
    def __init__(self, name):
        self.name = name
        self.credits = 1000
        self.games_played = 0
        self.games_won = 0
        self.total_winnings = 0
        self.biggest_win = 0
        self.current_streak = 0
        self.best_streak = 0
        self.turns_today = 20

    def to_dict(self):
        return self.__dict__
    
    @classmethod
    def from_dict(cls, data):
        player = cls(data['name'])
        for key, value in data.items():
            setattr(player, key, value)
        return player

class HiLoCasino:
    def __init__(self):
        self.player_data_dir = "../player_data"
        self.ensure_data_dir()
        self.min_number = 1
        self.max_number = 100
        
    def ensure_data_dir(self):
        if not os.path.exists(self.player_data_dir):
            os.makedirs(self.player_data_dir)
    
    def save_player(self, player):
        filename = os.path.join(self.player_data_dir, f"{player.name.lower()}_hilo.json")
        with open(filename, 'w') as f:
            json.dump(player.to_dict(), f, indent=2)
    
    def load_player(self, name):
        filename = os.path.join(self.player_data_dir, f"{name.lower()}_hilo.json")
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                return Player.from_dict(data)
        return None
    
    def display_banner(self):
        print("\n" + "="*60)
        print("              HI-LO CASINO - NUMBER GUESSING")
        print("              Guess the number, win big!")
        print("="*60)
        print()
    
    def display_player_stats(self, player):
        win_rate = (player.games_won / max(1, player.games_played)) * 100
        print(f"\n{'='*45}")
        print(f"PLAYER: {player.name}")
        print(f"Credits: {player.credits:,}")
        print(f"Games Played: {player.games_played} | Won: {player.games_won} ({win_rate:.1f}%)")
        print(f"Total Winnings: {player.total_winnings:,}")
        print(f"Biggest Win: {player.biggest_win:,}")
        print(f"Current Streak: {player.current_streak} | Best: {player.best_streak}")
        print(f"Turns Remaining Today: {player.turns_today}")
        print(f"{'='*45}\n")
    
    def get_difficulty_settings(self):
        """Let player choose difficulty for different payouts"""
        print("\n🎯 Choose your challenge:")
        print("1. Easy (1-50) - 2x payout")
        print("2. Medium (1-100) - 3x payout")
        print("3. Hard (1-200) - 5x payout")
        print("4. Expert (1-500) - 10x payout")
        print("5. Insane (1-1000) - 20x payout")
        
        difficulties = {
            "1": (50, 2, "Easy"),
            "2": (100, 3, "Medium"),
            "3": (200, 5, "Hard"),
            "4": (500, 10, "Expert"),
            "5": (1000, 20, "Insane")
        }
        
        choice = input("\nSelect difficulty (1-5): ")
        if choice in difficulties:
            max_num, multiplier, name = difficulties[choice]
            return max_num, multiplier, name
        else:
            return 100, 3, "Medium"  # Default
    
    def play_round(self, player):
        if player.credits <= 0:
            print("\n💸 You're out of credits! Game over!")
            return False
        
        if player.turns_today <= 0:
            print("\n⏰ You've used all your turns for today!")
            return False
        
        # Get difficulty and bet
        max_number, multiplier, difficulty_name = self.get_difficulty_settings()
        
        print(f"\n💰 You have {player.credits:,} credits")
        print(f"Difficulty: {difficulty_name} (1-{max_number}) - {multiplier}x payout")
        
        try:
            bet = int(input("How much do you want to bet? "))
            if bet <= 0 or bet > player.credits:
                print("\n❌ Invalid bet amount!")
                return True
        except ValueError:
            print("\n❌ Please enter a valid number!")
            return True
        
        # Generate secret number
        secret_number = random.randint(1, max_number)
        guesses_allowed = max(3, int(max_number ** 0.5))  # Scale guesses with difficulty
        
        print(f"\n🎲 I'm thinking of a number between 1 and {max_number}")
        print(f"You have {guesses_allowed} guesses to find it!")
        print(f"Bet: {bet:,} credits | Potential win: {bet * multiplier:,} credits")
        
        player.credits -= bet
        player.games_played += 1
        player.turns_today -= 1
        
        # Guessing loop
        for guess_num in range(1, guesses_allowed + 1):
            print(f"\n--- Guess {guess_num}/{guesses_allowed} ---")
            
            try:
                guess = int(input(f"Your guess (1-{max_number}): "))
                if guess < 1 or guess > max_number:
                    print(f"❌ Please guess between 1 and {max_number}!")
                    continue
            except ValueError:
                print("❌ Please enter a valid number!")
                continue
            
            if guess == secret_number:
                # WIN!
                bonus_multiplier = (guesses_allowed - guess_num + 1) / guesses_allowed
                winnings = int(bet * multiplier * bonus_multiplier)
                player.credits += winnings
                player.games_won += 1
                player.total_winnings += winnings
                player.current_streak += 1
                
                if winnings > player.biggest_win:
                    player.biggest_win = winnings
                
                if player.current_streak > player.best_streak:
                    player.best_streak = player.current_streak
                
                print(f"\n🎉 WINNER! The number was {secret_number}!")
                print(f"💰 You won {winnings:,} credits!")
                
                if guess_num == 1:
                    print("🎆 FIRST GUESS BONUS!")
                elif guess_num <= guesses_allowed // 2:
                    print("⭐ Quick guess bonus!")
                
                if player.current_streak > 1:
                    print(f"🔥 Winning streak: {player.current_streak}!")
                
                return True
            
            elif guess < secret_number:
                distance = secret_number - guess
                if distance <= max_number // 20:  # Very close
                    print("🔥 TOO LOW - but you're very close!")
                elif distance <= max_number // 10:  # Close
                    print("🔥 TOO LOW - getting warmer!")
                else:
                    print("❄️ TOO LOW - way off!")
            
            else:  # guess > secret_number
                distance = guess - secret_number
                if distance <= max_number // 20:  # Very close
                    print("🔥 TOO HIGH - but you're very close!")
                elif distance <= max_number // 10:  # Close
                    print("🔥 TOO HIGH - getting warmer!")
                else:
                    print("❄️ TOO HIGH - way off!")
        
        # Lost all guesses
        print(f"\n😵 Out of guesses! The number was {secret_number}")
        print(f"💸 You lost {bet:,} credits")
        player.current_streak = 0
        
        return True
    
    def show_leaderboard(self):
        """Show top players (simplified version)"""
        print("\n🏆 HALL OF FAME - Top Players")
        print("-" * 50)
        print("(In a real BBS, this would show all players)")
        print("Your goal: Build the highest net worth!")
        print("-" * 50)
        input("\nPress Enter to continue...")
    
    def buy_credits(self, player):
        """Allow player to buy more credits (limited per day)"""
        print("\n🏦 CREDIT EXCHANGE")
        print("Exchange your reputation for credits!")
        print(f"Current credits: {player.credits:,}")
        
        if player.games_won < 5:
            print("\n❌ You need to win at least 5 games before using the exchange!")
            input("Press Enter to continue...")
            return
        
        max_purchase = min(500, player.games_won * 10)
        print(f"Maximum you can buy today: {max_purchase} credits")
        
        try:
            amount = int(input("How many credits to buy (free once per day): "))
            if 1 <= amount <= max_purchase:
                player.credits += amount
                print(f"\n💰 Added {amount:,} credits to your account!")
            else:
                print("\n❌ Invalid amount!")
        except ValueError:
            print("\n❌ Please enter a valid number!")
        
        input("Press Enter to continue...")
    
    def main_game_loop(self, player):
        while True:
            self.display_player_stats(player)
            
            print("What would you like to do?")
            print("1. Play Hi-Lo")
            print("2. View Statistics")
            print("3. Hall of Fame")
            print("4. Credit Exchange")
            print("5. Game Rules")
            print("6. Quit Game")
            
            choice = input("\nEnter your choice: ")
            
            if choice == "1":
                if not self.play_round(player):
                    break
                input("\nPress Enter to continue...")
            
            elif choice == "2":
                self.show_detailed_stats(player)
            
            elif choice == "3":
                self.show_leaderboard()
            
            elif choice == "4":
                self.buy_credits(player)
            
            elif choice == "5":
                self.show_rules()
            
            elif choice == "6":
                print("\n👋 Thanks for playing Hi-Lo Casino!")
                print("Your progress has been saved.")
                break
            
            # Save progress after each action
            self.save_player(player)
    
    def show_detailed_stats(self, player):
        print("\n📈 DETAILED STATISTICS")
        print("-" * 40)
        
        if player.games_played > 0:
            win_rate = (player.games_won / player.games_played) * 100
            avg_winnings = player.total_winnings / player.games_played
            print(f"Win Rate: {win_rate:.1f}%")
            print(f"Average Winnings per Game: {avg_winnings:.0f} credits")
            
            if player.total_winnings > 0:
                print(f"Return on Investment: {(player.total_winnings / (player.games_played * 100)):.1f}x")
        else:
            print("No games played yet!")
        
        print(f"\nStreak Information:")
        print(f"Current Streak: {player.current_streak}")
        print(f"Best Streak Ever: {player.best_streak}")
        
        input("\nPress Enter to continue...")
    
    def show_rules(self):
        print("\n📜 GAME RULES")
        print("-" * 40)
        print("1. Choose your difficulty level (affects payout multiplier)")
        print("2. Place your bet (can't exceed your credits)")
        print("3. Guess the secret number within allowed attempts")
        print("4. Get hints: 'TOO HIGH' or 'TOO LOW'")
        print("5. Win credits based on difficulty and speed")
        print("\nDifficulty Levels:")
        print("• Easy (1-50): 2x payout, 7 guesses")
        print("• Medium (1-100): 3x payout, 10 guesses")
        print("• Hard (1-200): 5x payout, 14 guesses")
        print("• Expert (1-500): 10x payout, 22 guesses")
        print("• Insane (1-1000): 20x payout, 31 guesses")
        print("\nBonus: Faster guesses = higher payouts!")
        input("\nPress Enter to continue...")
    
    def run(self):
        self.display_banner()
        
        name = input("Enter your player name: ").strip()
        if not name:
            name = "Anonymous"
        
        # Load existing player or create new one
        player = self.load_player(name)
        if player is None:
            player = Player(name)
            print(f"\n🎉 Welcome to Hi-Lo Casino, {name}!")
            print("You start with 1,000 credits and 20 turns per day.")
            print("Guess numbers, win big, and climb the leaderboard!")
        else:
            print(f"\n👋 Welcome back, {name}!")
            # Reset daily turns (in a real BBS, this would be date-based)
            if player.turns_today <= 0:
                player.turns_today = 20
                print("Your daily turns have been restored!")
        
        input("\nPress Enter to enter the casino...")
        
        self.main_game_loop(player)
        self.save_player(player)

if __name__ == "__main__":
    game = HiLoCasino()
    game.run()

