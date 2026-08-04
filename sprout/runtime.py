from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot

from .agent_presets import AgentDefinition, AgentPreset, WorldDefinition
from .builtins import NOTHING


COORDINATE_FIELDS = ("x", "y", "row", "column")


def clone_value(value: object) -> object:
    if value is NOTHING:
        return NOTHING
    if type(value) is list:
        return [clone_value(item) for item in value]
    return value


@dataclass
class WorldRuntime:
    definition: WorldDefinition
    terrain_layer: dict[object, object] = field(default_factory=dict)
    object_layer: dict[object, object] = field(default_factory=dict)
    agent_layer: dict[object, object] = field(default_factory=dict)
    agents: dict[int, "AgentInstance"] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def width(self) -> int:
        return self.definition.width

    @property
    def height(self) -> int:
        return self.definition.height

    @property
    def space_type(self) -> str:
        return self.definition.space_type

    @property
    def environment_name(self) -> str:
        return self.definition.environment_name

    @property
    def environment_type(self) -> str:
        return self.definition.environment_type

    @property
    def line(self) -> int:
        return self.definition.line

    @property
    def column(self) -> int:
        return self.definition.column

    @property
    def sprout_type_name(self) -> str:
        return "world"

    @property
    def sprout_format_value(self) -> str:
        return f"<world {self.name}>"

    def occupancy_key(self, x: float, y: float) -> tuple[int, int]:
        return (int(x), int(y))

    def add_agent(self, instance: "AgentInstance") -> None:
        self.agents[instance.runtime_id] = instance
        if self.space_type == "grid":
            self.agent_layer[self.occupancy_key(instance.x, instance.y)] = instance.runtime_id
        else:
            self.agent_layer[instance.runtime_id] = (instance.x, instance.y)

    def remove_agent_from_layer(self, instance: "AgentInstance") -> None:
        if self.space_type == "grid":
            key = self.occupancy_key(instance.x, instance.y)
            if self.agent_layer.get(key) == instance.runtime_id:
                del self.agent_layer[key]
        else:
            self.agent_layer.pop(instance.runtime_id, None)

    def update_agent_position(self, instance: "AgentInstance", x: float, y: float) -> None:
        self.remove_agent_from_layer(instance)
        instance.set_position(x, y)
        if self.space_type == "grid":
            self.agent_layer[self.occupancy_key(x, y)] = instance.runtime_id
        else:
            self.agent_layer[instance.runtime_id] = (x, y)

    def active_agent_at(self, x: float, y: float, *, ignore_id: int | None = None) -> "AgentInstance | None":
        if self.space_type != "grid":
            return None
        instance_id = self.agent_layer.get(self.occupancy_key(x, y))
        if instance_id is None or instance_id == ignore_id:
            return None
        instance = self.agents.get(instance_id)
        if instance is None or not instance.active:
            return None
        return instance


@dataclass
class AgentInstance:
    runtime_id: int
    definition: AgentDefinition
    world: WorldRuntime
    x: float
    y: float
    fields: dict[str, object]
    movement_preset: AgentPreset
    position_preset: AgentPreset
    name: str | None = None
    active: bool = True
    removed: bool = False
    distance_moved_this_tick: float = 0.0

    @property
    def type_name(self) -> str:
        return self.definition.name

    @property
    def display_name(self) -> str:
        if self.name is not None:
            return self.name
        return f"{self.definition.name}#{self.runtime_id}"

    @property
    def error_name(self) -> str:
        return f"`{self.display_name}`"

    @property
    def sprout_type_name(self) -> str:
        return "agent instance"

    @property
    def sprout_format_value(self) -> str:
        return str(self)

    def set_position(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        if "x" in self.fields:
            self.fields["x"] = x
        if "y" in self.fields:
            self.fields["y"] = y
        if "column" in self.fields:
            self.fields["column"] = x
        if "row" in self.fields:
            self.fields["row"] = y

    def field_value(self, name: str) -> object:
        if name in self.fields:
            return self.fields[name]
        if name == "x":
            return self.x
        if name == "y":
            return self.y
        if name == "column":
            return self.x
        if name == "row":
            return self.y
        raise KeyError(name)

    def set_field_value(self, name: str, value: object) -> None:
        self.fields[name] = value

    def record_move(self, old_x: float, old_y: float) -> None:
        self.distance_moved_this_tick += hypot(self.x - old_x, self.y - old_y)

    def reset_tick_movement(self) -> None:
        self.distance_moved_this_tick = 0.0

    def __str__(self) -> str:
        status = "removed" if self.removed else "active"
        return f"<{status} {self.definition.name} {self.display_name}>"
