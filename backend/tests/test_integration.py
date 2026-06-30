"""Integration tests: verify production code has no debug prints."""

import ast
import inspect


class TestNoDebugPrints:
    """Verify no debug print() statements in production backend code."""

    def _check_module_for_prints(self, module):
        source = inspect.getsource(module)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    assert (
                        False
                    ), f"Debug print() found in {module.__name__} at line {node.lineno}"

    def test_no_print_in_main(self):
        from backend import main

        self._check_module_for_prints(main)

    def test_no_print_in_etl_cleaner(self):
        from backend.etl import cleaner

        self._check_module_for_prints(cleaner)

    def test_no_print_in_etl_loader(self):
        from backend.etl import loader

        self._check_module_for_prints(loader)

    def test_no_print_in_categorizer_prompts(self):
        from backend.categorizer import prompts

        self._check_module_for_prints(prompts)

    def test_no_print_in_categorizer_validator(self):
        from backend.categorizer import validator

        self._check_module_for_prints(validator)

    def test_no_print_in_categorizer_processor(self):
        from backend.categorizer import processor

        self._check_module_for_prints(processor)

    def test_no_print_in_api_clients(self):
        from backend.api.routes import clients

        self._check_module_for_prints(clients)

    def test_no_print_in_api_metrics(self):
        from backend.api.routes import metrics

        self._check_module_for_prints(metrics)
