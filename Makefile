.PHONY: dev-up dev-down

dev-up:
	npm install
	npm run dev & npm run mock-api

dev-down:
	pkill -f "node.*mock-api" || true
	pkill -f "next dev" || true
