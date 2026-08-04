import unittest

from sprout import run_source
from sprout.errors import SproutError


class RuntimeTests(unittest.TestCase):
    def error_message(self, source):
        with self.assertRaises(SproutError) as error:
            run_source(source)
        return error.exception.format()

    def test_goal_program_runs_end_to_end(self):
        self.assertEqual(
            run_source(
                "environment Land:\n"
                "    type = ground\n"
                "\n"
                "agent Banana uses:\n"
                "    position.cell\n"
                "    movement.ground\n"
                "    biology.energy\n"
                "\n"
                "    every tick:\n"
                "        energy = energy - 1\n"
                "        move self by 1, 0\n"
                "\n"
                "        if energy <= 0:\n"
                "            remove self\n"
                "\n"
                "world Kitchen:\n"
                "    size = 10, 10\n"
                "    space = grid\n"
                "    environment = Land\n"
                "\n"
                "spawn Banana as bob in Kitchen at 0, 4:\n"
                "    energy = 3\n"
                "\n"
                "tick.next(3)\n"
                "\n"
                "print(bob exists)\n"
            ),
            "false\n",
        )

    def test_instances_keep_independent_field_state(self):
        self.assertEqual(
            run_source(
                "environment Land:\n"
                "    type = ground\n"
                "\n"
                "agent Seed uses:\n"
                "    position.cell\n"
                "    movement.none\n"
                "    biology.energy\n"
                "\n"
                "    every tick:\n"
                "        energy = energy - 1\n"
                "\n"
                "world Plot:\n"
                "    size = 5, 5\n"
                "    space = grid\n"
                "    environment = Land\n"
                "\n"
                "spawn Seed as first in Plot at 0, 0:\n"
                "    energy = 5\n"
                "spawn Seed as second in Plot at 1, 0\n"
                "tick.next()\n"
                "print(first.energy, second.energy)\n"
            ),
            "4 99\n",
        )

    def test_spawn_override_validation(self):
        base = (
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Seed uses:\n"
            "    position.cell\n"
            "    movement.none\n"
            "    biology.energy\n"
            "\n"
            "world Plot:\n"
            "    size = 5, 5\n"
            "    space = grid\n"
            "    environment = Land\n"
            "\n"
        )
        duplicate = self.error_message(
            base
            + "spawn Seed as first in Plot at 0, 0:\n"
            "    energy = 5\n"
            "    energy = 6\n"
        )
        self.assertIn("overrides field `energy` more than once", duplicate)

        unknown = self.error_message(
            base
            + "spawn Seed as first in Plot at 0, 0:\n"
            "    vision = 6\n"
        )
        self.assertIn("has no field `vision`", unknown)

        coordinate = self.error_message(
            base
            + "spawn Seed as first in Plot at 0, 0:\n"
            "    row = 1\n"
        )
        self.assertIn("cannot override position field `row`", coordinate)

    def test_out_of_bounds_movement_is_rejected(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Walker uses:\n"
            "    position.cell\n"
            "    movement.ground\n"
            "\n"
            "    every tick:\n"
            "        move self by -1, 0\n"
            "\n"
            "world Board:\n"
            "    size = 5, 5\n"
            "    space = grid\n"
            "    environment = Land\n"
            "\n"
            "spawn Walker as walker in Board at 0, 0\n"
            "tick.next()\n"
        )
        self.assertIn("outside world `Board`", message)
        self.assertIn("Target position: (-1, 0).", message)

    def test_grid_occupancy_is_rejected(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Walker uses:\n"
            "    position.cell\n"
            "    movement.ground\n"
            "\n"
            "    every tick:\n"
            "        move self by 1, 0\n"
            "\n"
            "world Board:\n"
            "    size = 5, 5\n"
            "    space = grid\n"
            "    environment = Land\n"
            "\n"
            "spawn Walker as first in Board at 0, 0\n"
            "spawn Walker as second in Board at 1, 0\n"
            "tick.next()\n"
        )
        self.assertIn("would collide", message)
        self.assertIn("occupied by `second`", message)

    def test_passive_and_none_agents_cannot_move_themselves(self):
        for movement_preset in ("movement.passive", "movement.none"):
            with self.subTest(movement_preset=movement_preset):
                message = self.error_message(
                    "environment Land:\n"
                    "    type = ground\n"
                    "\n"
                    "agent Leaf uses:\n"
                    "    position.cell\n"
                    f"    {movement_preset}\n"
                    "\n"
                    "    every tick:\n"
                    "        move self by 1, 0\n"
                    "\n"
                    "world Board:\n"
                    "    size = 5, 5\n"
                    "    space = grid\n"
                    "    environment = Land\n"
                    "\n"
                    "spawn Leaf as leaf in Board at 0, 0\n"
                    "tick.next()\n"
                )
                self.assertIn(movement_preset, message)
                self.assertIn("cannot move", message)

    def test_mid_tick_spawn_waits_until_next_tick_and_removal_stops_updates(self):
        self.assertEqual(
            run_source(
                "environment Land:\n"
                "    type = ground\n"
                "\n"
                "agent Child uses:\n"
                "    position.cell\n"
                "    movement.none\n"
                "    biology.energy\n"
                "\n"
                "    every tick:\n"
                "        energy = energy - 1\n"
                "\n"
                "agent Spawner uses:\n"
                "    position.cell\n"
                "    movement.none\n"
                "    biology.energy\n"
                "\n"
                "    every tick:\n"
                "        spawn Child as baby in Plot at 1, 0:\n"
                "            energy = 10\n"
                "        remove self\n"
                "        energy = 999\n"
                "\n"
                "world Plot:\n"
                "    size = 5, 5\n"
                "    space = grid\n"
                "    environment = Land\n"
                "\n"
                "spawn Spawner as parent in Plot at 0, 0\n"
                "tick.next()\n"
                "print(parent exists, baby.energy)\n"
                "tick.next()\n"
                "print(baby.energy)\n"
            ),
            "false 10\n9\n",
        )

    def test_removed_instance_field_access_errors(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Seed uses:\n"
            "    position.cell\n"
            "    movement.none\n"
            "    biology.energy\n"
            "\n"
            "world Plot:\n"
            "    size = 5, 5\n"
            "    space = grid\n"
            "    environment = Land\n"
            "\n"
            "spawn Seed as seed in Plot at 0, 0\n"
            "remove seed\n"
            "print(seed.energy)\n"
        )
        self.assertIn("Cannot read `energy` from removed agent instance `seed`.", message)
        self.assertIn("type `Seed`", message)
        self.assertIn("world `Plot`", message)

    def test_spawn_order_updates_are_sequential_and_live(self):
        self.assertEqual(
            run_source(
                "environment Land:\n"
                "    type = ground\n"
                "\n"
                "agent Leader uses:\n"
                "    position.cell\n"
                "    movement.ground\n"
                "\n"
                "    every tick:\n"
                "        move self by 1, 0\n"
                "\n"
                "agent Watcher uses:\n"
                "    position.cell\n"
                "    movement.none\n"
                "    biology.energy\n"
                "\n"
                "    every tick:\n"
                "        if leader.column == 1:\n"
                "            energy = 7\n"
                "\n"
                "world Board:\n"
                "    size = 5, 5\n"
                "    space = grid\n"
                "    environment = Land\n"
                "\n"
                "spawn Leader as leader in Board at 0, 0\n"
                "spawn Watcher as watcher in Board at 2, 0\n"
                "tick.next()\n"
                "print(watcher.energy)\n"
            ),
            "7\n",
        )


if __name__ == "__main__":
    unittest.main()
