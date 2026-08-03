import unittest

from sprout import run_source
from sprout.ast_nodes import AgentDeclaration
from sprout.errors import SproutError
from sprout.interpreter import Interpreter
from sprout.lexer import Lexer
from sprout.parser import Parser


def parse(source):
    return Parser(Lexer(source).lex()).parse()


def run_on(interpreter, source):
    return interpreter.run(parse(source))


class AgentTests(unittest.TestCase):
    def error_message(self, source):
        with self.assertRaises(SproutError) as error:
            run_source(source)
        return error.exception.format()

    def test_parser_reads_agent_uses_declaration(self):
        program = parse(
            "agent Blob uses:\n"
            "    position.basic\n"
            "    movement.directional\n"
            "    biology.energy\n"
            "\n"
            "    hunger = 5\n"
        )
        statement = program.statements[0]
        self.assertIsInstance(statement, AgentDeclaration)
        self.assertEqual(statement.name, "Blob")
        self.assertTrue(statement.uses_presets)
        self.assertEqual(
            [(preset.category, preset.preset) for preset in statement.presets],
            [("position", "basic"), ("movement", "directional"), ("biology", "energy")],
        )
        self.assertEqual([field.name for field in statement.fields], ["hunger"])

    def test_valid_preset_loading_stores_agent_metadata(self):
        interpreter = Interpreter()
        output = run_on(
            interpreter,
            "agent Blob uses:\n"
            "    position.basic\n"
            "    movement.directional\n"
            "    biology.energy\n",
        )
        self.assertEqual(output, "")
        agent = interpreter.agents["Blob"]
        self.assertEqual(
            [preset.full_name for preset in agent.selected_presets.values()],
            ["position.basic", "movement.directional", "biology.energy"],
        )
        self.assertEqual(list(agent.fields), ["x", "y", "speed", "direction", "energy", "alive"])
        self.assertFalse(agent.fields["x"].has_default)
        self.assertEqual(agent.fields["x"].preset, "position.basic")

    def test_custom_variables_coexist_with_builtin_fields(self):
        interpreter = Interpreter()
        run_on(
            interpreter,
            "agent Blob uses:\n"
            "    position.basic\n"
            "    movement.directional\n"
            "    biology.energy\n"
            "\n"
            "    hunger = 5\n"
            "    vision = 10\n",
        )
        agent = interpreter.agents["Blob"]
        self.assertEqual(list(agent.fields), ["x", "y", "speed", "direction", "energy", "alive", "hunger", "vision"])
        self.assertEqual(agent.fields["hunger"].source, "custom")
        self.assertTrue(agent.fields["hunger"].has_default)
        self.assertEqual(agent.fields["hunger"].default, 5.0)
        self.assertEqual(agent.fields["vision"].default, 10.0)

    def test_agent_without_uses_allows_custom_variables(self):
        interpreter = Interpreter()
        run_on(interpreter, "agent Note:\n    label = \"seed\"\n")
        agent = interpreter.agents["Note"]
        self.assertEqual(agent.selected_presets, {})
        self.assertEqual(list(agent.fields), ["label"])
        self.assertEqual(agent.fields["label"].default, "seed")

    def test_duplicate_preset_categories_error(self):
        message = self.error_message(
            "agent Blob uses:\n"
            "    position.basic\n"
            "    position.cell\n"
        )
        self.assertIn("more than one `position` preset", message)
        self.assertIn("`position.basic` was already selected", message)

    def test_duplicate_builtin_and_custom_fields_error(self):
        message = self.error_message(
            "agent Blob uses:\n"
            "    biology.energy\n"
            "\n"
            "    energy = 5\n"
        )
        self.assertIn("Field `energy` already exists", message)
        self.assertIn("`biology.energy`", message)

    def test_duplicate_custom_fields_error(self):
        message = self.error_message(
            "agent Blob:\n"
            "    hunger = 5\n"
            "    hunger = 10\n"
        )
        self.assertIn("Field `hunger` already exists", message)
        self.assertIn("custom field", message)

    def test_invalid_preset_names_error(self):
        message = self.error_message(
            "agent Blob uses:\n"
            "    movement.fly\n"
        )
        self.assertIn("Unknown `movement` preset `fly`.", message)
        self.assertIn("directional", message)

    def test_invalid_categories_error(self):
        message = self.error_message(
            "agent Blob uses:\n"
            "    behavior.basic\n"
        )
        self.assertIn("Unknown agent preset category `behavior`.", message)
        self.assertIn("position, movement, biology", message)

    def test_preset_names_require_uses_header(self):
        message = self.error_message(
            "agent Blob:\n"
            "    position.basic\n"
        )
        self.assertIn("Agent presets require `uses`", message)

    def test_agent_declarations_do_not_create_runtime_variables(self):
        message = self.error_message(
            "agent Blob uses:\n"
            "    position.basic\n"
            "\n"
            "print(Blob)\n"
        )
        self.assertIn("`Blob` is not defined.", message)


if __name__ == "__main__":
    unittest.main()
