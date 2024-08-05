install_poetry_zsh:
	curl -sSL https://install.python-poetry.org | python3 - --version 1.5.1
	echo "export PATH=\"/Users/$$(whoami)/.local/bin:\$$PATH\"" >> ~/.zshrc && \
	source ~/.zshrc && \
	mkdir -p ~/.zfunc && \
	poetry completions zsh > ~/.zfunc/_poetry && \
	echo "fpath+=~/.zfunc" >> ~/.zshrc && \
	echo "autoload -Uz compinit && compinit" >> ~/.zshrc && \
	poetry --version

lint:
	poetry run black --check . && \
	poetry run ruff check . && \
	poetry run mypy .

run_local:
	cd running_bot; poetry run python -m flask --app main run --debug --port=8000

ngrok:
	ngrok http 8000

generate:
	poetry export --without-hashes --format=requirements.txt > running_bot/requirements.txt

test:
	poetry run pytest --cov-report=xml --cov-branch -n auto -m "not slow"
