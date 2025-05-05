.PHONY: dev-up dev-down scraper-test e2e-test

dev-up:
	npm install
	npm run dev & npm run mock-api

dev-down:
	pkill -f "node.*mock-api" || true
	pkill -f "next dev" || true

scraper-test:
	cd backend && python -c "from ig_scraper import main; import sys; sys.argv = ['ig_scraper.py', 'productivity', '--top', '3', '--min_engage', '1.0']; main()" && \
	python -c "from app.database import get_reels_by_audience; reels = get_reels_by_audience({}); print(f'Found {len(reels)} reels'); \
	assert len(reels) >= 3, 'Not enough reels found'; \
	assert all(r.get('transcript') for r in reels), 'Missing transcripts'; \
	assert all(r.get('audience_json') for r in reels), 'Missing audience data'; \
	print('Scraper test passed!')"

e2e-test:
	npx playwright test
