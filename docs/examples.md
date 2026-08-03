# Examples

The first programs below are available in `examples/` and are covered by
automated tests. The v0.3 snippets show metadata and tick-control syntax; they
do not demonstrate simulation behavior because v0.3 does not include live
agents, live world simulation, or movement calculations yet.

## hello_world.spr

```text
print("Hello, world!")
```

Output:

```text
Hello, world!
```

## scores.spr

```text
name = "Joel"
score = 10

if score >= 10:
    print("You win")
else:
    print("Keep trying")
```

Output:

```text
You win
```

## loops.spr

```text
repeat 3 as i:
    print("Lap", i)
```

Output:

```text
Lap 0
Lap 1
Lap 2
```

## lists.spr

```text
foods = ["pizza", "apple", "bread"]

for food in foods:
    print(food)

print(length(foods))
```

Output:

```text
pizza
apple
bread
3
```

## functions.spr

```text
func add(a, b):
    return a + b

result = add(2, 3)
print("Sum:", result)
```

Output:

```text
Sum: 5
```

## classify.spr

```text
func classify(score):
    if score >= 90:
        return "A"
    else if score >= 80:
        return "B"
    else:
        return "C"

scores = [95, 82, 61]

for s in scores:
    print(s, "->", classify(s))
```

Output:

```text
95 -> A
82 -> B
61 -> C
```

## exists.spr

```text
winner = nothing

if winner exists:
    print("Winner:", winner)
else:
    print("No winner yet")
```

Output:

```text
No winner yet
```

## world.spr

```text
environment Land:
    type = ground

agent Blob uses:
    position.continuous
    movement.ground
    biology.energy

world Meadow:
    size = 100, 80
    space = continuous
    environment = Land

place Blob in Meadow at 20, 35
```

Output: no output.

This example declares environment, agent, world, and world-placement metadata.
It does not spawn or render a Blob.

## v0.3 Tick Snippet

```text
tick.next(3)
print(tick.number)
```

Output:

```text
3
```

## v0.3 Agent Preset Snippet

```text
agent Blob uses:
    position.continuous
    movement.ground
    biology.energy

    hunger = 5
    vision = 10
```

This declares agent metadata. It injects fields from the selected presets and
adds the custom `hunger` and `vision` fields. It does not spawn a Blob.

## v0.3 Environment Placement Snippet

```text
agent Fish uses:
    position.continuous
    movement.water
    biology.energy

environment Lake:
    type = water

place Fish in Lake
```

This stores placement metadata after validating that `movement.water` is
allowed in a `water` environment.

## v0.3 World Placement Snippet

```text
environment Ground:
    type = ground

agent Ant uses:
    position.cell
    movement.grid

world Board:
    size = 20, 20
    space = grid
    environment = Ground

place Ant in Board at 4, 7
```

This stores world-placement metadata after validating the agent, world,
coordinates, movement/environment compatibility, and position/grid
compatibility.
