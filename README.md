# ytdl-web idea
Side project idea - wrap a web page around ytdl, so that I can start downloads from anywhere and have them
auto-saved to the network drive.

## Tools and libraries

[Flask](https://flask.palletsprojects.com/en/1.1.x/) for fastest dev or [fastapi](https://fastapi.tiangolo.com/) to learn?

FastAPI lacks the built-in templates and html support, so revert back to it.

## Notes

You have to disable the Intuit package index to install - it 404s the youtube-dl package. See ~/.pip/pip.conf

## Docs
Looks like it's easily embeddable - https://github.com/ytdl-org/youtube-dl#embedding-youtube-dl

