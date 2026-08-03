import unittest

from sprout import run_source
from sprout.ast_nodes import EnvironmentDeclaration, PlacementDeclaration
from sprout.errors import SproutError
from sprout.interpreter import Interpreter
from sprout.lexer import Lexer
from sprout.parser import Parser


def parse(source):
    return Parser(Lexer(source).lex()).parse()


def run_on(interpreter, source):
    return interpreter.run(parse(source))


class EnvironmentPlacementTests(unittest.TestCase):
    def error_message(self, source):
        with self.assertRaises(SproutError) as error:
            run_source(source)
        return error.exception.format()

    def run_program(self, source):
        interpreter = Interpreter()
        output = run_on(interpreter, source)
        self.assertEqual(output, "")
        return interpreter

    def placement_for(self, source):
        interpreter = self.run_program(source)
        self.assertEqual(len(interpreter.placements), 1)
        return interpreter.placements[0]

    def test_parser_reads_environment_and_place_declarations(self):
        program = parse(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "place Blob in Land\n"
        )
        self.assertIsInstance(program.statements[0], EnvironmentDeclaration)
        self.assertEqual(program.statements[0].name, "Land")
        self.assertEqual(program.statements[0].environment_type, "ground")
        self.assertIsInstance(program.statements[1], PlacementDeclaration)
        self.assertEqual(program.statements[1].agent_name, "Blob")
        self.assertEqual(program.statements[1].environment_name, "Land")

    def test_valid_ground_placement(self):
        placement = self.placement_for(
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "place Blob in Land\n"
        )
        self.assertEqual(placement.environment_type, "ground")
        self.assertEqual(placement.movement_preset, "movement.ground")
        self.assertTrue(placement.active_movement)

    def test_valid_water_placement(self):
        placement = self.placement_for(
            "agent Fish uses:\n"
            "    position.continuous\n"
            "    movement.water\n"
            "\n"
            "environment Lake:\n"
            "    type = water\n"
            "\n"
            "place Fish in Lake\n"
        )
        self.assertEqual(placement.environment_type, "water")
        self.assertEqual(placement.movement_preset, "movement.water")
        self.assertTrue(placement.active_movement)

    def test_valid_air_placement(self):
        interpreter = self.run_program(
            "agent Bird uses:\n"
            "    position.continuous\n"
            "    movement.air\n"
            "\n"
            "environment Sky:\n"
            "    type = air\n"
            "\n"
            "place Bird in Sky\n"
        )
        agent = interpreter.agents["Bird"]
        placement = interpreter.placements[0]
        self.assertIn("altitude", agent.fields)
        self.assertEqual(placement.environment_type, "air")
        self.assertEqual(placement.movement_preset, "movement.air")
        self.assertTrue(placement.active_movement)

    def test_amphibious_agent_in_ground(self):
        placement = self.placement_for(
            "agent Frog uses:\n"
            "    position.continuous\n"
            "    movement.amphibious\n"
            "\n"
            "environment Bank:\n"
            "    type = ground\n"
            "\n"
            "place Frog in Bank\n"
        )
        self.assertEqual(placement.environment_type, "ground")
        self.assertEqual(placement.movement_preset, "movement.amphibious")

    def test_amphibious_agent_in_water(self):
        placement = self.placement_for(
            "agent Frog uses:\n"
            "    position.continuous\n"
            "    movement.amphibious\n"
            "\n"
            "environment Pond:\n"
            "    type = water\n"
            "\n"
            "place Frog in Pond\n"
        )
        self.assertEqual(placement.environment_type, "water")
        self.assertEqual(placement.movement_preset, "movement.amphibious")

    def test_aerial_ground_agent_in_ground(self):
        placement = self.placement_for(
            "agent Hopper uses:\n"
            "    position.continuous\n"
            "    movement.aerial_ground\n"
            "\n"
            "environment Field:\n"
            "    type = ground\n"
            "\n"
            "place Hopper in Field\n"
        )
        self.assertEqual(placement.environment_type, "ground")
        self.assertEqual(placement.movement_preset, "movement.aerial_ground")
        self.assertTrue(placement.active_movement)

    def test_aerial_ground_agent_in_air(self):
        placement = self.placement_for(
            "agent Hopper uses:\n"
            "    position.continuous\n"
            "    movement.aerial_ground\n"
            "\n"
            "environment Breeze:\n"
            "    type = air\n"
            "\n"
            "place Hopper in Breeze\n"
        )
        self.assertEqual(placement.environment_type, "air")
        self.assertEqual(placement.movement_preset, "movement.aerial_ground")
        self.assertTrue(placement.active_movement)

    def test_invalid_ground_agent_in_air(self):
        message = self.error_message(
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "environment Sky:\n"
            "    type = air\n"
            "\n"
            "place Blob in Sky\n"
        )
        self.assertIn("Blob uses movement.ground and cannot be placed in an air environment.", message)

    def test_invalid_water_agent_on_ground(self):
        message = self.error_message(
            "agent Fish uses:\n"
            "    position.continuous\n"
            "    movement.water\n"
            "\n"
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "place Fish in Land\n"
        )
        self.assertIn("Fish uses movement.water and cannot be placed in a ground environment.", message)

    def test_passive_agent_placement(self):
        placement = self.placement_for(
            "agent Leaf uses:\n"
            "    position.continuous\n"
            "    movement.passive\n"
            "\n"
            "environment Sky:\n"
            "    type = air\n"
            "\n"
            "place Leaf in Sky\n"
        )
        self.assertEqual(placement.environment_type, "air")
        self.assertEqual(placement.movement_preset, "movement.passive")
        self.assertFalse(placement.active_movement)

    def test_movement_none_allows_stationary_placement(self):
        placement = self.placement_for(
            "agent Rock uses:\n"
            "    position.continuous\n"
            "    movement.none\n"
            "\n"
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "place Rock in Land\n"
        )
        self.assertEqual(placement.environment_type, "ground")
        self.assertEqual(placement.movement_preset, "movement.none")
        self.assertFalse(placement.active_movement)

    def test_invalid_environment_type(self):
        message = self.error_message(
            "environment Desert:\n"
            "    type = sand\n"
        )
        self.assertIn("Unknown environment type `sand`.", message)
        self.assertIn("ground, water, air", message)

    def test_unknown_agent(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "place Blob in Land\n"
        )
        self.assertIn("Cannot place unknown agent `Blob`.", message)

    def test_unknown_environment(self):
        message = self.error_message(
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "place Blob in Land\n"
        )
        self.assertIn("Cannot place `Blob` in unknown environment `Land`.", message)

    def test_duplicate_environment_names(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "environment Land:\n"
            "    type = water\n"
        )
        self.assertIn("Environment `Land` is already defined.", message)

    def test_duplicate_placements_are_allowed_as_separate_metadata(self):
        interpreter = self.run_program(
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "place Blob in Land\n"
            "place Blob in Land\n"
        )
        self.assertEqual(len(interpreter.placements), 2)


if __name__ == "__main__":
    unittest.main()
