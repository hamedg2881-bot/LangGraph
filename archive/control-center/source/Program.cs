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
var profileSwitchLock = new SemaphoreSlim(1, 1);

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


app.MapPost("/api/profile-switch", async Task<IResult>
    (ProfileSwitchRequest request, IHttpClientFactory httpFactory) =>
{
    if (request is null ||
        string.IsNullOrWhiteSpace(request.TargetProfile))
        return Results.BadRequest(new { error = "TargetProfile is required." });

    if (!request.Confirm)
        return Results.BadRequest(new {
            error = "Explicit confirmation is required.",
            code = "confirmation-required"
        });

    if (!request.AcknowledgeRequestInterruptionRisk)
        return Results.BadRequest(new {
            error = "You must acknowledge that active requests may be interrupted.",
            code = "interruption-risk-not-acknowledged"
        });

    if (!await profileSwitchLock.WaitAsync(0))
        return Results.Conflict(new {
            error = "Another profile switch is already in progress."
        });

    try
    {
        var root = JsonNode.Parse(await File.ReadAllTextAsync(manifestPath))
            as JsonObject;

        var profiles = root?["profiles"] as JsonObject;
        var definitions = root?["services"] as JsonObject;
        var switching = root?["switching"] as JsonObject;

        if (profiles is null || definitions is null)
            return Results.Problem("Profile configuration is incomplete.");

        var targetName = request.TargetProfile.Trim();
        var target = profiles[targetName] as JsonObject;

        if (target is null)
            return Results.BadRequest(new {
                error = "Unknown target profile.",
                targetProfile = targetName
            });

        var targets = target["services"] as JsonObject;
        if (targets is null || targets.Count == 0)
            return Results.Problem("Target profile has no service definitions.");

        var plan = new List<(string name, string type, string resource,
            string desired, string healthUrl, int startTimeout, int stopTimeout)>();

        foreach (var item in targets)
        {
            if (item.Value is null)
                return Results.BadRequest(new {
                    error = "A service target is null.",
                    service = item.Key
                });

            var desired = item.Value.ToString().ToLowerInvariant();
            if (desired is not ("running" or "stopped"))
                return Results.BadRequest(new {
                    error = "Service target must be running or stopped.",
                    service = item.Key
                });

            var def = definitions[item.Key] as JsonObject;
            if (def is null)
                return Results.BadRequest(new {
                    error = "Service definition is missing.",
                    service = item.Key
                });

            var type = def["type"]?.ToString() ?? "";
            var resource = def["resource"]?.ToString() ?? "";

            if (type is not ("docker" or "systemd") ||
                string.IsNullOrWhiteSpace(resource))
                return Results.BadRequest(new {
                    error = "Invalid service runtime definition.",
                    service = item.Key
                });

            int ReadPositiveInt(string key, int fallback)
            {
                return int.TryParse(def[key]?.ToString(), out var n) && n > 0
                    ? n : fallback;
            }

            plan.Add((
                item.Key,
                type,
                resource,
                desired,
                def["healthUrl"]?.ToString() ?? "",
                ReadPositiveInt("startupTimeoutSeconds", 180),
                ReadPositiveInt("stopTimeoutSeconds", 30)
            ));
        }

        var previous = new Dictionary<string, string>(
            StringComparer.OrdinalIgnoreCase);

        foreach (var svc in plan)
        {
            var runtime = await ReadRuntimeStatus(svc.type, svc.resource);
            if (runtime is not ("running" or "active" or "exited" or
                "inactive" or "failed" or "dead"))
                return Results.Conflict(new {
                    error = "Could not reliably determine current service state; nothing was changed.",
                    service = svc.name,
                    runtime
                });

            previous[svc.name] = runtime;
        }

        var changed = new List<string>();

        async Task<(int exitCode, string stdout, string stderr)> SetService(
            string name, bool start)
        {
            var svc = plan.Single(x => x.name == name);
            string executable;
            string[] args;
            int timeout;

            if (svc.type == "docker")
            {
                executable = "docker";
                args = start
                    ? new[] { "start", svc.resource }
                    : new[] { "stop", "--time",
                        svc.stopTimeout.ToString(CultureInfo.InvariantCulture),
                        svc.resource };
                timeout = start ? 30 : svc.stopTimeout + 20;
            }
            else
            {
                executable = "systemctl";
                args = new[] { start ? "start" : "stop", svc.resource };
                timeout = start ? 60 : svc.stopTimeout + 20;
            }

            return await RunCommand(executable, args, timeout);
        }

        async Task<bool> WaitUntilHealthy(
            (string name, string type, string resource, string desired,
             string healthUrl, int startTimeout, int stopTimeout) svc)
        {
            var deadline = DateTimeOffset.UtcNow.AddSeconds(svc.startTimeout);
            var client = httpFactory.CreateClient("health");

            while (DateTimeOffset.UtcNow < deadline)
            {
                var runtime = await ReadRuntimeStatus(svc.type, svc.resource);

                if (runtime is "running" or "active")
                {
                    if (string.IsNullOrWhiteSpace(svc.healthUrl))
                        return true;

                    var check = await CheckEndpoint(client, svc.healthUrl);
                    if (check.status == "ok")
                        return true;
                }

                await Task.Delay(TimeSpan.FromSeconds(3));
            }

            return false;
        }

        var stopped = new List<string>();
        var started = new List<string>();

        try
        {
            foreach (var svc in plan.Where(x =>
                x.desired == "stopped" &&
                previous[x.name] is "running" or "active"))
            {
                var result = await SetService(svc.name, false);
                if (result.exitCode != 0)
                    throw new InvalidOperationException(
                        $"Stopping {svc.name} failed: {result.stderr}");

                changed.Add(svc.name);
                stopped.Add(svc.name);
            }

            foreach (var svc in plan.Where(x =>
                x.desired == "running" &&
                previous[x.name] is not ("running" or "active")))
            {
                var result = await SetService(svc.name, true);
                if (result.exitCode != 0)
                    throw new InvalidOperationException(
                        $"Starting {svc.name} failed: {result.stderr}");

                changed.Add(svc.name);
                started.Add(svc.name);
            }

            foreach (var svc in plan.Where(x => x.desired == "running"))
            {
                if (!await WaitUntilHealthy(svc))
                    throw new InvalidOperationException(
                        $"Service {svc.name} did not become healthy within " +
                        $"{svc.startTimeout} seconds.");
            }

            return Results.Ok(new {
                success = true,
                targetProfile = targetName,
                stoppedServices = stopped,
                startedServices = started,
                message = "Target services are running and passed their health checks."
            });
        }
        catch (Exception ex)
        {
            var rollbackErrors = new List<string>();

            foreach (var name in changed.AsEnumerable().Reverse())
            {
                try
                {
                    var svc = plan.Single(x => x.name == name);
                    var wasRunning = previous[name] is "running" or "active";
                    var now = await ReadRuntimeStatus(svc.type, svc.resource);
                    var isRunning = now is "running" or "active";

                    if (wasRunning != isRunning)
                    {
                        var result = await SetService(name, wasRunning);
                        if (result.exitCode != 0)
                            rollbackErrors.Add(
                                $"{name}: {result.stderr}");
                    }
                }
                catch (Exception rollbackEx)
                {
                    rollbackErrors.Add($"{name}: {rollbackEx.Message}");
                }
            }

            return Results.Problem(
                title: "Profile switch failed",
                detail: ex.Message + (rollbackErrors.Count == 0
                    ? " Rollback was attempted."
                    : " Rollback errors: " + string.Join("; ", rollbackErrors)),
                statusCode: StatusCodes.Status500InternalServerError,
                extensions: new Dictionary<string, object?> {
                    ["targetProfile"] = targetName,
                    ["changedServices"] = changed,
                    ["rollbackErrors"] = rollbackErrors
                });
        }
    }
    catch (JsonException)
    {
        return Results.Problem("Profile configuration contains invalid JSON.");
    }
    finally
    {
        profileSwitchLock.Release();
    }
});

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
