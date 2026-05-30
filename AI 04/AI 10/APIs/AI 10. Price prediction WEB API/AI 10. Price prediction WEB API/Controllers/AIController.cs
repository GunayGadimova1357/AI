using AI_10._Price_prediction_WEB_API.DTOs;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace AI_10._Price_prediction_WEB_API.Controllers;

[Route("api/[controller]")]
[ApiController]
public class AIController : ControllerBase
{
    private readonly HttpClient _httpClient;

    public AIController(IHttpClientFactory factory)
    {
        _httpClient = factory.CreateClient("ai");
    }

    [HttpPost("predict")]
    public async Task<IActionResult> Predict([FromBody] PredictIn predict)
    {
        var res = await _httpClient.PostAsJsonAsync("/predict", predict);

        if (!res.IsSuccessStatusCode)
        {
            return StatusCode((int)res.StatusCode, await res.Content.ReadAsStringAsync());
        }
        var prediction = await res.Content.ReadFromJsonAsync<PredictOutPython>();
        return Ok(prediction);
    }
    
}
