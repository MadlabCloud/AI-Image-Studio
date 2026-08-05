.PHONY: install test lint package
install:
	python -m pip install -e ".[dev,mcp]"
test:
	pytest
	python scripts/validate_bundle.py
package:
	python scripts/build_distributions.py
