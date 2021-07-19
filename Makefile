all: clean process evaluate

clean:
	rm -f test/urls/*;
	rm -f test/text/*;
	rm -f test/summary*.txt;

process:
	for filename in test/samples/*.pdf; do \
		printf "\nFile: $$filename \nCommand: U_ANN \n"; \
		./main.py -c U_ANN -i "$$filename" -o "test/urls/$$(basename "$$filename")-U_ANN.txt"; \
		for executor in PDFM GROB; do \
			printf "Command: TXT [Executor: $$executor] \n"; \
			./main.py -c TXT -e $$executor -i "$$filename" -o "test/text/$$(basename "$$filename")-$$executor.txt"; \
			for cmd in U_TXT U_ALL; do \
				for regex in 1 2 3 4; do \
					printf "Command: $$cmd [Executor: $$executor] [Regex: $$regex] \n"; \
					./main.py -c "$$cmd" -e "$$executor" -r "$$regex" -i "$$filename" -o "test/urls/$$(basename "$$filename")-$$executor-R$$regex-$$cmd.txt"; \
				done \
			done \
		done \
	done

evaluate:
	for cmd in "U_ANN" "U_TXT" "U_ALL"; do \
		./evaluate.py -l test/labels -u test/urls -c $$cmd -o test/summary-$$cmd.csv >test/summary-$$cmd.txt; \
	done
