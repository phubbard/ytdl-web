# ytdl-web
Side project idea - wrap a web page around ytdl, so that I can start downloads from anywhere and have them
auto-saved to the network drive.

I see youtube and similar links all the time, and want to view them on the TV minus ads, or maybe just defer
watching. This little app uses a home server with SMB connection to my NAS to save. Super basic web wrapper 
around YTDL, with a bit of usefulness in the 'build list of target directories' logic and HTML.

## Current status

Works as intended, but
- Downloads run in the background, but there's no way to see if the failed or finished
- Basic Bootstrap v4 CSS, explicitly _without_ JS. Input validation is most-basic, but looks OK.
- No file management, I expect clutter to accumulate.
- Utterly insecure - no input validation, so internal-network use only.

### Next steps
- For iOS, add manifest or whatever so it looks a proper home screen icon.
- Productionize it - WSGI, debug off, reverse proxy. Cannot currently be exposed to the internet.
- Find a way to push results as they happen - or at least a spinner
- Some sort of temp directory with automatic cleanup would be cool.
- ~~Put directories into config file.
- ~~Multiple concurrent downloads - hmm. Async? Threads? Websockets to push updates?
- Try [v2 Flask beta?](https://www.reddit.com/r/Python/comments/msbt3p/flask_20_is_coming_please_help_us_test/)

## Installation

	python3 -m venv venv
	source venv/bin/activatate
	pip install -r requirements.txt
	
## Run it

	source venv/bin/activatate
	python main.py

## Maintain it

TBD - YTDL has periodic updates, need to determine how to upgrade the library in place.

## Tools and libraries

FastAPI lacks the built-in templates and html support, so Flask is perfect. We also, of course, use 
the Python API for youtube-dl.

## Docs

- [Flask](https://flask.palletsprojects.com/en/1.1.x/) for fastest dev
- [fastapi](https://fastapi.tiangolo.com/) to learn? No, need HTML/CSS/templates
- [YTDL is easily embeddable](https://github.com/ytdl-org/youtube-dl#embedding-youtube-dl). Nice.
- CSS styles from [Bootstrap v4](https://getbootstrap.com/docs/5.0/forms/overview/)
- Film icon from [here](https://icons.getbootstrap.com/icons/film/)
- Reset icon from [here](https://icons.getbootstrap.com/icons/x-circle/)  
- Favicon from [here](https://www.favicon.cc/?action=icon&file_id=935559)
- Form styled using [this documentation](https://getbootstrap.com/docs/5.0/forms/overview/)

