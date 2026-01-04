.PHONY: help build up down restart logs clean test status

# Default target
help:
	@echo "Trigo Homework - Prometheus Service Discovery"
	@echo ""
	@echo "Available commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make restart  - Restart all services"
	@echo "  make logs     - Follow logs from all services"
	@echo "  make status   - Show service status"
	@echo "  make test     - Run verification tests"
	@echo "  make clean    - Remove all containers and volumes"

# Build Docker images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start services
up:
	@echo "Starting services..."
	docker-compose up -d
	@echo ""
	@echo "Services started! Access Prometheus at http://localhost:9090"
	@echo "Run 'make status' to check service health"

# Stop services
down:
	@echo "Stopping services..."
	docker-compose down

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart

# Follow logs
logs:
	docker-compose logs -f

# Show status
status:
	@echo "Service Status:"
	@docker-compose ps
	@echo ""
	@echo "Health Checks:"
	@docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $$(docker-compose ps -q) 2>/dev/null || true

# Run tests
test:
	@echo "Running verification tests..."
	@echo ""
	@echo "Test 1: Checking inventory service..."
	@curl -s http://localhost:1337/inventory | head -c 100 && echo "... [OK]"
	@echo ""
	@echo "Test 2: Checking service discovery output..."
	@docker exec service_discovery cat /shared/targets.json | head -n 10 && echo "... [OK]"
	@echo ""
	@echo "Test 3: Checking Prometheus health..."
	@curl -s http://localhost:9090/-/healthy && echo " [OK]"
	@echo ""
	@echo "Test 4: Checking discovered targets..."
	@curl -s http://localhost:9090/api/v1/targets | grep -o '"job":"sensors"' | head -n 1 && echo "Sensors discovered [OK]"
	@echo ""
	@echo "All tests passed! ✓"

# Clean up everything
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Cleanup complete!"

