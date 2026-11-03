using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Net.Http;
using System.Globalization;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://0.0.0.0:5090");
builder.Services.AddHttpClient("health", client =>
{
    client.Timeout = TimeSpan.FromSeconds(3);
});

builder.Services.AddHostedService<HistoryBackgroundService>();

var app = builder.Build();
var manifestPath = "/opt/ai/control-center/config/profiles.json";

app.UseDefaultFiles();
app.UseStaticFiles();

app.MapGet("/api/health", () => Results.Ok(new
{
    status = "ok",
    application = "DGX Spark Control Center",
    timestamp = DateTimeOffset.UtcNow
}));

app.MapGet("/api/profiles", () =>
{
    if (!File.Exists(manifestPath))
        return Results.Problem("Manifest file not found.");

    try
    {
        var manifest = JsonNode.Parse(File.ReadAllText(manifestPath));
        return Results.Ok(manifest);
    }
    catch (Exception ex)
    {
        return Results.Problem($"Cannot read manifest: {ex.Message}");
    }
});

app.MapGet("/api/status", async (IHttpClientFactory httpFactory) =>
{
    var now = DateTimeOffset.UtcNow;
    JsonNode? manifest;

    try
    {
        manifest = JsonNode.Parse(await File.ReadAllTextAsync(manifestPath));
    }
    catch (Exception ex)
    {
        return Results.Problem($"Manifest unavailable: {ex.Message}");
    }

    var serviceResults = new List<object>();
    var services = manifest?["services"] as JsonObject;
    var shared = manifest?["sharedServices"] as JsonObject;
    var client = httpFactory.CreateClient("health");

    if (services is not null)
    {
        foreach (var entry in services)
        {
            var name = entry.Key;
            var item = entry.Value;
            var type = item?["type"]?.GetValue<string>() ?? "unknown";
            var resource = item?["resource"]?.GetValue<string>() ?? name;
            var url = item?["healthUrl"]?.GetValue<string>();
            var runtime = await ReadRuntimeStatus(type, resource);
            var endpoint = await CheckEndpoint(client, url);

            serviceResults.Add(new
            {
                name,
                category = "profile",
                type,
                resource,
                runtimeStatus = runtime,
                endpointStatus = endpoint.status,
                endpointHttpCode = endpoint.httpCode,
                endpointError = endpoint.error,
                healthUrl = url,
                readiness = GetReadiness(runtime, endpoint.status, type),
                checkedAt = now
            });
        }
    }

    if (shared is not null)
    {
        foreach (var entry in shared)
        {
            var name = entry.Key;
            var item = entry.Value;
            var type = item?["type"]?.GetValue<string>() ?? "unknown";
            var resource = item?["resource"]?.GetValue<string>() ?? name;
            var url = item?["healthUrl"]?.GetValue<string>();
            var runtime = await ReadRuntimeStatus(type, resource);
            var endpoint = await CheckEndpoint(client, url);

            serviceResults.Add(new
            {
                name,
                category = "shared",
                type,
                resource,
                runtimeStatus = runtime,
                endpointStatus = endpoint.status,
                endpointHttpCode = endpoint.httpCode,
                endpointError = endpoint.error,
                healthUrl = url,
                readiness = GetReadiness(runtime, endpoint.status, type),
                checkedAt = now
            });
        }
    }

    return Results.Ok(new
    {
        host = Environment.MachineName,
        timestamp = now,
        resources = ReadResources(),
        services = serviceResults
    });
});


