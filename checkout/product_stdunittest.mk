#########################################################################
#									#
# Copyright (c) Nokia Siemens Network 2009. All rights reserved.			#
#									#
# This material, including documentation and any related computer	#
# programs, is protected by copyright controlled by Nokia. 		#
# All rights are reserved. Copying, including reproducing, storing, 	#
# adapting or translating, any or all of this material requires 	#
# the prior written consent of NSN. This material also contains 	#
# confidential information which may not be disclosed to others 	#
# without the prior written consent of NSN.								#
#									#
# Module: code_statistics.mk							#
# Author: Chi Xiaobo, last changed: July 1st, 2009		#
#									#
# Description: 								#
#1. user's unittest makefile should include this file to generate the \
code coverage report.
#2. the user's makefile should define GCOV_SRC_DIRS to point the source code files \
in which dirs that your want to get the calculate the coverage; usually this do\
 not include those test codes.
#########################################################################

ifeq ($(GCOV_SRC_DIRS),)
	ifneq ($(SRC_DIRS),)
		GCOV_SRC_DIRS:=$(SRC_DIRS)
	else
		GCOV_SRC_DIRS:=../src
	endif
endif

ifeq ($(gcov),y)
LCOV_FLAG= -fprofile-arcs -ftest-coverage 
CFLAGS += $(LCOV_FLAG) 
CPPFLAGS += $(LCOV_FLAG) 
LFLAGS += $(LCOV_FLAG) 
LD_FLAGS += $(LCOV_FLAG) 
C_FLAGS += $(LCOV_FLAG) 
endif

CPPFLAGS += -D__NO_TIME_TYPE -fpermissive
CXXFLAGS += $(CPPFLAGS) $(LIB)
CFLAGS += $(CPPFLAGS) $(LIB)

LCOV_DIR_OPTS=$(foreach dir,$(GCOV_SRC_DIRS), -d $(dir) )

#LCOV is the code coverage tool for c/c++
LCOV_BIN_DIR=$(VOBTAG)/SS_ILThirdpart/lcov-1.11
LCOV_BIN=$(LCOV_BIN_DIR)/bin/lcov
LCOV_GENHTML=$(LCOV_BIN_DIR)/bin/genhtml

LCOV_OUTPUT_DIR=lcov_report
LCOV_OUTPUT_FILE=$(LCOV_OUTPUT_DIR)/lcov.report.txt

ifdef TNSDL_OPT
	test_language="TNSDL"
else
	test_language="C/C++"
endif

################### Target #####################################

.PHONY: coverage
coverage:
	-@mkdir -p $(LCOV_OUTPUT_DIR)
	-@$(LCOV_BIN) --rc lcov_branch_coverage=1 $(LCOV_DIR_OPTS) -b . -c  -o $(LCOV_OUTPUT_FILE)
	-@$(LCOV_GENHTML) --rc lcov_branch_coverage=1 -o $(LCOV_OUTPUT_DIR) $(LCOV_OUTPUT_FILE)
	-@echo "test_language: $(test_language)" >> $(LCOV_OUTPUT_FILE)

.PHONY: coverage_clean
coverage_clean:
	-rm -rf $(LCOV_OUTPUT_DIR)

clean: coverage_clean

################### END #####################################

