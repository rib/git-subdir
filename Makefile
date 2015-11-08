all: git-subdir.html man1/git-subdir.1

%.xml: %.txt
	asciidoc -f asciidoc.conf -d manpage -b docbook -o $@ $<

%.html: %.txt
	asciidoc -f asciidoc.conf -d manpage -o $@ $<

man1/%.1: %.xml
	xmlto man $< -o man1

README.md: git-subdir.xml
	pandoc -f docbook -t markdown_github $< -o $@

check:
	./tests.py -v

clean:
	rm -f git-subdir.xml git-subdir.html man1/git-subdir.1
