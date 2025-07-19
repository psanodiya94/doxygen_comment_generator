#include "SampleHeader.h"
#include <iostream>

namespace ExampleProject {

int MathUtils::factorial(int n) {
    if (n < 0) throw std::invalid_argument("Negative input");
    int result = 1;
    for (int i = 2; i <= n; ++i) result *= i;
    return result;
}

SettingsManager::SettingsManager(const std::string& appName) {
    // Implementation
}

SettingsManager::~SettingsManager() = default;

bool SettingsManager::loadConfig(const std::string& filename) {
    // Implementation
    return true;
}

void SettingsManager::saveConfig() const {
    // Implementation
}

std::string SettingsManager::getSetting(const std::string& key) const {
    // Implementation
    return {};
}

void SettingsManager::setSetting(const std::string& key, const std::string& value) {
    // Implementation
}

bool SettingsManager::hasSetting(const std::string& key) const noexcept {
    // Implementation
    return false;
}

DatabaseConnection::DatabaseConnection() = default;
DatabaseConnection::DatabaseConnection(const ConfigParams& params) {}
DatabaseConnection::~DatabaseConnection() = default;

void DatabaseConnection::connect(const ConfigParams& params) {}
void DatabaseConnection::disconnect() noexcept {}
DatabaseConnection::Status DatabaseConnection::getStatus() const noexcept { return currentStatus; }
std::vector<std::string> DatabaseConnection::executeQuery(const std::string& query) { return {}; }
bool DatabaseConnection::validateParams(const ConfigParams& params) const { return true; }

void ThreadSafeDBConnection::connect(const ConfigParams& params) {}
void ThreadSafeDBConnection::disconnect() noexcept {}
bool ThreadSafeDBConnection::validateParams(const ConfigParams& params) const { return true; }

std::shared_ptr<DatabaseConnection> createDBConnection(const ConfigParams& params) {
    return std::make_shared<DatabaseConnection>(params);
}

const std::string APP_VERSION = "1.0.0";

bool isFeatureEnabled(const std::string& featureName) noexcept {
    return featureName == "test";
}

} //