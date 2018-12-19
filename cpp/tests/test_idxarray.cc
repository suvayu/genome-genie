#include <catch/catch.hpp>

#include <memory>
#include <iostream>
#include <typeinfo>
#include <iterator>
#include <cstdio>
#include <cstdlib>

#include <arrow/memory_pool.h>
#include <arrow/builder.h>
#include <arrow/array.h>
#include <arrow/table.h>

#include <gandiva/arrow.h>
#include <gandiva/filter.h>
#include <gandiva/tree_expr_builder.h>
#include <gandiva/projector.h>

#include "../macros.h"

using namespace gandiva;

using arrow::NumericArray;

namespace gandiva {
  using arrow::DataType;

  std::shared_ptr<arrow::ChunkedArray> view_array_by_idx
  (const ArrayPtr& arr, const ArrayPtr& idx)
  {
    std::shared_ptr<arrow::ChunkedArray> chunks;
    return chunks;
  }
}

ConditionPtr select_even(FieldPtr int_field)
{
  // even: i % 2 == 0
  auto int_node = TreeExprBuilder::MakeField(int_field);
  auto lit_2 = TreeExprBuilder::MakeLiteral(int64_t(2));
  auto remainder = TreeExprBuilder::MakeFunction("mod", {int_node, lit_2}, arrow::int64());
  auto lit_0 = TreeExprBuilder::MakeLiteral(int64_t(0));
  auto even = TreeExprBuilder::MakeFunction("equal", {remainder, lit_0}, arrow::boolean());
  auto condition = TreeExprBuilder::MakeCondition(even);
  return condition;
}

SCENARIO("indexing with index arrays", "[index-arrays]")
{
  arrow::MemoryPool* pool_ = arrow::default_memory_pool();

  GIVEN("A RecordBatch with one column: a 15-element Array")
    {
      int num_records = 15;
      std::vector<int64_t> expect;
      ArrayPtr arr;
      arrow::Int64Builder i64builder;
      i64builder.Reserve(num_records);
      for (uint8_t i = 0; i < 15; ++i) {
	auto val = std::rand();
	if (0 == val % 2) {
	  expect.push_back(val);
	}
	i64builder.UnsafeAppend(val);
      }
      EXPECT_OK(i64builder.Finish(&arr));

      // schema for input fields
      auto field0 = field("f0", arrow::int64());
      auto schema = arrow::schema({field0});

      // input record batch
      auto input_batch = arrow::RecordBatch::Make(schema, num_records, {arr});

      WHEN("Filtered for even numbers")
	{
	  auto condition = select_even(field0);

	  std::shared_ptr<Filter> filter;
	  EXPECT_OK(Filter::Make(schema, condition, &filter));
  
	  std::shared_ptr<SelectionVector> selected;
	  EXPECT_OK(SelectionVector::MakeInt16(num_records, pool_, &selected));
	  EXPECT_OK(filter->Evaluate(*input_batch, selected));

	  // NOTE: cast also needed for arr when directly accessing elements
	  auto idx_arr = std::dynamic_pointer_cast<
	    NumericArray<arrow::UInt16Type>>(selected->ToArray());
	  REQUIRE(idx_arr);

	  auto chunks = view_array_by_idx(arr, idx_arr);
	  REQUIRE(chunks);
	  REQUIRE(expect.size() == chunks->length());
	  
	  // for(uint i = 0; i < idx_arr->length(); ++i) {
	  //   REQUIRE(expect[i] == );
	  // }
	}
    }
}
