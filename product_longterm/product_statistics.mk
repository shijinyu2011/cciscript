#########################################################################
#									#
# Copyright (c) Nokia Siemens Network 2006-20010. All rights reserved.			#
#									#
# This material, including documentation and any related computer	#
# programs, is protected by copyright controlled by Nokia. 		#
# All rights are reserved. Copying, including reproducing, storing, 	#
# adapting or translating, any or all of this material requires 	#
# the prior written consent of NSN. This material also contains 	#
# confidential information which may not be disclosed to others 	#
# without the prior written consent of NSN.				#
#									#
#									#
# Module: 								#
#	project_stdctargets.mk							#
# Author: 								#
#	Chi Xiaobo June 15th, 2009							#
#									#
# Description: 								#
# 	This file include some IL1 project special standard targets #
#	for building sub targets beside stdctargets.mk	#
#									#
#									#
#########################################################################

########### Targets for recursive code complex #########################
code_complex: $(DIRS:=/complex)

nodirs_complex \
$(DIRS:=/complex):
	-@echo nodirs_complex $(DIRS:=/complex)
	-@( echo -e "\nSub complex: $(@:/complex=) of $(PWD)" ; cd $(@:/complex=) && $(MAKE) code_complex )

complex_clean: $(DIRS:=/complex_clean)

nodirs_complex_clean \
$(DIRS:=/complex_clean):
	-@echo nodirs_complex_clean $(DIRS:=/complex_clean)
	-@( echo -e "\nSub complex_clean: $(@:/complex_clean=) of $(PWD)" ; cd $(@:/complex_clean=) && $(MAKE) complex_clean )

########### #####################

########### Targets for recursive code static check #########################
code_lint: $(DIRS:=/lint)

nodirs_lint \
$(DIRS:=/lint):
	-@echo nodirs_lint $(DIRS:=/lint)
	-@( echo -e "\nSub lint: $(@:/lint=) of $(PWD)" ; cd $(@:/lint=) && $(MAKE) code_lint )

lint_clean: $(DIRS:=/lint_clean)

nodirs_lint_clean \
$(DIRS:=/lint_clean):
	-@echo nodirs_lint_clean $(DIRS:=/lint_clean)
	-@( echo -e "\nSub lint_clean: $(@:/lint_clean=) of $(PWD)" ; cd $(@:/lint_clean=) && $(MAKE) lint_clean )

########### #####################


