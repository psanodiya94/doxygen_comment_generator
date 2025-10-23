#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>
#include <string>
#include <vector>

// Example test file using Catch2 framework

TEST_CASE("String operations", "[string]") {
    std::string str = "Hello";

    SECTION("length") {
        REQUIRE(str.length() == 5);
        CHECK(str.length() > 0);
    }

    SECTION("concatenation") {
        str += " World";
        REQUIRE(str == "Hello World");
        CHECK(str.length() == 11);
    }
}

TEST_CASE("Vector operations", "[vector][container]") {
    std::vector<int> vec;

    SECTION("empty vector") {
        REQUIRE(vec.empty());
        CHECK(vec.size() == 0);
    }

    SECTION("push elements") {
        vec.push_back(1);
        vec.push_back(2);
        vec.push_back(3);

        REQUIRE(vec.size() == 3);
        CHECK(vec[0] == 1);
        CHECK(vec.back() == 3);
    }
}

TEST_CASE("Mathematical operations", "[math]") {
    int a = 10;
    int b = 5;

    REQUIRE(a + b == 15);
    REQUIRE(a - b == 5);
    REQUIRE(a * b == 50);
    REQUIRE(a / b == 2);
}

SCENARIO("User authentication", "[auth][scenario]") {
    GIVEN("A user with valid credentials") {
        std::string username = "testuser";
        std::string password = "password123";

        WHEN("User attempts to login") {
            bool authenticated = (username == "testuser" && password == "password123");

            THEN("Login should succeed") {
                REQUIRE(authenticated == true);
            }
        }
    }

    GIVEN("A user with invalid credentials") {
        std::string username = "testuser";
        std::string password = "wrongpassword";

        WHEN("User attempts to login") {
            bool authenticated = (username == "testuser" && password == "password123");

            THEN("Login should fail") {
                REQUIRE(authenticated == false);
            }
        }
    }
}

TEST_CASE("Exception handling", "[exceptions]") {
    REQUIRE_THROWS([]() {
        throw std::runtime_error("Test error");
    }());

    REQUIRE_NOTHROW([]() {
        int x = 1 + 1;
    }());
}

TEST_CASE("Boolean conditions", "[bool]") {
    bool flag = true;

    REQUIRE(flag);
    CHECK_FALSE(!flag);
}

TEMPLATE_TEST_CASE("Template operations", "[template]", int, float, double) {
    TestType value = static_cast<TestType>(10);
    REQUIRE(value == static_cast<TestType>(10));
}
