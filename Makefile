all: clean ann all-pdfium all-grob all-pdfm evaluate
all-pdfium: text-pdfium links-pdfium
all-grob: text-grob links-grob
all-pdfm: text-pdfm links-pdfm

clean:
	rm -f test/urls/* test/text/* test/summary*.*

# ANNOTATIONS ==========================================================================================================
ann:
	for filename in test/samples/*.pdf; do \
		echo "File: $$filename [Command: U_ANN]"; \
		./main.py -c U_ANN -i $$filename -o test/urls/$$(basename $$filename)-U_ANN.txt; \
	done;

# PDFIUM ===============================================================================================================
text-pdfium:
	for filename in test/samples/*.pdf; do \
		echo "File: $$filename [Command: TXT] [Executor: PDFIUM]"; \
		./main.py -c TXT -e PDFIUM -i $$filename -o test/text/$$(basename $$filename)-PDFIUM.txt; \
	done;

links-pdfium:
	for filename in test/samples/*.pdf; do \
		for cmd in U_TXT U_ALL; do \
			echo "File: $$filename [Executor: PDFIUM] [Command: $$cmd]"; \
			./main.py -c $$cmd -e PDFIUM -i $$filename -o test/urls/$$(basename $$filename)-PDFIUM-$$cmd.txt; \
		done; \
	done;

# GROBID ===============================================================================================================
text-grob:
	for filename in test/samples/*.pdf; do \
		echo "File: $$filename [Command: TXT] [Executor: GROB]"; \
		./main.py -c TXT -e GROB -i $$filename -o test/text/$$(basename $$filename)-GROB.txt; \
	done;

links-grob:
	for filename in test/samples/*.pdf; do \
		for cmd in U_TXT U_ALL; do \
			for regex in 3 4; do \
				echo "File: $$filename [Executor: GROB] [Command: $$cmd] [Regex: $$regex]"; \
				./main.py -c $$cmd -e GROB -r $$regex -i $$filename -o test/urls/$$(basename $$filename)-GROB-R$$regex-$$cmd.txt; \
			done; \
		done; \
	done;

# PDFMINER =============================================================================================================
text-pdfm:
	for filename in test/samples/*.pdf; do \
		echo "File: $$filename [Command: TXT] [Executor: PDFM]"; \
		./main.py -c TXT -e PDFM -i $$filename -o test/text/$$(basename $$filename)-PDFM.txt; \
	done;

links-pdfm:
	for filename in test/samples/*.pdf; do \
		for cmd in U_TXT U_ALL; do \
			for regex in 3 4; do \
				echo "File: $$filename [Executor: PDFM] [Command: $$cmd] [Regex: $$regex]"; \
				./main.py -c $$cmd -e PDFM -r $$regex -i $$filename -o test/urls/$$(basename $$filename)-PDFM-R$$regex-$$cmd.txt; \
			done; \
		done; \
	done;

# EVALUATION ===========================================================================================================
evaluate:
	for cmd in U_ANN U_TXT U_ALL; do \
		./evaluate.py -l test/labels -u test/urls -c $$cmd -o test/ >test/summary-$$cmd.txt; \
	done
