# LaTeX Makefile
FILE=report

all: $(FILE).pdf

.PHONY: clean

clean:
	rm -rf *.blg 
	rm -rf *.out 
	rm -rf *.bbl 
	rm -rf *.log
	rm -rf *.aux
	rm -f ${FILE}.pdf


$(FILE).pdf: *.tex *.bib
	pdflatex -shell-escape $(FILE).tex
	pdflatex -shell-escape $(FILE).tex
	bibtex $(FILE)
	pdflatex -shell-escape $(FILE).tex
	pdflatex -shell-escape $(FILE).tex
