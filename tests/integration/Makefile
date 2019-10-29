# Self-Documented Makefile
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help: ## Show this help message.
	@grep -E '^[a-zA-Z0-9_\.-\%]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

CLEAN_FIND_CMD=find \
	. \
	-type f \( \
		-name '*.script' \
	\) \
	-or -type d \( \
		-name '*.dSYM' -or \
		-name 'Sandbox' -or \
		-name 'Output' \
	\) \
	-not -path "**Expected**" \
	-not -path "**Input**"

CLEAN_FILES=$(shell $(CLEAN_FIND_CMD))
clean: ## Clean all temporary artefacts
	echo $(CLEAN_FILES) | \
		xargs rm -rfv

