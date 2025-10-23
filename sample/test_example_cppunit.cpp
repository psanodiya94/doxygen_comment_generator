#include <cppunit/TestCase.h>
#include <cppunit/TestFixture.h>
#include <cppunit/ui/text/TextTestRunner.h>
#include <cppunit/extensions/HelperMacros.h>
#include <string>

// Example test file using CppUnit framework

class StringTest : public CppUnit::TestFixture {
    CPPUNIT_TEST_SUITE(StringTest);
    CPPUNIT_TEST(testLength);
    CPPUNIT_TEST(testConcatenation);
    CPPUNIT_TEST(testComparison);
    CPPUNIT_TEST_SUITE_END();

protected:
    std::string str1;
    std::string str2;

public:
    void setUp() {
        str1 = "Hello";
        str2 = "World";
    }

    void tearDown() {
        // Cleanup
    }

    void testLength() {
        CPPUNIT_ASSERT_EQUAL(5, static_cast<int>(str1.length()));
        CPPUNIT_ASSERT(str1.length() > 0);
    }

    void testConcatenation() {
        std::string result = str1 + " " + str2;
        CPPUNIT_ASSERT_EQUAL(std::string("Hello World"), result);
        CPPUNIT_ASSERT_EQUAL(11, static_cast<int>(result.length()));
    }

    void testComparison() {
        CPPUNIT_ASSERT(str1 != str2);
        CPPUNIT_ASSERT_EQUAL(str1, std::string("Hello"));
    }
};

class MathTest : public CppUnit::TestFixture {
    CPPUNIT_TEST_SUITE(MathTest);
    CPPUNIT_TEST(testAddition);
    CPPUNIT_TEST(testSubtraction);
    CPPUNIT_TEST(testMultiplication);
    CPPUNIT_TEST_SUITE_END();

public:
    void testAddition() {
        CPPUNIT_ASSERT_EQUAL(4, 2 + 2);
        CPPUNIT_ASSERT_EQUAL(10, 7 + 3);
    }

    void testSubtraction() {
        CPPUNIT_ASSERT_EQUAL(0, 5 - 5);
        CPPUNIT_ASSERT_EQUAL(3, 10 - 7);
    }

    void testMultiplication() {
        CPPUNIT_ASSERT_EQUAL(12, 3 * 4);
        CPPUNIT_ASSERT_EQUAL(0, 5 * 0);
    }
};

CPPUNIT_TEST_SUITE_REGISTRATION(StringTest);
CPPUNIT_TEST_SUITE_REGISTRATION(MathTest);

int main() {
    CppUnit::TextTestRunner runner;
    runner.addTest(StringTest::suite());
    runner.addTest(MathTest::suite());
    runner.run();
    return 0;
}
