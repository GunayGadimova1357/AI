namespace AI_10._Price_prediction_WEB_API.DTOs;

public class PredictIn
{
    public float Bedrooms { get; set; }
    public float Bathrooms { get; set; }
    public float Sqm { get; set; }

    public string City { get; set; } = string.Empty;

}
