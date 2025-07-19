#pragma once

#include <vector>
#include <string>
#include <stdexcept>
#include <memory>

namespace ExampleProject {

class DatabaseConnection;

struct ConfigParams;

enum class Color {
    RED,
    GREEN,
    BLUE
};

namespace MathUtils {
int factorial(int n);
}

class IConfigManager {
public:
    virtual ~IConfigManager() = default;
    virtual bool loadConfig(const std::string& filename) = 0;
    virtual void saveConfig() const = 0;
};

class SettingsManager final : public IConfigManager {
public:
    static constexpr int MAX_SETTINGS = 100;
    explicit SettingsManager(const std::string& appName);
    ~SettingsManager() override;
    bool loadConfig(const std::string& filename) override;
    void saveConfig() const override;
    std::string getSetting(const std::string& key) const;
    void setSetting(const std::string& key, const std::string& value);
    bool hasSetting(const std::string& key) const noexcept;
    SettingsManager(const SettingsManager&) = delete;
    SettingsManager& operator=(const SettingsManager&) = delete;
private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

template <typename T, size_t N>
class BoundedArray {
public:
    BoundedArray() = default;
    T& at(size_t index);
    T& operator[](size_t index) noexcept;
    constexpr size_t size() const noexcept { return N; }
private:
    T data[N];
};

class DatabaseConnection {
public:
    enum Status {
        DISCONNECTED,
        CONNECTING,
        CONNECTED
    };
    DatabaseConnection();
    explicit DatabaseConnection(const ConfigParams& params);
    ~DatabaseConnection();
    void connect(const ConfigParams& params);
    void disconnect() noexcept;
    Status getStatus() const noexcept;
    std::vector<std::string> executeQuery(const std::string& query);
    bool isConnected() const noexcept {
        return getStatus() == CONNECTED;
    }
protected:
    virtual bool validateParams(const ConfigParams& params) const;
private:
    Status currentStatus = DISCONNECTED;
    std::string connectionString;
};

class ThreadSafeDBConnection : public DatabaseConnection {
public:
    using DatabaseConnection::DatabaseConnection;
    void connect(const ConfigParams& params) override;
    void disconnect() noexcept override;
protected:
    bool validateParams(const ConfigParams& params) const final;
};

struct ConfigParams {
    std::string host;
    int port;
    std::string username;
    std::string password;
    int timeout = 30;
};

std::shared_ptr<DatabaseConnection> createDBConnection(const ConfigParams& params);


extern const std::string APP_VERSION;


bool isFeatureEnabled(const std::string& featureName) noexcept;

} // namespace ExampleProject