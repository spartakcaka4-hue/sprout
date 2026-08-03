# Examples

Each program below is available in `examples/` and is covered by automated
tests.

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

