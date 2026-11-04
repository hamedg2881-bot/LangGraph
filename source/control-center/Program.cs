using System.Diagnostics;
using System.Globalization;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Nodes;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls(Environment.GetEnvironmentVariable("CONTROL_CENTER_URL") ?? "http://0.0.0.0:5090");
builder.Services.AddHttpClient("platform", client => client.Timeout = TimeSpan.FromSeconds(5));
builder.Services.AddHostedService<HistoryBackgroundService>();

var app = builder.Build();
app.UseDefaultFiles();
app.UseStaticFiles();

app.MapGet("/api/health", () => Results.Ok(new
{
    status = "ok",
    application = "DGX Spark Control Center",
    version = "2.0.0",
    timestamp = DateTimeOffset.UtcNow
}));

app.MapGet("/api/status", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient("platform");
    var agentBase = BaseUrl("LANGGRAPH_AGENT_URL", "http://127.0.0.1:8100");
    var dynamoBase = BaseUrl("DYNAMO_URL", "http://127.0.0.1:8013");
    var agentHealth = await CheckEndpoint(client, $"{agentBase}/health");
    var agentModels = await GetJson(client, $"{agentBase}/v1/models");
    var dynamoHealth = await CheckEndpoint(client, $"{dynamoBase}/health");
    var dynamoModels = await GetJson(client, $"{dynamoBase}/v1/models") ?? await GetJson(client, $"{dynamoBase}/models");

    var containerNames = await DiscoverContainers();
    var runtime = new List<object>();
    foreach (var name in containerNames)
    {
        var state = await ReadContainerStatus(name);
        runtime.Add(new
        {
            id = name,
            name,
            role = ClassifyContainer(name),
            runtimeStatus = state,
            readiness = state == "running" ? "running" : state == "unknown" ? "unknown" : "stopped"
        });
    }

    var logicalModels = ReadModelIds(agentModels);
    var workers = ReadModelIds(dynamoModels);
    return Results.Ok(new
    {
        host = Environment.MachineName,
        timestamp = DateTimeOffset.UtcNow,
        resources = ReadResources(),
        agent = new { health = agentHealth.status, httpCode = agentHealth.httpCode, models = logicalModels },
        dynamo = new { health = dynamoHealth.status, httpCode = dynamoHealth.httpCode, models = workers },
        runtime
    });
});

app.MapGet("/api/ai-status", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient("platform");
    var agentBase = BaseUrl("LANGGRAPH_AGENT_URL", "http://127.0.0.1:8100");
    var dynamoBase = BaseUrl("DYNAMO_URL", "http://127.0.0.1:8013");
    var agentHealth = await CheckEndpoint(client, $"{agentBase}/health");
    var dynamoHealth = await CheckEndpoint(client, $"{dynamoBase}/health");
    var models = await GetJson(client, $"{agentBase}/v1/models");
    return Results.Ok(new
    {
        timestamp = DateTimeOffset.UtcNow,
        agent = new { health = agentHealth.status, modelsStatus = models is null ? "unreachable" : "ok", models = ReadModelIds(models) },
        dynamo = new { health = dynamoHealth.status, httpCode = dynamoHealth.httpCode }
    });
});

