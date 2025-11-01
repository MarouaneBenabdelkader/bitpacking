# Makefile for compiling LaTeX report

# Main target
.PHONY: all
all: report.pdf

# Compile the LaTeX document
report.pdf: report.tex
	pdflatex -interaction=nonstopmode report.tex
	pdflatex -interaction=nonstopmode report.tex
	@echo "PDF generated: report.pdf"

# Clean auxiliary files
.PHONY: clean
clean:
	rm -f *.aux *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz

# Clean everything including PDF
.PHONY: cleanall
cleanall: clean
	rm -f report.pdf

# Quick compile (single pass)
.PHONY: quick
quick: report.tex
	pdflatex -interaction=nonstopmode report.tex

# View the PDF (platform-specific)
.PHONY: view
view: report.pdf
ifeq ($(OS),Windows_NT)
	start report.pdf
else
	@command -v xdg-open > /dev/null && xdg-open report.pdf || open report.pdf
endif

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all       - Compile the LaTeX report (default)"
	@echo "  quick     - Quick compile (single pass)"
	@echo "  clean     - Remove auxiliary files"
	@echo "  cleanall  - Remove all generated files including PDF"
	@echo "  view      - Open the PDF after compilation"
	@echo "  help      - Show this help message"
