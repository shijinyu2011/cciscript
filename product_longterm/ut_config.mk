####UT target #######################
test unittest:
	for d in $(UTESTDIR);do cd $$d && make clean && make -C $$d gcov=y && make coverage;done
	for d in $(UTESTDIR); do ls $$d/*.xml && cat $$d/*.xml | sed 's/<?xml[^>]*>//' | sed -e 's#&#&amp;#g' >>$(VOBTAG)/product/build/TESTS-TestSuites.xml;done

test_clean unittest_clean:
	for d in $(UTESTDIR);do cd $$d && make clean;done
