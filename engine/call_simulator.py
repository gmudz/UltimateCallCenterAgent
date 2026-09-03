"""
Call Simulator - Demo mode for streaming pre-scripted Arabic call scenarios.
"""
import json, os, asyncio
from typing import Dict, List, Callable, Optional

SCENARIOS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "demo_scenarios.json")

class CallSimulator:
    def __init__(self):
        self.scenarios: List[Dict] = []
        self.current_scenario: Optional[Dict] = None
        self.is_running = False
        self.current_index = 0
        self._load_scenarios()

    def _load_scenarios(self):
        try:
            with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.scenarios = data.get("scenarios", [])
        except Exception as e:
            print(f"Error loading scenarios: {e}")
            self.scenarios = []

    def get_scenarios_list(self) -> List[Dict]:
        return [{"id": s["id"], "client_name": s["client_name"], "client_type": s["client_type"],
                 "dialect": s["client_dialect"], "description": s["description"]} for s in self.scenarios]

    def select_scenario(self, scenario_id: str) -> Optional[Dict]:
        for s in self.scenarios:
            if s["id"] == scenario_id:
                self.current_scenario = s
                self.current_index = 0
                return s
        return None

    async def stream_scenario(self, scenario_id: str, callback: Callable, delay_multiplier: float = 1.0):
        scenario = self.select_scenario(scenario_id)
        if not scenario:
            return
        self.is_running = True
        self.current_index = 0
        segments = scenario["segments"]
        for i, segment in enumerate(segments):
            if not self.is_running:
                break
            self.current_index = i
            delay = 3.0 * delay_multiplier
            if i > 0:
                time_diff = segment["timestamp"] - segments[i-1]["timestamp"]
                delay = max(1.5, min(time_diff, 6.0)) * delay_multiplier
            await asyncio.sleep(delay)
            await callback({
                "type": "transcript",
                "segment_index": i,
                "total_segments": len(segments),
                "speaker": segment["speaker"],
                "text": segment["text"],
                "timestamp": segment["timestamp"],
                "client_name": scenario["client_name"],
                "client_type": scenario["client_type"],
                "is_last": i == len(segments) - 1,
                "progress": round((i + 1) / len(segments) * 100, 1)
            })
        self.is_running = False
        await callback({"type": "call_ended", "client_name": scenario["client_name"], "total_segments": len(segments)})

    def stop(self):
        self.is_running = False

    def pause(self):
        self.is_running = False

    def get_status(self) -> Dict:
        return {"is_running": self.is_running, "current_scenario": self.current_scenario["id"] if self.current_scenario else None,
                "current_index": self.current_index, "total_scenarios": len(self.scenarios)}
