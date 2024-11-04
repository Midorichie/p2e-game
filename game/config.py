# game/config.py
STACKS_API_URL = "https://stacks-node-api.mainnet.stacks.co"
GAME_TITLE = "Crypto Quest"
INITIAL_PLAYER_BALANCE = 0
REWARD_RATES = {
    "EASY": 100,    # Satoshis
    "MEDIUM": 250,
    "HARD": 500
}

# game/models.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Player:
    wallet_address: str
    username: str
    level: int = 1
    experience: int = 0
    balance: int = INITIAL_PLAYER_BALANCE
    completed_quests: List[str] = None

    def __post_init__(self):
        self.completed_quests = self.completed_quests or []

@dataclass
class Quest:
    id: str
    name: str
    difficulty: str
    reward: int
    requirements: Dict[str, int]

# game/blockchain.py
from typing import Dict
import requests
from .config import STACKS_API_URL

class StacksBlockchain:
    def __init__(self):
        self.api_url = STACKS_API_URL

    async def get_balance(self, address: str) -> int:
        response = requests.get(f"{self.api_url}/extended/v1/address/{address}/balances")
        return response.json().get("stx", {}).get("balance", 0)

    async def send_reward(self, player_address: str, amount: int) -> bool:
        # Implement actual reward distribution logic here
        pass

# game/game_logic.py
from typing import Optional
from .models import Player, Quest
from .blockchain import StacksBlockchain

class GameManager:
    def __init__(self):
        self.blockchain = StacksBlockchain()
        self.players: Dict[str, Player] = {}
        self.quests: Dict[str, Quest] = self._initialize_quests()

    def _initialize_quests(self) -> Dict[str, Quest]:
        return {
            "quest_1": Quest(
                id="quest_1",
                name="Crypto Warrior Training",
                difficulty="EASY",
                reward=REWARD_RATES["EASY"],
                requirements={"level": 1}
            ),
            "quest_2": Quest(
                id="quest_2",
                name="Digital Asset Defense",
                difficulty="MEDIUM",
                reward=REWARD_RATES["MEDIUM"],
                requirements={"level": 2}
            )
        }

    async def register_player(self, wallet_address: str, username: str) -> Player:
        if wallet_address in self.players:
            raise ValueError("Player already registered")
        
        player = Player(wallet_address=wallet_address, username=username)
        self.players[wallet_address] = player
        return player

    async def complete_quest(self, wallet_address: str, quest_id: str) -> Optional[int]:
        player = self.players.get(wallet_address)
        if not player:
            raise ValueError("Player not found")

        quest = self.quests.get(quest_id)
        if not quest:
            raise ValueError("Quest not found")

        if quest_id in player.completed_quests:
            raise ValueError("Quest already completed")

        if player.level < quest.requirements["level"]:
            raise ValueError("Level requirement not met")

        # Award experience and reward
        player.experience += quest.reward // 10
        player.completed_quests.append(quest_id)
        
        # Level up logic
        if player.experience >= player.level * 1000:
            player.level += 1

        # Send blockchain reward
        success = await self.blockchain.send_reward(wallet_address, quest.reward)
        if success:
            return quest.reward
        return None