app.MapGet("/api/ai-status", async (IHttpClientFactory httpFactory) =>
{
    var client = httpFactory.CreateClient("health");
    var agentBase = (Environment.GetEnvironmentVariable("LANGGRAPH_AGENT_URL") ?? "http://127.0.0.1:8100").TrimEnd('/');
    var dynamoBase = (Environment.GetEnvironmentVariable("DYNAMO_URL") ?? "http://127.0.0.1:8013").TrimEnd('/');
    var agentHealth = await CheckEndpoint(client, $"{agentBase}/health");
    var dynamoHealth = await CheckEndpoint(client, $"{dynamoBase}/health");
    var modelsStatus = "unreachable";
    var models = new List<string>();
    try
    {
        using var response = await client.GetAsync($"{agentBase}/v1/models");
        modelsStatus = response.IsSuccessStatusCode ? "ok" : $"http-{(int)response.StatusCode}";
        if (response.IsSuccessStatusCode)
        {
            var payload = JsonNode.Parse(await response.Content.ReadAsStringAsync());
            if (payload?["data"] is JsonArray items)
                models = items.Select(item => item?["id"]?.GetValue<string>()).Where(id => !string.IsNullOrWhiteSpace(id)).Select(id => id!).ToList();
        }
    }
    catch (TaskCanceledException) { modelsStatus = "timeout"; }
    catch { modelsStatus = "unreachable"; }
    return Results.Ok(new
    {
        timestamp = DateTimeOffset.UtcNow,
        agent = new { health = agentHealth.status, modelsStatus, models },
        dynamo = new { health = dynamoHealth.status, httpCode = dynamoHealth.httpCode }
    });
});
app.MapGet("/api/history", (int? hours) =>
{
    var requestedHours = Math.Clamp(hours ?? 24, 1, 720);
    var cutoff = DateTimeOffset.UtcNow.AddHours(-requestedHours);
    var items = ReadHistoryFiles("/opt/ai/control-center/data", "resources", cutoff);
    return Results.Ok(new { retentionDays = 30, hours = requestedHours, samples = items });
});

app.MapGet("/api/events", (int? limit) =>
{
    var requestedLimit = Math.Clamp(limit ?? 100, 1, 1000);
    var items = ReadHistoryFiles(
        "/opt/ai/control-center/data", "events",
        DateTimeOffset.UtcNow.AddDays(-30));
    return Results.Ok(new
    {
        retentionDays = 30,
        events = items.TakeLast(requestedLimit).ToList()
    });
});


app.MapPost("/api/profile-switch", () =>
    Results.Problem(
        title: "Profile switching is disabled",
        detail: "Model lifecycle remains read-only until the safe Model Manager supports request leases, draining, and queue coordination.",
        statusCode: StatusCodes.Status410Gone));

app.Run();


static List<JsonNode> ReadHistoryFiles(string directory, string prefix, DateTimeOffset cutoff)
{
    var result = new List<(DateTimeOffset timestamp, JsonNode item)>();
    if (!Directory.Exists(directory))
        return new List<JsonNode>();

    foreach (var file in Directory.EnumerateFiles(directory, $"{prefix}-*.jsonl").OrderBy(x => x))
    {
        foreach (var line in File.ReadLines(file))
        {
            try
            {
                var item = JsonNode.Parse(line);
                var raw = item?["timestamp"]?.GetValue<string>();
                if (item is not null &&
                    DateTimeOffset.TryParse(raw, out var timestamp) &&
                    timestamp >= cutoff)
                    result.Add((timestamp, item));
            }
            catch
            {
                // Ignore a malformed or partially written line.
            }
        }
    }

    return result.OrderBy(x => x.timestamp).Select(x => x.item).ToList();
}

static async Task<string> ReadRuntimeStatus(string type, string resource)
{
    if (type == "docker")
    {
        var result = await RunCommand("docker",
            new[] { "inspect", "--format", "{{.State.Status}}", resource });

        if (result.exitCode != 0)
            return "unknown";

        return result.stdout.Trim().ToLowerInvariant();
    }

    if (type == "systemd")
    {
        var result = await RunCommand("systemctl",
            new[] { "is-active", resource });

        return result.exitCode == 0
            ? result.stdout.Trim().ToLowerInvariant()
            : result.stdout.Trim().ToLowerInvariant() is "inactive" or "failed"
                ? result.stdout.Trim().ToLowerInvariant()
                : "unknown";
    }

    return "unknown";
}

static async Task<(string status, int? httpCode, string? error)> CheckEndpoint(
    HttpClient client, string? url)
{
    if (string.IsNullOrWhiteSpace(url))
        return ("not-configured", null, null);

    try
    {
        using var response = await client.GetAsync(url);
        var code = (int)response.StatusCode;

        return response.IsSuccessStatusCode
            ? ("ok", code, null)
            : ("http-error", code, $"HTTP {code}");
    }
    catch (TaskCanceledException)
    {
        return ("timeout", null, "Health check timed out");
    }
    catch (Exception ex)
    {
        return ("unreachable", null, ex.GetType().Name);
    }
}

