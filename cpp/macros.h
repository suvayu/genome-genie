#ifndef MY_MACROS_H
#define MY_MACROS_H

#define STRINGIFY(x) #x

#define EXPECT_TRUE(condition)                                  \
  if (true) {                                                   \
    if (!(condition)) {                                         \
      fprintf(stderr, "Check failed: %s\n", #condition);        \
      exit(1);                                                  \
    }                                                           \
  } else std::cerr << ""

#define EXPECT_FALSE(cond)    EXPECT_TRUE(!(cond))

// C99 declares isnan and isinf should be macros, so the #ifdef test
// should be reliable everywhere.  Of course, it's not, but these
// are testing pertty marginal functionality anyway, so it's ok to
// not-run them even in situations they might, with effort, be made to work.
#ifdef isnan  // Some compilers, like sun's for Solaris 10, don't define this
#define EXPECT_NAN(arg)                                         \
  do {                                                          \
    if (!isnan(arg)) {                                          \
      fprintf(stderr, "Check failed: isnan(%s)\n", #arg);       \
      exit(1);                                                  \
    }                                                           \
  } while (0)
#else
#define EXPECT_NAN(arg)
#endif

#ifdef isinf  // Some compilers, like sun's for Solaris 10, don't define this
#define EXPECT_INF(arg)                                         \
  do {                                                          \
    if (!isinf(arg)) {                                          \
      fprintf(stderr, "Check failed: isinf(%s)\n", #arg);       \
      exit(1);                                                  \
    }                                                           \
  } while (0)
#else
#define EXPECT_INF(arg)
#endif

// Arrow specific macros
#include <arrow/status.h>

#define EXPECT_OK(expr)         \
  do {                          \
    ::arrow::Status s = (expr); \
  } while (false)

#define ASSERT_OK(expr)                                               \
  do {                                                                \
    ::arrow::Status s = (expr);                                       \
    if (!s.ok()) {                                                    \
      std::cerr << "'" STRINGIFY(expr) "' failed with " << s.ToString();  \
    }                                                                 \
  } while (false)

#define EXPECT_ARROW_ARRAY_EQUALS(a, b)                                \
  EXPECT_TRUE((a)->Equals(b)) << "expected array: " << (a)->ToString() \
                              << " actual array: " << (b)->ToString();

#endif	// MY_MACROS_H
