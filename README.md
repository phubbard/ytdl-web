# ytdl-web
Side project idea - wrap a web page around ytdl, so that I can start downloads from anywhere and have them
auto-saved to the network drive.

I see youtube and similar links all the time, and want to view them on the TV minus ads, or maybe just defer
watching. This little app uses a home server with SMB connection to my NAS to save and move. Super basic web wrapper 
around YTDL, with a bit of usefulness in the 'build list of target directories' logic and HTML.

## Current status

Works as intended, but
- One file at a time, and the page doesn't return until complete.
- Might be cleaner to setcwd to the target instead of doing download/move.
- No CSS at all. Pages are ugly.
- No file management, I expect clutter to accumulate.

### Next steps

Productionize it - WSGI, debug off, reverse proxy. Cannot currently be exposed to the internet.
Find a way to push results as they happen - or at least a spinner
Some sort of temp directory with automatic cleanup would be cool.
CSS. Even most-basic. Media queries for phone FTW.
Put directories into config file.
Multiple concurrent downloads - hmm. Async? Threads? Websockets to push updates?


## Installation

	python3 -m venv venv
	source venv/bin/activatate
	pip install -r requirements.txt
	
## Run it

	source venv/bin/activatate
	python main.py

## Tools and libraries

[Flask](https://flask.palletsprojects.com/en/1.1.x/) for fastest dev or [fastapi](https://fastapi.tiangolo.com/) to learn?

FastAPI lacks the built-in templates and html support, so revert back to it.

## Notes

You have to disable the Intuit package index to install - it 404s the youtube-dl package. See ~/.pip/pip.conf

## Docs
Looks like [it's easily embeddable](https://github.com/ytdl-org/youtube-dl#embedding-youtube-dl). Nice.

