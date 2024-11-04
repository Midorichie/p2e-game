# game/config.py
from enum import Enum
from typing import Dict

class Rarity(Enum):
    COMMON = "COMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"

class GameConfig:
    STACKS_API_URL = "https://stacks-node-api.mainnet.stacks.co"
    GAME_TITLE = "Crypto Quest"
    INITIAL_PLAYER_BALANCE = 0
    
    # Enhanced reward system with rarity-based multipliers
    BASE_REWARDS = {
        "EASY": 100,    # Satoshis
        "MEDIUM": 250,
        "HARD": 500,
        "BOSS": 1000
    }
    
    RARITY_MULTIPLIERS = {
        Rarity.COMMON: 1,
        Rarity.RARE: 1.5,
        Rarity.EPIC: 2,
        Rarity.LEGENDARY: 3
    }
    
    # Daily rewards and limits
    DAILY_QUEST_LIMIT = 10
    DAILY_REWARD_BONUS = 1000  # Extra satoshis for completing daily quest limit

# game/models.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json

@dataclass
class Item:
    id: str
    name: str
    rarity: Rarity
    boost: float  # Reward multiplier boost
    durability: int = 100

@dataclass
class PlayerInventory:
    items: Dict[str, Item] = field(default_factory=dict)
    equipped_items: Dict[str, str] = field(default_factory=dict)

    def equip_item(self, item_id: str, slot: str) -> bool:
        if item_id in self.items and self.items[item_id].durability > 0:
            self.equipped_items[slot] = item_id
            return True
        return False

@dataclass
class Player:
    wallet_address: str
    username: str
    level: int = 1
    experience: int = 0
    balance: int = GameConfig.INITIAL_PLAYER_BALANCE
    completed_quests: List[str] = field(default_factory=list)
    inventory: PlayerInventory = field(default_factory=PlayerInventory)
    daily_quests_completed: int = 0
    last_quest_reset: datetime = field(default_factory=datetime.now)
    achievement_points: int = 0
    
    def to_json(self):
        return json.dumps({
            'wallet_address': self.wallet_address,
            'username': self.username,
            'level': self.level,
            'experience': self.experience,
            'balance': self.balance,
            'achievement_points': self.achievement_points
        })

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    points: int
    requirements: Dict[str, int]

# game/game_logic.py
from typing import Optional, Tuple
from datetime import datetime, timedelta
import random
from .models import Player, Quest, Achievement, Item, Rarity
from .blockchain import StacksBlockchain

class GameManager:
    def __init__(self):
        self.blockchain = StacksBlockchain()
        self.players: Dict[str, Player] = {}
        self.quests: Dict[str, Quest] = self._initialize_quests()
        self.achievements: Dict[str, Achievement] = self._initialize_achievements()
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0)

    def _check_daily_reset(self, player: Player):
        now = datetime.now()
        if (now - player.last_quest_reset).days >= 1:
            player.daily_quests_completed = 0
            player.last_quest_reset = now

    async def complete_quest(self, wallet_address: str, quest_id: str) -> Tuple[Optional[int], List[str]]:
        player = self.players.get(wallet_address)
        if not player:
            raise ValueError("Player not found")

        self._check_daily_reset(player)
        
        if player.daily_quests_completed >= GameConfig.DAILY_QUEST_LIMIT:
            raise ValueError("Daily quest limit reached")

        quest = self.quests.get(quest_id)
        if not quest:
            raise ValueError("Quest not found")

        # Calculate reward with bonuses
        base_reward = quest.reward
        multiplier = 1.0

        # Apply equipped item bonuses
        for item_id in player.inventory.equipped_items.values():
            item = player.inventory.items.get(item_id)
            if item and item.durability > 0:
                multiplier *= (1 + item.boost)
                item.durability -= 1

        # Apply rarity multiplier
        if random.random() < 0.1:  # 10% chance for rare reward
            multiplier *= GameConfig.RARITY_MULTIPLIERS[Rarity.RARE]

        final_reward = int(base_reward * multiplier)

        # Award experience and update player
        player.experience += quest.reward // 5
        player.completed_quests.append(quest_id)
        player.daily_quests_completed += 1

        # Check for level up
        if player.experience >= player.level * 1000:
            player.level += 1
            self._check_achievements(player)

        # Check for daily bonus
        earned_achievements = []
        if player.daily_quests_completed == GameConfig.DAILY_QUEST_LIMIT:
            final_reward += GameConfig.DAILY_REWARD_BONUS
            earned_achievements.append("DAILY_WARRIOR")

        # Send blockchain reward
        success = await self.blockchain.send_reward(wallet_address, final_reward)
        if success:
            return final_reward, earned_achievements
        return None, []

    def _check_achievements(self, player: Player) -> List[str]:
        earned = []
        for achievement in self.achievements.values():
            if (
                achievement.id not in player.completed_quests and
                all(
                    getattr(player, req, 0) >= value 
                    for req, value in achievement.requirements.items()
                )
            ):
                earned.append(achievement.id)
                player.achievement_points += achievement.points
                player.completed_quests.append(achievement.id)
        return earned

    async def mint_item(self, player_address: str, item_type: str) -> Optional[Item]:
        player = self.players.get(player_address)
        if not player:
            raise ValueError("Player not found")

        # Implement item minting logic with NFT integration
        rarity = self._calculate_item_rarity()
        item = Item(
            id=f"item_{len(player.inventory.items)}",
            name=f"{rarity.name} {item_type}",
            rarity=rarity,
            boost=GameConfig.RARITY_MULTIPLIERS[rarity] * 0.1
        )
        
        # Mint NFT on blockchain
        success = await self.blockchain.mint_nft(
            player_address,
            item.id,
            item.to_json()
        )
        
        if success:
            player.inventory.items[item.id] = item
            return item
        return None

    def _calculate_item_rarity(self) -> Rarity:
        roll = random.random()
        if roll < 0.01:
            return Rarity.LEGENDARY
        elif roll < 0.05:
            return Rarity.EPIC
        elif roll < 0.20:
            return Rarity.RARE
        return Rarity.COMMON