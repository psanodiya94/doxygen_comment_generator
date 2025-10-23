#include <gtest/gtest.h>
#include <string>
#include <vector>

// Example test file using Google Test framework

class StringUtilsTest : public ::testing::Test {
protected:
    void SetUp() override {
        test_string = "Hello, World!";
    }

    void TearDown() override {
        // Cleanup
    }

    std::string test_string;
};

TEST_F(StringUtilsTest, TestStringLength) {
    EXPECT_EQ(test_string.length(), 13);
    EXPECT_TRUE(test_string.length() > 0);
}

TEST_F(StringUtilsTest, TestStringComparison) {
    std::string expected = "Hello, World!";
    EXPECT_EQ(test_string, expected);
    EXPECT_STREQ(test_string.c_str(), expected.c_str());
}

TEST(MathUtilsTest, TestAddition) {
    int result = 2 + 2;
    EXPECT_EQ(result, 4);
    EXPECT_NE(result, 5);
}

TEST(MathUtilsTest, TestDivisionByZero) {
    EXPECT_THROW({
        int x = 10;
        int y = 0;
        if (y == 0) throw std::runtime_error("Division by zero");
        int result = x / y;
    }, std::runtime_error);
}

TEST(VectorTest, TestVectorOperations) {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    EXPECT_EQ(vec.size(), 5);
    EXPECT_FALSE(vec.empty());
    EXPECT_EQ(vec[0], 1);
    EXPECT_EQ(vec.back(), 5);
}

TEST(BoundaryTest, TestNegativeValues) {
    int negative = -10;
    EXPECT_LT(negative, 0);
    EXPECT_LE(negative, -10);
}

TEST(BoundaryTest, TestPositiveValues) {
    int positive = 10;
    EXPECT_GT(positive, 0);
    EXPECT_GE(positive, 10);
}

class CalculatorTest : public ::testing::Test {
protected:
    int add(int a, int b) { return a + b; }
    int subtract(int a, int b) { return a - b; }
    int multiply(int a, int b) { return a * b; }
};

TEST_F(CalculatorTest, TestBasicArithmetic) {
    EXPECT_EQ(add(2, 3), 5);
    EXPECT_EQ(subtract(5, 3), 2);
    EXPECT_EQ(multiply(3, 4), 12);
}

TEST_F(CalculatorTest, TestZeroOperations) {
    EXPECT_EQ(add(0, 5), 5);
    EXPECT_EQ(multiply(0, 100), 0);
    EXPECT_EQ(subtract(10, 0), 10);
}