app.MapGet("/api/registry/models", async (IHttpClientFactory factory) =>
{
    var key = Environment.GetEnvironmentVariable("LANGGRAPH_ADMIN_API_KEY");
    if (string.IsNullOrWhiteSpace(key))
        return Results.Problem(
            title: "Registry integration is not configured",
            detail: "Set LANGGRAPH_ADMIN_API_KEY in the Control Center service environment. The value is used server-side only.",
            statusCode: StatusCodes.Status503ServiceUnavailable);

    var client = factory.CreateClient("platform");
    using var request = new HttpRequestMessage(HttpMethod.Get, $"{BaseUrl("LANGGRAPH_AGENT_URL", "http://127.0.0.1:8100")}/admin/models");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", key);
    try
    {
        using var response = await client.SendAsync(request);
        if (!response.IsSuccessStatusCode)
            return Results.Problem(
                title: "Registry request failed",
                detail: $"Agent Registry returned HTTP {(int)response.StatusCode}.",
                statusCode: StatusCodes.Status502BadGateway);

        var payload = JsonNode.Parse(await response.Content.ReadAsStringAsync());
        if (payload?["data"] is JsonArray models)
        {
            foreach (var model in models)
            {
                var id = model?["id"]?.GetValue<string>();
                if (string.IsNullOrWhiteSpace(id)) continue;
                using var statusRequest = new HttpRequestMessage(
                    HttpMethod.Get,
                    $"{BaseUrl("LANGGRAPH_AGENT_URL", "http://127.0.0.1:8100")}/admin/models/{Uri.EscapeDataString(id)}/status");
                statusRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", key);
                using var statusResponse = await client.SendAsync(statusRequest);
                if (!statusResponse.IsSuccessStatusCode) continue;
                var statusPayload = JsonNode.Parse(await statusResponse.Content.ReadAsStringAsync());
                model!["runtime_status"] = statusPayload?["runtime_status"]?.DeepClone();
                model["selectable"] = statusPayload?["selectable"]?.DeepClone();
            }
        }
        return Results.Json(payload);
    }
    catch (TaskCanceledException)
    {
        return Results.Problem(title: "Registry timeout", statusCode: StatusCodes.Status504GatewayTimeout);
    }
    catch
    {
        return Results.Problem(title: "Registry unavailable", statusCode: StatusCodes.Status502BadGateway);
    }
});

app.MapPost("/api/registry/sync", async (IHttpClientFactory factory) =>
    await ProxyRegistry(factory, HttpMethod.Post, "/sync", new JsonObject()));

app.MapPost("/api/registry/{id}/{action}", async (string id, string action, IHttpClientFactory factory) =>
{
    var allowed = new[] { "approve", "reject", "enable", "disable" };
    if (!allowed.Contains(action, StringComparer.Ordinal))
        return Results.BadRequest(new { detail = "Unsupported Registry action." });
    return await ProxyRegistry(factory, HttpMethod.Post,
        $"/{Uri.EscapeDataString(id)}/{action}", new JsonObject());
});

app.MapPatch("/api/registry/{id}", async (string id, JsonNode payload, IHttpClientFactory factory) =>
    await ProxyRegistry(factory, HttpMethod.Patch, $"/{Uri.EscapeDataString(id)}", payload));

app.MapGet("/api/model-manager/status", async (IHttpClientFactory factory) =>
    await ProxyAgentAdmin(factory, HttpMethod.Get, "/admin/model-manager/status", null));

app.MapPost("/api/model-manager/queue/{id}/cancel", async (string id, IHttpClientFactory factory) =>
    await ProxyAgentAdmin(factory, HttpMethod.Post,
        $"/admin/model-manager/queue/{Uri.EscapeDataString(id)}/cancel", new JsonObject()));

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
    var items = ReadHistoryFiles("/opt/ai/control-center/data", "events", DateTimeOffset.UtcNow.AddDays(-30));
    return Results.Ok(new { retentionDays = 30, events = items.TakeLast(requestedLimit).ToList() });
});

app.MapPost("/api/profile-switch", () => Results.Problem(
    title: "Profile switching is retired",
    detail: "Model lifecycle is managed by LangGraph and Dynamo. Direct Docker/systemd model switching is not supported.",
    statusCode: StatusCodes.Status410Gone));

app.Run();

static string BaseUrl(string name, string fallback) =>
    (Environment.GetEnvironmentVariable(name) ?? fallback).TrimEnd('/');

static List<string> ReadModelIds(JsonNode? payload)
{
    if (payload?["data"] is not JsonArray items) return new();
    return items.Select(item => item?["id"]?.GetValue<string>())
        .Where(id => !string.IsNullOrWhiteSpace(id)).Select(id => id!).ToList();
}

static async Task<JsonNode?> GetJson(HttpClient client, string url)
{
    try
    {
        using var response = await client.GetAsync(url);
        if (!response.IsSuccessStatusCode) return null;
        return JsonNode.Parse(await response.Content.ReadAsStringAsync());
    }
    catch { return null; }
}

