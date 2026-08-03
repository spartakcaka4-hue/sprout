from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_ENVIRONMENT_TYPES = ("ground", "water", "air")
SUPPORTED_WORLD_SPACE_TYPES = ("grid", "continuous")


@dataclass(frozen=True)
class AgentPreset:
    category: str
    name: str
    fields: tuple[str, ...]
    allowed_environments: tuple[str, ...] = ()
    can_move_actively: bool = False
    description: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.category}.{self.name}"


@dataclass(frozen=True)
class AgentFieldDefinition:
    name: str
    source: str
    preset: str | None
    default: object | None
    has_default: bool


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    selected_presets: dict[str, AgentPreset]
    fields: dict[str, AgentFieldDefinition]
    line: int
    column: int


@dataclass(frozen=True)
class EnvironmentDefinition:
    name: str
    environment_type: str
    line: int
    column: int


@dataclass(frozen=True)
class PlacementDefinition:
    agent_name: str
    environment_name: str
    environment_type: str
    movement_preset: str
    active_movement: bool
    line: int
    column: int


@dataclass(frozen=True)
class WorldDefinition:
    name: str
    width: int
    height: int
    space_type: str
    environment_name: str
    environment_type: str
    line: int
    column: int


@dataclass(frozen=True)
class WorldPlacementDefinition:
    agent_name: str
    world_name: str
    x: float
    y: float
    space_type: str
    environment_name: str
    environment_type: str
    movement_preset: str
    allowed_environments: tuple[str, ...]
    active_movement: bool
    position_preset: str
    line: int
    column: int


PRESET_GROUPS: dict[str, dict[str, AgentPreset]] = {
    "position": {
        "none": AgentPreset("position", "none", ()),
        "basic": AgentPreset("position", "basic", ("x", "y")),
        "cell": AgentPreset("position", "cell", ("row", "column")),
        "continuous": AgentPreset("position", "continuous", ("x", "y")),
    },
    "movement": {
        "none": AgentPreset(
            "movement",
            "none",
            (),
            SUPPORTED_ENVIRONMENT_TYPES,
            False,
            "Cannot initiate movement; may be associated with an environment as stationary metadata.",
        ),
        "directional": AgentPreset(
            "movement",
            "directional",
            ("speed", "direction"),
            SUPPORTED_ENVIRONMENT_TYPES,
            True,
            "Legacy generic directional movement metadata.",
        ),
        "velocity": AgentPreset(
            "movement",
            "velocity",
            ("velocity_x", "velocity_y"),
            SUPPORTED_ENVIRONMENT_TYPES,
            True,
            "Legacy generic velocity movement metadata.",
        ),
        "grid": AgentPreset(
            "movement",
            "grid",
            ("grid_x", "grid_y"),
            SUPPORTED_ENVIRONMENT_TYPES,
            True,
            "Legacy generic grid movement metadata.",
        ),
        "ground": AgentPreset(
            "movement",
            "ground",
            ("speed", "direction"),
            ("ground",),
            True,
            "Can actively move in ground environments.",
        ),
        "water": AgentPreset(
            "movement",
            "water",
            ("speed", "direction"),
            ("water",),
            True,
            "Can actively move in water environments.",
        ),
        "air": AgentPreset(
            "movement",
            "air",
            ("speed", "direction", "altitude"),
            ("air",),
            True,
            "Can actively move in air environments.",
        ),
        "amphibious": AgentPreset(
            "movement",
            "amphibious",
            ("speed", "direction"),
            ("ground", "water"),
            True,
            "Can actively move in ground and water environments.",
        ),
        "aerial_ground": AgentPreset(
            "movement",
            "aerial_ground",
            ("speed", "direction", "altitude"),
            ("ground", "air"),
            True,
            "Can actively move in ground and air environments.",
        ),
        "passive": AgentPreset(
            "movement",
            "passive",
            ("direction",),
            SUPPORTED_ENVIRONMENT_TYPES,
            False,
            "Cannot initiate movement; may later be moved by external forces.",
        ),
    },
    "biology": {
        "none": AgentPreset("biology", "none", ()),
        "energy": AgentPreset("biology", "energy", ("energy", "alive")),
        "health": AgentPreset("biology", "health", ("health", "max_health", "alive")),
        "lifecycle": AgentPreset("biology", "lifecycle", ("age", "lifespan", "alive")),
    },
}
