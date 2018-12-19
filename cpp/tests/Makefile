CC              := $(shell which gcc)
CXX             := $(shell which g++)
PKGCONFIG	:= $(shell which pkg-config)

CXXSTD          := -std=c++17
OPTS            := -g -Wall -m64 $(CXXSTD)

CXXFLAGS        := $(OPTS) -pthread -fPIC $(shell $(PKGCONFIG) --cflags gandiva)
LDFLAGS         := $(shell $(PKGCONFIG) --libs gandiva)

TESTSRC	:= $(wildcard test_*.cc)
TESTS	:= $(patsubst %.cc,%,$(filter-out test_main.cc,$(TESTSRC)))

.PHONY:	clean

tests:	$(patsubst %.cc,%.o,$(TESTSRC))
	$(CXX) $^ -o $@ $(LDFLAGS)

$(TESTS):%:	test_main.o %.o
	$(CXX) $+ -o $@ $(LDFLAGS)

$(patsubst %.cc,%.o,$(TESTSRC)):%.o:	%.cc
	$(CXX) -c $(CXXFLAGS) $< -o $@

clean:
	rm -rf *.o $(TESTS) tests
