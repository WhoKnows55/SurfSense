# =============================================================================
# SurfSense Makefile
# =============================================================================
# Common commands for development

.PHONY: help install run test check-api clean \
        eval-llm eval-score scenarios train figures

# Default target
help:
	@echo ""
	@echo "SurfSense - AI Surf Trip Planning Assistant"
	@echo ""
	@echo "Development:"
	@echo "  make install      Install all dependencies"
	@echo "  make run          Start the terminal chat"
	@echo "  make test         Run test suite"
	@echo "  make check-api    Verify all API connections"
	@echo "  make clean        Remove cache files"
	@echo ""
	@echo "Evaluation:"
	@echo "  make eval-llm     Full pipeline: generate runs + score + summary"
	@echo "  make eval-llm FORCE=1  Regenerate all run files (re-queries both systems)"
	@echo "  make eval-score   Re-score existing run files (no new API calls)"
	@echo "  make scenarios    Run the three scripted demo scenarios (Chapter 4.1)"
	@echo "  make snapshots    Fetch missing snapshot files for new spots"
	@echo ""
	@echo "ML:"
	@echo "  make train        Train the ML model"
	@echo "  make figures      Regenerate all ML figures from evaluation notebook"
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

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

# Full LLM baseline pipeline. Set FORCE=1 to regenerate existing run files.
eval-llm:
	@echo "Running LLM evaluation pipeline (11 scenarios)..."
ifdef FORCE
	python -m evaluation.pipeline --force
else
	python -m evaluation.pipeline
endif

# Score only — no new API calls, just re-read run files and update results.csv
eval-score:
	@echo "Scoring existing run files..."
	python -m evaluation.llm_baseline.score
	@echo "Results written to evaluation/llm_baseline/results.csv"

# Three scripted demo scenarios (thesis Section 3.4)
scenarios:
	@echo "Running scenario 1 (single spot, beginner, rule-based)..."
	python -m scenarios.01_single_spot_guincho
	@echo "Running scenario 2 (multi-spot trip, intermediate, rule-based)..."
	python -m scenarios.02_multi_spot_trip
	@echo "Running scenario 3 (Guincho ML scoring)..."
	python -m scenarios.03_guincho_ml
	@echo "All scenarios complete."

# Fetch any missing snapshot files for spots defined in generate_snapshots.py
snapshots:
	@echo "Generating missing snapshots..."
	python -m scenarios.generate_snapshots --all

# ---------------------------------------------------------------------------
# ML
# ---------------------------------------------------------------------------

train:
	@echo "Training ML model..."
	python -m ml.train
	@echo "Model saved to ml/models/"

figures:
	@echo "Regenerating ML figures (requires ml/notebooks/03_evaluation.ipynb)..."
	jupyter nbconvert --to notebook --execute ml/notebooks/03_evaluation.ipynb \
		--output ml/notebooks/03_evaluation.ipynb

# ---------------------------------------------------------------------------
# Clean cache and temporary files
# ---------------------------------------------------------------------------

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
