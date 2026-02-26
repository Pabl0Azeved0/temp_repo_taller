.DEFAULT_GOAL := help

.PHONY: help venv up down restart restart-db restart-full test test-local tester-validate

help:
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  venv            : 🐍 Create virtual environment and install dependencies"
	@echo "  up              : 🚀 Start the Docker containers in the background"
	@echo "  down            : 🛑 Stop the Docker containers"
	@echo "  test            : 🧪 Run the test cases inside the Docker container"
	@echo "  test-local      : 🧪 Run the test cases locally (requires venv)"
	@echo "  tester-validate : 🎯 Validates step-by-step each question from INSTRUCTIONS.md"
	@echo "  restart         : 🔄 Standard restart (stop containers, rebuild, and up)"
	@echo "  restart-db      : 💽 Wipes the Database volume and restarts (Fresh DB)"
	@echo "  restart-full    : 🔥 NUKE & PAVE: Wipes volumes, images, and rebuilds everything"
	@echo ""

venv:
	@echo "🐍 Creating virtual environment and installing dependencies..."
	@python3 -m venv venv
	@./venv/bin/pip install --upgrade pip
	@./venv/bin/pip install -r requirements.txt
	@echo "✅ Virtual environment created successfully! (To activate, run: source venv/bin/activate)"

up:
	@echo "🚀 Starting containers..."
	@docker compose up --build -d
	@echo "✅ Containers are up and running!"

down:
	@echo "🛑 Stopping containers..."
	@docker compose down
	@echo "✅ Containers stopped!"

test:
	@echo "🧪 Running Tests in Docker..."
	@docker compose exec web pytest -v tests/

test-local:
	@echo "🧪 Running Tests Locally..."
	@if [ -d "venv" ]; then \
		PYTHONPATH=. ./venv/bin/pytest -v tests/; \
	else \
		echo "⚠️  venv not found! Run 'make venv' first."; \
	fi

tester-validate:
	@echo "========================================================="
	@echo "🎯 Validating Question 1: MiniVenmo.create_user()"
	@echo "========================================================="
	@if [ -d "venv" ]; then PYTHONPATH=. ./venv/bin/pytest -v tests/test_app.py::test_create_user; else docker compose exec web pytest -v tests/test_app.py::test_create_user; fi
	@echo ""
	@echo "========================================================="
	@echo "🎯 Validating Question 2: User.pay() balances and credit"
	@echo "========================================================="
	@if [ -d "venv" ]; then PYTHONPATH=. ./venv/bin/pytest -v tests/test_app.py::test_pay_with_balance tests/test_app.py::test_pay_with_credit tests/test_app.py::test_pay_exceed_credit; else docker compose exec web pytest -v tests/test_app.py::test_pay_with_balance tests/test_app.py::test_pay_with_credit tests/test_app.py::test_pay_exceed_credit; fi
	@echo ""
	@echo "========================================================="
	@echo "🎯 Validating Question 3: User.retrieve_activity() and MiniVenmo.render_feed()"
	@echo "========================================================="
	@if [ -d "venv" ]; then PYTHONPATH=. ./venv/bin/pytest -v tests/test_app.py::test_retrieve_activity; else docker compose exec web pytest -v tests/test_app.py::test_retrieve_activity; fi
	@echo ""
	@echo "========================================================="
	@echo "🎯 Validating Question 4: User.add_friend()"
	@echo "========================================================="
	@if [ -d "venv" ]; then PYTHONPATH=. ./venv/bin/pytest -v tests/test_app.py::test_add_friend; else docker compose exec web pytest -v tests/test_app.py::test_add_friend; fi
	@echo ""
	@echo "========================================================="
	@echo "🎯 Validating Question 5: Feed with friends added"
	@echo "========================================================="
	@if [ -d "venv" ]; then PYTHONPATH=. ./venv/bin/pytest -v tests/test_app.py::test_render_feed; else docker compose exec web pytest -v tests/test_app.py::test_render_feed; fi
	@echo ""
	@echo "✅ All INSTRUCTIONS.md validations completed!"

restart:
	@echo "🔄 Restarting services..."
	@docker compose down
	@docker compose up --build -d
	@echo "✅ Services restarted!"

restart-db:
	@echo "💽 Resetting Database (Volumes wiped)..."
	@docker compose down -v
	@docker compose up --build -d
	@echo "✅ Database reset complete!"

restart-full:
	@echo "🔥 Nuke & Pave: Stopping containers, pruning volumes & images..."
	@docker compose down -v
	@docker volume prune -f
	@docker rmi -f $$(docker images -aq) || true
	@echo "🚀 Rebuilding and starting everything..."
	@docker compose up --build -d
	@echo "✅ Full restart complete!"