static string GetReadiness(string runtime, string endpoint, string type)
{
    if (runtime is "exited" or "inactive" or "failed" or "dead")
        return "stopped";

    if (runtime != "running" && runtime != "active")
        return "unknown";

    if (endpoint == "ok")
        return "endpoint-healthy";

    if (endpoint == "not-configured")
        return "runtime-only";

    return "degraded";
}

static async Task<(int exitCode, string stdout, string stderr)> RunCommand(
    string file, IEnumerable<string> arguments, int timeoutSeconds = 4)
{
    try
    {
        var start = new ProcessStartInfo
        {
            FileName = file,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        foreach (var arg in arguments)
            start.ArgumentList.Add(arg);

        using var process = new Process { StartInfo = start };
        process.Start();

        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();

        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(Math.Max(1, timeoutSeconds)));
        try
        {
            await process.WaitForExitAsync(cts.Token);
        }
        catch (OperationCanceledException)
        {
            try { process.Kill(true); } catch { }
            return (-1, "", "Command timeout");
        }

        return (process.ExitCode, await stdoutTask, await stderrTask);
    }
    catch (Exception ex)
    {
        return (-1, "", ex.GetType().Name);
    }
}

static object ReadResources()
{
    object? memory = null;
    try
    {
        var values = File.ReadAllLines("/proc/meminfo")
            .Select(line => line.Split(':', 2))
            .Where(parts => parts.Length == 2)
            .ToDictionary(
                parts => parts[0],
                parts => long.TryParse(
                    parts[1].Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries)[0],
                    out var value) ? value : 0);

        long kb(string key) => values.TryGetValue(key, out var value) ? value : 0;

        memory = new
        {
            totalGiB = Math.Round(kb("MemTotal") / 1048576d, 2),
            availableGiB = Math.Round(kb("MemAvailable") / 1048576d, 2),
            usedGiB = Math.Round((kb("MemTotal") - kb("MemAvailable")) / 1048576d, 2),
            swapTotalGiB = Math.Round(kb("SwapTotal") / 1048576d, 2),
            swapFreeGiB = Math.Round(kb("SwapFree") / 1048576d, 2)
        };
    }
    catch { }

    object? disk = null;
    try
    {
        var drive = new DriveInfo("/");
        disk = new
        {
            totalGiB = Math.Round(drive.TotalSize / 1073741824d, 2),
            freeGiB = Math.Round(drive.AvailableFreeSpace / 1073741824d, 2),
            usedPercent = Math.Round(
                100d * (drive.TotalSize - drive.AvailableFreeSpace) /
                Math.Max(1, drive.TotalSize), 1)
        };
    }
    catch { }

    object? load = null;
    try
    {
        var parts = File.ReadAllText("/proc/loadavg")
            .Split(' ', StringSplitOptions.RemoveEmptyEntries);
        load = new { oneMinute = parts[0], fiveMinutes = parts[1], fifteenMinutes = parts[2] };
    }
    catch { }

    object? gpu = null;
    var gpuResult = RunCommand("nvidia-smi", new[]
    {
        "--query-gpu=utilization.gpu,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits"
    }).GetAwaiter().GetResult();

    if (gpuResult.exitCode == 0)
    {
        var line = gpuResult.stdout.Trim().Split('\n').FirstOrDefault()?.Trim();
        var parts = line?.Split(',', StringSplitOptions.TrimEntries);

        if (parts is { Length: >= 3 })
        {
            gpu = new
            {
                utilizationPercent = ParseDouble(parts[0]),
                temperatureC = ParseDouble(parts[1]),
                powerWatts = ParseDouble(parts[2]),
                memoryTotalGiB = (double?)null,
                memoryFreeGiB = (double?)null,
                note = "Total/free GPU memory not reported by this query; values are intentionally omitted."
            };
        }
    }

    return new
    {
        timestamp = DateTimeOffset.UtcNow,
        memory,
        disk,
        loadAverage = load,
        gpu
    };
}

static double? ParseDouble(string value)
{
    return double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var result)
        ? result
        : null;
}


public sealed record ProfileSwitchRequest(
    string TargetProfile,
    bool Confirm = false,
    bool AcknowledgeRequestInterruptionRisk = false);
