# Makefile for compiling the LaTeX report
# Usage: make        (builds report.pdf)
#        make clean  (removes build artifacts)

TEX = report.tex
PDF = report.pdf

.PHONY: all clean

all: $(PDF)

$(PDF): $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)

clean:
	rm -f *.aux *.log *.out *.toc *.pdf
