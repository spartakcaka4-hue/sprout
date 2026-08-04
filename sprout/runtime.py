from __future__ import annotations

from dataclasses import dataclass, field
from math import floor, hypot

from .agent_presets import AgentDefinition, AgentPreset, WorldDefinition
from .builtins import NOTHING


COORDINATE_FIELDS = ("x", "y", "row", "column")


def clone_value(value: object) -> object:
    if value is NOTHING:
        return NOTHING
    if type(value) is list:
        return [clone_value(item) for item in value]
    return value


@dataclass(slots=True)
class WorldRuntime:
    definition: WorldDefinition
    terrain_layer: dict[object, object] = field(default_factory=dict)
    object_layer: dict[object, object] = field(default_factory=dict)
    agent_layer: dict[object, object] = field(default_factory=dict)
    agents: dict[int, "AgentInstance"] = field(default_factory=dict)
    spatial_bucket_size: float = 1.0
    spatial_buckets: dict[tuple[int, int], set[int]] = field(default_factory=dict)

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

    def spatial_bucket_key(self, x: float, y: float) -> tuple[int, int]:
        return (floor(x / self.spatial_bucket_size), floor(y / self.spatial_bucket_size))

    def add_agent(self, instance: "AgentInstance") -> None:
        self.agents[instance.runtime_id] = instance
        if self.definition.space_type == "grid":
            self.agent_layer[(int(instance.x), int(instance.y))] = instance.runtime_id
        else:
            self.agent_layer[instance.runtime_id] = (instance.x, instance.y)
            self.spatial_buckets.setdefault(
                self.spatial_bucket_key(instance.x, instance.y),
                set(),
            ).add(instance.runtime_id)

    def remove_agent_from_layer(self, instance: "AgentInstance") -> None:
        if self.definition.space_type == "grid":
            key = (int(instance.x), int(instance.y))
            if self.agent_layer.get(key) == instance.runtime_id:
                del self.agent_layer[key]
        else:
            self.agent_layer.pop(instance.runtime_id, None)
            key = self.spatial_bucket_key(instance.x, instance.y)
            bucket = self.spatial_buckets.get(key)
            if bucket is not None:
                bucket.discard(instance.runtime_id)
                if not bucket:
                    del self.spatial_buckets[key]

    def update_agent_position(self, instance: "AgentInstance", x: float, y: float) -> None:
        self.remove_agent_from_layer(instance)
        instance.set_position(x, y)
        if self.definition.space_type == "grid":
            self.agent_layer[(int(x), int(y))] = instance.runtime_id
        else:
            self.agent_layer[instance.runtime_id] = (x, y)
            self.spatial_buckets.setdefault(self.spatial_bucket_key(x, y), set()).add(instance.runtime_id)

    def active_agent_at(self, x: float, y: float, *, ignore_id: int | None = None) -> "AgentInstance | None":
        if self.definition.space_type != "grid":
            return None
        instance_id = self.agent_layer.get((int(x), int(y)))
        if instance_id is None or instance_id == ignore_id:
            return None
        instance = self.agents.get(instance_id)
        if instance is None or not instance.active:
            return None
        return instance

    def nearby_agents(self, x: float, y: float, radius: float) -> list["AgentInstance"]:
        if self.definition.space_type == "grid":
            return []
        radius_squared = radius * radius
        min_bucket_x = floor((x - radius) / self.spatial_bucket_size)
        max_bucket_x = floor((x + radius) / self.spatial_bucket_size)
        min_bucket_y = floor((y - radius) / self.spatial_bucket_size)
        max_bucket_y = floor((y + radius) / self.spatial_bucket_size)
        found: list[AgentInstance] = []
        for bucket_x in range(min_bucket_x, max_bucket_x + 1):
            for bucket_y in range(min_bucket_y, max_bucket_y + 1):
                for instance_id in self.spatial_buckets.get((bucket_x, bucket_y), ()):
                    instance = self.agents.get(instance_id)
                    if instance is None or not instance.active or instance.removed:
                        continue
                    dx = instance.x - x
                    dy = instance.y - y
                    if dx * dx + dy * dy <= radius_squared:
                        found.append(instance)
        return found


@dataclass(slots=True)
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
