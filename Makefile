
clean:
	rm -rf dist build reformer.egg-info
	find -name ".pyc" -delete

upload: clean
	python3.5 setup.py sdist bdist_wheel
	twine upload dist/*