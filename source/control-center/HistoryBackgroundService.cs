using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;

public sealed class HistoryBackgroundService : BackgroundService
{
    private const string DataDirectory = "/opt/ai/control-center/data";
    private static readonly TimeSpan Retention = TimeSpan.FromDays(30);
    private readonly ILogger<HistoryBackgroundService> _logger;
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(10) };
    private readonly Dictionary<string, string> _previousReadiness = new();
    private DateTimeOffset _lastPrune = DateTimeOffset.MinValue;

    public HistoryBackgroundService(ILogger<HistoryBackgroundService> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        Directory.CreateDirectory(DataDirectory);
        PruneOldFiles();

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                var status = await _http.GetFromJsonAsync<JsonNode>(
                    "http://127.0.0.1:5090/api/status", stoppingToken);

                if (status is not null)
                {
                    var now = DateTimeOffset.UtcNow;
                    await AppendAsync("resources", new
                    {
                        timestamp = now,
                        resources = status["resources"]?.DeepClone()
                    }, stoppingToken);

                    if (status["runtime"] is JsonArray services)
                    {
                        foreach (var service in services)
                        {
                            if (service is null) continue;

                            var name = service["id"]?.GetValue<string>() ?? "unknown";
                            var readiness = service["readiness"]?.GetValue<string>() ?? "unknown";
                            var runtime = service["runtimeStatus"]?.GetValue<string>() ?? "unknown";

                            if (!_previousReadiness.TryGetValue(name, out var previous) ||
                                previous != readiness)
                            {
                                await AppendAsync("events", new
                                {
                                    timestamp = now,
                                    type = "runtime-readiness-changed",
                                    service = name,
                                    previousReadiness = previous ?? "unknown",
                                    readiness,
                                    runtimeStatus = runtime
                                }, stoppingToken);

                                _previousReadiness[name] = readiness;
                            }
                        }
                    }
                }
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "History sampling failed");
                try
                {
                    await AppendAsync("events", new
                    {
                        timestamp = DateTimeOffset.UtcNow,
                        type = "history-sampling-error",
                        message = ex.Message
                    }, stoppingToken);
                }
                catch (Exception writeEx)
                {
                    _logger.LogError(writeEx, "Could not write history error event");
                }
            }

            if (DateTimeOffset.UtcNow - _lastPrune >= TimeSpan.FromMinutes(10))
                PruneOldFiles();

            try
            {
                await Task.Delay(TimeSpan.FromSeconds(60), stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }

        _http.Dispose();
    }

    private static async Task AppendAsync(string prefix, object value, CancellationToken token)
    {
        var now = DateTimeOffset.UtcNow;
        var file = Path.Combine(DataDirectory,
            $"{prefix}-{now:yyyyMMdd-HH}.jsonl");

        await File.AppendAllTextAsync(
            file, JsonSerializer.Serialize(value) + Environment.NewLine, token);
    }

    private void PruneOldFiles()
    {
        try
        {
            Directory.CreateDirectory(DataDirectory);
            var cutoffHour = DateTimeOffset.UtcNow.Add(-Retention);
            cutoffHour = new DateTimeOffset(
                cutoffHour.Year, cutoffHour.Month, cutoffHour.Day,
                cutoffHour.Hour, 0, 0, TimeSpan.Zero);

            foreach (var file in Directory.EnumerateFiles(DataDirectory, "*.jsonl"))
            {
                var name = Path.GetFileNameWithoutExtension(file);
                var parts = name.Split('-');
                if (parts.Length != 3) continue;

                if (!DateTime.TryParseExact(
                    $"{parts[1]}-{parts[2]}", "yyyyMMdd-HH",
                    CultureInfo.InvariantCulture, DateTimeStyles.None, out var hour))
                    continue;

                var fileHour = new DateTimeOffset(hour, TimeSpan.Zero);
                if (fileHour <= cutoffHour)
                    File.Delete(file);
            }

            _lastPrune = DateTimeOffset.UtcNow;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "History retention cleanup failed");
        }
    }
}
