import unittest

from sprout import run_source
from sprout.ast_nodes import WorldDeclaration, WorldPlacementDeclaration
from sprout.errors import SproutError
from sprout.interpreter import Interpreter
from sprout.lexer import Lexer
from sprout.parser import Parser


def parse(source):
    return Parser(Lexer(source).lex()).parse()


def run_on(interpreter, source):
    return interpreter.run(parse(source))


class WorldTests(unittest.TestCase):
    def error_message(self, source):
        with self.assertRaises(SproutError) as error:
            run_source(source)
        return error.exception.format()

    def run_program(self, source):
        interpreter = Interpreter()
        output = run_on(interpreter, source)
        self.assertEqual(output, "")
        return interpreter

    def world_for(self, source, name):
        interpreter = self.run_program(source)
        return interpreter.worlds[name]

    def world_placement_for(self, source):
        interpreter = self.run_program(source)
        self.assertEqual(len(interpreter.world_placements), 1)
        return interpreter.world_placements[0]

    def test_parser_reads_world_and_world_placement(self):
        program = parse(
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "place Blob in Meadow at 20, 35\n"
        )
        self.assertIsInstance(program.statements[0], WorldDeclaration)
        self.assertEqual(program.statements[0].name, "Meadow")
        self.assertEqual(program.statements[0].space_type, "continuous")
        self.assertEqual(program.statements[0].environment_name, "Land")
        self.assertIsInstance(program.statements[1], WorldPlacementDeclaration)
        self.assertEqual(program.statements[1].agent_name, "Blob")
        self.assertEqual(program.statements[1].world_name, "Meadow")

    def test_valid_continuous_world(self):
        world = self.world_for(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n",
            "Meadow",
        )
        self.assertEqual(world.width, 100)
        self.assertEqual(world.height, 80)
        self.assertEqual(world.space_type, "continuous")
        self.assertEqual(world.environment_name, "Land")
        self.assertEqual(world.environment_type, "ground")

    def test_valid_grid_world(self):
        world = self.world_for(
            "environment Ground:\n"
            "    type = ground\n"
            "\n"
            "world Board:\n"
            "    size = 20, 20\n"
            "    space = grid\n"
            "    environment = Ground\n",
            "Board",
        )
        self.assertEqual(world.width, 20)
        self.assertEqual(world.height, 20)
        self.assertEqual(world.space_type, "grid")

    def test_world_fields_may_be_in_different_order(self):
        world = self.world_for(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "world Meadow:\n"
            "    environment = Land\n"
            "    space = continuous\n"
            "    size = 100, 80\n",
            "Meadow",
        )
        self.assertEqual((world.width, world.height, world.space_type, world.environment_name), (100, 80, "continuous", "Land"))

    def test_world_names_do_not_become_variables(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "print(Meadow)\n"
        )
        self.assertIn("`Meadow` is not defined.", message)

    def test_duplicate_world_name(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "world Meadow:\n"
            "    size = 20, 20\n"
            "    space = grid\n"
            "    environment = Land\n"
        )
        self.assertIn("World `Meadow` is already defined.", message)

    def test_missing_world_fields(self):
        cases = [
            (
                "environment Land:\n"
                "    type = ground\n"
                "\n"
                "world Meadow:\n"
                "    space = continuous\n"
                "    environment = Land\n",
                "missing `size`",
            ),
            (
                "environment Land:\n"
                "    type = ground\n"
                "\n"
                "world Meadow:\n"
                "    size = 100, 80\n"
                "    environment = Land\n",
                "missing `space`",
            ),
            (
                "environment Land:\n"
                "    type = ground\n"
                "\n"
                "world Meadow:\n"
                "    size = 100, 80\n"
                "    space = continuous\n",
                "missing `environment`",
            ),
        ]
        for source, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.error_message(source))

    def test_duplicate_world_fields(self):
        cases = [
            (
                "size",
                "world Meadow:\n"
                "    size = 100, 80\n"
                "    size = 20, 20\n"
                "    space = continuous\n"
                "    environment = Land\n",
            ),
            (
                "space",
                "world Meadow:\n"
                "    size = 100, 80\n"
                "    space = continuous\n"
                "    space = grid\n"
                "    environment = Land\n",
            ),
            (
                "environment",
                "world Meadow:\n"
                "    size = 100, 80\n"
                "    space = continuous\n"
                "    environment = Land\n"
                "    environment = Lake\n",
            ),
        ]
        for field_name, source in cases:
            with self.subTest(field_name=field_name):
                self.assertIn(f"can only set `{field_name}` once", self.error_message(source))

    def test_unknown_world_field(self):
        message = self.error_message(
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "    color = green\n"
        )
        self.assertIn("Unknown world field `color`.", message)

    def test_invalid_world_sizes(self):
        cases = [
            ("size = 0, 10", "World width must be greater than 0."),
            ("size = 10, 0", "World height must be greater than 0."),
            ("size = -5, 10", "World width must be greater than 0."),
            ("size = 10.5, 20", "World width must be a whole number."),
            ('size = "large", 20', "World width must be a positive whole number"),
        ]
        for size_line, expected in cases:
            with self.subTest(size_line=size_line):
                message = self.error_message(
                    "environment Land:\n"
                    "    type = ground\n"
                    "\n"
                    "world Meadow:\n"
                    f"    {size_line}\n"
                    "    space = continuous\n"
                    "    environment = Land\n"
                )
                self.assertIn("Invalid world size.", message)
                self.assertIn(expected, message)

    def test_invalid_space_type(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = hex\n"
            "    environment = Land\n"
        )
        self.assertIn("Unknown world space type `hex`.", message)
        self.assertIn("grid, continuous", message)

    def test_unknown_environment_reference(self):
        message = self.error_message(
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
        )
        self.assertIn("World `Meadow` references unknown environment `Land`.", message)

    def test_nested_world_declaration(self):
        message = self.error_message(
            "if true:\n"
            "    world Meadow:\n"
            "        size = 100, 80\n"
            "        space = continuous\n"
            "        environment = Land\n"
        )
        self.assertIn("World declarations are only allowed at the top level.", message)

    def test_empty_world_block(self):
        message = self.error_message("world Meadow:\n")
        self.assertIn("Expected an indented block after `world`.", message)
        message = self.error_message("world Meadow:\n    # empty\n")
        self.assertIn("Expected an indented block after `world`.", message)

    def test_malformed_world_metadata_syntax(self):
        cases = [
            ("world Meadow:\n    size 100, 80\n", "Expected `=` after `size`."),
            ("world Meadow:\n    size = 100 80\n", "Expected `,` between world width and height."),
            ("world Meadow:\n    space = \"wide\"\n", "Expected a world space type"),
            ("world Meadow:\n    environment = \"Land\"\n", "Expected an environment name"),
        ]
        for source, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.error_message(source))

    def test_ground_agent_in_ground_continuous_world(self):
        placement = self.world_placement_for(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "place Blob in Meadow at 20, 35\n"
        )
        self.assertEqual((placement.world_name, placement.x, placement.y), ("Meadow", 20.0, 35.0))
        self.assertEqual(placement.environment_type, "ground")
        self.assertEqual(placement.movement_preset, "movement.ground")
        self.assertEqual(placement.position_preset, "position.continuous")
        self.assertTrue(placement.active_movement)

    def test_water_agent_in_water_continuous_world(self):
        placement = self.world_placement_for(
            "environment Lake:\n"
            "    type = water\n"
            "\n"
            "agent Fish uses:\n"
            "    position.continuous\n"
            "    movement.water\n"
            "\n"
            "world Pond:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Lake\n"
            "\n"
            "place Fish in Pond at 20.5, 35.25\n"
        )
        self.assertEqual(placement.environment_type, "water")
        self.assertEqual((placement.x, placement.y), (20.5, 35.25))

    def test_air_agent_in_air_continuous_world(self):
        placement = self.world_placement_for(
            "environment Sky:\n"
            "    type = air\n"
            "\n"
            "agent Bird uses:\n"
            "    position.continuous\n"
            "    movement.air\n"
            "\n"
            "world Airspace:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Sky\n"
            "\n"
            "place Bird in Airspace at 20, 35\n"
        )
        self.assertEqual(placement.environment_type, "air")
        self.assertEqual(placement.movement_preset, "movement.air")

    def test_grid_agent_in_grid_world(self):
        placement = self.world_placement_for(
            "environment Ground:\n"
            "    type = ground\n"
            "\n"
            "agent Ant uses:\n"
            "    position.cell\n"
            "    movement.grid\n"
            "\n"
            "world Board:\n"
            "    size = 20, 20\n"
            "    space = grid\n"
            "    environment = Ground\n"
            "\n"
            "place Ant in Board at 4, 7\n"
        )
        self.assertEqual(placement.space_type, "grid")
        self.assertEqual((placement.x, placement.y), (4.0, 7.0))
        self.assertEqual(placement.position_preset, "position.cell")

    def test_passive_agent_world_placement(self):
        placement = self.world_placement_for(
            "environment Sky:\n"
            "    type = air\n"
            "\n"
            "agent Leaf uses:\n"
            "    position.continuous\n"
            "    movement.passive\n"
            "\n"
            "world Airspace:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Sky\n"
            "\n"
            "place Leaf in Airspace at 20, 35\n"
        )
        self.assertEqual(placement.movement_preset, "movement.passive")
        self.assertFalse(placement.active_movement)

    def test_movement_none_world_placement(self):
        placement = self.world_placement_for(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Rock uses:\n"
            "    position.none\n"
            "    movement.none\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "place Rock in Meadow at 20, 35\n"
        )
        self.assertEqual(placement.movement_preset, "movement.none")
        self.assertEqual(placement.position_preset, "position.none")
        self.assertFalse(placement.active_movement)

    def test_duplicate_world_placements_are_allowed(self):
        interpreter = self.run_program(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "place Blob in Meadow at 20, 35\n"
            "place Blob in Meadow at 20, 35\n"
        )
        self.assertEqual(len(interpreter.world_placements), 2)

    def test_unknown_agent_in_world_placement(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "place Blob in Meadow at 20, 35\n"
        )
        self.assertIn("Cannot place unknown agent `Blob`.", message)

    def test_unknown_world_in_world_placement(self):
        message = self.error_message(
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "place Blob in Meadow at 20, 35\n"
        )
        self.assertIn("Cannot place `Blob` in unknown world `Meadow`.", message)

    def test_world_coordinate_bounds(self):
        cases = [
            ("-1, 35", "x", "at least 0 and less than 100"),
            ("20, -1", "y", "at least 0 and less than 80"),
            ("100, 35", "x", "at least 0 and less than 100"),
            ("20, 80", "y", "at least 0 and less than 80"),
        ]
        for coordinates, axis, expected in cases:
            with self.subTest(coordinates=coordinates):
                message = self.error_message(
                    "environment Land:\n"
                    "    type = ground\n"
                    "\n"
                    "agent Blob uses:\n"
                    "    position.continuous\n"
                    "    movement.ground\n"
                    "\n"
                    "world Meadow:\n"
                    "    size = 100, 80\n"
                    "    space = continuous\n"
                    "    environment = Land\n"
                    "\n"
                    f"place Blob in Meadow at {coordinates}\n"
                )
                self.assertIn("World placement coordinate is out of bounds.", message)
                self.assertIn(f"`{axis}`", message)
                self.assertIn(expected, message)

    def test_decimal_coordinate_in_grid_world(self):
        message = self.error_message(
            "environment Ground:\n"
            "    type = ground\n"
            "\n"
            "agent Ant uses:\n"
            "    position.cell\n"
            "    movement.grid\n"
            "\n"
            "world Board:\n"
            "    size = 20, 20\n"
            "    space = grid\n"
            "    environment = Ground\n"
            "\n"
            "place Ant in Board at 4.5, 7\n"
        )
        self.assertIn("Grid world coordinates must be whole numbers.", message)

    def test_text_coordinate(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "place Blob in Meadow at \"x\", 7\n"
        )
        self.assertIn("Invalid world placement coordinate.", message)
        self.assertIn("Found: text", message)

    def test_movement_environment_mismatch_in_world(self):
        message = self.error_message(
            "environment Sky:\n"
            "    type = air\n"
            "\n"
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "world Airspace:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Sky\n"
            "\n"
            "place Blob in Airspace at 20, 35\n"
        )
        self.assertIn("Blob uses movement.ground and cannot be placed in an air environment.", message)

    def test_position_cell_in_continuous_world(self):
        message = self.error_message(
            "environment Land:\n"
            "    type = ground\n"
            "\n"
            "agent Ant uses:\n"
            "    position.cell\n"
            "    movement.ground\n"
            "\n"
            "world Meadow:\n"
            "    size = 100, 80\n"
            "    space = continuous\n"
            "    environment = Land\n"
            "\n"
            "place Ant in Meadow at 20, 35\n"
        )
        self.assertIn("Ant uses position.cell and cannot be placed in world `Meadow` with continuous space.", message)

    def test_position_continuous_in_grid_world(self):
        message = self.error_message(
            "environment Ground:\n"
            "    type = ground\n"
            "\n"
            "agent Blob uses:\n"
            "    position.continuous\n"
            "    movement.ground\n"
            "\n"
            "world Board:\n"
            "    size = 20, 20\n"
            "    space = grid\n"
            "    environment = Ground\n"
            "\n"
            "place Blob in Board at 4, 7\n"
        )
        self.assertIn("Blob uses position.continuous and cannot be placed in world `Board` with grid space.", message)


if __name__ == "__main__":
    unittest.main()
