PRODUCT = $(VOBTAG)/product
PLATFORM = $(VOBTAG)/flexiserver
LIBSOPT=true
SKIPTAGFAIL=true
INDIRECT_LINKING=true
PRODUCT_LIBS=$(PRODUCT)/lib
PRMJ=8


STD_CFLAGS = -D__TN_OS=3
STD_FLAGS = -D__TN_OS=3

PRODUCT_FAMILY=RCP

# This enables including product spesific makefile 
# after stdtargets.mk and stdctargets.mk. This can be used e.g. with product 
# spesific lint- and complexity targets.
# these two *.mk files will be included by build/mak/stdctargets.mk 
# and build/mak/stdctargets.mk 
PRODUCT_STDCTARGETS_MK=build/product_statistics.mk
PRODUCT_STDTARGETS_MK=build/product_stdtargets.mk


