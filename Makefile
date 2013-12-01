.PHONY: env

env:
	virtualenv env
	. env/bin/activate && pip install -r requirements.txt

download: 
	. env/bin/activate && ./download.py

