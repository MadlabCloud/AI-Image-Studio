.PHONY: install lint test package
install:
	python -m pip install -e ".[dev,mcp]"
lint:
	python -m ruff check .
test:
	pytest
	python scripts/validate_bundle.py
package:
	python scripts/build_distributions.py
