# =============================================================================
# SurfSense Makefile
# =============================================================================
# Common commands for development

.PHONY: help install run test check-api clean

# Default target
help:
	@echo ""
	@echo "🏄 SurfSense - AI Surf Trip Planning Assistant"
	@echo ""
	@echo "Commands:"
	@echo "  make install   Install all dependencies"
	@echo "  make run       Start the terminal chat"
	@echo "  make test      Run test suite"
	@echo "  make check-api Verify all API connections"
	@echo "  make clean     Remove cache files"
	@echo ""

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo ""
	@echo "✅ Installation complete!"
	@echo "   Run 'make run' to start chatting."

# Run the terminal chat application
run:
	@echo "🏄 Starting SurfSense..."
	python -m app

# Run tests
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v
	@echo "✅ Tests complete!"

# Verify all API connections and env vars
check-api:
	@echo "🔌 Checking API connections..."
	pytest tests/test_api_connections.py -v
	@echo "✅ All API connections verified!"

# Clean cache and temporary files
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/
	@echo "✅ Cleanup complete!"
