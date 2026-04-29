# Makefile for compiling the LaTeX report
# Usage: make         (builds report.pdf)
#        make clean   (removes intermediate build artifacts)
#        make distclean (removes intermediates and report.pdf)

TEX = report.tex
PDF = report.pdf
PDFLATEX ?= pdflatex

.PHONY: all clean distclean

all: $(PDF)

$(PDF): $(TEX)
	@echo "Compiling $(TEX) with pdflatex..."
	@$(PDFLATEX) -interaction=nonstopmode $(TEX) > /dev/null 2>&1 || \
		(echo "pdflatex failed on pass 1. See report.log for details."; exit 1)
	@$(PDFLATEX) -interaction=nonstopmode $(TEX) > /dev/null 2>&1 || \
		(echo "pdflatex failed on pass 2. See report.log for details."; exit 1)
	@echo "Built $(PDF)"

clean:
	@rm -f *.aux *.log *.out *.toc

distclean: clean
	@rm -f $(PDF)
