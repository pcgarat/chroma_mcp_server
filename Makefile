# Makefile para scripts de utilidad de chroma_mcp_server
# Proporciona órdenes convenientes para ejecutar scripts en scripts/propios

# Directorio donde están los scripts
SCRIPTS_DIR := scripts/propios
SCRIPT_DIR := $(shell cd "$(SCRIPTS_DIR)" && pwd)

# Colores para output
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

.PHONY: help reset-collections generate-cursor-rules setup-env check-env setup-mcp-config index-project

# Orden por defecto: mostrar ayuda
.DEFAULT_GOAL := help

help: ## Muestra esta ayuda
	@echo "$(GREEN)Scripts disponibles para chroma_mcp_server:$(NC)"
	@echo ""
	@echo "$(YELLOW)Órdenes disponibles:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Ejemplos:$(NC)"
	@echo "  make reset-collections      # Resetea todas las colecciones de ChromaDB"
	@echo "  make generate-cursor-rules  # Genera reglas de Cursor optimizadas"
	@echo "  make setup-mcp-config       # Configura el servidor MCP de ChromaDB en un proyecto"
	@echo "  make index-project          # Indexa todos los documentos de un proyecto"
	@echo "  make check-env              # Verifica que el archivo .env existe"
	@echo ""

reset-collections: ## Resetea todas las colecciones de ChromaDB (borra y recrea)
	@echo "$(GREEN)🔄 Reseteando colecciones de ChromaDB...$(NC)"
	@bash "$(SCRIPT_DIR)/reset-collections.sh"

generate-cursor-rules: ## Genera reglas de Cursor optimizadas en un proyecto (interactivo)
	@echo "$(GREEN)📝 Generando reglas de Cursor...$(NC)"
	@PYTHONIOENCODING=utf-8 python3 "$(SCRIPT_DIR)/generate_cursor_rules.py"

setup-env: ## Carga variables de entorno desde .env (requiere source make setup-env)
	@echo "$(YELLOW)⚠️  Esta orden debe ejecutarse con: source <(make setup-env)$(NC)"
	@echo "$(YELLOW)   O usa: source $(SCRIPT_DIR)/setup-chroma-env.sh$(NC)"
	@bash "$(SCRIPT_DIR)/setup-chroma-env.sh"

setup-mcp-config: ## Configura el servidor MCP de ChromaDB en un proyecto (interactivo)
	@echo "$(GREEN)🔧 Configurando servidor MCP de ChromaDB...$(NC)"
	@PYTHONIOENCODING=utf-8 python3 "$(SCRIPT_DIR)/setup-mcp-config.py"

index-project: ## Indexa todos los documentos de un proyecto (lee mcp.json para obtener CHROMA_TENANT)
	@echo "$(GREEN)📚 Indexando proyecto...$(NC)"
	@PYTHONIOENCODING=utf-8 python3 "$(SCRIPT_DIR)/index-project.py"

check-env: ## Verifica que el archivo .env existe y muestra su ubicación
	@if [ -f ".env" ]; then \
		echo "$(GREEN)✅ Archivo .env encontrado en: $(shell pwd)/.env$(NC)"; \
	elif [ -f "$(SCRIPT_DIR)/.env" ]; then \
		echo "$(GREEN)✅ Archivo .env encontrado en: $(SCRIPT_DIR)/.env$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Archivo .env no encontrado$(NC)"; \
		if [ -f "$(SCRIPT_DIR)/env-template" ]; then \
			echo "$(YELLOW)💡 Para crear el archivo .env, ejecuta:$(NC)"; \
			echo "   cp $(SCRIPT_DIR)/env-template .env"; \
			echo "   # Luego edita .env con tus valores"; \
		fi; \
		exit 1; \
	fi