static async Task<(string status, int? httpCode)> CheckEndpoint(HttpClient client, string url)
{
    try
    {
        using var response = await client.GetAsync(url);
        return (response.IsSuccessStatusCode ? "ok" : "http-error", (int)response.StatusCode);
    }
    catch (TaskCanceledException) { return ("timeout", null); }
    catch { return ("unreachable", null); }
}

static async Task<List<string>> DiscoverContainers()
{
    var configured = Environment.GetEnvironmentVariable("CONTROL_CENTER_CONTAINERS");
    if (!string.IsNullOrWhiteSpace(configured))
        return configured.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Distinct(StringComparer.Ordinal).ToList();

    var result = await RunCommand("docker", new[] { "ps", "-a", "--format", "{{.Names}}" });
    if (result.exitCode != 0) return new();
    return result.stdout.Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
        .Where(name => name.StartsWith("dynamo-", StringComparison.OrdinalIgnoreCase)
            || name.StartsWith("langgraph-", StringComparison.OrdinalIgnoreCase)
            || name.Equals("open-webui", StringComparison.OrdinalIgnoreCase))
        .Distinct(StringComparer.Ordinal).OrderBy(name => name).ToList();
}

static string ClassifyContainer(string name)
{
    var value = name.ToLowerInvariant();
    if (value.Contains("vllm") || value.Contains("worker") || value.Contains("vision")) return "worker";
    if (value.Contains("frontend") || value.Contains("gateway")) return "gateway";
    if (value.Contains("etcd") || value.Contains("nats")) return "dependency";
    if (value.Contains("postgres")) return "database";
    if (value.Contains("webui")) return "ui";
    if (value.Contains("agent")) return "agent";
    return "runtime";
}

static async Task<string> ReadContainerStatus(string name)
{
    var result = await RunCommand("docker", new[] { "inspect", "--format", "{{.State.Status}}", name });
    return result.exitCode == 0 ? result.stdout.Trim().ToLowerInvariant() : "unknown";
}

static async Task<(int exitCode, string stdout)> RunCommand(string file, IEnumerable<string> arguments)
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
        foreach (var arg in arguments) start.ArgumentList.Add(arg);
        using var process = new Process { StartInfo = start };
        process.Start();
        var output = process.StandardOutput.ReadToEndAsync();
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(4));
        try { await process.WaitForExitAsync(cts.Token); }
        catch (OperationCanceledException) { try { process.Kill(true); } catch { } return (-1, ""); }
        return (process.ExitCode, await output);
    }
    catch { return (-1, ""); }
}

static List<JsonNode> ReadHistoryFiles(string directory, string prefix, DateTimeOffset cutoff)
{
    var result = new List<(DateTimeOffset timestamp, JsonNode item)>();
    if (!Directory.Exists(directory)) return new();
    foreach (var file in Directory.EnumerateFiles(directory, $"{prefix}-*.jsonl").OrderBy(x => x))
    {
        foreach (var line in File.ReadLines(file))
        {
            try
            {
                var item = JsonNode.Parse(line);
                var raw = item?["timestamp"]?.GetValue<string>();
                if (item is not null && DateTimeOffset.TryParse(raw, out var timestamp) && timestamp >= cutoff)
                    result.Add((timestamp, item));
            }
            catch { }
        }
    }
    return result.OrderBy(x => x.timestamp).Select(x => x.item).ToList();
}

static object ReadResources()
{
    object? memory = null;
    try
    {
        var values = File.ReadAllLines("/proc/meminfo")
            .Select(line => line.Split(':', 2))
            .Where(parts => parts.Length == 2)
            .ToDictionary(parts => parts[0], parts => long.TryParse(
                parts[1].Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries)[0], out var value) ? value : 0);
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
            usedPercent = Math.Round(100d * (drive.TotalSize - drive.AvailableFreeSpace) / Math.Max(1, drive.TotalSize), 1)
        };
    }
    catch { }

    object? load = null;
    try
    {
        var parts = File.ReadAllText("/proc/loadavg").Split(' ', StringSplitOptions.RemoveEmptyEntries);
        load = new { oneMinute = parts[0], fiveMinutes = parts[1], fifteenMinutes = parts[2] };
    }
    catch { }

    object? gpu = null;
    var gpuResult = awaitRunNvidia();
    if (gpuResult.exitCode == 0)
    {
        var parts = gpuResult.stdout.Trim().Split(',', StringSplitOptions.TrimEntries);
        if (parts.Length >= 3)
            gpu = new
            {
                utilizationPercent = ParseDouble(parts[0]),
                temperatureC = ParseDouble(parts[1]),
                powerWatts = ParseDouble(parts[2])
            };
    }

    return new { timestamp = DateTimeOffset.UtcNow, memory, disk, loadAverage = load, gpu };
}

