# ytdl-web
Side project - wrap a web page around ytdl, so that I can start downloads from anywhere and have them
auto-saved to the network drive.

I see youtube and similar links all the time, and want to view them on the TV minus ads, or maybe just defer
watching. This little app uses a home server with SMB connection to my NAS to save. Super basic web wrapper 
around YTDL, with a bit of usefulness in the 'build list of target directories' logic and HTML.

## Project goals
- Lightweight web pages that load fast, render properly on desktop, mobile and tablet. 
- No javascript
- multiple concurrent downloads
- hands-off operation
- DIY the SQL part, just to learn it myself
- SQLite for jobs and logging

## Current status

As of 10/18/2021, jobs and logging are saved into SQLite, enabling the addition of a polling/detail page, plus a table 
of recent jobs on the home page. Much nicer!

Works as intended:
- Downloads run in the background
- Basic Bootstrap v4 CSS, explicitly _without_ JS. Input validation is most-basic, but looks OK.
- No file management, I expect clutter to accumulate.
- Utterly insecure - no input validation, so internal-network use only. [Little Bobby Tables risk](https://xkcd.com/327/)
- Added 'retry' button to failed downloads
- ported from youtube-dl to [yt_dlp](https://github.com/yt-dlp/yt-dlp) which seems maintained and quite nice.
- 
### Next steps
- Add pagination to index table
- Add intelligence to log display - collapse the middle if too long (accordion maybe)
- Widen margins on log display
- Add 'retry this download IFF rc != 0' kind of thing
- Parse debug logs or API to include download bytes and percentage to poll/detail. Progress bar!
- Move ad-hoc test code into proper unit tests.
- For iOS, add manifest or whatever so it looks a proper home screen icon.
- Productionize it - WSGI, debug off, reverse proxy. Cannot currently be exposed to the internet.
- Some sort of temp directory with automatic cleanup would be cool.
- Try [v2 Flask beta?](https://www.reddit.com/r/Python/comments/msbt3p/flask_20_is_coming_please_help_us_test/)

## Installation

	python3 -m venv venv
	source venv/bin/activatate
	pip install -r requirements.txt
	
## Run it

	source venv/bin/activatate
	python main.py

There's also run.sh for in the background.

## Maintain it

TBD - yt_dlp has periodic updates, need to determine how to upgrade the library in place. There's a shell script now.

## Tools and libraries

FastAPI lacks the built-in templates and html support, so Flask is perfect. We also, of course, use 
the Python API for yt_dlp.

## Docs

- [Flask](https://flask.palletsprojects.com/en/1.1.x/) for fastest dev
- [yt_dlp](https://github.com/yt-dlp/yt-dlp) embedding docs are excellent.
- CSS styles from [Bootstrap v4](https://getbootstrap.com/docs/5.0/forms/overview/)
- Film icon from [here](https://icons.getbootstrap.com/icons/film/)
- Reset icon from [here](https://icons.getbootstrap.com/icons/x-circle/)  
- Favicon from [here](https://www.favicon.cc/?action=icon&file_id=935559)
- Form styled using [this documentation](https://getbootstrap.com/docs/5.0/forms/overview/)
