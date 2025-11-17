.PHONY: help install test run clean

# Default target
help:
	@echo "🏄 SurfSense - Available Commands"
	@echo ""
	@echo "  make install   - Install all dependencies"
	@echo "  make test      - Run test suite with pytest"
	@echo "  make run       - Start the application"
	@echo "  make clean     - Remove cache files and build artifacts"
	@echo ""

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Run tests
test:
	@echo "Running pytest..."
	pytest tests/ -v
	@echo "✓ Tests complete"

# Run application
run:
	python -m app

# Clean cache and build files
clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "✓ Cleanup complete"