static (int exitCode, string stdout) awaitRunNvidia()
{
    try
    {
        var start = new ProcessStartInfo
        {
            FileName = "nvidia-smi",
            ArgumentList = { "--query-gpu=utilization.gpu,temperature.gpu,power.draw", "--format=csv,noheader,nounits" },
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        using var process = Process.Start(start);
        if (process is null || !process.WaitForExit(3000)) return (-1, "");
        return (process.ExitCode, process.StandardOutput.ReadToEnd());
    }
    catch { return (-1, ""); }
}

static double? ParseDouble(string value) =>
    double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var result) ? result : null;

static async Task<IResult> ProxyAgentAdmin(
    IHttpClientFactory factory, HttpMethod method, string path, JsonNode? payload)
{
    var key = Environment.GetEnvironmentVariable("LANGGRAPH_ADMIN_API_KEY");
    if (string.IsNullOrWhiteSpace(key))
        return Results.Problem(title: "Agent administration is not configured",
            detail: "The server-side Agent Registry credential is missing.",
            statusCode: StatusCodes.Status503ServiceUnavailable);

    var client = factory.CreateClient("platform");
    using var request = new HttpRequestMessage(method,
        $"{BaseUrl("LANGGRAPH_AGENT_URL", "http://127.0.0.1:8100")}{path}");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", key);
    if (payload is not null)
        request.Content = new StringContent(payload.ToJsonString(), System.Text.Encoding.UTF8, "application/json");

    try
    {
        using var response = await client.SendAsync(request);
        var body = await response.Content.ReadAsStringAsync();
        return Results.Content(body, response.Content.Headers.ContentType?.ToString() ?? "application/json",
            System.Text.Encoding.UTF8, (int)response.StatusCode);
    }
    catch (TaskCanceledException)
    {
        return Results.Problem(title: "Agent administration timeout", statusCode: StatusCodes.Status504GatewayTimeout);
    }
    catch
    {
        return Results.Problem(title: "Agent administration unavailable", statusCode: StatusCodes.Status502BadGateway);
    }
}

static async Task<IResult> ProxyRegistry(
    IHttpClientFactory factory, HttpMethod method, string path, JsonNode? payload)
{
    var key = Environment.GetEnvironmentVariable("LANGGRAPH_ADMIN_API_KEY");
    if (string.IsNullOrWhiteSpace(key))
        return Results.Problem(title: "Registry integration is not configured",
            detail: "The server-side Agent Registry credential is missing.",
            statusCode: StatusCodes.Status503ServiceUnavailable);

    var client = factory.CreateClient("platform");
    using var request = new HttpRequestMessage(method,
        $"{BaseUrl("LANGGRAPH_AGENT_URL", "http://127.0.0.1:8100")}/admin/models{path}");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", key);
    if (payload is not null)
        request.Content = new StringContent(payload.ToJsonString(), System.Text.Encoding.UTF8, "application/json");

    try
    {
        using var response = await client.SendAsync(request);
        var body = await response.Content.ReadAsStringAsync();
        return Results.Content(body, response.Content.Headers.ContentType?.ToString() ?? "application/json",
            System.Text.Encoding.UTF8, (int)response.StatusCode);
    }
    catch (TaskCanceledException)
    {
        return Results.Problem(title: "Registry timeout", statusCode: StatusCodes.Status504GatewayTimeout);
    }
    catch
    {
        return Results.Problem(title: "Registry unavailable", statusCode: StatusCodes.Status502BadGateway);
    }
}
